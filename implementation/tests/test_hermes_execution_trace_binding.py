"""Binding production tests for the optional Hermes execution trace summary."""

from __future__ import annotations

from mvp_vertical.hermes_execution_trace import validate_shape
from mvp_vertical.hermes_run_binding import ExternalHermesRunBinding


class _Observer:
    def observe(self):
        return {
            "runs_api_status": "compatible",
            "safety_status": "qualified",
        }


class _Pantheon:
    def __init__(self):
        self.return_calls = []

    def reserve_launch(self, **kwargs):
        return {
            "launch_reservation_id": "launch-reservation-trace-1",
            "snapshot_id": "launch-snapshot-trace-1",
            "snapshot_digest": "sha256:" + "a" * 64,
            "work_issue_version": 4,
            "replayed": False,
            "snapshot": {
                "kind": "hermes_launch_context_snapshot",
                "question": "Analyse le projet.",
                "field_projection_version": "scoped-context-v1",
                "entities": [],
            },
        }

    def record_start(self, **kwargs):
        return {
            "runtime_start_recorded": True,
            "work_issue": {"version": 5},
        }

    def record_return(self, **kwargs):
        self.return_calls.append(kwargs)
        return {
            "runtime_status": kwargs["normalized_return"]["outcome"],
            "work_issue_auto_resolved": False,
            "evidence_created": False,
            "decision_created": False,
        }


class _Hermes:
    def __init__(self, status):
        self.status = status

    def submit(self, **kwargs):
        return {"run_id": "run-trace-1", "status": "started"}

    def get_status(self, run_id):
        assert run_id == "run-trace-1"
        return self.status


def _binding(*, pantheon, hermes):
    return ExternalHermesRunBinding(
        observer=_Observer(),
        pantheon=pantheon,
        hermes=hermes,
    )


def test_launch_then_reconcile_produces_only_observed_first_slice_trace() -> None:
    pantheon = _Pantheon()
    binding = _binding(
        pantheon=pantheon,
        hermes=_Hermes({"status": "completed", "output": "Analyse candidate."}),
    )

    launch_receipt = binding.launch(
        admission_id="admission-trace-1",
        idempotency_key="launch-trace-1",
    )
    result = binding.reconcile_once(
        launch_receipt=launch_receipt,
        idempotency_key="reconcile-trace-1",
    )

    assert result["pantheon_return_recorded"] is True
    assert result["technical_receipt_is_evidence"] is False
    assert len(pantheon.return_calls) == 1

    normalized = pantheon.return_calls[0]["normalized_return"]
    trace = normalized["execution_trace_summary"]
    assert result["execution_trace_summary"] == trace
    assert validate_shape(trace) == trace
    assert trace["correlation"] == {
        "admission_id": "admission-trace-1",
        "launch_reservation_id": "launch-reservation-trace-1",
        "snapshot_id": "launch-snapshot-trace-1",
        "snapshot_digest": "sha256:" + "a" * 64,
        "run_id": "run-trace-1",
    }
    assert trace["execution"] == {
        "terminal_status": "completed",
        "retry_count": 0,
    }
    assert trace["trace_refs"] == ["hermes://runs/run-trace-1"]
    assert trace["provenance"] == {
        "pantheon_observed": [
            "correlation.admission_id",
            "correlation.launch_reservation_id",
            "correlation.snapshot_id",
            "correlation.snapshot_digest",
            "correlation.run_id",
        ],
        "binding_observed": ["execution.retry_count"],
        "runtime_reported": ["execution.terminal_status"],
    }
    assert "runtime" not in trace
    assert "tools" not in trace
    assert "limits" not in trace
    assert "refusals" not in trace
    assert "step_count" not in trace["execution"]
    assert "repair_count" not in trace["execution"]


def test_retry_count_is_omitted_without_an_explicit_no_retry_observation() -> None:
    pantheon = _Pantheon()
    binding = _binding(
        pantheon=pantheon,
        hermes=_Hermes({"status": "completed", "output": "Analyse candidate."}),
    )

    result = binding.reconcile_once(
        launch_receipt={
            "admission_id": "admission-trace-1",
            "launch_reservation_id": "launch-reservation-trace-1",
            "snapshot_id": "launch-snapshot-trace-1",
            "snapshot_digest": "sha256:" + "a" * 64,
            "run_id": "run-trace-1",
            "return_expected_issue_version": 5,
        },
        idempotency_key="manual-reconcile-trace-1",
    )

    trace = result["execution_trace_summary"]
    assert trace["execution"] == {"terminal_status": "completed"}
    assert trace["provenance"]["binding_observed"] == []


def test_legacy_incomplete_launch_receipt_remains_accepted_without_trace_summary() -> None:
    pantheon = _Pantheon()
    binding = _binding(
        pantheon=pantheon,
        hermes=_Hermes({"status": "failed", "error": "synthetic failure"}),
    )

    result = binding.reconcile_once(
        launch_receipt={
            "admission_id": "admission-trace-1",
            "run_id": "run-trace-1",
            "return_expected_issue_version": 5,
        },
        idempotency_key="legacy-reconcile-trace-1",
    )

    assert result["pantheon_return_recorded"] is True
    normalized = pantheon.return_calls[0]["normalized_return"]
    assert normalized["outcome"] == "failed"
    assert "execution_trace_summary" not in normalized
    assert "execution_trace_summary" not in result
