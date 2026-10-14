"""Read-only tests for the install / liveness verification surface.

They classify fictional install evidence and check the verdict. They probe
nothing, access no NAS, install nothing and write nothing.
"""

import unittest

from pantheon_mcp import install


def _green_evidence() -> dict:
    return {
        "component": "langfuse-hermes",
        "installed": True,
        "health": {"reachable": True, "status_code": 200, "latency_ms": 40},
        "checks": [
            {"name": "health", "status": "green"},
            {"name": "ready", "status": "green"},
        ],
        "expected_checks": ["health", "ready"],
    }


class TestVerifyInstall(unittest.TestCase):
    def test_green_when_installed_answers_and_checks_green(self):
        report = install.verify_install(_green_evidence())
        self.assertEqual(report["result"], "ok", report)
        self.assertEqual(report["verdict"], "green", report)
        self.assertTrue(report["installed"])
        self.assertTrue(report["answers"])
        self.assertTrue(report["checks_green"])
        self.assertFalse(report["capability_gaps"], report["capability_gaps"])
        self.assertFalse(report["decides"])
        self.assertEqual(report["posture"], "read-only")

    def test_degraded_when_unreachable(self):
        ev = _green_evidence()
        ev["health"] = {"reachable": False}
        report = install.verify_install(ev)
        self.assertEqual(report["verdict"], "degraded", report)
        self.assertFalse(report["answers"])

    def test_degraded_when_a_check_is_red(self):
        ev = _green_evidence()
        ev["checks"] = [
            {"name": "health", "status": "green"},
            {"name": "ready", "status": "red", "detail": "port closed"},
        ]
        report = install.verify_install(ev)
        self.assertEqual(report["verdict"], "degraded", report)
        self.assertFalse(report["checks_green"])
        self.assertTrue(any("ready" in g for g in report["capability_gaps"]))

    def test_absent_when_not_installed(self):
        report = install.verify_install({"component": "x", "installed": False})
        self.assertEqual(report["verdict"], "absent", report)
        self.assertFalse(report["installed"])

    def test_unknown_with_capability_gaps_when_evidence_insufficient(self):
        report = install.verify_install({"component": "x"})
        self.assertEqual(report["verdict"], "unknown", report)
        self.assertTrue(report["capability_gaps"], report)

    def test_health_without_reachable_is_unknown_with_gap(self):
        evidence = _green_evidence()
        evidence["health"] = {"status_code": 200}
        report = install.verify_install(evidence)
        self.assertEqual(report["verdict"], "unknown", report)
        self.assertIsNone(report["answers"])
        self.assertTrue(
            any("health.reachable" in gap for gap in report["capability_gaps"]),
            report,
        )

    def test_install_from_log_markers(self):
        report = install.verify_install(
            {
                "component": "x",
                "install_success_markers": ["bootstrap complete"],
                "logs": "starting...\nbootstrap complete\nlistening",
                "health": {"reachable": True, "status_code": 200},
                "checks": [{"name": "health", "status": "green"}],
            }
        )
        self.assertTrue(report["installed"])
        self.assertEqual(report["verdict"], "green", report)

    def test_non_mapping_is_error(self):
        report = install.verify_install("not a mapping")
        self.assertEqual(report["result"], "error", report)
        self.assertFalse(report["decides"])


if __name__ == "__main__":
    unittest.main()
