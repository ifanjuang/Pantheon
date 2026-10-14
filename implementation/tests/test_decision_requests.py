"""PostgreSQL acceptance tests for typed Decision Request resolutions."""

from __future__ import annotations

import uuid

import psycopg
import pytest

from mvp_vertical import (
    agency_data,
    decision_requests,
    store,
    work_issue_scopes,
    work_issues,
)


@pytest.fixture
def conn():
    try:
        connection = store.connect()
    except Exception as exc:  # pragma: no cover - local unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    for migration in (
        work_issues.MIGRATION,
        agency_data.MIGRATION,
        work_issue_scopes.MIGRATION,
        decision_requests.MIGRATION,
        decision_requests.HUMAN_RESPONSE_MIGRATION,
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


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _project(conn, project_id: str = "project-alpha") -> str:
    conn.execute(
        """
        INSERT INTO agency_projects (
            project_id, code, display_name, created_by, updated_by
        ) VALUES (%s, %s, %s, 'human', 'human')
        """,
        (project_id, project_id.upper(), "Projet Alpha"),
    )
    conn.commit()
    return project_id


def _scoped_issue(conn, project_id: str, issue_id: str = "issue-envelope") -> dict:
    return work_issue_scopes.create_scoped_issue(
        conn,
        issue_id=issue_id,
        case_ref=project_id,
        title="Finaliser la synthèse enveloppe",
        description="La variante de couverture doit être arbitrée.",
        created_by="human-reviewer",
        idempotency_key=_id("create-issue"),
        scopes=[
            {
                "scope_link_id": f"scope-{issue_id}-{project_id}",
                "entity_type": "project",
                "entity_id": project_id,
                "scope_role": "primary",
            }
        ],
    )


def _request_kwargs(
    *,
    request_id: str | None = None,
    project_ref: str | None = "project-alpha",
    work_issue_ref: str | None = "issue-envelope",
    blocking: bool = True,
) -> dict:
    return {
        "request_id": request_id or _id("decision-request"),
        "decision_type": "arbitration",
        "question": "Quelle variante de couverture doit être retenue ?",
        "priority": "high",
        "response_mode": "single_option",
        "blocking": blocking,
        "candidate_ref": "result-envelope-001",
        "candidate_digest": "a" * 64,
        "decision_surface": "cockpit.decisions",
        "decision_owner": "architect-project-owner",
        "created_by": "human-reviewer",
        "idempotency_key": _id("create-request"),
        "project_ref": project_ref,
        "work_issue_ref": work_issue_ref,
        "options": [
            {
                "option_id": "option-zinc",
                "label": "Zinc",
                "consequence": "Poursuivre la synthèse avec le zinc.",
                "limitations": ["Prix non confirmé"],
            },
            {
                "option_id": "option-ardoise",
                "label": "Ardoise",
                "consequence": "Poursuivre la synthèse avec l’ardoise.",
                "limitations": [],
            },
        ],
        "recommendation_candidate": "option-zinc",
        "source_refs": ["information-envelope-a01"],
        "evidence_gaps": ["Prix final"],
        "blocked_action": "Finaliser la synthèse.",
        "next_safe_action": "Enregistrer la détermination humaine.",
    }


def _question_kwargs(*, request_id: str | None = None, blocking: bool = False) -> dict:
    values = _request_kwargs(
        request_id=request_id,
        work_issue_ref="issue-envelope" if blocking else None,
        blocking=blocking,
    )
    values.update(
        decision_type="question",
        question="Quelle finition existante doit être conservée ?",
        response_mode="free_text",
        options=[],
        recommendation_candidate=None,
    )
    return values


def test_pending_request_is_attention_not_a_resolution(conn) -> None:
    project_id = _project(conn)
    _scoped_issue(conn, project_id)
    projection = decision_requests.create_request(conn, **_request_kwargs())

    request = projection["decision_request"]
    assert request["status"] == "pending"
    assert request["blocking"] is True
    assert request["resolved_decision_ref"] is None
    assert request["resolved_response_ref"] is None
    assert projection["human_response"] is None
    assert projection["decision_record"] is None
    assert projection["attention_required"] is True
    assert projection["request_is_not_decision"] is True
    assert projection["human_response_is_not_decision"] is True
    assert projection["resolution_is_not_authorization"] is True
    assert projection["decision_is_not_execution"] is True


