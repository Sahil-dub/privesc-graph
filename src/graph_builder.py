from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx
import yaml


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_escalation_rules(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def normalize_actions(actions: str | list[str]) -> set[str]:
    if isinstance(actions, str):
        return {actions}

    return set(actions)


def extract_allowed_actions(policy: dict[str, Any]) -> set[str]:
    allowed_actions: set[str] = set()

    statements = policy.get("Statement", [])
    if isinstance(statements, dict):
        statements = [statements]

    for statement in statements:
        if statement.get("Effect") != "Allow":
            continue

        actions = statement.get("Action", [])
        allowed_actions.update(normalize_actions(actions))

    return allowed_actions


def identity_node_id(identity: dict[str, Any]) -> str:
    return f"{identity['type']}/{identity['name']}"


def action_matches(required_action: str, allowed_actions: set[str]) -> bool:
    if "*" in allowed_actions:
        return True

    service = required_action.split(":", maxsplit=1)[0]
    service_wildcard = f"{service}:*"

    return required_action in allowed_actions or service_wildcard in allowed_actions


def rule_matches_identity(rule: dict[str, Any], allowed_actions: set[str]) -> bool:
    required_actions = rule.get("required_actions", [])

    return all(
        action_matches(required_action, allowed_actions)
        for required_action in required_actions
    )


def build_permission_graph(
    org: dict[str, Any],
    escalation_rules: dict[str, Any],
) -> nx.DiGraph:
    graph = nx.DiGraph()

    admin_node = org["admin_node"]
    graph.add_node(admin_node, node_type="admin_target", is_admin=True)

    for identity in org["identities"]:
        node_id = identity_node_id(identity)
        allowed_actions = extract_allowed_actions(identity["policy"])

        graph.add_node(
            node_id,
            node_type=identity["type"],
            name=identity["name"],
            arn=identity["arn"],
            allowed_actions=sorted(allowed_actions),
            is_admin=node_id == admin_node,
        )

        for rule in escalation_rules["rules"]:
            if not rule_matches_identity(rule, allowed_actions):
                continue

            graph.add_edge(
                node_id,
                admin_node,
                rule_id=rule["id"],
                technique=rule["name"],
                category=rule["category"],
                severity=rule["severity"],
                edge_label=rule["edge_label"],
            )

    return graph


def build_graph_from_files(
    org_path: Path,
    rules_path: Path,
) -> nx.DiGraph:
    org = load_json(org_path)
    escalation_rules = load_escalation_rules(rules_path)

    return build_permission_graph(org, escalation_rules)


def main() -> None:
    org_path = Path("data/synthetic_policies/small_demo.json")
    rules_path = Path("data/escalation_rules.yaml")

    graph = build_graph_from_files(org_path, rules_path)

    print(f"Built graph with {graph.number_of_nodes()} nodes")
    print(f"Built graph with {graph.number_of_edges()} escalation edges")


if __name__ == "__main__":
    main()