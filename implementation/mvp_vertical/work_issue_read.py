"""Read-only Work Issue projections for the cards-first cockpit.

The adapter reads governed Work Issue aggregates plus optional Work Card
presentation metadata. It creates no card record, changes no issue status and
grants no Hermes authority.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from functools import lru_cache
from typing import Any

import jsonschema
import psycopg
import yaml
from psycopg.rows import dict_row

from . import work_issues
from .work_activity_projection import project_work_activity


MAX_SUBJECT_TAGS = 5
_STATUS_ORDER = {
    "review": 0,
    "waiting": 1,
    "open": 2,
    "in_progress": 3,
    "done": 4,
    "cancelled": 5,
}
_GOVERNANCE_REFS = [
    "docs/governance/WORK_ISSUE_AND_DELEGATED_MERGE_MODEL.md",
    "docs/governance/TASK_CONTRACTS.md",
    "docs/governance/CONTEXT_PACKS.md",
    "docs/governance/APPROVALS.md",
]


def _string_list(value: Any, *, limit: int | None = None) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
        if limit is not None and len(result) >= limit:
            break
    return result


def _empty_metadata() -> dict[str, Any]:
    return {
        "workflow": {},
        "information_ref": None,
        "result_ref": None,
        "decision_request": {},
    }


def _metadata(conn: psycopg.Connection, issue_id: str) -> dict:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT workflow, information_ref, result_ref, decision_request "
            "FROM work_card_metadata WHERE issue_id = %s",
            (issue_id,),
        )
        row = cur.fetchone()
    return dict(row) if row is not None else _empty_metadata()


def _metadata_by_issue(
    conn: psycopg.Connection,
    issue_ids: list[str],
) -> dict[str, dict[str, Any]]:
    output = {issue_id: _empty_metadata() for issue_id in issue_ids}
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT issue_id, workflow, information_ref, result_ref, decision_request
              FROM work_card_metadata
             WHERE issue_id = ANY(%s)
            """,
            (issue_ids,),
        )
        for row in cur.fetchall():
            item = dict(row)
            output[item.pop("issue_id")] = item
    return output


def _card_projection(issue: dict, metadata: dict) -> dict:
    """Expose explicit presentation metadata without changing Work Issue semantics."""
    projected = dict(issue)
    workflow = metadata.get("workflow") if isinstance(metadata.get("workflow"), dict) else {}
    decision = (
        metadata.get("decision_request")
        if isinstance(metadata.get("decision_request"), dict)
        else {}
    )

    projected["objective"] = workflow.get("objective") or issue.get("description")
    projected["milestones"] = workflow.get("milestones") or []
    projected["responsibilities"] = workflow.get("responsibilities") or []
    projected["skills"] = workflow.get("skills") or []
    projected["functions"] = workflow.get("functions") or []
    projected["tools"] = workflow.get("tools") or []
    projected["type_tags"] = _string_list(
        workflow.get("type_tags") or [issue.get("issue_type")]
    )
    projected["subject_tags"] = _string_list(
        workflow.get("subject_tags"), limit=MAX_SUBJECT_TAGS
    )
    # Temporary compatibility for the current Cockpit card normalizer. This is a
    # projection alias only; the governed Work Issue schema does not acquire tags.
    projected["tags"] = list(projected["subject_tags"])
    projected["limits"] = _string_list(workflow.get("limits"))
    projected["information_ref"] = metadata.get("information_ref")
    projected["result_ref"] = metadata.get("result_ref")
    projected["decision_title"] = decision.get("title")
    projected["decision_question"] = decision.get("question")
    projected["result_summary"] = decision.get("result_summary")
    projected["decision_options"] = decision.get("options") or []
    return projected


