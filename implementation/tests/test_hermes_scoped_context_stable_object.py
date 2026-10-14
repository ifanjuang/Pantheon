"""Acceptance coverage for admitted Project Anatomy stable-object reads."""

from __future__ import annotations

import uuid

import pytest

from mvp_vertical import (
    agency_data,
    apu_owner,
    hermes_execution,
    hermes_handoff_preview,
    hermes_handoff_store,
    hermes_scoped_context,
    work_issues,
)


def _id(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex}"


@pytest.fixture
def conn():
    try:
        connection = agency_data.connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(agency_data.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(apu_owner.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(work_issues.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(hermes_handoff_store.MIGRATION.read_text(encoding="utf-8"))
    for migration in hermes_execution.MIGRATIONS:
        connection.execute(migration.read_text(encoding="utf-8"))
    connection.commit()
    yield connection
    connection.close()


def _stable(project_id: str, object_id: str, *, name: str) -> dict:
    return {
        "stable_object_id": object_id,
        "project_ref": project_id,
        "object_family": "element",
        "nomenclature": {
            "internal_code": object_id[-12:],
            "display_name": name,
        },
    }


def _representation(project_id: str, representation_id: str) -> dict:
    return {
        "representation_id": representation_id,
        "project_ref": project_id,
        "source_artifact_ref": "drawing.context.A",
        "source_kind": "drawing",
        "identifiers": [{"scheme": "drawing.fragment", "value": representation_id}],
        "observed_at": "2026-09-06T08:00:00Z",
        "binding_ref": "fixture.context.drawing",
        "adapter_version": "1.0",
        "freshness_token": "drawing-context-A:1",
        "proof_status": "candidate",
    }


def _attribute(object_id: str, claim_id: str, representation_id: str) -> dict:
    return {
        "attribute_claim_id": claim_id,
        "subject_ref": {"entity_type": "stable_object", "entity_id": object_id},
        "attribute_key": "geometry.width",
        "value": {"value_type": "number", "value": 120, "unit": "mm"},
        "assertion_mode": "observed",
        "source_authority": "project_working_document",
        "proof_status": "candidate",
        "source_representation_refs": [representation_id],
    }


def _relation(
    subject_id: str,
    object_id: str,
    claim_id: str,
    representation_id: str,
    *,
    relation_type: str,
) -> dict:
    return {
        "relation_claim_id": claim_id,
        "subject_ref": {"entity_type": "stable_object", "entity_id": subject_id},
        "relation_type": relation_type,
        "object_ref": {"entity_type": "stable_object", "entity_id": object_id},
        "assertion_mode": "human_asserted",
        "source_authority": "project_working_document",
        "proof_status": "accepted_as_support",
        "source_representation_refs": [representation_id],
    }


def _running_with_stable_object(conn):
    project = agency_data.create_project(
        conn,
        project_id=_id("project"),
        code=_id("CTX").upper(),
        display_name="Projet contexte Anatomy",
        actor="human-reviewer",
        actor_kind="human",
        idempotency_key=_id("project-create"),
    )
    project_id = project["project_id"]
    root_object = _id("apu-wall")
    outgoing_neighbour = _id("apu-door")
    incoming_neighbour = _id("apu-space")
    representation_id = _id("representation")
    outgoing_relation = _id("relation-out")
    incoming_relation = _id("relation-in")

    apu_owner.store_reviewed_dossier(
        conn,
        project_id=project_id,
        stable_objects=[
            _stable(project_id, root_object, name="Cloison analysée"),
            _stable(project_id, outgoing_neighbour, name="Porte voisine"),
            _stable(project_id, incoming_neighbour, name="Espace voisin"),
        ],
        source_representations=[_representation(project_id, representation_id)],
        attribute_claims=[_attribute(root_object, _id("attribute"), representation_id)],
        relation_claims=[
            _relation(
                root_object,
                outgoing_neighbour,
                outgoing_relation,
                representation_id,
                relation_type="architecture.hosted_by",
            ),
            _relation(
                incoming_neighbour,
                root_object,
                incoming_relation,
                representation_id,
                relation_type="spatial.adjacent_to",
            ),
        ],
        review_ref="review:architect:2026-09-06",
        actor="human:architect",
        idempotency_key=_id("apu-bootstrap"),
    )

    selected = [
        {
            "entity_id": f"stable_object:{root_object}",
            "entity_type": "stable_object",
        }
    ]
    envelope = {
        "root_entity": {
            "entity_id": f"project:{project_id}",
            "entity_type": "project",
        },
        "descendants": [],
        "source_refs": [],
        "explicit_additions": [],
        "explicit_exclusions": [],
        "scope_widened_implicitly": False,
    }
    preview = hermes_handoff_preview.build_preview(
        question="Que savons-nous directement sur cette cloison ?",
        card_context_envelope=envelope,
        selected_context=selected,
    )
    handoff = hermes_handoff_store.submit_handoff(
        conn,
        actor="ifan",
        idempotency_key=_id("handoff"),
        question="Que savons-nous directement sur cette cloison ?",
        preview=preview,
        card_context_envelope=envelope,
        selected_context=selected,
        include_declared_descendants=False,
    )
    admission = hermes_execution.admit_handoff(
        conn,
        handoff_id=handoff["handoff_id"],
        actor="ifan",
        idempotency_key=_id("admit"),
        ttl_seconds=900,
    )
    run_id = _id("hermes-run")
    hermes_execution.record_external_runtime_start(
        conn,
        admission_id=admission["admission_id"],
        run_id=run_id,
        actor="hermes-runtime",
        expected_issue_version=handoff["work_issue"]["version"],
        idempotency_key=_id("start"),
    )
    return {
        "admission": admission,
        "run_id": run_id,
        "project_id": project_id,
        "root_object": root_object,
        "outgoing_neighbour": outgoing_neighbour,
        "incoming_neighbour": incoming_neighbour,
        "representation_id": representation_id,
        "outgoing_relation": outgoing_relation,
        "incoming_relation": incoming_relation,
    }


def test_admitted_stable_object_exposes_direct_claims_without_scope_widening(conn) -> None:
    state = _running_with_stable_object(conn)
    admission = state["admission"]

    manifest = hermes_scoped_context.get_context_manifest(
        conn,
        admission_id=admission["admission_id"],
        run_id=state["run_id"],
        actor="hermes-runtime",
    )
    stable_ref = next(
        item
        for item in manifest["entities"]
        if item["entity_type"] == "stable_object"
    )
    assert stable_ref == {
        "entity_id": f"stable_object:{state['root_object']}",
        "entity_type": "stable_object",
        "materializable": True,
    }
    assert manifest["global_search_available"] is False
    assert manifest["global_listing_available"] is False
    assert manifest["source_dereference_available"] is False

    materialized = hermes_scoped_context.get_context_entity(
        conn,
        admission_id=admission["admission_id"],
        run_id=state["run_id"],
        entity_type="stable_object",
        entity_id=f"stable_object:{state['root_object']}",
        actor="hermes-runtime",
    )
    record = materialized["record"]

    assert materialized["record_owner_system"] == "postgres_apu_object_projection"
    assert materialized["current_revision"] == 1
    assert record["object_id"] == state["root_object"]
    assert record["project_ref"] == state["project_id"]
    assert record["stable_object"]["nomenclature"]["display_name"] == "Cloison analysée"
    assert [claim["attribute_key"] for claim in record["attribute_claims"]] == [
        "geometry.width"
    ]
    assert {claim["relation_claim_id"] for claim in record["relation_claims"]} == {
        state["outgoing_relation"],
        state["incoming_relation"],
    }
    assert record["source_representation_refs"] == [state["representation_id"]]

    relation_endpoint_ids = {
        (claim.get("subject_ref") or {}).get("entity_id")
        for claim in record["relation_claims"]
    } | {
        (claim.get("object_ref") or {}).get("entity_id")
        for claim in record["relation_claims"]
    }
    assert state["outgoing_neighbour"] in relation_endpoint_ids
    assert state["incoming_neighbour"] in relation_endpoint_ids

    assert record["scope"] == {
        "exact_stable_object_only": True,
        "direct_attribute_claims_only": True,
        "direct_relation_claims_only": True,
        "relation_traversal_performed": False,
        "neighbour_records_materialized": False,
        "global_search_performed": False,
        "global_listing_performed": False,
    }
    assert record["authority"]["projection_only"] is True
    assert record["authority"]["creates_project_fact"] is False
    assert record["authority"]["resolves_relation_semantics"] is False
    assert record["authority"]["matches_requirements"] is False
    assert "requirements" not in record
    assert "relation_semantics" not in record
    assert "neighbours" not in record

    with pytest.raises(
        hermes_scoped_context.ScopedContextConflict,
        match="outside the exact admitted Context Pack",
    ):
        hermes_scoped_context.get_context_entity(
            conn,
            admission_id=admission["admission_id"],
            run_id=state["run_id"],
            entity_type="stable_object",
            entity_id=f"stable_object:{state['outgoing_neighbour']}",
            actor="hermes-runtime",
        )
