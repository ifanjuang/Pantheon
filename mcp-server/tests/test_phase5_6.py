"""Phase 5-6 tests: skeleton tools, fixtures and the housing vertical.

Fixture-driven and read-only: each development fixture under fixtures/ is
loaded and its declared expectations are asserted against the importable
logic (no MCP SDK required, no side effects).
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_DIR))

import yaml  # noqa: E402

from pantheon_mcp import contracts, policy  # noqa: E402

FIXTURES = MODULE_DIR / "fixtures"

FORBIDDEN_LANGUAGE = [
    "approved",
    "validated truth",
    "authorized action",
    "safe to execute",
]


def _load(name: str) -> dict:
    return yaml.safe_load((FIXTURES / name).read_text(encoding="utf-8"))


class TestSkeletonTools(unittest.TestCase):
    def test_task_contract_skeleton_shape(self):
        req = _load("sequence_conformance.yaml")["request"]
        skel = contracts.prepare_task_contract_skeleton(req)
        self.assertEqual(skel["object"], "TASK_CONTRACT_CANDIDATE_SKELETON")
        self.assertTrue(skel["review_required"])
        self.assertIn(skel["status"], skel["allowed_status_terms"])
        self.assertTrue(skel["forbidden_behaviors"])
        dumped = json.dumps(skel).lower()
        for phrase in FORBIDDEN_LANGUAGE:
            self.assertNotIn(phrase, dumped)

    def test_evidence_pack_skeleton_shape(self):
        req = _load("sequence_conformance.yaml")["request"]
        skel = contracts.prepare_evidence_pack_skeleton(req)
        self.assertEqual(skel["object"], "EVIDENCE_PACK_CANDIDATE_SKELETON")
        for field in ("sources_expected", "assumptions_to_state",
                      "claims_to_support", "register_candidates"):
            self.assertIn(field, skel)
        self.assertEqual(skel["sources_expected"], req["sources_expected"])

    def test_missing_scope_yields_scope_unclear(self):
        skel = contracts.prepare_task_contract_skeleton({"intent": "summarize notes"})
        self.assertEqual(skel["scope_status"], "scope unclear")


class TestSequenceConformance(unittest.TestCase):
    def test_full_sequence(self):
        fx = _load("sequence_conformance.yaml")
        expected = fx["expected"]

        report = policy.classify_request(fx["request"])
        for key, want in expected["classify_request"].items():
            self.assertEqual(report[key], want, key)

        skel = contracts.prepare_task_contract_skeleton(fx["request"])
        self.assertEqual(skel["object"], expected["prepare_task_contract_skeleton"]["object"])
        dumped = json.dumps(skel).lower()
        for phrase in expected["prepare_task_contract_skeleton"]["forbidden_language"]:
            self.assertNotIn(phrase.lower(), dumped)

        pack = contracts.prepare_evidence_pack_skeleton(fx["request"])
        self.assertEqual(pack["object"], expected["prepare_evidence_pack_skeleton"]["object"])
        for field in expected["prepare_evidence_pack_skeleton"]["includes"]:
            self.assertIn(field, pack)

        gate = policy.check_external_action(expected["refusal_check"]["attempted_action"])
        self.assertEqual(gate["status"], expected["refusal_check"]["expected_status"])


class TestHousingVertical(unittest.TestCase):
    """Résidence Les Tilleuls — VEFA surface claim (fictional)."""

    def setUp(self):
        self.fx = _load("residence_les_tilleuls_vefa_surface_claim.yaml")

    def test_classification_is_k4_v4_c4_blocked(self):
        want = self.fx["expected_outputs"]["classification"]
        report = policy.classify_request(self.fx["request"])
        self.assertEqual(report["consequence_level"], want["consequence_level"])
        self.assertEqual(report["required_verification"], want["required_verification"])
        self.assertEqual(report["required_approval_ceiling"], want["approval_level"])
        self.assertEqual(report["blocked_until_gate"], want["blocked_until_gate"])

    def test_refusal_cases_in_french(self):
        for case in self.fx["refusal_cases"]:
            report = policy.classify_request({"perform": [case["request"]]})
            self.assertEqual(report["result"], "refused", case["request"])

    def test_skeletons_stay_candidate(self):
        skel = contracts.prepare_task_contract_skeleton(self.fx["request"])
        self.assertIn(skel["status"], skel["allowed_status_terms"])
        pack = contracts.prepare_evidence_pack_skeleton(self.fx["request"])
        self.assertEqual(pack["status"], "blocked pending evidence")
        self.assertEqual(pack["sources_expected"], self.fx["request"]["sources_expected"])


class TestBaseFixtures(unittest.TestCase):
    """Every development fixture classifies without error and, when it
    declares an expected classification, matches it."""

    def test_all_fixtures(self):
        for path in sorted(FIXTURES.glob("*.yaml")):
            if path.name.startswith("passport_"):
                continue
            fx = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(fx, dict) or "request" not in fx:
                continue
            report = policy.classify_request(fx["request"])
            self.assertIn(report["result"], ("classified", "refused"), path.name)
            expected = (fx.get("expected_outputs") or fx.get("expected") or {})
            want = expected.get("classification") or expected.get("classify_request") or {}
            if want.get("result") == "refused" or fx.get("case_type") == "refusal":
                self.assertEqual(report["result"], "refused", path.name)
                continue
            for key in ("consequence_level", "required_verification"):
                if key in want:
                    self.assertEqual(report[key], want[key], f"{path.name}:{key}")


if __name__ == "__main__":
    unittest.main()
