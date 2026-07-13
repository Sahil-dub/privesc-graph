import networkx as nx
import pandas as pd

from src.risk_model import extract_graph_features, score_identity_risk


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

def test_score_identity_risk_keeps_no_path_at_zero() -> None:
    features = pd.DataFrame(
        [
            {
                "identity": "user/readonly_user",
                "path_count": 0,
                "shortest_path_length": 0,
                "out_degree": 0,
                "betweenness_centrality": 0.0,
                "has_admin_path": 0,
            }
        ]
    )

    scored = score_identity_risk(features)

    assert scored.loc[0, "identity"] == "user/readonly_user"
    assert scored.loc[0, "risk_score"] == 0


def test_score_identity_risk_scores_direct_admin_path_above_zero() -> None:
    features = pd.DataFrame(
        [
            {
                "identity": "user/dev_user",
                "path_count": 1,
                "shortest_path_length": 1,
                "out_degree": 1,
                "betweenness_centrality": 0.0,
                "has_admin_path": 1,
            }
        ]
    )

    scored = score_identity_risk(features)

    assert scored.loc[0, "identity"] == "user/dev_user"
    assert scored.loc[0, "risk_score"] > 0


def test_score_identity_risk_sorts_highest_risk_first() -> None:
    features = pd.DataFrame(
        [
            {
                "identity": "user/readonly_user",
                "path_count": 0,
                "shortest_path_length": 0,
                "out_degree": 0,
                "betweenness_centrality": 0.0,
                "has_admin_path": 0,
            },
            {
                "identity": "user/dev_user",
                "path_count": 2,
                "shortest_path_length": 1,
                "out_degree": 2,
                "betweenness_centrality": 0.0,
                "has_admin_path": 1,
            },
        ]
    )

    scored = score_identity_risk(features)

    assert scored.loc[0, "identity"] == "user/dev_user"
    assert scored.loc[1, "identity"] == "user/readonly_user"

    