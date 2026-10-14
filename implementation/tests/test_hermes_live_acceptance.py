"""Unit tests for the operator-only Hermes live binding acceptance harness."""

from __future__ import annotations

import json

import pytest

from mvp_vertical.hermes_live_acceptance import (
    EventCollection,
    HermesLiveAcceptanceRefused,
    HermesLiveBindingAcceptance,
    HermesRunEventInspector,
    SYNTHETIC_MARKER,
    _tool_event_assessment,
    _validate_synthetic_envelope,
)


class _SseResponse:
    def __init__(self, events):
        self._events = events

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def raise_for_status(self):
        return None

    def iter_lines(self):
        for event in self._events:
            yield "data: " + json.dumps(event)


class _SseClient:
    def __init__(self, events):
        self._events = events

    def stream(self, *_args, **_kwargs):
        return _SseResponse(self._events)


def test_event_inspector_projects_public_role_stages_beside_raw_events() -> None:
    events = [
        {"event": "reasoning.available", "text": "private", "timestamp": 1},
        {
            "event": "message.delta",
            "delta": "🦉 Athena · Plan\nAction: vérifier\n",
            "timestamp": 2,
        },
        {"event": "tool.started", "tool": "inventory", "timestamp": 3},
        {
            "event": "tool.completed",
            "tool": "inventory",
            "error": False,
            "timestamp": 4,
        },
        {"event": "run.completed", "timestamp": 5},
    ]
    result = HermesRunEventInspector(
        "http://hermes.invalid",
        "api-key",
        client=_SseClient(events),
    ).collect_events("run-role-1")

    assert result.events == events
    assert result.stream_complete is True
    assert [stage["visible_role"] for stage in result.role_stages] == [
        "Athena",
        "Athena",
        "Hermes",
        "Hermes",
        "Athena",
    ]
    assert all(stage["private_reasoning_included"] is False for stage in result.role_stages)


class _Observer:
    def __init__(self, *, qualified: bool = True, compatible: bool = True):
        self.qualified = qualified
        self.compatible = compatible
        self.calls = 0

    def observe(self):
        self.calls += 1
        return {
            "runs_api_status": "compatible" if self.compatible else "incomplete",
            "safety_status": "qualified" if self.qualified else "not_qualified",
            "tool_surface": {
                "active_tools": [
                    "pantheon_context_manifest",
                    "pantheon_context_entity",
                ]
            },
        }


class _Binding:
    def __init__(self):
        self.launch_calls = []
        self.reconcile_calls = []

    def launch(self, **kwargs):
        self.launch_calls.append(kwargs)
        return {
            "launch_reservation_id": "launch-reservation-1",
            "snapshot_id": "launch-snapshot-1",
            "snapshot_digest": "digest-1",
            "run_id": "run-1",
            "session_id": kwargs["admission_id"],
            "runtime_start_recorded": True,
            "return_expected_issue_version": 5,
            "automatic_retry_performed": False,
            "provider_routing_performed": False,
            "model_override_performed": False,
        }

    def reconcile_once(self, **kwargs):
        self.reconcile_calls.append(kwargs)
        return {
            "runtime_status": "completed",
            "pantheon_return_recorded": True,
        }


class _Pantheon:
    def __init__(self, *, synthetic: bool = True, scope_refused: bool = True, closed: bool = True):
        self.synthetic = synthetic
        self.scope_refused = scope_refused
        self.closed = closed

    def execution_envelope(self, admission_id):
        root_id = "project:synthetic-hermes-acceptance" if self.synthetic else "project:real-client"
        question = (
            f"{SYNTHETIC_MARKER} Call pantheon_context_manifest, then "
            "pantheon_context_entity for the root entity."
            if self.synthetic
            else "Analyse le dossier client."
        )
        return {
            "question": question,
            "context_pack": {
                "root_entity": {"entity_type": "project", "entity_id": root_id},
            },
        }

    def active_manifest(self, admission_id):
        return {
            "entities": [
                {
                    "entity_type": "project",
                    "entity_id": "project:synthetic-hermes-acceptance",
                }
            ]
        }

    def probe_out_of_scope(self, **kwargs):
        return {
            "http_status": 409 if self.scope_refused else 200,
            "refused": self.scope_refused,
            "scope_refusal_verified": self.scope_refused,
            "detail": "requested entity is outside the exact admitted Context Pack",
        }

    def probe_context_closed(self, admission_id):
        return {
            "http_status": 409 if self.closed else 200,
            "closed": self.closed,
            "detail": "admission-bound context requires a running Hermes run",
        }


class _Hermes:
    def __init__(self, *, session_ok: bool = True, stream_complete: bool = True, omit_entity: bool = False):
        self.session_ok = session_ok
        self.stream_complete = stream_complete
        self.omit_entity = omit_entity
        self.status_calls = 0

    def status(self, run_id):
        self.status_calls += 1
        if self.status_calls == 1:
            return {
                "run_id": run_id,
                "status": "running",
                "session_id": "admission-1" if self.session_ok else "wrong-session",
                "model": "hermes-agent",
            }
        return {
            "run_id": run_id,
            "status": "completed",
            "session_id": "admission-1" if self.session_ok else "wrong-session",
            "model": "hermes-agent",
        }

    def collect_events(self, run_id):
        events = [
            {"event": "tool.started", "tool": "pantheon_context_manifest"},
            {"event": "tool.completed", "tool": "pantheon_context_manifest", "error": False},
        ]
        if not self.omit_entity:
            events.extend(
                [
                    {"event": "tool.started", "tool": "pantheon_context_entity"},
                    {"event": "tool.completed", "tool": "pantheon_context_entity", "error": False},
                ]
            )
        events.append({"event": "run.completed"})
        return EventCollection(
            events=events,
            stream_complete=self.stream_complete,
            diagnostic=None if self.stream_complete else "stream timeout",
        )


