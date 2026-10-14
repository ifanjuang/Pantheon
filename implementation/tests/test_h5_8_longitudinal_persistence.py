"""H5.8 PostgreSQL acceptance for a bounded longitudinal Project Anatomy path."""

from __future__ import annotations

import uuid

import pytest

from mvp_vertical import (
    agency_data,
    apu_mapping_reviews,
    apu_owner,
    apu_write_preparation,
    execution_results,
)
from mvp_vertical.project_anatomy_projection import get_project_anatomy_projection


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


def _project(conn) -> str:
    project_id = _id("project-h58")
    conn.execute(
        "INSERT INTO agency_projects "
        "(project_id, code, display_name, created_by, updated_by) "
        "VALUES (%s, %s, %s, 'test', 'test')",
        (project_id, _id("H58"), "H5.8 longitudinal acceptance"),
    )
    return project_id


def _t0_dossier(project_id: str, object_id: str) -> tuple[dict, dict, dict]:
    stable = {
        "stable_object_id": object_id,
        "project_ref": project_id,
        "object_family": "element",
        "nomenclature": {
            "internal_code": "P17",
            "display_name": "Baie séjour",
            "aliases": ["P12"],
            "name_history": [{"value": "P12", "source_ref": "drawing:a101:index-a"}],
        },
    }
    representation = {
        "representation_id": "rep.pdf.h58.opening-017.t0",
        "project_ref": project_id,
        "source_artifact_ref": "source.pdf.esq.a101",
        "source_version_ref": "drawing:a101:index-a",
        "source_kind": "drawing",
        "identifiers": [{"scheme": "drawing.local_label", "value": "P12"}],
        "observed_at": "2026-01-10T09:00:00Z",
        "binding_ref": "binding.synthetic.drawing",
        "adapter_version": "1.0.0",
        "freshness_token": "sha256:h58-a101-a",
        "content_digest": "sha256:h58-pdf-p12-t0",
        "proof_status": "accepted_as_support",
    }
    width = {
        "attribute_claim_id": "claim.h58.t0.pdf.opening017.width",
        "subject_ref": {
            "entity_type": "source_representation",
            "entity_id": representation["representation_id"],
        },
        "attribute_key": "geometry.width",
        "value": {"value_type": "number", "value": 0.90, "unit": "m"},
        "assertion_mode": "observed",
        "source_authority": "project_working_document",
        "proof_status": "accepted_as_support",
        "source_representation_refs": [representation["representation_id"]],
        "validity": {"established_at_phase": "DIAG"},
    }
    identity = {
        "relation_claim_id": "identity.h58.t0.pdf.opening017",
        "subject_ref": {
            "entity_type": "source_representation",
            "entity_id": representation["representation_id"],
        },
        "relation_type": "identity.represents",
        "object_ref": {"entity_type": "stable_object", "entity_id": object_id},
        "assertion_mode": "human_asserted",
        "source_authority": "project_working_document",
        "proof_status": "accepted_as_support",
        "source_representation_refs": [representation["representation_id"]],
        "validity": {"established_at_phase": "DIAG"},
    }
    return stable, representation, {"width": width, "identity": identity}


