import networkx as nx

from src.risk_model import extract_graph_features


def test_extract_graph_features_for_identity_with_admin_path() -> None:
    graph = nx.DiGraph()
    graph.add_edge("user/dev_user", "role/AdminRole")

    features = extract_graph_features(graph, "role/AdminRole")
    row = features.set_index("identity").loc["user/dev_user"]

    assert row["path_count"] == 1
    assert row["shortest_path_length"] == 1
    assert row["out_degree"] == 1
    assert row["has_admin_path"] == 1


def test_extract_graph_features_includes_identity_without_admin_path() -> None:
    graph = nx.DiGraph()
    graph.add_node("user/readonly_user")
    graph.add_node("role/AdminRole")

    features = extract_graph_features(graph, "role/AdminRole")
    row = features.set_index("identity").loc["user/readonly_user"]

    assert row["path_count"] == 0
    assert row["shortest_path_length"] == 0
    assert row["out_degree"] == 0
    assert row["has_admin_path"] == 0


def test_extract_graph_features_excludes_admin_node() -> None:
    graph = nx.DiGraph()
    graph.add_node("role/AdminRole")

    features = extract_graph_features(graph, "role/AdminRole")

    assert features.empty