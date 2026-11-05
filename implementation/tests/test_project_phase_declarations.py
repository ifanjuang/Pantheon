"""Phases declared per project, as the project advances.

A project declares each phase it goes through as one ProjectClaim ``phase``,
with the date the declaration takes effect. The value must come from the
governed phase vocabulary and cannot be a non-project scope marker. A Project
Anatomy claim established at a phase the project has not declared is reported
as a limitation by the Cockpit projection, never refused.
"""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

import pytest

from mvp_vertical import agency_claims, agency_data, agency_schema, apu_owner
from mvp_vertical.project_anatomy_projection import get_project_anatomy_projection

ROOT = Path(__file__).resolve().parents[1]
PROJECTION_SQL = ROOT / "mvp_vertical" / "sql" / "036_project_claim_provenance_basis.sql"


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def test_sql_list_projection_covers_exactly_the_list_claim_fields() -> None:
    declared = sorted(
        claim_type
        for claim_type, field in agency_schema.project_claim_fields().items()
        if field.get("aggregation") == "list"
    )
    match = re.search(r"list_claim_types TEXT\[\] := ARRAY\[([^\]]*)\]", PROJECTION_SQL.read_text(encoding="utf-8"))
    assert match, "the SQL projection no longer declares its list claim types"
    in_sql = sorted(re.findall(r"'([a-z_]+)'", match.group(1)))
    assert in_sql == declared == ["parcelle", "phase"]


def test_phase_field_is_a_vocabulary_list_with_an_effective_date() -> None:
    field = agency_schema.project_claim_fields()["phase"]
    assert field["key"] == "phases"
    assert field["aggregation"] == "list"
    assert field["vocabulary"] == "phase"
    assert field["effective_at_required"] is True
    assert field["mutable"] is False


@pytest.fixture
def conn():
    try:
        connection = agency_data.connect()
        connection.execute(apu_owner.MIGRATION.read_text(encoding="utf-8"))
        connection.commit()
    except Exception as exc:  # pragma: no cover - local unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute("BEGIN")
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


def _project(conn) -> str:
    project_id = _id("project")
    conn.execute(
        "INSERT INTO agency_projects (project_id, code, display_name, created_by, updated_by) "
        "VALUES (%s, %s, %s, 'test', 'test')",
        (project_id, _id("PH")[:24], "Projet phases"),
    )
    return project_id


def _declare(conn, project_id: str, phase: str, effective_at: str | None = "2026-03-01T00:00:00Z", **extra):
    return agency_claims.record_claim(
        conn,
        project_id=project_id,
        claim_type="phase",
        value=phase,
        actor="human:architect",
        effective_at=effective_at,
        **extra,
    )


def _declared(conn, project_id: str) -> tuple[list[str], list[str]]:
    """The declared phases through the Python projection and the SQL read cache."""
    values, _refs = agency_claims.project_claim_projection(conn, project_id)
    cached = conn.execute(
        "SELECT claim_values FROM agency_projects WHERE project_id = %s", (project_id,)
    ).fetchone()[0]
    return list(values.get("phase") or []), list(cached.get("phase") or [])


def test_phases_are_declared_progressively_with_their_effective_date(conn) -> None:
    project_id = _project(conn)
    assert _declared(conn, project_id) == ([], [])
    _declare(conn, project_id, "ESQ", "2026-01-15T00:00:00Z")
    _declare(conn, project_id, "APS", "2026-03-01T00:00:00Z")
    python_view, sql_view = _declared(conn, project_id)
    assert set(python_view) == set(sql_view) == {"ESQ", "APS"}
    refs = agency_claims.project_claim_projection(conn, project_id)[1]["phase"]
    assert {ref["value"]: str(ref["effective_at"])[:10] for ref in refs} == {
        "ESQ": "2026-01-15",
        "APS": "2026-03-01",
    }


@pytest.mark.parametrize(
    ("phase", "message"),
    [
        ("ESQUISSE", "not declared in the phase vocabulary"),
        ("AGENCY_LIBRARY", "non-project scope marker"),
        ("GLOBAL_REFERENCE", "non-project scope marker"),
    ],
)
def test_undeclared_phase_or_scope_marker_is_refused(conn, phase: str, message: str) -> None:
    project_id = _project(conn)
    with pytest.raises(agency_claims.AgencyClaimError, match=message):
        _declare(conn, project_id, phase)
    assert _declared(conn, project_id) == ([], [])


