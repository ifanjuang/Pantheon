from __future__ import annotations

from pathlib import Path

from mvp_vertical import apu_cross_family, pantheon_contracts


ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "mvp_vertical" / "sql" / "023_apu_cross_family_links.sql"

def test_cross_family_links_reuse_owners_without_universal_relation_vocabulary() -> None:
    sql = SQL.read_text(encoding="utf-8")
    assert apu_cross_family.SCOPE_ENTITY_TYPE == "apu_object"
    assert "agency_decision_request_scope_refs" in sql
    assert "backing_entity_type IS DISTINCT FROM 'apu_object'" in sql
    assert "INSERT INTO agency_entity_relations" not in sql
    assert "INSERT INTO agency_apu_object_relations" not in sql
    assert "UPDATE agency_apu_objects" not in sql
    assert "DELETE FROM agency_apu_objects" not in sql


def test_decision_scope_contract_uses_canonical_contract() -> None:
    source = pantheon_contracts.provenance("decision_request")
    assert source["source_repository"] == "ifanjuang/Pantheon"
    assert source["source_path"] == "schemas/decision_request.schema.yaml"
    assert source["posture"] == "canonical-repository"
    assert source["authority_transfer"] is False

    schema = pantheon_contracts.schema_path("decision_request").read_text(encoding="utf-8")
    assert "scope_refs:" in schema
    assert "const: apu_object" in schema
    assert "scope_ref_is_semantic_relation: false" in schema
    assert "scope_ref_mutates_apu: false" in schema


def test_cross_family_links_ignore_discarded_parallel_carrier_internals() -> None:
    source = (ROOT / "mvp_vertical" / "apu_cross_family.py").read_text(encoding="utf-8")
    for forbidden in (
        "object_identity",
        "spatial_node",
        "stable_object.matches",
        "representation_match",
        "relation_claim",
    ):
        assert forbidden not in source