def test_global_and_project_views_preserve_one_request_identity(conn) -> None:
    project_id = _project(conn)
    _scoped_issue(conn, project_id)
    request_id = "decision-request-shared"
    decision_requests.create_request(conn, **_request_kwargs(request_id=request_id))

    global_view = decision_requests.list_requests(conn, status="pending")
    project_view = decision_requests.list_requests(
        conn,
        status="pending",
        project_ref=project_id,
    )
    assert [item["decision_request"]["request_id"] for item in global_view] == [request_id]
    assert [item["decision_request"]["request_id"] for item in project_view] == [request_id]


def test_only_one_pending_blocking_request_targets_a_work_issue(conn) -> None:
    project_id = _project(conn)
    _scoped_issue(conn, project_id)
    decision_requests.create_request(conn, **_request_kwargs(request_id="request-one"))

    with pytest.raises(decision_requests.DecisionRequestConflict):
        decision_requests.create_request(conn, **_request_kwargs(request_id="request-two"))

    preference = decision_requests.create_request(
        conn,
        **_request_kwargs(request_id="request-preference", blocking=False),
    )
    assert preference["decision_request"]["blocking"] is False


def test_project_and_work_issue_links_must_share_an_explicit_scope(conn) -> None:
    first = _project(conn, "project-alpha")
    _project(conn, "project-beta")
    _scoped_issue(conn, first)

    with pytest.raises(decision_requests.DecisionRequestError, match="not scoped"):
        decision_requests.create_request(
            conn,
            **_request_kwargs(project_ref="project-beta"),
        )


def test_arbitration_resolution_creates_decision_without_changing_work_issue(conn) -> None:
    project_id = _project(conn)
    issue_projection = _scoped_issue(conn, project_id)
    request = decision_requests.create_request(conn, **_request_kwargs())["decision_request"]
    issue_before = work_issues.get_issue(conn, "issue-envelope")["work_issue"]

    resolved = decision_requests.resolve_request(
        conn,
        request_id=request["request_id"],
        decision_id="decision-envelope-zinc",
        decision="approve",
        decided_by="architect-human",
        identity_assurance="declared",
        expected_revision=request["revision"],
        idempotency_key=_id("resolve"),
        selected_option_ids=["option-zinc"],
        rationale="Le zinc est retenu pour poursuivre les études.",
    )

    resolved_request = resolved["decision_request"]
    assert resolved_request["status"] == "resolved"
    assert resolved_request["resolved_decision_ref"] == "decision-envelope-zinc"
    assert resolved_request["resolved_response_ref"] is None
    assert resolved["human_response"] is None
    assert resolved["attention_required"] is False
    record = resolved["decision_record"]
    assert record["object_type"] == "decision_record"
    assert record["decision_id"] == "decision-envelope-zinc"
    assert record["applies_to"] == request["request_id"]
    assert record["candidate_digest"] == request["candidate_digest"]
    assert record["consequences"]["selected_option_ids"] == ["option-zinc"]
    assert record["consequences"]["work_issue_transitioned"] is False
    assert record["consequences"]["runtime_continuation_authorized"] is False
    assert record["consequences"]["action_executed"] is False
    assert record["consequences"]["result_validated"] is False

    issue_after = work_issues.get_issue(conn, "issue-envelope")["work_issue"]
    assert issue_after["status"] == issue_before["status"]
    assert issue_after["version"] == issue_before["version"]
    assert issue_projection["work_issue"]["issue_id"] == issue_after["issue_id"]


def test_free_text_question_creates_human_response_not_decision(conn) -> None:
    _project(conn)
    request = decision_requests.create_request(conn, **_question_kwargs())["decision_request"]

    resolved = decision_requests.resolve_request(
        conn,
        request_id=request["request_id"],
        response_id="human-response-finish",
        decided_by="architect-human",
        identity_assurance="declared",
        expected_revision=request["revision"],
        idempotency_key=_id("respond"),
        response_text="Conserver l’enduit existant côté jardin.",
    )

    resolved_request = resolved["decision_request"]
    assert resolved_request["status"] == "resolved"
    assert resolved_request["resolved_response_ref"] == "human-response-finish"
    assert resolved_request["resolved_decision_ref"] is None
    assert resolved["decision_record"] is None
    response = resolved["human_response"]
    assert response["response_id"] == "human-response-finish"
    assert response["request_id"] == request["request_id"]
    assert response["responded_by"] == "architect-human"
    assert response["response_text"] == "Conserver l’enduit existant côté jardin."
    assert response["candidate_digest"] == request["candidate_digest"]
    assert resolved["resolution_is_not_authorization"] is True
    assert resolved["events"][-1]["response_ref"] == "human-response-finish"
    assert resolved["events"][-1]["decision_ref"] is None

    fetched = decision_requests.get_response(conn, "human-response-finish")
    assert fetched["human_response"] == response
    assert fetched["response_is_not_authorization"] is True
    assert fetched["response_is_not_evidence"] is True


