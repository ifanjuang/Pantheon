"""Contract tests for bounded Knowledge edit variants in Execution Results."""

from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
VARIANT_SCHEMA = ROOT / "schemas" / "knowledge_edit_variant_candidate.schema.yaml"
VARIANT_EXAMPLE = ROOT / "schemas" / "examples" / "knowledge_edit_variant_candidate.example.yaml"
EXECUTION_SCHEMA = ROOT / "schemas" / "execution_result.schema.yaml"
EXECUTION_EXAMPLE = ROOT / "schemas" / "examples" / "execution_result.example.yaml"


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def validator(path: Path) -> jsonschema.Draft202012Validator:
    schema = load_yaml(path)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )


def test_variant_example_validates() -> None:
    validator(VARIANT_SCHEMA).validate(load_yaml(VARIANT_EXAMPLE))


def test_variant_cannot_claim_selection_application_or_validation() -> None:
    example = load_yaml(VARIANT_EXAMPLE)
    check = validator(VARIANT_SCHEMA)
    for field in (
        "selects_variant",
        "applies_edit",
        "validates_knowledge",
        "admits_evidence",
        "promotes_memory",
        "authorizes_task",
    ):
        broken = deepcopy(example)
        broken["authority"][field] = True
        with pytest.raises(jsonschema.ValidationError):
            check.validate(broken)


def test_variant_requires_exact_digest_and_label_shapes() -> None:
    example = load_yaml(VARIANT_EXAMPLE)
    check = validator(VARIANT_SCHEMA)

    broken_digest = deepcopy(example)
    broken_digest["request_scope_digest"] = "not-a-digest"
    with pytest.raises(jsonschema.ValidationError):
        check.validate(broken_digest)

    broken_label = deepcopy(example)
    broken_label["variant_label"] = "C"
    with pytest.raises(jsonschema.ValidationError):
        check.validate(broken_label)


def test_execution_result_accepts_variant_as_typed_candidate() -> None:
    envelope = load_yaml(EXECUTION_EXAMPLE)
    payload = load_yaml(VARIANT_EXAMPLE)
    envelope["execution_result"]["results"] = [
        {
            "result_id": "knowledge-edit-variant-result-a",
            "result_kind": "knowledge_edit_variant",
            "schema_ref": "schemas/knowledge_edit_variant_candidate.schema.yaml",
            "payload": payload,
            "authority": {
                "is_fact": False,
                "is_evidence": False,
                "is_decision": False,
                "is_memory": False,
                "is_apu_write": False,
                "authorizes_external_effect": False,
            },
        }
    ]
    envelope["execution_result"]["clarifications"] = []
    envelope["review_dispositions"] = []

    validator(EXECUTION_SCHEMA).validate(envelope)
