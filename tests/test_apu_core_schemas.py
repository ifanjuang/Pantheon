"""Contract tests for the Project Anatomy / APU V0.2 core primitives.

These tests are validation-only. They execute no adapter, workflow, approval,
project write or external effect.
"""

from __future__ import annotations

import copy
from pathlib import Path

import jsonschema
import pytest
import yaml
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / "architecture-project-understanding"
EXAMPLE_DIR = ROOT / "schemas" / "examples" / "architecture-project-understanding"

PAIRS = {
    "shared.schema.yaml": "shared.example.yaml",
    "stable_object.schema.yaml": "stable_object.example.yaml",
    "source_representation.schema.yaml": "source_representation.example.yaml",
    "attribute_claim.schema.yaml": "attribute_claim.example.yaml",
    "relation_claim.schema.yaml": "relation_claim.example.yaml",
    "observation_bundle.schema.yaml": "observation_bundle.example.yaml",
    "derivation.schema.yaml": "derivation.example.yaml",
    "requirement.schema.yaml": "requirement.example.yaml",
}


def _load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict), f"{path} must contain a YAML mapping"
    return value


def _registry() -> Registry:
    registry = Registry()
    for name in (
        "shared.schema.yaml",
        "source_representation.schema.yaml",
        "attribute_claim.schema.yaml",
        "relation_claim.schema.yaml",
    ):
        registry = registry.with_resource(
            uri=name,
            resource=Resource.from_contents(
                _load(SCHEMA_DIR / name),
                default_specification=DRAFT202012,
            ),
        )
    return registry


def _validator(schema_name: str) -> jsonschema.Draft202012Validator:
    schema = _load(SCHEMA_DIR / schema_name)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
        registry=_registry(),
    )


def test_v02_core_examples_validate() -> None:
    for schema_name, example_name in PAIRS.items():
        _validator(schema_name).validate(_load(EXAMPLE_DIR / example_name))


def test_stable_object_is_identity_only() -> None:
    example = _load(EXAMPLE_DIR / "stable_object.example.yaml")
    validator = _validator("stable_object.schema.yaml")

    for forbidden_field, value in (
        ("kind", "opening"),
        ("proof_status", "candidate"),
        ("matches", []),
        ("source_artifact_id", "SRC-1"),
    ):
        broken = copy.deepcopy(example)
        broken[forbidden_field] = value
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(broken)


def test_source_representation_does_not_require_identity_match() -> None:
    example = _load(EXAMPLE_DIR / "source_representation.example.yaml")
    assert "stable_object_id" not in example
    assert "match" not in example
    _validator("source_representation.schema.yaml").validate(example)


def test_attribute_claim_carries_no_approval_or_use_grant() -> None:
    example = _load(EXAMPLE_DIR / "attribute_claim.example.yaml")
    validator = _validator("attribute_claim.schema.yaml")

    for forbidden_field, value in (
        ("approval_state", "approved_for_internal_use"),
        ("allowed_use", ["internal_review"]),
        ("forbidden_use", ["contractual_action"]),
    ):
        broken = copy.deepcopy(example)
        broken[forbidden_field] = value
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(broken)


def test_identity_represents_has_typed_endpoints() -> None:
    example = _load(EXAMPLE_DIR / "relation_claim.example.yaml")
    validator = _validator("relation_claim.schema.yaml")
    validator.validate(example)

    wrong_subject = copy.deepcopy(example)
    wrong_subject["subject_ref"]["entity_type"] = "stable_object"
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(wrong_subject)

    wrong_object = copy.deepcopy(example)
    wrong_object["object_ref"]["entity_type"] = "source_representation"
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(wrong_object)


def test_requirement_is_prescriptive_and_source_generic() -> None:
    example = _load(EXAMPLE_DIR / "requirement.example.yaml")
    validator = _validator("requirement.schema.yaml")
    validator.validate(example)

    ids = copy.deepcopy(example)
    ids["requirement_id"] = "REQ-IDS-FIRE-RATING"
    ids["source"] = {
        "source_type": "ids",
        "source_ref": "IDS-ARCH-001",
        "source_artifact_ref": "SRC-IDS-001",
    }
    ids["requirement_kind"] = "attribute"
    ids["target"] = {
        "selector": {
            "object_family": "element",
            "classification_scheme": "IFC4.3",
            "classification_value": "IfcDoor",
        }
    }
    ids["constraint"] = {
        "operator": "must_exist",
        "attribute_key": "performance.fire_rating",
    }
    validator.validate(ids)


def test_derivation_may_produce_relation_claims() -> None:
    example = _load(EXAMPLE_DIR / "derivation.example.yaml")
    example["derivation_id"] = "DERIV-SPATIAL-001"
    example["produces"] = [
        {"claim_type": "relation_claim", "claim_id": "REL-SPATIAL-001"}
    ]
    _validator("derivation.schema.yaml").validate(example)


def test_apu_entity_ref_is_closed_to_the_v02_project_world() -> None:
    shared = _load(SCHEMA_DIR / "shared.schema.yaml")
    wrapper = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$defs": shared["$defs"],
        "$ref": "#/$defs/apu_entity_ref",
    }
    validator = jsonschema.Draft202012Validator(wrapper)
    for entity_type in ("stable_object", "source_representation", "requirement", "program"):
        validator.validate({"entity_type": entity_type, "entity_id": "REF-001"})

    for forbidden_type in ("information", "decision", "work_issue", "project_claim", "evidence"):
        with pytest.raises(jsonschema.ValidationError):
            validator.validate({"entity_type": forbidden_type, "entity_id": "REF-001"})


def test_v01_parallel_carriers_are_not_accepted_by_v02_core_schemas() -> None:
    attribute = _load(EXAMPLE_DIR / "attribute_claim.example.yaml")
    attribute["about"] = {
        "stable_object_id": "OBJ-001",
        "attribute": "geometry.width",
    }
    with pytest.raises(jsonschema.ValidationError):
        _validator("attribute_claim.schema.yaml").validate(attribute)

    requirement = _load(EXAMPLE_DIR / "requirement.example.yaml")
    requirement["from_program"] = "PRG-LEGACY"
    with pytest.raises(jsonschema.ValidationError):
        _validator("requirement.schema.yaml").validate(requirement)

    requirement = _load(EXAMPLE_DIR / "requirement.example.yaml")
    requirement["target"] = {"space_group_id": "GROUP-LEGACY"}
    with pytest.raises(jsonschema.ValidationError):
        _validator("requirement.schema.yaml").validate(requirement)
