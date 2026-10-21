"""Read-only tests for the relation-profile check in the APU validator.

They validate fictional candidate dossiers against the governed relation
profile architecture@1. A declared relation type is governable, not true,
admitted, Evidence or approved. Nothing here executes, persists or canonizes.
"""

import copy
import os
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("PANTHEON_REPO_PATH", str(ROOT))

from pantheon_mcp import apu  # noqa: E402


def _object(object_id: str, family: str, name: str) -> dict:
    return {
        "stable_object_id": object_id,
        "project_ref": "PRJ-1",
        "object_family": family,
        "nomenclature": {"display_name": name},
    }


def _relation(claim_id: str, subject: str, relation_type: str, obj: str, **extra) -> dict:
    claim = {
        "relation_claim_id": claim_id,
        "subject_ref": {"entity_type": "stable_object", "entity_id": subject},
        "relation_type": relation_type,
        "object_ref": {"entity_type": "stable_object", "entity_id": obj},
        "assertion_mode": "observed",
        "source_authority": "project_working_document",
        "proof_status": "candidate",
    }
    claim.update(extra)
    return claim


def _dossier(*relations: dict) -> dict:
    return {
        "stable_object": [
            _object("ROOM-1", "spatial", "Chambre 1"),
            _object("ROOM-2", "spatial", "Séjour"),
            _object("WALL-1", "element", "Cloison C1"),
            _object("DOOR-1", "element", "Porte P1"),
        ],
        "relation_claim": list(relations),
    }


class TestRelationProfileValidation(unittest.TestCase):
    def test_active_relation_type_is_ok_without_review_note(self):
        report = apu.validate_apu_dossier(
            _dossier(_relation("RC-1", "DOOR-1", "architecture.opens_to", "ROOM-1"))
        )
        self.assertEqual(report["result"], "ok", report)
        self.assertEqual(report["vocabulary_errors"], [])
        self.assertEqual(report["gate"]["human_decisions_required"], [])

    def test_undeclared_relation_type_is_rejected(self):
        report = apu.validate_apu_dossier(
            _dossier(_relation("RC-1", "DOOR-1", "opens_into", "ROOM-1"))
        )
        self.assertEqual(report["result"], "error")
        self.assertTrue(
            any("'opens_into' is not declared in architecture@1" in item
                for item in report["vocabulary_errors"]),
            report["vocabulary_errors"],
        )
        self.assertFalse(report["gate"]["canonical_emission_allowed"])

    def test_candidate_relation_type_passes_with_review_note(self):
        report = apu.validate_apu_dossier(
            _dossier(_relation("RC-1", "WALL-1", "architecture.separates", "ROOM-1"))
        )
        self.assertEqual(report["result"], "ok", report)
        self.assertTrue(
            any("'architecture.separates' is still candidate" in item
                for item in report["gate"]["human_decisions_required"]),
            report["gate"],
        )

    def test_object_family_outside_the_profile_is_rejected(self):
        report = apu.validate_apu_dossier(
            _dossier(_relation("RC-1", "ROOM-2", "architecture.opens_to", "ROOM-1"))
        )
        self.assertEqual(report["result"], "error")
        self.assertTrue(
            any("subject_ref object_family 'spatial'" in item
                for item in report["vocabulary_errors"]),
            report["vocabulary_errors"],
        )

    def test_entity_type_outside_the_profile_is_rejected(self):
        report = apu.validate_apu_dossier(
            _dossier(_relation("RC-1", "WALL-1", "identity.represents", "ROOM-1"))
        )
        self.assertEqual(report["result"], "error")
        self.assertTrue(
            any("subject_ref.entity_type 'stable_object'" in item
                for item in report["vocabulary_errors"]),
            report["vocabulary_errors"],
        )

    def test_controlled_qualifier_values_are_checked(self):
        good = _relation(
            "RC-1", "ROOM-1", "spatial.adjacent_to", "ROOM-2",
            qualifier={"ouvrage_state": "existing"},
        )
        bad = copy.deepcopy(good)
        bad["relation_claim_id"] = "RC-2"
        bad["qualifier"] = {"ouvrage_state": "after_works"}
        report = apu.validate_apu_dossier(_dossier(good, bad))
        self.assertEqual(report["result"], "error")
        self.assertEqual(len(report["vocabulary_errors"]), 1, report["vocabulary_errors"])
        self.assertIn("'after_works' is outside", report["vocabulary_errors"][0])

    def test_controlled_qualifier_not_admitted_for_the_relation_is_rejected(self):
        report = apu.validate_apu_dossier(
            _dossier(
                _relation(
                    "RC-1", "ROOM-1", "spatial.adjacent_to", "ROOM-2",
                    qualifier={"junction_type": "tee"},
                )
            )
        )
        self.assertEqual(report["result"], "error")
        self.assertTrue(
            any("qualifier.junction_type is not admitted" in item
                for item in report["vocabulary_errors"]),
            report["vocabulary_errors"],
        )

    def test_uncontrolled_qualifier_keys_stay_free(self):
        report = apu.validate_apu_dossier(
            _dossier(
                _relation(
                    "RC-1", "DOOR-1", "architecture.opens_to", "ROOM-1",
                    qualifier={"side": "bedroom_side"},
                )
            )
        )
        self.assertEqual(report["result"], "ok", report)

    def test_requirement_relation_type_is_checked(self):
        dossier = _dossier()
        dossier["requirement"] = {
            "requirement_id": "REQ-1",
            "source": {"source_type": "document", "source_ref": "DOC-CCTP"},
            "requirement_kind": "relation",
            "target": {"entity_ref": {"entity_type": "stable_object", "entity_id": "ROOM-1"}},
            "constraint": {
                "operator": "must_relate_to",
                "relation_type": "spatial.next_to",
                "related_target": {
                    "entity_ref": {"entity_type": "stable_object", "entity_id": "ROOM-2"}
                },
            },
            "source_authority": "project_working_document",
            "proof_status": "candidate",
        }
        report = apu.validate_apu_dossier(dossier)
        self.assertEqual(report["result"], "error")
        self.assertTrue(
            any("constraint.relation_type 'spatial.next_to'" in item
                for item in report["vocabulary_errors"]),
            report["vocabulary_errors"],
        )

    def test_missing_profile_fails_closed(self):
        with mock.patch.object(apu, "RELATION_PROFILE_PATH", "registries/missing.registry.json"):
            report = apu.validate_apu_dossier(
                _dossier(_relation("RC-1", "DOOR-1", "architecture.opens_to", "ROOM-1"))
            )
        self.assertEqual(report["result"], "error")
        self.assertTrue(
            any("relation profile unavailable" in item for item in report["vocabulary_errors"]),
            report["vocabulary_errors"],
        )


if __name__ == "__main__":
    unittest.main()
