"""Focused validation tests for the minimal Work Issue persistence contract."""

from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "work_issue_slice.schema.yaml"
EXAMPLE_PATH = ROOT / "schemas" / "examples" / "work_issue_slice.example.yaml"


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


def test_minimal_slice_validates(validator, example) -> None:
    validator.validate(example)


def test_hermes_may_return_an_issue_to_review(validator, example) -> None:
    event = example["events"][0]
    event["transition"] = {
        "from_status": "in_progress",
        "to_status": "review",
        "actor_kind": "hermes",
    }
    validator.validate(example)


@pytest.mark.parametrize("forbidden_status", ["done", "cancelled"])
def test_hermes_cannot_close_an_issue(validator, example, forbidden_status) -> None:
    broken = deepcopy(example)
    broken["events"][0]["transition"]["to_status"] = forbidden_status

    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)


def test_closed_issue_requires_a_close_reason(validator, example) -> None:
    broken = deepcopy(example)
    broken["work_issue"]["status"] = "done"

    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)


def test_active_issue_refuses_a_close_reason(validator, example) -> None:
    broken = deepcopy(example)
    broken["work_issue"]["close_reason"] = "answered"

    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)


def test_terminal_states_are_not_valid_transition_origins(validator, example) -> None:
    broken = deepcopy(example)
    broken["events"][0]["transition"] = {
        "from_status": "done",
        "to_status": "in_progress",
        "actor_kind": "human",
    }

    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)


def test_event_actor_must_match_transition_actor(validator, example) -> None:
    broken = deepcopy(example)
    broken["events"][0]["transition"]["actor_kind"] = "human"

    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)
