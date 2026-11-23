import csv
import json
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import sys
import time

SEED = 42
REPETITIONS = 20
WARMUP_ROUNDS = 2
WARMUP_MAX_SECONDS = 5.0
TIMEOUT_SECONDS = 60.0
SLOW_BLOCK_LIMIT_SECONDS = 90.0
JSON_BUFFER_BYTES = 8 * 1024 * 1024

HIERHOLZER_SIZES = [100, 1_000, 10_000, 50_000, 100_000, 500_000, 1_000_000]
BACKTRACKING_SIZES = list(range(10, 36, 2))
SCENARIOS = ["melhor", "medio", "pior"]

ROOT_DIR = Path(__file__).resolve().parent
CSV_PATH = ROOT_DIR / "resultados.csv"
CSV_COLUMNS = [
    "linguagem",
    "problema",
    "algoritmo",
    "cenario",
    "n",
    "m",
    "media_ms",
    "desvio_padrao_ms",
    "repeticoes",
    "status",
]


def print_live(text: str) -> None:
    cols = shutil.get_terminal_size(fallback=(120, 24)).columns
    max_len = max(10, cols - 1)
    if len(text) > max_len:
        text = text[: max_len - 3] + "..."
    sys.stdout.write("\r" + text.ljust(max_len))
    sys.stdout.flush()


def clear_live() -> None:
    cols = shutil.get_terminal_size(fallback=(120, 24)).columns
    max_len = max(10, cols - 1)
    sys.stdout.write("\r" + (" " * max_len) + "\r")
    sys.stdout.flush()


def clean_instance_files(folder: Path) -> None:
    if not folder.exists():
        return
    for file_path in folder.glob("inst_*.json"):
        try:
            file_path.unlink()
        except OSError:
            pass


def save_graph_json(adj: list[list[int]], file_path: Path) -> None:
    with file_path.open("w", encoding="utf-8", buffering=JSON_BUFFER_BYTES) as f:
        json.dump(adj, f, separators=(",", ":"))


def _build_random_cycle(n: int, rng: random.Random) -> tuple[list[set[int]], list[int], int]:
    order = list(range(n))
    rng.shuffle(order)
    adj: list[set[int]] = [set() for _ in range(n)]
    for i in range(n):
        u = order[i]
        v = order[(i + 1) % n]
        adj[u].add(v)
        adj[v].add(u)
    return adj, order, n


