"""PostgreSQL acceptance for progressive APU claim writes.

After the one reviewed dossier import, a claim enters the APU only through the
existing chain: Observation Bundle candidate -> review (accept_claim_candidate)
-> write command -> human authorization -> application. A replacement keeps the
replaced claim and links it; it never edits it.
"""

from __future__ import annotations

import uuid

import psycopg
import pytest

from mvp_vertical import (
    agency_data,
    apu_mapping_reviews,
    apu_owner,
    apu_owner_claims,
    apu_object_read,
    apu_write_preparation,
    execution_results,
)


@pytest.fixture
def conn():
    try:
        connection = agency_data.connect()
        for migration in (
            execution_results.MIGRATION,
            apu_owner.MIGRATION,
            apu_mapping_reviews.MIGRATION,
            apu_write_preparation.MIGRATION,
            apu_write_preparation.APPLICATION_MIGRATION,
        ):
            connection.execute(migration.read_text(encoding="utf-8"))
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
    return f"{prefix}-{uuid.uuid4().hex}"


DOOR = "OBJ-DOOR-017"
WALL = "OBJ-WALL-004"
REP = "rep.drawing.door-017.t0"
REP_B = "rep.drawing.door-017.t1"


def _project(conn) -> str:
    project_id = _id("project-claims")
    conn.execute(
        "INSERT INTO agency_projects "
        "(project_id, code, display_name, created_by, updated_by) "
        "VALUES (%s, %s, %s, 'test', 'test')",
        (project_id, _id("CLM"), "Écriture APU progressive"),
    )
    return project_id


def _width(claim_id: str, value: float, **extra) -> dict:
    return {
        "attribute_claim_id": claim_id,
        "subject_ref": {"entity_type": "stable_object", "entity_id": DOOR},
        "attribute_key": "geometry.width",
        "value": {"value_type": "number", "value": value, "unit": "m"},
        "assertion_mode": "observed",
        "source_authority": "project_working_document",
        "proof_status": "candidate",
        "source_representation_refs": [REP_B],
        **extra,
    }


def _import(conn, project_id: str) -> None:
    objects = [
        {
            "stable_object_id": DOOR,
            "project_ref": project_id,
            "object_family": "element",
            "nomenclature": {"internal_code": "P17", "display_name": "Porte séjour"},
        },
        {
            "stable_object_id": WALL,
            "project_ref": project_id,
            "object_family": "element",
            "nomenclature": {"internal_code": "M4", "display_name": "Mur séjour"},
        },
    ]
    representation = {
        "representation_id": REP,
        "project_ref": project_id,
        "source_artifact_ref": "source.pdf.a101",
        "source_version_ref": "drawing:a101:index-a",
        "source_kind": "drawing",
        "identifiers": [{"scheme": "drawing.local_label", "value": "P17"}],
        "observed_at": "2026-01-10T09:00:00Z",
        "binding_ref": "binding.synthetic.drawing",
        "adapter_version": "1.0.0",
        "freshness_token": "sha256:a101-a",
        "content_digest": "sha256:a101-p17",
        "proof_status": "candidate",
    }
    apu_owner.store_reviewed_dossier(
        conn,
        project_id=project_id,
        stable_objects=objects,
        source_representations=[
            representation,
            dict(representation) | {
                "representation_id": REP_B,
                "source_version_ref": "drawing:a101:index-b",
                "freshness_token": "sha256:a101-b",
                "content_digest": "sha256:a101-p17-b",
            },
        ],
        attribute_claims=[
            _width("claim.door.width.t0", 0.90, source_representation_refs=[REP])
        ],
        relation_claims=[],
        review_ref="review:claims:t0",
        actor="human:architect",
        idempotency_key=_id("import"),
    )


