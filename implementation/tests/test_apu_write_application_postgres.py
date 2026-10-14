"""PostgreSQL acceptance tests for bounded APU match application."""

from __future__ import annotations

import hashlib
import json
import uuid

import pytest

from mvp_vertical import (
    agency_data,
    apu_mapping_reviews,
    apu_owner,
    apu_write_preparation,
    execution_results,
    store,
)
from mvp_vertical.project_anatomy_projection import get_project_anatomy_projection


@pytest.fixture
def conn():
    try:
        connection = store.connect()
        connection.execute(agency_data.MIGRATION.read_text(encoding="utf-8"))
        connection.execute(execution_results.MIGRATION.read_text(encoding="utf-8"))
        connection.execute(apu_mapping_reviews.MIGRATION.read_text(encoding="utf-8"))
        connection.execute(apu_owner.MIGRATION.read_text(encoding="utf-8"))
        connection.execute(apu_write_preparation.MIGRATION.read_text(encoding="utf-8"))
        connection.execute(
            apu_write_preparation.APPLICATION_MIGRATION.read_text(encoding="utf-8")
        )
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


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _project(conn, label: str) -> str:
    project_id = _id("project")
    conn.execute(
        "INSERT INTO agency_projects "
        "(project_id, code, display_name, created_by, updated_by) "
        "VALUES (%s, %s, %s, 'test', 'test')",
        (project_id, _id(label), f"Projet {label}"),
    )
    return project_id


def _bootstrap_object(conn, project_id: str, object_id: str) -> None:
    apu_owner.store_reviewed_dossier(
        conn,
        project_id=project_id,
        stable_objects=[
            {
                "stable_object_id": object_id,
                "project_ref": project_id,
                "object_family": "spatial",
                "nomenclature": {
                    "internal_code": "ROOM-01",
                    "display_name": "Pièce test",
                },
            }
        ],
        source_representations=[],
        attribute_claims=[],
        relation_claims=[],
        review_ref="review:apu-bootstrap",
        actor="human:architect",
        idempotency_key=_id("apu-bootstrap"),
    )


def _persist_document_structure(
    conn,
    *,
    project_id: str,
    document_id: str,
    structure_id: str,
    fragment_id: str,
) -> None:
    source_digest = _sha(f"source:{document_id}")
    extraction_id = _id("extraction")
    body = "Pièce séjour"
    conn.execute(
        """
        INSERT INTO source_documents (
            document_id, dossier, parent_project_id, source_ref, source_digest,
            media_type, byte_size, analysis_status
        ) VALUES (%s, %s, %s, %s, %s, 'application/pdf', 128, 'ready')
        """,
        (document_id, project_id, project_id, f"plans/{document_id}.pdf", source_digest),
    )
    conn.execute(
        """
        INSERT INTO extraction_runs (
            extraction_id, document_id, contract_id, contract_digest,
            source_digest, converter, converter_version, config_digest,
            status, markdown_content, chunk_count, quality_flags
        ) VALUES (%s, %s, 'contract:apu-match', %s, %s, 'fixture', '1', %s,
                  'ready', %s, 0, '[]'::jsonb)
        """,
        (extraction_id, document_id, _sha("contract"), source_digest, _sha("config"), body),
    )
    conn.execute(
        """
        INSERT INTO structured_compilations (
            compilation_id, extraction_id, compiler, compiler_version,
            config_digest, output_digest, status, quality_flags, diagnostics,
            unit_count, chunk_count, page_count, table_count, anomaly_count
        ) VALUES (%s, %s, 'pantheon_structured_extraction', '2', %s, %s,
                  'ready', '[]'::jsonb, '[]'::jsonb, 1, 0, 1, 0, 0)
        """,
        (structure_id, extraction_id, _sha("compiler-config"), _sha("structure")),
    )
    conn.execute(
        """
        INSERT INTO extraction_units (
            unit_id, compilation_id, extraction_id, ordinal, content_type,
            body, text_digest, page_start, page_end, structural_locator,
            section_path, quality_flags
        ) VALUES (%s, %s, %s, 0, 'paragraph', %s, %s, 1, 1,
                  'page:1/paragraph:room', '[]'::jsonb, '[]'::jsonb)
        """,
        (fragment_id, structure_id, extraction_id, body, _sha(body)),
    )


