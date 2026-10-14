from __future__ import annotations

import json
from pathlib import Path

from mvp_vertical import hermes_cli


class _FakeBinding:
    def __init__(self) -> None:
        self.launch_calls = []
        self.reconcile_calls = []

    def launch(self, **values):
        self.launch_calls.append(values)
        return {
            "kind": "external_hermes_run_launch_receipt",
            "admission_id": values["admission_id"],
            "run_id": "run-1",
            "automatic_retry_performed": False,
            "provider_routing_performed": False,
            "technical_receipt_is_evidence": False,
        }

    def reconcile_once(self, **values):
        self.reconcile_calls.append(values)
        return {
            "kind": "hermes_run_reconciliation",
            "run_id": values["launch_receipt"]["run_id"],
            "pantheon_return_recorded": True,
            "scheduler_effect": False,
            "retry_effect": False,
            "technical_receipt_is_evidence": False,
        }


def _governed_args(tmp_path: Path) -> list[str]:
    return [
        "--allowed-tool",
        "pantheon_context_manifest",
        "--expected-profile",
        "pantheon-governed",
        "--memory-status-receipt",
        str(tmp_path / "memory.json"),
    ]


def test_capture_memory_status_is_one_shot_and_writes_sanitized_receipt(
    monkeypatch, tmp_path: Path
) -> None:
    calls = []

    def capture(**values):
        calls.append(values)
        return {
            "kind": "hermes_profile_memory_observation",
            "profile": values["profile"],
            "status": "qualified",
            "raw_output_retained": False,
            "write_effect": False,
            "authority_effect": "none",
        }

    monkeypatch.setattr(hermes_cli, "capture_memory_status", capture)
    output = tmp_path / "memory.json"
    status = hermes_cli.main(
        [
            "capture-memory-status",
            "--profile",
            "pantheon-governed",
            "--hermes-command",
            "/opt/hermes/bin/hermes",
            "--timeout",
            "7",
            "--output",
            str(output),
        ]
    )

    assert status == 0
    assert calls == [{
        "profile": "pantheon-governed",
        "hermes_command": "/opt/hermes/bin/hermes",
        "timeout": 7.0,
    }]
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["raw_output_retained"] is False
    assert payload["write_effect"] is False
    assert payload["authority_effect"] == "none"


def test_launch_is_one_shot_and_writes_receipt(monkeypatch, tmp_path: Path) -> None:
    binding = _FakeBinding()
    monkeypatch.setattr(hermes_cli, "_binding", lambda args: binding)
    output = tmp_path / "launch.json"

    status = hermes_cli.main(
        [
            "launch",
            *_governed_args(tmp_path),
            "--admission-id",
            "admission-1",
            "--idempotency-key",
            "operator-key",
            "--output",
            str(output),
        ]
    )

    assert status == 0
    assert binding.launch_calls == [
        {"admission_id": "admission-1", "idempotency_key": "operator-key"}
    ]
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["automatic_retry_performed"] is False
    assert payload["provider_routing_performed"] is False
    assert payload["technical_receipt_is_evidence"] is False


def test_reconcile_observes_once_without_scheduler_or_retry(monkeypatch, tmp_path: Path) -> None:
    binding = _FakeBinding()
    monkeypatch.setattr(hermes_cli, "_binding", lambda args: binding)
    receipt = tmp_path / "launch.json"
    receipt.write_text(json.dumps({"admission_id": "admission-1", "run_id": "run-1"}), encoding="utf-8")
    output = tmp_path / "return.json"

    status = hermes_cli.main(
        [
            "reconcile",
            "--receipt",
            str(receipt),
            "--idempotency-key",
            "reconcile-key",
            "--output",
            str(output),
        ]
    )

    assert status == 0
    assert len(binding.reconcile_calls) == 1
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["scheduler_effect"] is False
    assert payload["retry_effect"] is False
    assert payload["technical_receipt_is_evidence"] is False


def test_launch_refuses_non_admission_identity(monkeypatch, capsys, tmp_path: Path) -> None:
    monkeypatch.setattr(hermes_cli, "_binding", lambda args: _FakeBinding())

    status = hermes_cli.main(
        [
            "launch",
            *_governed_args(tmp_path),
            "--admission-id",
            "task-1",
            "--idempotency-key",
            "operator-key",
        ]
    )

    assert status == 1
    assert "must be a Pantheon admission-... identity" in capsys.readouterr().err


def test_observe_requires_allowlist_profile_and_memory_receipt() -> None:
    parser = hermes_cli.build_parser()
    invalid = (
        ["observe"],
        ["observe", "--allowed-tool", "pantheon_context_manifest"],
        [
            "observe",
            "--allowed-tool",
            "pantheon_context_manifest",
            "--expected-profile",
            "pantheon-governed",
        ],
    )
    for argv in invalid:
        try:
            parser.parse_args(argv)
        except SystemExit as exc:
            assert exc.code == 2
        else:
            raise AssertionError(f"observe accepted incomplete governed posture: {argv}")


def test_observer_loader_passes_profile_and_memory_receipt(monkeypatch, tmp_path: Path) -> None:
    memory = tmp_path / "memory.json"
    memory.write_text(
        json.dumps({
            "kind": "hermes_profile_memory_observation",
            "profile": "pantheon-governed",
        }),
        encoding="utf-8",
    )
    captured = {}

    class FakeObserver:
        def __init__(self, *args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs

        def observe(self):
            return {"kind": "observed"}

    monkeypatch.setenv("HERMES_API_BASE", "http://hermes:8642/p/pantheon-governed")
    monkeypatch.setenv("HERMES_API_KEY", "hk")
    monkeypatch.setattr(hermes_cli, "HermesRunsApiObserver", FakeObserver)

    status = hermes_cli.main([
        "observe",
        "--allowed-tool",
        "pantheon_context_manifest",
        "--expected-profile",
        "pantheon-governed",
        "--memory-status-receipt",
        str(memory),
    ])

    assert status == 0
    assert captured["args"] == (
        "http://hermes:8642/p/pantheon-governed",
        "hk",
    )
    assert captured["kwargs"]["expected_profile"] == "pantheon-governed"
    assert captured["kwargs"]["memory_observation"]["profile"] == "pantheon-governed"
