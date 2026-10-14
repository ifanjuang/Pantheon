"""Contract tests for the first explicit Information relations."""

from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "entity_relation.schema.yaml"
EXAMPLE = ROOT / "schemas" / "examples" / "information_entity_relation.example.yaml"
INFORMATION_SCHEMA = ROOT / "schemas" / "information_card_projection.schema.yaml"


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def validator() -> jsonschema.Draft202012Validator:
    schema = load_yaml(SCHEMA)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )


def test_information_relation_example_validates() -> None:
    validator().validate(load_yaml(EXAMPLE))


@pytest.mark.parametrize(
    "relation_type",
    ["responds_to", "relies_on", "supersedes", "contradicts"],
)
def test_the_four_relation_types_are_admitted(relation_type: str) -> None:
    example = load_yaml(EXAMPLE)
    example["relation_type"] = relation_type
    validator().validate(example)


def test_unapproved_relation_type_is_refused() -> None:
    example = load_yaml(EXAMPLE)
    example["relation_type"] = "contains"
    with pytest.raises(jsonschema.ValidationError):
        validator().validate(example)


def test_endpoint_types_are_bounded_to_information() -> None:
    example = load_yaml(EXAMPLE)
    for endpoint in ("from", "to"):
        broken = deepcopy(example)
        broken[endpoint]["entity_type"] = "document"
        with pytest.raises(jsonschema.ValidationError):
            validator().validate(broken)


def test_unknown_properties_are_refused() -> None:
    example = load_yaml(EXAMPLE)
    example["review_status"] = "approved"
    with pytest.raises(jsonschema.ValidationError):
        validator().validate(example)


def test_retirement_requires_actor() -> None:
    example = load_yaml(EXAMPLE)
    example["retired_at"] = "2026-08-06T03:00:00Z"
    example["retired_by"] = None
    with pytest.raises(jsonschema.ValidationError):
        validator().validate(example)


def test_information_projection_admits_initial_revision_zero() -> None:
    schema = load_yaml(INFORMATION_SCHEMA)
    assert schema["properties"]["revision"]["minimum"] == 0


def test_contract_keeps_non_authority_boundaries() -> None:
    schema = load_yaml(SCHEMA)
    boundary = schema["x-boundary"]
    assert boundary["generic_storage_shape"] is True
    assert boundary["admitted_endpoint_types"] == ["information"]
    for field in (
        "inferred_relation",
        "project_truth_created",
        "evidence_admission",
        "professional_validation",
        "task_authorization",
        "runtime_execution",
        "memory_promotion",
    ):
        assert boundary[field] is False
