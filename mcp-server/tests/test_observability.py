"""Read-only tests for the observability verification surface.

They classify fictional observability evidence and check the verdict. They query
nothing, access no NAS and write nothing.
"""

import unittest

from pantheon_mcp import observability


def _observable_evidence() -> dict:
    return {
        "component": "hermes",
        "signals": [
            {"name": "logs", "present": True},
            {"name": "metrics", "present": True},
        ],
        "expected_signals": ["logs", "metrics"],
        "freshness": {"last_event_age_s": 12, "max_age_s": 60},
        "errors": {"count": 0, "threshold": 5},
    }


class TestVerifyObservability(unittest.TestCase):
    def test_observable_when_present_fresh_and_errors_ok(self):
        report = observability.verify_observability(_observable_evidence())
        self.assertEqual(report["result"], "ok", report)
        self.assertEqual(report["verdict"], "observable", report)
        self.assertTrue(report["signals_present"])
        self.assertTrue(report["fresh"])
        self.assertTrue(report["errors_ok"])
        self.assertFalse(report["capability_gaps"], report["capability_gaps"])
        self.assertFalse(report["decides"])
        self.assertEqual(report["posture"], "read-only")

    def test_blind_when_no_signal_present(self):
        ev = _observable_evidence()
        ev["signals"] = [
            {"name": "logs", "present": False},
            {"name": "metrics", "present": False},
        ]
        report = observability.verify_observability(ev)
        self.assertEqual(report["verdict"], "blind", report)
        self.assertFalse(report["has_signal"])

    def test_degraded_when_expected_signal_absent(self):
        ev = _observable_evidence()
        ev["signals"] = [
            {"name": "logs", "present": True},
            {"name": "metrics", "present": False},
        ]
        report = observability.verify_observability(ev)
        self.assertEqual(report["verdict"], "degraded", report)
        self.assertFalse(report["signals_present"])
        self.assertTrue(any("metrics" in g for g in report["capability_gaps"]))

    def test_degraded_when_stale(self):
        ev = _observable_evidence()
        ev["freshness"] = {"last_event_age_s": 600, "max_age_s": 60}
        report = observability.verify_observability(ev)
        self.assertEqual(report["verdict"], "degraded", report)
        self.assertFalse(report["fresh"])

    def test_degraded_when_errors_over_threshold(self):
        ev = _observable_evidence()
        ev["errors"] = {"count": 12, "threshold": 5}
        report = observability.verify_observability(ev)
        self.assertEqual(report["verdict"], "degraded", report)
        self.assertFalse(report["errors_ok"])

    def test_unknown_with_gaps_when_insufficient(self):
        report = observability.verify_observability({"component": "x"})
        self.assertEqual(report["verdict"], "unknown", report)
        self.assertTrue(report["capability_gaps"], report)

    def test_unknown_when_present_but_freshness_and_errors_missing(self):
        report = observability.verify_observability(
            {
                "component": "x",
                "signals": [{"name": "logs", "present": True}],
                "expected_signals": ["logs"],
            }
        )
        self.assertEqual(report["verdict"], "unknown", report)
        self.assertTrue(report["signals_present"])

    def test_non_mapping_is_error(self):
        report = observability.verify_observability("not a mapping")
        self.assertEqual(report["result"], "error", report)
        self.assertFalse(report["decides"])


if __name__ == "__main__":
    unittest.main()
