from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from mvp_vertical import hermes_cli
from mvp_vertical.hermes_runs_observer import (
    capture_presentation_config,
    qualify_presentation_config_observation,
)


PROFILE = "pantheon-governed"


def _runner(values: dict[str, object], calls: list[tuple[list[str], dict]]):
    def run(command, **kwargs):
        calls.append((list(command), kwargs))
        key = command[-2]
        value = values.get(key, False)
        if value == "ERROR":
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="unsupported")
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps(value) + "\n", stderr="")

    return run


def _aligned_receipt(*, captured_at: str | None = None) -> dict:
    digest = "sha256:" + "0" * 64

    def record(key: str, value: bool) -> dict:
        return {
            "key": key,
            "value": value,
            "status": "observed",
            "exit_code": 0,
            "stdout_digest": digest,
        }

    return {
        "kind": "hermes_profile_presentation_config_observation",
        "observation_source": "hermes_config_get_json_cli",
        "profile": PROFILE,
        "captured_at": captured_at or datetime.now(timezone.utc).isoformat(),
        "settings": {
            "show_reasoning": record("display.show_reasoning", False),
            "show_commentary": record("display.show_commentary", True),
            "interim_assistant_messages": record("display.interim_assistant_messages", True),
            "stream_reasoning_deltas": record("plugins.stream_reasoning_deltas", False),
        },
        "platforms": {
            "telegram": {
                "show_reasoning": record("display.platforms.telegram.show_reasoning", False),
                "interim_assistant_messages": record(
                    "display.platforms.telegram.interim_assistant_messages", True
                ),
            }
        },
        "platform_scope": ["telegram"],
        "configuration_alignment": "aligned",
        "behavior_status": "not_evaluated",
        "raw_output_retained": False,
        "write_effect": False,
        "activation_changed": False,
        "authority_effect": "none",
        "technical_receipt_is_evidence": False,
    }


def test_capture_reads_resolved_global_and_platform_values_without_shell() -> None:
    calls: list[tuple[list[str], dict]] = []
    values = {
        "display.show_reasoning": False,
        "display.show_commentary": True,
        "display.interim_assistant_messages": True,
        "plugins.stream_reasoning_deltas": False,
        "display.platforms.telegram.show_reasoning": False,
        "display.platforms.telegram.interim_assistant_messages": True,
    }

    receipt = capture_presentation_config(
        profile=PROFILE,
        platforms=["telegram"],
        hermes_command="/opt/hermes/bin/hermes",
        timeout=7,
        runner=_runner(values, calls),
    )

    assert receipt["configuration_alignment"] == "aligned"
    assert receipt["settings"]["show_reasoning"]["value"] is False
    assert receipt["settings"]["stream_reasoning_deltas"]["value"] is False
    assert receipt["platforms"]["telegram"]["show_reasoning"]["value"] is False
    assert receipt["raw_output_retained"] is False
    assert receipt["write_effect"] is False
    assert receipt["authority_effect"] == "none"
    assert len(calls) == 6
    assert all(kwargs["shell"] is False for _, kwargs in calls)
    assert all(command[:3] == ["/opt/hermes/bin/hermes", "-p", PROFILE] for command, _ in calls)
    assert all(command[-1] == "--json" for command, _ in calls)


def test_reasoning_enabled_globally_or_on_platform_is_misaligned() -> None:
    calls: list[tuple[list[str], dict]] = []
    values = {
        "display.show_reasoning": False,
        "display.show_commentary": True,
        "display.interim_assistant_messages": True,
        "plugins.stream_reasoning_deltas": False,
        "display.platforms.telegram.show_reasoning": True,
        "display.platforms.telegram.interim_assistant_messages": True,
    }
    receipt = capture_presentation_config(
        profile=PROFILE,
        platforms=["telegram"],
        runner=_runner(values, calls),
    )
    assert receipt["configuration_alignment"] == "misaligned"

    qualified = qualify_presentation_config_observation(
        receipt,
        expected_profile=PROFILE,
    )
    assert qualified["receipt_status"] == "observed"
    assert qualified["configuration_alignment"] == "misaligned"
    assert qualified["posture_status"] == "not_qualified"
    assert qualified["behavior_status"] == "not_evaluated"


def test_missing_security_key_is_incomplete_not_silently_safe() -> None:
    calls: list[tuple[list[str], dict]] = []
    values = {
        "display.show_reasoning": False,
        "display.show_commentary": True,
        "display.interim_assistant_messages": True,
        "plugins.stream_reasoning_deltas": "ERROR",
    }
    receipt = capture_presentation_config(
        profile=PROFILE,
        runner=_runner(values, calls),
    )
    assert receipt["configuration_alignment"] == "incomplete"
    assert receipt["settings"]["stream_reasoning_deltas"]["status"] == "unsupported_or_error"


