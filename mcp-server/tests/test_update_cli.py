"""Read-only tests for the update verification CLI.

They run the entry point over fictional evidence and check the JSON output and
the exit code (0 only when the verdict is current). They fetch nothing, update
nothing and write nothing outside a temp file.
"""

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from pantheon_mcp import update_cli


def _run_with_file(payload: dict):
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "evidence.yaml"
        path.write_text(yaml.safe_dump(payload), encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = update_cli.run([str(path)])
    return code, json.loads(buf.getvalue())


class TestUpdateCli(unittest.TestCase):
    def test_current_evidence_exits_zero(self):
        code, report = _run_with_file(
            {"component": "hermes", "current_version": "1.5.0", "available_version": "1.5.0"}
        )
        self.assertEqual(code, 0, report)
        self.assertEqual(report["verdict"], "current", report)
        self.assertFalse(report["decides"])

    def test_update_available_exits_one(self):
        code, report = _run_with_file(
            {"current_version": "1.4.2", "available_version": "1.5.0"}
        )
        self.assertEqual(code, 1, report)
        self.assertEqual(report["verdict"], "update_available", report)

    def test_unknown_evidence_exits_one(self):
        code, report = _run_with_file({"component": "x"})
        self.assertEqual(code, 1, report)
        self.assertEqual(report["verdict"], "unknown", report)
        self.assertTrue(report["capability_gaps"])

    def test_missing_file_exits_one(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = update_cli.run(["/no/such/evidence.yaml"])
        self.assertEqual(code, 1)
        self.assertIn("cannot read evidence", buf.getvalue())

    def test_invalid_yaml_exits_one(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            path.write_text("a: b: c\n", encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = update_cli.run([str(path)])
        self.assertEqual(code, 1)
        self.assertIn("invalid YAML", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
