"""Read-only tests for the gate-validation slice."""

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = MODULE_DIR.parent
sys.path.insert(0, str(MODULE_DIR))

from pantheon_mcp import gate_validation  # noqa: E402
from pantheon_mcp.service import PantheonPolicyService  # noqa: E402

NOW = datetime(2026, 7, 23, 12, 0, 0, tzinfo=timezone.utc)


def _valid_payload():
    return {
        "decision": {
            "decision_id": "dec-001",
            "decided_by": "marie.dupont",
            "decided_at": "2026-07-23T10:00:00Z",
            "expires_at": "2026-07-24T10:00:00Z",
            "approval_level": "C3",
            "scope": {"scope_type": "project", "scope_id": "P-42"},
            "object_identity": "effect:send-quote:sha256:abc",
            "content_digest": "sha256:abc",
        },
        "expectation": {
            "required_ceiling": "C3",
            "required_scope": {"scope_type": "project", "scope_id": "P-42"},
            "object_identity": "effect:send-quote:sha256:abc",
            "expected_digest": "sha256:abc",
        },
    }


class GateValidationTest(unittest.TestCase):
    def test_fully_matching_decision_is_valid(self):
        result = gate_validation.validate_decision(_valid_payload(), now=NOW)
        self.assertEqual(result["verdict"], "valid")
        self.assertTrue(result["gate_signal_validation_performed"])
        self.assertTrue(all(s != "fail" for s in result["checks"].values()))

    def test_expired_decision_is_invalid(self):
        payload = _valid_payload()
        payload["decision"]["expires_at"] = "2026-07-23T11:00:00Z"  # before NOW
        result = gate_validation.validate_decision(payload, now=NOW)
        self.assertEqual(result["verdict"], "invalid")
        self.assertEqual(result["checks"]["expiry"], "fail")

    def test_scope_mismatch_is_invalid(self):
        payload = _valid_payload()
        payload["decision"]["scope"]["scope_id"] = "P-99"
        result = gate_validation.validate_decision(payload, now=NOW)
        self.assertEqual(result["verdict"], "invalid")
        self.assertEqual(result["checks"]["scope"], "fail")

    def test_insufficient_level_is_invalid(self):
        payload = _valid_payload()
        payload["decision"]["approval_level"] = "C1"  # below required C3
        result = gate_validation.validate_decision(payload, now=NOW)
        self.assertEqual(result["verdict"], "invalid")
        self.assertEqual(result["checks"]["level"], "fail")

    def test_object_identity_mismatch_is_invalid(self):
        payload = _valid_payload()
        payload["decision"]["object_identity"] = "effect:other"
        result = gate_validation.validate_decision(payload, now=NOW)
        self.assertEqual(result["verdict"], "invalid")
        self.assertEqual(result["checks"]["object_identity"], "fail")

    def test_digest_mismatch_is_invalid(self):
        payload = _valid_payload()
        payload["decision"]["content_digest"] = "sha256:tampered"
        result = gate_validation.validate_decision(payload, now=NOW)
        self.assertEqual(result["verdict"], "invalid")
        self.assertEqual(result["checks"]["digest"], "fail")

    def test_system_signer_is_refused(self):
        for signer in ["system", "hermes", "service:runner", "pantheon-mcp", "bot-7", ""]:
            payload = _valid_payload()
            payload["decision"]["decided_by"] = signer
            result = gate_validation.validate_decision(payload, now=NOW)
            self.assertEqual(result["verdict"], "invalid", signer)
            self.assertEqual(result["checks"]["signer"], "fail", signer)

    def test_human_signer_with_role_prefix_is_accepted(self):
        payload = _valid_payload()
        payload["decision"]["decided_by"] = "architect:marie.dupont"
        result = gate_validation.validate_decision(payload, now=NOW)
        self.assertEqual(result["checks"]["signer"], "ok")

    def test_missing_required_fields_are_flagged(self):
        result = gate_validation.validate_decision({"decision": {}, "expectation": {}}, now=NOW)
        self.assertEqual(result["verdict"], "invalid")
        self.assertEqual(result["checks"]["structural"], "fail")

    def test_missing_expiry_and_digest_are_noted_not_asserted(self):
        payload = _valid_payload()
        payload["decision"].pop("expires_at")
        payload["expectation"].pop("expected_digest")
        result = gate_validation.validate_decision(payload, now=NOW)
        # Not-checked states are noted but do not by themselves fail the verdict.
        self.assertEqual(result["checks"]["expiry"], "not_checked")
        self.assertEqual(result["checks"]["digest"], "not_checked")
        self.assertEqual(result["verdict"], "valid")
        self.assertTrue(any("expiry" in f for f in result["findings"]))

    def test_valid_verdict_is_not_an_authorization(self):
        result = gate_validation.validate_decision(_valid_payload(), now=NOW)
        self.assertTrue(any("not an approval" in f for f in result["limits"]))

    # --- issuer authentication (the human-issuer chainlink) ---

    def test_issuer_unauthenticated_when_no_registry_configured(self):
        result = gate_validation.validate_decision(_valid_payload(), now=NOW)
        self.assertEqual(result["checks"]["issuer"], "not_checked")
        self.assertFalse(result["issuer_authenticated"])
        self.assertEqual(result["verdict"], "valid")  # not configured != failure

    def test_correct_issuer_signature_authenticates_and_stays_valid(self):
        payload = _valid_payload()
        secret = "issuer-secret-key"
        payload["decision"]["signature"] = gate_validation._expected_issuer_signature(
            secret, payload["decision"]
        )
        result = gate_validation.validate_decision(
            payload, now=NOW, issuer_keys={"marie.dupont": secret}
        )
        self.assertEqual(result["checks"]["issuer"], "ok")
        self.assertTrue(result["issuer_authenticated"])
        self.assertEqual(result["verdict"], "valid")

    def test_missing_signature_with_registry_fails(self):
        result = gate_validation.validate_decision(
            _valid_payload(), now=NOW, issuer_keys={"marie.dupont": "k"}
        )
        self.assertEqual(result["checks"]["issuer"], "fail")
        self.assertEqual(result["verdict"], "invalid")

    def test_unknown_issuer_fails(self):
        payload = _valid_payload()
        payload["decision"]["signature"] = "whatever"
        result = gate_validation.validate_decision(
            payload, now=NOW, issuer_keys={"someone.else": "k"}
        )
        self.assertEqual(result["checks"]["issuer"], "fail")
        self.assertTrue(any("no registered signing key" in f for f in result["findings"]))

    def test_tampered_signature_or_payload_fails(self):
        payload = _valid_payload()
        secret = "issuer-secret-key"
        payload["decision"]["signature"] = gate_validation._expected_issuer_signature(
            secret, payload["decision"]
        )
        # move the decision to a different scope after signing -> signature no longer verifies
        payload["decision"]["scope"] = {"scope_type": "project", "scope_id": "P-99"}
        result = gate_validation.validate_decision(
            payload, now=NOW, issuer_keys={"marie.dupont": secret}
        )
        self.assertEqual(result["checks"]["issuer"], "fail")
        self.assertTrue(result["issuer_authenticated"] is False)


class GateValidationServiceTest(unittest.TestCase):
    def test_service_projects_the_verdict_with_no_authorization_effect(self):
        service = PantheonPolicyService(REPO_ROOT)
        result = service.validate_decision(_valid_payload())
        self.assertEqual(result["operation"], "policy.decision.validate")
        self.assertEqual(result["authorization_effect"], "none")
        self.assertFalse(result["write_effect"])
        self.assertFalse(result["execution_effect"])
        self.assertIn("verdict", result)
        self.assertIn("input_sha256", result)


if __name__ == "__main__":
    unittest.main()
