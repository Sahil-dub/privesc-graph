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

    def score_identity_risk(features: pd.DataFrame) -> pd.DataFrame:
    scored_features = features.copy()

    if scored_features.empty:
        scored_features["risk_score"] = []
        return scored_features

    scored_features["risk_score"] = 0.0

    has_path = scored_features["has_admin_path"] == 1

    scored_features.loc[has_path, "risk_score"] += 60

    scored_features.loc[has_path, "risk_score"] += (
        20 / scored_features.loc[has_path, "shortest_path_length"]
    )

    scored_features["risk_score"] += scored_features["path_count"].clip(upper=5) * 3
    scored_features["risk_score"] += scored_features["out_degree"].clip(upper=5) * 2
    scored_features["risk_score"] += (
        scored_features["betweenness_centrality"].clip(upper=1.0) * 10
    )

    scored_features["risk_score"] = scored_features["risk_score"].clip(upper=100).round(2)

    return scored_features.sort_values(
        by=["risk_score", "path_count", "identity"],
        ascending=[False, False, True],
    ).reset_index(drop=True)