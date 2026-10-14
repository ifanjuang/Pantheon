"""Validation tests for candidate-only APU mapping adapter results."""

from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest
import yaml
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012


ROOT = Path(__file__).resolve().parents[1]
FAMILY = ROOT / "schemas" / "architecture-project-understanding"
SCHEMA_PATH = FAMILY / "adapter_result.schema.yaml"
EXAMPLE_PATH = ROOT / "schemas" / "examples" / "architecture-project-understanding" / "adapter_result.example.yaml"


def _load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _validator() -> jsonschema.Draft202012Validator:
    schema = _load(SCHEMA_PATH)
    shared = Resource.from_contents(_load(FAMILY / "shared.schema.yaml"), default_specification=DRAFT202012)
    registry = Registry().with_resource(uri="shared.schema.yaml", resource=shared)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema, registry=registry)


def test_example_validates() -> None:
    _validator().validate(_load(EXAMPLE_PATH))


def test_mapping_cannot_claim_apu_write_or_truth() -> None:
    for field in (
        "is_fact",
        "is_evidence",
        "is_decision",
        "is_memory",
        "is_apu_write",
        "authorizes_external_effect",
    ):
        broken = deepcopy(_load(EXAMPLE_PATH))
        broken["authority"][field] = True
        with pytest.raises(jsonschema.ValidationError):
            _validator().validate(broken)


def test_mapping_requires_source_qualification_and_candidate_identity() -> None:
    for field in ("source_qualification_result_ref", "mappings"):
        broken = deepcopy(_load(EXAMPLE_PATH))
        del broken[field]
        with pytest.raises(jsonschema.ValidationError):
            _validator().validate(broken)


def test_match_candidate_uses_existing_apu_reference_without_adopting_it() -> None:
    example = _load(EXAMPLE_PATH)
    candidate = example["mappings"][0]["match_candidates"][0]
    assert candidate["stable_object_ref"] == "space.chambre-r2"
    assert example["authority"]["is_apu_write"] is False
