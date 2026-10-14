"""Adversarial type validation across direct, CLI and MCP evidence surfaces."""

from __future__ import annotations

import copy
import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import yaml

from pantheon_mcp import (
    backup,
    backup_cli,
    exposure,
    exposure_cli,
    install,
    install_cli,
    observability,
    observability_cli,
    server,
)


FAMILIES = {
    "install": {
        "verify": install.verify_install,
        "cli": install_cli.run,
        "mcp": server.verify_install,
        "positive": "green",
        "evidence": {
            "component": "x",
            "installed": True,
            "health": {"reachable": True, "status_code": 200},
            "checks": [{"name": "health", "status": "green"}],
        },
        "boolean_paths": [("installed",), ("health", "reachable")],
    },
    "backup": {
        "verify": backup.verify_backup,
        "cli": backup_cli.run,
        "mcp": server.verify_backup,
        "positive": "protected",
        "evidence": {
            "component": "x",
            "present": True,
            "freshness": {"last_backup_age_s": 1, "max_age_s": 10},
            "restore": {"verified": True},
        },
        "boolean_paths": [("present",), ("restore", "verified")],
    },
    "exposure": {
        "verify": exposure.verify_exposure,
        "cli": exposure_cli.run,
        "mcp": server.verify_exposure,
        "positive": "guarded",
        "evidence": {
            "component": "x",
            "reach": "vpn",
            "auth": {"enforced": True},
            "scope": {"limited": True},
        },
        "boolean_paths": [("auth", "enforced"), ("scope", "limited")],
    },
    "observability": {
        "verify": observability.verify_observability,
        "cli": observability_cli.run,
        "mcp": server.verify_observability,
        "positive": "observable",
        "evidence": {
            "component": "x",
            "signals": [{"name": "logs", "present": True}],
            "freshness": {"last_event_age_s": 1, "max_age_s": 10},
            "errors": {"count": 0, "threshold": 1},
        },
        "boolean_paths": [("signals", 0, "present")],
    },
}


def _with_value(evidence: dict, path: tuple, value) -> dict:
    result = copy.deepcopy(evidence)
    cursor = result
    for part in path[:-1]:
        cursor = cursor[part]
    cursor[path[-1]] = value
    return result


def _run_cli(run, evidence: dict) -> tuple[int, dict]:
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "evidence.yaml"
        path.write_text(yaml.safe_dump(evidence), encoding="utf-8")
        output = io.StringIO()
        with redirect_stdout(output):
            code = run([str(path)])
    return code, json.loads(output.getvalue())


class TestStrictEvidenceTypes(unittest.TestCase):
    def assert_invalid(self, report: dict, positive: str) -> None:
        self.assertEqual(report["result"], "error", report)
        self.assertEqual(report["verdict"], "invalid", report)
        self.assertNotEqual(report["verdict"], positive, report)
        self.assertTrue(report["problems"], report)
        self.assertFalse(report["decides"], report)

    def test_direct_verifiers_reject_every_non_boolean_shape(self):
        invalid_values = ("false", 0, None, [], {})
        for family, case in FAMILIES.items():
            for path in case["boolean_paths"]:
                for invalid in invalid_values:
                    with self.subTest(family=family, path=path, invalid=invalid):
                        evidence = _with_value(case["evidence"], path, invalid)
                        report = case["verify"](evidence)
                        self.assert_invalid(report, case["positive"])

    def test_real_false_is_valid_not_coerced(self):
        for family, case in FAMILIES.items():
            for path in case["boolean_paths"]:
                with self.subTest(family=family, path=path):
                    evidence = _with_value(case["evidence"], path, False)
                    report = case["verify"](evidence)
                    self.assertEqual(report["result"], "ok", report)
                    self.assertNotEqual(report["verdict"], case["positive"], report)

    def test_cli_surfaces_reject_string_false(self):
        for family, case in FAMILIES.items():
            path = case["boolean_paths"][0]
            evidence = _with_value(case["evidence"], path, "false")
            with self.subTest(family=family):
                code, report = _run_cli(case["cli"], evidence)
                self.assertEqual(code, 1, report)
                self.assert_invalid(report, case["positive"])

    def test_mcp_surfaces_reject_string_false(self):
        for family, case in FAMILIES.items():
            path = case["boolean_paths"][0]
            evidence = _with_value(case["evidence"], path, "false")
            with self.subTest(family=family):
                report = json.loads(case["mcp"](yaml.safe_dump(evidence)))
                self.assert_invalid(report, case["positive"])

    def test_missing_schema_fails_closed(self):
        with TemporaryDirectory() as tmp:
            with patch(
                "pantheon_mcp.evidence_validation.find_repo_root",
                return_value=Path(tmp),
            ):
                report = install.verify_install(FAMILIES["install"]["evidence"])
        self.assert_invalid(report, FAMILIES["install"]["positive"])
        self.assertIn("schema unavailable", report["problems"][0])


if __name__ == "__main__":
    unittest.main()