def generate_eulerian_graph(
    n: int, scenario: str, rng: random.Random
) -> tuple[list[list[int]], int]:
    adj, _, m = _build_random_cycle(n, rng)
    max_sparse_edges = int(0.45 * (n * (n - 1) // 2))

    if scenario == "medio":
        raw_target = round(rng.uniform(2.0, 2.6) * n)
        m_target = min(max_sparse_edges, raw_target)
        max_attempts = max(1000, (m_target - m) * 20)
        attempts = 0
        while m + 2 < m_target and attempts < max_attempts:
            attempts += 1
            u = rng.randrange(n)
            v = rng.randrange(n)
            w = rng.randrange(n)
            if u == v or v == w or u == w:
                continue
            if v in adj[u] or w in adj[v] or u in adj[w]:
                continue
            adj[u].add(v)
            adj[v].add(u)
            adj[v].add(w)
            adj[w].add(v)
            adj[w].add(u)
            adj[u].add(w)
            m += 3

    elif scenario == "pior":
        raw_target = round(rng.uniform(6.5, 8.5) * n)
        m_target = min(max_sparse_edges, raw_target)
        num_pivots = min(n, max(5, n // 20))
        pivots = rng.sample(range(n), num_pivots)
        max_attempts = max(2000, (m_target - m) * 25)
        attempts = 0
        while m + 2 < m_target and attempts < max_attempts:
            attempts += 1
            mode = rng.random()
            if mode < 0.45 and num_pivots >= 2:
                u, v = rng.sample(pivots, 2)
                w = rng.randrange(n)
            elif mode < 0.75:
                u = rng.choice(pivots)
                v = rng.randrange(n)
                w = rng.randrange(n)
            else:
                u = rng.randrange(n)
                v = rng.randrange(n)
                w = rng.randrange(n)

            if u == v or v == w or u == w:
                continue
            if v in adj[u] or w in adj[v] or u in adj[w]:
                continue
            adj[u].add(v)
            adj[v].add(u)
            adj[v].add(w)
            adj[w].add(v)
            adj[w].add(u)
            adj[u].add(w)
            m += 3

    result: list[list[int]] = []
    for neighbors_set in adj:
        neighbors = list(neighbors_set)
        rng.shuffle(neighbors)
        result.append(neighbors)
    return result, m


def generate_hamiltonian_graph(
    n: int, scenario: str, rng: random.Random
) -> tuple[list[list[int]], int]:
    max_edges = n * (n - 1) // 2
    adj: list[set[int]] = [set() for _ in range(n)]

    if scenario == "melhor":
        rest = list(range(1, n))
        rng.shuffle(rest)
        path = [0] + rest
        for i in range(n):
            u = path[i]
            v = path[(i + 1) % n]
            adj[u].add(v)
            adj[v].add(u)
        m = n

        m_target = min(max_edges, rng.randint(round(1.1 * n), round(1.4 * n)))
        while m < m_target:
            u = rng.randrange(n)
            v = rng.randrange(n)
            if u != v and v not in adj[u]:
                adj[u].add(v)
                adj[v].add(u)
                m += 1

        next_in_cycle = [0] * n
        for i in range(n):
            next_in_cycle[path[i]] = path[(i + 1) % n]

        result = []
        for u in range(n):
            neighbors = list(adj[u])
            rng.shuffle(neighbors)
            forced_next = next_in_cycle[u]
            neighbors.remove(forced_next)
            neighbors.insert(0, forced_next)
            result.append(neighbors)
        return result, m

    if scenario == "medio":
        order = list(range(n))
        rng.shuffle(order)
        for i in range(1, n):
            u = order[i]
            v = order[rng.randrange(i)]
            adj[u].add(v)
            adj[v].add(u)
        m = n - 1

        m_target = min(max_edges, rng.randint(round(1.3 * n), round(1.7 * n)))
        while m < m_target:
            u = rng.randrange(n)
            v = rng.randrange(n)
            if u != v and v not in adj[u]:
                adj[u].add(v)
                adj[v].add(u)
                m += 1

        result = []
        for neighbors_set in adj:
            neighbors = list(neighbors_set)
            rng.shuffle(neighbors)
            result.append(neighbors)
        return result, m

    # scenario == "pior"
    perm = list(range(n))
    rng.shuffle(perm)
    a = (n // 2) - 1
    set_a = perm[:a]
    set_b = perm[a:]
    b = len(set_b)

    m = 0
    for i in range(1, a):
        u = set_a[i]
        v = set_a[rng.randrange(i)]
        adj[u].add(v)
        adj[v].add(u)
        m += 1

    for u in set_b:
        chosen_a = rng.sample(set_a, 2)
        for v in chosen_a:
            if v not in adj[u]:
                adj[u].add(v)
                adj[v].add(u)
                m += 1

    candidates: list[tuple[int, int]] = []
    for i in range(a):
        u = set_a[i]
        for j in range(i + 1, a):
            v = set_a[j]
            if v not in adj[u]:
                candidates.append((u, v))
    for u in set_a:
        for v in set_b:
            if v not in adj[u]:
                candidates.append((u, v))

    rng.shuffle(candidates)
    max_allowed = (a * (a - 1) // 2) + (a * b)
    target_total = round(rng.uniform(0.65, 0.90) * max_allowed)
    extra_needed = min(len(candidates), max(0, target_total - m))

    for u, v in candidates[:extra_needed]:
        adj[u].add(v)
        adj[v].add(u)
        m += 1

    result = []
    for neighbors_set in adj:
        neighbors = list(neighbors_set)
        rng.shuffle(neighbors)
        result.append(neighbors)
    return result, m


def generate_batch(
    problema: str,
    algoritmo: str,
    scenario: str,
    n: int,
    target_dir: Path,
    rng: random.Random,
) -> tuple[list[Path], int]:
    target_dir.mkdir(parents=True, exist_ok=True)
    clean_instance_files(target_dir)

    instance_paths: list[Path] = []
    edge_counts: list[int] = []

    for idx in range(1, REPETITIONS + 1):
        print_live(
            f"[{algoritmo} | {scenario} | n={n:,}] Gerando lote: {idx}/{REPETITIONS} instâncias..."
        )
        if problema == "eulerian":
            graph, m = generate_eulerian_graph(n, scenario, rng)
        else:
            graph, m = generate_hamiltonian_graph(n, scenario, rng)

        inst_path = target_dir / f"inst_{idx:02d}.json"
        save_graph_json(graph, inst_path)
        instance_paths.append(inst_path)
        edge_counts.append(m)

    m_avg = round(sum(edge_counts) / len(edge_counts))
    return instance_paths, m_avg


def run_single_invocation(
    language: str, problema: str, json_path: Path
) -> tuple[str, float]:
    abs_json = str(json_path.resolve())
    if language == "C":
        cmd = [str(ROOT_DIR / "grafo_bench"), problema, abs_json]
        cwd = str(ROOT_DIR)
    else:
        cmd = [sys.executable, "main.py", problema, abs_json]
        cwd = str(ROOT_DIR / "python")

    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return "TIMEOUT", 0.0
    except OSError:
        return "ERRO", 0.0

    if proc.returncode != 0:
        return "ERRO", 0.0

    raw_out = proc.stdout.strip()
    if not raw_out:
        return "ERRO", 0.0

    try:
        elapsed_ms = float(raw_out.splitlines()[-1].strip())
    except ValueError:
        return "ERRO", 0.0

    if not (elapsed_ms >= 0.0) or elapsed_ms == float("inf"):
        return "ERRO", 0.0

    return "OK", elapsed_ms


def benchmark_runner(
    language: str,
    problema: str,
    algoritmo: str,
    scenario: str,
    n: int,
    m_avg: int,
    instance_paths: list[Path],
) -> dict[str, object]:
    for w_idx in range(1, WARMUP_ROUNDS + 1):
        print_live(
            f"[{algoritmo} | {scenario} | n={n:,} | {language}] Aquecimento {w_idx}/{WARMUP_ROUNDS}..."
        )
        w_start = time.perf_counter()
        w_status, _ = run_single_invocation(language, problema, instance_paths[0])
        w_elapsed = time.perf_counter() - w_start

        if w_status != "OK":
            clear_live()
            return {
                "linguagem": language,
                "problema": problema,
                "algoritmo": algoritmo,
                "cenario": scenario,
                "n": n,
                "m": m_avg,
                "media_ms": "",
                "desvio_padrao_ms": "",
                "repeticoes": 0,
                "status": w_status,
                "acum_s": 0.0,
                "mean_val": None,
                "std_val": None,
            }

        if w_idx == 1 and w_elapsed > WARMUP_MAX_SECONDS:
            break

    times_ms: list[float] = []
    final_status = "OK"
    block_start = time.perf_counter()

    for idx, inst_path in enumerate(instance_paths, start=1):
        status, elapsed_ms = run_single_invocation(language, problema, inst_path)
        acum_s = time.perf_counter() - block_start

        if status != "OK":
            final_status = status
            break

        times_ms.append(elapsed_ms)
        print_live(
            f"[{algoritmo} | {scenario} | n={n:,} | {language}] "
            f"Rep {idx}/{REPETITIONS} | ultima={elapsed_ms:.3f} ms | acum={acum_s:.2f}s"
        )

        if len(times_ms) >= 3 and acum_s > SLOW_BLOCK_LIMIT_SECONDS and idx < REPETITIONS:
            final_status = "PARCIAL_90S"
            break

    acum_total_s = time.perf_counter() - block_start
    clear_live()

    reps = len(times_ms)
    if reps == 0:
        mean_val = None
        std_val = None
        media_str = ""
        std_str = ""
    elif reps == 1:
        mean_val = statistics.mean(times_ms)
        std_val = 0.0
        media_str = f"{mean_val:.6f}"
        std_str = "0.0"
    else:
        mean_val = statistics.mean(times_ms)
        std_val = statistics.stdev(times_ms)
        media_str = f"{mean_val:.6f}"
        std_str = f"{std_val:.6f}"

    return {
        "linguagem": language,
        "problema": problema,
        "algoritmo": algoritmo,
        "cenario": scenario,
        "n": n,
        "m": m_avg,
        "media_ms": media_str,
        "desvio_padrao_ms": std_str,
        "repeticoes": reps,
        "status": final_status,
        "acum_s": acum_total_s,
        "mean_val": mean_val,
        "std_val": std_val,
    }


def print_runner_result(res: dict[str, object]) -> None:
    mean_val = res["mean_val"]
    std_val = res["std_val"]
    if mean_val is None:
        stats_col = f"{'-':>25}"
    else:
        stats_col = f"{mean_val:10.3f} ± {std_val:8.3f} ms"

    line = (
        f"{str(res['linguagem']):<6} | "
        f"{str(res['algoritmo']):<12} | "
        f"{str(res['cenario']):<6} | "
        f"n={int(res['n']):>9} | "
        f"m={int(res['m']):>10} | "
        f"acum={float(res['acum_s']):>6.2f}s | "
        f"{stats_col} | "
        f"reps={int(res['repeticoes']):>2}/{REPETITIONS} | "
        f"{res['status']}"
    )
    print(line, flush=True)


def print_backtracking_summary(
    best_viable: dict[tuple[str, str], tuple[int, float] | None]
) -> None:
    print("\n" + "=" * 78)
    print("RESUMO BACKTRACKING (HAMILTONIANO) — MAIOR N VIÁVEL EM ATÉ 60s")
    print("=" * 78)
    header = f"{'Cenário':<10} | {'Linguagem':<10} | {'Maior n Viável':>15} | {'Média (ms)':>18}"
    print(header)
    print("-" * 78)
    for scenario in SCENARIOS:
        for lang in ("C", "Python"):
            entry = best_viable.get((scenario, lang))
            if entry is None:
                n_str = "N/A"
                mean_str = "N/A"
            else:
                n_str = f"{entry[0]:,}"
                mean_str = f"{entry[1]:.3f}"
            print(f"{scenario:<10} | {lang:<10} | {n_str:>15} | {mean_str:>18}")
    print("=" * 78, flush=True)


def main() -> None:
    rng = random.Random(SEED)

    benchmarks = [
        ("eulerian", "Hierholzer", HIERHOLZER_SIZES, ROOT_DIR / "graph" / "eulerian"),
        ("hamiltonian", "Backtracking", BACKTRACKING_SIZES, ROOT_DIR / "graph" / "hamiltonian"),
    ]

    best_viable_bt: dict[tuple[str, str], tuple[int, float] | None] = {
        (scenario, lang): None for scenario in SCENARIOS for lang in ("C", "Python")
    }

    with CSV_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        csv_file.flush()

        for problema, algoritmo, sizes, graph_dir in benchmarks:
            graph_dir.mkdir(parents=True, exist_ok=True)
            print(f"\n=== INICIANDO BENCHMARK: {algoritmo.upper()} ({problema}) ===", flush=True)

            for scenario in SCENARIOS:
                print(f"\n--- Cenário: {scenario} ---", flush=True)
                stopped_runners: set[str] = set()

                for n in sizes:
                    active_runners = [lang for lang in ("C", "Python") if lang not in stopped_runners]
                    if not active_runners:
                        break

                    try:
                        instance_paths, m_avg = generate_batch(
                            problema=problema,
                            algoritmo=algoritmo,
                            scenario=scenario,
                            n=n,
                            target_dir=graph_dir,
                            rng=rng,
                        )

                        for lang in active_runners:
                            res = benchmark_runner(
                                language=lang,
                                problema=problema,
                                algoritmo=algoritmo,
                                scenario=scenario,
                                n=n,
                                m_avg=m_avg,
                                instance_paths=instance_paths,
                            )
                            print_runner_result(res)

                            writer.writerow({col: res[col] for col in CSV_COLUMNS})
                            csv_file.flush()

                            if (
                                problema == "hamiltonian"
                                and res["mean_val"] is not None
                                and res["status"] in ("OK", "PARCIAL_90S")
                            ):
                                best_viable_bt[(scenario, lang)] = (n, float(res["mean_val"]))

                            if res["status"] in ("TIMEOUT", "ERRO"):
                                stopped_runners.add(lang)
                    finally:
                        clear_live()
                        clean_instance_files(graph_dir)

    print_backtracking_summary(best_viable_bt)


if __name__ == "__main__":
    main()
