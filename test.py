import ast
import os
import subprocess
import sys

GREEN = "\033[1;32m"
RED = "\033[1;31m"
RESET = "\033[0m"

def parse_output(stdout: str) -> list[list[int]]:
	lines = stdout.strip().splitlines()
	return [ast.literal_eval(line) for line in lines]

def main():
	if len(sys.argv) < 2:
		print("Uso: python test.py <caminho_do_grafo.json>")
		sys.exit(1)

	path = sys.argv[1]

	env = os.environ.copy()
	env["PYTHONPATH"] = "."

	c = subprocess.run(
		["./test/test_runner",path],
		capture_output= True,
		text=True,
		check=True
	)
	py = subprocess.run(
		[sys.executable, "test/main.py", path],
		capture_output=True,
		text=True,
		env=env,
		check=True
	)

	c_result = parse_output(c.stdout)
	py_result = parse_output(py.stdout)

	algorithms = ["Hierholzer","Backtracking"]
	ok = True

	for i, name in enumerate(algorithms):
		if c_result[i] != py_result[i]:
			print(f"{RED}[FALHA] {name}")
			print(f"C/{algorithms[i]}:{c_result[i]}")
			print(f"Python/{algorithms[i]}:{py_result[i]}{RESET}\n")
			ok = False
			continue
		print(f"{GREEN}[SUCESSO] {name}")
		print(f"C/{algorithms[i]}:{c_result[i]}")
		print(f"Python/{algorithms[i]}:{py_result[i]}{RESET}\n")

	if ok:
		print(f"{GREEN}[OK] Saídas idênticas para '{path}'{RESET}\n")

if __name__ == "__main__":
	main()
