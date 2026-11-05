"""PostgreSQL acceptance tests for the clean Project Anatomy owner."""

from __future__ import annotations

import uuid

import psycopg
import pytest

from mvp_vertical import agency_data, apu_owner, store


@pytest.fixture
def conn():
    try:
        connection = store.connect()
        connection.execute(agency_data.MIGRATION.read_text(encoding="utf-8"))
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


def _id(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex}"


def _project(conn, label: str) -> str:
    project_id = _id("project")
    conn.execute(
        "INSERT INTO agency_projects "
        "(project_id, code, display_name, created_by, updated_by) "
        "VALUES (%s, %s, %s, 'test', 'test')",
        (project_id, _id(label)[:30], f"Projet {label}"),
    )
    return project_id


def _stable(project_id: str, object_id: str, *, family: str = "element") -> dict:
    return {
        "stable_object_id": object_id,
        "project_ref": project_id,
        "object_family": family,
        "nomenclature": {
            "internal_code": object_id[-12:],
            "display_name": f"Objet {object_id[-8:]}",
        },
    }


def _representation(project_id: str, representation_id: str) -> dict:
    return {
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
    }


def _attribute(object_id: str, claim_id: str, representation_id: str) -> dict:
    return {
        "attribute_claim_id": claim_id,
        "subject_ref": {"entity_type": "stable_object", "entity_id": object_id},
        "attribute_key": "geometry.width",
        "value": {"value_type": "number", "value": 900, "unit": "mm"},
        "assertion_mode": "observed",
        "source_authority": "project_working_document",
        "proof_status": "candidate",
        "source_representation_refs": [representation_id],
    }


def _relation(origin: str, target: str, claim_id: str, representation_id: str) -> dict:
    return {
        "relation_claim_id": claim_id,
        "subject_ref": {"entity_type": "stable_object", "entity_id": origin},
        "relation_type": "architecture.hosted_by",
        "object_ref": {"entity_type": "stable_object", "entity_id": target},
        "assertion_mode": "human_asserted",
        "source_authority": "project_working_document",
        "proof_status": "accepted_as_support",
        "source_representation_refs": [representation_id],
    }


def _dossier(project_id: str) -> dict:
    opening = _id("apu-opening")
    boundary = _id("apu-boundary")
    representation = _id("representation")
    return {
        "stable_objects": [
            _stable(project_id, opening),
            _stable(project_id, boundary),
        ],
        "source_representations": [_representation(project_id, representation)],
        "attribute_claims": [_attribute(opening, _id("attribute"), representation)],
        "relation_claims": [
            _relation(opening, boundary, _id("relation"), representation)
        ],
    }


def _store(conn, project_id: str, *, key: str | None = None, dossier: dict | None = None):
    return apu_owner.store_reviewed_dossier(
        conn,
        project_id=project_id,
        **(dossier or _dossier(project_id)),
        review_ref="review:architect:2026-08-09",
        actor="human:architect",
        idempotency_key=key or _id("apu-bootstrap"),
    )


def test_reviewed_dossier_becomes_one_server_owned_projection(conn) -> None:
    project_id = _project(conn, "owner")
    projection = _store(conn, project_id)

    assert projection["project_ref"] == project_id
    assert projection["model_version"] == 2
    assert projection["model_authority_ref"] == apu_owner.MODEL_AUTHORITY_REF
    assert projection["model_doctrine_ref"] == apu_owner.MODEL_DOCTRINE_REF
    assert projection["owner_revision"] == 1
    assert len(projection["stable_objects"]) == 2
    assert len(projection["source_representations"]) == 1
    assert len(projection["attribute_claims"]) == 1
    assert len(projection["relation_claims"]) == 1
    assert projection["authority"] == apu_owner.AUTHORITY

    events = apu_owner.list_apu_events(conn, project_id=project_id)
    assert [event["event_type"] for event in events] == ["reviewed_dossier_imported"]
    assert events[0]["expected_revision"] == 0
    assert events[0]["resulting_revision"] == 1
    assert events[0]["payload"]["automatic_creation"] is False
    assert events[0]["payload"]["runtime_write"] is False


