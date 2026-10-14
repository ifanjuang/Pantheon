from __future__ import annotations

from pathlib import Path

from mvp_vertical.work_activity_projection import project_work_activity


ROOT = Path(__file__).resolve().parents[1]
COCKPIT_PROJECTION = (
    ROOT / "mvp_vertical" / "cockpit" / "projection" / "cockpit_projection.js"
)


def _aggregate(*, execution_trace_summary: dict | None) -> dict:
    normalized_return = {
        "outcome": "result_candidate",
        "summary": "Candidate result",
        "result_refs": ["result://1"],
        "evidence_candidate_refs": [],
        "trace_refs": ["hermes://runs/run-cockpit-trace-1"],
    }
    if execution_trace_summary is not None:
        normalized_return["execution_trace_summary"] = execution_trace_summary

    return {
        "work_issue": {
            "issue_id": "work-cockpit-trace-1",
            "status": "review",
            "assigned_to": "hermes",
            "version": 4,
            "task_contract_ref": "task-contract:cockpit-trace-1",
            "context_pack_ref": "context-pack:cockpit-trace-1",
            "type_tags": ["verification"],
            "subject_tags": ["execution"],
            "limits": ["human review required"],
        },
        "comments": [],
        "hermes_runs": [
            {
                "run_id": "run-cockpit-trace-1",
                "status": "returned",
                "requested_effect": "read_only",
                "started_at": "2026-08-25T18:00:00Z",
                "returned_at": "2026-08-25T18:01:00Z",
                "updated_at": "2026-08-25T18:01:00Z",
                "normalized_return": normalized_return,
            }
        ],
        "events": [],
    }


def _summary() -> dict:
    return {
        "schema_version": "hermes-execution-trace-summary-v1",
        "correlation": {
            "admission_id": "admission-cockpit-trace-1",
            "launch_reservation_id": "launch-reservation-cockpit-trace-1",
            "snapshot_id": "launch-snapshot-cockpit-trace-1",
            "snapshot_digest": "sha256:" + "a" * 64,
            "run_id": "run-cockpit-trace-1",
        },
        "execution": {
            "terminal_status": "completed",
            "retry_count": 0,
        },
        "trace_refs": ["hermes://runs/run-cockpit-trace-1"],
        "provenance": {
            "pantheon_observed": [
                "correlation.admission_id",
                "correlation.launch_reservation_id",
                "correlation.snapshot_id",
                "correlation.snapshot_digest",
                "correlation.run_id",
            ],
            "binding_observed": ["execution.retry_count"],
            "runtime_reported": ["execution.terminal_status"],
        },
    }


def test_work_activity_passes_through_the_admitted_technical_receipt_without_governance_effect() -> None:
    summary = _summary()

    projected = project_work_activity(
        _aggregate(execution_trace_summary=summary)
    )

    assert projected["execution_trace_summary"] == summary
    assert projected["execution_trace_summary"] is not summary
    assert projected["issue"]["status"] == "review"
    assert projected["review_required"] is True
    assert projected["result_candidate"]["outcome"] == "result_candidate"
    assert projected["trace_refs"] == ["hermes://runs/run-cockpit-trace-1"]
    assert projected["limits"] == [
        "runtime_success != Evidence",
        "runtime_success != Decision",
        "runtime_success != Knowledge",
        "runtime_success != Work Issue resolution",
        "Trace != proof",
        "UI status != authorization",
    ]


def test_work_activity_keeps_the_execution_trace_summary_optional() -> None:
    projected = project_work_activity(
        _aggregate(execution_trace_summary=None)
    )

    assert projected["execution_trace_summary"] is None
    assert projected["issue"]["status"] == "review"
    assert projected["review_required"] is True


def test_work_card_renders_execution_trace_as_technical_detail_without_owning_status() -> None:
    source = COCKPIT_PROJECTION.read_text(encoding="utf-8")

    assert "technicalExecutionRows(activity.execution_trace_summary)" in source
    assert 'rows.push(["Exécution technique"' in source
    assert (
        "Information technique uniquement · succès runtime ≠ Evidence · Decision · "
        "Knowledge · résolution du Work Issue."
    ) in source
    assert 'status: projectedIssue?.status || issue.status || "open"' in source
    assert "execution_trace_summary" not in source.split(
        'status: projectedIssue?.status || issue.status || "open"', 1
    )[0].rsplit("return card({", 1)[-1]
