from __future__ import annotations

from typing import Any

import networkx as nx


def find_paths_to_admin(
    graph: nx.DiGraph,
    admin_node: str,
    max_path_length: int | None = None,
) -> dict[str, list[list[str]]]:
    paths_by_identity: dict[str, list[list[str]]] = {}

    for node in graph.nodes:
        if node == admin_node:
            continue

        if not nx.has_path(graph, node, admin_node):
            continue

        cutoff = max_path_length
        paths = list(nx.all_simple_paths(graph, node, admin_node, cutoff=cutoff))

        if paths:
            paths_by_identity[node] = paths

    return paths_by_identity


def find_shortest_paths_to_admin(
    graph: nx.DiGraph,
    admin_node: str,
) -> dict[str, list[str]]:
    shortest_paths: dict[str, list[str]] = {}

    for node in graph.nodes:
        if node == admin_node:
            continue

        if not nx.has_path(graph, node, admin_node):
            continue

        shortest_paths[node] = nx.shortest_path(graph, node, admin_node)

    return shortest_paths


def summarize_escalation_paths(
    graph: nx.DiGraph,
    admin_node: str,
) -> list[dict[str, Any]]:
    paths_by_identity = find_paths_to_admin(graph, admin_node)
    shortest_paths = find_shortest_paths_to_admin(graph, admin_node)

    summaries = []

    for identity, paths in paths_by_identity.items():
        shortest_path = shortest_paths[identity]

        summaries.append(
            {
                "identity": identity,
                "path_count": len(paths),
                "shortest_path_length": len(shortest_path) - 1,
                "shortest_path": shortest_path,
            }
        )

    return sorted(
        summaries,
        key=lambda summary: (
            summary["shortest_path_length"],
            -summary["path_count"],
            summary["identity"],
        ),
    )