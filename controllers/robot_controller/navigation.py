import json
import os
from shortest_path import shortest_path


def load_map(map_path=None):
    if map_path is None:
        map_path = os.path.join(os.path.dirname(__file__), "map.json")
    with open(map_path, "r") as f:
        data = json.load(f)
    return data["nodes"], data["edges"]


def get_route(nodes, edges, current_node, obstructed_nodes, end_node):
    route = shortest_path(nodes, obstructed_nodes, edges, current_node, end_node)
    print(f"Path: {route}")
    return route
