# Caminho-Euleriano-x-Caminho-Hamiltoniano

Comparação entre algoritmos que resolvem o problema dos caminhos eulerianos (**Hierholzer**) e o problema dos caminhos hamiltonianos (**Backtracking**), implementados em **C** e em **Python**.

Este documento explica como compilar o projeto, validar as implementações e reproduzir os resultados do benchmark (`resultados.csv`).

---

## Estrutura do repositório

```
.
├── C/
│   ├── main.c                      # executável do benchmark (mede só o tempo do algoritmo)
│   ├── lib/cJSON.{c,h}             # parser JSON
│   └── algorithm/
│       ├── graph.{c,h}             # lista de adjacência com id de aresta
│       ├── list.{c,h}              # vetor dinâmico de int
│       ├── eulerian/hierholzer.{c,h}
│       └── hamiltonian/backtracking.{c,h}
├── python/
│   ├── main.py                     # benchmark em Python (mesma interface do binário C)
│   └── algorithm/
│       ├── eulerian/hierholzer.py
│       └── hamiltonian/backtracking.py
├── test/
│   ├── main.c                      # imprime os caminhos encontrados (C)  -> test/test_runner
│   └── main.py                     # imprime os caminhos encontrados (Python)
├── test.py                         # compara a saída de C e Python para um grafo
├── script.py                       # gera os grafos, roda o benchmark e escreve resultados.csv
└── README.md
```

## Requisitos

| Item | Versão |
|------|--------|
| GCC (ou outro compilador C compatível) | com suporte a `clock_gettime` (Linux/macOS) |
| Python | **3.10+** (usa a sintaxe `list[int] \| None`) |
| Bibliotecas Python | apenas a biblioteca padrão |
| SO | Linux (testado); macOS deve funcionar; no Windows use WSL |

Não há dependências externas: o cJSON já está em `C/lib/`.

## 1. Compilar

Execute **na raiz do repositório** (os nomes e caminhos dos binários são esperados exatamente assim pelos scripts).

```bash
SRC="C/lib/cJSON.c C/algorithm/graph.c C/algorithm/list.c \
     C/algorithm/eulerian/hierholzer.c C/algorithm/hamiltonian/backtracking.c"

# Binário do benchmark (usado por script.py)
gcc -O2 -o grafo_bench C/main.c $SRC -lm

# Binário de teste de corretude (usado por test.py)
gcc -O2 -o test/test_runner test/main.c $SRC -lm
```

> O nível de otimização `-O2` é uma sugestão; use sempre o mesmo nível ao comparar execuções. Pode aparecer um aviso sobre `list_remove` sem `return` — ele não é usado e não afeta os resultados.

## 2. Formato da entrada

Os grafos são **não direcionados**, em JSON, como lista de adjacência: a posição `i` contém os vizinhos do vértice `i`. A lista deve ser simétrica (se `1` está na lista de `0`, então `0` está na lista de `1`).

```json
[[1, 2], [0, 2, 3], [0, 1], [1]]
```

Os dois programas ignoram vizinhos menores que `i` ao ler o arquivo, então cada aresta é criada uma única vez.

## 3. Validar as implementações (C × Python)

Antes do benchmark, confirme que as versões em C e Python produzem exatamente a mesma saída:

```bash
python3 test.py caminho/do/grafo.json
```

Exemplo com um triângulo (`[[1,2],[0,2],[0,1]]`):

```
[SUCESSO] Hierholzer     C: [0, 1, 2, 0]   Python: [0, 1, 2, 0]
[SUCESSO] Backtracking   C: [0, 1, 2]      Python: [0, 1, 2]
[OK] Saídas idênticas para 'grafo.json'
```

Cada linha de saída do runner é um caminho: a primeira é o circuito de Hierholzer, a segunda é o caminho hamiltoniano (lista vazia `[]` se não existir).

## 4. Rodar um único experimento manualmente

Ambos os executáveis têm a mesma interface: `<modo> <arquivo.json>`, onde `modo` é `eulerian` ou `hamiltonian`. A saída é o tempo do algoritmo em **milissegundos** (a leitura do JSON e a construção do grafo não entram na medição).

```bash
# C
./grafo_bench eulerian    caminho/do/grafo.json
./grafo_bench hamiltonian caminho/do/grafo.json

# Python (precisa rodar de dentro de python/ por causa dos imports)
cd python
python3 main.py eulerian    ../caminho/do/grafo.json
python3 main.py hamiltonian ../caminho/do/grafo.json
```

## 5. Reproduzir o benchmark completo