def _t3_bundle(project_id: str, object_id: str, task_contract_ref: str) -> tuple[dict, str, str]:
    representation_id = "rep.revit.h58.opening-017.t3"
    relation_id = "identity.h58.t3.revit.opening017"
    representation = {
        "representation_id": representation_id,
        "project_ref": project_id,
        "source_artifact_ref": "source.revit.exe",
        "source_version_ref": "revit:model-save-118",
        "source_kind": "revit",
        "identifiers": [{"scheme": "revit.unique_id", "value": "uid-opening-17-t3"}],
        "observed_at": "2026-05-14T08:45:00Z",
        "binding_ref": "binding.synthetic.revit",
        "adapter_version": "1.0.0",
        "freshness_token": "sha256:h58-revit-118",
        "content_digest": "sha256:h58-revit-opening17-t3",
        "proof_status": "candidate",
    }
    relation = {
        "relation_claim_id": relation_id,
        "subject_ref": {"entity_type": "source_representation", "entity_id": representation_id},
        "relation_type": "identity.represents",
        "object_ref": {"entity_type": "stable_object", "entity_id": object_id},
        "assertion_mode": "proposed",
        "source_authority": "model_interpretation_candidate",
        "proof_status": "candidate",
        "certainty": "E3",
        "source_representation_refs": [representation_id],
        "notes": "Revit occurrence may represent the previously reviewed opening.",
        "validity": {"established_at_phase": "EXE"},
    }
    width = {
        "attribute_claim_id": "claim.h58.t3.revit.opening017.width",
        "subject_ref": {"entity_type": "source_representation", "entity_id": representation_id},
        "attribute_key": "geometry.width",
        "value": {"value_type": "number", "value": 0.93, "unit": "m"},
        "assertion_mode": "observed",
        "source_authority": "model_interpretation_candidate",
        "proof_status": "candidate",
        "certainty": "E3",
        "source_representation_refs": [representation_id],
        "validity": {"established_at_phase": "EXE"},
    }
    payload = {
        "observation_bundle_id": "observation-bundle.h58.t3.revit",
        "project_ref": project_id,
        "task_contract_ref": task_contract_ref,
        "basis": {
            "source_artifact_refs": ["source.revit.exe"],
            "source_version_refs": ["revit:model-save-118"],
            "exact_digests": [
                {
                    "source_artifact_ref": "source.revit.exe",
                    "source_version_ref": "revit:model-save-118",
                    "digest": "sha256:h58-revit-118",
                }
            ],
        },
        "method": {
            "capability_id": "revit.observe.openings",
            "binding_id": "binding.synthetic.revit",
            "operation_id": "revit.observe.openings.v1",
            "adapter_ref": "pantheon.synthetic.revit",
            "adapter_version": "1.0.0",
            "request_ref": "request:h58:t3",
        },
        "observed_at": "2026-05-14T08:45:00Z",
        "freshness_token": "sha256:h58-revit-118",
        "scope": {
            "document_refs": ["revit-document:h58"],
            "level_refs": ["level:00", "level:01"],
            "categories": ["OST_Doors"],
        },
        "coverage": {
            "completeness": "partial_for_declared_scope",
            "observed_scope": {
                "document_refs": ["revit-document:h58"],
                "level_refs": ["level:00"],
                "categories": ["OST_Doors"],
            },
            "excluded_reasons": ["level_01_not_traversed"],
            "absence_inference_allowed": False,
        },
        "limitations": ["Only level 00 was traversed; no deletion may be inferred for level 01."],
        "source_representations": [representation],
        "attribute_claim_candidates": [width],
        "relation_claim_candidates": [relation],
        "gaps": [{"code": "coverage.level_not_traversed", "subject_refs": ["level:01"]}],
        "withheld": [],
        "warnings": [{"code": "absence.inference_forbidden", "message": "Partial coverage cannot establish deletion."}],
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
    return payload, representation_id, relation_id


def test_h5_8_t0_to_t3_path_persists_reviewed_identity_without_collapsing_history(conn) -> None:
    project_id = _project(conn)
    object_id = "OBJ-OPENING-017"
    stable, t0_representation, t0 = _t0_dossier(project_id, object_id)

    apu_owner.store_reviewed_dossier(
        conn,
        project_id=project_id,
        stable_objects=[stable],
        source_representations=[t0_representation],
        attribute_claims=[t0["width"]],
        relation_claims=[t0["identity"]],
        review_ref="review:h58:t0",
        actor="human:architect",
        idempotency_key=_id("h58-t0-dossier"),
    )

    task_contract_ref = "task-contract:h58:revit-observe"
    bundle, representation_id, relation_id = _t3_bundle(project_id, object_id, task_contract_ref)
    execution_result_id = _id("execution-h58-t3")
    result_id = _id("result-h58-t3")

    execution_results.store_execution_result(
        conn,
        execution_result={
            "execution_result_id": execution_result_id,
            "task_contract_ref": task_contract_ref,
            "project_ref": project_id,
            "producer": {"runtime": "synthetic-revit-h58", "binding_ref": "binding.synthetic.revit"},
            "produced_at": "2026-05-14T08:46:00Z",
            "authority": dict(execution_results.AUTHORITY),
            "results": [
                {
                    "result_id": result_id,
                    "result_kind": "observation_bundle",
                    "schema_ref": execution_results.OBSERVATION_BUNDLE_SCHEMA_REF,
                    "payload": bundle,
                }
            ],
            "clarification_requests": [],
        },
        idempotency_key=_id("h58-store-result"),
    )

    review = apu_mapping_reviews.append_mapping_review(
        conn,
        execution_result_id=execution_result_id,
        result_ref=result_id,
        mapping_ref=relation_id,
        action="select_existing_object",
        selected_stable_object_ref=object_id,
        clarification_question=None,
        note="Reviewed continuity from T0 drawing identity to T3 Revit occurrence.",
        reviewer="human:architect",
        idempotency_key=_id("h58-mapping-review"),
    )
    assert review["authority"]["confirms_stable_identity"] is False

    command = apu_write_preparation.prepare_write_command(
        conn,
        execution_result_id=execution_result_id,
        result_ref=result_id,
        mapping_ref=relation_id,
        prepared_by="human:architect",
        idempotency_key=_id("h58-prepare-write"),
    )
    assert command["command"]["source_representation"]["representation_id"] == representation_id
    assert command["command"]["identity_relation_claim"]["relation_claim_id"] == relation_id
    assert "claim.h58.t3.revit.opening017.width" not in str(command["command"])

    authorization = apu_write_preparation.append_authorization(
        conn,
        command_id=command["command_id"],
        action="authorize_application",
        note="Authorize only the reviewed identity match.",
        authorized_by="human:architect",
        idempotency_key=_id("h58-authorize"),
    )
    assert authorization["authority"]["authorizes_command_application"] is True
    assert authorization["authority"]["confirms_stable_identity"] is False

    receipt = apu_write_preparation.apply_authorized_write_command(
        conn,
        command_id=command["command_id"],
        applied_by="human:architect",
        idempotency_key=_id("h58-apply"),
    )
    assert receipt["authority"]["match_recorded"] is True
    assert receipt["authority"]["stable_identity_professionally_validated"] is False
    assert receipt["authority"]["is_evidence"] is False

    stored_execution = execution_results.get_execution_result(conn, execution_result_id)
    sibling_width = stored_execution["results"][0]["payload"]["attribute_claim_candidates"][0]
    assert sibling_width["attribute_claim_id"] == "claim.h58.t3.revit.opening017.width"
    assert sibling_width["value"] == {"value_type": "number", "value": 0.93, "unit": "m"}
    assert stored_execution["results"][0]["payload"]["coverage"]["absence_inference_allowed"] is False

    anatomy = apu_owner.get_project_anatomy(conn, project_id=project_id)
    assert anatomy["owner_revision"] == 2
    assert [claim["attribute_claim_id"] for claim in anatomy["attribute_claims"]] == [
        "claim.h58.t0.pdf.opening017.width"
    ]
    assert {claim["relation_claim_id"] for claim in anatomy["relation_claims"]} == {
        "identity.h58.t0.pdf.opening017",
        relation_id,
    }

    projection = get_project_anatomy_projection(conn, project_id=project_id)
    assert projection["authority"]["cockpit_projection_only"] is True
    assert projection["authority"]["authorization_inferred"] is False
    assert projection["coverage"]["absence_inference_allowed"] is False

    pdf_source = next(item for item in projection["sources"] if item["representation_id"] == t0_representation["representation_id"])
    revit_source = next(item for item in projection["sources"] if item["representation_id"] == representation_id)
    assert pdf_source["mapped_object_refs"] == [object_id]
    assert revit_source["identity_claims"][0]["proof_status"] == "candidate"
    assert revit_source["mapped_object_refs"] == []
    assert revit_source in projection["unmapped_material"]

    events = apu_owner.list_apu_events(conn, project_id=project_id)
    assert [event["event_type"] for event in events] == [
        "reviewed_dossier_imported",
        "source_match_applied",
    ]
    assert events[-1]["payload"]["stable_identity_professionally_validated"] is False
    assert events[-1]["payload"]["evidence_admitted"] is False
