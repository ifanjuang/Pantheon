"""Validate the optional subordinate Hermes execution trace summary.

The summary is a bounded technical receipt embedded in the existing normalized
Runtime Return. It is not a new aggregate, Evidence, approval, truth or runtime
authority.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

import psycopg
from psycopg.rows import dict_row

SCHEMA_VERSION = "hermes-execution-trace-summary-v1"
MAX_SERIALIZED_BYTES = 64 * 1024
MAX_ITEMS = 100
MAX_PROVENANCE_PATHS = 200
MAX_IDENTIFIER_CHARS = 300
MAX_TRACE_REF_CHARS = 500
MAX_COUNTER = 2**31 - 1
TERMINAL_STATUSES = {"completed", "failed", "cancelled", "timed_out", "partial"}
PROVENANCE_GROUPS = {"pantheon_observed", "binding_observed", "runtime_reported"}
CORRELATION_PATHS = {
    "correlation.admission_id",
    "correlation.launch_reservation_id",
    "correlation.snapshot_id",
    "correlation.snapshot_digest",
    "correlation.run_id",
}


class HermesExecutionTraceError(ValueError):
    pass


class HermesExecutionTraceConflict(HermesExecutionTraceError):
    pass


def _bounded_string(value: Any, *, label: str, maximum: int = MAX_IDENTIFIER_CHARS) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HermesExecutionTraceError(f"{label} must be a non-empty string")
    if len(value) > maximum:
        raise HermesExecutionTraceError(f"{label} exceeds {maximum} characters")
    return value


def _bounded_counter(value: Any, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise HermesExecutionTraceError(f"{label} must be an integer")
    if value < 0 or value > MAX_COUNTER:
        raise HermesExecutionTraceError(f"{label} must be between 0 and {MAX_COUNTER}")
    return value


def _exact_keys(value: Mapping[str, Any], *, allowed: set[str], label: str) -> None:
    unsupported = sorted(set(value) - allowed)
    if unsupported:
        raise HermesExecutionTraceError(
            f"unsupported {label} field(s): " + ", ".join(unsupported)
        )


def _included_fact_paths(summary: Mapping[str, Any]) -> set[str]:
    paths: set[str] = set()
    correlation = summary["correlation"]
    paths.update(f"correlation.{key}" for key in correlation)
    runtime = summary.get("runtime")
    if isinstance(runtime, dict):
        paths.update(f"runtime.{key}" for key in runtime)
    execution = summary.get("execution")
    if isinstance(execution, dict):
        paths.update(f"execution.{key}" for key in execution)
    limits = summary.get("limits")
    if isinstance(limits, dict):
        paths.update(f"limits.{key}" for key in limits)
    for aggregate in ("tools", "refusals", "trace_refs"):
        if aggregate in summary:
            paths.add(aggregate)
    return paths


def validate_shape(summary: Any) -> dict[str, Any]:
    if not isinstance(summary, dict):
        raise HermesExecutionTraceError("execution_trace_summary must be an object")
    serialized = json.dumps(
        summary,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(serialized) > MAX_SERIALIZED_BYTES:
        raise HermesExecutionTraceError(
            f"execution_trace_summary exceeds {MAX_SERIALIZED_BYTES} serialized bytes"
        )

    _exact_keys(
        summary,
        allowed={
            "schema_version",
            "correlation",
            "runtime",
            "execution",
            "tools",
            "limits",
            "refusals",
            "trace_refs",
            "provenance",
        },
        label="execution_trace_summary",
    )
    if summary.get("schema_version") != SCHEMA_VERSION:
        raise HermesExecutionTraceError(
            f"execution_trace_summary.schema_version must be {SCHEMA_VERSION!r}"
        )

    correlation = summary.get("correlation")
    if not isinstance(correlation, dict):
        raise HermesExecutionTraceError("execution_trace_summary.correlation is required")
    correlation_keys = {
        "admission_id",
        "launch_reservation_id",
        "snapshot_id",
        "snapshot_digest",
        "run_id",
    }
    _exact_keys(correlation, allowed=correlation_keys, label="correlation")
    if set(correlation) != correlation_keys:
        raise HermesExecutionTraceError("execution_trace_summary.correlation is incomplete")
    for key in correlation_keys:
        _bounded_string(correlation[key], label=f"correlation.{key}")

    runtime = summary.get("runtime")
    if runtime is not None:
        if not isinstance(runtime, dict):
            raise HermesExecutionTraceError("execution_trace_summary.runtime must be an object")
        allowed = {"implementation", "version", "profile"}
        _exact_keys(runtime, allowed=allowed, label="runtime")
        if not runtime:
            raise HermesExecutionTraceError("execution_trace_summary.runtime cannot be empty")
        for key, value in runtime.items():
            maximum = 80 if key == "profile" else MAX_IDENTIFIER_CHARS
            _bounded_string(value, label=f"runtime.{key}", maximum=maximum)

    execution = summary.get("execution")
    if execution is not None:
        if not isinstance(execution, dict):
            raise HermesExecutionTraceError("execution_trace_summary.execution must be an object")
        allowed = {
            "started_at",
            "ended_at",
            "terminal_status",
            "step_count",
            "tool_call_count",
            "retry_count",
            "repair_count",
        }
        _exact_keys(execution, allowed=allowed, label="execution")
        if not execution:
            raise HermesExecutionTraceError("execution_trace_summary.execution cannot be empty")
        for key in ("started_at", "ended_at"):
            if key in execution:
                _bounded_string(execution[key], label=f"execution.{key}")
        if "terminal_status" in execution:
            status = _bounded_string(
                execution["terminal_status"], label="execution.terminal_status"
            )
            if status not in TERMINAL_STATUSES:
                raise HermesExecutionTraceError(
                    "execution.terminal_status is outside the bounded vocabulary"
                )
        for key in ("step_count", "tool_call_count", "retry_count", "repair_count"):
            if key in execution:
                _bounded_counter(execution[key], label=f"execution.{key}")

    tools = summary.get("tools")
    if tools is not None:
        if not isinstance(tools, list) or len(tools) > MAX_ITEMS:
            raise HermesExecutionTraceError(
                f"execution_trace_summary.tools must contain at most {MAX_ITEMS} items"
            )
        for index, item in enumerate(tools):
            if not isinstance(item, dict):
                raise HermesExecutionTraceError(f"tools[{index}] must be an object")
            _exact_keys(
                item,
                allowed={"tool_id", "call_count", "terminal_status"},
                label=f"tools[{index}]",
            )
            if set(item) != {"tool_id", "call_count", "terminal_status"}:
                raise HermesExecutionTraceError(f"tools[{index}] is incomplete")
            _bounded_string(item["tool_id"], label=f"tools[{index}].tool_id")
            _bounded_counter(item["call_count"], label=f"tools[{index}].call_count")
            _bounded_string(
                item["terminal_status"], label=f"tools[{index}].terminal_status"
            )

    limits = summary.get("limits")
    if limits is not None:
        if not isinstance(limits, dict):
            raise HermesExecutionTraceError("execution_trace_summary.limits must be an object")
        allowed = {"max_steps", "observed_steps", "timeout_seconds", "timed_out"}
        _exact_keys(limits, allowed=allowed, label="limits")
        if not limits:
            raise HermesExecutionTraceError("execution_trace_summary.limits cannot be empty")
        for key in ("max_steps", "observed_steps", "timeout_seconds"):
            if key in limits:
                _bounded_counter(limits[key], label=f"limits.{key}")
        if "timed_out" in limits and not isinstance(limits["timed_out"], bool):
            raise HermesExecutionTraceError("limits.timed_out must be boolean")

    refusals = summary.get("refusals")
    if refusals is not None:
        if not isinstance(refusals, list) or len(refusals) > MAX_ITEMS:
            raise HermesExecutionTraceError(
                f"execution_trace_summary.refusals must contain at most {MAX_ITEMS} items"
            )
        for index, item in enumerate(refusals):
            if not isinstance(item, dict):
                raise HermesExecutionTraceError(f"refusals[{index}] must be an object")
            _exact_keys(item, allowed={"code", "count"}, label=f"refusals[{index}]")
            if set(item) != {"code", "count"}:
                raise HermesExecutionTraceError(f"refusals[{index}] is incomplete")
            if item["code"] != "context_entity_not_admitted":
                raise HermesExecutionTraceError(
                    f"refusals[{index}].code is outside the first-slice vocabulary"
                )
            _bounded_counter(item["count"], label=f"refusals[{index}].count")

    trace_refs = summary.get("trace_refs")
    if trace_refs is not None:
        if not isinstance(trace_refs, list) or not trace_refs or len(trace_refs) > MAX_ITEMS:
            raise HermesExecutionTraceError(
                f"execution_trace_summary.trace_refs must contain 1..{MAX_ITEMS} items"
            )
        if len(set(trace_refs)) != len(trace_refs):
            raise HermesExecutionTraceError("execution_trace_summary.trace_refs must be unique")
        for index, ref in enumerate(trace_refs):
            _bounded_string(ref, label=f"trace_refs[{index}]", maximum=MAX_TRACE_REF_CHARS)

    provenance = summary.get("provenance")
    if not isinstance(provenance, dict) or set(provenance) != PROVENANCE_GROUPS:
        raise HermesExecutionTraceError(
            "execution_trace_summary.provenance must contain exactly "
            "pantheon_observed, binding_observed and runtime_reported"
        )
    all_paths: list[str] = []
    for group in sorted(PROVENANCE_GROUPS):
        paths = provenance[group]
        if not isinstance(paths, list) or len(paths) > MAX_PROVENANCE_PATHS:
            raise HermesExecutionTraceError(
                f"provenance.{group} must contain at most {MAX_PROVENANCE_PATHS} paths"
            )
        if len(set(paths)) != len(paths):
            raise HermesExecutionTraceError(f"provenance.{group} paths must be unique")
        for index, path in enumerate(paths):
            _bounded_string(path, label=f"provenance.{group}[{index}]")
        all_paths.extend(paths)
    if len(set(all_paths)) != len(all_paths):
        raise HermesExecutionTraceError("a provenance path may appear in only one group")

    included = _included_fact_paths(summary)
    unknown = sorted(set(all_paths) - included)
    if unknown:
        raise HermesExecutionTraceError(
            "provenance references absent field(s): " + ", ".join(unknown)
        )
    pantheon_paths = set(provenance["pantheon_observed"])
    if pantheon_paths != CORRELATION_PATHS:
        raise HermesExecutionTraceError(
            "first-slice pantheon_observed provenance must contain only exact correlation fields"
        )
    return summary


def validate_against_persisted_run(
    conn: psycopg.Connection,
    *,
    summary: dict[str, Any],
    admission_id: str,
    run_id: str,
    run: Mapping[str, Any],
    normalized_trace_refs: list[str],
) -> None:
    validate_shape(summary)
    correlation = summary["correlation"]
    if correlation["admission_id"] != admission_id:
        raise HermesExecutionTraceConflict(
            "execution trace admission_id differs from the route admission"
        )
    if correlation["run_id"] != run_id:
        raise HermesExecutionTraceConflict("execution trace run_id differs from the route run")

    reservation_ref = str(run.get("launch_reservation_ref") or "").strip()
    if not reservation_ref:
        raise HermesExecutionTraceConflict(
            "execution trace requires a persisted launch reservation for this run"
        )
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT launch_reservation_id, admission_id, snapshot_id, snapshot_digest
              FROM hermes_run_launch_reservations
             WHERE launch_reservation_id = %s
            """,
            (reservation_ref,),
        )
        reservation = cur.fetchone()
    if reservation is None:
        raise HermesExecutionTraceConflict("execution trace launch reservation is not persisted")
    expected = {
        "admission_id": str(reservation["admission_id"]),
        "launch_reservation_id": str(reservation["launch_reservation_id"]),
        "snapshot_id": str(reservation["snapshot_id"]),
        "snapshot_digest": str(reservation["snapshot_digest"]),
        "run_id": run_id,
    }
    for key, value in expected.items():
        if correlation[key] != value:
            raise HermesExecutionTraceConflict(
                f"execution trace correlation.{key} differs from persisted launch state"
            )

    summary_refs = list(summary.get("trace_refs") or [])
    outside = sorted(set(summary_refs) - set(normalized_trace_refs))
    if outside:
        raise HermesExecutionTraceConflict(
            "execution trace references are not present in normalized return trace_refs: "
            + ", ".join(outside)
        )
