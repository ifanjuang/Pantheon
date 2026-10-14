"""Tests for Phase 5 candidate skeleton helpers.

These tests exercise pure functions only. They write nothing, send nothing,
approve nothing and promote no memory.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import yaml

MODULE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_DIR))

from pantheon_mcp import contracts, server  # noqa: E402

FORBIDDEN_STATUS_WORDS = (
    "approved",
    "validated truth",
    "authorized action",
    "safe to execute",
)


class TestContractSkeletons(unittest.TestCase):
    def test_task_contract_skeleton_is_candidate_only(self):
        result = contracts.prepare_task_contract_skeleton(
            {
                "intent": "Compare a contractor quote against the CCTP before answering.",
                "scope": {"scope_type": "dossier", "scope_id": "fixture"},
                "sources_expected": ["CCTP", "quote"],
            }
        )
        self.assertEqual(result["object"], "TASK_CONTRACT_CANDIDATE_SKELETON")
        self.assertIn(result["status"], result["allowed_status_terms"])
        self.assertTrue(result["review_required"])
        self.assertIn("forbidden_behaviors", result)
        text = json.dumps(result).lower()
        for word in FORBIDDEN_STATUS_WORDS:
            self.assertNotIn(word, text)

    def test_evidence_pack_skeleton_contains_review_slots(self):
        result = contracts.prepare_evidence_pack_skeleton(
            {
                "intent": "Validate a consequential claim only after evidence review.",
                "professional_position": True,
                "scope": {"scope_type": "project", "scope_id": "fixture"},
                "sources_expected": ["D1", "D2"],
                "contradictions_to_resolve": ["D1 vs D2"],
            }
        )
        self.assertEqual(result["object"], "EVIDENCE_PACK_CANDIDATE_SKELETON")
        self.assertIn("D1", result["sources_expected"])
        self.assertIn("contradictions_to_resolve", result)
        self.assertIn("claims_to_support", result)
        self.assertTrue(result["review_required"])
        self.assertEqual(result["classification"]["consequence_level"], "K4")
        self.assertEqual(result["classification"]["approval_ceiling"], "C4")

    def test_server_tools_return_json_candidates(self):
        raw = yaml.safe_dump(
            {
                "intent": "Prepare candidate evidence for a client-facing issue.",
                "professional_position": True,
                "scope": {"scope_type": "dossier", "scope_id": "fixture"},
            },
            sort_keys=False,
        )
        task = json.loads(server.prepare_task_contract_skeleton(raw))
        evidence = json.loads(server.prepare_evidence_pack_skeleton(raw))
        self.assertEqual(task["object"], "TASK_CONTRACT_CANDIDATE_SKELETON")
        self.assertEqual(evidence["object"], "EVIDENCE_PACK_CANDIDATE_SKELETON")
        self.assertEqual(task["classification"]["approval_ceiling"], "C4")

    def test_invalid_yaml_is_reported(self):
        report = json.loads(server.prepare_task_contract_skeleton("intent: ["))
        self.assertEqual(report["result"], "error")
        self.assertIn("invalid YAML", report["problems"][0])

    def test_server_consultation_tools_return_shared_contract(self):
        catalog = json.loads(server.get_consultation_catalog())
        explanation = json.loads(server.explain_architecture("memvid"))
        status = json.loads(
            server.get_capability_status(
                yaml.safe_dump(
                    {
                        "capability_id": "memvid",
                        "producer": "hermes_dashboard",
                        "listed": True,
                        "detected": True,
                        "installed": True,
                        "configured": None,
                        "enabled": False,
                        "reachable": None,
                        "health": "unknown",
                        "update_status": "unknown",
                        "rollback_status": "unknown",
                        "governance_status": "candidate",
                        "task_use_status": "not_established",
                    },
                    sort_keys=False,
                )
            )
        )

        self.assertEqual(catalog["contract"], "pantheon.consultation.v1")
        self.assertEqual(explanation["topic"], "knowledge")
        self.assertEqual(status["source_mode"], "provided_status_candidate")
        self.assertFalse(status["runtime_probe_performed"])
        self.assertEqual(status["authorization_effect"], "none")


if __name__ == "__main__":
    unittest.main()
