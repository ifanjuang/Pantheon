from pathlib import Path

import jsonschema
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "decision_request.schema.yaml"
EXAMPLE_PATH = ROOT / "schemas" / "examples" / "decision_request.example.yaml"


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


def _resolved_question() -> dict:
    payload = _load(EXAMPLE_PATH)
    payload.update(
        status="resolved",
        decision_type="question",
        response_mode="free_text",
        options=[],
        recommendation_candidate=None,
        resolved_decision_ref=None,
        resolved_response_ref="human-response-001",
        resolved_at="2026-08-06T11:00:00Z",
        revision=2,
    )
    return payload


def test_decision_request_example_validates() -> None:
    _validator().validate(_load(EXAMPLE_PATH))


def test_blocking_request_requires_work_issue() -> None:
    invalid = _load(EXAMPLE_PATH)
    invalid["work_issue_ref"] = None
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(invalid)


def test_option_response_requires_reviewable_options() -> None:
    invalid = _load(EXAMPLE_PATH)
    invalid["options"] = []
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(invalid)


@pytest.mark.parametrize("resolution_field", ["resolved_decision_ref", "resolved_response_ref"])
def test_pending_request_cannot_claim_a_resolution(resolution_field: str) -> None:
    invalid = _load(EXAMPLE_PATH)
    invalid[resolution_field] = "resolution-001"
    invalid["resolved_at"] = "2026-08-06T11:00:00Z"
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(invalid)


def test_resolved_decision_request_requires_decision_record_reference() -> None:
    valid = _load(EXAMPLE_PATH)
    valid["status"] = "resolved"
    valid["revision"] = 2
    valid["resolved_decision_ref"] = "decision-001"
    valid["resolved_at"] = "2026-08-06T11:00:00Z"
    _validator().validate(valid)

    missing = dict(valid)
    missing["resolved_decision_ref"] = None
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(missing)


def test_resolved_question_requires_human_response_not_decision() -> None:
    valid = _resolved_question()
    _validator().validate(valid)

    missing = dict(valid)
    missing["resolved_response_ref"] = None
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(missing)

    wrong_authority = dict(valid)
    wrong_authority["resolved_response_ref"] = None
    wrong_authority["resolved_decision_ref"] = "decision-001"
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(wrong_authority)


def test_resolved_decision_cannot_claim_human_response_reference() -> None:
    invalid = _load(EXAMPLE_PATH)
    invalid["status"] = "resolved"
    invalid["revision"] = 2
    invalid["resolved_decision_ref"] = None
    invalid["resolved_response_ref"] = "human-response-001"
    invalid["resolved_at"] = "2026-08-06T11:00:00Z"
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(invalid)


def test_free_text_request_does_not_carry_choice_options() -> None:
    invalid = _load(EXAMPLE_PATH)
    invalid["decision_type"] = "question"
    invalid["response_mode"] = "free_text"
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(invalid)


def test_h3_decision_scope_is_bounded_to_apu_objects() -> None:
    valid = _load(EXAMPLE_PATH)
    assert valid["scope_refs"] == [
        {"entity_type": "apu_object", "entity_id": "boundary.facade-south"}
    ]
    _validator().validate(valid)

    invalid = _load(EXAMPLE_PATH)
    invalid["scope_refs"] = [
        {"entity_type": "information", "entity_id": "information-001"}
    ]
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(invalid)


def test_apu_scoped_decision_request_requires_project_classification() -> None:
    invalid = _load(EXAMPLE_PATH)
    invalid["project_ref"] = None
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(invalid)


def test_global_decisions_are_only_unclassified_requests() -> None:
    schema = _load(SCHEMA_PATH)
    rules = schema["x-decision-request-rules"]
    assert rules["global_decisions_view_contains_only_unclassified_requests"] is True
    assert rules["unclassified_request_has_null_project_ref"] is True
    assert rules["project_view_requires_matching_project_ref"] is True
    assert rules["apu_scope_requires_project_classification"] is True
    assert rules["scope_refs_remain_request_owned"] is True
    assert rules["question_resolution_creates_human_response"] is True
    assert rules["decision_resolution_creates_separate_decision_record"] is True
    assert rules["resolution_reference_is_type_driven"] is True
    assert schema["x-boundary"]["agency_decision_owner"] is False


def test_request_and_human_response_are_not_runtime_authority() -> None:
    schema = _load(SCHEMA_PATH)
    boundary = schema["x-boundary"]
    assert boundary["request_is_decision"] is False
    assert boundary["request_is_approval"] is False
    assert boundary["agency_decision_owner"] is False
    assert boundary["human_response_is_decision"] is False
    assert boundary["human_response_is_authorization"] is False
    assert boundary["scope_ref_is_semantic_relation"] is False
    assert boundary["scope_ref_is_task_authorization"] is False
    assert boundary["scope_ref_mutates_apu"] is False
    assert boundary["automatic_work_issue_transition"] is False
    assert boundary["automatic_runtime_continuation"] is False
    assert boundary["runtime_execution"] is False
    assert boundary["scheduler"] is False
    assert boundary["queue_system"] is False
    assert boundary["provider_routing"] is False
    assert boundary["memory_promotion"] is False
    assert boundary["evidence_admission"] is False
    assert boundary["automatic_approval"] is False
