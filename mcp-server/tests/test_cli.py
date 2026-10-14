"""Read-only tests for the APU validation CLI.

They run the entry point over fictional dossiers and check the JSON output and
the exit code. They execute nothing and write nothing outside a temp file.
"""

import io
import json
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("PANTHEON_REPO_PATH", str(ROOT))

import yaml  # noqa: E402

from pantheon_mcp import cli  # noqa: E402

_CLEAN = {
    "program": {
        "program_id": "PRG-1",
        "program_type": "housing",
        "program_layer": "specific_requirement",
        "source_authority": "approved_client_decision",
        "proof_status": "accepted_as_support",
    }
}


def _run_with_file(payload: dict):
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "dossier.yaml"
        path.write_text(yaml.safe_dump(payload), encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cli.run([str(path)])
    return code, json.loads(buf.getvalue())


class TestApuCli(unittest.TestCase):
    def test_clean_dossier_exits_zero(self):
        code, report = _run_with_file(_CLEAN)
        self.assertEqual(code, 0, report)
        self.assertEqual(report["result"], "ok", report)
        self.assertEqual(report["gate"]["posture"], "candidate-only")

    def test_unknown_type_exits_one(self):
        code, report = _run_with_file({"not_a_real_type": {}})
        self.assertEqual(code, 1, report)
        self.assertEqual(report["result"], "error", report)

    def test_missing_file_exits_one(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cli.run(["/no/such/dossier.yaml"])
        self.assertEqual(code, 1)
        self.assertIn("cannot read dossier", buf.getvalue())

    def test_invalid_yaml_exits_one(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            path.write_text("a: b: c\n", encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = cli.run([str(path)])
        self.assertEqual(code, 1)
        self.assertIn("invalid YAML", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
