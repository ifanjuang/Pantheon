"""Composed acceptance test for the candidate Pantheon-Hermes distribution.

This test joins the real one-shot run binding with the real context-bridge tool
handlers using deterministic fakes. It proves composition only; it does not claim
an installed runtime, activation, task authorization, result acceptance or Evidence.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from mvp_vertical.hermes_run_binding import ExternalHermesRunBinding


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_TOOLS = ROOT / "hermes" / "plugins" / "pantheon-context-bridge" / "tools.py"


def _load_context_bridge():
    spec = importlib.util.spec_from_file_location("pantheon_context_bridge_tools", PLUGIN_TOOLS)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Observer:
    def observe(self) -> dict:
        return {
            "runs_api_status": "compatible",
            "safety_status": "qualified",
            "authority_effect": "none",
        }


class _Pantheon:
    def __init__(self) -> None:
        self.started: list[dict] = []
        self.returned: list[dict] = []

    def reserve_launch(self, **values) -> dict:
        assert values["admission_id"] == "admission-distribution-1"
        return {
            "launch_reservation_id": "launch-distribution-1",
            "snapshot_id": "snapshot-distribution-1",
            "snapshot_digest": "digest-distribution-1",
            "work_issue_version": 7,
            "replayed": False,
            "snapshot": {
                "kind": "hermes_launch_context_snapshot",
                "requested_effect": "read_only",
                "question": "Review the admitted Project context.",
                "entities": [
                    {
                        "entity_ref": {
                            "entity_type": "project",
                            "entity_id": "project:p1",
                        },
                        "materializable": True,
                    }
                ],
            },
        }

    def record_start(self, **values) -> dict:
        self.started.append(values)
        return {
            "runtime_start_recorded": True,
            "work_issue": {"version": 8},
        }

    def record_return(self, **values) -> dict:
        self.returned.append(values)
        return {
            "runtime_return_recorded": True,
            "result_accepted": False,
            "evidence_admitted": False,
            "project_mutated": False,
        }


class _Hermes:
    def __init__(self) -> None:
        self.submitted: list[dict] = []

    def submit(self, **values) -> dict:
        self.submitted.append(values)
        return {"run_id": "run-distribution-1", "status": "started"}

    def get_status(self, run_id: str) -> dict:
        assert run_id == "run-distribution-1"
        return {
            "status": "completed",
            "output": "Candidate review produced from the admitted context only.",
        }


def test_composed_distribution_launches_reads_context_and_returns_candidate(monkeypatch) -> None:
    pantheon = _Pantheon()
    hermes = _Hermes()
    binding = ExternalHermesRunBinding(
        observer=_Observer(),
        pantheon=pantheon,
        hermes=hermes,
    )

    receipt = binding.launch(
        admission_id="admission-distribution-1",
        idempotency_key="distribution-acceptance",
    )

    assert receipt["session_id"] == "admission-distribution-1"
    assert receipt["runtime_submission_performed"] is True
    assert receipt["automatic_retry_performed"] is False
    assert receipt["provider_routing_performed"] is False
    assert receipt["technical_receipt_is_evidence"] is False

    submitted = hermes.submitted[0]
    bootstrap = json.loads(submitted["input_text"])
    assert bootstrap["launch_context_snapshot"]["requested_effect"] == "read_only"
    assert submitted["session_id"] == receipt["session_id"]

    bridge = _load_context_bridge()
    observed_paths: list[str] = []

    def fake_get_json(path: str) -> dict:
        observed_paths.append(path)
        if path.endswith("/active-context"):
            return {
                "kind": "hermes_scoped_context_manifest",
                "admission_id": "admission-distribution-1",
                "entities": [
                    {"entity_type": "project", "entity_id": "project:p1"}
                ],
                "authority_effect": "none",
            }
        return {
            "kind": "hermes_scoped_context_entity",
            "entity_ref": {"entity_type": "project", "entity_id": "project:p1"},
            "record": {"project_id": "p1", "revision": 3},
            "is_evidence": False,
        }

    monkeypatch.setattr(bridge, "_get_json", fake_get_json)
    manifest = json.loads(
        bridge.pantheon_context_manifest({}, task_id=receipt["session_id"])
    )
    entity = json.loads(
        bridge.pantheon_context_entity(
            {"entity_type": "project", "entity_id": "project:p1"},
            task_id=receipt["session_id"],
        )
    )

    assert manifest["authority_effect"] == "none"
    assert entity["is_evidence"] is False
    assert observed_paths == [
        "/hermes/execution-admissions/admission-distribution-1/active-context",
        "/hermes/execution-admissions/admission-distribution-1/active-context/entities/project/project%3Ap1",
    ]

    reconciled = binding.reconcile_once(
        launch_receipt=receipt,
        idempotency_key="distribution-acceptance",
    )

    assert reconciled["pantheon_return_recorded"] is True
    assert pantheon.returned[0]["normalized_return"]["outcome"] == "result_candidate"
    assert pantheon.returned[0]["result_candidate"]["source_refs"] == []
    assert reconciled["recorded"] == {
        "runtime_return_recorded": True,
        "result_accepted": False,
        "evidence_admitted": False,
        "project_mutated": False,
    }
