"""Read-only tests for the install verification CLI.

They run the entry point over fictional evidence and check the JSON output and
the exit code (0 only when the verdict is green). They probe nothing, access no
NAS, install nothing and write nothing outside a temp file.
"""

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from pantheon_mcp import install_cli

_GREEN = {
    "component": "hermes",
    "installed": True,
    "health": {"reachable": True, "status_code": 200},
    "checks": [{"name": "health", "status": "green"}],
    "expected_checks": ["health"],
}


def _run_with_file(payload: dict):
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "evidence.yaml"
        path.write_text(yaml.safe_dump(payload), encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = install_cli.run([str(path)])
    return code, json.loads(buf.getvalue())


class TestInstallCli(unittest.TestCase):
    def test_green_evidence_exits_zero(self):
        code, report = _run_with_file(_GREEN)
        self.assertEqual(code, 0, report)
        self.assertEqual(report["verdict"], "green", report)
        self.assertFalse(report["decides"])

    def test_degraded_evidence_exits_one(self):
        payload = dict(_GREEN, health={"reachable": False})
        code, report = _run_with_file(payload)
        self.assertEqual(code, 1, report)
        self.assertEqual(report["verdict"], "degraded", report)

    def test_unknown_evidence_exits_one(self):
        code, report = _run_with_file({"component": "x"})
        self.assertEqual(code, 1, report)
        self.assertEqual(report["verdict"], "unknown", report)
        self.assertTrue(report["capability_gaps"])

    def test_missing_file_exits_one(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = install_cli.run(["/no/such/evidence.yaml"])
        self.assertEqual(code, 1)
        self.assertIn("cannot read evidence", buf.getvalue())

    def test_invalid_yaml_exits_one(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            path.write_text("a: b: c\n", encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = install_cli.run([str(path)])
        self.assertEqual(code, 1)
        self.assertIn("invalid YAML", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
