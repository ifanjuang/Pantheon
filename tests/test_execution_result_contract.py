"""Validation tests for typed execution results and separate review dispositions."""

from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "execution_result.schema.yaml"
EXAMPLE_PATH = ROOT / "schemas" / "examples" / "execution_result.example.yaml"


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture
def validator() -> jsonschema.Draft202012Validator:
    schema = load_yaml(SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )


@pytest.fixture
def example() -> dict:
    return load_yaml(EXAMPLE_PATH)


def test_execution_result_example_validates(validator, example) -> None:
    validator.validate(example)


def test_execution_requires_at_least_one_typed_result(validator, example) -> None:
    broken = deepcopy(example)
    broken["execution_result"]["results"] = []
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)


def test_result_cannot_claim_project_truth_or_write_authority(validator, example) -> None:
    for field in (
        "is_fact",
        "is_evidence",
        "is_decision",
        "is_memory",
        "is_apu_write",
        "authorizes_external_effect",
    ):
        broken = deepcopy(example)
        broken["execution_result"]["results"][0]["authority"][field] = True
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(broken)


def test_execution_envelope_cannot_claim_authority(validator, example) -> None:
    broken = deepcopy(example)
    broken["execution_result"]["authority"]["is_fact"] = True
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)


def test_choice_clarification_requires_options(validator, example) -> None:
    broken = deepcopy(example)
    del broken["execution_result"]["clarifications"][0]["options"]
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)


def test_needs_clarification_disposition_requires_clarification_ref(validator, example) -> None:
    broken = deepcopy(example)
    del broken["review_dispositions"][1]["clarification_ref"]
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)


def test_review_disposition_cannot_adopt_or_write(validator, example) -> None:
    for field in (
        "adopts_project_truth",
        "writes_apu",
        "admits_evidence",
        "promotes_memory",
    ):
        broken = deepcopy(example)
        broken["review_dispositions"][0]["authority"][field] = True
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(broken)


def test_result_schema_reference_must_be_relative(validator, example) -> None:
    broken = deepcopy(example)
    broken["execution_result"]["results"][0]["schema_ref"] = "/tmp/schema.yaml"
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)
