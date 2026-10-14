"""Validation tests for append-only APU mapping review events."""

from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "architecture-project-understanding" / "mapping_review.schema.yaml"
EXAMPLE_PATH = ROOT / "schemas" / "examples" / "architecture-project-understanding" / "mapping_review.example.yaml"


def _load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture
def validator() -> jsonschema.Draft202012Validator:
    schema = _load(SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )


@pytest.fixture
def example() -> dict:
    return _load(EXAMPLE_PATH)


def test_mapping_review_example_validates(validator, example) -> None:
    validator.validate(example)


def test_existing_object_selection_requires_selected_ref(validator, example) -> None:
    broken = deepcopy(example)
    del broken["selected_stable_object_ref"]
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)


def test_clarification_requires_question(validator, example) -> None:
    broken = deepcopy(example)
    broken["action"] = "needs_clarification"
    broken.pop("selected_stable_object_ref", None)
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)


def test_non_selection_cannot_carry_selected_ref(validator, example) -> None:
    broken = deepcopy(example)
    broken["action"] = "reject_mapping"
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)


def test_review_cannot_claim_identity_or_write_authority(validator, example) -> None:
    for field in (
        "confirms_stable_identity",
        "writes_apu",
        "adopts_project_truth",
        "admits_evidence",
        "promotes_memory",
    ):
        broken = deepcopy(example)
        broken["authority"][field] = True
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(broken)