def _bundle(conn, project_id: str, attributes: list[dict], relations: list[dict]) -> tuple[str, str]:
    execution_id = _id("execution-bundle")
    result_id = _id("result-bundle")
    payload = {
        "observation_bundle_id": _id("observation-bundle"),
        "project_ref": project_id,
        "task_contract_ref": "task-contract:claims",
        "basis": {
            "source_artifact_refs": ["source.pdf.a101"],
            "source_version_refs": ["drawing:a101:index-b"],
            "exact_digests": [
                {
                    "source_artifact_ref": "source.pdf.a101",
                    "source_version_ref": "drawing:a101:index-b",
                    "digest": "sha256:a101-b",
                }
            ],
        },
        "method": {
            "capability_id": "drawing.observe.openings",
            "binding_id": "binding.synthetic.drawing",
            "operation_id": "drawing.observe.openings.v1",
            "adapter_ref": "pantheon.synthetic.drawing",
            "adapter_version": "1.0.0",
            "request_ref": "request:claims",
        },
        "observed_at": "2026-03-02T10:00:00Z",
        "freshness_token": "sha256:a101-b",
        "scope": {"document_refs": ["drawing:a101"]},
        "coverage": {
            "completeness": "partial_for_declared_scope",
            "observed_scope": {"document_refs": ["drawing:a101"]},
            "excluded_reasons": [],
            "absence_inference_allowed": False,
        },
        "limitations": ["Synthetic test bundle."],
        "source_representations": [],
        "attribute_claim_candidates": attributes,
        "relation_claim_candidates": relations,
        "gaps": [],
        "withheld": [],
        "warnings": [],
        "operational_outcome": "success",
        "authority": {
            "is_fact": False,
            "is_evidence": False,
            "is_decision": False,
            "is_memory": False,
            "is_apu_write": False,
            "authorizes_external_effect": False,
        },
    }
    execution_results.store_execution_result(
        conn,
        execution_result={
            "execution_result_id": execution_id,
            "task_contract_ref": "task-contract:claims",
            "project_ref": project_id,
            "producer": {"kind": "fixture", "version": "1"},
            "produced_at": "2026-03-02T10:00:00Z",
            "authority": dict(execution_results.AUTHORITY),
            "results": [
                {
                    "result_id": result_id,
                    "result_kind": "observation_bundle",
                    "schema_ref": execution_results.OBSERVATION_BUNDLE_SCHEMA_REF,
                    "payload": payload,
                }
            ],
            "clarification_requests": [],
        },
        idempotency_key=_id("bundle"),
    )
    return execution_id, result_id


def _review(conn, execution_id, result_id, ref, *, action="accept_claim_candidate", superseded=None):
    return apu_mapping_reviews.append_mapping_review(
        conn,
        execution_result_id=execution_id,
        result_ref=result_id,
        mapping_ref=ref,
        action=action,
        selected_stable_object_ref=None,
        clarification_question="Quelle cote fait foi ?" if action == "needs_clarification" else None,
        note="Revue humaine du candidat.",
        reviewer="human:architect",
        idempotency_key=_id("review"),
        superseded_claim_ref=superseded,
    )


def _prepare(conn, execution_id, result_id, ref):
    return apu_write_preparation.prepare_write_command(
        conn,
        execution_result_id=execution_id,
        result_ref=result_id,
        mapping_ref=ref,
        prepared_by="human:architect",
        idempotency_key=_id("prepare"),
    )


def _authorize(conn, command_id, action="authorize_application"):
    return apu_write_preparation.append_authorization(
        conn,
        command_id=command_id,
        action=action,
        note=None,
        authorized_by="human:architect",
        idempotency_key=_id("authorize"),
    )


def _apply(conn, command_id, key=None):
    return apu_write_preparation.apply_authorized_write_command(
        conn,
        command_id=command_id,
        applied_by="human:architect",
        idempotency_key=key or _id("apply"),
    )


def _write(conn, execution_id, result_id, ref, *, superseded=None):
    _review(conn, execution_id, result_id, ref, superseded=superseded)
    prepared = _prepare(conn, execution_id, result_id, ref)
    _authorize(conn, prepared["command_id"])
    return prepared, _apply(conn, prepared["command_id"])


