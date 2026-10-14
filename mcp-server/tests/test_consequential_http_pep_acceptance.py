"""Issue Pantheon-Next#664: real Next HTTP PDP -> existing MVP PEP acceptance.

The original synthetic external-effect fixture proves the one bounded signed path
with replay protection. Direct-human local governed effects reuse the same real
HTTP PDP and decision validator without pretending they are delegated runtime
tasks. All effects here are synthetic test callbacks; the in-memory one-shot
consumer is a fixture, not Pantheon persistence.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

MODULE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = MODULE_DIR.parent
IMPLEMENTATION_DIR = REPO_ROOT / "implementation"
sys.path.insert(0, str(MODULE_DIR))
sys.path.insert(0, str(IMPLEMENTATION_DIR))

from mvp_vertical.policy_gate import HttpPolicyClient, governed_effect  # noqa: E402
from pantheon_mcp import effect_qualification, gate_validation  # noqa: E402
from pantheon_mcp.http_api import create_app  # noqa: E402
from pantheon_mcp.service import PantheonPolicyService  # noqa: E402

API_KEY = "qualification-policy-api-key"
ISSUER = "marie.dupont"
ISSUER_SECRET = "qualification-issuer-secret"
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
    decision["signature"] = gate_validation._expected_issuer_signature(
        ISSUER_SECRET, decision
    )
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
        },
        "decision_expectation": {
            "required_ceiling": "C3",
            "required_scope": dict(SCOPE),
            "object_identity": identity,
            "expected_digest": digest,
        },
    }


def _decision(*, expires_at: str = "2099-01-01T00:00:00Z") -> dict:
    decision = {
        "decision_id": "decision-qualification-http-001",
        "decided_by": ISSUER,
        "expires_at": expires_at,
        "approval_level": "C3",
        "scope": dict(SCOPE),
        "object_identity": effect_qualification.expected_object_identity(SCOPE),
        "content_digest": effect_qualification.expected_effect_digest(SCOPE),
    }
    decision["signature"] = gate_validation._expected_issuer_signature(
        ISSUER_SECRET, decision
    )
    return {
        "decision": decision,
        # Deliberately caller-controlled.  The PEP must replace this with its
        # candidate-derived expectation before either HTTP policy call.
        "expectation": {
            "required_ceiling": "C0",
            "required_scope": {"scope_type": "project", "scope_id": "attacker"},
            "object_identity": "caller-controlled",
            "expected_digest": "sha256:caller-controlled",
        },
    }


def _direct_human_candidate() -> dict:
    return {
        "request": {
            "intent": "act_working_information",
            "external_effect": False,
            "writes_state": True,
            "transmission_requested": False,
            "memory_promotion_requested": False,
            "professional_position": False,
            "financial_or_contractual_effect": False,
            "scope": dict(SCOPE),
        },
        "decision_expectation": {
            "required_ceiling": "C2",
            "required_scope": dict(SCOPE),
            "object_identity": "information:info-fixture:acted",
            "expected_digest": "sha256:direct-human-fixture",
        },
    }


def _direct_human_decision() -> dict:
    decision = {
        "decision_id": "decision-direct-human-http-001",
        "decided_by": ISSUER,
        "expires_at": "2099-01-01T00:00:00Z",
        "approval_level": "C2",
        "scope": dict(SCOPE),
        "object_identity": "information:info-fixture:acted",
        "content_digest": "sha256:direct-human-fixture",
    }
    decision["signature"] = gate_validation._expected_issuer_signature(
        ISSUER_SECRET, decision
    )
    return {
        "decision": decision,
        "expectation": {
            "required_ceiling": "C0",
            "required_scope": {"scope_type": "project", "scope_id": "attacker"},
            "object_identity": "caller-controlled",
            "expected_digest": "sha256:caller-controlled",
        },
    }


class ConsequentialHttpPepAcceptanceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = PantheonPolicyService(REPO_ROOT)
        self.http = TestClient(
            create_app(
                service=self.service,
                api_key=API_KEY,
                enable_docs=False,
            )
        )
        self.policy = HttpPolicyClient(
            "http://testserver",
            API_KEY,
            client=self.http,
        )
        self.consumed: set[str] = set()
        self.effects: list[str] = []

    def consume_once(self, decision_id: str) -> bool:
        if decision_id in self.consumed:
            return False
        self.consumed.add(decision_id)
        return True

    def run_effect(self, candidate: dict | None = None, decision: dict | None = None) -> dict:
        with patch.object(
            self.service,
            "_issuer_keys",
            return_value={ISSUER: ISSUER_SECRET},
        ):
            return governed_effect(
                self.policy,
                candidate=candidate or _candidate(),
                decision_payload=decision or _decision(),
                consume_decision=self.consume_once,
                effect=lambda: self.effects.append("ran") or {"synthetic": True},
            )

    def test_real_http_signed_gate_runs_exactly_once_and_replay_fails_closed(self):
        first = self.run_effect()
        second = self.run_effect()

        self.assertEqual(first["status"], "applied")
        self.assertTrue(first["effect_ran"])
        self.assertEqual(first["result"], {"synthetic": True})
        self.assertEqual(
            first["qualification_trace"],
            {
                "decision_consumed_once": True,
                "decision_id": "decision-qualification-http-001",
                "runtime_success_is_evidence": False,
                "effect_execution_is_approval": False,
            },
        )
        self.assertEqual(second["status"], "blocked")
        self.assertEqual(second["disposition"], "blocked_replayed_decision")
        self.assertFalse(second["effect_ran"])
        self.assertEqual(self.effects, ["ran"])
        self.assertEqual(self.consumed, {"decision-qualification-http-001"})

    def test_real_http_direct_human_local_write_uses_decision_without_delegation_artifacts(self):
        result = self.run_effect(
            candidate=_direct_human_candidate(),
            decision=_direct_human_decision(),
        )

        self.assertEqual(result["status"], "applied")
        self.assertTrue(result["effect_ran"])
        self.assertEqual(result["disposition"], "eligible_with_gate_signals_unverified")
        self.assertEqual(result["result"], {"synthetic": True})
        self.assertNotIn("qualification_trace", result)
        self.assertEqual(self.consumed, set())
        self.assertEqual(self.effects, ["ran"])

    def test_real_http_pdp_denial_precedes_validation_consumption_and_effect(self):
        candidate = _candidate()
        candidate["request"]["intent"] = "external_document_metadata_update"

        result = self.run_effect(candidate=candidate)

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["disposition"], "blocked_external_effect_not_authorized")
        self.assertEqual(self.consumed, set())
        self.assertEqual(self.effects, [])

    def test_real_http_forged_signature_fails_before_consumption(self):
        payload = _decision()
        payload["decision"]["signature"] = "forged"

        result = self.run_effect(decision=payload)

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["disposition"], "blocked_invalid_gate")
        self.assertEqual(self.consumed, set())
        self.assertEqual(self.effects, [])

    def test_real_http_expired_decision_fails_before_consumption(self):
        result = self.run_effect(decision=_decision(expires_at="2026-08-15T00:00:00Z"))

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["disposition"], "blocked_invalid_gate")
        self.assertEqual(self.consumed, set())
        self.assertEqual(self.effects, [])

    def test_real_http_mismatched_signed_object_fails_closed(self):
        payload = _decision()
        payload["decision"]["object_identity"] = "qualification-external-effect:other"
        payload["decision"]["signature"] = gate_validation._expected_issuer_signature(
            ISSUER_SECRET, payload["decision"]
        )

        result = self.run_effect(decision=payload)

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["disposition"], "blocked_invalid_gate")
        self.assertEqual(self.consumed, set())
        self.assertEqual(self.effects, [])

    def test_real_http_invented_task_contract_ref_fails_closed(self):
        candidate = _candidate()
        candidate["gate_signals"]["task_contract_ref"] = "tc.invented"

        result = self.run_effect(candidate=candidate)

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["disposition"], "blocked_invalid_gate")
        self.assertEqual(self.consumed, set())
        self.assertEqual(self.effects, [])


if __name__ == "__main__":
    unittest.main()
