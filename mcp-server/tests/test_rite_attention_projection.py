"""Regression tests for the deterministic Rite attention front edge.

The projection may surface a question from an observable signal. It must not
activate a Rite, dispatch a Role, authorize an effect or turn completion into
approval.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = MODULE_DIR.parent
sys.path.insert(0, str(MODULE_DIR))

from pantheon_mcp import policy, request_handling  # noqa: E402


SCOPE = {"scope_type": "task", "scope_id": "rite-attention-test"}


class TestRiteAttentionProjection(unittest.TestCase):
    def test_tests_pass_surfaces_question_without_activating_rite(self):
        report = policy.classify_request(
            {
                "intent": "Vérifier le candidat jusqu'à ce que les tests passent.",
                "scope": SCOPE,
                "conditions": ["delivery_quality_required"],
                "completion_requirements": ["tests_pass"],
                "coordination": {"repeat_until": ["tests_pass"]},
            }
        )

        handling = report["handling"]
        self.assertEqual(handling["disposition"], "CONSULT")
        self.assertEqual(
            handling["metathoughts"],
            [
                {
                    "signal_id": "tests_pass_completion",
                    "signal_source": "completion_requirements:tests_pass",
                    "question": "What would passing these tests still not establish?",
                    "attention_failure": "tests_pass_treated_as_claim_proven",
                    "related_rite": "autocritique_contradictoire",
                    "default_mode": "mode_light",
                    "effect": "attention_only",
                }
            ],
        )
        self.assertNotIn("rite_candidate", handling)
        self.assertIn(
            "metathought_question_does_not_activate_rite",
            handling["constraints"],
        )

    def test_other_completion_requirement_stays_quiet(self):
        report = policy.classify_request(
            {
                "intent": "Vérifier un fait demandé.",
                "scope": SCOPE,
                "conditions": ["source_required"],
                "completion_requirements": ["requested_fact_resolved"],
            }
        )

        self.assertNotIn("metathoughts", report["handling"])
        self.assertNotIn(
            "metathought_question_does_not_activate_rite",
            report["handling"]["constraints"],
        )

    def test_existing_conflict_rite_candidate_remains_independent(self):
        report = policy.classify_request(
            {
                "intent": "Examiner un candidat testé et des sources contradictoires.",
                "scope": SCOPE,
                "conditions": ["evidence_gap"],
                "completion_requirements": ["tests_pass"],
                "conflict_detected": True,
            }
        )

        handling = report["handling"]
        self.assertEqual(handling["rite_candidate"], "concordance_des_sources")
        self.assertEqual(
            handling["metathoughts"][0]["related_rite"],
            "autocritique_contradictoire",
        )
        self.assertEqual(handling["metathoughts"][0]["effect"], "attention_only")

    def test_implemented_signal_stays_bound_to_governance_catalogue(self):
        doctrine = (
            REPO_ROOT / "docs/governance/rites/RITE_TRIGGER_CATALOGUE.md"
        ).read_text(encoding="utf-8")
        signal = request_handling.RITE_ATTENTION_SIGNALS["tests_pass_completion"]

        self.assertIn("tests_pass_completion", doctrine)
        self.assertIn(signal["question"], doctrine)
        self.assertIn("AUTOCRITIQUE_CONTRADICTOIRE", doctrine)
        self.assertIn("attention_only", doctrine)


if __name__ == "__main__":
    unittest.main()
