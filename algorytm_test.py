graph = {0: [1, 2, 3], 1: [0, 2], 2: [0, 1, 4], 3: [0, 4], 4: [3, 2]}
weights = {}
for g in graph:
    w = {}
    for s in graph[g]:
        w[s] = 1
    weights[g] = w

print(weights)

# p = [0, 2, 4]


def calculate_weight(path, weights):
    sum_w = 0

    for p in range(len(path) - 1):
        p_w = weights[path[p]]
        sum_w = sum_w + p_w[path[p + 1]]
    return sum_w


def update_weight(path, weights):
    for p in range(len(path) - 1):
        p_w = weights[path[p]]
        p_w[path[p + 1]] = p_w[path[p + 1]] + 1


# print(calculate_weight(p, weights))
#
# update_weight(p, weights)
#
# print(calculate_weight(p, weights))
# print(weights)

def find_shortest_path(graph, weights, start, end, path=[]):
    path = path + [start]
    if start == end:
        return path
    if start not in graph:
        return None
    shortest = None
    for node in graph[start]:
        if node not in path:
            newpath = find_shortest_path(graph, weights, node, end, path)
            if newpath:

                if not shortest or calculate_weight(newpath, weights) < calculate_weight(shortest, weights):
                    shortest = newpath
    return shortest


print(weights)
for i in range(10):
    result = find_shortest_path(graph, weights, 0, 4)
    print(i)
    print(f'path: {result}')
    update_weight(result, weights)
    print(f'weights: {weights}')
    print("___________________________________________________")
