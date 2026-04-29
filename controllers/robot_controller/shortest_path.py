import json
import os
from collections import deque

# Down below is a function implemented to find the shortest path using a breadth-first aproach
# A path is the shortest if it has the least number of edges in between, as the nodes are in a grid
#   We start by creating an adjacency list
#   Then we start the BFS
#     The queue contains all paths that we still need to search, bfs searches first all paths of length 1 , then all of length 2, etc...
#     We ppop the path, if the last node is the endpoint, we return the path. Otherwise we add all the neighbours that arent' marked visited and now mark then visited

# The BFS search gives one possible best path, there can be multiple. It is possible to adjust the algorithm so we prefer to keep moving in the same direction (fewer turns)
# or to prefer keep moving allong the "highway" in the middle of the warehouse. Or add driving rules (stay right etc...)
# These are optimalizations for later #TODO

def shortest_path(nodes, obstructed_nodes, edges, start_node, end_node):
    adj = { node: [] for node in nodes }
    for u, v in edges:
        adj[u].append(v)

    queue = deque([[start_node]])
    visited = { start_node}

    while queue:
        path = queue.popleft()
        current = path[-1]

        if current == end_node:
            return path

        for neighbor in adj[current]:
            if neighbor not in visited and neighbor not in obstructed_nodes:
                visited.add(neighbor)
                new_path = list(path)
                new_path.append(neighbor)
                queue.append(new_path)
    
    return None

# Test code:
if __name__ == "__main__":
    # Load data
    data_path = os.path.join(os.path.dirname(__file__), "map.json")
    with open(data_path, "r") as f:
        data = json.load(f)

    # Run function
    test_path = shortest_path(data["nodes"], data["edges"], "Droppoff_1", "Entrance_2_4")
    print(f"Path: {test_path}") # Expect: "Path: ['Droppoff_1', 'A1', 'B1', 'C1', 'D1', 'E1', 'E2', 'Entrance_2_4']"