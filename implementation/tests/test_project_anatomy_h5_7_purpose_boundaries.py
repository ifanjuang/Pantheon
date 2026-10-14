from __future__ import annotations

from mvp_vertical import project_anatomy_projection, project_document_currentness


def _shared_world() -> dict:
    return {
        "project_ref": "project-h57",
        "model_version": 2,
        "model_authority_ref": "contracts@h57",
        "owner_revision": 1,
        "stable_objects": [
            {
                "object_id": "OBJ-OPENING-017",
                "stable_object": {
                    "stable_object_id": "OBJ-OPENING-017",
                    "project_ref": "project-h57",
                    "object_family": "element",
                    "nomenclature": {"display_name": "Baie 017"},
                },
                "revision": 1,
            }
        ],
        "source_representations": [
            {
                "representation_id": "rep.pdf.p12",
                "project_ref": "project-h57",
                "source_artifact_ref": "plan.pdf",
                "source_version_ref": "plan-B",
                "source_kind": "drawing",
                "observed_at": "2026-08-09T09:00:00Z",
                "binding_ref": "drawing.observe",
                "adapter_version": "1.0.0",
                "freshness_token": "sha256:plan-b",
                "proof_status": "candidate",
                "identifiers": [{"scheme": "drawing.local_label", "value": "P12"}],
            },
            {
                "representation_id": "rep.ifc.door",
                "project_ref": "project-h57",
                "source_artifact_ref": "model.ifc",
                "source_version_ref": "ifc-42",
                "source_kind": "ifc",
                "observed_at": "2026-08-09T09:10:00Z",
                "binding_ref": "ifc.observe",
                "adapter_version": "1.0.0",
                "freshness_token": "sha256:ifc-42",
                "proof_status": "candidate",
                "identifiers": [{"scheme": "ifc.guid", "value": "IFC-GUID-17"}],
            },
        ],
        "attribute_claims": [
            {
                "attribute_claim_id": "claim.pdf.width",
                "subject_ref": {"entity_type": "stable_object", "entity_id": "OBJ-OPENING-017"},
                "attribute_key": "architecture.width",
                "value": {"value_type": "number", "value": 0.90, "unit": "m"},
                "assertion_mode": "observed",
                "source_authority": "project_working_document",
                "proof_status": "requires_more_evidence",
                "source_representation_refs": ["rep.pdf.p12"],
            },
            {
                "attribute_claim_id": "claim.ifc.width",
                "subject_ref": {"entity_type": "stable_object", "entity_id": "OBJ-OPENING-017"},
                "attribute_key": "architecture.width",
                "value": {"value_type": "number", "value": 0.93, "unit": "m"},
                "assertion_mode": "observed",
                "source_authority": "model_interpretation_candidate",
                "proof_status": "requires_more_evidence",
                "source_representation_refs": ["rep.ifc.door"],
            },
            {
                "attribute_claim_id": "claim.ifc.quantity",
                "subject_ref": {"entity_type": "stable_object", "entity_id": "OBJ-OPENING-017"},
                "attribute_key": "economy.quantity",
                "value": {"value_type": "number", "value": 1, "unit": "unit"},
                "assertion_mode": "derived",
                "source_authority": "model_interpretation_candidate",
                "proof_status": "candidate",
                "source_representation_refs": ["rep.ifc.door"],
            },
            {
                "attribute_claim_id": "claim.thermal.uw",
                "subject_ref": {"entity_type": "stable_object", "entity_id": "OBJ-OPENING-017"},
                "attribute_key": "thermal.uw",
                "value": {"value_type": "number", "value": 1.3, "unit": "W/m2.K"},
                "assertion_mode": "proposed",
                "source_authority": "project_working_document",
                "proof_status": "requires_more_evidence",
                "source_representation_refs": ["rep.pdf.p12"],
            },
        ],
        "relation_claims": [
            {
                "relation_claim_id": "identity.pdf",
                "subject_ref": {"entity_type": "source_representation", "entity_id": "rep.pdf.p12"},
                "relation_type": "identity.represents",
                "object_ref": {"entity_type": "stable_object", "entity_id": "OBJ-OPENING-017"},
                "assertion_mode": "human_asserted",
                "source_authority": "project_working_document",
                "proof_status": "accepted_as_support",
            },
            {
                "relation_claim_id": "identity.ifc",
                "subject_ref": {"entity_type": "source_representation", "entity_id": "rep.ifc.door"},
                "relation_type": "identity.represents",
                "object_ref": {"entity_type": "stable_object", "entity_id": "OBJ-OPENING-017"},
                "assertion_mode": "human_asserted",
                "source_authority": "project_working_document",
                "proof_status": "accepted_as_support",
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


def test_one_project_identity_carries_multi_purpose_material_without_global_winner() -> None:
    projection = project_anatomy_projection.build_project_anatomy_projection(
        _shared_world(), model_doctrine_ref="doctrine@h57"
    )
    obj = projection["structure"]["objects"][0]
    assert obj["object_id"] == "OBJ-OPENING-017"
    assert set(obj["source_representation_refs"]) == {"rep.pdf.p12", "rep.ifc.door"}

    widths = [
        claim["value"]["value"]
        for claim in obj["attribute_claims"]
        if claim["attribute_key"] == "architecture.width"
    ]
    assert widths == [0.90, 0.93]
    assert {claim["attribute_key"] for claim in obj["attribute_claims"]} >= {
        "architecture.width",
        "economy.quantity",
        "thermal.uw",
    }

    forbidden = {"current_value", "accepted_quantity", "payable_quantity", "compliant", "received", "approved"}
    assert forbidden.isdisjoint(obj)
    assert projection["authority"]["authorization_inferred"] is False
    assert projection["authority"]["absence_inferred"] is False


def test_project_anatomy_does_not_reuse_document_currentness_as_object_truth() -> None:
    projection = project_anatomy_projection.build_project_anatomy_projection(
        _shared_world(), model_doctrine_ref="doctrine@h57"
    )
    assert "purpose" not in projection
    assert "resolution_status" not in projection
    assert "current_value" not in projection
    assert project_document_currentness.AUTHORITY == {
        "is_evidence": False,
        "is_decision": False,
        "is_approval": False,
        "is_proof": False,
        "is_contractual_authority": False,
        "is_execution_authority": False,
        "changes_project_truth": False,
    }


def test_runtime_or_calculation_success_is_not_encoded_as_professional_acceptance() -> None:
    projection = project_anatomy_projection.build_project_anatomy_projection(
        _shared_world(), model_doctrine_ref="doctrine@h57"
    )
    thermal = next(
        claim for claim in projection["attribute_claims"] if claim["attribute_key"] == "thermal.uw"
    )
    assert thermal["proof_status"] == "requires_more_evidence"
    assert thermal["assertion_mode"] == "proposed"
    assert projection["authority"]["authorization_inferred"] is False


def test_h57_does_not_require_a_purpose_engine_or_metier_specific_identity() -> None:
    assert not hasattr(project_anatomy_projection, "PURPOSE_ENGINE")
    assert not hasattr(project_anatomy_projection, "CURRENT_VALUE")
    assert not hasattr(project_anatomy_projection, "ArchitectureObject")
    assert not hasattr(project_anatomy_projection, "EconomicObject")
    assert not hasattr(project_anatomy_projection, "ThermalObject")
    assert not hasattr(project_anatomy_projection, "CarbonObject")
