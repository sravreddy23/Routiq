from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from typing import Callable, List, Optional, Tuple

import networkx as nx


@dataclass
class RouteResult:
    path: List[str]
    total_cost: float
    visited_nodes: List[str]
    heuristic_trace: List[Tuple[str, float]]


def _reconstruct_path(parents: dict[str, Optional[str]], start: str, goal: str) -> List[str]:
    path = [goal]
    current = goal

    while current != start:
        parent = parents.get(current)
        if parent is None:
            return []
        path.append(parent)
        current = parent

    path.reverse()
    return path


def _calculate_path_cost(graph: nx.Graph, path: List[str]) -> float:
    total_cost = 0.0
    for source, target in zip(path, path[1:]):
        total_cost += float(graph[source][target]["weight"])
    return round(total_cost, 2)


def greedy_best_first_search(
    graph: nx.Graph,
    start: str,
    goal: str,
    heuristic_fn: Callable[[str, str], float],
) -> Optional[RouteResult]:
    """Run Greedy Best First Search using only h(n) for prioritization."""
    if start not in graph:
        raise ValueError(f"Invalid source node: {start}")
    if goal not in graph:
        raise ValueError(f"Invalid destination node: {goal}")
    if start == goal:
        heuristic_value = round(float(heuristic_fn(start, goal)), 2)
        return RouteResult([start], 0.0, [start], [(start, heuristic_value)])

    priority_queue: list[tuple[float, int, str]] = []
    sequence = count()
    parents: dict[str, Optional[str]] = {start: None}
    discovered = {start}
    visited_set = set()
    visited_order: List[str] = []
    heuristic_trace: List[Tuple[str, float]] = []

    heappush(priority_queue, (float(heuristic_fn(start, goal)), next(sequence), start))

    while priority_queue:
        _, _, current = heappop(priority_queue)

        if current in visited_set:
            continue

        visited_set.add(current)
        visited_order.append(current)
        heuristic_trace.append((current, round(float(heuristic_fn(current, goal)), 2)))

        if current == goal:
            path = _reconstruct_path(parents, start, goal)
            if not path:
                return None
            total_cost = _calculate_path_cost(graph, path)
            return RouteResult(path, total_cost, visited_order, heuristic_trace)

        for neighbor in graph.neighbors(current):
            if neighbor in visited_set or neighbor in discovered:
                continue

            parents[neighbor] = current
            discovered.add(neighbor)
            heappush(priority_queue, (float(heuristic_fn(neighbor, goal)), next(sequence), neighbor))

    return None
