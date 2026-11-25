#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import json
import math
import random
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

# ----------------------------------------------------------------------------
# Configuração
# ----------------------------------------------------------------------------
SEED = 42
REPETITIONS = 20
WARMUP_ROUNDS = 2
WARMUP_MAX_SECONDS = 5.0
TIMEOUT_SECONDS = 60.0
SLOW_BLOCK_LIMIT_SECONDS = 90.0
MIN_REPS_FOR_PARTIAL = 3
JSON_BUFFER = 8 * 1024 * 1024

HIERHOLZER_SIZES = [100, 1_000, 10_000, 50_000, 100_000, 500_000, 1_000_000]
BACKTRACKING_SIZES = list(range(10, 36, 2))
SCENARIOS = ["melhor", "medio", "pior"]

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "resultados.csv"
CSV_HEADER = [
    "linguagem", "problema", "algoritmo", "cenario", "n", "m",
    "media_ms", "desvio_padrao_ms", "repeticoes", "status",
]

ALGORITHMS = [
    {
        "algoritmo": "Hierholzer",
        "problema": "eulerian",
        "sizes": HIERHOLZER_SIZES,
        "dir": ROOT / "graph" / "eulerian",
    },
    {
        "algoritmo": "Backtracking",
        "problema": "hamiltonian",
        "sizes": BACKTRACKING_SIZES,
        "dir": ROOT / "graph" / "hamiltonian",
    },
]

RUNNERS = [
    {
        "name": "C",
        "cwd": ROOT,
        "cmd": lambda problema, path: ["./grafo_bench", problema, path],
    },
    {
        "name": "Python",
        "cwd": ROOT / "python",
        "cmd": lambda problema, path: [sys.executable, "main.py", problema, path],
    },
]

rng = random.Random(SEED)


# ----------------------------------------------------------------------------
# Terminal
# ----------------------------------------------------------------------------
def term_cols():
    return max(20, shutil.get_terminal_size((100, 24)).columns)


def live(msg):
    cols = term_cols()
    sys.stdout.write("\r" + msg[: cols - 1].ljust(cols - 1))
    sys.stdout.flush()


def clear_live():
    cols = term_cols()
    sys.stdout.write("\r" + " " * (cols - 1) + "\r")
    sys.stdout.flush()


def permanent(msg):
    clear_live()
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


# ----------------------------------------------------------------------------
# Utilidades de grafos (list[set[int]] durante a construção)
# ----------------------------------------------------------------------------
def new_adj(n):
    return [set() for _ in range(n)]


def add_edge(adj, u, v):
    adj[u].add(v)
    adj[v].add(u)


def finalize(adj):
    out = []
    for s in adj:
        lst = list(s)
        rng.shuffle(lst)
        out.append(lst)
    return out


def count_edges(lists):
    return sum(len(x) for x in lists) // 2


def random_cycle(adj, n):
    perm = list(range(n))
    rng.shuffle(perm)
    for i in range(n):
        add_edge(adj, perm[i], perm[(i + 1) % n])
    return n


def add_triangles(adj, n, m, target, pivots=None):
    needed = (target - m) // 3
    if needed <= 0:
        return m
    added = 0
    attempts = 0
    max_attempts = 30 * needed + 1000
    npiv = len(pivots) if pivots else 0
    while added < needed and attempts < max_attempts:
        attempts += 1
        if npiv and rng.random() < 0.5:
            u = pivots[rng.randrange(npiv)]
        else:
            u = rng.randrange(n)
        v = rng.randrange(n)
        w = rng.randrange(n)
        if u == v or u == w or v == w:
            continue
        au = adj[u]
        if v in au or w in au or w in adj[v]:
            continue
        au.add(v)
        au.add(w)
        adj[v].add(u)
        adj[v].add(w)
        adj[w].add(u)
        adj[w].add(v)
        added += 1
    return m + 3 * added


def add_random_edges(adj, n, m, target):
    max_edges = n * (n - 1) // 2
    target = min(target, max_edges)
    while m < target:
        u = rng.randrange(n)
        v = rng.randrange(n)
        if u == v or v in adj[u]:
            continue
        add_edge(adj, u, v)
        m += 1
    return m


# ----------------------------------------------------------------------------
# Geradores: Hierholzer
# ----------------------------------------------------------------------------
def gen_euler_melhor(n):
    adj = new_adj(n)
    random_cycle(adj, n)
    return finalize(adj)


def _euler_cap(n):
    return int(0.45 * n * (n - 1) / 2)


def gen_euler_medio(n):
    adj = new_adj(n)
    m = random_cycle(adj, n)
    target = min(_euler_cap(n), round(rng.uniform(2.0, 2.6) * n))
    add_triangles(adj, n, m, target)
    return finalize(adj)


