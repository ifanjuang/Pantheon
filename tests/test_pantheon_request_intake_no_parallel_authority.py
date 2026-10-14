from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "templates/hermes/skills/pantheon-request-intake/SKILL.md"
POLICY = ROOT / "mcp-server/pantheon_mcp/policy.py"
REQUEST_LIFECYCLE = ROOT / "docs/governance/REQUEST_LIFECYCLE.md"
ROLE_ACTIVATION = ROOT / "docs/governance/ROLE_ACTIVATION.md"


def test_intake_references_existing_owners_instead_of_copying_policy_tables() -> None:
    skill = SKILL.read_text(encoding="utf-8")
    policy = POLICY.read_text(encoding="utf-8")

    assert "docs/governance/REQUEST_LIFECYCLE.md" in skill
    assert "docs/governance/ROLE_ACTIVATION.md" in skill
    assert "mcp-server/docs/HERMES_INTEGRATION_CONTRACT.md" in skill

    # Consequence/verification/approval mappings stay in the Pantheon policy
    # owner. The Hermes adapter must not grow a shadow K/V/C table.
    assert "_K_TO_V" in policy
    assert '"K4": "C3"' in policy
    assert "K0 ->" not in skill
    assert "K1 ->" not in skill
    assert "K2 ->" not in skill
    assert "K3 ->" not in skill
    assert "K4 ->" not in skill

    lifecycle = REQUEST_LIFECYCLE.read_text(encoding="utf-8")
    activation = ROLE_ACTIVATION.read_text(encoding="utf-8")
    assert "Situated clarification is a function, not a Role" in lifecycle
    assert "These are governance-review triggers, not runtime dispatch instructions" in activation
