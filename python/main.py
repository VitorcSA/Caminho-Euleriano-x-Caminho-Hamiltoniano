import json
import time
import sys
from algorithm.eulerian.hierholzer import hierholzer
from algorithm.hamiltonian.backtracking import backtracking

def to_hierholzer(graph: list[list[int]]) -> list[list[tuple[int,int]]]:
	edge_cont = 0
	result = [[] for i in graph]

	used = set()
	for i, neighbors in enumerate(graph):
		for k in neighbors:
			if k < i:
				continue

			result[i].append((k,edge_cont))
			if i != k:
				result[k].append((i,edge_cont))

			edge_cont += 1

	return result

if __name__ == "__main__":
	mode = sys.argv[1]
	path = sys.argv[2]

	with open(path,"r",encoding="utf-8") as f:
		raw = json.load(f)

	if mode == "eulerian":
		graph = to_hierholzer(raw)
		t0 = time.perf_counter()
		hierholzer(graph)
		t1 = time.perf_counter()
	else:
		graph = raw
		t0 = time.perf_counter()
		backtracking(graph)
		t1 = time.perf_counter()

	print(f"{(t1-t0) * 1000.0}")
