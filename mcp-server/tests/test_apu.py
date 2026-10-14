"""Read-only tests for the APU validation surface.

They validate fictional candidate dossiers against the sole active governance
baseline. They execute nothing, persist nothing and canonize nothing.
"""

import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("PANTHEON_REPO_PATH", str(ROOT))

from pantheon_mcp import apu  # noqa: E402


def _clean_dossier() -> dict:
    return {
        "program": {
            "program_id": "PRG-1",
            "program_type": "housing",
            "program_layer": "specific_requirement",
            "source_authority": "approved_client_decision",
            "proof_status": "accepted_as_support",
        },
        "stable_object": {
            "stable_object_id": "SO-1",
            "project_ref": "PRJ-1",
            "object_family": "spatial",
            "nomenclature": {"display_name": "Chambre 1"},
        },
        "source_representation": {
            "representation_id": "REP-1",
            "project_ref": "PRJ-1",
            "source_artifact_ref": "SRC-1",
            "source_kind": "drawing",
            "identifiers": [
                {"scheme": "drawing.fragment", "value": "bedroom-polygon-1"}
            ],
            "observed_at": "2026-08-07T12:00:00Z",
            "binding_ref": "binding.drawing.fixture",
            "adapter_version": "0.2-test",
            "freshness_token": "fixture-revision-1",
            "proof_status": "candidate",
        },
        "requirement": {
            "requirement_id": "REQ-1",
            "source": {"source_type": "program", "source_ref": "PRG-1"},
            "requirement_kind": "attribute",
            "target": {
                "entity_ref": {"entity_type": "stable_object", "entity_id": "SO-1"}
            },
            "constraint": {
                "operator": "min",
                "attribute_key": "area",
                "expected_value": {
                    "value_type": "number",
                    "value": 9,
                    "unit": "m2",
                },
            },
            "source_authority": "approved_client_decision",
            "proof_status": "accepted_as_support",
        },
        "attribute_claim": {
            "attribute_claim_id": "AC-1",
            "subject_ref": {
                "entity_type": "source_representation",
                "entity_id": "REP-1",
            },
            "attribute_key": "area",
            "value": {"value_type": "number", "value": 8.4, "unit": "m2"},
            "assertion_mode": "observed",
            "source_authority": "project_working_document",
            "proof_status": "candidate",
            "source_representation_refs": ["REP-1"],
        },
        "relation_claim": {
            "relation_claim_id": "REL-ID-1",
            "subject_ref": {
                "entity_type": "source_representation",
                "entity_id": "REP-1",
            },
            "relation_type": "identity.represents",
            "object_ref": {"entity_type": "stable_object", "entity_id": "SO-1"},
            "assertion_mode": "proposed",
            "source_authority": "model_interpretation_candidate",
            "proof_status": "candidate",
            "source_representation_refs": ["REP-1"],
        },
    }


class TestApuValidation(unittest.TestCase):
    def test_v02_dossier_is_ok_and_candidate_only(self):
        report = apu.validate_apu_dossier(_clean_dossier())
        self.assertEqual(report["result"], "ok", report)
        self.assertEqual(report["validated"], 6)
        self.assertFalse(report["schema_errors"], report["schema_errors"])
        self.assertFalse(report["reference_errors"], report["reference_errors"])
        self.assertEqual(report["gate"]["posture"], "candidate-only")
        self.assertTrue(report["gate"]["canonical_emission_allowed"])
        self.assertFalse(report["gate"]["canonical_effect"])
        self.assertTrue(
            any(
                "identity relation remains candidate" in item
                for item in report["gate"]["human_decisions_required"]
            )
        )

    def test_unresolved_v02_reference_is_reported(self):
        dossier = _clean_dossier()
        dossier["requirement"]["target"]["entity_ref"]["entity_id"] = "SO-MISSING"
        report = apu.validate_apu_dossier(dossier)
        self.assertEqual(report["result"], "error", report)
        self.assertTrue(
            any("target.entity_ref" in item and "unresolved" in item for item in report["reference_errors"]),
            report["reference_errors"],
        )

    def test_unknown_object_type_is_reported(self):
        report = apu.validate_apu_dossier({"not_a_real_type": {}})
        self.assertEqual(report["result"], "error", report)
        self.assertTrue(any("unknown object type" in item for item in report["schema_errors"]))

    def test_discarded_carrier_is_rejected_as_unknown(self):
        report = apu.validate_apu_dossier(
            {
                "object_identity": {
                    "stable_id": "SO-1",
                    "object_kind": "opening",
                }
            }
        )
        self.assertEqual(report["result"], "error", report)
        self.assertTrue(
            any("unknown object type: object_identity" in item for item in report["schema_errors"])
        )

    def test_discarded_inline_match_shape_is_rejected(self):
        dossier = _clean_dossier()
        dossier["stable_object"]["matches"] = []
        report = apu.validate_apu_dossier(dossier)
        self.assertEqual(report["result"], "error", report)
        self.assertTrue(
            any("stable_object" in item and "matches" in item for item in report["schema_errors"])
        )

    def test_contradiction_references_are_resolved(self):
        dossier = _clean_dossier()
        second_claim = dict(dossier["attribute_claim"])
        second_claim["attribute_claim_id"] = "AC-2"
        second_claim["value"] = {"value_type": "number", "value": 9.1, "unit": "m2"}
        dossier["attribute_claim"] = [dossier["attribute_claim"], second_claim]
        dossier["contradiction"] = {
            "contradiction_id": "CTR-1",
            "subject_ref": {
                "entity_type": "source_representation",
                "entity_id": "REP-1",
            },
            "attribute_key": "area",
            "claim_refs": ["AC-1", "AC-MISSING"],
            "resolution": "pending_human",
        }

        report = apu.validate_apu_dossier(dossier)
        self.assertEqual(report["result"], "error", report)
        self.assertTrue(
            any("contradiction[0].claim_refs" in item and "AC-MISSING" in item for item in report["reference_errors"]),
            report["reference_errors"],
        )


if __name__ == "__main__":
    unittest.main()
