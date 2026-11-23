def hierholzer(graph: list[list[tuple[int,int]]]):
    start = next((i for i in range(len(graph)) if graph[i]),-1)
    used = set()
    stack, circuit = [], []
    if start >= 0:
        stack.append(start)

    while stack:
        u = stack[-1]
        while graph[u]:
            w, eid = graph[u].pop()
            if eid not in used:
                used.add(eid)
                stack.append(w)
                break
        else:
            circuit.append(stack.pop())

    return circuit