def _claim_ids(anatomy: dict, family: str) -> set[str]:
    field = f"{family}_claims"
    id_field = f"{family}_claim_id"
    return {item[id_field] for item in anatomy[field]}


def test_supersede_and_add_claims_through_the_reviewed_chain(conn) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    hosted = {
        "relation_claim_id": "claim.door.hosted-by.t1",
        "subject_ref": {"entity_type": "stable_object", "entity_id": DOOR},
        "relation_type": "architecture.hosted_by",
        "object_ref": {"entity_type": "stable_object", "entity_id": WALL},
        "assertion_mode": "observed",
        "source_authority": "project_working_document",
        "proof_status": "candidate",
        "source_representation_refs": [REP_B],
    }
    execution_id, result_id = _bundle(
        conn,
        project_id,
        [_width("claim.door.width.t1", 0.93, supersedes_claim_ref="claim.door.width.t0")],
        [hosted],
    )

    prepared, applied = _write(
        conn, execution_id, result_id, "claim.door.width.t1", superseded="claim.door.width.t0"
    )
    assert prepared["operation"] == "supersede_claim"
    assert prepared["target_stable_object_ref"] is None
    assert prepared["expected_object_revision"] is None
    assert prepared["command"]["expected_owner_revision"] == 1
    assert applied["status"] == "applied"
    assert applied["event"]["event_type"] == "claim_superseded"
    assert applied["owner_revision"] == 2
    assert applied["claim"]["proof_status"] == "candidate"
    assert applied["authority"]["claim_professionally_validated"] is False
    assert applied["authority"]["canonizes_claims"] is False

    _prepared, added = _write(conn, execution_id, result_id, "claim.door.hosted-by.t1")
    assert added["event"]["event_type"] == "claim_added"
    assert added["owner_revision"] == 3

    anatomy = apu_owner.get_project_anatomy(conn, project_id=project_id)
    assert anatomy["owner_revision"] == 3
    assert _claim_ids(anatomy, "attribute") == {"claim.door.width.t1"}
    assert _claim_ids(anatomy, "relation") == {"claim.door.hosted-by.t1"}
    assert anatomy["superseded_claims"] == [
        {
            "claim_family": "attribute",
            "superseded_claim_ref": "claim.door.width.t0",
            "superseding_claim_ref": "claim.door.width.t1",
            "event_ref": applied["event"]["event_id"],
        }
    ]
    # The replaced claim is kept, unchanged.
    row = conn.execute(
        "SELECT claim_payload FROM agency_apu_attribute_claims WHERE claim_id = %s",
        ("claim.door.width.t0",),
    ).fetchone()
    assert row[0]["value"]["value"] == 0.90
    events = [event["event_type"] for event in apu_owner.list_apu_events(conn, project_id=project_id)]
    assert events == ["reviewed_dossier_imported", "claim_superseded", "claim_added"]


def test_application_replays_and_refuses_a_second_application(conn) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    execution_id, result_id = _bundle(conn, project_id, [_width("claim.door.width.t1", 0.93)], [])
    _review(conn, execution_id, result_id, "claim.door.width.t1")
    prepared = _prepare(conn, execution_id, result_id, "claim.door.width.t1")
    assert prepared["operation"] == "add_claim"
    _authorize(conn, prepared["command_id"])
    key = _id("apply")
    first = _apply(conn, prepared["command_id"], key)
    again = _apply(conn, prepared["command_id"], key)
    assert again["status"] == "replayed"
    assert again["event"]["event_id"] == first["event"]["event_id"]
    with pytest.raises(apu_write_preparation.ApuWriteApplicationConflict, match="already applied"):
        _apply(conn, prepared["command_id"])