def test_bootstrap_is_idempotent_for_the_exact_dossier(conn) -> None:
    project_id = _project(conn, "idempotent")
    dossier = _dossier(project_id)
    key = _id("key")
    first = _store(conn, project_id, key=key, dossier=dossier)
    second = _store(conn, project_id, key=key, dossier=dossier)
    assert second == first
    assert len(apu_owner.list_apu_events(conn, project_id=project_id)) == 1


def test_idempotency_key_cannot_name_another_review(conn) -> None:
    project_id = _project(conn, "conflict")
    dossier = _dossier(project_id)
    key = _id("key")
    _store(conn, project_id, key=key, dossier=dossier)
    with pytest.raises(apu_owner.ApuOwnerConflict, match="another effect"):
        apu_owner.store_reviewed_dossier(
            conn,
            project_id=project_id,
            **dossier,
            review_ref="review:other",
            actor="human:architect",
            idempotency_key=key,
        )


def test_owner_refuses_cross_project_source(conn) -> None:
    project_a = _project(conn, "scope-a")
    project_b = _project(conn, "scope-b")
    dossier = _dossier(project_a)
    dossier["source_representations"][0]["project_ref"] = project_b
    with pytest.raises(apu_owner.ApuOwnerError, match="exact Project"):
        _store(conn, project_a, dossier=dossier)


def test_owner_refuses_invalid_governed_object_shape(conn) -> None:
    project_id = _project(conn, "schema")
    dossier = _dossier(project_id)
    dossier["stable_objects"][0]["object_family"] = "imaginary"
    with pytest.raises(apu_owner.ApuOwnerError, match="governed contract"):
        _store(conn, project_id, dossier=dossier)


def test_relation_must_resolve_inside_reviewed_dossier(conn) -> None:
    project_id = _project(conn, "relation")
    dossier = _dossier(project_id)
    dossier["relation_claims"][0]["object_ref"]["entity_id"] = _id("missing")
    with pytest.raises(apu_owner.ApuOwnerError, match="unknown stable object"):
        _store(conn, project_id, dossier=dossier)


def test_second_bootstrap_without_same_idempotency_is_refused(conn) -> None:
    project_id = _project(conn, "single")
    _store(conn, project_id)
    with pytest.raises(apu_owner.ApuOwnerConflict, match="already initialized"):
        _store(conn, project_id)


def test_database_claim_guard_refuses_cross_project_endpoint(conn) -> None:
    project_a = _project(conn, "db-a")
    project_b = _project(conn, "db-b")
    projection_a = _store(conn, project_a)
    projection_b = _store(conn, project_b)
    object_a = projection_a["stable_objects"][0]["object_id"]
    object_b = projection_b["stable_objects"][0]["object_id"]

    payload = {
        "relation_claim_id": _id("bad-relation"),
        "subject_ref": {"entity_type": "stable_object", "entity_id": object_a},
        "relation_type": "architecture.hosted_by",
        "object_ref": {"entity_type": "stable_object", "entity_id": object_b},
        "assertion_mode": "proposed",
        "source_authority": "model_interpretation_candidate",
        "proof_status": "candidate",
    }
    with pytest.raises(psycopg.errors.RaiseException, match="another Project"):
        with conn.transaction():
            conn.execute(
                """
                INSERT INTO agency_apu_relation_claims (
                    claim_id, project_id, subject_entity_type, subject_entity_id,
                    relation_type, object_entity_type, object_entity_id,
                    assertion_mode, source_authority, proof_status,
                    claim_payload, payload_digest, created_by
                ) VALUES (%s, %s, 'stable_object', %s, 'architecture.hosted_by',
                          'stable_object', %s, 'proposed',
                          'model_interpretation_candidate', 'candidate', %s, 'digest', 'test')
                """,
                (payload["relation_claim_id"], project_a, object_a, object_b, psycopg.types.json.Jsonb(payload)),
            )


