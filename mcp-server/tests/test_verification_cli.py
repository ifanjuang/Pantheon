"""Contract tests for the shared read-only verification CLI."""

from __future__ import annotations

import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from contextlib import redirect_stdout

import yaml

from pantheon_mcp import (
    backup_cli,
    exposure_cli,
    install_cli,
    observability_cli,
    update,
    update_cli,
    verification_cli,
)


CASES = {
    "install": {
        "success": "green",
        "legacy": install_cli.run,
        "evidence": {
            "component": "x",
            "installed": True,
            "health": {"reachable": True, "status_code": 200},
            "checks": [{"name": "health", "status": "green"}],
        },
    },
    "observability": {
        "success": "observable",
        "legacy": observability_cli.run,
        "evidence": {
            "component": "x",
            "signals": [{"name": "logs", "present": True}],
            "freshness": {"last_event_age_s": 1, "max_age_s": 10},
            "errors": {"count": 0, "threshold": 1},
        },
    },
    "backup": {
        "success": "protected",
        "legacy": backup_cli.run,
        "evidence": {
            "component": "x",
            "present": True,
            "freshness": {"last_backup_age_s": 1, "max_age_s": 10},
            "restore": {"verified": True},
        },
    },
    "exposure": {
        "success": "guarded",
        "legacy": exposure_cli.run,
        "evidence": {
            "component": "x",
            "reach": "vpn",
            "auth": {"enforced": True},
            "scope": {"limited": True},
        },
    },
    "update": {
        "success": "current",
        "legacy": update_cli.run,
        "evidence": {
            "component": "x",
            "current_version": "1.2.3",
            "available_version": "v1.2.3",
            "channel": "stable",
        },
    },
}


def _invoke(run, argv: list[str]) -> tuple[int, dict]:
    output = io.StringIO()
    with redirect_stdout(output):
        code = run(argv)
    return code, json.loads(output.getvalue())


def _evidence_file(tmp: str, evidence: dict) -> str:
    path = Path(tmp) / "evidence.yaml"
    path.write_text(yaml.safe_dump(evidence), encoding="utf-8")
    return str(path)


class TestVerificationCli(unittest.TestCase):
    def test_static_registry_covers_exactly_five_explicit_verifiers(self):
        self.assertEqual(
            tuple(verification_cli.VERIFIERS),
            ("install", "observability", "backup", "exposure", "update"),
        )
        self.assertEqual(
            {name: spec.success_verdict for name, spec in verification_cli.VERIFIERS.items()},
            {name: case["success"] for name, case in CASES.items()},
        )

    def test_unified_cli_returns_zero_only_for_each_positive_verdict(self):
        for kind, case in CASES.items():
            with self.subTest(kind=kind), TemporaryDirectory() as tmp:
                path = _evidence_file(tmp, case["evidence"])
                code, report = _invoke(verification_cli.run, [kind, path])
                self.assertEqual(code, 0, report)
                self.assertEqual(report["verdict"], case["success"], report)
                self.assertEqual(report["posture"], "read-only", report)
                self.assertFalse(report["decides"], report)

    def test_legacy_commands_keep_the_same_report_and_exit_code(self):
        for kind, case in CASES.items():
            with self.subTest(kind=kind), TemporaryDirectory() as tmp:
                path = _evidence_file(tmp, case["evidence"])
                generic = _invoke(verification_cli.run, [kind, path])
                legacy = _invoke(case["legacy"], [path])
                self.assertEqual(legacy, generic)

    def test_invalid_yaml_uses_the_common_non_positive_envelope(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            path.write_text("key: [", encoding="utf-8")
            code, report = _invoke(verification_cli.run, ["install", str(path)])
        self.assertEqual(code, 1)
        self.assertEqual(report["result"], "error")
        self.assertEqual(report["verdict"], "invalid")
        self.assertEqual(report["capability_gaps"], [])
        self.assertFalse(report["decides"])

    def test_update_evidence_now_uses_strict_schema_validation(self):
        report = update.verify_update(
            {
                "component": "x",
                "current_version": 123,
                "available_version": "1.2.3",
                "unexpected": True,
            }
        )
        self.assertEqual(report["result"], "error", report)
        self.assertEqual(report["verdict"], "invalid", report)
        self.assertTrue(report["problems"], report)
        self.assertFalse(report["decides"], report)


if __name__ == "__main__":
    unittest.main()
