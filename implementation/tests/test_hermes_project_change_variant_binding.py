"""Unit tests for Project change variants on the canonical Hermes run binding."""

from __future__ import annotations

import json

import pytest

from mvp_vertical.hermes_run_binding import (
    ExternalHermesRunBinding,
    HermesRunBindingError,
)


class _Observer:
    def observe(self):
        return {"runs_api_status": "compatible", "safety_status": "qualified"}


class _Pantheon:
    def __init__(self):
        self.reserve_calls = []
        self.start_calls = []
        self.return_calls = []

    def reserve_launch(self, **kwargs):
        self.reserve_calls.append(kwargs)
        return {
            "launch_reservation_id": "launch-reservation-variant",
            "snapshot_id": "launch-snapshot-variant",
            "snapshot_digest": "sha256:" + "2" * 64,
            "work_issue_version": 4,
            "replayed": False,
            "snapshot": {
                "kind": "hermes_launch_context_snapshot",
                "question": "Compare deux variantes.",
                "entities": [],
            },
        }

    def record_start(self, **kwargs):
        self.start_calls.append(kwargs)
        return {"runtime_start_recorded": True, "work_issue": {"version": 5}}

    def record_return(self, **kwargs):
        self.return_calls.append(kwargs)
        return {
            "runtime_return_recorded": True,
            "execution_result_stored": kwargs.get("execution_result") is not None,
            "variant_selected": False,
            "project_mutated": False,
            "decision_created": False,
            "evidence_admitted": False,
            "external_effect_authorized": False,
        }


class _Hermes:
    def __init__(self, status):
        self.status = status
        self.submit_calls = []
        self.status_calls = []

    def submit(self, **kwargs):
        self.submit_calls.append(kwargs)
        return {"run_id": "run-variant-1", "status": "started"}

    def get_status(self, run_id):
        self.status_calls.append(run_id)
        return self.status


def _execution_result() -> dict:
    shared = {
        "candidate_kind": "project_change_variant",
        "request_ref": "variant-request.project.couverture",
        "request_scope_digest": "sha256:" + "4" * 64,
        "project_ref": "project-lab",
        "base_revision": 1,
        "target_schema_id": "agency.project.v2",
        "rationale": "Alternative à comparer.",
        "assumptions": [],
        "compatibility_findings": [],
        "open_questions": [],
        "basis_refs": [{"entity_type": "project", "entity_id": "project-lab"}],
        "limitations": [],
        "authority": {
            "creates_change_candidate": False,
            "selects_variant": False,
            "applies_project_change": False,
            "creates_project_claim": False,
            "adopts_project_truth": False,
            "creates_decision": False,
            "admits_evidence": False,
            "authorizes_effect": False,
        },
    }

    def item(result_id: str, label: str, title: str) -> dict:
        payload = dict(shared)
        payload.update(
            {
                "variant_label": label,
                "variant_title": title,
                "proposed_attributes": {"architectural_style": title},
            }
        )
        return {
            "result_id": result_id,
            "result_kind": "project_change_variant",
            "schema_ref": "schemas/project_change_variant_candidate.schema.yaml",
            "payload": payload,
        }

    return {
        "execution_result_id": "execution-result.project-variants",
        "task_contract_ref": "task-contract.project-variants",
        "project_ref": "project-lab",
        "producer": {
            "capability": "compare_project_variants",
            "implementation": "hermes.skill.project-variants",
            "version": "0.20.0",
        },
        "produced_at": "2026-08-07T00:00:00+00:00",
        "authority": {
            "is_fact": False,
            "is_evidence": False,
            "is_decision": False,
            "is_memory": False,
            "is_apu_write": False,
            "authorizes_external_effect": False,
        },
        "results": [
            item("result.variant.zinc", "option-zinc", "Couverture zinc"),
            item("result.variant.ardoise", "option-ardoise", "Couverture ardoise"),
        ],
        "clarification_requests": [],
    }


def _receipt() -> dict:
    return {
        "admission_id": "admission-variant-1",
        "run_id": "run-variant-1",
        "return_expected_issue_version": 5,
    }


def _binding(status: dict, *, pantheon=None, hermes=None):
    return ExternalHermesRunBinding(
        observer=_Observer(),
        pantheon=pantheon or _Pantheon(),
        hermes=hermes or _Hermes(status),
    )


