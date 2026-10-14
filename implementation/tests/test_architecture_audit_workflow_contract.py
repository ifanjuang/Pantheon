from __future__ import annotations

from pathlib import Path

import yaml


IMPLEMENTATION_ROOT = Path(__file__).resolve().parents[1]
MONOREPO_ROOT = IMPLEMENTATION_ROOT.parent
WORKFLOW = MONOREPO_ROOT / ".github" / "workflows" / "implementation-architecture-audit.yml"
AUTHORITY_REF = "c335f5784cec005c1cf93e52b0b22ad4afce3442"


def test_architecture_audit_pins_reviewed_logical_ownership_registry() -> None:
    raw = WORKFLOW.read_text(encoding="utf-8")
    workflow = yaml.safe_load(raw)
    job = workflow["jobs"]["report"]

    assert job["env"]["PANTHEON_AUDIT_AUTHORITY_REF"] == AUTHORITY_REF
    assert "docs/governance/authority/PANTHEON_SYSTEM_OWNERSHIP_REGISTRY.json" in raw
    assert 'governance-core=governance=Pantheon governance=' in raw
    assert 'implementation=implementation=Pantheon implementation=' in raw


def test_active_audit_does_not_use_repository_names_as_owner_identities() -> None:
    raw = WORKFLOW.read_text(encoding="utf-8")

    assert "=governance=Pantheon-Next=" not in raw
    assert "=implementation=pantheon-mvp=" not in raw
    assert "--zone governance-core=governance=Pantheon-Next" not in raw
    assert "--zone implementation=implementation=pantheon-mvp" not in raw
