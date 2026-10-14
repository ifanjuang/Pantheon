"""Read-only tests for the update-availability verification surface.

They classify fictional version evidence and check the verdict. They fetch
nothing, update nothing and write nothing.
"""

import unittest

from pantheon_mcp import update


class TestVerifyUpdate(unittest.TestCase):
    def test_current_when_versions_equal(self):
        report = update.verify_update(
            {"component": "hermes", "current_version": "1.5.0", "available_version": "1.5.0"}
        )
        self.assertEqual(report["result"], "ok", report)
        self.assertEqual(report["verdict"], "current", report)
        self.assertFalse(report["capability_gaps"], report["capability_gaps"])
        self.assertFalse(report["decides"])
        self.assertEqual(report["posture"], "read-only")

    def test_update_available_when_behind(self):
        report = update.verify_update(
            {"current_version": "1.4.2", "available_version": "1.5.0"}
        )
        self.assertEqual(report["verdict"], "update_available", report)

    def test_ahead_when_newer_than_available(self):
        report = update.verify_update(
            {"current_version": "2.0.0", "available_version": "1.9.9"}
        )
        self.assertEqual(report["verdict"], "ahead", report)

    def test_tolerates_v_prefix_and_prerelease(self):
        report = update.verify_update(
            {"current_version": "v1.5.0", "available_version": "1.5.0-beta"}
        )
        self.assertEqual(report["verdict"], "current", report)

    def test_shorter_version_padded(self):
        report = update.verify_update(
            {"current_version": "1.5", "available_version": "1.5.0"}
        )
        self.assertEqual(report["verdict"], "current", report)

    def test_unknown_with_gaps_when_missing(self):
        report = update.verify_update({"current_version": "1.0.0"})
        self.assertEqual(report["verdict"], "unknown", report)
        self.assertTrue(any("available" in g for g in report["capability_gaps"]))

    def test_unknown_when_unparseable(self):
        report = update.verify_update(
            {"current_version": "rolling", "available_version": "stable"}
        )
        # purely non-numeric versions cannot be compared -> unknown, with gaps
        self.assertEqual(report["verdict"], "unknown", report)
        self.assertTrue(
            any("not comparable" in g for g in report["capability_gaps"]), report
        )

    def test_non_mapping_is_error(self):
        report = update.verify_update("not a mapping")
        self.assertEqual(report["result"], "error", report)
        self.assertFalse(report["decides"])


if __name__ == "__main__":
    unittest.main()
