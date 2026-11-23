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

def backtracking_dp(graph: list[list[int]]) -> list[int] | None:
    path = []
    failed = []
    for init in range(len(graph)):
        path.append(init)
        if handle_dp(graph,init,path,failed) < 0:
            path.pop()
            continue
        return path
    else:
        return None

def handle_dp(graph: list[list[int]],vertex: int,path: list[int],failed: list) -> int:
    if len(path) == len(graph):
        return 0
    state = (sorted(path),vertex)
    if state in failed:
        return -1
    for nxt in graph[vertex]:
        if nxt in path:
            continue
        path.append(nxt)
        if handle_dp(graph,nxt,path,failed) < 0:
            path.pop()
            continue
        return 0
    else:
        failed.append(state)
        return -1

