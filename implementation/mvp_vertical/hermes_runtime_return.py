"""Normalize an external Hermes return against one consumed execution admission.

The Work Issue keeps only its governed bounded normalized return. Rich candidate
material and optional typed Execution Results are stored separately as immutable
candidate records. None of these records closes the Work Issue, admits Evidence,
promotes Knowledge/memory, selects a variant or authorizes a consequential effect.
"""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from . import (
    execution_results,
    hermes_execution_trace,
    hermes_result_candidate,
    hermes_scoped_context,
    work_issue_read,
    work_issues,
)

ALLOWED_RETURN_FIELDS = {
    "outcome",
    "summary",
    "result_refs",
    "evidence_candidate_refs",
    "trace_refs",
    "execution_trace_summary",
}
PROJECT_VARIANT_KIND = "project_change_variant"


class HermesRuntimeReturnError(ValueError):
    pass


class HermesRuntimeReturnConflict(HermesRuntimeReturnError):
    pass


def _validate_normalized_return_shape(normalized_return: dict) -> None:
    unsupported = sorted(set(normalized_return) - ALLOWED_RETURN_FIELDS)
    if unsupported:
        raise HermesRuntimeReturnError(
            "unsupported normalized Hermes return field(s): " + ", ".join(unsupported)
        )
    summary = normalized_return.get("execution_trace_summary")
    if summary is not None:
        try:
            hermes_execution_trace.validate_shape(summary)
        except hermes_execution_trace.HermesExecutionTraceError as exc:
            raise HermesRuntimeReturnError(str(exc)) from exc