def test_launch_remains_the_existing_one_shot_binding() -> None:
    pantheon = _Pantheon()
    hermes = _Hermes({"status": "running"})
    receipt = _binding({}, pantheon=pantheon, hermes=hermes).launch(
        admission_id="admission-variant-1",
        idempotency_key="variant-launch-key",
    )
    assert len(pantheon.reserve_calls) == 1
    assert len(hermes.submit_calls) == 1
    assert len(pantheon.start_calls) == 1
    assert receipt["run_id"] == "run-variant-1"
    assert receipt["automatic_retry_performed"] is False


def test_completed_structured_output_records_execution_result_without_selection() -> None:
    pantheon = _Pantheon()
    hermes = _Hermes(
        {
            "status": "completed",
            "output": json.dumps(
                {
                    "kind": "pantheon_project_change_variants",
                    "summary": "Deux alternatives à comparer.",
                    "execution_result": _execution_result(),
                }
            ),
        }
    )
    result = _binding({}, pantheon=pantheon, hermes=hermes).reconcile_once(
        launch_receipt=_receipt(),
        idempotency_key="variant-reconcile-key",
    )

    assert hermes.status_calls == ["run-variant-1"]
    assert len(pantheon.return_calls) == 1
    call = pantheon.return_calls[0]
    assert call["normalized_return"]["result_refs"] == [
        "result.variant.zinc",
        "result.variant.ardoise",
    ]
    assert call["execution_result"]["execution_result_id"] == (
        "execution-result.project-variants"
    )
    assert call["result_candidate"]["candidate_payload"]["variant_count"] == 2
    assert result["kind"] == "hermes_run_reconciliation"
    assert result["execution_result_stored"] is True
    assert result["project_change_variant_count"] == 2
    assert result["variant_selected"] is False
    assert result["project_mutated"] is False
    assert result["decision_created"] is False
    assert result["evidence_admitted"] is False


@pytest.mark.parametrize(
    "output, message",
    [
        (
            json.dumps(
                {
                    "kind": "pantheon_project_change_variants",
                    "summary": "Sans résultat.",
                }
            ),
            "requires execution_result",
        ),
        (
            json.dumps(
                {
                    "kind": "pantheon_project_change_variants",
                    "summary": "Une seule option.",
                    "execution_result": {
                        **_execution_result(),
                        "results": [_execution_result()["results"][0]],
                    },
                }
            ),
            "at least two alternatives",
        ),
        (
            json.dumps(
                {
                    "kind": "pantheon_project_change_variants",
                    "summary": "Deux options.",
                    "execution_result": _execution_result(),
                    "unexpected": True,
                }
            ),
            "unsupported Project variant envelope field",
        ),
    ],
)
def test_malformed_variant_envelope_fails_before_pantheon_write(output: str, message: str) -> None:
    pantheon = _Pantheon()
    binding = _binding(
        {"status": "completed", "output": output},
        pantheon=pantheon,
    )
    with pytest.raises(HermesRunBindingError, match=message):
        binding.reconcile_once(
            launch_receipt=_receipt(),
            idempotency_key="variant-reconcile-key",
        )
    assert pantheon.return_calls == []


def test_non_variant_output_preserves_generic_reconciliation() -> None:
    pantheon = _Pantheon()
    result = _binding(
        {"status": "completed", "output": "ordinary candidate"},
        pantheon=pantheon,
    ).reconcile_once(
        launch_receipt=_receipt(),
        idempotency_key="variant-reconcile-key",
    )
    assert result["kind"] == "hermes_run_reconciliation"
    assert len(pantheon.return_calls) == 1
    assert pantheon.return_calls[0].get("execution_result") is None
    assert pantheon.return_calls[0]["result_candidate"]["result_type"] == "hermes_run_output"


def test_running_and_cancelled_are_observations_only() -> None:
    for runtime_status in ("running", "cancelled"):
        pantheon = _Pantheon()
        result = _binding(
            {"status": runtime_status},
            pantheon=pantheon,
        ).reconcile_once(
            launch_receipt=_receipt(),
            idempotency_key="variant-reconcile-key",
        )
        assert result["pantheon_return_recorded"] is False
        assert pantheon.return_calls == []


def test_failed_run_uses_existing_failed_return_without_execution_result() -> None:
    pantheon = _Pantheon()
    result = _binding(
        {"status": "failed", "error": "provider failed"},
        pantheon=pantheon,
    ).reconcile_once(
        launch_receipt=_receipt(),
        idempotency_key="variant-reconcile-key",
    )
    assert len(pantheon.return_calls) == 1
    assert pantheon.return_calls[0]["normalized_return"]["outcome"] == "failed"
    assert pantheon.return_calls[0].get("execution_result") is None
    assert "execution_result_stored" not in result