def test_a_stale_owner_revision_blocks_the_second_of_two_commands(conn) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    execution_id, result_id = _bundle(
        conn,
        project_id,
        [_width("claim.door.width.a", 0.91), _width("claim.door.width.b", 0.92)],
        [],
    )
    commands = []
    for ref in ("claim.door.width.a", "claim.door.width.b"):
        _review(conn, execution_id, result_id, ref)
        prepared = _prepare(conn, execution_id, result_id, ref)
        _authorize(conn, prepared["command_id"])
        commands.append(prepared["command_id"])
    _apply(conn, commands[0])
    with pytest.raises(apu_write_preparation.ApuWriteApplicationConflict, match="stale APU owner revision"):
        _apply(conn, commands[1])


def test_a_claim_is_replaced_only_once(conn) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    execution_id, result_id = _bundle(
        conn,
        project_id,
        [_width("claim.door.width.a", 0.91), _width("claim.door.width.b", 0.92)],
        [],
    )
    _write(conn, execution_id, result_id, "claim.door.width.a", superseded="claim.door.width.t0")
    _review(conn, execution_id, result_id, "claim.door.width.b", superseded="claim.door.width.t0")
    with pytest.raises(apu_write_preparation.ApuWriteApplicationConflict, match="already replaced"):
        _prepare(conn, execution_id, result_id, "claim.door.width.b")


def test_replacement_must_share_subject_and_key(conn) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    other_key = _width("claim.door.height.t1", 2.10)
    other_key["attribute_key"] = "geometry.height"
    execution_id, result_id = _bundle(conn, project_id, [other_key], [])
    _review(conn, execution_id, result_id, "claim.door.height.t1", superseded="claim.door.width.t0")
    with pytest.raises(apu_write_preparation.ApuWritePreparationError, match="same subject and key"):
        _prepare(conn, execution_id, result_id, "claim.door.height.t1")


def test_a_declared_replacement_needs_the_review_to_accept_it(conn) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    execution_id, result_id = _bundle(
        conn,
        project_id,
        [_width("claim.door.width.t1", 0.93, supersedes_claim_ref="claim.door.width.t0")],
        [],
    )
    _review(conn, execution_id, result_id, "claim.door.width.t1")
    with pytest.raises(apu_write_preparation.ApuWritePreparationError, match="did not accept"):
        _prepare(conn, execution_id, result_id, "claim.door.width.t1")


def test_review_actions_follow_the_candidate_kind(conn) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    execution_id, result_id = _bundle(conn, project_id, [_width("claim.door.width.t1", 0.93)], [])
    for action in ("select_existing_object", "mark_unmatched"):
        with pytest.raises(apu_mapping_reviews.ApuMappingReviewError, match="claim candidate"):
            _review(conn, execution_id, result_id, "claim.door.width.t1", action=action)
    with pytest.raises(apu_mapping_reviews.ApuMappingReviewError, match="claim acceptance"):
        _review(
            conn,
            execution_id,
            result_id,
            "claim.door.width.t1",
            action="needs_clarification",
            superseded="claim.door.width.t0",
        )
    _review(conn, execution_id, result_id, "claim.door.width.t1", action="needs_clarification")
    with pytest.raises(apu_write_preparation.ApuWritePreparationError, match="accept_claim_candidate"):
        _prepare(conn, execution_id, result_id, "claim.door.width.t1")


def test_a_rejection_after_authorization_blocks_application(conn) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    execution_id, result_id = _bundle(conn, project_id, [_width("claim.door.width.t1", 0.93)], [])
    _review(conn, execution_id, result_id, "claim.door.width.t1")
    prepared = _prepare(conn, execution_id, result_id, "claim.door.width.t1")
    _authorize(conn, prepared["command_id"])
    _authorize(conn, prepared["command_id"], action="reject_application")
    with pytest.raises(apu_write_preparation.ApuWritePreparationError, match="authorize_application"):
        _apply(conn, prepared["command_id"])
    anatomy = apu_owner.get_project_anatomy(conn, project_id=project_id)
    assert anatomy["owner_revision"] == 1


