from __future__ import annotations

import uuid

import psycopg
import pytest

from mvp_vertical import (
    agency_data,
    decision_requests,
    decision_signing,
    store,
    work_issue_scopes,
    work_issues,
)


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


@pytest.fixture
def conn():
    try:
        connection = store.connect()
    except Exception as exc:  # pragma: no cover - unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    for migration in (
        work_issues.MIGRATION,
        agency_data.MIGRATION,
        work_issue_scopes.MIGRATION,
        decision_requests.MIGRATION,
        decision_requests.HUMAN_RESPONSE_MIGRATION,
        decision_requests.EFFECT_BINDING_MIGRATION,
    ):
        connection.execute(migration.read_text(encoding="utf-8"))
    connection.execute(
        """
        TRUNCATE agency_decision_events, agency_human_responses,
                 agency_decision_records, agency_decision_options,
                 agency_decision_requests, work_issue_scope_events,
                 work_issue_scope_links, issue_events, hermes_runs,
                 issue_comments, work_card_metadata, work_issues,
                 agency_information_cards, agency_people,
                 agency_organizations, agency_projects
        RESTART IDENTITY CASCADE
        """
    )
    connection.commit()
    yield connection
    connection.close()


def _bound_request(conn) -> dict:
    return decision_requests.create_request(
        conn,
        request_id=_id("decision-request"),
        decision_type="approval",
        question="Autoriser exactement cet effet ?",
        priority="high",
        response_mode="decision_value",
        blocking=False,
        candidate_ref="agency_information:info-a",
        candidate_digest="a" * 64,
        approval_level="C2",
        decision_scope={"scope_type": "project", "scope_id": "project-a"},
        expires_at="2099-01-01T00:00:00+00:00",
        decision_surface="cockpit.decisions",
        decision_owner="architect-project-owner",
        created_by="human-reviewer",
        idempotency_key=_id("create-request"),
    )["decision_request"]


def test_effect_bounds_are_fixed_before_decision_and_copied_exactly(conn) -> None:
    request = _bound_request(conn)
    decision_id = _id("decision")
    signable = {
        "decision_id": decision_id,
        "decided_by": "human-reviewer",
        "approval_level": request["approval_level"],
        "scope": request["decision_scope"],
        "object_identity": request["candidate_ref"],
        "content_digest": request["candidate_digest"]["value"],
        "expires_at": request["expires_at"],
    }
    signature = decision_signing.sign_decision(signable, "test-secret")

    resolved = decision_requests.resolve_request(
        conn,
        request_id=request["request_id"],
        decision_id=decision_id,
        decision="approve",
        decided_by="human-reviewer",
        identity_assurance="authenticated",
        authenticated_principal={
            "user_id": "human-reviewer",
            "identity_provider": "https://idp.example.test",
        },
        signature=signature,
        expected_revision=request["revision"],
        idempotency_key=_id("resolve"),
    )

    record = resolved["decision_record"]
    assert record["approval_level"] == "C2"
    assert record["scope"] == {"scope_type": "project", "scope_id": "project-a"}
    assert record["object_identity"] == "agency_information:info-a"
    assert record["content_digest"] == "a" * 64
    assert record["expires_at"] == request["expires_at"]
    assert record["signature"] == signature
    assert resolved["resolution_is_not_authorization"] is True

    payload = decision_requests.policy_decision_payload(
        conn,
        decision_id,
        expectation={
            "required_ceiling": "C2",
            "required_scope": {"scope_type": "project", "scope_id": "project-a"},
            "object_identity": "agency_information:info-a",
            "expected_digest": "a" * 64,
        },
    )
    assert payload["decision"] == signable | {"signature": signature}


def test_declared_or_unbound_decision_cannot_be_projected_for_effect(conn) -> None:
    request = decision_requests.create_request(
        conn,
        request_id=_id("decision-request"),
        decision_type="approval",
        question="Valider le candidat ?",
        priority="normal",
        response_mode="decision_value",
        blocking=False,
        candidate_ref="candidate-a",
        candidate_digest="b" * 64,
        decision_surface="cockpit.decisions",
        decision_owner="architect-project-owner",
        created_by="human-reviewer",
        idempotency_key=_id("create-request"),
    )["decision_request"]
    decision_id = _id("decision")
    decision_requests.resolve_request(
        conn,
        request_id=request["request_id"],
        decision_id=decision_id,
        decision="approve",
        decided_by="human-reviewer",
        identity_assurance="declared",
        expected_revision=request["revision"],
        idempotency_key=_id("resolve"),
    )

    with pytest.raises(
        decision_requests.DecisionRequestError,
        match="authenticated Decision identity",
    ):
        decision_requests.policy_decision_payload(
            conn,
            decision_id,
            expectation={},
        )


def test_database_refuses_effect_bounds_different_from_request(conn) -> None:
    request = _bound_request(conn)

    with pytest.raises(psycopg.errors.RaiseException, match="exactly match"):
        conn.execute(
            """
            INSERT INTO agency_decision_records (
                decision_id, request_id, applies_to, decision, decided_by,
                identity_assurance, authenticated_principal, candidate_digest,
                approval_level, scope, object_identity, content_digest,
                expires_at, signature, decision_surface, consequences
            ) VALUES (
                %s, %s, %s, 'approve', 'human-reviewer', 'authenticated',
                %s::jsonb, %s, 'C2', %s::jsonb, %s, %s, %s, %s, %s, '{}'::jsonb
            )
            """,
            (
                _id("decision"),
                request["request_id"],
                request["request_id"],
                '{"user_id":"human-reviewer","identity_provider":"https://idp.example.test"}',
                request["candidate_digest"]["value"],
                '{"scope_type":"project","scope_id":"wrong-project"}',
                request["candidate_ref"],
                request["candidate_digest"]["value"],
                request["expires_at"],
                "invalid-signature",
                request["decision_surface"],
            ),
        )
    conn.rollback()


def test_question_cannot_be_effect_bound(conn) -> None:
    with pytest.raises(
        decision_requests.DecisionRequestError,
        match="question Decision Requests cannot carry effect-bound",
    ):
        decision_requests.create_request(
            conn,
            request_id=_id("decision-request"),
            decision_type="question",
            question="Quelle valeur ?",
            priority="normal",
            response_mode="free_text",
            blocking=False,
            candidate_ref="candidate-a",
            candidate_digest="c" * 64,
            approval_level="C2",
            decision_scope={"scope_type": "project", "scope_id": "project-a"},
            expires_at="2099-01-01T00:00:00+00:00",
            decision_surface="cockpit.decisions",
            decision_owner="architect-project-owner",
            created_by="human-reviewer",
            idempotency_key=_id("create-request"),
        )
