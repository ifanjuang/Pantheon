from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from mvp_vertical.hermes_runs_observer import (
    HermesMemoryObservationError,
    capture_memory_status,
    parse_memory_status,
    qualify_memory_observation,
)


QUALIFIED_OUTPUT = """
Memory status
────────────────────────────────────────
  Built-in (MEMORY.md / USER.md):
    Memory injection:   disabled ✗
    User profile:       disabled ✗
    Memory tool:        disabled ✗
  Provider:  (none — built-in only)
"""


def test_parse_complete_disabled_posture_is_qualified_without_raw_output() -> None:
    receipt = parse_memory_status(QUALIFIED_OUTPUT, profile="pantheon-governed")

    assert receipt["status"] == "qualified"
    assert receipt["profile"] == "pantheon-governed"
    assert receipt["external_provider"] == "off"
    assert receipt["built_in_memory_injection"] == "off"
    assert receipt["built_in_user_profile_injection"] == "off"
    assert receipt["memory_tool"] == "off"
    assert receipt["missing_axes"] == []
    assert receipt["active_axes"] == []
    assert receipt["raw_output_retained"] is False
    assert receipt["stdout_digest"].startswith("sha256:")
    assert "stdout" not in receipt
    assert receipt["write_effect"] is False
    assert receipt["authority_effect"] == "none"


def test_active_or_incomplete_memory_posture_is_not_qualified() -> None:
    active = parse_memory_status(
        QUALIFIED_OUTPUT.replace("Memory injection:   disabled", "Memory injection:   enabled")
        .replace("Provider:  (none — built-in only)", "Provider:  mem0"),
        profile="pantheon-governed",
    )
    assert active["status"] == "not_qualified"
    assert active["active_axes"] == ["built_in_memory_injection", "external_provider"]

    incomplete = parse_memory_status(
        "Memory status\n  Provider: (none — built-in only)\n",
        profile="pantheon-governed",
    )
    assert incomplete["status"] == "not_qualified"
    assert incomplete["missing_axes"] == [
        "built_in_memory_injection",
        "built_in_user_profile_injection",
        "memory_tool",
    ]


def test_capture_runs_exact_read_only_command_without_shell() -> None:
    calls = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(stdout=QUALIFIED_OUTPUT, stderr="", returncode=0)

    receipt = capture_memory_status(
        profile="pantheon-governed",
        hermes_command="/opt/hermes/bin/hermes",
        timeout=7.0,
        runner=runner,
    )

    assert calls == [(
        ["/opt/hermes/bin/hermes", "-p", "pantheon-governed", "memory", "status"],
        {
            "capture_output": True,
            "text": True,
            "timeout": 7.0,
            "check": False,
            "shell": False,
        },
    )]
    assert receipt["status"] == "qualified"
    assert receipt["command"][-4:] == ["-p", "pantheon-governed", "memory", "status"]


def test_failed_capture_and_bad_profile_fail_closed() -> None:
    def runner(command, **kwargs):
        return SimpleNamespace(stdout=QUALIFIED_OUTPUT, stderr="failed", returncode=2)

    receipt = capture_memory_status(profile="pantheon-governed", runner=runner)
    assert receipt["status"] == "not_qualified"
    assert "did not exit successfully" in receipt["reason"]

    with pytest.raises(HermesMemoryObservationError, match="letters, numbers"):
        capture_memory_status(profile="../personal", runner=runner)


def test_qualification_requires_matching_profile_and_all_axes_off() -> None:
    now = datetime(2026, 8, 4, 18, 0, tzinfo=timezone.utc)
    receipt = parse_memory_status(
        QUALIFIED_OUTPUT,
        profile="pantheon-governed",
        captured_at=(now - timedelta(seconds=15)).isoformat(),
    )
    qualified = qualify_memory_observation(
        receipt,
        expected_profile="pantheon-governed",
        observed_at=now,
    )
    assert qualified["status"] == "qualified"
    assert qualified["session_memory_key"] == "absent"
    assert qualified["age_seconds"] == 15.0

    mismatch = qualify_memory_observation(
        receipt,
        expected_profile="assistant-personal",
        observed_at=now,
    )
    assert mismatch["status"] == "not_qualified"
    assert "differs from expected profile" in mismatch["reason"]

    missing = qualify_memory_observation(
        None,
        expected_profile="pantheon-governed",
        observed_at=now,
    )
    assert missing["status"] == "not_evaluated"
    assert missing["session_memory_key"] == "absent"


def test_qualification_rejects_stale_future_or_misattributed_receipts() -> None:
    now = datetime(2026, 8, 4, 18, 0, tzinfo=timezone.utc)
    cases = (
        (
            parse_memory_status(
                QUALIFIED_OUTPUT,
                profile="pantheon-governed",
                captured_at=(now - timedelta(minutes=6)).isoformat(),
            ),
            "is stale",
        ),
        (
            parse_memory_status(
                QUALIFIED_OUTPUT,
                profile="pantheon-governed",
                captured_at=(now + timedelta(minutes=1)).isoformat(),
            ),
            "in the future",
        ),
        (
            parse_memory_status(
                QUALIFIED_OUTPUT,
                profile="pantheon-governed",
                captured_at=now.isoformat(),
            ),
            "unexpected source",
        ),
    )
    cases[2][0]["observation_source"] = "manual_edit"

    for receipt, expected_reason in cases:
        observed = qualify_memory_observation(
            receipt,
            expected_profile="pantheon-governed",
            observed_at=now,
        )
        assert observed["status"] == "not_qualified"
        assert expected_reason in observed["reason"]


def test_qualification_rejects_tampered_or_unsanitized_receipts() -> None:
    base = parse_memory_status(QUALIFIED_OUTPUT, profile="pantheon-governed")
    mutations = (
        ("command", ["hermes", "memory", "status"]),
        ("stdout_digest", "sha256:bad"),
        ("raw_output_retained", True),
        ("write_effect", True),
        ("authority_effect", "memory"),
        ("technical_receipt_is_evidence", True),
        ("captured_at", "not-a-date"),
    )

    for field, value in mutations:
        receipt = deepcopy(base)
        receipt[field] = value
        observed = qualify_memory_observation(
            receipt,
            expected_profile="pantheon-governed",
        )
        assert observed["status"] == "not_qualified", field
