"""Read-only consultation-contract tests.

The tests exercise transport-neutral logic only.  No runtime probe, network
request, state write, authorization or knowledge retrieval is performed.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

MODULE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = MODULE_DIR.parent
sys.path.insert(0, str(MODULE_DIR))

from pantheon_mcp import consultation, source_map  # noqa: E402


class TestConsultationCatalog(unittest.TestCase):
    def test_catalog_is_honest_about_implemented_and_future_surfaces(self):
        report = consultation.consultation_catalog()
        by_id = {item["id"]: item for item in report["surfaces"]}

        self.assertEqual(report["contract"], "pantheon.consultation.v1")
        self.assertEqual(
            report["repository_version"],
            (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        )
        self.assertEqual(
            by_id["architecture_explanations"]["status"],
            "implemented_read_only",
        )
        self.assertEqual(
            by_id["capability_status_qualification"]["status"],
            "implemented_read_only_partial",
        )
        self.assertEqual(
            by_id["runtime_inventory"]["status"],
            "implemented_external_read_only_partial",
        )
        self.assertIn("MCP does not inventory", by_id["runtime_inventory"]["limitation"])
        self.assertEqual(
            by_id["http_consultation_api"]["status"],
            "documented_non_implemented",
        )
        self.assertEqual(
            by_id["knowledge_and_document_retrieval"]["status"],
            "documented_non_implemented",
        )
        self.assertNotIn("openwebui", report["known_architecture_topics"])
        self.assertIn("hermes-client", report["known_architecture_topics"])
        self.assertIn("pantheon-cockpit", report["known_architecture_topics"])
        self.assertFalse(report["write_effect"])


class TestArchitectureExplanation(unittest.TestCase):
    def test_memvid_alias_resolves_to_knowledge_with_sources(self):
        report = consultation.explain_architecture("Memvid")

        self.assertEqual(report["result"], "explained")
        self.assertEqual(report["topic"], "knowledge")
        self.assertGreaterEqual(len(report["sources"]), 2)
        self.assertTrue(all(source["exists"] for source in report["sources"]))
        self.assertEqual(report["authority_effect"], "none")

    def test_dashboard_reports_preview_and_external_plugin_posture(self):
        report = consultation.explain_architecture("dashboard")

        self.assertEqual(report["topic"], "pantheon-control")
        self.assertIn("static public preview", report["placement"])
        self.assertIn("external Hermes dashboard-plugin", report["placement"])
        self.assertIn("auto-install", report["must_not"])

    def test_cockpit_resolves_to_governed_pantheon_projection(self):
        report = consultation.explain_architecture("cockpit")

        self.assertEqual(report["result"], "explained")
        self.assertEqual(report["topic"], "pantheon-cockpit")
        self.assertIn("governed projection", report["placement"])
        self.assertTrue(
            any(
                "second general-purpose chat frontend" in item
                for item in report["must_not"]
            )
        )
        self.assertTrue(all(source["exists"] for source in report["sources"]))

    def test_hermes_web_resolves_to_replaceable_runtime_client(self):
        report = consultation.explain_architecture("hermes-web")

        self.assertEqual(report["result"], "explained")
        self.assertEqual(report["topic"], "hermes-client")
        self.assertIn("replaceable", report["placement"])
        self.assertTrue(
            any("governance authority" in item for item in report["must_not"])
        )

    def test_retired_openwebui_is_not_an_active_architecture_topic(self):
        report = consultation.explain_architecture("openwebui")

        self.assertEqual(report["result"], "unknown_topic")
        self.assertNotIn("openwebui", report["known_topics"])

    def test_indexed_source_keeps_its_declared_status_header(self):
        report = consultation.explain_architecture("pantheon")
        architecture = next(
            source
            for source in report["sources"]
            if source["source_file"] == "docs/governance/ARCHITECTURE.md"
        )

        self.assertEqual(architecture["authority"], "active doctrine")
        self.assertIn("active doctrine", architecture["declared_status"])
        self.assertEqual(len(architecture["content_sha256"]), 64)

    def test_unknown_topic_does_not_trigger_free_path_read(self):
        report = consultation.explain_architecture("../../etc/passwd")

        self.assertEqual(report["result"], "unknown_topic")
        self.assertIn("No free-path", report["limits"][0])

    def test_structure_projection_has_no_openwebui_owner(self):
        report = source_map.explain_structure()

        self.assertNotIn("openwebui-integration", source_map.SOURCES)
        self.assertNotIn("OpenWebUI", str(report["boundary"]))
        self.assertIn("Hermes Web/dashboard", report["boundary"]["interaction"])
        self.assertIn("Pantheon Cockpit", report["boundary"]["projection"])


class TestCapabilityStatusQualification(unittest.TestCase):
    def test_live_hermes_observation_stays_unapproved_and_unsupported(self):
        report = consultation.qualify_capability_status(
            {
                "capability_id": "mem0",
                "producer": "hermes_dashboard",
                "listed": True,
                "detected": True,
                "installed": True,
                "configured": True,
                "enabled": True,
                "reachable": True,
                "health": "healthy",
                "update_status": "update_available",
                "rollback_status": "available",
                "governance_status": "candidate",
                "task_use_status": "not_established",
            }
        )

        self.assertEqual(report["result"], "qualified_candidate")
        self.assertIn("installed != approved", report["warnings"])
        self.assertIn("healthy != safe", report["warnings"])
        self.assertIn(
            "update_available != update_authorized",
            report["warnings"],
        )
        self.assertTrue(
            any("no evidence_refs" in gap for gap in report["capability_gaps"])
        )
        self.assertFalse(report["runtime_probe_performed"])
        self.assertEqual(report["authorization_effect"], "none")

    def test_complete_status_preserves_dashboard_and_governance_axes(self):
        candidate = {
            "capability_id": "document-retrieval",
            "producer": "hermes_dashboard",
            "listed": True,
            "detected": True,
            "installed": True,
            "configured": True,
            "enabled": True,
            "reachable": True,
            "health": "healthy",
            "update_status": "up_to_date",
            "rollback_status": "tested",
            "governance_status": "approved_for_project",
            "task_use_status": "eligible_under_reviewed_contract",
            "observed_at": "2026-07-15T21:00:00+02:00",
            "scope": {"scope_type": "project", "scope_id": "example-project"},
            "evidence_refs": ["evidence-pack.example"],
        }
        report = consultation.qualify_capability_status(candidate)

        self.assertEqual(report["result"], "qualified_candidate")
        self.assertTrue(report["observed"]["enabled"])
        self.assertEqual(
            report["observed"]["governance_status"],
            "approved_for_project",
        )
        self.assertEqual(report["capability_gaps"], [])
        self.assertEqual(
            report["use_posture"],
            "requires_task_preflight_and_any_applicable_human_decision",
        )

        scope_mismatch = consultation.qualify_capability_status(
            {
                **candidate,
                "task_use_status": "requires_approval",
            }
        )
        self.assertIn(
            "governance_eligible != task_authorized",
            scope_mismatch["warnings"],
        )

    def test_impossible_runtime_combinations_fail_closed(self):
        report = consultation.qualify_capability_status(
            {
                "capability_id": "broken-observation",
                "producer": "hermes_dashboard",
                "listed": True,
                "detected": False,
                "installed": True,
                "configured": False,
                "enabled": True,
                "reachable": True,
                "health": "unknown",
                "update_status": "unknown",
                "rollback_status": "unknown",
                "governance_status": "candidate",
                "task_use_status": "not_established",
            }
        )

        self.assertEqual(report["result"], "invalid")
        self.assertTrue(any("installed" in item for item in report["problems"]))
        self.assertTrue(any("configured" in item for item in report["problems"]))
        self.assertTrue(any("reachable" in item for item in report["problems"]))

    def test_invalid_vocabulary_fails_closed(self):
        report = consultation.qualify_capability_status(
            {
                "capability_id": "mem0",
                "listed": "yes",
                "health": ["healthy"],
                "evidence_refs": "not-a-list",
            }
        )

        self.assertEqual(report["result"], "invalid")
        self.assertTrue(any("listed" in item for item in report["problems"]))
        self.assertTrue(any("health" in item for item in report["problems"]))
        self.assertTrue(any("evidence_refs" in item for item in report["problems"]))


class TestEffectiveAuthorityIndex(unittest.TestCase):
    def test_registered_subindex_rows_are_loaded(self):
        info = source_map.describe_source("capability-registry")

        self.assertEqual(info["authority"], "candidate / to verify")
        self.assertEqual(info["status"], "documented non-implemented")


class TestHermesCandidateConfiguration(unittest.TestCase):
    def test_native_allowlist_exposes_only_bounded_read_only_tools(self):
        template = yaml.safe_load(
            (
                REPO_ROOT
                / "templates/hermes/connection/pantheon_policy_mcp.template.yaml"
            ).read_text(encoding="utf-8")
        )
        server = template["mcp_servers"]["pantheon-policy"]

        self.assertEqual(
            set(server["tools"]["include"]),
            {
                "route_governed_request",
                "read_doctrine",
                "explain_governance_structure",
                "get_consultation_catalog",
                "explain_architecture",
                "get_capability_status",
                "evaluate_preflight",
                "prepare_task_contract_skeleton",
                "prepare_evidence_pack_skeleton",
                "plan_context_pack",
                "validate_context_pack",
            },
        )
        self.assertTrue(
            {
                "classify_request",
                "find_relevant_sources",
                "list_sources",
            }.isdisjoint(server["tools"]["include"])
        )
        self.assertFalse(server["tools"]["resources"])
        self.assertFalse(server["sampling"]["enabled"])


if __name__ == "__main__":
    unittest.main()