def gen_euler_pior(n):
    adj = new_adj(n)
    m = random_cycle(adj, n)
    k = min(n, max(5, n // 20))
    pivots = rng.sample(range(n), k)
    target = min(_euler_cap(n), round(rng.uniform(6.5, 8.5) * n))
    add_triangles(adj, n, m, target, pivots=pivots)
    return finalize(adj)


# ----------------------------------------------------------------------------
# Geradores: Backtracking
# ----------------------------------------------------------------------------
def gen_ham_melhor(n):
    adj = new_adj(n)
    rest = list(range(1, n))
    rng.shuffle(rest)
    path = [0] + rest
    for i in range(n):
        add_edge(adj, path[i], path[(i + 1) % n])
    target = min(n * (n - 1) // 2, rng.randint(round(1.1 * n), round(1.4 * n)))
    add_random_edges(adj, n, n, target)
    lists = finalize(adj)
    for i in range(n):
        u = path[i]
        nxt = path[(i + 1) % n]
        lst = lists[u]
        lst.remove(nxt)
        lst.insert(0, nxt)
    return lists


def gen_ham_medio(n):
    adj = new_adj(n)
    perm = list(range(n))
    rng.shuffle(perm)
    for i in range(1, n):
        add_edge(adj, perm[i], perm[rng.randrange(i)])
    target = min(n * (n - 1) // 2, rng.randint(round(1.3 * n), round(1.7 * n)))
    add_random_edges(adj, n, n - 1, target)
    return finalize(adj)


def gen_ham_pior(n):
    adj = new_adj(n)
    perm = list(range(n))
    rng.shuffle(perm)
    a = n // 2 - 1
    A = perm[:a]
    B = perm[a:]
    for i in range(1, a):
        add_edge(adj, A[i], A[rng.randrange(i)])
    for v in B:
        for u in rng.sample(A, 2):
            add_edge(adj, v, u)
    candidates = []
    for i in range(a):
        ai = A[i]
        for v in B:
            if v not in adj[ai]:
                candidates.append((ai, v))
        for j in range(i + 1, a):
            aj = A[j]
            if aj not in adj[ai]:
                candidates.append((ai, aj))
    rng.shuffle(candidates)
    k = int(rng.uniform(0.65, 0.90) * len(candidates))
    for u, v in candidates[:k]:
        add_edge(adj, u, v)
    return finalize(adj)


GENERATORS = {
    ("Hierholzer", "melhor"): gen_euler_melhor,
    ("Hierholzer", "medio"): gen_euler_medio,
    ("Hierholzer", "pior"): gen_euler_pior,
    ("Backtracking", "melhor"): gen_ham_melhor,
    ("Backtracking", "medio"): gen_ham_medio,
    ("Backtracking", "pior"): gen_ham_pior,
}


# ----------------------------------------------------------------------------
# Arquivos temporários
# ----------------------------------------------------------------------------
def inst_path(directory, i):
    return directory / f"inst_{i:02d}.json"


def clean_instances(directory):
    for p in directory.glob("inst_*.json"):
        try:
            p.unlink()
        except OSError:
            pass


def generate_batch(algoritmo, cenario, n, directory):
    gen = GENERATORS[(algoritmo, cenario)]
    total_m = 0
    t0 = time.perf_counter()
    for i in range(1, REPETITIONS + 1):
        live(f"[gerando] {algoritmo}/{cenario} n={n:,} inst {i:02d}/{REPETITIONS} "
             f"({time.perf_counter() - t0:.1f}s)")
        lists = gen(n)
        total_m += count_edges(lists)
        payload = json.dumps(lists, separators=(",", ":"))
        del lists
        with open(inst_path(directory, i), "w", buffering=JSON_BUFFER, encoding="utf-8") as f:
            f.write(payload)
        del payload
    live(f"[gerando] {algoritmo}/{cenario} n={n:,} concluído em {time.perf_counter() - t0:.1f}s")
    return round(total_m / REPETITIONS)


# ----------------------------------------------------------------------------
# Execução
# ----------------------------------------------------------------------------
def run_once(runner, problema, path):
    """Retorna (tempo_ms | None, status) com status em OK/TIMEOUT/ERRO."""
    cmd = runner["cmd"](problema, str(path.resolve()))
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(runner["cwd"]),
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return None, "TIMEOUT"
    except OSError:
        return None, "ERRO"
    if proc.returncode != 0:
        return None, "ERRO"
    try:
        value = float(proc.stdout.strip())
    except ValueError:
        return None, "ERRO"
    if not math.isfinite(value) or value < 0:
        return None, "ERRO"
    return value, "OK"


def run_block(runner, algo, cenario, n, directory):
    problema = algo["problema"]
    algoritmo = algo["algoritmo"]
    lang = runner["name"]
    tag = f"[{lang}] {algoritmo}/{cenario} n={n:,}"
    first = inst_path(directory, 1)

    # Aquecimento (descartado da estatística)
    for r in range(1, WARMUP_ROUNDS + 1):
        live(f"{tag} aquecimento {r}/{WARMUP_ROUNDS}")
        t0 = time.perf_counter()
        _, st = run_once(runner, problema, first)
        elapsed = time.perf_counter() - t0
        if st != "OK":
            break
        if r == 1 and elapsed > WARMUP_MAX_SECONDS:
            break

    samples = []
    status = "OK"
    block_start = time.perf_counter()
    acum = 0.0
    for i in range(1, REPETITIONS + 1):
        live(f"{tag} rep {i:02d}/{REPETITIONS} acum={acum:.1f}s")
        value, st = run_once(runner, problema, inst_path(directory, i))
        acum = time.perf_counter() - block_start
        if st != "OK":
            status = st
            break
        samples.append(value)
        if (i < REPETITIONS and len(samples) >= MIN_REPS_FOR_PARTIAL
                and acum > SLOW_BLOCK_LIMIT_SECONDS):
            status = "PARCIAL_90S"
            break
    return samples, status, acum


def compute_stats(samples):
    k = len(samples)
    if k == 0:
        return "", ""
    mean = statistics.fmean(samples)
    dev = 0.0 if k == 1 else statistics.stdev(samples)
    return mean, dev


def fmt_num(x):
    return "" if x == "" else f"{x:.6f}"


def report_block(writer, fh, runner, algo, cenario, n, m, samples, status, acum):
    mean, dev = compute_stats(samples)
    writer.writerow([
        runner["name"], algo["problema"], algo["algoritmo"], cenario, n, m,
        fmt_num(mean), fmt_num(dev), len(samples), status,
    ])
    fh.flush()
    if mean == "":
        stats_txt = f"{'-':>12} ± {'-':>10} ms"
    else:
        stats_txt = f"{mean:>12.4f} ± {dev:>10.4f} ms"
    permanent(
        f"{runner['name']:<6} {algo['algoritmo']:<12} {cenario:<6} "
        f"n={n:>9,} m={m:>10,} acum={acum:>7.2f}s  {stats_txt}  "
        f"reps={len(samples):>2}/{REPETITIONS}  {status}"
    )
    return mean


# ----------------------------------------------------------------------------
# Principal
# ----------------------------------------------------------------------------
def print_summary(best):
    print()
    print("=" * 96)
    print("RESUMO — Backtracking (Hamiltoniano): maior n viável em até "
          f"{TIMEOUT_SECONDS:.0f}s e média (ms)")
    print("=" * 96)
    print(f"{'cenario':<8} | {'C: maior n':>10} | {'C: média ms':>16} | "
          f"{'Python: maior n':>15} | {'Python: média ms':>18}")
    print("-" * 96)
    for cen in SCENARIOS:
        cells = []
        for lang in ("C", "Python"):
            entry = best.get((cen, lang))
            if entry is None:
                cells.append(("-", "-"))
            else:
                cells.append((str(entry[0]), f"{entry[1]:.4f}"))
        print(f"{cen:<8} | {cells[0][0]:>10} | {cells[0][1]:>16} | "
              f"{cells[1][0]:>15} | {cells[1][1]:>18}")
    print("=" * 96)


def main():
    if not (ROOT / "grafo_bench").exists():
        sys.exit("Erro: executável ./grafo_bench não encontrado na raiz do projeto.")
    if not (ROOT / "python" / "main.py").exists():
        sys.exit("Erro: python/main.py não encontrado.")

    best = {}
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(CSV_HEADER)
        fh.flush()

        for algo in ALGORITHMS:
            directory = algo["dir"]
            directory.mkdir(parents=True, exist_ok=True)
            algoritmo = algo["algoritmo"]
            print(f"\n### {algoritmo} ({algo['problema']}) ###")

            for cenario in SCENARIOS:
                stopped = {r["name"]: False for r in RUNNERS}

                for n in algo["sizes"]:
                    if all(stopped.values()):
                        break

                    clean_instances(directory)
                    try:
                        m = generate_batch(algoritmo, cenario, n, directory)

                        for runner in RUNNERS:
                            lang = runner["name"]
                            if stopped[lang]:
                                continue
                            samples, status, acum = run_block(
                                runner, algo, cenario, n, directory)
                            mean = report_block(writer, fh, runner, algo, cenario,
                                                n, m, samples, status, acum)
                            if status in ("TIMEOUT", "ERRO"):
                                stopped[lang] = True
                            elif algoritmo == "Backtracking" and mean != "":
                                best[(cenario, lang)] = (n, mean)
                    finally:
                        clean_instances(directory)

    clear_live()
    print_summary(best)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_live()
        print("\nInterrompido pelo usuário.")
        sys.exit(130)