def test_a_newer_review_supersedes_the_authorized_command(conn) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    execution_id, result_id = _bundle(conn, project_id, [_width("claim.door.width.t1", 0.93)], [])
    _review(conn, execution_id, result_id, "claim.door.width.t1")
    prepared = _prepare(conn, execution_id, result_id, "claim.door.width.t1")
    _authorize(conn, prepared["command_id"])
    _review(conn, execution_id, result_id, "claim.door.width.t1", action="reject_mapping")
    with pytest.raises(apu_write_preparation.ApuWritePreparationError, match="accept_claim_candidate"):
        _apply(conn, prepared["command_id"])


def test_a_claim_on_an_unknown_subject_is_refused(conn) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    orphan = _width("claim.ghost.width", 0.80)
    orphan["subject_ref"] = {"entity_type": "stable_object", "entity_id": "OBJ-GHOST"}
    execution_id, result_id = _bundle(conn, project_id, [orphan], [])
    _review(conn, execution_id, result_id, "claim.ghost.width")
    with pytest.raises(apu_write_preparation.ApuWritePreparationNotFound, match="claim subject"):
        _prepare(conn, execution_id, result_id, "claim.ghost.width")


def test_the_database_refuses_a_mismatched_supersession(conn) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    height = _width("claim.door.height.direct", 2.10)
    height["attribute_key"] = "geometry.height"
    apu_owner._insert_attribute_claim(conn, height, project_id=project_id, actor="test")
    event_id = apu_owner.list_apu_events(conn, project_id=project_id)[0]["event_id"]
    with pytest.raises(psycopg.errors.RaiseException, match="same subject and key"):
        with conn.transaction():
            conn.execute(
                "INSERT INTO agency_apu_claim_supersessions "
                "(superseded_claim_id, superseding_claim_id, claim_family, project_id, event_id) "
                "VALUES (%s, %s, 'attribute', %s, %s)",
                ("claim.door.width.t0", "claim.door.height.direct", project_id, event_id),
            )


def test_scoped_hermes_object_read_matches_global_supersession_and_preserves_history(conn) -> None:
    """Hermes must not revive an explicitly superseded width as a live conflict."""
    from mvp_vertical import hermes_scoped_context

    project_id = _project(conn)
    _import(conn, project_id)
    execution_id, result_id = _bundle(
        conn, project_id,
        [_width("claim.door.width.t1", 0.93, supersedes_claim_ref="claim.door.width.t0")],
        [],
    )
    _prepared, applied = _write(
        conn, execution_id, result_id,
        "claim.door.width.t1", superseded="claim.door.width.t0",
    )
    global_view = apu_owner.get_project_anatomy(conn, project_id=project_id)
    object_view = apu_object_read.get_stable_object_context(conn, object_id=DOOR)
    hermes_view = hermes_scoped_context.materialize_context_entity(
        conn, entity_type="stable_object", entity_id=f"stable_object:{DOOR}"
    )["record"]

    expected = [claim for claim in global_view["attribute_claims"]
                if claim["subject_ref"]["entity_id"] == DOOR]
    assert object_view["attribute_claims"] == expected
    assert hermes_view["attribute_claims"] == expected
    assert [claim["value"]["value"] for claim in expected] == [0.93]
    assert object_view["superseded_claims"] == global_view["superseded_claims"]
    assert hermes_view["superseded_claims"] == global_view["superseded_claims"]
    assert object_view["superseded_claims"][0]["event_ref"] == applied["event"]["event_id"]
    assert object_view["source_representation_refs"] == [REP_B]
    assert object_view["scope"]["relation_traversal_performed"] is False

    historical = conn.execute(
        "SELECT claim_payload FROM agency_apu_attribute_claims WHERE claim_id = %s",
        ("claim.door.width.t0",),
    ).fetchone()
    assert historical[0]["value"]["value"] == 0.90


