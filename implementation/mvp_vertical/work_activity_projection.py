"""Strict Cockpit projection of the governed Work Issue aggregate.

The source aggregate remains authoritative. This module only derives a bounded
read model from fields already admitted by ``work_issue_slice.schema.yaml`` and
explicit Work Card presentation metadata. It does not infer runtime ownership,
human requests, Evidence status or task authorization from absent fields.

An admitted ``execution_trace_summary`` is passed through as technical read data
only. This projection does not reconstruct, enrich, persist or promote the
receipt and does not infer any governance effect from runtime success.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


VOCABULARY = (
    Path(__file__).resolve().parent
    / "cockpit"
    / "registries"
    / "work_activity_vocabulary.json"
)
PROJECTION_SCHEMA_ID = "cockpit.work_activity"
PROJECTION_SCHEMA_REVISION = 1
MAX_SUBJECT_TAGS = 5


class WorkActivityProjectionError(ValueError):
    """The governed aggregate cannot be projected without guessing."""


@lru_cache(maxsize=1)
def load_vocabulary() -> dict[str, Any]:
    try:
        vocabulary = json.loads(VOCABULARY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkActivityProjectionError(
            f"work activity vocabulary is unavailable or invalid: {exc}"
        ) from exc

    if vocabulary.get("schema_id") != "cockpit.work_activity_vocabulary":
        raise WorkActivityProjectionError("unexpected work activity vocabulary schema_id")
    if vocabulary.get("revision") != 1:
        raise WorkActivityProjectionError("unsupported work activity vocabulary revision")
    for key in ("statuses", "outcomes", "event_types"):
        if not isinstance(vocabulary.get(key), dict):
            raise WorkActivityProjectionError(f"work activity vocabulary requires {key}")
    return vocabulary


def _mapping(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise WorkActivityProjectionError(f"{field} must be an object")
    return value


def _sequence(value: Any, *, field: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise WorkActivityProjectionError(f"{field} must be an array of objects")
    return value


def _strings(value: Any, *, limit: int | None = None) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    seen: set[str] = set()
    for raw in value:
        item = str(raw).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
        if limit is not None and len(result) >= limit:
            break
    return result


def _title(entries: dict[str, Any], key: Any, *, field: str) -> str:
    entry = entries.get(str(key))
    if not isinstance(entry, dict) or not isinstance(entry.get("title"), str):
        raise WorkActivityProjectionError(f"{field} has no registered label for {key!r}")
    return entry["title"]


def _latest(items: list[dict[str, Any]], *fields: str) -> dict[str, Any] | None:
    if not items:
        return None

    def marker(item: dict[str, Any]) -> str:
        for field in fields:
            value = item.get(field)
            if value:
                return str(value)
        return ""

    return max(items, key=marker)


def _unique_strings(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value is None:
            continue
        text = str(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _event_projection(
    event: dict[str, Any],
    *,
    event_labels: dict[str, Any],
    issue_status_labels: dict[str, Any],
) -> dict[str, Any]:
    event_type = event.get("event_type")
    projected: dict[str, Any] = {
        "event_type": event_type,
        "label": _title(event_labels, event_type, field="event_types"),
        "occurred_at": event.get("occurred_at"),
        "actor": event.get("actor"),
        "actor_kind": event.get("actor_kind"),
        "run_ref": event.get("run_ref"),
    }

    if event_type == "status_changed":
        transition = _mapping(event.get("transition"), field="event.transition")
        from_status = transition.get("from_status")
        to_status = transition.get("to_status")
        projected["detail"] = (
            f"{_title(issue_status_labels, from_status, field='work_issue statuses')}"
            f" → {_title(issue_status_labels, to_status, field='work_issue statuses')}"
        )
    else:
        projected["detail"] = None
    return projected


def project_work_activity(aggregate: dict[str, Any]) -> dict[str, Any]:
    """Derive one strict activity read model from one governed aggregate.

    A missing Work Issue or missing aggregate collection is refused. In
    particular, a Hermes run is never projected as an orphan Work Issue.
    """

    root = _mapping(aggregate, field="aggregate")
    issue = _mapping(root.get("work_issue"), field="work_issue")
    issue_id = issue.get("issue_id")
    if not issue_id:
        raise WorkActivityProjectionError("work_issue.issue_id is required")

    _sequence(root.get("comments"), field="comments")
    runs = _sequence(root.get("hermes_runs"), field="hermes_runs")
    events = _sequence(root.get("events"), field="events")

    vocabulary = load_vocabulary()
    statuses = _mapping(vocabulary["statuses"], field="vocabulary.statuses")
    issue_status_labels = _mapping(
        statuses.get("work_issue"), field="vocabulary.statuses.work_issue"
    )
    run_status_labels = _mapping(
        statuses.get("hermes_run"), field="vocabulary.statuses.hermes_run"
    )
    outcome_labels = _mapping(vocabulary["outcomes"], field="vocabulary.outcomes")
    event_labels = _mapping(vocabulary["event_types"], field="vocabulary.event_types")

    issue_status = issue.get("status")
    issue_projection = {
        "issue_id": str(issue_id),
        "status": issue_status,
        "status_label": _title(
            issue_status_labels, issue_status, field="work_issue statuses"
        ),
        "assigned_to": issue.get("assigned_to"),
        "version": issue.get("version"),
        "task_contract_ref": issue.get("task_contract_ref"),
        "context_pack_ref": issue.get("context_pack_ref"),
        "type_tags": _strings(issue.get("type_tags")),
        "subject_tags": _strings(
            issue.get("subject_tags") or issue.get("tags"),
            limit=MAX_SUBJECT_TAGS,
        ),
        "limits": _strings(issue.get("limits")),
    }

    latest_run = _latest(
        runs, "updated_at", "returned_at", "started_at", "created_at"
    )
    latest_run_projection: dict[str, Any] | None = None
    result_candidate: dict[str, Any] | None = None
    execution_trace_summary: dict[str, Any] | None = None
    trace_refs: list[str] = []

    if latest_run is not None:
        run_status = latest_run.get("status")
        latest_run_projection = {
            "run_id": latest_run.get("run_id"),
            "status": run_status,
            "status_label": _title(
                run_status_labels, run_status, field="hermes_run statuses"
            ),
            "requested_effect": latest_run.get("requested_effect"),
            "started_at": latest_run.get("started_at"),
            "returned_at": latest_run.get("returned_at"),
            "updated_at": latest_run.get("updated_at"),
        }

        normalized_return = latest_run.get("normalized_return")
        if normalized_return is not None:
            returned = _mapping(
                normalized_return, field="hermes_run.normalized_return"
            )
            outcome = returned.get("outcome")
            trace_refs = _unique_strings(list(returned.get("trace_refs") or []))
            result_candidate = {
                "outcome": outcome,
                "outcome_label": _title(
                    outcome_labels, outcome, field="normalized return outcomes"
                ),
                "summary": returned.get("summary"),
                "result_refs": _unique_strings(
                    list(returned.get("result_refs") or [])
                ),
                "evidence_candidate_refs": _unique_strings(
                    list(returned.get("evidence_candidate_refs") or [])
                ),
                "trace_refs": trace_refs,
            }
            technical_receipt = returned.get("execution_trace_summary")
            if technical_receipt is not None:
                execution_trace_summary = dict(
                    _mapping(
                        technical_receipt,
                        field="hermes_run.normalized_return.execution_trace_summary",
                    )
                )

    activity = [
        _event_projection(
            event,
            event_labels=event_labels,
            issue_status_labels=issue_status_labels,
        )
        for event in events
    ]
    latest_event = _latest(activity, "occurred_at")

    return {
        "schema": {
            "id": PROJECTION_SCHEMA_ID,
            "revision": PROJECTION_SCHEMA_REVISION,
        },
        "issue": issue_projection,
        "latest_run": latest_run_projection,
        "activity": activity,
        "latest_event": latest_event,
        "result_candidate": result_candidate,
        "execution_trace_summary": execution_trace_summary,
        "trace_refs": trace_refs,
        "review_required": issue_status == "review",
        "limits": [
            "runtime_success != Evidence",
            "runtime_success != Decision",
            "runtime_success != Knowledge",
            "runtime_success != Work Issue resolution",
            "Trace != proof",
            "UI status != authorization",
        ],
    }
