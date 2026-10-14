"""Read-only tests for the exposure-surface verification surface.

They classify fictional exposure evidence and check the verdict. They open no
port, access no NAS, send nothing and write nothing.
"""

import unittest

from pantheon_mcp import exposure


def _guarded_evidence() -> dict:
    return {
        "component": "runtime_client",
        "reach": "vpn",
        "auth": {"enforced": True},
        "scope": {"limited": True},
    }


class TestVerifyExposure(unittest.TestCase):
    def test_guarded_when_contained_authenticated_and_scoped(self):
        report = exposure.verify_exposure(_guarded_evidence())
        self.assertEqual(report["result"], "ok", report)
        self.assertEqual(report["verdict"], "guarded", report)
        self.assertEqual(report["component"], "runtime_client")
        self.assertTrue(report["reach_contained"])
        self.assertTrue(report["authenticated"])
        self.assertTrue(report["scoped"])
        self.assertFalse(report["capability_gaps"], report["capability_gaps"])
        self.assertFalse(report["decides"])
        self.assertEqual(report["posture"], "read-only")

    def test_hermes_web_uses_same_generic_verification_contract(self):
        report = exposure.verify_exposure(
            {**_guarded_evidence(), "component": "hermes_web"}
        )
        self.assertEqual(report["verdict"], "guarded", report)
        self.assertEqual(report["component"], "hermes_web")
        self.assertFalse(report["decides"])

    def test_exposed_when_public_without_auth(self):
        ev = dict(_guarded_evidence(), reach="public", auth={"enforced": False})
        report = exposure.verify_exposure(ev)
        self.assertEqual(report["verdict"], "exposed", report)
        self.assertFalse(report["reach_contained"])
        self.assertTrue(any("without authentication" in g for g in report["capability_gaps"]))

    def test_degraded_when_public_but_protected(self):
        ev = dict(_guarded_evidence(), reach="public")
        report = exposure.verify_exposure(ev)
        self.assertEqual(report["verdict"], "degraded", report)
        self.assertFalse(report["reach_contained"])

    def test_degraded_when_contained_but_unauthenticated(self):
        ev = dict(_guarded_evidence(), auth={"enforced": False})
        report = exposure.verify_exposure(ev)
        self.assertEqual(report["verdict"], "degraded", report)
        self.assertFalse(report["authenticated"])

    def test_degraded_when_scope_open(self):
        ev = dict(_guarded_evidence(), scope={"limited": False})
        report = exposure.verify_exposure(ev)
        self.assertEqual(report["verdict"], "degraded", report)
        self.assertFalse(report["scoped"])

    def test_unknown_with_gaps_when_insufficient(self):
        report = exposure.verify_exposure({"component": "x"})
        self.assertEqual(report["verdict"], "unknown", report)
        self.assertTrue(report["capability_gaps"], report)

    def test_unknown_when_contained_but_auth_and_scope_missing(self):
        report = exposure.verify_exposure({"component": "x", "reach": "local"})
        self.assertEqual(report["verdict"], "unknown", report)
        self.assertTrue(report["reach_contained"])

    def test_non_mapping_is_error(self):
        report = exposure.verify_exposure("not a mapping")
        self.assertEqual(report["result"], "error", report)
        self.assertFalse(report["decides"])


if __name__ == "__main__":
    unittest.main()