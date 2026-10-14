from __future__ import annotations

import json
from pathlib import Path

from mvp_vertical import agency_schema


FIXTURES = Path(__file__).parent / "fixtures" / "agency"


def _fixtures() -> list[dict]:
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(FIXTURES.glob("f*.json"))
    ]


def test_fixture_project_claim_types_exist_in_current_registry() -> None:
    declared = set(agency_schema.project_claim_fields())
    used = {
        claim["claim_type"]
        for fixture in _fixtures()
        for claim in fixture.get("project_claims") or []
    }

    assert used <= declared
    assert "montant_marche" in declared


def test_fixture_project_attributes_are_declared_flexible_attributes() -> None:
    registry = agency_schema.get_entity_registry("project")
    allowed = {
        field["key"]
        for field in registry["fields"]
        if field.get("storage") == "attributes"
    }

    for fixture in _fixtures():
        assert set(fixture["project"].get("attributes") or {}) <= allowed


def test_fixture_project_phases_use_current_project_phase_enum_when_present() -> None:
    registry = agency_schema.get_entity_registry("project")
    phase = next(field for field in registry["fields"] if field["key"] == "phase")
    allowed = set(phase["values"])

    for fixture in _fixtures():
        value = fixture["project"].get("phase")
        if value is not None:
            assert value in allowed


def test_fixture_information_statuses_use_current_information_registry() -> None:
    registry = agency_schema.get_entity_registry("information")
    status = next(field for field in registry["fields"] if field["key"] == "status")
    allowed = set(status["values"])

    for fixture in _fixtures():
        for information in fixture["information"]:
            assert information["status"] in allowed
