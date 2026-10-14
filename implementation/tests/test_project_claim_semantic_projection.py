import json
from pathlib import Path

import pytest

from mvp_vertical import agency_claims, agency_schema


ROOT = Path(__file__).resolve().parents[1]
PROJECT_SCHEMA = ROOT / "mvp_vertical" / "agency_schema" / "project.json"
AGENCY_SQL = ROOT / "mvp_vertical" / "sql" / "002_agency_data.sql"


LEGACY_CLAIM_ATTRIBUTES = {
    "budget",
    "surface_terrain",
    "surface_existante",
    "surface_projet",
    "emprise",
    "parcelles",
    "plu_zone",
    "permit_number",
    "permit_date",
    "reception_date",
    "erp_type",
}


def test_project_registry_separates_descriptive_attributes_from_claim_projections() -> None:
    registry = json.loads(PROJECT_SCHEMA.read_text(encoding="utf-8"))
    assert registry["schema_id"] == "agency.project.v2"

    fields = {field["key"]: field for field in registry["fields"]}
    for key in LEGACY_CLAIM_ATTRIBUTES:
        field = fields[key]
        assert field["storage"] == "projection"
        assert field["semantics"] == "claim"
        assert field["mutable"] is False
        assert field["claim_type"]

    assert fields["programme_summary"]["storage"] == "attributes"
    assert fields["architectural_style"]["storage"] == "attributes"
    assert fields["agency_notes"]["storage"] == "attributes"


def test_legacy_claim_attributes_are_no_longer_valid_project_attributes() -> None:
    for key in LEGACY_CLAIM_ATTRIBUTES:
        with pytest.raises(agency_schema.AgencySchemaError, match="unsupported Project attribute field"):
            agency_schema.normalize_project_attributes({key: "legacy"})

    assert agency_schema.normalize_project_attributes(
        {
            "programme_summary": "Maison familiale",
            "architectural_style": "Architecture normande contemporaine",
            "agency_notes": "À préciser en APD",
        }
    ) == {
        "programme_summary": "Maison familiale",
        "architectural_style": "Architecture normande contemporaine",
        "agency_notes": "À préciser en APD",
    }


def test_project_edit_view_does_not_offer_claim_projections_as_plain_fields() -> None:
    edit_fields = {field["key"] for field in agency_schema.get_project_schema("edit")["fields"]}
    assert not (edit_fields & LEGACY_CLAIM_ATTRIBUTES)
    assert {"programme_summary", "architectural_style", "agency_notes"} <= edit_fields


def test_schema_init_drops_obsolete_attribute_keys_and_creates_append_only_claim_store() -> None:
    sql = AGENCY_SQL.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS agency_project_claims" in sql
    assert "agency_project_claims are append-only" in sql
    assert "attributes = attributes - ARRAY[" in sql
    for key in LEGACY_CLAIM_ATTRIBUTES:
        assert f"'{key}'" in sql


def test_governance_contract_allows_asserted_without_backing_but_requires_backing_for_source_backed() -> None:
    asserted = {
        "claim_id": "claim.demo.zone",
        "project_id": "project-demo",
        "claim_type": "plu_zone",
        "value": "UDb",
        "unit": None,
        "backing_ref": None,
        "provenance": {
            "source_kind": "human_assertion",
            "source_ref": None,
            "asserted_by": "human:test",
            "derivation_note": None,
        },
        "status": "asserted",
        "certainty": "E0",
        "observed_at": "2026-07-27T00:00:00+00:00",
        "revision": 0,
        "supersedes": None,
        "note": None,
        "governance_refs": list(agency_claims.GOVERNANCE_REFS),
    }
    agency_claims.validate_claim(asserted)

    source_backed = dict(asserted)
    source_backed["claim_id"] = "claim.demo.zone.source"
    source_backed["status"] = "source_backed"
    with pytest.raises(agency_claims.ClaimContractViolation):
        agency_claims.validate_claim(source_backed)

    source_backed["backing_ref"] = {
        "entity_type": "information",
        "entity_id": "information-demo",
        "observed_status": "acted",
    }
    source_backed["provenance"] = {
        "source_kind": "information",
        "source_ref": "information-demo",
        "asserted_by": "human:test",
        "derivation_note": None,
    }
    agency_claims.validate_claim(source_backed)


def test_structured_basis_is_bounded_to_execution_candidate_provenance() -> None:
    common = {
        "project_id": "project-demo",
        "claim_type": "plu_zone",
        "value": "UDb",
        "unit": None,
        "backing_ref": None,
        "status": "asserted",
        "certainty": "E0",
        "observed_at": "2026-07-27T00:00:00+00:00",
        "revision": 0,
        "supersedes": None,
        "note": None,
        "governance_refs": list(agency_claims.GOVERNANCE_REFS),
    }
    basis = [{
        "entity_type": "information",
        "entity_id": "information-demo",
        "observed_revision": 1,
        "observed_status": "acted",
    }]

    human_claim = {
        **common,
        "claim_id": "claim.demo.human-basis",
        "provenance": {
            "source_kind": "human_assertion",
            "source_ref": None,
            "candidate_ref": None,
            "basis_refs": basis,
            "asserted_by": "human:test",
            "derivation_note": None,
        },
    }
    with pytest.raises(agency_claims.ClaimContractViolation):
        agency_claims.validate_claim(human_claim)

    historical_execution_claim = {
        **common,
        "claim_id": "claim.demo.execution-history",
        "provenance": {
            "source_kind": "execution_result",
            "source_ref": None,
            "candidate_ref": {
                "execution_id": "execution.demo",
                "result_id": "result.demo",
                "review_disposition_id": "disposition.demo",
            },
            "basis_refs": [],
            "asserted_by": "human:test",
            "derivation_note": None,
        },
    }
    agency_claims.validate_claim(historical_execution_claim)


def test_parcels_are_declared_as_aggregated_scalar_claims() -> None:
    parcel_field = agency_schema.project_claim_fields()["parcelle"]
    assert parcel_field["key"] == "parcelles"
    assert parcel_field["aggregation"] == "list"
    assert parcel_field["type"] == "string_list"
