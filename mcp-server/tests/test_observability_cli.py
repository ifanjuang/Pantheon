"""Read-only tests for the observability verification CLI.

They run the entry point over fictional evidence and check the JSON output and
the exit code (0 only when the verdict is observable). They query nothing, access
no NAS and write nothing outside a temp file.
"""

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from pantheon_mcp import observability_cli

_OBSERVABLE = {
    "component": "hermes",
    "signals": [
        {"name": "logs", "present": True},
        {"name": "metrics", "present": True},
    ],
    "expected_signals": ["logs", "metrics"],
    "freshness": {"last_event_age_s": 12, "max_age_s": 60},
    "errors": {"count": 0, "threshold": 5},
}


def _run_with_file(payload: dict):
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "evidence.yaml"
        path.write_text(yaml.safe_dump(payload), encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = observability_cli.run([str(path)])
    return code, json.loads(buf.getvalue())


class TestObservabilityCli(unittest.TestCase):
    def test_observable_evidence_exits_zero(self):
        code, report = _run_with_file(_OBSERVABLE)
        self.assertEqual(code, 0, report)
        self.assertEqual(report["verdict"], "observable", report)
        self.assertFalse(report["decides"])

    def test_blind_evidence_exits_one(self):
        payload = dict(
            _OBSERVABLE,
            signals=[{"name": "logs", "present": False}, {"name": "metrics", "present": False}],
        )
        code, report = _run_with_file(payload)
        self.assertEqual(code, 1, report)
        self.assertEqual(report["verdict"], "blind", report)

    def test_unknown_evidence_exits_one(self):
        code, report = _run_with_file({"component": "x"})
        self.assertEqual(code, 1, report)
        self.assertEqual(report["verdict"], "unknown", report)
        self.assertTrue(report["capability_gaps"])

    def test_missing_file_exits_one(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = observability_cli.run(["/no/such/evidence.yaml"])
        self.assertEqual(code, 1)
        self.assertIn("cannot read evidence", buf.getvalue())

    def test_invalid_yaml_exits_one(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            path.write_text("a: b: c\n", encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = observability_cli.run([str(path)])
        self.assertEqual(code, 1)
        self.assertIn("invalid YAML", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