def test_event_and_claim_history_is_append_only(conn) -> None:
    project_id = _project(conn, "history")
    projection = _store(conn, project_id)
    event_id = apu_owner.list_apu_events(conn, project_id=project_id)[0]["event_id"]
    claim_id = projection["attribute_claims"][0]["attribute_claim_id"]

    for statement, value in (
        ("UPDATE agency_apu_events SET actor = 'other' WHERE event_id = %s", event_id),
        ("UPDATE agency_apu_attribute_claims SET created_by = 'other' WHERE claim_id = %s", claim_id),
    ):
        with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
            with conn.transaction():
                conn.execute(statement, (value,))


def _store_with_kind(conn, project_id: str, source_kind: str) -> dict:
    representation = _representation(project_id, _id("rep"))
    representation["source_kind"] = source_kind
    return apu_owner.store_reviewed_dossier(
        conn,
        project_id=project_id,
        stable_objects=[_stable(project_id, _id("obj"))],
        source_representations=[representation],
        attribute_claims=[],
        relation_claims=[],
        review_ref="review:kinds",
        actor="human:architect",
        idempotency_key=_id("kinds"),
    )


@pytest.mark.parametrize("source_kind", ["document", "email", "cad_drawing", "drawing", "other"])
def test_declared_source_kinds_are_stored(conn, source_kind: str) -> None:
    project_id = _project(conn, "kinds")
    stored = _store_with_kind(conn, project_id, source_kind)["source_representations"]
    assert [item["source_kind"] for item in stored] == [source_kind]


def test_undeclared_source_kind_is_refused_by_the_owner_not_by_the_database(conn) -> None:
    project_id = _project(conn, "undeclared")
    with pytest.raises(apu_owner.ApuOwnerError, match="not declared in the source kind vocabulary"):
        _store_with_kind(conn, project_id, "bordereau")
    # Nothing was written: the same Project can still be initialized.
    assert _store_with_kind(conn, project_id, "document")["owner_revision"] == 1


def test_agency_source_kind_is_stored_through_the_local_file(conn, tmp_path, monkeypatch) -> None:
    import json

    agency = tmp_path / "source-kinds.json"
    agency.write_text(json.dumps({
        "registry_kind": "vocabulary_overlay",
        "extends": "architecture_source_kind_profile",
        "entries": [{"id": "plan_recolement", "status": "active",
                     "label": "Plan de récolement", "description": "Plan fourni par l'entreprise."}],
    }), encoding="utf-8")
    project_id = _project(conn, "agency")
    # Without the file the kind is undeclared...
    with pytest.raises(apu_owner.ApuOwnerError, match="not declared"):
        _store_with_kind(conn, project_id, "plan_recolement")
    # ...with it, the same kind is stored, with no migration of the database.
    monkeypatch.setenv("PANTHEON_SOURCE_KIND_OVERLAY", str(agency))
    stored = _store_with_kind(conn, project_id, "plan_recolement")["source_representations"]
    assert [item["source_kind"] for item in stored] == ["plan_recolement"]


def test_unreadable_agency_file_stops_the_owner_instead_of_being_ignored(conn, monkeypatch) -> None:
    monkeypatch.setenv("PANTHEON_SOURCE_KIND_OVERLAY", "/nonexistent/source-kinds.json")
    with pytest.raises(apu_owner.ApuOwnerError, match="cannot read the agency source kind file"):
        _store_with_kind(conn, _project(conn, "unreadable"), "document")


def test_database_checks_the_shape_of_a_source_kind_only(conn) -> None:
    constraint = "agency_apu_source_representations_source_kind_check"
    definition = conn.execute(
        "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = %s", (constraint,)
    ).fetchone()[0]
    assert "point_cloud" not in definition and "~" in definition

    project_id = _project(conn, "shape")
    insert = (
        "INSERT INTO agency_apu_source_representations (representation_id, project_id, "
        "source_kind, proof_status, representation_payload, payload_digest, created_by) "
        "VALUES (%s, %s, %s, 'candidate', %s::jsonb, 'd', 'test')"
    )

    def payload(kind: str, representation_id: str) -> str:
        return (f'{{"representation_id": "{representation_id}", "project_ref": "{project_id}", '
                f'"source_kind": "{kind}", "proof_status": "candidate"}}')

    ok_id = _id("rep")
    conn.execute(insert, (ok_id, project_id, "plan_recolement", payload("plan_recolement", ok_id)))
    for bad in ("Plan", "x", "a-b", "1plan", "a" * 41):
        conn.execute("SAVEPOINT shape")
        bad_id = _id("rep")
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute(insert, (bad_id, project_id, bad, payload(bad, bad_id)))
        conn.execute("ROLLBACK TO SAVEPOINT shape")


