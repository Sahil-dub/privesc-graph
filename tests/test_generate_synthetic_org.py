import pytest

from src.generate_synthetic_org import generate_synthetic_org


def test_generate_synthetic_org_includes_admin_role() -> None:
    org = generate_synthetic_org(
        org_name="test_org",
        identity_count=3,
        escalation_density=0.25,
        seed=42,
    )

    assert org["org_name"] == "test_org"
    assert org["admin_node"] == "role/AdminRole"
    assert org["identity_count"] == 4

    admin_identity = org["identities"][0]

    assert admin_identity["name"] == "AdminRole"
    assert admin_identity["type"] == "role"
    assert admin_identity["policy"]["Statement"][0]["Action"] == ["*"]


def test_generate_synthetic_org_creates_requested_number_of_identities() -> None:
    org = generate_synthetic_org(
        org_name="test_org",
        identity_count=10,
        escalation_density=0.2,
        seed=42,
    )

    assert len(org["identities"]) == 11
    assert org["identity_count"] == 11


def test_generate_synthetic_org_is_repeatable_with_same_seed() -> None:
    first_org = generate_synthetic_org(
        org_name="test_org",
        identity_count=5,
        escalation_density=0.4,
        seed=123,
    )
    second_org = generate_synthetic_org(
        org_name="test_org",
        identity_count=5,
        escalation_density=0.4,
        seed=123,
    )

    assert first_org == second_org


@pytest.mark.parametrize("invalid_density", [-0.1, 1.1])
def test_generate_synthetic_org_rejects_invalid_escalation_density(
    invalid_density: float,
) -> None:
    with pytest.raises(ValueError, match="escalation_density must be between 0 and 1"):
        generate_synthetic_org(
            org_name="test_org",
            identity_count=5,
            escalation_density=invalid_density,
            seed=42,
        )