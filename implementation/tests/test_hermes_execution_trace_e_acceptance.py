from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "validate_hermes_execution_trace_e_acceptance.py"


def _module():
    spec = importlib.util.spec_from_file_location("hermes_execution_trace_e_acceptance", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def _artifacts(tmp_path: Path) -> Path:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    admission_id = "admission-hermes-020-lab"
    run_id = "run-phase-e-1"
    launch = {
        "admission_id": admission_id,
        "launch_reservation_id": "launch-reservation-hermes-020-lab",
        "snapshot_id": "launch-snapshot-hermes-020-lab",
        "snapshot_digest": "sha256:" + "2" * 64,
        "run_id": run_id,
        "automatic_retry_performed": False,
    }
    trace = {
        "schema_version": "hermes-execution-trace-summary-v1",
        "correlation": {
            key: launch[key]
            for key in (
                "admission_id",
                "launch_reservation_id",
                "snapshot_id",
                "snapshot_digest",
                "run_id",
            )
        },
        "execution": {"terminal_status": "completed", "retry_count": 0},
        "trace_refs": [f"hermes://runs/{run_id}"],
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
    reconciliation = {
        "pantheon_return_recorded": True,
        "execution_trace_summary": trace,
        "recorded": {
            "result_accepted": False,
            "evidence_admitted": False,
            "project_mutated": False,
        },
    }
    base = f"/hermes/execution-admissions/{admission_id}"
    state = {
        "pantheon_reads": [
            f"{base}/active-context",
            f"{base}/active-context/entities/project/project-lab",
            f"{base}/active-context/entities/project/project-outside",
        ],
        "pantheon_writes": [
            f"{base}/launch-reservations",
            f"{base}/runs/start",
            f"{base}/runs/{run_id}/return",
        ],
    }
    _write_json(artifacts / "launch-receipt.json", launch)
    _write_json(artifacts / "return-receipt.json", reconciliation)
    _write_json(artifacts / "fixture-state.json", state)
    return artifacts


def _contract_sources(tmp_path: Path) -> tuple[Path, Path]:
    runtime = tmp_path / "hermes_runtime_return.py"
    runtime.write_text(
        """from . import work_issues\n\ndef record_external_runtime_return():\n    return {\n        \"decision_created\": False,\n        \"evidence_admitted\": False,\n        \"external_effect_authorized\": False,\n    }\n""",
        encoding="utf-8",
    )
    issues = tmp_path / "work_issues.py"
    issues.write_text(
        'RETURN_TO_ISSUE_STATUS = {"result_candidate": "review", "failed": "waiting"}\n',
        encoding="utf-8",
    )
    return runtime, issues


def test_phase_e_acceptance_reuses_existing_artifacts_and_keeps_governance_separate(tmp_path: Path) -> None:
    module = _module()
    artifacts = _artifacts(tmp_path)
    runtime, issues = _contract_sources(tmp_path)

    result = module.validate(
        artifacts=artifacts,
        runtime_return_source=runtime,
        work_issues_source=issues,
    )

    assert result["status"] == "passed"
    assert result["exact_correlation_retained"] is True
    assert result["retry_count"] == 0
    assert result["governed_tools"] == [
        {
            "tool_id": "pantheon_context_manifest",
            "call_count": 1,
            "terminal_status": "completed",
        },
        {
            "tool_id": "pantheon_context_entity",
            "call_count": 2,
            "terminal_status": "completed",
        },
    ]
    assert result["refusals"] == [
        {"code": "context_entity_not_admitted", "count": 1}
    ]
    assert result["work_issue_auto_resolved"] is False
    assert result["evidence_admitted"] is False
    assert result["decision_created"] is False
    assert result["knowledge_or_memory_owner_reached"] is False
    assert result["external_effect_authorized"] is False


def test_phase_e_acceptance_fails_closed_on_an_extra_pantheon_write(tmp_path: Path) -> None:
    module = _module()
    artifacts = _artifacts(tmp_path)
    runtime, issues = _contract_sources(tmp_path)
    state_path = artifacts / "fixture-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["pantheon_writes"].append("/evidence/promote")
    _write_json(state_path, state)

    with pytest.raises(module.PhaseEAcceptanceError, match="unexpected Pantheon write"):
        module.validate(
            artifacts=artifacts,
            runtime_return_source=runtime,
            work_issues_source=issues,
        )


def test_phase_e_acceptance_fails_closed_on_an_extra_context_read(tmp_path: Path) -> None:
    module = _module()
    artifacts = _artifacts(tmp_path)
    runtime, issues = _contract_sources(tmp_path)
    state_path = artifacts / "fixture-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["pantheon_reads"].append(
        "/hermes/execution-admissions/admission-hermes-020-lab/active-context/entities/project/project-extra"
    )
    _write_json(state_path, state)

    with pytest.raises(
        module.PhaseEAcceptanceError,
        match="unexpected or repeated Pantheon context read",
    ):
        module.validate(
            artifacts=artifacts,
            runtime_return_source=runtime,
            work_issues_source=issues,
        )


def test_phase_e_acceptance_cross_checks_zero_retry_against_launch_receipt(tmp_path: Path) -> None:
    module = _module()
    artifacts = _artifacts(tmp_path)
    runtime, issues = _contract_sources(tmp_path)
    launch_path = artifacts / "launch-receipt.json"
    launch = json.loads(launch_path.read_text(encoding="utf-8"))
    launch["automatic_retry_performed"] = True
    _write_json(launch_path, launch)

    with pytest.raises(
        module.PhaseEAcceptanceError,
        match="does not prove zero automatic retries",
    ):
        module.validate(
            artifacts=artifacts,
            runtime_return_source=runtime,
            work_issues_source=issues,
        )


def test_phase_e_acceptance_fails_closed_on_relative_knowledge_owner_import(tmp_path: Path) -> None:
    module = _module()
    artifacts = _artifacts(tmp_path)
    runtime, issues = _contract_sources(tmp_path)
    runtime.write_text(
        runtime.read_text(encoding="utf-8").replace(
            "from . import work_issues",
            "from . import work_issues, knowledge_store",
        ),
        encoding="utf-8",
    )

    with pytest.raises(module.PhaseEAcceptanceError, match="Knowledge owner"):
        module.validate(
            artifacts=artifacts,
            runtime_return_source=runtime,
            work_issues_source=issues,
        )