def test_aligned_configuration_remains_behaviorally_not_evaluated() -> None:
    result = qualify_presentation_config_observation(
        _aligned_receipt(),
        expected_profile=PROFILE,
    )
    assert result["receipt_status"] == "observed"
    assert result["configuration_alignment"] == "aligned"
    assert result["posture_status"] == "not_evaluated"
    assert result["behavior_status"] == "not_evaluated"
    assert result["configuration_only"] is True
    assert result["technical_receipt_is_evidence"] is False
    assert "user-visible behavior still requires surface observation" in result["reason"]


def test_stale_configuration_receipt_is_not_qualified_as_current_observation() -> None:
    now = datetime.now(timezone.utc)
    stale = _aligned_receipt(captured_at=(now - timedelta(minutes=10)).isoformat())
    result = qualify_presentation_config_observation(
        stale,
        expected_profile=PROFILE,
        observed_at=now,
    )
    assert result["receipt_status"] == "not_qualified"
    assert result["posture_status"] == "not_evaluated"
    assert "stale" in result["reason"]


def test_missing_receipt_preserves_backward_compatible_observation() -> None:
    result = qualify_presentation_config_observation(None, expected_profile=PROFILE)
    assert result["receipt_status"] == "not_evaluated"
    assert result["posture_status"] == "not_evaluated"
    assert result["behavior_status"] == "not_evaluated"


def test_cli_capture_presentation_config_is_one_shot(monkeypatch, tmp_path: Path) -> None:
    calls = []

    def capture(**values):
        calls.append(values)
        return {
            "kind": "hermes_profile_presentation_config_observation",
            "profile": values["profile"],
            "configuration_alignment": "aligned",
            "raw_output_retained": False,
            "write_effect": False,
            "authority_effect": "none",
        }

    monkeypatch.setattr(hermes_cli, "capture_presentation_config", capture)
    output = tmp_path / "presentation.json"
    status = hermes_cli.main([
        "capture-presentation-config",
        "--profile",
        PROFILE,
        "--platform",
        "telegram",
        "--platform",
        "discord",
        "--hermes-command",
        "/opt/hermes/bin/hermes",
        "--timeout",
        "7",
        "--output",
        str(output),
    ])

    assert status == 0
    assert calls == [{
        "profile": PROFILE,
        "platforms": ["telegram", "discord"],
        "hermes_command": "/opt/hermes/bin/hermes",
        "timeout": 7.0,
    }]
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["configuration_alignment"] == "aligned"
    assert payload["raw_output_retained"] is False


def test_cli_observe_adds_config_without_claiming_surface_qualification(
    monkeypatch, tmp_path: Path
) -> None:
    class FakeObserver:
        def observe(self):
            return {
                "kind": "hermes_runs_api_observation",
                "safety_status": "qualified",
                "non_equivalences": [],
            }

    receipt = tmp_path / "presentation.json"
    receipt.write_text(json.dumps(_aligned_receipt()), encoding="utf-8")
    memory = tmp_path / "memory.json"
    memory.write_text(json.dumps({"kind": "memory"}), encoding="utf-8")
    output = tmp_path / "observed.json"

    monkeypatch.setattr(hermes_cli, "_observer", lambda args: FakeObserver())
    status = hermes_cli.main([
        "observe",
        "--allowed-tool",
        "pantheon_context_manifest",
        "--expected-profile",
        PROFILE,
        "--memory-status-receipt",
        str(memory),
        "--presentation-config-receipt",
        str(receipt),
        "--output",
        str(output),
    ])

    assert status == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["safety_status"] == "qualified"
    assert payload["presentation_config"]["configuration_alignment"] == "aligned"
    assert payload["governed_surface_status"] == "not_evaluated"
    assert payload["presentation_behavior_status"] == "not_evaluated"
    assert "runtime safety_status qualified != governed surface qualified" in payload["non_equivalences"]


def test_observed_keys_match_the_namespace_the_deployment_script_writes() -> None:
    """Bind the observer's key namespace to the script that sets those values.

    The observer queried `platforms.<p>.show_reasoning` while
    `deployment/ubuntu/configure-hermes-activity-projection` sets
    `display.platforms.<p>.show_reasoning`. Hermes answered "no such key" for
    every platform, so `configuration_alignment` could never reach
    `misaligned` -- a channel projecting private reasoning stayed invisible to
    the one check meant to catch it. Reading the namespace off the script keeps
    the two from drifting apart again in silence.
    """
    script = (
        Path(__file__).resolve().parents[2]
        / "deployment"
        / "ubuntu"
        / "configure-hermes-activity-projection"
    ).read_text(encoding="utf-8")

    calls: list[tuple[list[str], dict]] = []
    capture_presentation_config(
        profile=PROFILE,
        platforms=["whatsapp"],
        runner=_runner({}, calls),
    )
    queried = {command[-2] for command, _ in calls}

    for key in sorted(queried):
        assert key in script, f"{key} is queried but never written by the deployment script"

    assert "display.platforms.whatsapp.show_reasoning" in queried
    assert "display.platforms.whatsapp.interim_assistant_messages" in queried
