"""Contract tests for bounded Project change variant candidates."""

from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
VARIANT_SCHEMA = ROOT / "schemas" / "project_change_variant_candidate.schema.yaml"
VARIANT_EXAMPLE = ROOT / "schemas" / "examples" / "project_change_variant_candidate.example.yaml"
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


def result_authority() -> dict[str, bool]:
    return {
        "is_fact": False,
        "is_evidence": False,
        "is_decision": False,
        "is_memory": False,
        "is_apu_write": False,
        "authorizes_external_effect": False,
    }


def test_project_change_variant_example_validates() -> None:
    validator(VARIANT_SCHEMA).validate(load_yaml(VARIANT_EXAMPLE))


def test_project_change_variant_cannot_claim_authority() -> None:
    example = load_yaml(VARIANT_EXAMPLE)
    check = validator(VARIANT_SCHEMA)
    for field in (
        "creates_change_candidate",
        "selects_variant",
        "applies_project_change",
        "creates_project_claim",
        "adopts_project_truth",
        "creates_decision",
        "admits_evidence",
        "authorizes_effect",
    ):
        broken = deepcopy(example)
        broken["authority"][field] = True
        with pytest.raises(jsonschema.ValidationError):
            check.validate(broken)


def test_project_change_variant_requires_exact_scope_and_non_empty_change() -> None:
    example = load_yaml(VARIANT_EXAMPLE)
    check = validator(VARIANT_SCHEMA)

    without_scope = deepcopy(example)
    without_scope.pop("request_scope_digest")
    with pytest.raises(jsonschema.ValidationError):
        check.validate(without_scope)

    empty_change = deepcopy(example)
    empty_change["proposed_attributes"] = {}
    with pytest.raises(jsonschema.ValidationError):
        check.validate(empty_change)


def test_project_change_variant_has_no_branch_identity() -> None:
    schema = load_yaml(VARIANT_SCHEMA)
    example = load_yaml(VARIANT_EXAMPLE)
    assert "branch_id" not in schema["properties"]
    assert "branch_ref" not in schema["properties"]
    assert "branch_id" not in example
    assert "branch_ref" not in example


def test_execution_result_can_carry_sibling_project_variants() -> None:
    envelope = load_yaml(EXECUTION_EXAMPLE)
    option_a = load_yaml(VARIANT_EXAMPLE)
    option_b = deepcopy(option_a)
    option_b["variant_label"] = "option-ardoise"
    option_b["variant_title"] = "Couverture ardoise naturelle"
    option_b["proposed_attributes"] = {
        "architectural_style": "Volumétrie en L sous couverture en ardoise naturelle.",
        "programme_summary": "Maison principale avec deux loggias et couverture ardoise naturelle.",
    }
    option_b["rationale"] = "Cette alternative conserve le matériau régional de référence."

    assert option_a["request_ref"] == option_b["request_ref"]
    assert option_a["request_scope_digest"] == option_b["request_scope_digest"]
    assert option_a["project_ref"] == option_b["project_ref"]
    assert option_a["base_revision"] == option_b["base_revision"]
    assert option_a["variant_label"] != option_b["variant_label"]

    envelope["execution_result"]["project_ref"] = option_a["project_ref"]
    envelope["execution_result"]["results"] = [
        {
            "result_id": "result.project-change-variant.zinc",
            "result_kind": "project_change_variant",
            "schema_ref": "schemas/project_change_variant_candidate.schema.yaml",
            "payload": option_a,
            "authority": result_authority(),
        },
        {
            "result_id": "result.project-change-variant.ardoise",
            "result_kind": "project_change_variant",
            "schema_ref": "schemas/project_change_variant_candidate.schema.yaml",
            "payload": option_b,
            "authority": result_authority(),
        },
    ]
    envelope["execution_result"]["clarifications"] = []
    envelope["review_dispositions"] = []

    validator(EXECUTION_SCHEMA).validate(envelope)
