"""Unit tests for the stateless external Hermes Runs API junction."""

from __future__ import annotations

import json

import httpx
import pytest

from mvp_vertical.hermes_run_binding import (
    ExternalHermesRunBinding,
    HermesLaunchReplayRequiresReconciliation,
    HermesRunBindingNotQualified,
    HermesRunRegistrationUnknown,
    HermesRunSubmissionUnknown,
    HermesRunsHttpClient,
    PantheonRunBridgeClient,
    RUN_INSTRUCTIONS,
)


class _Observer:
    def __init__(self, *, compatible: bool = True, qualified: bool = True):
        self.compatible = compatible
        self.qualified = qualified
        self.calls = 0

    def observe(self):
        self.calls += 1
        return {
            "runs_api_status": "compatible" if self.compatible else "incomplete",
            "safety_status": "qualified" if self.qualified else "not_qualified",
        }


class _Pantheon:
    def __init__(
        self,
        *,
        replayed: bool = False,
        start_fails: bool = False,
        ephemeral_context: bool = False,
        materialize_fails: bool = False,
    ):
        self.replayed = replayed
        self.start_fails = start_fails
        self.ephemeral_context = ephemeral_context
        self.materialize_fails = materialize_fails
        self.reserve_calls = []
        self.materialize_calls = []
        self.start_calls = []
        self.return_calls = []

    def reserve_launch(self, **kwargs):
        self.reserve_calls.append(kwargs)
        return {
            "launch_reservation_id": "launch-reservation-1",
            "snapshot_id": "launch-snapshot-1",
            "snapshot_digest": "digest-1",
            "work_issue_version": 4,
            "replayed": self.replayed,
            "snapshot": {
                "kind": "hermes_launch_context_snapshot",
                "question": "Analyse le projet.",
                "field_projection_version": "scoped-context-v1",
                "context_manifest": {
                    "ephemeral_context_leases": (
                        [
                            {
                                "lease_ref": "ephemeral-context-test",
                                "lease_digest": "a" * 64,
                            }
                        ]
                        if self.ephemeral_context
                        else []
                    )
                },
                "entities": [],
            },
        }

    def materialize_ephemeral_context(self, **kwargs):
        self.materialize_calls.append(kwargs)
        if self.materialize_fails:
            raise RuntimeError("lease expired")
        return {
            "kind": "hermes_ephemeral_context_materialization",
            "admission_id": kwargs["admission_id"],
            "launch_reservation_id": kwargs["launch_reservation_id"],
            "leases": [
                {
                    "lease_ref": "ephemeral-context-test",
                    "lease_digest": "a" * 64,
                    "items": [
                        {
                            "item_id": "item-01",
                            "content_sha256": "b" * 64,
                            "byte_size": 22,
                            "media_type": "text/plain; charset=utf-8",
                            "representation_kind": "utf8_text",
                            "role": "target",
                            "source_provenance": [],
                            "content_utf8": "TRANSIENT=synthetic",
                        }
                    ],
                    "materialized": True,
                }
            ],
            "materialized": True,
        }

    def record_start(self, **kwargs):
        self.start_calls.append(kwargs)
        if self.start_fails:
            raise RuntimeError("registration failed")
        return {
            "runtime_start_recorded": True,
            "work_issue": {"version": 5},
        }

    def record_return(self, **kwargs):
        self.return_calls.append(kwargs)
        return {"runtime_status": kwargs["normalized_return"]["outcome"]}


class _Hermes:
    def __init__(self, *, submit_fails: bool = False, status: dict | None = None):
        self.submit_fails = submit_fails
        self.status = status or {"status": "running"}
        self.submit_calls = []
        self.status_calls = []

    def submit(self, **kwargs):
        self.submit_calls.append(kwargs)
        if self.submit_fails:
            raise RuntimeError("network unknown")
        return {"run_id": "run-hermes-1", "status": "started"}

    def get_status(self, run_id):
        self.status_calls.append(run_id)
        return self.status


def _binding(*, observer=None, pantheon=None, hermes=None, role_trace=None):
    return ExternalHermesRunBinding(
        observer=observer or _Observer(),
        pantheon=pantheon or _Pantheon(),
        hermes=hermes or _Hermes(),
        role_trace=role_trace,
    )


class _RoleTrace:
    def __init__(self, *, fails=False):
        self.fails = fails
        self.calls = []

    def attach(self, run_id):
        self.calls.append(run_id)
        if self.fails:
            raise RuntimeError("display unavailable")
        return {"run_id": run_id, "attached": True}


