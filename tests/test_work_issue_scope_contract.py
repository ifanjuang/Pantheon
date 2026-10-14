from pathlib import Path

import jsonschema
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "work_issue_scope_link.schema.yaml"
EXAMPLE_PATH = ROOT / "schemas" / "examples" / "work_issue_scope_link.example.yaml"


def _load(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _validator() -> jsonschema.Draft202012Validator:
    schema = _load(SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )


def test_work_issue_scope_example_validates() -> None:
    _validator().validate(_load(EXAMPLE_PATH))


def test_scope_types_are_closed_to_reviewed_owners() -> None:
    schema = _load(SCHEMA_PATH)
    assert schema["$defs"]["work_scope_ref"]["properties"]["entity_type"]["enum"] == [
        "agency",
        "project",
        "information",
        "decision",
        "person",
        "organization",
        "apu_object",
    ]

    invalid = _load(EXAMPLE_PATH)
    invalid["scope_ref"]["entity_type"] = "anything"
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(invalid)


def test_scope_link_is_not_a_semantic_relation_or_authorization() -> None:
    schema = _load(SCHEMA_PATH)
    boundary = schema["x-boundary"]
    assert boundary["semantic_relation"] is False
    assert boundary["second_graph"] is False
    assert boundary["scope_widening"] is False
    assert boundary["context_pack_mutation"] is False
    assert boundary["task_authorization"] is False
    assert boundary["project_truth_created"] is False
    assert boundary["evidence_admission"] is False
    assert boundary["runtime_execution"] is False


def test_retired_scope_requires_a_retiring_actor() -> None:
    invalid = _load(EXAMPLE_PATH)
    invalid["retired_at"] = "2026-08-06T10:00:00Z"
    invalid["retired_by"] = None
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(invalid)


def test_scope_role_vocabulary_is_closed() -> None:
    invalid = _load(EXAMPLE_PATH)
    invalid["scope_role"] = "owner"
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(invalid)
