from __future__ import annotations

from typing import Any

import networkx as nx
import pandas as pd

from src.escalation_finder import find_paths_to_admin, find_shortest_paths_to_admin


def extract_graph_features(
    graph: nx.DiGraph,
    admin_node: str,
) -> pd.DataFrame:
    paths_by_identity = find_paths_to_admin(graph, admin_node)
    shortest_paths = find_shortest_paths_to_admin(graph, admin_node)
    betweenness = nx.betweenness_centrality(graph)

    rows: list[dict[str, Any]] = []

    for node in graph.nodes:
        if node == admin_node:
            continue

        paths = paths_by_identity.get(node, [])
        shortest_path = shortest_paths.get(node)

        rows.append(
            {
                "identity": node,
                "path_count": len(paths),
                "shortest_path_length": (
                    len(shortest_path) - 1 if shortest_path is not None else 0
                ),
                "out_degree": graph.out_degree(node),
                "betweenness_centrality": betweenness[node],
                "has_admin_path": int(node in paths_by_identity),
            }
        )

    return pd.DataFrame(rows)