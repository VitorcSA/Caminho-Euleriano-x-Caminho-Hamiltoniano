def backtracking(graph: list[list[int]]) -> list[int] | None:
    path = []
    for init in range(len(graph)):
        path.append(init)
        if handle(graph,init,path) < 0:
            path.pop()
            continue
        return path
    else:
        return []

def handle(graph: list[list[int]],vertex: int,path: list[int]) -> int:
    if len(path) == len(graph):
        return 0
    for next in graph[vertex]:
        if next in path:
            continue
        path.append(next)
        if handle(graph,next,path) < 0:
            path.pop()
            continue
        return 0
    else:
        return -1