def _clean(mapping: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in mapping.items():
        if value is None:
            continue
        output[key] = value.isoformat() if isinstance(value, datetime) else value
    return output


@lru_cache(maxsize=1)
def _projection_validator() -> jsonschema.Draft202012Validator:
    schema = yaml.safe_load(work_issues.SCHEMA.read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )


def _validated_aggregate(
    issue: dict[str, Any],
    *,
    comments: list[dict[str, Any]],
    runs: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    projection = {
        "work_issue": issue,
        "comments": comments,
        "hermes_runs": runs,
        "events": events,
        "governance_refs": list(_GOVERNANCE_REFS),
    }
    try:
        _projection_validator().validate(projection)
    except (OSError, jsonschema.ValidationError) as exc:
        raise work_issues.WorkIssueError(
            f"stored Work Issue projection violates its governed contract: {exc}"
        ) from exc
    return projection


def _batched_aggregates(
    conn: psycopg.Connection,
    case_ref: str,
    *,
    include_terminal: bool,
    limit: int,
) -> list[dict[str, Any]]:
    terminal_filter = "" if include_terminal else "AND status NOT IN ('done', 'cancelled')"
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"""
            SELECT *
              FROM work_issues
             WHERE case_ref = %s
               {terminal_filter}
             ORDER BY updated_at DESC, issue_id ASC
             LIMIT %s
            """,
            (case_ref, limit),
        )
        issues = [_clean(dict(row)) for row in cur.fetchall()]

    if not issues:
        return []

    issue_ids = [issue["issue_id"] for issue in issues]
    comments: dict[str, list[dict[str, Any]]] = defaultdict(list)
    runs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    events: dict[str, list[dict[str, Any]]] = defaultdict(list)

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT comment_id, issue_id AS issue_ref, body, author, created_at
              FROM issue_comments
             WHERE issue_id = ANY(%s)
             ORDER BY issue_id, created_at, comment_id
            """,
            (issue_ids,),
        )
        for row in cur.fetchall():
            item = _clean(dict(row))
            comments[item["issue_ref"]].append(item)

        cur.execute(
            """
            SELECT run_id, issue_id AS issue_ref, task_contract_ref, context_pack_ref,
                   status, requested_effect, started_at, returned_at, normalized_return,
                   created_at, updated_at
              FROM hermes_runs
             WHERE issue_id = ANY(%s)
             ORDER BY issue_id, created_at, run_id
            """,
            (issue_ids,),
        )
        for row in cur.fetchall():
            item = _clean(dict(row))
            runs[item["issue_ref"]].append(item)

        cur.execute(
            """
            SELECT event_id, issue_id AS issue_ref, run_ref, event_type, actor,
                   actor_kind, expected_version, resulting_version,
                   idempotency_key, payload, occurred_at
              FROM issue_events
             WHERE issue_id = ANY(%s)
             ORDER BY issue_id, occurred_at, event_id
            """,
            (issue_ids,),
        )
        for row in cur.fetchall():
            item = _clean(dict(row))
            payload = item.pop("payload", {}) or {}
            if item["event_type"] == "status_changed" and "transition" in payload:
                item["transition"] = payload["transition"]
            events[item["issue_ref"]].append(item)

    return [
        _validated_aggregate(
            issue,
            comments=comments[issue["issue_id"]],
            runs=runs[issue["issue_id"]],
            events=events[issue["issue_id"]],
        )
        for issue in issues
    ]


def get_issue_record(conn: psycopg.Connection, issue_id: str) -> dict:
    """Return the Work Issue record with read-only Card metadata projected on top."""
    projection = work_issues.get_issue(conn, issue_id)
    issue = projection.get("work_issue")
    if not isinstance(issue, dict):
        raise work_issues.WorkIssueError(
            "stored Work Issue projection is missing its work_issue record"
        )
    return _card_projection(issue, _metadata(conn, issue_id))


def list_issue_projections(
    conn: psycopg.Connection,
    case_ref: str,
    *,
    include_terminal: bool = True,
    limit: int = 100,
) -> list[dict]:
    """Return governed Work Issue aggregates for one exact case reference.

    `case_ref` is matched exactly. The function does not infer project identity,
    traverse parents or broaden scope. Work Card metadata and activity are joined
    only for the Cockpit read projection; they do not schedule, dispatch or
    authorize.
    """
    if not case_ref.strip():
        raise work_issues.WorkIssueError("case_ref is required")
    if limit < 1 or limit > 500:
        raise work_issues.WorkIssueError("limit must be between 1 and 500")

    projections = _batched_aggregates(
        conn,
        case_ref,
        include_terminal=include_terminal,
        limit=limit,
    )
    if not projections:
        return []

    issue_ids = [projection["work_issue"]["issue_id"] for projection in projections]
    metadata = _metadata_by_issue(conn, issue_ids)
    for projection in projections:
        issue = projection["work_issue"]
        projection["work_issue"] = _card_projection(
            issue,
            metadata[issue["issue_id"]],
        )
        projection["work_activity"] = project_work_activity(projection)

    projections.sort(
        key=lambda projection: _STATUS_ORDER.get(
            projection["work_issue"]["status"], 99
        )
    )
    return projections