def test_declaration_without_effective_date_is_refused(conn) -> None:
    project_id = _project(conn)
    with pytest.raises(agency_claims.AgencyClaimError, match="requires effective_at"):
        _declare(conn, project_id, "ESQ", effective_at=None)


def test_a_mistaken_declaration_is_superseded_not_edited(conn) -> None:
    project_id = _project(conn)
    wrong = _declare(conn, project_id, "APD")
    _declare(conn, project_id, "APS", supersedes=wrong["claim_id"])
    python_view, sql_view = _declared(conn, project_id)
    assert python_view == sql_view == ["APS"]
    # The mistaken declaration is kept in the append-only history.
    history = [claim["value"] for claim in agency_claims.list_project_claims(conn, project_id)]
    assert sorted(history) == ["APD", "APS"]


def test_agency_phase_is_declared_through_the_local_file(conn, tmp_path, monkeypatch) -> None:
    agency = tmp_path / "phases.json"
    agency.write_text(json.dumps({
        "registry_kind": "vocabulary_overlay",
        "extends": "architecture_phase_profile",
        "entries": [{"id": "FAISA", "status": "active", "category": "mission_element",
                     "label": "Faisabilité", "description": "Étude de faisabilité avant esquisse."}],
    }), encoding="utf-8")
    project_id = _project(conn)
    with pytest.raises(agency_claims.AgencyClaimError, match="not declared"):
        _declare(conn, project_id, "FAISA")
    monkeypatch.setenv("PANTHEON_PHASE_OVERLAY", str(agency))
    _declare(conn, project_id, "FAISA")
    assert _declared(conn, project_id)[0] == ["FAISA"]


def _store_claim_at_phase(conn, project_id: str, phase: str) -> str:
    object_id = _id("apu-object")
    representation_id = _id("representation")
    claim_id = _id("attribute")
    apu_owner.store_reviewed_dossier(
        conn,
        project_id=project_id,
        stable_objects=[{
            "stable_object_id": object_id,
            "project_ref": project_id,
            "object_family": "element",
            "nomenclature": {"internal_code": object_id[-12:], "display_name": "Porte"},
        }],
        source_representations=[{
            "representation_id": representation_id,
            "project_ref": project_id,
            "source_artifact_ref": "drawing.A",
            "source_kind": "drawing",
            "identifiers": [{"scheme": "drawing.fragment", "value": representation_id}],
            "observed_at": "2026-08-09T10:00:00Z",
            "binding_ref": "fixture.drawing",
            "adapter_version": "1.0",
            "freshness_token": "drawing-A:1",
            "proof_status": "candidate",
        }],
        attribute_claims=[{
            "attribute_claim_id": claim_id,
            "subject_ref": {"entity_type": "stable_object", "entity_id": object_id},
            "attribute_key": "geometry.width",
            "value": {"value_type": "number", "value": 900, "unit": "mm"},
            "assertion_mode": "observed",
            "source_authority": "project_working_document",
            "proof_status": "candidate",
            "source_representation_refs": [representation_id],
            "validity": {"established_at_phase": phase},
        }],
        relation_claims=[],
        review_ref="review:architect:phases",
        actor="human:architect",
        idempotency_key=_id("phases"),
    )
    return claim_id


def test_anatomy_claim_at_an_undeclared_phase_is_stored_and_reported(conn) -> None:
    project_id = _project(conn)
    _declare(conn, project_id, "ESQ")
    # The owner accepts the claim: the phase is in the vocabulary.
    claim_id = _store_claim_at_phase(conn, project_id, "PRO")

    projection = get_project_anatomy_projection(conn, project_id=project_id)
    assert projection["phases"]["declared_phases"] == ["ESQ"]
    assert projection["phases"]["refused"] is False
    assert [(item["phase"], item["claim_id"]) for item in projection["phases"]["claims_outside_declared_phases"]] == [
        ("PRO", claim_id)
    ]

    # Declaring the phase later clears the limitation; the claim never changed.
    _declare(conn, project_id, "PRO", "2026-09-01T00:00:00Z")
    projection = get_project_anatomy_projection(conn, project_id=project_id)
    assert projection["phases"]["claims_outside_declared_phases"] == []
    assert [item["claim_id"] for item in projection["attribute_claims"]] == [claim_id]


