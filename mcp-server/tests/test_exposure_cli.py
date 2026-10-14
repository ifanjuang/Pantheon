"""Read-only tests for the exposure verification CLI.

They run the entry point over fictional evidence and check the JSON output and
the exit code (0 only when the verdict is guarded). They open no port, access no
NAS, send nothing and write nothing outside a temp file.
"""

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from pantheon_mcp import exposure_cli

_GUARDED = {
    "component": "runtime_client",
    "reach": "vpn",
    "auth": {"enforced": True},
    "scope": {"limited": True},
}


def _run_with_file(payload: dict):
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "evidence.yaml"
        path.write_text(yaml.safe_dump(payload), encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = exposure_cli.run([str(path)])
    return code, json.loads(buf.getvalue())


class TestExposureCli(unittest.TestCase):
    def test_guarded_evidence_exits_zero(self):
        code, report = _run_with_file(_GUARDED)
        self.assertEqual(code, 0, report)
        self.assertEqual(report["component"], "runtime_client")
        self.assertEqual(report["verdict"], "guarded", report)
        self.assertFalse(report["decides"])

    def test_exposed_evidence_exits_one(self):
        code, report = _run_with_file(dict(_GUARDED, reach="public", auth={"enforced": False}))
        self.assertEqual(code, 1, report)
        self.assertEqual(report["verdict"], "exposed", report)

    def test_unknown_evidence_exits_one(self):
        code, report = _run_with_file({"component": "x"})
        self.assertEqual(code, 1, report)
        self.assertEqual(report["verdict"], "unknown", report)
        self.assertTrue(report["capability_gaps"])

    def test_missing_file_exits_one(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = exposure_cli.run(["/no/such/evidence.yaml"])
        self.assertEqual(code, 1)
        self.assertIn("cannot read evidence", buf.getvalue())

    def test_invalid_yaml_exits_one(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            path.write_text("a: b: c\n", encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = exposure_cli.run([str(path)])
        self.assertEqual(code, 1)
        self.assertIn("invalid YAML", buf.getvalue())


if __name__ == "__main__":
    unittest.main()