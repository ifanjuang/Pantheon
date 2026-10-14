"""Distributed ambiguity tests for the Hermes live acceptance harness."""

from __future__ import annotations

from mvp_vertical.hermes_live_acceptance import (
    HermesLiveBindingAcceptance,
    SYNTHETIC_MARKER,
)
from mvp_vertical.hermes_run_binding import (
    HermesLaunchReplayRequiresReconciliation,
    HermesRunRegistrationUnknown,
    HermesRunSubmissionUnknown,
)


class _Observer:
    def observe(self):
        return {
            "runs_api_status": "compatible",
            "safety_status": "qualified",
        }


class _Pantheon:
    def execution_envelope(self, admission_id):
        return {
            "question": (
                f"{SYNTHETIC_MARKER} pantheon_context_manifest "
                "pantheon_context_entity"
            ),
            "context_pack": {
                "root_entity": {
                    "entity_type": "project",
                    "entity_id": "project:synthetic-ambiguity-proof",
                }
            },
        }


class _HermesUnused:
    def status(self, run_id):  # pragma: no cover - ambiguity exits before use
        raise AssertionError("Hermes inspector must not run after launch ambiguity")

    def collect_events(self, run_id):  # pragma: no cover
        raise AssertionError("Hermes inspector must not run after launch ambiguity")


class _SubmissionUnknown:
    def launch(self, **kwargs):
        raise HermesRunSubmissionUnknown(
            "unknown",
            launch_reservation_id="launch-reservation-unknown",
        )


class _RegistrationUnknown:
    def launch(self, **kwargs):
        raise HermesRunRegistrationUnknown(
            "registration unknown",
            launch_reservation_id="launch-reservation-known",
            run_id="run-known",
        )


class _Replay:
    def launch(self, **kwargs):
        raise HermesLaunchReplayRequiresReconciliation("replay")


def _run(binding):
    return HermesLiveBindingAcceptance(
        observer=_Observer(),
        binding=binding,
        pantheon=_Pantheon(),
        hermes=_HermesUnused(),
    ).run_live(
        admission_id="admission-synthetic-1",
        idempotency_key="acceptance-ambiguity-1",
        ack="SYNTHETIC_ONLY",
    )


def test_unknown_submission_is_inconclusive_and_preserves_reservation() -> None:
    receipt = _run(_SubmissionUnknown())
    assert receipt["target_binding_status"] == "inconclusive"
    assert receipt["distributed_ambiguity"] is True
    assert receipt["launch_reservation_id"] == "launch-reservation-unknown"
    assert receipt["run_id"] is None
    assert receipt["operator_reconciliation_required"] is True
    assert receipt["automatic_retry_performed"] is False
    assert receipt["automatic_stop_performed"] is False


def test_unknown_registration_preserves_real_run_id_without_retry() -> None:
    receipt = _run(_RegistrationUnknown())
    assert receipt["target_binding_status"] == "inconclusive"
    assert receipt["launch_reservation_id"] == "launch-reservation-known"
    assert receipt["run_id"] == "run-known"
    assert receipt["operator_reconciliation_required"] is True
    assert receipt["automatic_retry_performed"] is False


def test_replayed_reservation_never_becomes_permission_to_resubmit() -> None:
    receipt = _run(_Replay())
    assert receipt["target_binding_status"] == "inconclusive"
    assert receipt["operator_reconciliation_required"] is True
    assert receipt["automatic_retry_performed"] is False
