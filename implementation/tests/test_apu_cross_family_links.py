"""PostgreSQL acceptance for APU cross-family references."""

from __future__ import annotations

import uuid

import psycopg
import pytest

from mvp_vertical import (
    agency_claims,
    agency_data,
    apu_cross_family,
    apu_owner,
    decision_requests,
    execution_results,
    project_claim_candidates,
    store,
)


def _id(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex}"


@pytest.fixture
def conn():
    try:
        connection = store.connect()
    except Exception as exc:  # pragma: no cover - local unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    for migration in (
        agency_data.MIGRATION,
        apu_owner.MIGRATION,
        decision_requests.MIGRATION,
        decision_requests.HUMAN_RESPONSE_MIGRATION,
        decision_requests.EFFECT_BINDING_MIGRATION,
        execution_results.MIGRATION,
        agency_claims.MIGRATION,
        apu_cross_family.MIGRATION,
    ):
        connection.execute(migration.read_text(encoding="utf-8"))
    connection.execute(
        """
        TRUNCATE agency_decision_request_scope_refs,
                 agency_decision_events, agency_human_responses,
                 agency_decision_records,
                 agency_decision_options, agency_decision_requests,
                 agency_project_claims,
                 execution_result_review_dispositions,
                 execution_clarification_requests, execution_result_items, execution_results,
                 agency_apu_relation_claims, agency_apu_attribute_claims,
                 agency_apu_source_representations, agency_apu_events,
                 agency_apu_objects, agency_apu_project_state,
                 agency_information_cards, agency_project_events, agency_projects
        RESTART IDENTITY CASCADE
        """
    )
    connection.commit()
    yield connection
    connection.close()


def _project(conn, label: str) -> str:
    project_id = _id("project")
    agency_data.create_project(
        conn,
        project_id=project_id,
        code=_id(label)[:24],
        display_name=f"Projet {label}",
        actor="human:test",
        actor_kind="human",
        idempotency_key=_id("project-create"),
        attributes={"programme_summary": "Maison individuelle"},
    )
    return project_id


def _apu_object(project_id: str, object_id: str) -> dict:
    return {
        "stable_object_id": object_id,
        "project_ref": project_id,
        "object_family": "spatial",
        "nomenclature": {"display_name": object_id},
    }


def _bootstrap_apu(conn, project_id: str, *, object_id: str | None = None) -> str:
    target = object_id or _id("apu-space")
    apu_owner.store_reviewed_dossier(
        conn,
        project_id=project_id,
        stable_objects=[_apu_object(project_id, target)],
        source_representations=[],
        attribute_claims=[],
        relation_claims=[],
        review_ref=_id("review"),
        actor="human:architect",
        idempotency_key=_id("apu-bootstrap"),
    )
    return target


def _request_kwargs(project_id: str, *, request_id: str | None = None, key: str | None = None) -> dict:
    return {
        "request_id": request_id or _id("decision-request"),
        "decision_type": "validation",
        "question": "Cette pièce est-elle bien la chambre principale ?",
        "priority": "normal",
        "response_mode": "decision_value",
        "blocking": False,
        "candidate_ref": _id("candidate"),
        "candidate_digest": "a" * 64,
        "decision_surface": "cockpit.project-anatomy",
        "decision_owner": "architect-project-owner",
        "created_by": "human:architect",
        "idempotency_key": key or _id("decision-create"),
        "project_ref": project_id,
    }


def test_decision_request_scope_ref_is_request_owned_and_queryable(conn) -> None:
    project_id = _project(conn, "decision-scope")
    object_id = _bootstrap_apu(conn, project_id)
    scope = {"entity_type": "apu_object", "entity_id": object_id}

    projection = apu_cross_family.create_decision_request(
        conn,
        scope_refs=[scope],
        **_request_kwargs(project_id),
    )

    request = projection["decision_request"]
    assert request["scope_refs"] == [scope]
    assert request["project_ref"] == project_id
    assert projection["request_is_not_decision"] is True

    reverse = apu_cross_family.list_decision_requests_for_apu_object(
        conn,
        object_id=object_id,
    )
    assert [item["decision_request"]["request_id"] for item in reverse] == [
        request["request_id"]
    ]


