"""Read-only tests for the backup / recoverability verification surface.

They classify fictional backup evidence and check the verdict. They run no backup
or restore, access no NAS and write nothing.
"""

import unittest

from pantheon_mcp import backup


def _protected_evidence() -> dict:
    return {
        "component": "registre-probatoire",
        "present": True,
        "freshness": {"last_backup_age_s": 3600, "max_age_s": 86400},
        "restore": {"verified": True},
    }


class TestVerifyBackup(unittest.TestCase):
    def test_protected_when_present_recent_and_restore_verified(self):
        report = backup.verify_backup(_protected_evidence())
        self.assertEqual(report["result"], "ok", report)
        self.assertEqual(report["verdict"], "protected", report)
        self.assertTrue(report["present"])
        self.assertTrue(report["recent"])
        self.assertTrue(report["restore_verified"])
        self.assertFalse(report["capability_gaps"], report["capability_gaps"])
        self.assertFalse(report["decides"])
        self.assertEqual(report["posture"], "read-only")

    def test_unprotected_when_no_backup(self):
        report = backup.verify_backup({"component": "x", "present": False})
        self.assertEqual(report["verdict"], "unprotected", report)
        self.assertFalse(report["present"])

    def test_degraded_when_stale(self):
        ev = _protected_evidence()
        ev["freshness"] = {"last_backup_age_s": 999999, "max_age_s": 86400}
        report = backup.verify_backup(ev)
        self.assertEqual(report["verdict"], "degraded", report)
        self.assertFalse(report["recent"])

    def test_degraded_when_restore_not_demonstrated(self):
        ev = _protected_evidence()
        ev["restore"] = {"verified": False}
        report = backup.verify_backup(ev)
        self.assertEqual(report["verdict"], "degraded", report)
        self.assertFalse(report["restore_verified"])
        self.assertTrue(any("restore" in g for g in report["capability_gaps"]))

    def test_present_from_markers(self):
        report = backup.verify_backup(
            {
                "component": "x",
                "backup_markers": ["/snap/x-1"],
                "freshness": {"last_backup_age_s": 10, "max_age_s": 100},
                "restore": {"verified": True},
            }
        )
        self.assertTrue(report["present"])
        self.assertEqual(report["verdict"], "protected", report)

    def test_unknown_with_gaps_when_insufficient(self):
        report = backup.verify_backup({"component": "x"})
        self.assertEqual(report["verdict"], "unknown", report)
        self.assertTrue(report["capability_gaps"], report)

    def test_unknown_when_present_but_freshness_and_restore_missing(self):
        report = backup.verify_backup({"component": "x", "present": True})
        self.assertEqual(report["verdict"], "unknown", report)
        self.assertTrue(report["present"])

    def test_non_mapping_is_error(self):
        report = backup.verify_backup("not a mapping")
        self.assertEqual(report["result"], "error", report)
        self.assertFalse(report["decides"])


if __name__ == "__main__":
    unittest.main()
