import networkx as nx

from src.graph_builder import (
    build_permission_graph,
    extract_allowed_actions,
    rule_matches_identity,
)


def test_extract_allowed_actions_ignores_denied_actions() -> None:
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["iam:PassRole", "lambda:CreateFunction"],
                "Resource": "*",
            },
            {
                "Effect": "Deny",
                "Action": "iam:AttachUserPolicy",
                "Resource": "*",
            },
        ],
    }

    assert extract_allowed_actions(policy) == {"iam:PassRole", "lambda:CreateFunction"}


def test_rule_matches_identity_when_all_required_actions_are_allowed() -> None:
    rule = {
        "required_actions": ["iam:PassRole", "lambda:CreateFunction"],
    }
    allowed_actions = {"iam:PassRole", "lambda:CreateFunction", "s3:ListBucket"}

    assert rule_matches_identity(rule, allowed_actions)


def test_rule_does_not_match_when_required_action_is_missing() -> None:
    rule = {
        "required_actions": ["iam:PassRole", "lambda:CreateFunction"],
    }
    allowed_actions = {"iam:PassRole"}

    assert not rule_matches_identity(rule, allowed_actions)


def test_build_permission_graph_adds_escalation_edge() -> None:
    org = {
        "org_name": "test_org",
        "admin_node": "role/AdminRole",
        "identity_count": 2,
        "escalation_density": 0.5,
        "identities": [
            {
                "name": "AdminRole",
                "type": "role",
                "arn": "arn:aws:iam::123456789012:role/AdminRole",
                "policy": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["*"],
                            "Resource": "*",
                        }
                    ],
                },
            },
            {
                "name": "dev_user",
                "type": "user",
                "arn": "arn:aws:iam::123456789012:user/dev_user",
                "policy": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["iam:PassRole", "lambda:CreateFunction"],
                            "Resource": "*",
                        }
                    ],
                },
            },
        ],
    }
    escalation_rules = {
        "rules": [
            {
                "id": "pass_role_to_lambda",
                "name": "Pass a privileged role to a Lambda function",
                "category": "service_role_abuse",
                "required_actions": ["iam:PassRole", "lambda:CreateFunction"],
                "severity": "critical",
                "edge_label": "can_pass_role_to_lambda",
            }
        ]
    }

    graph = build_permission_graph(org, escalation_rules)

    assert isinstance(graph, nx.DiGraph)
    assert graph.has_node("user/dev_user")
    assert graph.has_node("role/AdminRole")
    assert graph.has_edge("user/dev_user", "role/AdminRole")

    edge_data = graph["user/dev_user"]["role/AdminRole"]

    assert edge_data["rule_id"] == "pass_role_to_lambda"
    assert edge_data["severity"] == "critical"


def test_build_permission_graph_does_not_add_edge_for_safe_identity() -> None:
    org = {
        "org_name": "test_org",
        "admin_node": "role/AdminRole",
        "identity_count": 2,
        "escalation_density": 0.0,
        "identities": [
            {
                "name": "AdminRole",
                "type": "role",
                "arn": "arn:aws:iam::123456789012:role/AdminRole",
                "policy": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["*"],
                            "Resource": "*",
                        }
                    ],
                },
            },
            {
                "name": "readonly_user",
                "type": "user",
                "arn": "arn:aws:iam::123456789012:user/readonly_user",
                "policy": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["s3:GetObject", "s3:ListBucket"],
                            "Resource": "*",
                        }
                    ],
                },
            },
        ],
    }
    escalation_rules = {
        "rules": [
            {
                "id": "pass_role_to_lambda",
                "name": "Pass a privileged role to a Lambda function",
                "category": "service_role_abuse",
                "required_actions": ["iam:PassRole", "lambda:CreateFunction"],
                "severity": "critical",
                "edge_label": "can_pass_role_to_lambda",
            }
        ]
    }

    graph = build_permission_graph(org, escalation_rules)

    assert not graph.has_edge("user/readonly_user", "role/AdminRole")