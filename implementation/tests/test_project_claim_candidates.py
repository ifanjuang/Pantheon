from __future__ import annotations

import uuid

import pytest

from mvp_vertical import (
    agency_claims,
    agency_data,
    execution_results,
    project_claim_candidates,
)


def _id(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex}"


@pytest.fixture
def conn():
    try:
        connection = agency_data.connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    execution_results.ensure_schema(connection)
    connection.execute(agency_claims.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(agency_claims.PROVENANCE_MIGRATION.read_text(encoding="utf-8"))
    connection.execute(
        "TRUNCATE agency_project_claims, execution_result_review_dispositions, "
        "execution_clarification_requests, execution_result_items, execution_results, "
        "agency_change_candidate_events, agency_change_candidates, "
        "agency_project_events, agency_projects RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _project(conn) -> dict:
    return agency_data.create_project(
        conn,
        project_id=_id("project"),
        code=_id("F")[:24],
        display_name="Projet Claim candidat",
        actor="human:test",
        actor_kind="human",
        idempotency_key=_id("project-create"),
        attributes={"programme_summary": "Maison individuelle"},
    )


def _information(conn, project_id: str) -> str:
    information_id = _id("information")
    conn.execute(
        """
        INSERT INTO agency_information_cards (
            information_id, series_id, project_id, title, category,
            source_type, source_note, index_label, summary, details,
            status, limits, type_tags, subject_tags, author, acted_at
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            'acted', '[]'::jsonb, '[]'::jsonb, '[]'::jsonb, %s, clock_timestamp()
        )
        """,
        (
            information_id,
            _id("series"),
            project_id,
            "Synthèse de coût",
            "cost_synthesis",
            "native",
            "Fixture de test",
            "A01",
            "Budget de référence",
            "Synthèse agie utilisée comme base du candidat.",
            "human:test",
        ),
    )
    conn.commit()
    return information_id


def _candidate_payload(
    project_id: str,
    information_id: str,
    *,
    unit: str | None = "EUR",
) -> dict:
    return {
        "project_ref": project_id,
        "claim_type": "budget",
        "proposed_value": 375000,
        "unit": unit,
        "certainty": "E2",
        "observed_at": "2026-08-06T16:00:00+00:00",
        "effective_at": "2026-08-06T00:00:00+00:00",
        "basis_refs": [
            {
                "entity_type": "information",
                "entity_id": information_id,
                "observed_revision": 1,
                "observed_status": "acted",
            }
        ],
        "supersedes_claim_ref": None,
        "rationale": "Budget extracted from the acted cost synthesis.",
        "limitations": ["No market award has been checked."],
        "authority": {
            "creates_project_claim": False,
            "adopts_project_truth": False,
            "admits_evidence": False,
            "creates_decision": False,
            "creates_work_issue": False,
            "authorizes_effect": False,
        },
    }


def _store_candidate(
    conn,
    project_id: str,
    *,
    information_id: str | None = None,
    unit: str | None = "EUR",
) -> tuple[str, str, str]:
    basis_information_id = information_id or _information(conn, project_id)
    execution_id = _id("execution")
    result_id = _id("result")
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
            "produced_at": "2026-08-06T16:00:00+00:00",
            "authority": dict(execution_results.AUTHORITY),
            "results": [
                {
                    "result_id": result_id,
                    "result_kind": "project_claim_candidate",
                    "schema_ref": "schemas/project_claim_candidate.schema.yaml",
                    "payload": _candidate_payload(
                        project_id,
                        basis_information_id,
                        unit=unit,
                    ),
                }
            ],
            "clarification_requests": [],
        },
        idempotency_key=_id("execution-store"),
    )
    return execution_id, result_id, basis_information_id


def _accept(conn, result_id: str, *, reviewer_kind: str = "human") -> str:
    stored = execution_results.append_review_disposition(
        conn,
        result_ref=result_id,
        disposition="accepted_for_claim",
        reviewer="human:reviewer" if reviewer_kind == "human" else "system:test",
        reviewer_kind=reviewer_kind,
        note="Candidate reviewed for separate Claim creation.",
        idempotency_key=_id("claim-review"),
    )
    matching = [
        item
        for item in stored["review_dispositions"]
        if item["result_ref"] == result_id and item["disposition"] == "accepted_for_claim"
    ]
    return matching[-1]["disposition_id"]


def test_candidate_requires_latest_human_acceptance(conn) -> None:
    project = _project(conn)
    execution_id, result_id, information_id = _store_candidate(conn, project["project_id"])

    with pytest.raises(project_claim_candidates.ProjectClaimCandidateError, match="not been reviewed"):
        project_claim_candidates.create_claim_from_candidate(
            conn,
            execution_id=execution_id,
            result_id=result_id,
            actor="human:ifan",
            status="source_backed",
            backing_ref={"entity_type": "information", "entity_id": information_id},
        )

    with pytest.raises(execution_results.ExecutionResultError, match="human reviewer"):
        _accept(conn, result_id, reviewer_kind="system")

    with pytest.raises(project_claim_candidates.ProjectClaimCandidateError, match="not been reviewed"):
        project_claim_candidates.create_claim_from_candidate(
            conn,
            execution_id=execution_id,
            result_id=result_id,
            actor="human:ifan",
            status="asserted",
        )


