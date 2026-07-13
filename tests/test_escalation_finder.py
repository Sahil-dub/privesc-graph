import networkx as nx

from src.escalation_finder import (
    find_paths_to_admin,
    find_shortest_paths_to_admin,
    summarize_escalation_paths,
)


def test_find_paths_to_admin_returns_direct_path() -> None:
    graph = nx.DiGraph()
    graph.add_edge("user/dev_user", "role/AdminRole")

    paths = find_paths_to_admin(graph, "role/AdminRole")

    assert paths == {
        "user/dev_user": [["user/dev_user", "role/AdminRole"]],
    }


def test_find_paths_to_admin_ignores_nodes_without_admin_path() -> None:
    graph = nx.DiGraph()
    graph.add_node("user/readonly_user")
    graph.add_node("role/AdminRole")

    paths = find_paths_to_admin(graph, "role/AdminRole")

    assert paths == {}


def test_find_shortest_paths_to_admin_prefers_shorter_route() -> None:
    graph = nx.DiGraph()
    graph.add_edge("user/dev_user", "role/intermediate_role")
    graph.add_edge("role/intermediate_role", "role/AdminRole")
    graph.add_edge("user/dev_user", "role/AdminRole")

    shortest_paths = find_shortest_paths_to_admin(graph, "role/AdminRole")

    assert shortest_paths["user/dev_user"] == ["user/dev_user", "role/AdminRole"]


def test_summarize_escalation_paths_reports_path_count_and_shortest_length() -> None:
    graph = nx.DiGraph()
    graph.add_edge("user/dev_user", "role/AdminRole")
    graph.add_edge("user/dev_user", "role/intermediate_role")
    graph.add_edge("role/intermediate_role", "role/AdminRole")

    summaries = summarize_escalation_paths(graph, "role/AdminRole")

    assert summaries == [
        {
            "identity": "user/dev_user",
            "path_count": 2,
            "shortest_path_length": 1,
            "shortest_path": ["user/dev_user", "role/AdminRole"],
        },
        {
            "identity": "role/intermediate_role",
            "path_count": 1,
            "shortest_path_length": 1,
            "shortest_path": ["role/intermediate_role", "role/AdminRole"],
        },
    ]