def test_decision_scope_ref_refuses_unknown_and_cross_project_objects(conn) -> None:
    project_a = _project(conn, "scope-a")
    project_b = _project(conn, "scope-b")
    foreign_object = _bootstrap_apu(conn, project_b)

    with pytest.raises(apu_cross_family.ApuCrossFamilyError, match="another Project"):
        apu_cross_family.create_decision_request(
            conn,
            scope_refs=[{"entity_type": "apu_object", "entity_id": foreign_object}],
            **_request_kwargs(project_a),
        )

    with pytest.raises(apu_cross_family.ApuCrossFamilyError):
        apu_cross_family.create_decision_request(
            conn,
            scope_refs=[{"entity_type": "apu_object", "entity_id": _id("missing-apu")}],
            **_request_kwargs(project_a),
        )


def test_decision_scope_replay_is_exact_and_scope_rows_are_append_only(conn) -> None:
    project_id = _project(conn, "scope-replay")
    object_a = _bootstrap_apu(conn, project_id)
    object_b = _id("apu-space")
    # The owner exposes no incremental create-object command; a second reviewed Project
    # gives us a distinct valid id for the replay-mismatch check only.
    other_project = _project(conn, "scope-replay-other")
    _bootstrap_apu(conn, other_project, object_id=object_b)
    request_id = _id("decision-request")
    key = _id("decision-create")
    kwargs = _request_kwargs(project_id, request_id=request_id, key=key)
    scope = {"entity_type": "apu_object", "entity_id": object_a}

    first = apu_cross_family.create_decision_request(conn, scope_refs=[scope], **kwargs)
    replay = apu_cross_family.create_decision_request(conn, scope_refs=[scope], **kwargs)
    assert replay["decision_request"] == first["decision_request"]

    with pytest.raises(decision_requests.DecisionRequestConflict, match="scope_refs"):
        apu_cross_family.create_decision_request(
            conn,
            scope_refs=[{"entity_type": "apu_object", "entity_id": object_b}],
            **kwargs,
        )

    with pytest.raises(psycopg.errors.RaiseException, match="immutable"):
        with conn.transaction():
            conn.execute(
                "UPDATE agency_decision_request_scope_refs SET ordinal = 4 WHERE request_id = %s",
                (request_id,),
            )


def test_resolved_decision_reuses_request_scope_without_duplicate_owner(conn) -> None:
    project_id = _project(conn, "decision-resolved")
    object_id = _bootstrap_apu(conn, project_id)
    created = apu_cross_family.create_decision_request(
        conn,
        scope_refs=[{"entity_type": "apu_object", "entity_id": object_id}],
        **_request_kwargs(project_id),
    )
    request = created["decision_request"]

    decision_requests.resolve_request(
        conn,
        request_id=request["request_id"],
        decision_id=_id("decision"),
        decision="approve",
        decided_by="human:architect",
        identity_assurance="declared",
        expected_revision=request["revision"],
        idempotency_key=_id("decision-resolve"),
    )
    decision_id = decision_requests.get_request(conn, request["request_id"])["decision_record"][
        "decision_id"
    ]
    projection = apu_cross_family.get_decision(conn, decision_id)
    assert projection["scope_refs"] == [
        {"entity_type": "apu_object", "entity_id": object_id}
    ]
    assert projection["scope_refs_are_request_owned"] is True


