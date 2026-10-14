from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


IMPLEMENTATION = Path(__file__).resolve().parents[1]
ROOT = IMPLEMENTATION.parent
SCRIPT = IMPLEMENTATION / "tools" / "check_uhp_hermes_runtime_compatibility.py"
SPEC = importlib.util.spec_from_file_location("pantheon_uhp_runtime_compat", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

CompatibilityError = MODULE.CompatibilityError
build_report = MODULE.build_report
discover_harnessrouter_hermes_version = MODULE.discover_harnessrouter_hermes_version


def test_exact_harnessrouter_hermes_pin_is_discovered(tmp_path: Path) -> None:
    entrypoint = tmp_path / "entrypoint.sh"
    entrypoint.write_text(
        "pip install 'hermes-agent==9.8.7' anthropic\n",
        encoding="utf-8",
    )

    assert discover_harnessrouter_hermes_version(entrypoint) == "9.8.7"


def test_missing_or_ambiguous_harnessrouter_pin_fails_closed(tmp_path: Path) -> None:
    missing = tmp_path / "missing.sh"
    missing.write_text("echo no runtime pin\n", encoding="utf-8")
    with pytest.raises(CompatibilityError, match="no exact"):
        discover_harnessrouter_hermes_version(missing)

    ambiguous = tmp_path / "ambiguous.sh"
    ambiguous.write_text(
        "hermes-agent==1.2.3\nhermes-agent==4.5.6\n",
        encoding="utf-8",
    )
    with pytest.raises(CompatibilityError, match="multiple Hermes pins"):
        discover_harnessrouter_hermes_version(ambiguous)


def test_runtime_mismatch_blocks_matched_ab_without_rejecting_protocol() -> None:
    report = build_report(
        harnessrouter_version="7.0.0",
        harnessrouter_ref="a" * 40,
        protocol_version="2099-01-01",
        harnessrouter_hermes_version="1.0.0",
        pantheon_hermes_version="2.0.0",
        pantheon_hermes_ref="b" * 40,
    )

    assert report["status"] == "blocked_runtime_mismatch"
    assert report["exact_hermes_version_match"] is False
    assert report["matched_ab_allowed"] is False
    assert "Transport characterization may continue" in report["interpretation"]
    assert report["authority"]["adopts_transport"] is False
    assert report["authority"]["dispatches_task"] is False
    assert "protocol conformance != runtime comparability" in report["non_equivalences"]


def test_exact_runtime_match_only_opens_the_ab_gate() -> None:
    report = build_report(
        harnessrouter_version="7.0.0",
        harnessrouter_ref="a" * 40,
        protocol_version="2099-01-01",
        harnessrouter_hermes_version="2.0.0",
        pantheon_hermes_version="2.0.0",
        pantheon_hermes_ref="b" * 40,
    )

    assert report["status"] == "ready_for_matched_ab"
    assert report["matched_ab_allowed"] is True
    assert report["authority"] == {
        "installs_runtime": False,
        "activates_runtime": False,
        "dispatches_task": False,
        "authorizes_effect": False,
        "adopts_transport": False,
        "admits_evidence": False,
    }


def test_current_registry_exports_harnessrouter_without_second_pin_authority() -> None:
    from tools.export_external_qualification_pins import selected_exports

    values = selected_exports(["harnessrouter", "hermes-agent"])

    assert values["HARNESSROUTER_PIN_ID"] == "harnessrouter"
    assert values["HARNESSROUTER_REPOSITORY"] == "HarnessRouter/harnessrouter"
    assert values["HARNESSROUTER_RELEASE_TAG"].startswith("v")
    assert values["HARNESSROUTER_PROTOCOL_VERSION"]
    assert values["HERMES_PIN_ID"] == "hermes-agent"


def test_cli_require_match_fails_only_the_matched_ab_gate(
    tmp_path: Path,
    capsys,
) -> None:
    entrypoint = tmp_path / "entrypoint.sh"
    entrypoint.write_text("hermes-agent==1.0.0\n", encoding="utf-8")
    output = tmp_path / "report.json"

    rc = MODULE.main(
        [
            "--harnessrouter-entrypoint",
            str(entrypoint),
            "--harnessrouter-version",
            "7.0.0",
            "--harnessrouter-ref",
            "a" * 40,
            "--protocol-version",
            "2099-01-01",
            "--pantheon-hermes-version",
            "2.0.0",
            "--pantheon-hermes-ref",
            "b" * 40,
            "--output",
            str(output),
            "--require-match",
        ]
    )

    assert rc == 2
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["status"] == "blocked_runtime_mismatch"
    assert report["matched_ab_allowed"] is False
    capsys.readouterr()
