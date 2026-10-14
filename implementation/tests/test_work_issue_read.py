"""Read-only Work Issue cockpit projection tests."""

from __future__ import annotations

import json
import uuid

import pytest

from mvp_vertical import work_issue_read, work_issues


@pytest.fixture
def conn():
    try:
        connection = work_issues.connect()
    except Exception as exc:  # pragma: no cover - local unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(
        "TRUNCATE issue_events, hermes_runs, issue_comments, work_issues RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _create(conn, *, case_ref: str, title: str) -> dict:
    return work_issues.create_issue(
        conn,
        issue_id=_id("issue"),
        case_ref=case_ref,
        title=title,
        description="Review one bounded project matter without broadening its declared case.",
        created_by="human-reviewer",
        idempotency_key=_id("create"),
    )


def test_list_issue_projections_matches_exact_case_and_prioritizes_waiting(conn) -> None:
    open_projection = _create(
        conn,
        case_ref="project-maison-a",
        title="Review the current project document",
    )
    waiting_projection = _create(
        conn,
        case_ref="project-maison-a",
        title="Clarify one missing project source",
    )
    _create(
        conn,
        case_ref="project-other",
        title="Unrelated project matter",
    )

    waiting_issue = waiting_projection["work_issue"]
    work_issues.transition_issue(
        conn,
        issue_id=waiting_issue["issue_id"],
        to_status="waiting",
        actor="human-reviewer",
        actor_kind="human",
        expected_version=waiting_issue["version"],
        idempotency_key=_id("wait"),
    )

    listed = work_issue_read.list_issue_projections(conn, "project-maison-a")

    assert [item["work_issue"]["status"] for item in listed] == ["waiting", "open"]
    assert {item["work_issue"]["case_ref"] for item in listed} == {"project-maison-a"}
    assert open_projection["work_issue"]["issue_id"] in {
        item["work_issue"]["issue_id"] for item in listed
    }


def test_batched_list_preserves_governed_aggregate_and_card_metadata(conn) -> None:
    created = _create(
        conn,
        case_ref="project-batched-parity",
        title="Verify batched projection parity",
    )
    issue = created["work_issue"]
    commented = work_issues.add_comment(
        conn,
        issue_id=issue["issue_id"],
        comment_id=_id("comment"),
        body="Keep the same bounded aggregate.",
        author="human-reviewer",
        expected_version=issue["version"],
        idempotency_key=_id("comment-event"),
    )
    work_issues.transition_issue(
        conn,
        issue_id=issue["issue_id"],
        to_status="waiting",
        actor="human-reviewer",
        actor_kind="human",
        expected_version=commented["work_issue"]["version"],
        idempotency_key=_id("wait"),
    )
    conn.execute(
        """
        INSERT INTO work_card_metadata (
            issue_id, workflow, information_ref, result_ref, decision_request
        ) VALUES (%s, %s::jsonb, %s, %s, %s::jsonb)
        """,
        (
            issue["issue_id"],
            json.dumps({
                "objective": "Verify parity",
                "type_tags": ["verification"],
                "subject_tags": ["chantier", "responsabilité"],
                "limits": ["read_only"],
            }),
            "information:info-1",
            "result:pending",
            json.dumps({"title": "Human review", "options": ["accept", "correct"]}),
        ),
    )
    conn.commit()

    expected = work_issues.get_issue(conn, issue["issue_id"])
    listed = work_issue_read.list_issue_projections(conn, "project-batched-parity")

    assert len(listed) == 1
    actual = listed[0]
    assert actual["comments"] == expected["comments"]
    assert actual["hermes_runs"] == expected["hermes_runs"]
    assert actual["events"] == expected["events"]
    assert actual["governance_refs"] == expected["governance_refs"]
    for key, value in expected["work_issue"].items():
        assert actual["work_issue"][key] == value
    assert actual["work_issue"]["objective"] == "Verify parity"
    assert actual["work_issue"]["type_tags"] == ["verification"]
    assert actual["work_issue"]["subject_tags"] == ["chantier", "responsabilité"]
    assert actual["work_issue"]["information_ref"] == "information:info-1"
    assert actual["work_issue"]["decision_options"] == ["accept", "correct"]
    assert actual["work_activity"]["schema"] == {
        "id": "cockpit.work_activity",
        "revision": 1,
    }


def test_list_issue_projections_exposes_bounded_hermes_cognitive_return(conn) -> None:
    created = _create(
        conn,
        case_ref="project-athena-live",
        title="Qualify one synthetic situated-reasoning run",
    )
    issue = created["work_issue"]
    normalized_return = {
        "outcome": "result_candidate",
        "summary": (
            "Source-backed: the admitted partition is 120 mm thick. "
            "Interpretation: moving it may affect circulation and hosted elements. "
            "Uncertainty: no global project traversal was performed."
        ),
        "result_refs": [],
        "evidence_candidate_refs": [],
        "trace_refs": ["hermes://runs/run-athena-live"],
    }
    conn.execute(
        """
        INSERT INTO hermes_runs (
            run_id, issue_id, task_contract_ref, context_pack_ref,
            status, requested_effect, returned_at, normalized_return
        ) VALUES (
            %s, %s, %s, %s, 'returned', 'read_only',
            CURRENT_TIMESTAMP, %s::jsonb
        )
        """,
        (
            "run-athena-live",
            issue["issue_id"],
            "task-contract:athena-live",
            "context-pack:athena-live",
            json.dumps(normalized_return),
        ),
    )
    conn.commit()

    listed = work_issue_read.list_issue_projections(conn, "project-athena-live")

    assert len(listed) == 1
    run = listed[0]["hermes_runs"][0]
    assert run["run_id"] == "run-athena-live"
    assert run["status"] == "returned"
    assert run["normalized_return"] == normalized_return
    assert run["normalized_return"]["summary"].startswith("Source-backed:")
    assert listed[0]["work_issue"]["case_ref"] == "project-athena-live"


def test_list_issue_projections_refuses_unbounded_limit(conn) -> None:
    with pytest.raises(work_issues.WorkIssueError, match="limit"):
        work_issue_read.list_issue_projections(conn, "project-maison-a", limit=501)
