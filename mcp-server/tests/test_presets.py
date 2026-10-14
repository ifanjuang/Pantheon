"""Read-only tests for the verification preset reader/projector.

They validate fictional presets and check the projected plan. They run no
verification, gather no evidence and write nothing.
"""

import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("PANTHEON_REPO_PATH", str(ROOT))

from pantheon_mcp import presets  # noqa: E402


def _preset() -> dict:
    return {
        "module_id": "hermes",
        "title": "Hermes verification preset",
        "verifications": {
            "install": {"applies": True, "expected_checks": ["health"]},
            "observability": {"applies": True, "freshness_max_age_s": 60},
            "backup": {"applies": False},
            "update": {"applies": True, "channel": "stable"},
        },
    }


class TestLoadVerificationPreset(unittest.TestCase):
    def test_valid_preset_projects_plan(self):
        report = presets.load_verification_preset(_preset())
        self.assertEqual(report["result"], "ok", report)
        names = [a["verification"] for a in report["active"]]
        self.assertEqual(names, ["install", "observability", "update"])  # known order, backup excluded
        self.assertIn("backup", report["inactive"])
        self.assertIn("exposure", report["inactive"])  # absent => inactive
        self.assertFalse(report["decides"])
        self.assertEqual(report["posture"], "read-only")

    def test_thresholds_and_evidence_fields_carried(self):
        report = presets.load_verification_preset(_preset())
        install = next(a for a in report["active"] if a["verification"] == "install")
        self.assertEqual(install["thresholds"], {"expected_checks": ["health"]})
        self.assertIn("expected_checks", install["evidence_fields"])
        self.assertIn("checks", install["evidence_fields"])

    def test_schema_error_when_unknown_verification(self):
        bad = _preset()
        bad["verifications"]["not_a_real_one"] = {"applies": True}
        report = presets.load_verification_preset(bad)
        self.assertEqual(report["result"], "error", report)
        self.assertTrue(report["problems"])

    def test_schema_error_when_module_id_missing(self):
        bad = {"verifications": {"install": {"applies": True}}}
        report = presets.load_verification_preset(bad)
        self.assertEqual(report["result"], "error", report)

    def test_gap_when_no_verification_applies(self):
        report = presets.load_verification_preset(
            {"module_id": "x", "verifications": {"install": {"applies": False}}}
        )
        self.assertEqual(report["result"], "ok", report)
        self.assertEqual(report["active"], [])
        self.assertTrue(report["capability_gaps"])

    def test_non_mapping_is_error(self):
        report = presets.load_verification_preset("not a mapping")
        self.assertEqual(report["result"], "error", report)
        self.assertFalse(report["decides"])


if __name__ == "__main__":
    unittest.main()
