"""Read-only tests for the backup verification CLI.

They run the entry point over fictional evidence and check the JSON output and
the exit code (0 only when the verdict is protected). They run no backup or
restore, access no NAS and write nothing outside a temp file.
"""

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from pantheon_mcp import backup_cli

_PROTECTED = {
    "component": "registre-probatoire",
    "present": True,
    "freshness": {"last_backup_age_s": 3600, "max_age_s": 86400},
    "restore": {"verified": True},
}


def _run_with_file(payload: dict):
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "evidence.yaml"
        path.write_text(yaml.safe_dump(payload), encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = backup_cli.run([str(path)])
    return code, json.loads(buf.getvalue())


class TestBackupCli(unittest.TestCase):
    def test_protected_evidence_exits_zero(self):
        code, report = _run_with_file(_PROTECTED)
        self.assertEqual(code, 0, report)
        self.assertEqual(report["verdict"], "protected", report)
        self.assertFalse(report["decides"])

    def test_unprotected_evidence_exits_one(self):
        code, report = _run_with_file(dict(_PROTECTED, present=False))
        self.assertEqual(code, 1, report)
        self.assertEqual(report["verdict"], "unprotected", report)

    def test_unknown_evidence_exits_one(self):
        code, report = _run_with_file({"component": "x"})
        self.assertEqual(code, 1, report)
        self.assertEqual(report["verdict"], "unknown", report)
        self.assertTrue(report["capability_gaps"])

    def test_missing_file_exits_one(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = backup_cli.run(["/no/such/evidence.yaml"])
        self.assertEqual(code, 1)
        self.assertIn("cannot read evidence", buf.getvalue())

    def test_invalid_yaml_exits_one(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            path.write_text("a: b: c\n", encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = backup_cli.run([str(path)])
        self.assertEqual(code, 1)
        self.assertIn("invalid YAML", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
