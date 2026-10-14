"""Regression tests for progressive request handling.

These tests exercise policy projection only. No role is dispatched, no workflow
runs, and no external effect is authorized.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

MODULE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = MODULE_DIR.parent
sys.path.insert(0, str(MODULE_DIR))

from pantheon_mcp import policy, request_handling  # noqa: E402


SCOPE = {"scope_type": "task", "scope_id": "progressive-handling-test"}


class TestProgressiveRequestHandling(unittest.TestCase):
    def test_direct_harmless_rewrite_exits_at_k0_without_contract(self):
        report = policy.classify_request(
            {
                "intent": "Améliore ce message : merci de confirmer le rendez-vous de mardi.",
                "requested_transformation": "rewrite",
            }
        )

        self.assertEqual(report["consequence_level"], "K0")
        self.assertFalse(report["task_contract_required"])
        self.assertEqual(report["required_gates"], [])
        self.assertEqual(report["handling"]["disposition"], "PROCEED")
        self.assertEqual(report["handling"]["role_viewpoints"], [])
        self.assertNotIn("topology", report["handling"])
        self.assertIn(
            "preserve_claim_status_and_meaning",
            report["handling"]["constraints"],
        )

    def test_material_condition_prevents_k0_fast_exit(self):
        report = policy.classify_request(
            {
                "intent": "Reformuler ce texte après vérification de la source.",
                "requested_transformation": "rewrite",
                "scope": SCOPE,
                "conditions": ["source_required"],
            }
        )

        self.assertEqual(report["consequence_level"], "K2")
        self.assertTrue(report["task_contract_required"])
        self.assertEqual(report["handling"]["disposition"], "CONSULT")
        self.assertIn("ARGOS", report["handling"]["role_viewpoints"])

    def test_external_effect_condition_drives_k4_and_gate_without_legacy_flag(self):
        report = policy.classify_request(
            {
                "intent": "Préparer l'effet demandé.",
                "scope": SCOPE,
                "conditions": ["external_effect"],
            }
        )

        self.assertEqual(report["consequence_level"], "K4")
        self.assertEqual(report["required_approval_ceiling"], "C3")
        self.assertEqual(report["handling"]["disposition"], "GATE")
        self.assertTrue(report["handling"]["effect_gate"]["effect_requested_now"])

    def test_explicit_dependency_derives_sequential_handoff(self):
        report = policy.classify_request(
            {
                "intent": "Préparer une analyse engageante avec base sourcée.",
                "scope": SCOPE,
                "conditions": ["source_required", "legal_or_professional_risk"],
                "coordination": {
                    "requires": [["supporting_basis", "consequence_review"]],
                },
            }
        )

        self.assertEqual(report["consequence_level"], "K4")
        self.assertEqual(report["handling"]["disposition"], "CONSULT")
        self.assertEqual(report["handling"]["role_viewpoints"], ["ARGOS", "THEMIS"])
        self.assertEqual(
            report["handling"]["topology"]["suggested"],
            "sequential_handoff",
        )
        self.assertEqual(
            report["handling"]["coordination"]["requires"],
            [["supporting_basis", "consequence_review"]],
        )
        self.assertFalse(report["handling"]["effect_gate"]["effect_requested_now"])

    def test_independent_work_with_synthesis_derives_fanout(self):
        report = policy.classify_request(
            {
                "intent": "Comparer plusieurs états indépendants puis synthétiser.",
                "scope": SCOPE,
                "conditions": ["source_required", "project_history_reuse"],
                "coordination": {
                    "independent": [["source_state", "prior_state"]],
                    "synthesize": True,
                },
            }
        )

        self.assertEqual(report["handling"]["disposition"], "CONSULT")
        self.assertEqual(report["handling"]["role_viewpoints"], ["ARGOS", "MNEMOSYNE"])
        self.assertEqual(
            report["handling"]["topology"]["suggested"],
            "fanout_extract_then_single_synthesis",
        )

    def test_independent_work_without_synthesis_derives_parallel(self):
        report = policy.classify_request(
            {
                "intent": "Effectuer deux vérifications indépendantes.",
                "scope": SCOPE,
                "conditions": ["source_required", "delivery_quality_required"],
                "coordination": {
                    "independent": [["source_check", "delivery_check"]],
                },
            }
        )

        self.assertEqual(
            report["handling"]["topology"]["suggested"],
            "parallel_independent_workers",
        )

    def test_branch_relation_derives_existing_router_topology(self):
        report = policy.classify_request(
            {
                "intent": "Choisir la suite selon le résultat du contrôle.",
                "scope": SCOPE,
                "conditions": ["complex_task"],
                "coordination": {
                    "branch_on": ["verification_result"],
                },
            }
        )

        self.assertEqual(report["handling"]["disposition"], "CONSULT")
        self.assertEqual(report["handling"]["topology"]["suggested"], "router")
        self.assertEqual(
            report["handling"]["coordination"]["branch_on"],
            ["verification_result"],
        )

    def test_repeat_until_is_control_relation_not_new_topology(self):
        report = policy.classify_request(
            {
                "intent": "Réviser le candidat jusqu'à satisfaction du critère.",
                "scope": SCOPE,
                "conditions": ["delivery_quality_required"],
                "completion_requirements": ["acceptance_criteria_met"],
                "coordination": {
                    "repeat_until": ["acceptance_criteria_met"],
                },
            }
        )

        self.assertEqual(report["handling"]["disposition"], "CONSULT")
        self.assertNotIn("topology", report["handling"])
        self.assertEqual(
            report["handling"]["coordination"]["repeat_until"],
            ["acceptance_criteria_met"],
        )
        self.assertEqual(
            report["handling"]["completion_requirements"],
            ["acceptance_criteria_met"],
        )

    def test_explicit_completion_requirements_override_generic_fallback(self):
        report = policy.classify_request(
            {
                "intent": "Examiner une source selon un critère propre à la tâche.",
                "scope": SCOPE,
                "conditions": ["source_required"],
                "completion_requirements": ["requested_fact_resolved"],
            }
        )

        self.assertEqual(
            report["handling"]["completion_requirements"],
            ["requested_fact_resolved"],
        )

    def test_current_and_target_state_are_projection_only(self):
        report = policy.classify_request(
            {
                "intent": "Faire progresser le candidat.",
                "scope": SCOPE,
                "conditions": ["complex_task"],
                "current_state": "draft",
                "target_state": "reviewable_candidate",
            }
        )

        self.assertEqual(report["handling"]["current_state"], "draft")
        self.assertEqual(report["handling"]["target_state"], "reviewable_candidate")

    def test_conflict_proposes_existing_rite_without_new_conflict_schema(self):
        report = policy.classify_request(
            {
                "intent": "Examiner des éléments contradictoires.",
                "scope": SCOPE,
                "conditions": ["evidence_gap"],
                "conflict_detected": True,
            }
        )

        self.assertEqual(report["handling"]["disposition"], "CONSULT")
        self.assertIn("ARGOS", report["handling"]["role_viewpoints"])
        self.assertEqual(
            report["handling"]["rite_candidate"],
            "concordance_des_sources",
        )

    def test_external_transmission_moves_to_gate(self):
        report = policy.classify_request(
            {
                "intent": "Envoyer la réponse préparée.",
                "scope": SCOPE,
                "conditions": ["external_transmission"],
            }
        )

        self.assertEqual(report["consequence_level"], "K4")
        self.assertEqual(report["handling"]["disposition"], "GATE")
        self.assertIn("IRIS", report["handling"]["role_viewpoints"])
        self.assertTrue(report["handling"]["effect_gate"]["effect_requested_now"])
        self.assertEqual(
            report["handling"]["effect_gate"]["required_approval_ceiling"],
            "C4",
        )

    def test_declared_relations_remain_candidate_inputs(self):
        report = policy.classify_request(
            {
                "intent": "Examiner ce point.",
                "scope": SCOPE,
                "conditions": ["source_required"],
                "coordination": {"branch_on": ["source_status"]},
            }
        )

        self.assertIn(
            "declared_conditions_and_relations_are_candidates_not_truth",
            report["handling"]["constraints"],
        )
        self.assertEqual(report["handling"]["conditions"], ["source_required"])

    def test_general_professional_objects_share_condition_driven_handling(self):
        cases = (
            (
                {
                    "intent": "Déterminer le budget à annoncer pour un dossier client.",
                    "scope": {"scope_type": "dossier", "scope_id": "budget-fixture"},
                    "conditions": [
                        "factual_claim",
                        "source_required",
                        "legal_or_professional_risk",
                        "delivery_quality_required",
                    ],
                    "coordination": {
                        "requires": [
                            ["supporting_basis", "consequence_review"],
                            ["consequence_review", "readiness_review"],
                        ]
                    },
                    "completion_requirements": [
                        "exact_source_opened",
                        "monetary_perimeter_reconciled",
                        "readiness_stated",
                    ],
                },
                ["ARGOS", "THEMIS", "APOLLO"],
                "sequential_handoff",
            ),
            (
                {
                    "intent": "Rédiger un message externe à partir de faits du dossier.",
                    "scope": {"scope_type": "task", "scope_id": "message-fixture"},
                    "conditions": [
                        "narrative_or_editorial_work",
                        "source_required",
                        "external_transmission",
                        "client_delivery",
                    ],
                    "completion_requirements": [
                        "sources_qualified",
                        "commitments_reviewed",
                        "draft_ready_for_human_gate",
                    ],
                },
                ["APOLLO", "ARGOS", "IRIS"],
                None,
            ),
            (
                {
                    "intent": "Produire une section technique de cahier des charges.",
                    "scope": {"scope_type": "task", "scope_id": "specification-fixture"},
                    "conditions": [
                        "artifact_fabrication",
                        "factual_claim",
                        "source_required",
                        "legal_or_professional_risk",
                        "delivery_quality_required",
                    ],
                    "completion_requirements": [
                        "technical_basis_qualified",
                        "section_complete",
                        "readiness_stated",
                    ],
                },
                ["HEPHAISTOS", "ARGOS", "THEMIS", "APOLLO"],
                None,
            ),
        )

        for request, expected_roles, expected_topology in cases:
            with self.subTest(intent=request["intent"]):
                report = policy.classify_request(request)
                handling = report["handling"]
                self.assertEqual(handling["role_viewpoints"], expected_roles)
                self.assertEqual(
                    handling.get("topology", {}).get("suggested"),
                    expected_topology,
                )
                self.assertEqual(
                    handling["completion_requirements"],
                    request["completion_requirements"],
                )
                self.assertIn(handling["disposition"], {"CONSULT", "GATE"})

    def test_role_trigger_projection_is_subset_of_role_activation_doctrine(self):
        doctrine = (REPO_ROOT / "docs/governance/ROLE_ACTIVATION.md").read_text(
            encoding="utf-8"
        )
        marker = "mandatory_role_triggers:"
        start = doctrine.index(marker)
        end = doctrine.index("```", start)
        parsed = yaml.safe_load(doctrine[start:end])
        canonical = parsed["mandatory_role_triggers"]

        for trigger, roles in request_handling.ROLE_TRIGGER_MAP.items():
            for role in roles:
                self.assertIn(role, canonical, f"role missing from doctrine: {role}")
                self.assertIn(
                    trigger,
                    canonical[role],
                    f"{trigger} -> {role} is not owned by ROLE_ACTIVATION.md",
                )


if __name__ == "__main__":
    unittest.main()
