from __future__ import annotations

import pytest

from mvp_vertical.project_anatomy_projection import build_project_anatomy_projection


def _anatomy() -> dict:
    return {
        "project_ref": "project-1",
        "model_version": 2,
        "model_authority_ref": "contracts@baseline",
        "owner_revision": 7,
        "stable_objects": [
            {
                "object_id": "space-1",
                "stable_object": {
                    "stable_object_id": "space-1",
                    "project_ref": "project-1",
                    "object_family": "spatial",
                    "nomenclature": {"display_name": "Séjour", "internal_code": "S01"},
                },
                "revision": 3,
            },
            {
                "object_id": "door-1",
                "stable_object": {
                    "stable_object_id": "door-1",
                    "project_ref": "project-1",
                    "object_family": "element",
                    "nomenclature": {"display_name": "Porte séjour"},
                },
                "revision": 1,
            },
        ],
        "source_representations": [
            {
                "representation_id": "revit-1",
                "project_ref": "project-1",
                "source_artifact_ref": "model.rvt",
                "source_kind": "revit",
                "observed_at": "2026-08-08T10:00:00Z",
                "binding_ref": "revit.document.snapshot.v1",
                "adapter_version": "0.1.0",
                "freshness_token": "r1",
                "proof_status": "source_complete_for_task",
                "identifiers": [{"scheme": "revit.unique_id", "value": "abc"}],
            },
            {
                "representation_id": "photo-1",
                "project_ref": "project-1",
                "source_artifact_ref": "site-photo.jpg",
                "source_kind": "photo",
                "observed_at": "2026-08-08T11:00:00Z",
                "binding_ref": "photo.observation.v1",
                "adapter_version": "0.1.0",
                "freshness_token": "p1",
                "proof_status": "source_incomplete",
                "identifiers": [{"scheme": "file", "value": "site-photo.jpg"}],
                "limitations": ["single viewpoint"],
            },
        ],
        "attribute_claims": [
            {
                "attribute_claim_id": "claim-width",
                "subject_ref": {"entity_type": "stable_object", "entity_id": "door-1"},
                "attribute_key": "architecture.width",
                "value": {"value_type": "number", "value": 0.9, "unit": "m"},
                "assertion_mode": "observed",
                "source_authority": "project_working_document",
                "proof_status": "requires_more_evidence",
                "certainty": "E2",
                "source_representation_refs": ["revit-1"],
                "validity": {"established_at_phase": "PRO"},
            }
        ],
        "relation_claims": [
            {
                "relation_claim_id": "identity-1",
                "subject_ref": {"entity_type": "source_representation", "entity_id": "revit-1"},
                "relation_type": "identity.represents",
                "object_ref": {"entity_type": "stable_object", "entity_id": "door-1"},
                "assertion_mode": "human_asserted",
                "source_authority": "project_working_document",
                "proof_status": "accepted_as_support",
            },
            {
                "relation_claim_id": "opens-1",
                "subject_ref": {"entity_type": "stable_object", "entity_id": "door-1"},
                "relation_type": "architecture.opens_to",
                "object_ref": {"entity_type": "stable_object", "entity_id": "space-1"},
                "assertion_mode": "observed",
                "source_authority": "project_working_document",
                "proof_status": "accepted_as_support",
                "source_representation_refs": ["revit-1"],
            },
        ],
        "authority": {
            "is_projection": True,
            "is_evidence": False,
            "is_decision": False,
            "authorizes_tasks": False,
            "permits_runtime_writes": False,
        },
    }


