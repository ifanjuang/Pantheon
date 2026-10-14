from __future__ import annotations

from pathlib import Path
from typing import Any

import jsonschema
import yaml
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas" / "architecture-project-understanding"
CORPUS = (
    ROOT
    / "schemas"
    / "examples"
    / "architecture-project-understanding"
    / "multi_purpose_qualification_corpus.yaml"
)


def _load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _registry() -> Registry:
    shared = Resource.from_contents(
        _load(SCHEMAS / "shared.schema.yaml"),
        default_specification=DRAFT202012,
    )
    return Registry().with_resource(uri="shared.schema.yaml", resource=shared)


def _validate_items(schema_name: str, items: list[dict[str, Any]]) -> None:
    validator = jsonschema.Draft202012Validator(
        _load(SCHEMAS / schema_name),
        format_checker=jsonschema.FormatChecker(),
        registry=_registry(),
    )
    for item in items:
        validator.validate(item)


def _corpus() -> dict[str, Any]:
    return _load(CORPUS)


def test_h5_7_project_world_reuses_only_canonical_project_anatomy_primitives() -> None:
    corpus = _corpus()
    assert corpus["status"] == "qualification_only"
    world = corpus["project_world"]

    _validate_items("stable_object.schema.yaml", world["stable_objects"])
    _validate_items("source_representation.schema.yaml", world["source_representations"])
    _validate_items("attribute_claim.schema.yaml", world["attribute_claims"])
    _validate_items("relation_claim.schema.yaml", world["relation_claims"])

    stable_ids = {item["stable_object_id"] for item in world["stable_objects"]}
    assert stable_ids == {"OBJ-OPENING-017", "OBJ-HVAC-004", "OBJ-SWALE-001"}
    assert not any(
        token in object_id.lower()
        for object_id in stable_ids
        for token in ("economicobject", "thermalobject", "carbonobject", "constructionobject")
    )


def test_h5_7_same_opening_identity_is_reused_across_four_professional_purposes() -> None:
    purposes = {item["purpose_id"]: item for item in _corpus()["purpose_cases"]}
    expected = {
        "architecture_design",
        "economy_quantities",
        "construction_det",
        "thermal_re2020_preparation",
        "acv_carbon_preparation",
    }
    assert set(purposes) == expected

    shared = {
        purpose
        for purpose, item in purposes.items()
        if "OBJ-OPENING-017" in item["stable_object_refs"]
    }
    assert shared == {
        "architecture_design",
        "economy_quantities",
        "construction_det",
        "thermal_re2020_preparation",
        "acv_carbon_preparation",
    }


def test_h5_7_every_purpose_basis_and_conflict_ref_points_to_exact_existing_claim() -> None:
    corpus = _corpus()
    claim_ids = {
        claim["attribute_claim_id"]
        for claim in corpus["project_world"]["attribute_claims"]
    }
    stable_ids = {
        item["stable_object_id"] for item in corpus["project_world"]["stable_objects"]
    }

    for purpose in corpus["purpose_cases"]:
        assert set(purpose["stable_object_refs"]) <= stable_ids
        assert set(purpose["basis_claim_refs"]) <= claim_ids
        for conflict in purpose["conflict_sets"]:
            assert len(conflict) >= 2
            assert set(conflict) <= claim_ids


def test_h5_7_conflicting_widths_are_retained_without_global_winner() -> None:
    corpus = _corpus()
    claims = {
        claim["attribute_claim_id"]: claim
        for claim in corpus["project_world"]["attribute_claims"]
    }
    width_ids = {
        "claim.pdf.opening-width",
        "claim.ifc.opening-width",
        "claim.revit.opening-width",
    }
    values = {
        claims[claim_id]["value"]["value"]
        for claim_id in width_ids
    }
    assert values == {0.90, 0.93}
    assert {claims[claim_id]["source_representation_refs"][0] for claim_id in width_ids} == {
        "rep.pdf.opening-017",
        "rep.ifc.opening-017",
        "rep.revit.opening-017",
    }

    for purpose in corpus["purpose_cases"]:
        if width_ids <= set().union(*(set(group) for group in purpose["conflict_sets"])):
            assert "universal_current_value" in purpose.get("prohibited_inferences", []) or purpose[
                "purpose_id"
            ] == "thermal_re2020_preparation"

    assert "current_value" not in corpus["project_world"]
    assert "selected_value" not in corpus["project_world"]


def test_h5_7_document_currentness_stays_purpose_specific_and_is_not_project_truth() -> None:
    currentness = {
        item["purpose"]: item for item in _corpus()["document_currentness_examples"]
    }
    assert currentness["latest_received"] == {
        "document_ref": "document:dpgf-menuiseries",
        "purpose": "latest_received",
        "posture": "resolved",
        "version_ref": "revision:C",
        "basis_refs": ["receipt:C"],
    }
    assert currentness["current_for_coordination"]["version_ref"] == "revision:B"
    assert currentness["current_contractual"]["posture"] == "unresolved"
    assert "version_ref" not in currentness["current_contractual"]
    assert currentness["latest_received"]["version_ref"] != currentness[
        "current_for_coordination"
    ]["version_ref"]

    economy = next(
        item for item in _corpus()["purpose_cases"] if item["purpose_id"] == "economy_quantities"
    )
    assert "contractual_currentness_from_latest_received" in economy["prohibited_inferences"]


def test_h5_7_economy_det_thermal_and_acv_boundaries_remain_explicit() -> None:
    purposes = {item["purpose_id"]: item for item in _corpus()["purpose_cases"]}

    assert {"adopted_dpgf_quantity", "payable_quantity"} <= set(
        purposes["economy_quantities"]["missing_inputs"]
    )
    assert {"verified", "compliant", "received", "reservation_free"} <= set(
        purposes["construction_det"]["prohibited_inferences"]
    )
    assert {"validated_input", "regulatory_compliance"} <= set(
        purposes["thermal_re2020_preparation"]["prohibited_inferences"]
    )
    assert {"specified_product", "fdes_applicable", "acv_approved"} <= set(
        purposes["acv_carbon_preparation"]["prohibited_inferences"]
    )


def test_h5_7_group_source_assertion_is_not_duplicated_to_landscape_object() -> None:
    corpus = _corpus()
    claim = next(
        item
        for item in corpus["project_world"]["attribute_claims"]
        if item["attribute_claim_id"] == "claim.cctp.swale-capacity-group"
    )
    assert claim["subject_ref"] == {
        "entity_type": "source_representation",
        "entity_id": "rep.cctp.swale-group",
    }
    assert claim["subject_ref"]["entity_id"] != "OBJ-SWALE-001"
    assert "not duplicated" in claim["notes"]


def test_h5_7_fixture_grants_no_professional_or_external_authority() -> None:
    authority = _corpus()["authority"]
    assert authority
    assert set(authority.values()) == {False}

    prohibited = {
        value
        for purpose in _corpus()["purpose_cases"]
        for value in purpose["prohibited_inferences"]
    }
    assert {
        "payable_quantity",
        "regulatory_compliance",
        "acv_approved",
        "received",
    } <= prohibited
