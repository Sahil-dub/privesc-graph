from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

from faker import Faker

ESCALATION_ACTION_SETS = [
    ["iam:AttachUserPolicy"],
    ["iam:PutUserPolicy"],
    ["iam:AttachRolePolicy"],
    ["iam:PutRolePolicy"],
    ["iam:AddUserToGroup"],
    ["iam:CreatePolicyVersion"],
    ["iam:SetDefaultPolicyVersion"],
    ["iam:CreateAccessKey"],
    ["iam:CreateLoginProfile"],
    ["sts:AssumeRole"],
    ["iam:PassRole", "lambda:CreateFunction"],
    ["iam:PassRole", "ec2:RunInstances"],
    ["lambda:UpdateFunctionCode"],
]

SAFE_ACTION_SETS = [
    ["s3:GetObject", "s3:ListBucket"],
    ["cloudwatch:GetMetricData", "cloudwatch:ListMetrics"],
    ["logs:DescribeLogGroups", "logs:GetLogEvents"],
    ["ec2:DescribeInstances", "ec2:DescribeSecurityGroups"],
    ["iam:GetUser", "iam:ListGroupsForUser"],
]

DEFAULT_OUTPUT_DIR = Path("data/synthetic_policies")


def build_policy_document(actions: list[str], resource: str = "*") -> dict[str, Any]:
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": actions,
                "Resource": resource,
            }
        ],
    }


def build_identity(
    name: str,
    identity_type: str,
    actions: list[str],
    is_escalation_capable: bool,
) -> dict[str, Any]:
    return {
        "name": name,
        "type": identity_type,
        "arn": f"arn:aws:iam::123456789012:{identity_type}/{name}",
        "is_escalation_capable": is_escalation_capable,
        "policy": build_policy_document(actions),
    }


def generate_synthetic_org(
    org_name: str,
    identity_count: int,
    escalation_density: float,
    seed: int | None = None,
) -> dict[str, Any]:
    if not 0 <= escalation_density <= 1:
        raise ValueError("escalation_density must be between 0 and 1")

    fake = Faker()
    if seed is not None:
        random.seed(seed)
        Faker.seed(seed)

    identities = []

    admin_role = build_identity(
        name="AdminRole",
        identity_type="role",
        actions=["*"],
        is_escalation_capable=False,
    )
    identities.append(admin_role)

    for index in range(identity_count):
        identity_type = random.choice(["user", "role", "group"])
        readable_name = fake.unique.user_name().replace(".", "_")
        name = f"{identity_type}_{readable_name}_{index}"

        is_escalation_capable = random.random() < escalation_density
        action_pool = ESCALATION_ACTION_SETS if is_escalation_capable else SAFE_ACTION_SETS
        actions = random.choice(action_pool)

        identities.append(
            build_identity(
                name=name,
                identity_type=identity_type,
                actions=actions,
                is_escalation_capable=is_escalation_capable,
            )
        )

    return {
        "org_name": org_name,
        "admin_node": "role/AdminRole",
        "identity_count": len(identities),
        "escalation_density": escalation_density,
        "identities": identities,
    }


def write_org_file(org: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{org['org_name'].lower().replace(' ', '_')}.json"
    output_path = output_dir / filename

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(org, file, indent=2)

    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a synthetic AWS-style IAM organization."
    )
    parser.add_argument("--org-name", default="demo_org")
    parser.add_argument("--identity-count", type=int, default=20)
    parser.add_argument("--escalation-density", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    org = generate_synthetic_org(
        org_name=args.org_name,
        identity_count=args.identity_count,
        escalation_density=args.escalation_density,
        seed=args.seed,
    )
    output_path = write_org_file(org, args.output_dir)

    print(f"Wrote synthetic org to {output_path}")


if __name__ == "__main__":
    main()