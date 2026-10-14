"""Contract tests for bounded Hermes execution trace summaries."""

from __future__ import annotations

import copy

import pytest

from mvp_vertical import hermes_execution_trace


def _summary() -> dict:
    return {
        "schema_version": "hermes-execution-trace-summary-v1",
        "correlation": {
            "admission_id": "admission-1",
            "launch_reservation_id": "launch-reservation-1",
            "snapshot_id": "launch-snapshot-1",
            "snapshot_digest": "digest-1",
            "run_id": "run-1",
        },
        "execution": {"terminal_status": "completed"},
        "trace_refs": ["hermes://runs/run-1"],
        "provenance": {
            "pantheon_observed": [
                "correlation.admission_id",
                "correlation.launch_reservation_id",
                "correlation.snapshot_id",
                "correlation.snapshot_digest",
                "correlation.run_id",
            ],
            "binding_observed": ["trace_refs"],
            "runtime_reported": ["execution.terminal_status"],
        },
    }


def test_valid_partial_execution_trace_summary_is_accepted() -> None:
    assert hermes_execution_trace.validate_shape(_summary()) == _summary()


def test_unenumerated_optional_fact_remains_compatible_with_canonical_examples() -> None:
    summary = _summary()
    summary["runtime"] = {"implementation": "hermes-agent"}
    assert hermes_execution_trace.validate_shape(summary) == summary


def test_negative_counter_is_refused() -> None:
    summary = _summary()
    summary["execution"]["retry_count"] = -1
    summary["provenance"]["binding_observed"].append("execution.retry_count")
    with pytest.raises(hermes_execution_trace.HermesExecutionTraceError, match="between 0"):
        hermes_execution_trace.validate_shape(summary)


def test_false_pantheon_observed_provenance_is_refused() -> None:
    summary = _summary()
    summary["provenance"]["runtime_reported"] = []
    summary["provenance"]["pantheon_observed"].append("execution.terminal_status")
    with pytest.raises(
        hermes_execution_trace.HermesExecutionTraceError,
        match="pantheon_observed",
    ):
        hermes_execution_trace.validate_shape(summary)


def test_duplicate_provenance_path_is_refused() -> None:
    summary = _summary()
    summary["provenance"]["binding_observed"].append("execution.terminal_status")
    with pytest.raises(
        hermes_execution_trace.HermesExecutionTraceError,
        match="only one group",
    ):
        hermes_execution_trace.validate_shape(summary)


def test_provenance_cannot_name_an_absent_fact() -> None:
    summary = _summary()
    summary["provenance"]["binding_observed"].append("runtime.implementation")
    with pytest.raises(
        hermes_execution_trace.HermesExecutionTraceError,
        match="absent field",
    ):
        hermes_execution_trace.validate_shape(summary)


def test_oversized_collection_is_refused() -> None:
    summary = _summary()
    summary["tools"] = [
        {"tool_id": f"tool-{index}", "call_count": 1, "terminal_status": "completed"}
        for index in range(101)
    ]
    summary["provenance"]["runtime_reported"].append("tools")
    with pytest.raises(hermes_execution_trace.HermesExecutionTraceError, match="at most 100"):
        hermes_execution_trace.validate_shape(summary)


def test_summary_does_not_accept_new_refusal_vocabulary_silently() -> None:
    summary = _summary()
    summary["refusals"] = [{"code": "policy_denied", "count": 1}]
    summary["provenance"]["binding_observed"].append("refusals")
    with pytest.raises(
        hermes_execution_trace.HermesExecutionTraceError,
        match="first-slice vocabulary",
    ):
        hermes_execution_trace.validate_shape(summary)


def test_unknown_top_level_field_is_refused() -> None:
    summary = copy.deepcopy(_summary())
    summary["approval"] = True
    with pytest.raises(
        hermes_execution_trace.HermesExecutionTraceError,
        match="unsupported execution_trace_summary field",
    ):
        hermes_execution_trace.validate_shape(summary)
