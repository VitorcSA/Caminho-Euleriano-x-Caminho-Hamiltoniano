import sys
import json
import time
from python.algorithm.eulerian.hierholzer import hierholzer
from python.algorithm.hamiltonian.backtracking import backtracking

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

def main():
	path = sys.argv[1]

	with open(path,"r",encoding="utf-8") as f:
		raw = json.load(f)

	graph = to_hierholzer(raw)
	hierholzer_result = hierholzer(graph)
	t1 = time.perf_counter()

	graph = raw
	backtracking_result = backtracking(graph)

	print(hierholzer_result)
	print(backtracking_result)

if __name__ == "__main__":
	main()
