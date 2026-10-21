"""Read-only tests for the relation-profile check in the APU validator.

They validate fictional candidate dossiers against the governed relation
profile architecture@1. A declared relation type is governable, not true,
admitted, Evidence or approved. Nothing here executes, persists or canonizes.
"""

import copy
import json
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

    def test_non_string_relation_type_is_a_schema_error_not_a_crash(self):
        report = apu.validate_apu_dossier(
            _dossier(_relation("RC-1", "DOOR-1", ["architecture.opens_to"], "ROOM-1"))
        )
        self.assertEqual(report["result"], "error")
        self.assertTrue(report["schema_errors"], report)
        self.assertEqual(report["vocabulary_errors"], [])

    def test_non_mapping_requirement_parts_do_not_crash(self):
        dossier = _dossier()
        dossier["requirement"] = {
            "requirement_id": "REQ-1",
            "source": "DOC-CCTP",
            "requirement_kind": "relation",
            "target": "ROOM-1",
            "constraint": ["must_relate_to"],
            "source_authority": "project_working_document",
            "proof_status": "candidate",
        }
        report = apu.validate_apu_dossier(dossier)
        self.assertEqual(report["result"], "error")
        self.assertTrue(report["schema_errors"], report)

    def test_candidate_relation_type_in_requirement_yields_review_note(self):
        dossier = _dossier()
        dossier["requirement"] = {
            "requirement_id": "REQ-1",
            "source": {"source_type": "document", "source_ref": "DOC-CCTP"},
            "requirement_kind": "relation",
            "target": {"entity_ref": {"entity_type": "stable_object", "entity_id": "WALL-1"}},
            "constraint": {
                "operator": "must_relate_to",
                "relation_type": "architecture.separates",
                "related_target": {
                    "entity_ref": {"entity_type": "stable_object", "entity_id": "ROOM-1"}
                },
            },
            "source_authority": "project_working_document",
            "proof_status": "candidate",
        }
        report = apu.validate_apu_dossier(dossier)
        self.assertEqual(report["result"], "ok", report)
        self.assertTrue(
            any("constraint: relation type 'architecture.separates' is still candidate" in item
                for item in report["gate"]["human_decisions_required"]),
            report["gate"],
        )

    def test_deprecated_relation_type_is_rejected_with_its_replacement(self):
        profile = apu.load_relation_profile()
        for entry in profile["entries"]:
            if entry["id"] == "architecture.connects_via":
                entry["status"] = "deprecated"
                entry["replaced_by"] = "architecture.opens_to"
        errors, notes = apu.relation_profile_findings(
            profile, relation_type="architecture.connects_via", label="rc"
        )
        self.assertEqual(notes, [])
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("is deprecated in architecture@1; use 'architecture.opens_to'", errors[0])

    def test_building_state_is_not_admitted_on_identity_relations(self):
        errors, _notes = apu.relation_profile_findings(
            apu.load_relation_profile(),
            relation_type="identity.replaced_by",
            qualifier={"ouvrage_state": "existing"},
            label="rc",
        )
        self.assertEqual(errors, ["rc.qualifier.ouvrage_state is not admitted for 'identity.replaced_by'"])

    def test_family_check_is_skipped_for_objects_outside_the_dossier(self):
        report = apu.validate_apu_dossier(
            _dossier(_relation("RC-1", "DOOR-1", "architecture.opens_to", "SO-ELSEWHERE"))
        )
        self.assertEqual(report["vocabulary_errors"], [])

    def test_mislabelled_entity_type_is_a_reference_error(self):
        dossier = _dossier(_relation("RC-1", "DOOR-1", "architecture.opens_to", "REP-1"))
        dossier["source_representation"] = {
            "representation_id": "REP-1",
            "project_ref": "PRJ-1",
            "source_artifact_ref": "SRC-1",
            "source_kind": "drawing",
            "identifiers": [{"scheme": "drawing.fragment", "value": "room-1"}],
            "observed_at": "2026-08-07T12:00:00Z",
            "binding_ref": "binding.drawing.fixture",
            "adapter_version": "0.2-test",
            "freshness_token": "fixture-revision-1",
            "proof_status": "candidate",
        }
        report = apu.validate_apu_dossier(dossier)
        self.assertEqual(report["result"], "error")
        self.assertFalse(report["gate"]["canonical_emission_allowed"])
        self.assertTrue(
            any("declares entity_type 'stable_object' but 'REP-1' is source_representation[0]"
                in item for item in report["reference_errors"]),
            report["reference_errors"],
        )

    def test_duplicate_relation_ids_fail_closed(self):
        profile = apu.load_relation_profile()
        profile["entries"].append(dict(profile["entries"][0]))
        with mock.patch.object(apu, "read_repo_text", return_value=json.dumps(profile)):
            report = apu.validate_apu_dossier(
                _dossier(_relation("RC-1", "DOOR-1", "architecture.opens_to", "ROOM-1"))
            )
        self.assertEqual(report["result"], "error")
        self.assertTrue(
            any("duplicate relation ids: identity.represents" in item
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
