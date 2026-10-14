"""Focused validation tests for the transport-neutral Document → Knowledge contract."""

from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "document_knowledge_slice.schema.yaml"
EXAMPLE_PATH = ROOT / "schemas" / "examples" / "document_knowledge_slice.example.yaml"


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


def test_minimal_document_to_knowledge_slice_validates(validator, example) -> None:
    validator.validate(example)


def test_document_structure_is_required_before_chunks(validator, example) -> None:
    broken = deepcopy(example)
    del broken["document_structure"]

    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)


def test_chunk_must_reference_a_fragment(validator, example) -> None:
    broken = deepcopy(example)
    del broken["chunks"][0]["fragment_ref"]

    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)


def test_fragment_requires_source_locator(validator, example) -> None:
    broken = deepcopy(example)
    del broken["document_structure"]["fragments"][0]["locator"]

    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)


def test_fragment_qualification_cannot_claim_project_truth(validator, example) -> None:
    broken = deepcopy(example)
    broken["document_structure"]["fragments"][0]["qualification"]["project_state"] = "approved"

    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)


def test_document_card_requires_parent_project(validator, example) -> None:
    broken = deepcopy(example)
    del broken["document_card"]["parent_project_id"]

    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)


@pytest.mark.parametrize("authority_field", ["is_source", "is_evidence", "is_memory"])
def test_document_card_cannot_claim_authority(validator, example, authority_field) -> None:
    broken = deepcopy(example)
    broken["document_card"]["authority"][authority_field] = True

    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)


def test_knowledge_publication_cannot_claim_approval(validator, example) -> None:
    broken = deepcopy(example)
    broken["knowledge_publications"][0]["review_status"] = "approved"

    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)


def test_knowledge_publication_remains_outside_evidence_and_memory(validator, example) -> None:
    for field in ("is_evidence", "is_memory", "is_doctrine"):
        broken = deepcopy(example)
        broken["knowledge_publications"][0]["authority"][field] = True
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(broken)


def test_parser_observation_kind_is_explicit(validator, example) -> None:
    broken = deepcopy(example)
    del broken["extraction"]["observation_kind"]

    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)


@pytest.mark.parametrize("source_ref", ["/etc/passwd", "Projects/MAISON-A/../secret.pdf"])
def test_source_reference_must_stay_relative_and_contained(validator, example, source_ref) -> None:
    broken = deepcopy(example)
    broken["source_document"]["source_ref"] = source_ref

    with pytest.raises(jsonschema.ValidationError):
        validator.validate(broken)