def test_option_question_creates_human_response_without_authority(conn) -> None:
    _project(conn)
    values = _request_kwargs(blocking=False, work_issue_ref=None)
    values["decision_type"] = "question"
    values["question"] = "Quel matériau est actuellement posé ?"
    request = decision_requests.create_request(conn, **values)["decision_request"]

    resolved = decision_requests.resolve_request(
        conn,
        request_id=request["request_id"],
        response_id="human-response-material",
        decided_by="architect-human",
        identity_assurance="declared",
        expected_revision=1,
        idempotency_key=_id("respond"),
        selected_option_ids=["option-zinc"],
    )

    assert resolved["human_response"]["selected_option_ids"] == ["option-zinc"]
    assert resolved["human_response"]["response_text"] is None
    assert resolved["decision_record"] is None
    assert resolved["resolution_is_not_authorization"] is True


def test_question_cannot_be_resolved_as_decision(conn) -> None:
    _project(conn)
    request = decision_requests.create_request(conn, **_question_kwargs())["decision_request"]

    with pytest.raises(decision_requests.DecisionRequestError, match="cannot carry Decision"):
        decision_requests.resolve_request(
            conn,
            request_id=request["request_id"],
            response_id="human-response-wrong",
            decision_id="decision-wrong",
            decision="approve",
            decided_by="architect-human",
            identity_assurance="declared",
            expected_revision=1,
            idempotency_key=_id("wrong"),
            response_text="Information seulement.",
        )


def test_decision_request_cannot_be_resolved_as_human_response(conn) -> None:
    project_id = _project(conn)
    _scoped_issue(conn, project_id)
    request = decision_requests.create_request(conn, **_request_kwargs())["decision_request"]

    with pytest.raises(decision_requests.DecisionRequestError, match="cannot carry response_id"):
        decision_requests.resolve_request(
            conn,
            request_id=request["request_id"],
            response_id="human-response-wrong",
            decision_id="decision-right",
            decision="approve",
            decided_by="architect-human",
            identity_assurance="declared",
            expected_revision=1,
            idempotency_key=_id("wrong"),
            selected_option_ids=["option-zinc"],
        )


def test_question_decision_value_mode_is_refused_for_new_requests(conn) -> None:
    _project(conn)
    values = _question_kwargs()
    values["response_mode"] = "decision_value"
    with pytest.raises(decision_requests.DecisionRequestError, match="cannot use decision_value"):
        decision_requests.create_request(conn, **values)


def test_decision_resolution_replay_is_idempotent(conn) -> None:
    project_id = _project(conn)
    _scoped_issue(conn, project_id)
    request = decision_requests.create_request(conn, **_request_kwargs())["decision_request"]
    key = _id("resolve")
    first = decision_requests.resolve_request(
        conn,
        request_id=request["request_id"],
        decision_id="decision-one",
        decision="approve",
        decided_by="architect-human",
        identity_assurance="declared",
        expected_revision=1,
        idempotency_key=key,
        selected_option_ids=["option-zinc"],
    )
    replay = decision_requests.resolve_request(
        conn,
        request_id=request["request_id"],
        decision_id="decision-one",
        decision="approve",
        decided_by="architect-human",
        identity_assurance="declared",
        expected_revision=1,
        idempotency_key=key,
        selected_option_ids=["option-zinc"],
    )
    assert replay["decision_record"]["decision_id"] == first["decision_record"]["decision_id"]
    assert len(replay["events"]) == len(first["events"])


def test_human_response_replay_is_idempotent(conn) -> None:
    _project(conn)
    request = decision_requests.create_request(conn, **_question_kwargs())["decision_request"]
    key = _id("respond")
    kwargs = dict(
        request_id=request["request_id"],
        response_id="human-response-one",
        decided_by="architect-human",
        identity_assurance="declared",
        expected_revision=1,
        idempotency_key=key,
        response_text="Conserver l’existant.",
    )
    first = decision_requests.resolve_request(conn, **kwargs)
    replay = decision_requests.resolve_request(conn, **kwargs)
    assert replay["human_response"]["response_id"] == first["human_response"]["response_id"]
    assert len(replay["events"]) == len(first["events"])


