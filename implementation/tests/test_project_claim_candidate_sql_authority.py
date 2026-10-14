from __future__ import annotations

import hashlib
import uuid

import psycopg
import pytest
from psycopg.types.json import Jsonb

from mvp_vertical import agency_claims, agency_data, execution_results


def _id(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex}"


@pytest.fixture
def conn():
    try:
        db = agency_data.connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    execution_results.ensure_schema(db)
    db.execute(agency_claims.MIGRATION.read_text(encoding="utf-8"))
    db.execute(
        "TRUNCATE agency_project_claims, execution_result_review_dispositions, "
        "execution_clarification_requests, execution_result_items, execution_results, "
        "agency_change_candidate_events, agency_change_candidates, "
        "agency_project_events, agency_information_cards, agency_projects "
        "RESTART IDENTITY CASCADE"
    )
    db.commit()
    yield db
    db.close()


def _project(conn) -> str:
    project_id = _id("project")
    agency_data.create_project(
        conn,
        project_id=project_id,
        code=_id("F")[:24],
        display_name="SQL guard fixture",
        actor="human:test",
        actor_kind="human",
        idempotency_key=_id("project-create"),
        attributes={},
    )
    return project_id


def _information(conn, project_id: str) -> str:
    information_id = _id("information")
    conn.execute(
        """
        INSERT INTO agency_information_cards (
            information_id, series_id, project_id, title, category,
            source_type, source_note, index_label, summary, details,
            status, limits, type_tags, subject_tags, author, acted_at
        ) VALUES (
            %s, %s, %s, 'Cost synthesis', 'cost_synthesis',
            'native', 'SQL guard fixture', 'A01', 'Budget', 'Acted source.',
            'acted', '[]'::jsonb, '[]'::jsonb, '[]'::jsonb,
            'human:test', clock_timestamp()
        )
        """,
        (information_id, _id("series"), project_id),
    )
    conn.commit()
    return information_id


def _candidate(conn, *, kind: str = "project_claim_candidate"):
    project_id = _project(conn)
    information_id = _information(conn, project_id)
    execution_id = _id("execution")
    result_id = _id("result")
    payload = {
        "project_ref": project_id,
        "claim_type": "budget",
        "proposed_value": 375000,
        "unit": "EUR",
        "certainty": "E2",
        "observed_at": "2026-08-06T16:00:00+00:00",
        "effective_at": "2026-08-06T00:00:00+00:00",
        "basis_refs": [{
            "entity_type": "information",
            "entity_id": information_id,
            "observed_revision": 1,
            "observed_status": "acted",
        }],
        "rationale": "Budget extracted from an acted synthesis.",
        "limitations": ["Market award not checked."],
        "authority": {
            "creates_project_claim": False,
            "adopts_project_truth": False,
            "admits_evidence": False,
            "creates_decision": False,
            "creates_work_issue": False,
            "authorizes_effect": False,
        },
    }
    execution_results.store_execution_result(
        conn,
        execution_result={
            "execution_result_id": execution_id,
            "task_contract_ref": "task-contract.test",
            "project_ref": project_id,
            "producer": {
                "capability": "test",
                "implementation": "test",
                "version": "1.0.0",
            },
            "produced_at": "2026-08-06T16:00:00+00:00",
            "authority": dict(execution_results.AUTHORITY),
            "results": [{
                "result_id": result_id,
                "result_kind": kind,
                "schema_ref": "schemas/test.schema.yaml",
                "payload": payload,
            }],
            "clarification_requests": [],
        },
        idempotency_key=_id("execution-store"),
    )
    return project_id, information_id, execution_id, result_id, payload


