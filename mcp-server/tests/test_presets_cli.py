"""Read-only tests for the verification preset CLI.

They run the entry point over fictional presets and check the JSON output and the
exit code (0 when valid, 1 on errors). They run no verification and write nothing
outside a temp file.
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

from pantheon_mcp import presets_cli  # noqa: E402

_VALID = {
    "module_id": "hermes",
    "verifications": {"install": {"applies": True, "expected_checks": ["health"]}},
}


def _run_with_file(payload: dict):
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "preset.yaml"
        path.write_text(yaml.safe_dump(payload), encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = presets_cli.run([str(path)])
    return code, json.loads(buf.getvalue())


class TestPresetsCli(unittest.TestCase):
    def test_valid_preset_exits_zero(self):
        code, report = _run_with_file(_VALID)
        self.assertEqual(code, 0, report)
        self.assertEqual(report["result"], "ok", report)
        self.assertTrue(report["active"])

    def test_schema_error_exits_one(self):
        code, report = _run_with_file({"verifications": {"install": {"applies": True}}})
        self.assertEqual(code, 1, report)
        self.assertEqual(report["result"], "error", report)

    def test_missing_file_exits_one(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = presets_cli.run(["/no/such/preset.yaml"])
        self.assertEqual(code, 1)
        self.assertIn("cannot read preset", buf.getvalue())

    def test_invalid_yaml_exits_one(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            path.write_text("a: b: c\n", encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = presets_cli.run([str(path)])
        self.assertEqual(code, 1)
        self.assertIn("invalid YAML", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