@pytest.mark.parametrize(
    ("card_phase", "declared", "status"),
    [
        (None, ["ESQ"], "no_card_phase"),
        ("PRO", [], "no_phase_declared"),
        ("APS", ["ESQ", "APS"], "consistent"),
        ("PRO", ["ESQ", "APS"], "card_phase_not_declared"),
    ],
)
def test_card_phase_is_compared_with_the_declarations_never_derived(card_phase, declared, status) -> None:
    result = agency_claims.phase_consistency(card_phase, declared)
    assert result["status"] == status
    assert result["refused"] is False
    assert result["card_phase_derived"] is False


def test_card_phase_not_declared_is_reported_and_left_unchanged(conn) -> None:
    project_id = _project(conn)
    conn.execute("UPDATE agency_projects SET phase = 'PRO' WHERE project_id = %s", (project_id,))
    _declare(conn, project_id, "ESQ")
    result = agency_claims.project_phase_consistency(conn, project_id)
    assert (result["card_phase"], result["declared_phases"], result["status"]) == (
        "PRO", ["ESQ"], "card_phase_not_declared"
    )
    assert conn.execute(
        "SELECT phase FROM agency_projects WHERE project_id = %s", (project_id,)
    ).fetchone()[0] == "PRO"
    _declare(conn, project_id, "PRO", "2026-09-01T00:00:00Z")
    assert agency_claims.project_phase_consistency(conn, project_id)["status"] == "consistent"


def test_phase_declared_again_is_listed_once_in_both_projections(conn) -> None:
    project_id = _project(conn)
    _declare(conn, project_id, "APD", "2026-02-01T00:00:00Z")
    _declare(conn, project_id, "PRO", "2026-04-01T00:00:00Z")
    # Back to APD after a programme change: declared again with its new date.
    _declare(conn, project_id, "APD", "2026-06-01T00:00:00Z")
    python_view, sql_view = _declared(conn, project_id)
    assert sorted(python_view) == sorted(sql_view) == ["APD", "PRO"]
    cached_refs = conn.execute(
        "SELECT claim_refs FROM agency_projects WHERE project_id = %s", (project_id,)
    ).fetchone()[0]["phase"]
    apd = [ref for ref in cached_refs if ref["effective_at"].startswith("2026-06-01")]
    assert len(apd) == 1, "the most recent declaration of APD is the one projected"


def test_an_alias_is_stored_as_the_code_it_names_and_the_entry_is_kept(conn) -> None:
    project_id = _project(conn)
    claim = _declare(conn, project_id, "PC", "2026-08-11T00:00:00Z")
    assert claim["value"] == "DPC"
    assert "entered as 'PC', alias of 'DPC'" in claim["provenance"]["derivation_note"]
    _declare(conn, project_id, "PERMIS", "2026-09-01T00:00:00Z")
    python_view, sql_view = _declared(conn, project_id)
    assert python_view == sql_view == ["DPC"]


def test_an_agency_alias_is_declared_through_the_local_file(conn, tmp_path, monkeypatch) -> None:
    agency = tmp_path / "phases.json"
    agency.write_text(json.dumps({
        "registry_kind": "vocabulary_overlay",
        "extends": "architecture_phase_profile",
        "entries": [],
        "aliases": {"ESQUISSE": "ESQ"},
    }), encoding="utf-8")
    project_id = _project(conn)
    with pytest.raises(agency_claims.AgencyClaimError, match="not declared"):
        _declare(conn, project_id, "ESQUISSE")
    monkeypatch.setenv("PANTHEON_PHASE_OVERLAY", str(agency))
    assert _declare(conn, project_id, "ESQUISSE")["value"] == "ESQ"


def test_anatomy_claim_named_by_an_alias_is_within_the_declared_code(conn) -> None:
    project_id = _project(conn)
    _declare(conn, project_id, "DPC")
    _store_claim_at_phase(conn, project_id, "PC")
    projection = get_project_anatomy_projection(conn, project_id=project_id)
    assert projection["phases"]["claims_outside_declared_phases"] == []
