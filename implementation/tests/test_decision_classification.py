from __future__ import annotations

import uuid

import pytest

from mvp_vertical import (
    agency_data,
    decision_request_views,
    decision_requests,
    store,
    work_issue_scopes,
    work_issues,
)


@pytest.fixture
def conn():
    try:
        connection = store.connect()
    except Exception as exc:  # pragma: no cover - unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    try:
        for migration in (
            work_issues.MIGRATION,
            agency_data.MIGRATION,
            work_issue_scopes.MIGRATION,
            decision_requests.MIGRATION,
            decision_requests.HUMAN_RESPONSE_MIGRATION,
            decision_requests.EFFECT_BINDING_MIGRATION,
        ):
            connection.execute(migration.read_text(encoding="utf-8"))
        connection.commit()
        with connection.transaction(force_rollback=True):
            yield connection
    finally:
        connection.close()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _request_kwargs(
    *,
    request_id: str,
    project_ref: str | None,
    decision_type: str = "question",
) -> dict:
    return {
        "request_id": request_id,
        "decision_type": decision_type,
        "question": "Cette demande doit-elle être classée ?",
        "priority": "normal",
        "response_mode": "free_text" if decision_type == "question" else "decision_value",
        "blocking": False,
        "candidate_ref": _id("candidate"),
        "candidate_digest": "a" * 64,
        "decision_surface": "cockpit.decisions",
        "decision_owner": "architect",
        "created_by": "architect",
        "idempotency_key": _id("create-request"),
        "project_ref": project_ref,
        "work_issue_ref": None,
    }


def _project(conn, project_id: str) -> None:
    conn.execute(
        """
        INSERT INTO agency_projects (
            project_id, code, display_name, created_by, updated_by
        ) VALUES (%s, %s, %s, 'architect', 'architect')
        """,
        (project_id, _id("code"), "Projet classé"),
    )


def test_global_inbox_excludes_project_classified_requests(conn) -> None:
    project_id = _id("project")
    _project(conn, project_id)
    unclassified_id = _id("request-unclassified")
    classified_id = _id("request-classified")

    decision_requests.create_request(
        conn,
        **_request_kwargs(request_id=unclassified_id, project_ref=None),
    )
    decision_requests.create_request(
        conn,
        **_request_kwargs(request_id=classified_id, project_ref=project_id),
    )

    inbox = decision_request_views.list_unclassified_requests(
        conn,
        status="pending",
        limit=100,
    )
    assert [item["decision_request"]["request_id"] for item in inbox] == [
        unclassified_id
    ]
    project_view = decision_requests.list_requests(
        conn,
        status="pending",
        project_ref=project_id,
    )
    assert [item["decision_request"]["request_id"] for item in project_view] == [
        classified_id
    ]


def test_decision_scope_resolves_a_decision_record_not_agency_decision(conn) -> None:
    project_id = _id("project")
    _project(conn, project_id)
    request_id = _id("request")
    decision_id = _id("decision")
    issue_id = _id("issue")

    request = decision_requests.create_request(
        conn,
        **_request_kwargs(
            request_id=request_id,
            project_ref=project_id,
            decision_type="validation",
        ),
    )["decision_request"]
    decision_requests.resolve_request(
        conn,
        request_id=request_id,
        decision_id=decision_id,
        decision="approve",
        decided_by="architect",
        identity_assurance="declared",
        expected_revision=request["revision"],
        idempotency_key=_id("resolve"),
    )

    scoped = work_issue_scopes.create_scoped_issue(
        conn,
        issue_id=issue_id,
        case_ref=project_id,
        title="Appliquer la décision",
        description="La tâche référence une détermination humaine enregistrée.",
        created_by="architect",
        idempotency_key=_id("create-issue"),
        scopes=[
            {
                "scope_link_id": _id("scope-project"),
                "entity_type": "project",
                "entity_id": project_id,
                "scope_role": "primary",
            }
        ],
    )
    version = scoped["work_issue"]["version"]
    linked = work_issue_scopes.add_scope(
        conn,
        issue_id=issue_id,
        scope_link_id=_id("scope-decision"),
        entity_type="decision",
        entity_id=decision_id,
        scope_role="related",
        actor="architect",
        expected_version=version,
        idempotency_key=_id("link-decision"),
    )
    decision_scopes = [
        link
        for link in linked["scope_links"]
        if link["scope_ref"]["entity_type"] == "decision"
    ]
    assert decision_scopes[0]["scope_ref"]["entity_id"] == decision_id
