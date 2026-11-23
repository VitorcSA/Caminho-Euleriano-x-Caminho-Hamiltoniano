def is_odd(n: int) -> bool:
    return (n % 2) == 1

def vertex_cnt(graph: list[list[int]],init: int) -> int:
    path = [init]
    stack = [init]
    while stack:
        vertex = stack.pop()
        for next in graph[vertex]:
            if next not in path:
                path.append(next)
                stack.append(next)
    return len(path)
    
def is_bridge(graph: list[list[int]],u: int,v: int):
    before = vertex_cnt(graph,u)
    
    graph[u].remove(v)
    graph[v].remove(u)
    
    after = vertex_cnt(graph,u)
    
    graph[u].append(v)
    graph[v].append(u)
    
    return after < before
    

def fleury(graph: list[list[int]]) -> list[int]:
    start = next((i for i, adj in enumerate(graph) if adj), 0)
    for i in range(len(graph)):
        if is_odd(len(graph[i])):
            start = i
            break

    path = [start]
    vertex = path[-1]
    while graph[vertex]:
        for nxt in list(graph[vertex]):
            if not is_bridge(graph,vertex,nxt):
                graph[nxt].remove(vertex)
                graph[vertex].remove(nxt)
                path.append(nxt)
                vertex = nxt
                break
        else:
            nxt = graph[vertex].pop()
            graph[nxt].remove(vertex)
            path.append(nxt)
            vertex = nxt

    return path
