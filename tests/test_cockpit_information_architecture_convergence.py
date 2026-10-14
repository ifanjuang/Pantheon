"""Regression checks for Cockpit information-architecture convergence."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE = ROOT / "docs" / "governance"
OLD_INFORMATION_ARCHITECTURE = GOVERNANCE / "PANTHEON_COCKPIT_INFORMATION_ARCHITECTURE.md"
STRUCTURED_INTERFACE = GOVERNANCE / "PANTHEON_COCKPIT_STRUCTURED_AGENCY_INTERFACE.md"
KNOWLEDGE_GOVERNANCE = GOVERNANCE / "KNOWLEDGE_INGESTION_AND_MEMORY.md"
DECISION_REQUEST_SCHEMA = ROOT / "schemas" / "decision_request.schema.yaml"
AUTHORITY_INDEX = GOVERNANCE / "authority" / "GOVERNANCE_AUTHORITY_INDEX.md"
NAVIGATION_REGISTRY = (
    ROOT
    / "implementation"
    / "mvp_vertical"
    / "cockpit"
    / "registries"
    / "navigation_registry.json"
)


def test_retired_information_architecture_converges_on_navigation_registry() -> None:
    assert not OLD_INFORMATION_ARCHITECTURE.exists()

    structured = STRUCTURED_INTERFACE.read_text(encoding="utf-8")
    registry = json.loads(NAVIGATION_REGISTRY.read_text(encoding="utf-8"))
    root_ids = [item["id"] for item in registry["root_collection"]["items"]]

    assert root_ids
    assert len(root_ids) == len(set(root_ids))
    assert "Navigation Registry" in structured
    for root_id in root_ids:
        assert root_id in structured

    # The retired product promise must not remain as a second topology owner.
    assert "Pantheon ↔ Décisions ↔ Affaires ↔ Connaissances ↔ Compétences ↔ Outils" not in structured
    assert "A public `Compétences` root must not be created" in structured

    authority = AUTHORITY_INDEX.read_text(encoding="utf-8")
    assert "PANTHEON_COCKPIT_INFORMATION_ARCHITECTURE.md" not in authority
    assert "PANTHEON_COCKPIT_STRUCTURED_AGENCY_INTERFACE.md" in authority
    assert "Navigation Registry" in authority
    assert "still exposes `Workspace` rather than `Compétences`" not in authority
    assert "Decision/WorkIssue blocking follows `decision_request.schema.yaml`" in authority
    assert "project-to-general Knowledge promotion remains owned by Knowledge governance" in authority


def test_retired_owner_does_not_remove_decision_work_issue_boundary() -> None:
    decision_schema = DECISION_REQUEST_SCHEMA.read_text(encoding="utf-8")

    assert "one_active_blocking_request_per_work_issue: true" in decision_schema
    assert "work_issue_continuation_is_separate: true" in decision_schema
    assert "automatic_work_issue_transition: false" in decision_schema
    assert "automatic_runtime_continuation: false" in decision_schema


def test_retired_owner_does_not_remove_project_to_general_knowledge_boundary() -> None:
    knowledge = KNOWLEDGE_GOVERNANCE.read_text(encoding="utf-8")

    assert "project first; general only after human promotion" in knowledge
    assert "may become general only after explicit extraction, anonymization if needed, and validation" in knowledge
    assert "explicitly promoted to general or agency memory" in knowledge
