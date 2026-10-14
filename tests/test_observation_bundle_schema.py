"""Executable contract tests for candidate-only Observation Bundles."""

from __future__ import annotations

import copy
from pathlib import Path

import jsonschema
import pytest
import yaml
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas" / "architecture-project-understanding"
EXAMPLE = (
    ROOT
    / "schemas"
    / "examples"
    / "architecture-project-understanding"
    / "observation_bundle.example.yaml"
)


def _load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
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
                _load(SCHEMAS / name),
                default_specification=DRAFT202012,
            ),
        )
    return registry


def _validator() -> jsonschema.Draft202012Validator:
    schema = _load(SCHEMAS / "observation_bundle.schema.yaml")
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
        registry=_registry(),
    )


def _example() -> dict:
    return _load(EXAMPLE)


def test_complete_simple_source_observation_validates() -> None:
    bundle = _example()
    _validator().validate(bundle)
    assert bundle["coverage"]["absence_inference_allowed"] is True


@pytest.mark.parametrize("completeness", ["partial_for_declared_scope", "unknown"])
def test_non_complete_coverage_cannot_authorize_absence(completeness: str) -> None:
    bundle = _example()
    bundle["coverage"]["completeness"] = completeness
    bundle["coverage"]["absence_inference_allowed"] = False
    _validator().validate(bundle)

    bundle["coverage"]["absence_inference_allowed"] = True
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(bundle)


@pytest.mark.parametrize(
    "outcome", ["withheld", "blocked", "refused", "failed", "cancelled", "rolled_back"]
)
def test_non_successful_outcome_cannot_authorize_absence(outcome: str) -> None:
    bundle = _example()
    bundle["operational_outcome"] = outcome
    bundle["coverage"]["completeness"] = "complete_for_declared_scope"
    bundle["coverage"]["absence_inference_allowed"] = True
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(bundle)

    bundle["coverage"]["absence_inference_allowed"] = False
    _validator().validate(bundle)


def test_unresolved_representation_needs_no_stable_object() -> None:
    bundle = _example()
    bundle["attribute_claim_candidates"] = []
    assert all(
        "stable_object" not in representation
        for representation in bundle["source_representations"]
    )
    _validator().validate(bundle)


def test_conflicting_observations_remain_separate_candidates() -> None:
    bundle = _example()
    second = copy.deepcopy(bundle["attribute_claim_candidates"][0])
    second["attribute_claim_id"] = "claim.revit.room-number.002"
    second["value"]["value"] = "A-001"
    bundle["attribute_claim_candidates"].append(second)
    _validator().validate(bundle)
    assert len(bundle["attribute_claim_candidates"]) == 2


def test_identity_represents_remains_typed_and_candidate_only() -> None:
    bundle = _example()
    relation = {
        "relation_claim_id": "relation.identity.room-001",
        "subject_ref": {
            "entity_type": "source_representation",
            "entity_id": "rep.revit.project-a.room-001",
        },
        "relation_type": "identity.represents",
        "object_ref": {
            "entity_type": "stable_object",
            "entity_id": "object.room.001",
        },
        "assertion_mode": "proposed",
        "source_authority": "model_interpretation_candidate",
        "proof_status": "candidate",
        "certainty": "E2",
        "source_representation_refs": ["rep.revit.project-a.room-001"],
    }
    bundle["relation_claim_candidates"] = [relation]
    _validator().validate(bundle)

    relation["object_ref"]["entity_type"] = "source_representation"
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(bundle)


def test_prescriptive_material_cannot_masquerade_as_observed_claim() -> None:
    bundle = _example()
    bundle["attribute_claim_candidates"][0]["assertion_mode"] = "prescriptive"
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(bundle)

    bundle = _example()
    bundle["requirements"] = []
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(bundle)


def test_gap_and_withheld_states_need_no_synthetic_claim() -> None:
    bundle = _example()
    bundle["attribute_claim_candidates"] = []
    bundle["operational_outcome"] = "withheld"
    bundle["coverage"]["absence_inference_allowed"] = False
    bundle["gaps"] = [{"code": "missing.volume"}]
    bundle["withheld"] = [
        {
            "code": "volume.not_computed",
            "subject_refs": ["rep.revit.project-a.room-001"],
        }
    ]
    _validator().validate(bundle)


@pytest.mark.parametrize("outcome", ["failed", "refused"])
def test_non_success_outcomes_keep_zero_apu_authority(outcome: str) -> None:
    bundle = _example()
    bundle["operational_outcome"] = outcome
    bundle.pop("freshness_token")
    bundle["source_representations"] = []
    bundle["attribute_claim_candidates"] = []
    bundle["relation_claim_candidates"] = []
    bundle["coverage"] = {
        "completeness": "unknown",
        "observed_scope": {"document_refs": ["revit-document:model-a"]},
        "excluded_reasons": ["operation_did_not_complete"],
        "absence_inference_allowed": False,
    }
    _validator().validate(bundle)
    assert set(bundle["authority"].values()) == {False}


def test_multi_granularity_does_not_force_one_stable_object_per_occurrence() -> None:
    bundle = _example()
    component = copy.deepcopy(bundle["source_representations"][0])
    component["representation_id"] = "rep.revit.project-a.component-001"
    component["identifiers"][0]["value"] = "component-unique-id-001"
    component["context"]["native_context"]["category"] = "OST_Doors"
    bundle["source_representations"].append(component)
    bundle["scope"]["categories"].append("OST_Doors")
    bundle["coverage"]["observed_scope"]["categories"].append("OST_Doors")
    _validator().validate(bundle)
    assert bundle["relation_claim_candidates"] == []


def test_exact_source_version_and_digest_are_retained() -> None:
    bundle = _example()
    _validator().validate(bundle)
    assert bundle["basis"]["source_version_refs"] == [
        "snapshot.revit.model-a.00042"
    ]
    assert bundle["basis"]["exact_digests"][0]["digest"] == "sha256:590910f2"


def test_candidate_primitives_and_snake_case_are_enforced() -> None:
    bundle = _example()
    bundle["source_representations"][0]["proof_status"] = "accepted_as_support"
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(bundle)

    bundle = _example()
    bundle["observationBundleId"] = bundle.pop("observation_bundle_id")
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(bundle)

    bundle = _example()
    context = bundle["source_representations"][0]["context"]
    context["category"] = context["native_context"]["category"]
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(bundle)