def test_revision_a_source_cannot_be_attributed_to_version_b_bundle(conn) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    wrong_source = _width(
        "claim.door.width.wrong-revision", 0.93, source_representation_refs=[REP]
    )
    execution_id, result_id = _bundle(conn, project_id, [wrong_source], [])
    _review(conn, execution_id, result_id, wrong_source["attribute_claim_id"])
    with pytest.raises(
        apu_write_preparation.ApuWritePreparationError,
        match="source representation version is outside Observation Bundle basis",
    ):
        _prepare(conn, execution_id, result_id, wrong_source["attribute_claim_id"])


def test_claim_validity_cannot_name_a_different_source_version(conn) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    invalid = _width(
        "claim.door.width.wrong-validity",
        0.93,
        validity={"source_version_ref": "drawing:a101:index-a"},
    )
    execution_id, result_id = _bundle(conn, project_id, [invalid], [])
    _review(conn, execution_id, result_id, invalid["attribute_claim_id"])
    with pytest.raises(
        apu_write_preparation.ApuWritePreparationError,
        match="validity source_version_ref disagrees",
    ):
        _prepare(conn, execution_id, result_id, invalid["attribute_claim_id"])


def test_progressive_claim_requires_an_admitted_source_representation(conn) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    source_free = _width(
        "claim.door.width.without-source", 0.94, source_representation_refs=[]
    )
    execution_id, result_id = _bundle(conn, project_id, [source_free], [])
    _review(conn, execution_id, result_id, source_free["attribute_claim_id"])
    with pytest.raises(
        apu_write_preparation.ApuWritePreparationError,
        match="requires exact source representation provenance",
    ):
        _prepare(conn, execution_id, result_id, source_free["attribute_claim_id"])


def test_claim_cannot_reference_a_representation_owned_by_another_project(conn) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    other = _project(conn)
    foreign_rep = "rep.other-project"
    apu_owner.store_reviewed_dossier(
        conn,
        project_id=other,
        stable_objects=[{
            "stable_object_id": _id("other-object"),
            "project_ref": other,
            "object_family": "element",
            "nomenclature": {"display_name": "Other project's opening"},
        }],
        source_representations=[{
            "representation_id": foreign_rep,
            "project_ref": other,
            "source_artifact_ref": "source.pdf.a101",
            "source_version_ref": "drawing:a101:index-b",
            "source_kind": "drawing",
            "identifiers": [{"scheme": "drawing.local_label", "value": "foreign"}],
            "observed_at": "2026-03-02T10:00:00Z",
            "binding_ref": "binding.synthetic.drawing",
            "adapter_version": "1.0.0",
            "freshness_token": "sha256:a101-b",
            "proof_status": "candidate",
        }],
        attribute_claims=[],
        relation_claims=[],
        review_ref="review:claims:other",
        actor="human:architect",
        idempotency_key=_id("import-other"),
    )
    invalid = _width(
        "claim.door.width.cross-project",
        0.95,
        source_representation_refs=[foreign_rep],
    )
    execution_id, result_id = _bundle(conn, project_id, [invalid], [])
    _review(conn, execution_id, result_id, invalid["attribute_claim_id"])
    with pytest.raises(
        apu_write_preparation.ApuWritePreparationNotFound,
        match="source_representation_ref is not in this Project",
    ):
        _prepare(conn, execution_id, result_id, invalid["attribute_claim_id"])


def test_identity_relations_are_not_claim_writes() -> None:
    relation = {
        "relation_claim_id": "claim.door.merge",
        "subject_ref": {"entity_type": "stable_object", "entity_id": DOOR},
        "relation_type": "identity.merged_into",
        "object_ref": {"entity_type": "stable_object", "entity_id": WALL},
        "assertion_mode": "proposed",
        "source_authority": "model_interpretation_candidate",
        "proof_status": "candidate",
    }
    with pytest.raises(apu_owner.ApuOwnerError, match="identity relations"):
        apu_owner_claims.validate_claim_payload("relation", relation)