def test_projection_exposes_known_sources_uncertainty_and_unmapped_without_inventing_coverage() -> None:
    projection = build_project_anatomy_projection(
        _anatomy(),
        model_doctrine_ref="doctrine@baseline",
    )

    assert projection["model_authority_ref"] == "contracts@baseline"
    assert projection["model_doctrine_ref"] == "doctrine@baseline"
    assert projection["summary"] == {
        "stable_object_count": 2,
        "source_representation_count": 2,
        "attribute_claim_count": 1,
        "relation_claim_count": 2,
        "unmapped_source_representation_count": 1,
        "attention_claim_count": 1,
        "limited_source_count": 1,
    }
    assert [item["representation_id"] for item in projection["unmapped_material"]] == ["photo-1"]
    assert projection["coverage"]["status"] == "not_persisted"
    assert projection["coverage"]["absence_inference_allowed"] is False
    assert projection["structure"]["hierarchy"]["status"] == "not_derived"
    assert projection["authority"]["hierarchy_inferred_without_registered_semantics"] is False
    assert projection["authority"]["authorization_inferred"] is False

    door = next(item for item in projection["structure"]["objects"] if item["object_id"] == "door-1")
    assert door["display_name"] == "Porte séjour"
    assert door["source_representation_refs"] == ["revit-1"]
    assert door["phase_refs"] == ["PRO"]
    assert door["attention_claim_refs"] == ["claim-width"]
    assert projection["relations"][0]["relation_type"] == "architecture.opens_to"


def test_rejected_identity_alignment_does_not_hide_unmapped_source_material() -> None:
    anatomy = _anatomy()
    anatomy["relation_claims"][0]["proof_status"] = "rejected"

    projection = build_project_anatomy_projection(anatomy, model_doctrine_ref="doctrine@baseline")

    unmapped = {item["representation_id"] for item in projection["unmapped_material"]}
    assert unmapped == {"revit-1", "photo-1"}
    assert projection["authority"]["absence_inferred"] is False


@pytest.mark.parametrize("proof_status", ["candidate", "requires_more_evidence"])
def test_unresolved_identity_alignment_does_not_present_source_as_mapped(
    proof_status: str,
) -> None:
    anatomy = _anatomy()
    anatomy["relation_claims"][0]["proof_status"] = proof_status

    projection = build_project_anatomy_projection(anatomy, model_doctrine_ref="doctrine@baseline")

    sources = {item["representation_id"]: item for item in projection["sources"]}
    unmapped = {item["representation_id"] for item in projection["unmapped_material"]}
    assert sources["revit-1"]["mapped_object_refs"] == []
    assert sources["revit-1"]["identity_claims"][0]["proof_status"] == proof_status
    assert unmapped == {"revit-1", "photo-1"}


def test_source_identifiers_and_source_scoped_claims_are_preserved() -> None:
    anatomy = _anatomy()
    source_claim = {
        "attribute_claim_id": "claim-photo-condition",
        "subject_ref": {"entity_type": "source_representation", "entity_id": "photo-1"},
        "attribute_key": "architecture.condition",
        "value": {"value_type": "controlled_label", "value": "damaged"},
        "assertion_mode": "observed",
        "source_authority": "project_working_document",
        "proof_status": "requires_more_evidence",
        "certainty": "E1",
        "source_representation_refs": ["photo-1"],
    }
    anatomy["attribute_claims"].append(source_claim)

    projection = build_project_anatomy_projection(anatomy, model_doctrine_ref="doctrine@baseline")

    sources = {item["representation_id"]: item for item in projection["sources"]}
    photo = sources["photo-1"]
    assert photo["identifiers"] == [{"scheme": "file", "value": "site-photo.jpg"}]
    assert photo["attribute_claims"] == [
        {
            "claim_type": "attribute_claim",
            "claim_id": "claim-photo-condition",
            "subject_ref": {
                "entity_type": "source_representation",
                "entity_id": "photo-1",
            },
            "proof_status": "requires_more_evidence",
            "certainty": "E1",
            "assertion_mode": "observed",
            "source_authority": "project_working_document",
            "source_representation_refs": ["photo-1"],
            "phase_refs": [],
            "attribute_key": "architecture.condition",
            "value": {"value_type": "controlled_label", "value": "damaged"},
        }
    ]
    unmapped = {item["representation_id"]: item for item in projection["unmapped_material"]}
    assert unmapped["photo-1"]["identifiers"] == photo["identifiers"]
    assert projection["attribute_claims"][-1] == photo["attribute_claims"][0]
