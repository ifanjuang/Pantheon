"""Issue Pantheon-Next#664: one bounded green consequential path without production effects."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from jsonschema import Draft202012Validator

MODULE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = MODULE_DIR.parent
sys.path.insert(0, str(MODULE_DIR))

from pantheon_mcp import effect_qualification, gate_validation  # noqa: E402
from pantheon_mcp.service import PantheonPolicyService  # noqa: E402

SECRET = "qualification-issuer-secret"
SCOPE = {"scope_type": "project", "scope_id": "qualification-sandbox"}


def _candidate(*, expires_at: str = "2099-01-01T00:00:00Z") -> dict:
    identity = effect_qualification.expected_object_identity(SCOPE)
    digest = effect_qualification.expected_effect_digest(SCOPE)
    decision = {
        "decision_id": "decision-qualification-001",
        "decided_by": "marie.dupont",
        "expires_at": expires_at,
        "approval_level": "C3",
        "scope": dict(SCOPE),
        "object_identity": identity,
        "content_digest": digest,
    }
    decision["signature"] = gate_validation._expected_issuer_signature(SECRET, decision)
    return {
        "request": {
            "intent": effect_qualification.QUALIFICATION_INTENT,
            "external_effect": True,
            "writes_state": True,
            "transmission_requested": False,
            "memory_promotion_requested": False,
            "professional_position": False,
            "financial_or_contractual_effect": False,
            "scope": dict(SCOPE),
        },
        "gate_signals": {
            "task_contract_ref": effect_qualification.TASK_CONTRACT_REF,
            "evidence_pack_candidate_ref": effect_qualification.EVIDENCE_PACK_CANDIDATE_REF,
            "human_decision_ref": decision["decision_id"],
            "human_decision_level": decision["approval_level"],
        },
        "decision_validation": {
            "decision": decision,
            "expectation": {
                "required_ceiling": "C3",
                "required_scope": dict(SCOPE),
                "object_identity": identity,
                "expected_digest": digest,
            },
        },
    }


class ConsequentialGreenPathTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = PantheonPolicyService(REPO_ROOT)

    def _preflight(self, candidate: dict) -> dict:
        with patch.object(
            self.service,
            "_issuer_keys",
            return_value={"marie.dupont": SECRET},
        ):
            return self.service.evaluate_preflight(candidate)

    def test_repository_fixtures_conform_to_existing_schemas(self):
        cases = (
            (
                effect_qualification.TASK_CONTRACT_FIXTURE,
                REPO_ROOT / "schemas/task_contract.schema.yaml",
            ),
            (
                effect_qualification.EVIDENCE_PACK_FIXTURE,
                REPO_ROOT / "schemas/evidence_pack.schema.yaml",
            ),
        )
        for fixture_path, schema_path in cases:
            candidate = yaml.safe_load((REPO_ROOT / fixture_path).read_text(encoding="utf-8"))
            schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
            errors = list(Draft202012Validator(schema).iter_errors(candidate))
            self.assertEqual(errors, [], [error.message for error in errors])

    def test_nominal_fixture_emits_one_bounded_external_permission(self):
        report = self._preflight(_candidate())

        self.assertEqual(report["classification"]["consequence_level"], "K4")
        self.assertEqual(report["classification"]["required_approval_ceiling"], "C3")
        self.assertEqual(report["policy_disposition"], "eligible_with_gate_validated")
        self.assertTrue(report["candidate_work_allowed"])
        self.assertTrue(report["external_effect_allowed"])
        self.assertFalse(report["canonical_effect_allowed"])
        self.assertTrue(report["gate_signal_validation_performed"])
        self.assertTrue(report["replay_guard_required"])
        self.assertEqual(report["qualification"]["findings"], [])
        self.assertTrue(report["qualification"]["gate_validation"]["issuer_authenticated"])
        self.assertEqual(
            report["runtime_enforcement"],
            "pep_must_consume_decision_once_before_external_effect",
        )

    def test_invented_task_contract_reference_fails_closed(self):
        candidate = _candidate()
        candidate["gate_signals"]["task_contract_ref"] = "tc.invented"
        report = self._preflight(candidate)

        self.assertEqual(report["policy_disposition"], "blocked_invalid_gate")
        self.assertFalse(report["external_effect_allowed"])
        self.assertFalse(report["replay_guard_required"])
        self.assertTrue(
            any("task_contract_ref" in item for item in report["qualification"]["findings"])
        )

    def test_mismatched_decision_reference_fails_closed(self):
        candidate = _candidate()
        candidate["gate_signals"]["human_decision_ref"] = "decision-other"
        report = self._preflight(candidate)

        self.assertEqual(report["policy_disposition"], "blocked_invalid_gate")
        self.assertFalse(report["external_effect_allowed"])
        self.assertTrue(
            any("human_decision_ref" in item for item in report["qualification"]["findings"])
        )

    def test_forged_signature_fails_closed(self):
        candidate = _candidate()
        candidate["decision_validation"]["decision"]["signature"] = "forged"
        report = self._preflight(candidate)

        self.assertEqual(report["policy_disposition"], "blocked_invalid_gate")
        self.assertFalse(report["external_effect_allowed"])
        self.assertTrue(report["gate_signal_validation_performed"])
        self.assertEqual(
            report["qualification"]["gate_validation"]["checks"]["issuer"],
            "fail",
        )

    def test_expired_signed_decision_fails_closed(self):
        report = self._preflight(_candidate(expires_at="2026-08-15T00:00:00Z"))

        self.assertEqual(report["policy_disposition"], "blocked_invalid_gate")
        self.assertFalse(report["external_effect_allowed"])
        self.assertEqual(
            report["qualification"]["gate_validation"]["checks"]["expiry"],
            "fail",
        )

    def test_missing_issuer_registry_fails_strict_fixture_gate(self):
        report = self.service.evaluate_preflight(_candidate())

        self.assertEqual(report["policy_disposition"], "blocked_invalid_gate")
        self.assertFalse(report["external_effect_allowed"])
        self.assertFalse(report["qualification"]["gate_validation"]["issuer_authenticated"])

    def test_non_fixture_external_effect_stays_denied_even_with_valid_human_decision(self):
        candidate = _candidate()
        candidate["request"]["intent"] = "external_document_metadata_update"
        report = self._preflight(candidate)

        self.assertEqual(report["policy_disposition"], "eligible_with_gate_signals_unverified")
        self.assertFalse(report["external_effect_allowed"])
        self.assertFalse(report["canonical_effect_allowed"])
        self.assertFalse(report["gate_signal_validation_performed"])
        self.assertFalse(report["replay_guard_required"])
        self.assertIsNone(report["qualification"])


if __name__ == "__main__":
    unittest.main()
