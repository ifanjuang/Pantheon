"""Acceptance tests for the bounded Pantheon policy HTTP adapter."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

MODULE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = MODULE_DIR.parent
sys.path.insert(0, str(MODULE_DIR))

from pantheon_mcp.http_api import create_app  # noqa: E402
from pantheon_mcp.service import PantheonPolicyService  # noqa: E402


class TestPantheonPolicyHttpApi(unittest.TestCase):
    def setUp(self) -> None:
        self.service = PantheonPolicyService(REPO_ROOT)
        self.client = TestClient(
            create_app(
                service=self.service,
                api_key="test-policy-secret",
                max_body_bytes=1024,
                enable_docs=False,
            )
        )
        self.headers = {"Authorization": "Bearer test-policy-secret"}

    def test_liveness_is_public_but_policy_routes_require_authentication(self):
        self.assertEqual(self.client.get("/livez").status_code, 200)
        ready = self.client.get("/readyz")
        self.assertEqual(ready.status_code, 200)
        self.assertEqual(ready.json()["status"], "ready")
        self.assertEqual(self.client.get("/meta").status_code, 401)

        traced = self.client.get(
            "/meta",
            headers={**self.headers, "X-Request-ID": "fixture-request"},
        )
        self.assertEqual(traced.json()["mode"], "read_only")
        self.assertEqual(traced.json()["request_id"], "fixture-request")
        self.assertEqual(
            traced.headers["x-pantheon-request-id"], "fixture-request"
        )

    def test_missing_server_key_fails_closed(self):
        client = TestClient(
            create_app(service=self.service, api_key="", enable_docs=False)
        )
        response = client.get(
            "/meta", headers={"Authorization": "Bearer anything"}
        )
        self.assertEqual(response.status_code, 503)

    def test_repository_state_does_not_expose_internal_checkout_path(self):
        response = self.client.get("/repository/state", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("repo_path", response.json())
        self.assertTrue(response.json()["repository_accessible"])

    def test_http_classification_matches_transport_neutral_service_semantics(self):
        request = {
            "intent": "Prepare a client-facing contractual position on a disputed quote",
            "external_effect": True,
            "professional_position": True,
            "scope": {"scope_type": "project", "scope_id": "fixture-project"},
        }
        expected = self.service.classify_request(request)
        actual = self.client.post(
            "/policy/requests:classify",
            json=request,
            headers=self.headers,
        )
        self.assertEqual(actual.status_code, 200)
        payload = actual.json()
        for field in (
            "result",
            "consequence_level",
            "required_verification",
            "required_approval_ceiling",
            "task_contract_required",
            "evidence_required",
            "blocked_until_gate",
            "input_sha256",
        ):
            self.assertEqual(payload[field], expected[field])
        self.assertEqual(payload["authorization_effect"], "none")
        self.assertFalse(payload["execution_effect"])
        self.assertTrue(payload["request_id"])

    def test_k4_preflight_blocks_until_declared_gates_are_present(self):
        body = {
            "request": {
                "intent": "Transmit a contractual professional position to the client",
                "external_effect": True,
                "transmission_requested": True,
                "scope": {"scope_type": "project", "scope_id": "fixture-project"},
            },
            "gate_signals": {},
        }
        response = self.client.post(
            "/policy/preflights:evaluate",
            json=body,
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["classification"]["consequence_level"], "K4")
        self.assertEqual(payload["policy_disposition"], "blocked_pending_task_contract")
        self.assertIn("reviewed_task_contract_ref", payload["missing_requirements"])
        self.assertIn("evidence_pack_candidate_ref", payload["missing_requirements"])
        self.assertIn("human_decision_ref", payload["missing_requirements"])
        self.assertFalse(payload["candidate_work_allowed"])
        self.assertFalse(payload["external_effect_allowed"])

    def test_gate_references_allow_candidate_work_but_never_external_effect(self):
        body = {
            "request": {
                "intent": "Transmit a contractual professional position to the client",
                "external_effect": True,
                "transmission_requested": True,
                "scope": {"scope_type": "project", "scope_id": "fixture-project"},
            },
            "gate_signals": {
                "task_contract_ref": "tc-fixture",
                "evidence_pack_candidate_ref": "epc-fixture",
                "human_decision_ref": "decision-fixture",
                "human_decision_level": "C4",
            },
        }
        payload = self.client.post(
            "/policy/preflights:evaluate",
            json=body,
            headers=self.headers,
        ).json()
        self.assertEqual(
            payload["policy_disposition"],
            "eligible_with_gate_signals_unverified",
        )
        self.assertTrue(payload["candidate_work_allowed"])
        self.assertFalse(payload["external_effect_allowed"])
        self.assertFalse(payload["gate_signal_validation_performed"])

    def test_body_size_limit_is_enforced_before_policy_evaluation(self):
        response = self.client.post(
            "/policy/requests:classify",
            content=b"{" + b"x" * 2048 + b"}",
            headers={**self.headers, "Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["result"], "request_too_large")
        self.assertTrue(response.headers["x-pantheon-request-id"])

    def test_legacy_ambiguous_routes_fail_loudly(self):
        context = self.client.get("/runtime/context-pack", headers=self.headers)
        snapshot = self.client.get("/domain/snapshot", headers=self.headers)
        self.assertEqual(context.status_code, 501)
        self.assertEqual(snapshot.status_code, 501)
        self.assertEqual(context.json()["result"], "contract_not_defined")
        self.assertIn("/context-packs:plan", context.json()["replacement"][0])

    def test_legacy_approval_route_is_a_classification_alias_only(self):
        response = self.client.post(
            "/domain/approval/classify",
            json={
                "intent": "Draft an internal note",
                "scope": {"scope_type": "task", "scope_id": "fixture-task"},
            },
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["compatibility_route"])
        self.assertEqual(response.json()["authorization_effect"], "none")

    def test_verification_profile_is_canonical_and_preset_route_is_deprecated(self):
        candidate = {
            "module_id": "fixture.module",
            "verifications": {
                "install": {
                    "applies": True,
                    "expected_checks": ["readyz"],
                }
            },
        }
        canonical = self.client.post(
            "/verifications/profiles:load",
            json=candidate,
            headers=self.headers,
        )
        self.assertEqual(canonical.status_code, 200)
        self.assertEqual(canonical.json()["operation"], "verification.profile.load")
        self.assertEqual(canonical.json()["object_term"], "verification_profile")
        self.assertTrue(canonical.json()["schema_identifier_legacy"])
        self.assertNotIn("compatibility_route", canonical.json())

        legacy = self.client.post(
            "/verifications/presets:load",
            json=candidate,
            headers=self.headers,
        )
        self.assertEqual(legacy.status_code, 200)
        self.assertTrue(legacy.json()["compatibility_route"])
        self.assertTrue(legacy.json()["deprecated"])
        self.assertEqual(
            legacy.json()["replacement"], "/verifications/profiles:load"
        )
        self.assertEqual(legacy.json()["authorization_effect"], "none")

    def test_context_pack_validation_is_schema_only(self):
        candidate = {
            "context_pack_id": "context.fixture",
            "purpose": "Prepare bounded context for a fictional Hermes task",
            "scope": {
                "scope_type": "project",
                "scope_id": "fixture-project",
                "included_scopes": ["fixture-project"],
                "excluded_scopes": ["all-other-projects"],
            },
            "target_surface": "hermes_task_contract",
            "included_doctrine": ["docs/governance/TASK_CONTRACTS.md"],
            "included_context": [],
            "task_constraints": ["fictional data only"],
            "evidence_expectations": ["cite dated source references"],
            "approval_expectations": ["human review before consequential use"],
            "output_expectations": ["candidate output only"],
            "forbidden_assumptions": ["retrieved material is not evidence"],
            "status": "draft",
        }
        response = self.client.post(
            "/context-packs:validate",
            json=candidate,
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["valid"])
        self.assertFalse(payload["canonical_effect"])
        self.assertFalse(payload["retrieval_performed"])

        invalid = self.client.post(
            "/context-packs:validate",
            json={"context_pack_id": "bad"},
            headers=self.headers,
        ).json()
        self.assertFalse(invalid["valid"])
        self.assertGreater(len(invalid["problems"]), 0)


if __name__ == "__main__":
    unittest.main()