def test_claim_acceptance_requires_project_claim_candidate_kind(conn) -> None:
    project = _project(conn)
    execution_id = _id("execution")
    result_id = _id("result")
    execution_results.store_execution_result(
        conn,
        execution_result={
            "execution_result_id": execution_id,
            "task_contract_ref": "task-contract.work-issue",
            "project_ref": project["project_id"],
            "producer": {
                "capability": "detect_work_issue",
                "implementation": "hermes.skill.work-issue",
                "version": "1.0.0",
            },
            "produced_at": "2026-08-06T16:00:00+00:00",
            "authority": dict(execution_results.AUTHORITY),
            "results": [
                {
                    "result_id": result_id,
                    "result_kind": "work_issue_candidate",
                    "schema_ref": "schemas/work_issue_candidate.schema.yaml",
                    "payload": {"project_ref": project["project_id"]},
                }
            ],
            "clarification_requests": [],
        },
        idempotency_key=_id("execution-store"),
    )

    with pytest.raises(execution_results.ExecutionResultError, match="project_claim_candidate"):
        execution_results.append_review_disposition(
            conn,
            result_ref=result_id,
            disposition="accepted_for_claim",
            reviewer="human:reviewer",
            reviewer_kind="human",
            note="Wrong candidate family.",
            idempotency_key=_id("claim-review"),
        )


def test_reviewed_candidate_creates_separate_append_only_claim(conn) -> None:
    project = _project(conn)
    execution_id, result_id, information_id = _store_candidate(conn, project["project_id"])
    disposition_id = _accept(conn, result_id)
    expected_basis = _candidate_payload(project["project_id"], information_id)["basis_refs"]

    claim = project_claim_candidates.create_claim_from_candidate(
        conn,
        execution_id=execution_id,
        result_id=result_id,
        actor="human:ifan",
        status="source_backed",
        certainty="E3",
        backing_ref={"entity_type": "information", "entity_id": information_id},
        note="Retained after professional review.",
    )

    assert claim["project_id"] == project["project_id"]
    assert claim["claim_type"] == "budget"
    assert claim["value"] == 375000
    assert claim["certainty"] == "E3"
    assert claim["effective_at"] == "2026-08-06T00:00:00+00:00"
    assert claim["provenance"]["candidate_ref"] == {
        "execution_id": execution_id,
        "result_id": result_id,
        "review_disposition_id": disposition_id,
    }
    assert claim["provenance"]["source_kind"] == "execution_result"
    assert claim["provenance"]["basis_refs"] == expected_basis

    source = execution_results.get_execution_result(conn, execution_id)
    assert source["results"][0]["payload"]["proposed_value"] == 375000
    assert source["authority"]["is_fact"] is False

    replay = project_claim_candidates.create_claim_from_candidate(
        conn,
        execution_id=execution_id,
        result_id=result_id,
        actor="human:ifan",
        status="source_backed",
        certainty="E3",
        backing_ref={"entity_type": "information", "entity_id": information_id},
    )
    assert replay["claim_id"] == claim["claim_id"]
    assert replay["provenance"]["basis_refs"] == expected_basis
    assert len(agency_claims.list_project_claims(conn, project["project_id"])) == 1

    projected = agency_data.get_project(conn, project["project_id"])["claim_refs"]["budget"]
    assert projected["certainty"] == "E3"
    assert projected["provenance"]["candidate_ref"]["result_id"] == result_id
    assert projected["provenance"]["basis_refs"] == expected_basis


def test_backing_ref_must_be_candidate_basis(conn) -> None:
    project = _project(conn)
    execution_id, result_id, _ = _store_candidate(conn, project["project_id"])
    other_information_id = _information(conn, project["project_id"])
    _accept(conn, result_id)

    with pytest.raises(project_claim_candidates.ProjectClaimCandidateError, match="basis_refs"):
        project_claim_candidates.create_claim_from_candidate(
            conn,
            execution_id=execution_id,
            result_id=result_id,
            actor="human:ifan",
            status="source_backed",
            backing_ref={
                "entity_type": "information",
                "entity_id": other_information_id,
            },
        )


def test_backing_ref_must_belong_to_candidate_project(conn) -> None:
    project = _project(conn)
    other_project = _project(conn)
    foreign_information_id = _information(conn, other_project["project_id"])
    execution_id, result_id, _ = _store_candidate(
        conn,
        project["project_id"],
        information_id=foreign_information_id,
    )
    _accept(conn, result_id)

    with pytest.raises(project_claim_candidates.ProjectClaimCandidateError, match="candidate Project"):
        project_claim_candidates.create_claim_from_candidate(
            conn,
            execution_id=execution_id,
            result_id=result_id,
            actor="human:ifan",
            status="source_backed",
            backing_ref={
                "entity_type": "information",
                "entity_id": foreign_information_id,
            },
        )


def test_candidate_unit_must_match_governed_claim_field(conn) -> None:
    project = _project(conn)
    execution_id, result_id, information_id = _store_candidate(
        conn,
        project["project_id"],
        unit="USD",
    )
    _accept(conn, result_id)

    with pytest.raises(project_claim_candidates.ProjectClaimCandidateError, match="governed unit"):
        project_claim_candidates.create_claim_from_candidate(
            conn,
            execution_id=execution_id,
            result_id=result_id,
            actor="human:ifan",
            status="source_backed",
            backing_ref={"entity_type": "information", "entity_id": information_id},
        )


def test_later_rejection_blocks_claim_creation(conn) -> None:
    project = _project(conn)
    execution_id, result_id, _ = _store_candidate(conn, project["project_id"])
    _accept(conn, result_id)
    execution_results.append_review_disposition(
        conn,
        result_ref=result_id,
        disposition="rejected",
        reviewer="human:reviewer",
        reviewer_kind="human",
        note="Superseding review rejected the candidate.",
        idempotency_key=_id("claim-rejection"),
    )

    with pytest.raises(project_claim_candidates.ProjectClaimCandidateError, match="not accepted_for_claim"):
        project_claim_candidates.create_claim_from_candidate(
            conn,
            execution_id=execution_id,
            result_id=result_id,
            actor="human:ifan",
            status="asserted",
        )