def _insert_review(conn, result_id: str, reviewer_kind: str) -> None:
    key = _id("review")
    conn.execute(
        """
        INSERT INTO execution_result_review_dispositions (
            disposition_id, result_ref, disposition, reviewer, reviewer_kind,
            note, idempotency_key, payload_digest
        ) VALUES (%s, %s, 'accepted_for_claim', %s, %s, NULL, %s, %s)
        """,
        (
            _id("disposition"), result_id, "actor:test", reviewer_kind,
            key, hashlib.sha256(key.encode()).hexdigest(),
        ),
    )


def _accepted_disposition(conn, result_id: str) -> str:
    stored = execution_results.append_review_disposition(
        conn,
        result_ref=result_id,
        disposition="accepted_for_claim",
        reviewer="human:test",
        reviewer_kind="human",
        note=None,
        idempotency_key=_id("review"),
    )
    return stored["review_dispositions"][-1]["disposition_id"]


def _insert_claim(
    conn,
    candidate,
    disposition_id: str,
    *,
    value=375000,
    backing=None,
    basis_refs=None,
):
    project_id, information_id, execution_id, result_id, payload = candidate
    selected_basis = payload["basis_refs"] if basis_refs is None else basis_refs
    conn.execute(
        """
        INSERT INTO agency_project_claims (
            claim_id, project_id, claim_type, value, unit,
            backing_entity_type, backing_entity_id, backing_observed_status,
            source_kind, asserted_by, status, certainty, observed_at, effective_at,
            candidate_execution_id, candidate_result_id,
            candidate_review_disposition_id, basis_refs
        ) VALUES (
            %s, %s, %s, %s, %s,
            'information', %s, 'acted',
            'execution_result', 'human:test', 'source_backed', %s, %s, %s,
            %s, %s, %s, %s
        )
        """,
        (
            _id("claim"), project_id, payload["claim_type"], Jsonb(value), payload["unit"],
            backing or information_id, payload["certainty"], payload["observed_at"],
            payload["effective_at"], execution_id, result_id, disposition_id,
            Jsonb(selected_basis),
        ),
    )


def test_sql_guard_requires_human_claim_acceptance(conn) -> None:
    candidate = _candidate(conn)
    with pytest.raises(psycopg.errors.RaiseException, match="human reviewer"):
        with conn.transaction():
            _insert_review(conn, candidate[3], "system")


def test_sql_guard_requires_claim_candidate_kind(conn) -> None:
    candidate = _candidate(conn, kind="work_issue_candidate")
    with pytest.raises(psycopg.errors.RaiseException, match="project_claim_candidate"):
        with conn.transaction():
            _insert_review(conn, candidate[3], "human")


def test_sql_guard_preserves_reviewed_value_and_basis(conn) -> None:
    candidate = _candidate(conn)
    disposition_id = _accepted_disposition(conn, candidate[3])
    with pytest.raises(psycopg.errors.RaiseException, match="value must match"):
        with conn.transaction():
            _insert_claim(conn, candidate, disposition_id, value=999999)

    other_information = _information(conn, candidate[0])
    with pytest.raises(psycopg.errors.RaiseException, match="basis_refs"):
        with conn.transaction():
            _insert_claim(conn, candidate, disposition_id, backing=other_information)

    substituted_basis = [dict(candidate[4]["basis_refs"][0], observed_revision=99)]
    with pytest.raises(psycopg.errors.RaiseException, match="exactly match"):
        with conn.transaction():
            _insert_claim(
                conn,
                candidate,
                disposition_id,
                basis_refs=substituted_basis,
            )


def test_sql_guard_accepts_exact_reviewed_candidate(conn) -> None:
    candidate = _candidate(conn)
    disposition_id = _accepted_disposition(conn, candidate[3])
    with conn.transaction():
        _insert_claim(conn, candidate, disposition_id)
    stored = conn.execute(
        "SELECT value, candidate_result_id, basis_refs FROM agency_project_claims "
        "WHERE candidate_result_id = %s",
        (candidate[3],),
    ).fetchone()
    assert stored == (375000, candidate[3], candidate[4]["basis_refs"])
