from pathlib import Path

import jsonschema
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "human_response.schema.yaml"


def _schema() -> dict:
    payload = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    jsonschema.Draft202012Validator.check_schema(payload)
    return payload


def _validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(
        _schema(),
        format_checker=jsonschema.FormatChecker(),
    )


def _response() -> dict:
    return {
        "response_id": "human-response-001",
        "request_id": "decision-request-001",
        "responded_by": "architect-human",
        "identity_assurance": "declared",
        "authenticated_principal": None,
        "selected_option_ids": [],
        "response_text": "La façade existante est conservée.",
        "candidate_digest": {
            "algorithm": "sha256",
            "value": "a" * 64,
        },
        "recorded_at": "2026-09-15T12:00:00Z",
    }


def test_human_response_validates_as_governed_information() -> None:
    _validator().validate(_response())


def test_declared_response_cannot_claim_authenticated_principal() -> None:
    invalid = _response()
    invalid["authenticated_principal"] = {
        "user_id": "architect-human",
        "identity_provider": "caller-asserted",
    }
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(invalid)


def test_authenticated_response_requires_identity_source() -> None:
    invalid = _response()
    invalid["identity_assurance"] = "authenticated"
    invalid["authenticated_principal"] = None
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(invalid)

    valid = _response()
    valid["identity_assurance"] = "authenticated"
    valid["authenticated_principal"] = {
        "user_id": "architect-human",
        "identity_provider": "oidc",
    }
    _validator().validate(valid)


def test_human_response_boundary_is_informational_only() -> None:
    boundary = _schema()["x-boundary"]
    assert boundary["response_is_decision"] is False
    assert boundary["response_is_approval"] is False
    assert boundary["response_is_authorization"] is False
    assert boundary["response_is_evidence"] is False
    assert boundary["automatic_work_issue_transition"] is False
    assert boundary["automatic_runtime_continuation"] is False
    assert boundary["runtime_execution"] is False
    assert boundary["automatic_approval"] is False