def test_owner_installed_with_the_former_closed_list_is_upgraded_once(conn) -> None:
    constraint = "agency_apu_source_representations_source_kind_check"
    conn.execute(f"ALTER TABLE agency_apu_source_representations DROP CONSTRAINT {constraint}")
    conn.execute(
        f"ALTER TABLE agency_apu_source_representations ADD CONSTRAINT {constraint} "
        "CHECK (source_kind IN ('revit', 'ifc', 'drawing', 'drawing_takeoff', 'image', "
        "'photo', 'manual', 'scan', 'point_cloud', 'other'))"
    )
    project_id = _project(conn, "upgrade")
    insert = (
        "INSERT INTO agency_apu_source_representations (representation_id, project_id, "
        "source_kind, proof_status, representation_payload, payload_digest, created_by) "
        "VALUES (%s, %s, %s, 'candidate', %s::jsonb, 'd', 'test')"
    )
    rep_id = _id("rep")
    body = (f'{{"representation_id": "{rep_id}", "project_ref": "{project_id}", '
            '"source_kind": "cad_drawing", "proof_status": "candidate"}')
    conn.execute("SAVEPOINT closed")
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(insert, (rep_id, project_id, "cad_drawing", body))
    conn.execute("ROLLBACK TO SAVEPOINT closed")

    conn.execute(apu_owner.MIGRATION.read_text(encoding="utf-8"))
    oid = conn.execute("SELECT oid FROM pg_constraint WHERE conname = %s", (constraint,)).fetchone()[0]
    conn.execute(insert, (rep_id, project_id, "cad_drawing", body))

    conn.execute(apu_owner.MIGRATION.read_text(encoding="utf-8"))  # replay: nothing to do
    assert conn.execute("SELECT oid FROM pg_constraint WHERE conname = %s", (constraint,)).fetchone()[0] == oid


def _dossier_with_phase(project_id: str, phase: str) -> dict:
    dossier = _dossier(project_id)
    dossier["attribute_claims"][0]["validity"] = {"established_at_phase": phase}
    return dossier


@pytest.mark.parametrize("phase", ["ESQ", "APS", "DCE", "AGENCY_LIBRARY"])
def test_declared_phase_codes_are_stored(conn, phase: str) -> None:
    project_id = _project(conn, "phases")
    stored = _store(conn, project_id, dossier=_dossier_with_phase(project_id, phase))
    assert stored["owner_revision"] == 1


def test_undeclared_phase_code_is_refused_by_the_owner(conn) -> None:
    project_id = _project(conn, "phase-undeclared")
    with pytest.raises(apu_owner.ApuOwnerError, match="'ESQUISSE' is not declared in the phase vocabulary"):
        _store(conn, project_id, dossier=_dossier_with_phase(project_id, "ESQUISSE"))
    # Nothing was written: the same Project can still be initialized.
    assert _store(conn, project_id, dossier=_dossier_with_phase(project_id, "ESQ"))["owner_revision"] == 1


def test_agency_phase_code_is_stored_through_the_local_file(conn, tmp_path, monkeypatch) -> None:
    import json

    agency = tmp_path / "phases.json"
    agency.write_text(json.dumps({
        "registry_kind": "vocabulary_overlay",
        "extends": "architecture_phase_profile",
        "entries": [{"id": "FAISA", "status": "active", "category": "mission_element",
                     "label": "Faisabilité", "description": "Étude de faisabilité avant esquisse."}],
    }), encoding="utf-8")
    project_id = _project(conn, "phase-agency")
    with pytest.raises(apu_owner.ApuOwnerError, match="not declared"):
        _store(conn, project_id, dossier=_dossier_with_phase(project_id, "FAISA"))
    monkeypatch.setenv("PANTHEON_PHASE_OVERLAY", str(agency))
    assert _store(conn, project_id, dossier=_dossier_with_phase(project_id, "FAISA"))["owner_revision"] == 1