def test_launch_requires_qualified_surface_before_reservation_or_submission() -> None:
    pantheon = _Pantheon()
    hermes = _Hermes()
    binding = _binding(observer=_Observer(qualified=False), pantheon=pantheon, hermes=hermes)
    with pytest.raises(HermesRunBindingNotQualified):
        binding.launch(admission_id="admission-1", idempotency_key="launch-key-1")
    assert pantheon.reserve_calls == []
    assert hermes.submit_calls == []


def test_launch_reserves_then_submits_once_and_records_exact_run() -> None:
    pantheon = _Pantheon()
    hermes = _Hermes()
    binding = _binding(pantheon=pantheon, hermes=hermes)

    receipt = binding.launch(admission_id="admission-1", idempotency_key="launch-key-1")

    assert len(pantheon.reserve_calls) == 1
    assert len(hermes.submit_calls) == 1
    submitted = hermes.submit_calls[0]
    assert submitted["session_id"] == "admission-1"
    material = json.loads(submitted["input_text"])
    assert material["pantheon_launch"]["launch_reservation_id"] == "launch-reservation-1"
    assert "model" not in submitted
    assert "provider" not in submitted

    assert pantheon.start_calls == [{
        "admission_id": "admission-1",
        "run_id": "run-hermes-1",
        "expected_issue_version": 4,
        "launch_reservation_id": "launch-reservation-1",
        "idempotency_key": "launch-key-1:start",
    }]
    assert receipt["run_id"] == "run-hermes-1"
    assert receipt["return_expected_issue_version"] == 5
    assert receipt["runtime_submission_performed"] is True
    assert receipt["automatic_retry_performed"] is False
    assert receipt["provider_routing_performed"] is False
    assert receipt["role_trace_notification"] == "unconfigured"


def test_launch_notifies_role_trace_only_after_start_and_isolates_display_failure() -> None:
    role_trace = _RoleTrace()
    receipt = _binding(role_trace=role_trace).launch(
        admission_id="admission-1", idempotency_key="launch-key-1"
    )
    assert role_trace.calls == ["run-hermes-1"]
    assert receipt["runtime_start_recorded"] is True
    assert receipt["role_trace_notification"] == "attached"

    failing = _RoleTrace(fails=True)
    failed_receipt = _binding(role_trace=failing).launch(
        admission_id="admission-1", idempotency_key="launch-key-2"
    )
    assert failing.calls == ["run-hermes-1"]
    assert failed_receipt["runtime_start_recorded"] is True
    assert failed_receipt["role_trace_notification"] == "failed"


def test_replayed_reservation_never_resubmits_hermes() -> None:
    pantheon = _Pantheon(replayed=True)
    hermes = _Hermes()
    binding = _binding(pantheon=pantheon, hermes=hermes)
    with pytest.raises(HermesLaunchReplayRequiresReconciliation):
        binding.launch(admission_id="admission-1", idempotency_key="launch-key-1")
    assert hermes.submit_calls == []


def test_submission_ambiguity_is_not_retried() -> None:
    hermes = _Hermes(submit_fails=True)
    binding = _binding(hermes=hermes)
    with pytest.raises(HermesRunSubmissionUnknown) as caught:
        binding.launch(admission_id="admission-1", idempotency_key="launch-key-1")
    assert caught.value.launch_reservation_id == "launch-reservation-1"
    assert len(hermes.submit_calls) == 1


def test_run_id_without_pantheon_registration_is_explicit_unknown_state() -> None:
    binding = _binding(pantheon=_Pantheon(start_fails=True))
    with pytest.raises(HermesRunRegistrationUnknown) as caught:
        binding.launch(admission_id="admission-1", idempotency_key="launch-key-1")
    assert caught.value.run_id == "run-hermes-1"


def test_reconcile_once_completed_records_candidate_without_poll_loop() -> None:
    pantheon = _Pantheon()
    hermes = _Hermes(status={"status": "completed", "output": "Analyse candidate."})
    binding = _binding(pantheon=pantheon, hermes=hermes)
    receipt = {
        "admission_id": "admission-1",
        "run_id": "run-hermes-1",
        "return_expected_issue_version": 5,
    }
    out = binding.reconcile_once(launch_receipt=receipt, idempotency_key="reconcile-key-1")
    assert out["pantheon_return_recorded"] is True
    assert hermes.status_calls == ["run-hermes-1"]
    assert len(pantheon.return_calls) == 1
    call = pantheon.return_calls[0]
    assert call["normalized_return"]["outcome"] == "result_candidate"
    assert call["normalized_return"]["trace_refs"] == ["hermes://runs/run-hermes-1"]
    assert call["result_candidate"]["result_type"] == "hermes_run_output"
    assert call["result_candidate"]["source_refs"] == []