def _persist_mapping_execution(
    conn,
    *,
    project_id: str,
    document_id: str,
    structure_id: str,
    fragment_id: str,
    object_id: str,
) -> tuple[str, str, str]:
    execution_id = _id("execution-mapping")
    result_id = _id("result-mapping")
    mapping_id = _id("mapping")
    execution_results.store_execution_result(
        conn,
        execution_result={
            "execution_result_id": execution_id,
            "task_contract_ref": "task-contract:apu-match",
            "project_ref": project_id,
            "producer": {"kind": "fixture", "version": "1"},
            "produced_at": "2026-08-09T09:00:00Z",
            "authority": dict(execution_results.AUTHORITY),
            "results": [
                {
                    "result_id": result_id,
                    "result_kind": "apu_object_mapping",
                    "schema_ref": (
                        "schemas/architecture-project-understanding/adapter_result.schema.yaml"
                    ),
                    "payload": {
                        "project_ref": project_id,
                        "document_ref": document_id,
                        "structure_ref": structure_id,
                        "mappings": [
                            {
                                "mapping_id": mapping_id,
                                "fragment_ref": fragment_id,
                                "candidate_object_ref": _id("candidate-room"),
                                "status": "candidate_matches",
                                "certainty": "E3",
                                "rationale": (
                                    "Le fragment revu peut représenter la pièce existante."
                                ),
                                "match_candidates": [
                                    {
                                        "stable_object_ref": object_id,
                                        "certainty": "E3",
                                        "rationale": "Objet sélectionné lors de la revue.",
                                    }
                                ],
                            }
                        ],
                    },
                }
            ],
            "clarification_requests": [],
        },
        idempotency_key=_id("mapping-execution"),
    )
    apu_mapping_reviews.append_mapping_review(
        conn,
        execution_result_id=execution_id,
        result_ref=result_id,
        mapping_ref=mapping_id,
        action="select_existing_object",
        selected_stable_object_ref=object_id,
        clarification_question=None,
        note="Sélection humaine bornée à ce mapping.",
        reviewer="human:architect",
        idempotency_key=_id("mapping-review"),
    )
    return execution_id, result_id, mapping_id