def test_response_mode_and_revision_are_enforced(conn) -> None:
    project_id = _project(conn)
    _scoped_issue(conn, project_id)
    request = decision_requests.create_request(conn, **_request_kwargs())["decision_request"]

    with pytest.raises(decision_requests.DecisionRequestError, match="exactly one option"):
        decision_requests.resolve_request(
            conn,
            request_id=request["request_id"],
            decision_id="decision-invalid",
            decision="approve",
            decided_by="architect-human",
            identity_assurance="declared",
            expected_revision=1,
            idempotency_key=_id("resolve-invalid"),
            selected_option_ids=[],
        )

    with pytest.raises(decision_requests.StaleDecisionRequest):
        decision_requests.resolve_request(
            conn,
            request_id=request["request_id"],
            decision_id="decision-stale",
            decision="approve",
            decided_by="architect-human",
            identity_assurance="declared",
            expected_revision=2,
            idempotency_key=_id("resolve-stale"),
            selected_option_ids=["option-zinc"],
        )


def test_cancellation_removes_attention_without_recording_resolution(conn) -> None:
    project_id = _project(conn)
    _scoped_issue(conn, project_id)
    request = decision_requests.create_request(conn, **_request_kwargs())["decision_request"]
    cancelled = decision_requests.cancel_request(
        conn,
        request_id=request["request_id"],
        cancelled_by="architect-human",
        expected_revision=request["revision"],
        idempotency_key=_id("cancel"),
        rationale="La question est devenue sans objet.",
    )
    assert cancelled["decision_request"]["status"] == "cancelled"
    assert cancelled["human_response"] is None
    assert cancelled["decision_record"] is None
    assert cancelled["attention_required"] is False


def test_decision_material_and_events_are_immutable(conn) -> None:
    project_id = _project(conn)
    _scoped_issue(conn, project_id)
    request = decision_requests.create_request(conn, **_request_kwargs())["decision_request"]
    resolved = decision_requests.resolve_request(
        conn,
        request_id=request["request_id"],
        decision_id="decision-immutable",
        decision="approve",
        decided_by="architect-human",
        identity_assurance="declared",
        expected_revision=1,
        idempotency_key=_id("resolve"),
        selected_option_ids=["option-zinc"],
    )

    with pytest.raises(psycopg.errors.RaiseException, match="immutable"):
        conn.execute(
            "UPDATE agency_decision_records SET rationale = 'rewritten' "
            "WHERE decision_id = 'decision-immutable'"
        )
    conn.rollback()
    event_id = resolved["events"][-1]["event_id"]
    with pytest.raises(psycopg.errors.RaiseException, match="immutable"):
        conn.execute("DELETE FROM agency_decision_events WHERE event_id = %s", (event_id,))
    conn.rollback()


def test_human_response_is_immutable(conn) -> None:
    _project(conn)
    request = decision_requests.create_request(conn, **_question_kwargs())["decision_request"]
    decision_requests.resolve_request(
        conn,
        request_id=request["request_id"],
        response_id="human-response-immutable",
        decided_by="architect-human",
        identity_assurance="declared",
        expected_revision=1,
        idempotency_key=_id("respond"),
        response_text="Conserver l’existant.",
    )

    with pytest.raises(psycopg.errors.RaiseException, match="immutable"):
        conn.execute(
            "UPDATE agency_human_responses SET response_text = 'rewritten' "
            "WHERE response_id = 'human-response-immutable'"
        )
    conn.rollback()


def test_database_rejects_decision_record_for_question(conn) -> None:
    _project(conn)
    request = decision_requests.create_request(conn, **_question_kwargs())["decision_request"]

    with pytest.raises(psycopg.errors.RaiseException, match="resolve to HumanResponse"):
        conn.execute(
            """
            INSERT INTO agency_decision_records (
                decision_id, request_id, applies_to, decision, decided_by,
                identity_assurance, candidate_digest, decision_surface
            ) VALUES (%s, %s, %s, 'approve', 'architect-human', 'declared', %s, %s)
            """,
            (
                "decision-illegal",
                request["request_id"],
                request["request_id"],
                request["candidate_digest"]["value"],
                request["decision_surface"],
            ),
        )
    conn.rollback()
