"""NetworkX-based priority-aware repair-route approximation."""
from math import asin, cos, radians, sin, sqrt

import networkx as nx
from networkx.algorithms.approximation import greedy_tsp


def distance_km(a, b):
    lat1, lon1, lat2, lon2 = map(radians, [a[0], a[1], b[0], b[1]])
    return 2 * 6371 * asin(sqrt(sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2))


def plan_route(defects, depot, max_repairs):
    selected = sorted(defects, key=lambda item: item["priority_score"], reverse=True)[:max_repairs]
    graph = nx.complete_graph(len(selected) + 1)
    positions = {0: depot}
    for index, defect in enumerate(selected, start=1):
        positions[index] = (defect["latitude"], defect["longitude"])
    for source, target in graph.edges:
        graph[source][target]["weight"] = distance_km(positions[source], positions[target])
    cycle = greedy_tsp(graph, weight="weight", source=0)
    ordered_indices = [node for node in cycle[1:-1] if node != 0]
    ordered = [selected[index - 1] for index in ordered_indices]
    points = [positions[node] for node in cycle]
    total = sum(distance_km(a, b) for a, b in zip(points, points[1:]))
    available = sum(item["priority_score"] for item in defects) or 1
    return {
        "algorithm": "NetworkX greedy TSP approximation",
        "depot": depot,
        "stops": ordered,
        "points": points,
        "distance_km": total,
        "priority_coverage": sum(item["priority_score"] for item in selected) / available * 100,
    }