def test_full_reviewed_match_chain_writes_canonical_candidate_effect(conn) -> None:
    project_id = _project(conn, "chain")
    object_id = _id("space")
    document_id = _id("document")
    structure_id = _id("structure")
    fragment_id = _id("fragment")
    _bootstrap_object(conn, project_id, object_id)
    _persist_document_structure(
        conn,
        project_id=project_id,
        document_id=document_id,
        structure_id=structure_id,
        fragment_id=fragment_id,
    )
    execution_id, result_id, mapping_id = _persist_mapping_execution(
        conn,
        project_id=project_id,
        document_id=document_id,
        structure_id=structure_id,
        fragment_id=fragment_id,
        object_id=object_id,
    )

    prepared = apu_write_preparation.prepare_write_command(
        conn,
        execution_result_id=execution_id,
        result_ref=result_id,
        mapping_ref=mapping_id,
        prepared_by="human:architect",
        idempotency_key=_id("prepare-match"),
    )
    command = prepared["command"]
    representation = command["source_representation"]
    relation = command["identity_relation_claim"]
    assert representation["representation_id"] == prepared["source_candidate_ref"]
    assert "source_candidate_ref" not in command
    assert "target_stable_object_ref" not in command
    assert "source_artifact_ref" not in command
    assert representation["project_ref"] == project_id
    assert representation["source_artifact_ref"] == document_id
    assert representation["proof_status"] == "candidate"
    assert representation["identifiers"] == [
        {"scheme": "pantheon.document.fragment", "value": fragment_id},
        {"scheme": "pantheon.document.structure", "value": structure_id},
    ]
    assert relation["relation_type"] == "identity.represents"
    assert relation["subject_ref"] == {
        "entity_type": "source_representation",
        "entity_id": representation["representation_id"],
    }
    assert relation["object_ref"] == {
        "entity_type": "stable_object",
        "entity_id": object_id,
    }
    assert relation["assertion_mode"] == "proposed"
    assert relation["source_authority"] == "model_interpretation_candidate"
    assert relation["proof_status"] == "candidate"

    apu_write_preparation.append_authorization(
        conn,
        command_id=command["command_id"],
        action="authorize_application",
        note="Autorisation humaine de l'effet canonique candidat.",
        authorized_by="human:architect",
        idempotency_key=_id("authorize-match"),
    )
    application_key = _id("apply-match")
    first = apu_write_preparation.apply_authorized_write_command(
        conn,
        command_id=command["command_id"],
        applied_by="human:architect",
        idempotency_key=application_key,
    )
    replay = apu_write_preparation.apply_authorized_write_command(
        conn,
        command_id=command["command_id"],
        applied_by="human:architect",
        idempotency_key=application_key,
    )

    assert first["status"] == "applied"
    assert replay["status"] == "replayed"
    assert first["owner_revision"] == 2
    assert first["object"]["revision"] == 1
    assert first["canonical_effect"]["source_representation_reused"] is False
    assert replay["canonical_effect"]["source_representation_reused"] is True
    assert first["authority"]["stable_identity_professionally_validated"] is False
    assert first["authority"]["is_evidence"] is False
    assert first["authority"]["is_decision"] is False
    assert first["authority"]["authorizes_external_effect"] is False

    anatomy = apu_owner.get_project_anatomy(conn, project_id=project_id)
    assert anatomy["owner_revision"] == 2
    assert anatomy["stable_objects"][0]["revision"] == 1
    assert anatomy["source_representations"] == [representation | {"revision": 1}]
    assert anatomy["relation_claims"] == [relation]
    assert anatomy["attribute_claims"] == []

    projection = get_project_anatomy_projection(conn, project_id=project_id)
    source = projection["sources"][0]
    assert projection["summary"]["source_representation_count"] == 1
    assert projection["summary"]["relation_claim_count"] == 1
    assert source["identity_claims"][0]["proof_status"] == "candidate"
    assert source["mapped_object_refs"] == []
    assert [item["representation_id"] for item in projection["unmapped_material"]] == [
        representation["representation_id"]
    ]
    assert projection["authority"]["absence_inferred"] is False
    assert projection["authority"]["authorization_inferred"] is False

    events = apu_owner.list_apu_events(conn, project_id=project_id)
    assert [item["event_type"] for item in events] == [
        "reviewed_dossier_imported",
        "source_match_applied",
    ]
    assert events[-1]["payload"]["source_representation_ref"] == representation[
        "representation_id"
    ]
    assert events[-1]["payload"]["identity_relation_claim_ref"] == relation[
        "relation_claim_id"
    ]
    assert events[-1]["payload"]["stable_identity_professionally_validated"] is False


def test_preparation_refuses_document_structure_from_another_project(conn) -> None:
    project_id = _project(conn, "owner-scope")
    source_project_id = _project(conn, "source-scope")
    object_id = _id("space")
    document_id = _id("document")
    structure_id = _id("structure")
    fragment_id = _id("fragment")
    _bootstrap_object(conn, project_id, object_id)
    _persist_document_structure(
        conn,
        project_id=source_project_id,
        document_id=document_id,
        structure_id=structure_id,
        fragment_id=fragment_id,
    )
    execution_id, result_id, mapping_id = _persist_mapping_execution(
        conn,
        project_id=project_id,
        document_id=document_id,
        structure_id=structure_id,
        fragment_id=fragment_id,
        object_id=object_id,
    )

    with pytest.raises(
        apu_write_preparation.ApuWritePreparationError,
        match="belongs to another Project",
    ):
        apu_write_preparation.prepare_write_command(
            conn,
            execution_result_id=execution_id,
            result_ref=result_id,
            mapping_ref=mapping_id,
            prepared_by="human:architect",
            idempotency_key=_id("prepare-cross-project"),
        )

    anatomy = apu_owner.get_project_anatomy(conn, project_id=project_id)
    assert anatomy["owner_revision"] == 1
    assert anatomy["source_representations"] == []
    assert anatomy["relation_claims"] == []