def _run_for_admission(
    conn: psycopg.Connection,
    *,
    admission_id: str,
    run_id: str,
) -> dict:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT r.*, a.work_issue_id, a.handoff_id, a.task_contract_ref,
                   h.context_pack
              FROM hermes_runs r
              JOIN hermes_execution_admissions a ON a.admission_id = r.admission_ref
              JOIN cockpit_hermes_handoffs h ON h.handoff_id = a.handoff_id
             WHERE r.run_id = %s
               AND r.admission_ref = %s
            """,
            (run_id, admission_id),
        )
        row = cur.fetchone()
    if row is None:
        raise HermesRuntimeReturnConflict(
            "Hermes return does not match a run consumed under this execution admission"
        )
    return dict(row)


def _event_exists(conn: psycopg.Connection, *, issue_id: str, idempotency_key: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM issue_events WHERE issue_id = %s AND idempotency_key = %s",
            (issue_id, idempotency_key),
        )
        return cur.fetchone() is not None


def _validate_candidate_sources(candidate: dict, context_pack: dict) -> None:
    admitted_sources = set(context_pack.get("source_refs") or [])
    returned_sources = set(candidate.get("source_refs") or [])
    outside_scope = sorted(returned_sources - admitted_sources)
    if outside_scope:
        raise HermesRuntimeReturnError(
            "Hermes result candidate references source(s) outside the admitted Context Pack: "
            + ", ".join(outside_scope)
        )


def _admitted_entities(context_pack: dict[str, Any]) -> set[tuple[str, str]]:
    """Return exact admitted identities plus their canonical unprefixed form.

    Context Pack entity refs may carry a transport prefix such as ``project:<id>``.
    The governed variant contract deliberately uses IDs without ``:``. Treating
    those two spellings as the same admitted identity does not widen the scope.
    """
    admitted: set[tuple[str, str]] = set()
    for ref in hermes_scoped_context.admitted_entity_refs(context_pack):
        entity_type = ref.entity_type
        entity_id = ref.entity_id
        admitted.add((entity_type, entity_id))
        prefix = f"{entity_type}:"
        if entity_id.startswith(prefix):
            canonical_id = entity_id[len(prefix):]
            if canonical_id:
                admitted.add((entity_type, canonical_id))
    return admitted


def _validate_project_variant_execution_result(
    execution_result: dict[str, Any],
    *,
    run: dict[str, Any],
) -> list[str]:
    if not isinstance(execution_result, dict):
        raise HermesRuntimeReturnError("execution_result must be an object")
    if execution_result.get("task_contract_ref") != run.get("task_contract_ref"):
        raise HermesRuntimeReturnConflict(
            "Execution Result task_contract_ref differs from the consumed admission"
        )

    project_ref = str(execution_result.get("project_ref") or "").strip()
    if not project_ref:
        raise HermesRuntimeReturnError("variant Execution Result project_ref is required")
    context_pack = dict(run.get("context_pack") or {})
    admitted = _admitted_entities(context_pack)
    if ("project", project_ref) not in admitted:
        raise HermesRuntimeReturnError(
            "variant Execution Result Project is outside the admitted Context Pack"
        )

    items = execution_result.get("results")
    if not isinstance(items, list) or not items:
        raise HermesRuntimeReturnError(
            "variant Execution Result must contain at least one result"
        )

    result_refs: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise HermesRuntimeReturnError("every Execution Result item must be an object")
        if item.get("result_kind") != PROJECT_VARIANT_KIND:
            raise HermesRuntimeReturnError(
                "admission-bound variant return accepts only project_change_variant results"
            )
        result_id = str(item.get("result_id") or "").strip()
        if not result_id or result_id in seen:
            raise HermesRuntimeReturnError(
                "variant Execution Result result_id values must be non-empty and unique"
            )
        seen.add(result_id)
        result_refs.append(result_id)

        payload = item.get("payload")
        if not isinstance(payload, dict):
            raise HermesRuntimeReturnError("project_change_variant payload must be an object")
        if payload.get("project_ref") != project_ref:
            raise HermesRuntimeReturnConflict(
                "variant payload and Execution Result refer to different Projects"
            )
        for basis_ref in payload.get("basis_refs") or []:
            if not isinstance(basis_ref, dict):
                raise HermesRuntimeReturnError("variant basis_ref must be an object")
            key = (
                str(basis_ref.get("entity_type") or "").strip(),
                str(basis_ref.get("entity_id") or "").strip(),
            )
            if not all(key) or key not in admitted:
                raise HermesRuntimeReturnError(
                    "variant basis reference is outside the admitted Context Pack: "
                    + ":".join(key)
                )
    return result_refs


def _append_result_refs(bounded_return: dict[str, Any], refs: list[str]) -> None:
    result_refs = list(bounded_return.get("result_refs") or [])
    for ref in refs:
        if ref in result_refs:
            continue
        if len(result_refs) >= 500:
            raise HermesRuntimeReturnError("result_refs exceeds the bounded maximum")
        result_refs.append(ref)
    bounded_return["result_refs"] = result_refs


def _project_result_to_work_card(
    conn: psycopg.Connection,
    *,
    issue_id: str,
    normalized_return: dict,
    persisted_candidate: dict | None,
) -> None:
    """Update only the Cockpit projection metadata; never the governed decision."""
    outcome = normalized_return.get("outcome")
    result_refs = list(normalized_return.get("result_refs") or [])
    candidate_ref = None
    if persisted_candidate is not None:
        candidate_ref = persisted_candidate.get("result_candidate_id")
    result_ref = candidate_ref or (str(result_refs[0]) if result_refs else None)

    decision_request = {}
    if outcome == "result_candidate":
        decision_request = {
            "title": "Validation du travail",
            "question": "Valider le résultat proposé ou le renvoyer en travail ?",
            "result_summary": str(normalized_return.get("summary") or ""),
            "options": ["Valider", "Refuser"],
        }

    conn.execute(
        """
        INSERT INTO work_card_metadata (
            issue_id, workflow, information_ref, result_ref, decision_request, updated_at
        ) VALUES (%s, '{}'::jsonb, NULL, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (issue_id) DO UPDATE
           SET result_ref = EXCLUDED.result_ref,
               decision_request = EXCLUDED.decision_request,
               updated_at = CURRENT_TIMESTAMP
        """,
        (issue_id, result_ref, Jsonb(decision_request)),
    )


def record_external_runtime_return(
    conn: psycopg.Connection,
    *,
    admission_id: str,
    run_id: str,
    normalized_return: dict,
    actor: str,
    expected_issue_version: int,
    idempotency_key: str,
    result_candidate: dict | None = None,
    execution_result: dict[str, Any] | None = None,
) -> dict:
    if not actor.strip():
        raise HermesRuntimeReturnError("Hermes actor is required")
    if not run_id.strip():
        raise HermesRuntimeReturnError("external Hermes run_id is required")
    _validate_normalized_return_shape(normalized_return)

    outcome = normalized_return.get("outcome")
    if outcome == "result_candidate" and result_candidate is None:
        raise HermesRuntimeReturnError(
            "outcome=result_candidate requires a separate Hermes result_candidate payload"
        )
    if outcome != "result_candidate" and result_candidate is not None:
        raise HermesRuntimeReturnError(
            "result_candidate payload is accepted only when outcome=result_candidate"
        )
    if outcome != "result_candidate" and execution_result is not None:
        raise HermesRuntimeReturnError(
            "execution_result payload is accepted only when outcome=result_candidate"
        )

    with conn.transaction():
        run = _run_for_admission(conn, admission_id=admission_id, run_id=run_id)
        trace_summary = normalized_return.get("execution_trace_summary")
        if trace_summary is not None:
            try:
                hermes_execution_trace.validate_against_persisted_run(
                    conn,
                    summary=trace_summary,
                    admission_id=admission_id,
                    run_id=run_id,
                    run=run,
                    normalized_trace_refs=list(normalized_return.get("trace_refs") or []),
                )
            except hermes_execution_trace.HermesExecutionTraceConflict as exc:
                raise HermesRuntimeReturnConflict(str(exc)) from exc
            except hermes_execution_trace.HermesExecutionTraceError as exc:
                raise HermesRuntimeReturnError(str(exc)) from exc

        issue = work_issue_read.get_issue_record(conn, run["work_issue_id"])
        if issue["version"] != expected_issue_version and run["status"] == "running":
            raise HermesRuntimeReturnConflict(
                f"stale Work Issue version: expected {expected_issue_version}, current {issue['version']}"
            )

        bounded_return = dict(normalized_return)
        persisted_execution_result = None
        if execution_result is not None:
            execution_result_refs = _validate_project_variant_execution_result(
                execution_result,
                run=run,
            )
            try:
                persisted_execution_result = execution_results.store_execution_result(
                    conn,
                    execution_result=execution_result,
                    idempotency_key=f"{idempotency_key}:execution-result",
                )
            except execution_results.ExecutionResultConflict as exc:
                raise HermesRuntimeReturnConflict(str(exc)) from exc
            except execution_results.ExecutionResultError as exc:
                raise HermesRuntimeReturnError(str(exc)) from exc
            _append_result_refs(bounded_return, execution_result_refs)

        persisted_candidate = None
        if result_candidate is not None:
            normalized_candidate = hermes_result_candidate.normalize_candidate(result_candidate)
            _validate_candidate_sources(normalized_candidate, dict(run["context_pack"] or {}))
            try:
                persisted_candidate = hermes_result_candidate.create_result_candidate(
                    conn,
                    run_id=run_id,
                    admission_id=admission_id,
                    issue_id=run["work_issue_id"],
                    summary=str(normalized_return.get("summary") or ""),
                    trace_refs=list(normalized_return.get("trace_refs") or []),
                    evidence_candidate_refs=list(
                        normalized_return.get("evidence_candidate_refs") or []
                    ),
                    candidate=normalized_candidate,
                    actor=actor.strip(),
                    idempotency_key=f"{idempotency_key}:result-candidate",
                )
            except hermes_result_candidate.HermesResultCandidateConflict as exc:
                raise HermesRuntimeReturnConflict(str(exc)) from exc
            except hermes_result_candidate.HermesResultCandidateError as exc:
                raise HermesRuntimeReturnError(str(exc)) from exc

            _append_result_refs(
                bounded_return,
                [persisted_candidate["result_candidate_id"]],
            )

        if run["status"] != "running":
            if not _event_exists(
                conn,
                issue_id=run["work_issue_id"],
                idempotency_key=idempotency_key,
            ):
                raise HermesRuntimeReturnConflict(
                    f"Hermes run is not running; current runtime status is {run['status']}"
                )
            stored_return = dict(run.get("normalized_return") or {})
            if stored_return != bounded_return:
                raise HermesRuntimeReturnConflict(
                    "idempotent Hermes return replay does not match the stored normalized return"
                )

        try:
            work_issues.record_hermes_return(
                conn,
                issue_id=run["work_issue_id"],
                run_id=run_id,
                normalized_return=bounded_return,
                actor=actor.strip(),
                expected_version=expected_issue_version,
                idempotency_key=idempotency_key,
            )
        except (work_issues.StaleWrite, work_issues.TransitionRefused) as exc:
            raise HermesRuntimeReturnConflict(str(exc)) from exc
        except work_issues.WorkIssueError as exc:
            raise HermesRuntimeReturnError(str(exc)) from exc

        _project_result_to_work_card(
            conn,
            issue_id=run["work_issue_id"],
            normalized_return=bounded_return,
            persisted_candidate=persisted_candidate,
        )
        updated_issue = work_issue_read.get_issue_record(conn, run["work_issue_id"])
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM hermes_runs WHERE run_id = %s", (run_id,))
            returned_run = dict(cur.fetchone())

        return {
            "admission_id": admission_id,
            "run_id": run_id,
            "runtime_return_recorded": True,
            "runtime_status": returned_run["status"],
            "work_issue": updated_issue,
            "result_status": "candidate",
            "result_candidate": persisted_candidate,
            "execution_result": persisted_execution_result,
            "execution_result_stored": persisted_execution_result is not None,
            "variant_selected": False,
            "project_mutated": False,
            "decision_created": False,
            "evidence_admitted": False,
            "external_effect_authorized": False,
            "issue_closed": updated_issue["status"] in {"done", "cancelled"},
            "non_equivalences": [
                "Hermes returned != Work Issue resolved",
                "Hermes result candidate != Evidence admitted",
                "Execution Result stored != variant selected",
                "variant produced != ChangeCandidate persisted",
                "source ref != Evidence",
                "trace != proof",
                "result candidate != canonical truth",
                "runtime success != governance success",
            ],
        }
