"""Validation tests for non-authoritative fragment qualification candidates."""

from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "fragment_qualification_candidate.schema.yaml"
EXAMPLE_PATH = ROOT / "schemas" / "examples" / "fragment_qualification_candidate.example.yaml"


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


def test_example_validates(validator, example) -> None:
    validator.validate(example)


def test_qualification_requires_a_semantic_proposal(validator, example) -> None:
    broken = deepcopy(example)
    qualification = broken["qualifications"][0]
    for field in (
        "topic",
        "discipline",
        "representation_kind",
        "project_state",
        "variant_ref",
        "coverage_refs",
    ):
        qualification.pop(field, None)

    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)


def test_rationale_and_certainty_are_required(validator, example) -> None:
    for field in ("rationale", "certainty"):
        broken = deepcopy(example)
        del broken["qualifications"][0][field]
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(broken)


def test_candidate_cannot_claim_authority(validator, example) -> None:
    for field in example["authority"]:
        broken = deepcopy(example)
        broken["authority"][field] = True
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(broken)


def test_candidate_cannot_emit_reviewed_or_approved_status(validator, example) -> None:
    for status in ("reviewed", "approved"):
        broken = deepcopy(example)
        broken["status"] = status
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(broken)


def test_producer_capability_is_stable(validator, example) -> None:
    broken = deepcopy(example)
    broken["producer"]["capability"] = "automatic-project-truth"

    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)