def test_source_backed_project_claim_can_reference_same_project_apu_object(conn) -> None:
    project_id = _project(conn, "claim-apu")
    object_id = _bootstrap_apu(conn, project_id)

    claim = agency_claims.record_claim(
        conn,
        project_id=project_id,
        claim_type="budget",
        value=375000,
        actor="human:architect",
        source_kind="human_assertion",
        backing_ref={"entity_type": "apu_object", "entity_id": object_id},
        status="source_backed",
        certainty="E3",
    )
    assert claim["backing_ref"]["entity_type"] == "apu_object"
    assert claim["backing_ref"]["entity_id"] == object_id
    assert apu_cross_family.list_project_claims_for_apu_object(
        conn, object_id=object_id
    )[0]["claim_id"] == claim["claim_id"]


def test_project_claim_apu_backing_refuses_cross_project_object(conn) -> None:
    project_a = _project(conn, "claim-a")
    project_b = _project(conn, "claim-b")
    foreign_object = _bootstrap_apu(conn, project_b)

    with pytest.raises(psycopg.errors.RaiseException, match="Claim Project"):
        agency_claims.record_claim(
            conn,
            project_id=project_a,
            claim_type="budget",
            value=375000,
            actor="human:architect",
            source_kind="human_assertion",
            backing_ref={"entity_type": "apu_object", "entity_id": foreign_object},
            status="source_backed",
            certainty="E2",
        )


def test_reviewed_execution_candidate_may_use_apu_object_basis_without_promotion(conn) -> None:
    project_id = _project(conn, "candidate-apu")
    object_id = _bootstrap_apu(conn, project_id)
    execution_id = _id("execution")
    result_id = _id("result")
    observed_status = "accepted_as_support"
    execution_results.store_execution_result(
        conn,
        execution_result={
            "execution_result_id": execution_id,
            "task_contract_ref": "task-contract.project-claim",
            "project_ref": project_id,
            "producer": {
                "capability": "extract_project_claim",
                "implementation": "hermes.skill.project-claim",
                "version": "1.0.0",
            },
            "produced_at": "2026-08-07T09:00:00+00:00",
            "authority": dict(execution_results.AUTHORITY),
            "results": [
                {
                    "result_id": result_id,
                    "result_kind": "project_claim_candidate",
                    "schema_ref": "schemas/project_claim_candidate.schema.yaml",
                    "payload": {
                        "project_ref": project_id,
                        "claim_type": "budget",
                        "proposed_value": 375000,
                        "unit": "EUR",
                        "certainty": "E2",
                        "observed_at": "2026-08-07T09:00:00+00:00",
                        "effective_at": None,
                        "basis_refs": [
                            {
                                "entity_type": "apu_object",
                                "entity_id": object_id,
                                "observed_revision": 1,
                                "observed_status": observed_status,
                            }
                        ],
                        "supersedes_claim_ref": None,
                        "rationale": "Budget rattaché à un objet projet revu.",
                        "limitations": ["Le rattachement ne valide pas le montant."],
                        "authority": {
                            "creates_project_claim": False,
                            "adopts_project_truth": False,
                            "admits_evidence": False,
                            "creates_decision": False,
                            "creates_work_issue": False,
                            "authorizes_effect": False,
                        },
                    },
                }
            ],
            "clarification_requests": [],
        },
        idempotency_key=_id("execution-store"),
    )
    accepted = execution_results.append_review_disposition(
        conn,
        result_ref=result_id,
        disposition="accepted_for_claim",
        reviewer="human:architect",
        reviewer_kind="human",
        note="Candidat retenu pour création séparée du Claim.",
        idempotency_key=_id("review"),
    )
    assert accepted["review_dispositions"][-1]["disposition"] == "accepted_for_claim"

    claim = project_claim_candidates.create_claim_from_candidate(
        conn,
        execution_id=execution_id,
        result_id=result_id,
        actor="human:architect",
        status="source_backed",
        certainty="E3",
        backing_ref={
            "entity_type": "apu_object",
            "entity_id": object_id,
            "observed_status": observed_status,
        },
    )
    assert claim["backing_ref"]["entity_type"] == "apu_object"
    assert claim["provenance"]["source_kind"] == "execution_result"
    assert execution_results.get_execution_result(conn, execution_id)["authority"]["is_fact"] is False