def _harness(*, observer=None, binding=None, pantheon=None, hermes=None):
    return HermesLiveBindingAcceptance(
        observer=observer or _Observer(),
        binding=binding or _Binding(),
        pantheon=pantheon or _Pantheon(),
        hermes=hermes or _Hermes(),
    )


def test_synthetic_envelope_requires_marker_root_and_explicit_context_tools() -> None:
    valid = {
        "question": (
            f"{SYNTHETIC_MARKER} pantheon_context_manifest pantheon_context_entity"
        ),
        "context_pack": {
            "root_entity": {
                "entity_type": "project",
                "entity_id": "project:synthetic-live-proof",
            }
        },
    }
    assert _validate_synthetic_envelope(valid) == {
        "entity_type": "project",
        "entity_id": "project:synthetic-live-proof",
    }

    invalid = dict(valid)
    invalid["question"] = "pantheon_context_manifest pantheon_context_entity"
    with pytest.raises(HermesLiveAcceptanceRefused, match="must contain marker"):
        _validate_synthetic_envelope(invalid)


def test_live_run_requires_explicit_synthetic_ack_before_launch() -> None:
    binding = _Binding()
    harness = _harness(binding=binding)
    with pytest.raises(HermesLiveAcceptanceRefused, match="SYNTHETIC_ONLY"):
        harness.run_live(
            admission_id="admission-1",
            idempotency_key="acceptance-0001",
            ack="",
        )
    assert binding.launch_calls == []


def test_unqualified_tool_surface_refuses_before_launch() -> None:
    binding = _Binding()
    harness = _harness(observer=_Observer(qualified=False), binding=binding)
    with pytest.raises(HermesLiveAcceptanceRefused, match="not qualified"):
        harness.run_live(
            admission_id="admission-1",
            idempotency_key="acceptance-0001",
            ack="SYNTHETIC_ONLY",
        )
    assert binding.launch_calls == []


def test_non_synthetic_admission_refuses_before_launch() -> None:
    binding = _Binding()
    harness = _harness(binding=binding, pantheon=_Pantheon(synthetic=False))
    with pytest.raises(HermesLiveAcceptanceRefused):
        harness.run_live(
            admission_id="admission-1",
            idempotency_key="acceptance-0001",
            ack="SYNTHETIC_ONLY",
        )
    assert binding.launch_calls == []


def test_full_live_acceptance_passes_only_with_all_boundary_proofs() -> None:
    binding = _Binding()
    result = _harness(binding=binding).run_live(
        admission_id="admission-1",
        idempotency_key="acceptance-0001",
        ack="SYNTHETIC_ONLY",
    )
    assert result["target_binding_status"] == "pass"
    assert all(result["checks"].values())
    assert result["technical_receipt_is_evidence"] is False
    assert result["activation_changed"] is False
    assert result["production_authorization"] is False
    assert len(binding.launch_calls) == 1
    assert len(binding.reconcile_calls) == 1


def test_missing_required_context_tool_is_a_failed_target_proof() -> None:
    result = _harness(hermes=_Hermes(omit_entity=True)).run_live(
        admission_id="admission-1",
        idempotency_key="acceptance-0001",
        ack="SYNTHETIC_ONLY",
    )
    assert result["target_binding_status"] == "fail"
    assert result["checks"]["required_context_tools_started"] is False
    assert result["checks"]["required_context_tools_completed"] is False


def test_incomplete_event_stream_is_inconclusive_not_pass() -> None:
    result = _harness(hermes=_Hermes(stream_complete=False)).run_live(
        admission_id="admission-1",
        idempotency_key="acceptance-0001",
        ack="SYNTHETIC_ONLY",
    )
    assert result["target_binding_status"] == "inconclusive"
    assert result["event_stream_complete"] is False


def test_session_mismatch_or_scope_escape_cannot_pass() -> None:
    mismatch = _harness(hermes=_Hermes(session_ok=False)).run_live(
        admission_id="admission-1",
        idempotency_key="acceptance-0001",
        ack="SYNTHETIC_ONLY",
    )
    assert mismatch["target_binding_status"] == "fail"
    assert mismatch["checks"]["session_echo_verified"] is False

    escaped = _harness(pantheon=_Pantheon(scope_refused=False)).run_live(
        admission_id="admission-1",
        idempotency_key="acceptance-0002",
        ack="SYNTHETIC_ONLY",
    )
    assert escaped["target_binding_status"] == "fail"
    assert escaped["checks"]["out_of_scope_refusal_verified"] is False


def test_tool_event_assessment_distinguishes_completion_and_errors() -> None:
    assessed = _tool_event_assessment(
        [
            {"event": "tool.started", "tool": "pantheon_context_manifest"},
            {"event": "tool.completed", "tool": "pantheon_context_manifest", "error": False},
            {"event": "tool.started", "tool": "pantheon_context_entity"},
            {"event": "tool.completed", "tool": "pantheon_context_entity", "error": True},
            {"event": "run.completed"},
        ]
    )
    assert assessed["required_tools_started"] is True
    assert assessed["required_tools_completed"] is True
    assert assessed["required_tools_error_free"] is False
    assert assessed["tool_errors"] == ["pantheon_context_entity"]