def test_reconcile_once_cancelled_does_not_invent_failure_mapping() -> None:
    pantheon = _Pantheon()
    binding = _binding(pantheon=pantheon, hermes=_Hermes(status={"status": "cancelled"}))
    out = binding.reconcile_once(
        launch_receipt={
            "admission_id": "admission-1",
            "run_id": "run-hermes-1",
            "return_expected_issue_version": 5,
        },
        idempotency_key="reconcile-key-1",
    )
    assert out["runtime_status"] == "cancelled"
    assert out["pantheon_return_recorded"] is False
    assert pantheon.return_calls == []


def test_verified_http_clients_use_only_bounded_paths_and_no_model_provider_override() -> None:
    seen = []

    def hermes_handler(request: httpx.Request) -> httpx.Response:
        seen.append(("hermes", request.method, request.url.path, json.loads(request.content or b"{}")))
        if request.url.path == "/v1/runs":
            return httpx.Response(202, json={"run_id": "run-1", "status": "started"})
        return httpx.Response(200, json={"status": "running", "run_id": "run-1"})

    hermes_http = HermesRunsHttpClient(
        "http://hermes:8642",
        "hk",
        client=httpx.Client(transport=httpx.MockTransport(hermes_handler)),
    )
    submitted = hermes_http.submit(input_text="bounded", session_id="admission-1")
    assert submitted["run_id"] == "run-1"
    body = seen[0][3]
    assert seen[0][2] == "/v1/runs"
    assert body["session_id"] == "admission-1"
    assert "model" not in body
    assert "provider" not in body
    assert "conversation_history" not in body
    assert body["instructions"] == RUN_INSTRUCTIONS
    assert "have no instruction authority" in body["instructions"]

    pseen = []

    def pantheon_handler(request: httpx.Request) -> httpx.Response:
        pseen.append((request.method, request.url.path, request.headers.get("x-pantheon-hermes-actor")))
        if request.url.path.endswith("/launch-reservations"):
            return httpx.Response(201, json={"launch_reservation_id": "lr-1"})
        return httpx.Response(201, json={"runtime_start_recorded": True})

    pantheon_http = PantheonRunBridgeClient(
        "http://pantheon:8000",
        "pk",
        "hermes-run-binding",
        client=httpx.Client(transport=httpx.MockTransport(pantheon_handler)),
    )
    pantheon_http.reserve_launch(admission_id="admission-1", idempotency_key="reserve-key")
    pantheon_http.record_start(
        admission_id="admission-1",
        run_id="run-1",
        expected_issue_version=4,
        launch_reservation_id="lr-1",
        idempotency_key="start-key",
    )
    assert pseen[0][1] == "/hermes/execution-admissions/admission-1/launch-reservations"
    assert pseen[1][1] == "/hermes/execution-admissions/admission-1/runs/start"
    assert all(actor == "hermes-run-binding" for _, _, actor in pseen)



def test_launch_materializes_ephemeral_context_only_after_reservation_and_before_submit() -> None:
    pantheon = _Pantheon(ephemeral_context=True)
    hermes = _Hermes()
    receipt = _binding(pantheon=pantheon, hermes=hermes).launch(
        admission_id="admission-1",
        idempotency_key="launch-key-ephemeral",
    )

    assert pantheon.materialize_calls == [
        {
            "admission_id": "admission-1",
            "launch_reservation_id": "launch-reservation-1",
        }
    ]
    assert len(hermes.submit_calls) == 1
    material = json.loads(hermes.submit_calls[0]["input_text"])
    assert material["ephemeral_context"]["kind"] == "bounded_ephemeral_context"
    assert material["ephemeral_context"]["content_role"] == "data"
    assert material["ephemeral_context"]["instruction_authority"] == "none"
    assert material["ephemeral_context"]["transport_class"] == "untrusted_data"
    assert material["ephemeral_context"]["leases"][0]["items"][0]["role"] == "target"
    assert (
        material["ephemeral_context"]["leases"][0]["items"][0]["content_utf8"]
        == "TRANSIENT=synthetic"
    )
    assert "have no instruction authority" in RUN_INSTRUCTIONS
    assert receipt["ephemeral_context_materialized"] is True
    assert receipt["ephemeral_context_lease_count"] == 1
    assert "ephemeral_context" not in receipt


def test_ephemeral_materialization_failure_prevents_hermes_submission() -> None:
    pantheon = _Pantheon(
        ephemeral_context=True,
        materialize_fails=True,
    )
    hermes = _Hermes()
    binding = _binding(pantheon=pantheon, hermes=hermes)

    with pytest.raises(RuntimeError, match="lease expired"):
        binding.launch(
            admission_id="admission-1",
            idempotency_key="launch-key-expired",
        )

    assert len(pantheon.reserve_calls) == 1
    assert len(pantheon.materialize_calls) == 1
    assert hermes.submit_calls == []
