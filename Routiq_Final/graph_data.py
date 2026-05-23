from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

import networkx as nx


DATA_FILE = Path(__file__).with_name("data").joinpath("india_cities.json")


@lru_cache(maxsize=1)
def load_city_records() -> List[dict[str, float | str]]:
    """Load the city dataset from disk.

    The file is external so the graph can scale to a much larger India-wide
    dataset without rewriting the planner code.
    """
    if DATA_FILE.exists():
        with DATA_FILE.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        cities = payload.get("cities", [])
        if not isinstance(cities, list) or not cities:
            raise ValueError("india_cities.json must contain a non-empty 'cities' list")
        return cities

    return [
        {"name": "Delhi", "x": 77.209, "y": 28.613},
        {"name": "Mumbai", "x": 72.878, "y": 19.076},
        {"name": "Bengaluru", "x": 77.594, "y": 12.971},
        {"name": "Chennai", "x": 80.270, "y": 13.082},
    ]


@lru_cache(maxsize=1)
def _city_positions() -> Dict[str, Tuple[float, float]]:
    positions: Dict[str, Tuple[float, float]] = {}
    for record in load_city_records():
        name = str(record["name"])
        positions[name] = (float(record["x"]), float(record["y"]))
    return positions


@lru_cache(maxsize=1)
def _positions_list() -> List[Tuple[str, Tuple[float, float]]]:
    return list(_city_positions().items())


def _distance_between(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return round(math.dist(a, b), 3)


def _connect_nearest_neighbors(
    graph: nx.Graph,
    positions: Dict[str, Tuple[float, float]],
    neighbors_per_node: int = 4,
) -> None:
    city_names = list(positions.keys())
    for city in city_names:
        ranked_neighbors = sorted(
            (
                (other_city, _distance_between(positions[city], positions[other_city]))
                for other_city in city_names
                if other_city != city
            ),
            key=lambda item: item[1],
        )

        for neighbor, distance in ranked_neighbors[:neighbors_per_node]:
            if not graph.has_edge(city, neighbor):
                graph.add_edge(city, neighbor, weight=round(distance * 10, 2))


def _ensure_connected(graph: nx.Graph, positions: Dict[str, Tuple[float, float]]) -> None:
    while not nx.is_connected(graph):
        components = [list(component) for component in nx.connected_components(graph)]
        if len(components) < 2:
            return

        left_component = components[0]
        right_component = components[1]

        best_pair: Tuple[str, str] | None = None
        best_distance = float("inf")

        for left_city in left_component:
            for right_city in right_component:
                distance = _distance_between(positions[left_city], positions[right_city])
                if distance < best_distance:
                    best_distance = distance
                    best_pair = (left_city, right_city)

        if best_pair is None:
            return

        source, target = best_pair
        graph.add_edge(source, target, weight=round(best_distance * 10, 2))


def build_graph() -> nx.Graph:
    """Create a connected weighted graph for the Indian city dataset."""
    graph = nx.Graph()
    positions = _city_positions()

    for city, position in positions.items():
        graph.add_node(city, pos=position)

    _connect_nearest_neighbors(graph, positions)
    _ensure_connected(graph, positions)
    return graph


def get_city_names() -> List[str]:
    return list(_city_positions().keys())


def get_heuristic_values(goal: str) -> Dict[str, float]:
    """Return heuristic values using straight-line distance to the goal city."""
    positions = _city_positions()
    if goal not in positions:
        raise ValueError(f"Unknown goal city: {goal}")

    goal_x, goal_y = positions[goal]
    heuristic_values: Dict[str, float] = {}

    for city, (x_coord, y_coord) in positions.items():
        heuristic_values[city] = round(math.dist((x_coord, y_coord), (goal_x, goal_y)), 3)

    return heuristic_values


def heuristic_for(city: str, goal: str) -> float:
    return get_heuristic_values(goal)[city]


CITY_POSITIONS = _city_positions()
