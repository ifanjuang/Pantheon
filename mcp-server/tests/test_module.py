"""Read-only tests for the bounded mcp-server module.

These tests exercise the importable logic without the MCP SDK, plus the
refusal posture (Phase 7). They execute no workflow, write nothing and
promote nothing.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_DIR))

import yaml  # noqa: E402

from pantheon_mcp import doctor, passports, policy, source_map  # noqa: E402
from pantheon_mcp.repo import find_repo_root, read_repo_text  # noqa: E402

FIXTURES = MODULE_DIR / "fixtures"


class TestRepoAccess(unittest.TestCase):
    def test_repo_root_found(self):
        root = find_repo_root()
        self.assertTrue((root / "CLAUDE.md").is_file())

    def test_path_escape_rejected(self):
        with self.assertRaises(PermissionError):
            read_repo_text("../outside.txt")
        with self.assertRaises(PermissionError):
            read_repo_text("docs/../../etc/passwd")


class TestSourceMap(unittest.TestCase):
    def test_all_sources_described(self):
        infos = source_map.list_sources()
        self.assertEqual(len(infos), len(source_map.SOURCES))
        for info in infos:
            self.assertIn("authority", info)
            self.assertIn("status", info)
            self.assertIn("declared_status", info)
            self.assertIn("content_sha256", info)
            self.assertIn("exists", info)
            self.assertIn(
                info["authority_resolution"],
                {"resolved", "not_indexed"},
            )
            if info["authority_resolution"] == "resolved":
                self.assertTrue(info["authority_ok"])
                self.assertIsNotNone(info["authority_source"]["line"])
            else:
                self.assertFalse(info["authority_ok"])
                self.assertEqual(info["authority"], "not indexed")
                self.assertTrue(info["authority_diagnostics"])

    def test_glossary_readable_and_labeled(self):
        info = source_map.read_source("glossary")
        self.assertTrue(info["exists"])
        self.assertIn("E0", info["body"])
        self.assertNotEqual(info["authority"], "")

    def test_unknown_key_reported_not_invented(self):
        info = source_map.describe_source("does-not-exist")
        self.assertIn("error", info)

    def test_structure_explains_placement_without_granting_authority(self):
        guide = source_map.explain_structure("task-contracts")
        self.assertEqual(guide["boundary"]["execution"], "Hermes Agent executes")
        self.assertIn("grants no authority", guide["boundary"]["effect"])
        self.assertEqual(guide["focus"]["authority_resolution"], "resolved")
        self.assertEqual(len(guide["sections"]), 1)
        self.assertEqual(guide["sections"][0]["key"], "delegation-and-decision")

    def test_structure_unknown_key_is_explicit(self):
        guide = source_map.explain_structure("not-a-source")
        self.assertEqual(guide["error"], "unknown source key")


class TestPassports(unittest.TestCase):
    def _load(self, name: str) -> dict:
        return yaml.safe_load((FIXTURES / name).read_text(encoding="utf-8"))

    def test_valid_passport_passes_shape(self):
        report = passports.validate_passport(self._load("passport_valid.yaml"))
        self.assertTrue(report["valid"], report["problems"])
        self.assertEqual(report["governance_gaps"], [])
        self.assertTrue(report["ready_for_review"])

    def test_unsafe_passport_flagged(self):
        report = passports.validate_passport(self._load("passport_invalid.yaml"))
        gaps = " ".join(report["governance_gaps"])
        self.assertIn("approval_required >= C3", gaps)
        self.assertIn("user_decision_gate_required", gaps)
        self.assertIn("visible != admitted", gaps)
        self.assertIn("unknown", gaps)
        self.assertFalse(report.get("ready_for_review", False))

    def test_validation_is_not_authorization(self):
        report = passports.validate_passport(self._load("passport_valid.yaml"))
        self.assertIn("not authorization", report["authority_note"])


class TestPolicy(unittest.TestCase):
    def test_refusal_posture(self):
        for action in ("send email", "merge PR", "approve output",
                       "promote_memory", "install skill", "schedule job"):
            report = policy.classify_request({"perform": [action]})
            self.assertEqual(report["result"], "refused", action)

    def test_external_effect_is_k4_v4(self):
        report = policy.classify_request(
            {"intent": "send the revised plan to the contractor",
             "external_effect": True,
             "scope": {"scope_type": "dossier", "scope_id": "maison-lierre"}}
        )
        self.assertEqual(report["consequence_level"], "K4")
        self.assertEqual(report["required_verification"], "V4")
        self.assertTrue(report["blocked_until_gate"])
        self.assertTrue(report["task_contract_required"])
        self.assertTrue(report["evidence_required"])

    def test_unknown_external_effect_escalates(self):
        report = policy.classify_request(
            {"intent": "answer the client", "external_effect": "unknown"}
        )
        self.assertEqual(report["consequence_level"], "K4")

    def test_professional_trigger_is_k3(self):
        report = policy.classify_request(
            {"intent": "compare the CCTP requirement with the signed DPGF amount",
             "scope": {"scope_type": "dossier", "scope_id": "maison-lierre"}}
        )
        self.assertEqual(report["consequence_level"], "K3")
        self.assertTrue(report["evidence_required"])
        self.assertTrue(report["task_contract_required"])

    def test_direct_human_local_write_keeps_k3_without_fabricated_runtime_contract(self):
        report = policy.classify_request(
            {
                "intent": "act_working_information",
                "external_effect": False,
                "writes_state": True,
                "delegated_execution": False,
                "scope": {"scope_type": "project", "scope_id": "fixture"},
            }
        )
        self.assertEqual(report["consequence_level"], "K3")
        self.assertEqual(report["required_verification"], "V3")
        self.assertFalse(report["task_contract_required"])
        self.assertFalse(report["evidence_required"])
        self.assertTrue(report["blocked_until_gate"])
        self.assertIn(
            "User Decision Gate before direct human governed-state effect",
            report["required_gates"],
        )

    def test_direct_human_professional_assertion_still_requires_evidence(self):
        report = policy.classify_request(
            {
                "intent": "record project surface",
                "external_effect": False,
                "writes_state": True,
                "delegated_execution": False,
                "scope": {"scope_type": "project", "scope_id": "fixture"},
            }
        )
        self.assertEqual(report["consequence_level"], "K3")
        self.assertFalse(report["task_contract_required"])
        self.assertTrue(report["evidence_required"])
        self.assertTrue(report["blocked_until_gate"])

    def test_omitted_delegation_mode_fails_conservative(self):
        report = policy.classify_request(
            {
                "intent": "local_state_write",
                "external_effect": False,
                "writes_state": True,
                "scope": {"scope_type": "project", "scope_id": "fixture"},
            }
        )
        self.assertTrue(report["delegated_execution"])
        self.assertTrue(report["task_contract_required"])
        self.assertTrue(report["evidence_required"])

    def test_invalid_delegation_mode_is_refused(self):
        report = policy.classify_request(
            {"intent": "local_state_write", "delegated_execution": "false"}
        )
        self.assertEqual(report["result"], "refused")
        self.assertIn("must be a boolean", report["reason"])

    def test_missing_scope_flagged(self):
        report = policy.classify_request({"intent": "summarize the meeting notes"})
        self.assertTrue(any("scope missing" in g for g in report["required_gates"]))

    def test_external_action_blocked_by_default(self):
        report = policy.check_external_action("file the permit application")
        self.assertEqual(report["status"], "blocked_by_default")


class TestDoctor(unittest.TestCase):
    def test_doctor_runs_green_on_blocking_checks(self):
        report = doctor.run_all()
        blocking = [c for c in report["checks"] if not c.get("informational")]
        self.assertTrue(report["ok"], [c for c in blocking if not c["ok"]])

    def test_vocabulary_check_is_informational_worklist(self):
        report = doctor.check_retired_vocabulary()
        self.assertTrue(report["informational"])
        self.assertEqual(
            report["remaining_occurrences"], len(report["occurrences"])
        )


if __name__ == "__main__":
    unittest.main()
