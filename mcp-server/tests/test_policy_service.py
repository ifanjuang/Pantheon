"""Tests for the transport-neutral Pantheon policy service."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = MODULE_DIR.parent
sys.path.insert(0, str(MODULE_DIR))

from pantheon_mcp import server  # noqa: E402
from pantheon_mcp.service import PantheonPolicyService, repository_commit  # noqa: E402


class TestPantheonPolicyService(unittest.TestCase):
    def setUp(self) -> None:
        self.service = PantheonPolicyService(REPO_ROOT)

    def test_catalog_reports_http_projection_as_partial_not_activated(self):
        report = self.service.consultation_catalog()
        by_id = {item["id"]: item for item in report["surfaces"]}
        http = by_id["http_consultation_api"]
        self.assertEqual(http["status"], "implemented_read_only_partial")
        self.assertIn("internal", http["interface"][0])
        self.assertIn("activation remain to verify", http["limitation"])
        self.assertEqual(report["authorization_effect"], "none")

    def test_service_source_catalog_has_envelope(self):
        report = self.service.list_sources()
        self.assertEqual(report["result"], "listed")
        self.assertGreater(len(report["sources"]), 10)
        self.assertEqual(report["operation"], "sources.list")
        self.assertFalse(report["write_effect"])

    def test_mcp_list_sources_keeps_historical_array_shape(self):
        report = json.loads(server.list_sources())
        self.assertIsInstance(report, list)
        self.assertGreater(len(report), 10)
        self.assertIn("source_file", report[0])

    def test_relevant_source_shortlist_is_compact_condition_driven_and_bounded(self):
        report = self.service.find_relevant_sources(
            {
                "conditions": ["source_required", "external_effect"],
                "terms": ["verification"],
                "limit": 3,
            }
        )

        self.assertEqual(report["result"], "shortlisted")
        self.assertLessEqual(len(report["candidates"]), 3)
        self.assertEqual(report["operation"], "sources.find_relevant")
        self.assertFalse(report["write_effect"])
        self.assertIn("answer-verification-gate", {item["key"] for item in report["candidates"]})
        for item in report["candidates"]:
            self.assertNotIn("body", item)
            self.assertNotIn("summary", item)
            self.assertNotIn("authority_diagnostics", item)
            self.assertTrue(item["matched_on"])

    def test_relevant_source_shortlist_does_not_guess_without_signals(self):
        report = self.service.find_relevant_sources({"limit": 99})

        self.assertEqual(report["result"], "no_match")
        self.assertEqual(report["limit"], 8)
        self.assertEqual(report["candidates"], [])
        self.assertIn("clarify", report["next_action"])

    def test_mcp_relevant_source_tool_uses_yaml_contract(self):
        report = json.loads(
            server.find_relevant_sources(
                "conditions:\n  - project_history_reuse\nlimit: 2\n"
            )
        )

        self.assertEqual(report["result"], "shortlisted")
        self.assertLessEqual(len(report["candidates"]), 2)
        self.assertIn("memory", {item["key"] for item in report["candidates"]})

    def test_governed_request_route_combines_classification_and_shortlist(self):
        report = self.service.route_governed_request(
            {
                "intent": "Prepare a source-dependent professional result",
                "conditions": ["source_required", "external_transmission"],
                "scope": {"scope_type": "project", "scope_id": "fixture"},
                "source_limit": 3,
            }
        )

        self.assertEqual(report["result"], "routed")
        self.assertEqual(report["operation"], "policy.request.route")
        self.assertEqual(report["classification"]["consequence_level"], "K4")
        self.assertLessEqual(len(report["source_route"]["candidates"]), 3)
        self.assertIn(
            "source-ingestion-retrieval",
            {item["key"] for item in report["source_route"]["candidates"]},
        )
        self.assertFalse(report["write_effect"])
        self.assertFalse(report["execution_effect"])
        self.assertIn("read_doctrine", report["next_action"])

    def test_mcp_governed_request_route_uses_one_yaml_contract(self):
        report = json.loads(
            server.route_governed_request(
                "intent: Reuse project history\n"
                "conditions:\n  - project_history_reuse\n"
                "source_limit: 2\n"
            )
        )

        self.assertEqual(report["result"], "routed")
        self.assertLessEqual(len(report["source_route"]["candidates"]), 2)
        self.assertIn(
            "memory", {item["key"] for item in report["source_route"]["candidates"]}
        )

    def test_mcp_governed_request_route_accepts_plain_text_alias(self):
        report = json.loads(
            server.route_governed_request(
                request_text="Reuse project history for a bounded professional answer"
            )
        )

        self.assertEqual(report["result"], "routed")
        self.assertIn("policy.request.route", report["operation"])
        self.assertTrue(report["classification"]["task_contract_required"])
        self.assertLessEqual(len(report["source_route"]["candidates"]), 3)

    def test_mcp_governed_request_route_rejects_empty_input_without_calling_policy(self):
        report = json.loads(server.route_governed_request())
        self.assertEqual(report["result"], "error")
        self.assertIn("required", report["problems"][0])

    def test_unknown_source_key_never_becomes_a_path(self):
        report = self.service.read_doctrine("../../etc/passwd")
        self.assertEqual(report["error"], "unknown source key")
        self.assertNotIn("body", report)

    def test_mcp_read_doctrine_accepts_deferred_runtime_input_key_alias(self):
        report = json.loads(server.read_doctrine(input_key="answer-verification-gate"))
        self.assertEqual(report["uri"], "pantheon://answer-verification-gate")
        self.assertIn("body", report)

    def test_preflight_rejects_insufficient_human_decision_level(self):
        report = self.service.evaluate_preflight(
            {
                "request": {
                    "intent": "Transmit a contractual professional position",
                    "external_effect": True,
                    "transmission_requested": True,
                    "scope": {"scope_type": "project", "scope_id": "fixture"},
                },
                "gate_signals": {
                    "task_contract_ref": "tc-fixture",
                    "evidence_pack_candidate_ref": "epc-fixture",
                    "human_decision_ref": "decision-fixture",
                    "human_decision_level": "C3",
                },
            }
        )
        self.assertEqual(
            report["policy_disposition"], "blocked_pending_human_decision"
        )
        self.assertIn(
            "human_decision_level_at_required_ceiling",
            report["missing_requirements"],
        )
        self.assertFalse(report["external_effect_allowed"])

    def test_direct_human_local_write_needs_decision_but_not_a_fake_task_contract(self):
        report = self.service.evaluate_preflight(
            {
                "request": {
                    "intent": "act_working_information",
                    "external_effect": False,
                    "writes_state": True,
                    "delegated_execution": False,
                    "transmission_requested": False,
                    "memory_promotion_requested": False,
                    "professional_position": False,
                    "financial_or_contractual_effect": False,
                    "scope": {"scope_type": "project", "scope_id": "fixture"},
                },
                "gate_signals": {
                    "human_decision_ref": "decision-fixture",
                    "human_decision_level": "C2",
                },
            }
        )
        self.assertEqual(report["classification"]["consequence_level"], "K3")
        self.assertFalse(report["classification"]["delegated_execution"])
        self.assertFalse(report["classification"]["task_contract_required"])
        self.assertFalse(report["classification"]["evidence_required"])
        self.assertTrue(report["classification"]["blocked_until_gate"])
        self.assertEqual(
            report["policy_disposition"], "eligible_with_gate_signals_unverified"
        )
        self.assertEqual(report["missing_requirements"], [])
        self.assertTrue(report["candidate_work_allowed"])
        self.assertFalse(report["external_effect_allowed"])
        self.assertFalse(report["canonical_effect_allowed"])

    def test_direct_human_write_without_decision_still_fails_closed(self):
        report = self.service.evaluate_preflight(
            {
                "request": {
                    "intent": "act_working_information",
                    "external_effect": False,
                    "writes_state": True,
                    "delegated_execution": False,
                    "scope": {"scope_type": "project", "scope_id": "fixture"},
                },
                "gate_signals": {},
            }
        )
        self.assertEqual(
            report["policy_disposition"], "blocked_pending_human_decision"
        )
        self.assertIn("human_decision_ref", report["missing_requirements"])
        self.assertFalse(report["candidate_work_allowed"])

    def test_repository_commit_is_read_without_shell_execution(self):
        commit = repository_commit(REPO_ROOT)
        self.assertNotEqual(commit, "unknown")
        self.assertGreaterEqual(len(commit), 7)


if __name__ == "__main__":
    unittest.main()