Depois de compilar `grafo_bench` (seção 1):

```bash
python3 script.py
```

O script faz, para cada problema, cenário e tamanho `n`:

1. gera 20 grafos aleatórios em `graph/eulerian/` ou `graph/hamiltonian/` (arquivos `inst_XX.json`, apagados ao final de cada lote);
2. executa 2 rodadas de aquecimento;
3. executa as 20 instâncias em C e em Python, registrando média e desvio padrão;
4. grava uma linha em `resultados.csv` e mostra o progresso no terminal.

Ao final imprime um resumo com o **maior `n` viável (até 60 s)** do Backtracking por cenário e linguagem.

### Parâmetros do experimento

Definidos no topo de `script.py`:

| Parâmetro | Valor |
|-----------|-------|
| `SEED` | 42 (geração dos grafos determinística) |
| `REPETITIONS` | 20 instâncias por `n` |
| `WARMUP_ROUNDS` | 2 (a segunda é pulada se a primeira levar > 5 s) |
| `TIMEOUT_SECONDS` | 60 s por execução (status `TIMEOUT`) |
| `SLOW_BLOCK_LIMIT_SECONDS` | 90 s acumulados no lote → para com status `PARCIAL_90S` (após ≥ 3 repetições) |
| Hierholzer — `n` | 100; 1.000; 10.000; 50.000; 100.000; 500.000; 1.000.000 |
| Backtracking — `n` | 10, 12, 14, …, 34 |
| Cenários | `melhor`, `medio`, `pior` |

Se uma linguagem estoura o tempo (`TIMEOUT`) ou falha (`ERRO`) em um `n`, ela é removida dos tamanhos maiores daquele cenário.

### Cenários

- **Hierholzer:** todos partem de um ciclo aleatório (grau par em todos os vértices). `melhor` = apenas o ciclo; `medio` = ciclo + triângulos aleatórios (~2,0–2,6·n arestas); `pior` = triângulos concentrados em vértices "pivô" (~6,5–8,5·n arestas, limitado a 45% do grafo completo).
- **Backtracking:** `melhor` = existe ciclo hamiltoniano e ele é o primeiro vizinho de cada lista; `medio` = árvore aleatória + arestas extras (~1,3–1,7·n); `pior` = grafo densificado construído para dificultar a busca (conjunto `A` de `n/2 − 1` vértices conectado ao resto, sem ciclo hamiltoniano).

### Saída: `resultados.csv`

| Coluna | Descrição |
|--------|-----------|
| `linguagem` | `C` ou `Python` |
| `problema` / `algoritmo` | `eulerian` / `Hierholzer` ou `hamiltonian` / `Backtracking` |
| `cenario` | `melhor`, `medio` ou `pior` |
| `n`, `m` | vértices e média de arestas das 20 instâncias |
| `media_ms`, `desvio_padrao_ms` | estatísticas do tempo do algoritmo |
| `repeticoes` | repetições efetivamente concluídas |
| `status` | `OK`, `PARCIAL_90S`, `TIMEOUT` ou `ERRO` |

## Dicas e avisos para reprodução

- **Tempo total:** a execução completa pode levar de dezenas de minutos a várias horas, dependendo da máquina, principalmente por causa dos tamanhos grandes do Hierholzer e dos timeouts de 60 s do Backtracking.
- **Disco e memória:** com `n = 1.000.000` no cenário `pior` do Hierholzer cada instância tem milhões de arestas (arquivos JSON de centenas de MB), e as 20 instâncias do lote ficam no disco ao mesmo tempo. Reserve alguns GB livres e memória suficiente; se necessário, remova `500_000` e `1_000_000` de `HIERHOLZER_SIZES`.
- **Mesmas instâncias, tempos diferentes:** a semente fixa garante os mesmos grafos, mas os tempos absolutos dependem de CPU, SO e carga da máquina. Para comparar bem, feche outros programas, mantenha a máquina na tomada e use sempre a mesma flag de otimização. O que deve se reproduzir é a **tendência** (crescimento por `n`, C vs. Python, melhor/médio/pior caso), não os valores exatos.
- **Interromper e continuar:** o CSV é reescrito a cada execução de `script.py` (`mode="w"`); copie `resultados.csv` antes de rodar de novo se quiser preservá-lo.
- **Erros de import no Python:** `python/main.py` deve ser executado de dentro de `python/` (o `script.py` já faz isso); `test/main.py` deve ser executado da raiz com `PYTHONPATH=.` (o `test.py` já faz isso).
