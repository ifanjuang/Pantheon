"""Contract tests for ProjectClaim candidates and governed Claim creation."""

from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_SCHEMA = ROOT / "schemas" / "project_claim_candidate.schema.yaml"
CANDIDATE_EXAMPLE = ROOT / "schemas" / "examples" / "project_claim_candidate.example.yaml"
CLAIM_SCHEMA = ROOT / "schemas" / "project_claim.schema.yaml"
CLAIM_EXAMPLE = ROOT / "schemas" / "examples" / "project_claim_from_candidate.example.yaml"
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


def test_project_claim_candidate_example_validates() -> None:
    validator(CANDIDATE_SCHEMA).validate(load_yaml(CANDIDATE_EXAMPLE))


def test_project_claim_candidate_cannot_claim_authority() -> None:
    example = load_yaml(CANDIDATE_EXAMPLE)
    check = validator(CANDIDATE_SCHEMA)
    for field in (
        "creates_project_claim",
        "adopts_project_truth",
        "admits_evidence",
        "creates_decision",
        "creates_work_issue",
        "authorizes_effect",
    ):
        broken = deepcopy(example)
        broken["authority"][field] = True
        with pytest.raises(jsonschema.ValidationError):
            check.validate(broken)


def test_project_claim_candidate_requires_basis_and_certainty() -> None:
    example = load_yaml(CANDIDATE_EXAMPLE)
    check = validator(CANDIDATE_SCHEMA)

    without_basis = deepcopy(example)
    without_basis["basis_refs"] = []
    with pytest.raises(jsonschema.ValidationError):
        check.validate(without_basis)

    without_certainty = deepcopy(example)
    without_certainty.pop("certainty")
    with pytest.raises(jsonschema.ValidationError):
        check.validate(without_certainty)


def test_execution_result_accepts_project_claim_candidate() -> None:
    envelope = load_yaml(EXECUTION_EXAMPLE)
    payload = load_yaml(CANDIDATE_EXAMPLE)
    envelope["execution_result"]["project_ref"] = payload["project_ref"]
    envelope["execution_result"]["results"] = [
        {
            "result_id": "project-claim-result-surface",
            "result_kind": "project_claim_candidate",
            "schema_ref": "schemas/project_claim_candidate.schema.yaml",
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


def test_project_claim_retains_exact_candidate_provenance() -> None:
    validator(CLAIM_SCHEMA).validate(load_yaml(CLAIM_EXAMPLE))


def test_execution_result_origin_requires_candidate_identity() -> None:
    claim = load_yaml(CLAIM_EXAMPLE)
    claim["provenance"].pop("candidate_ref")
    with pytest.raises(jsonschema.ValidationError):
        validator(CLAIM_SCHEMA).validate(claim)


def test_execution_result_origin_requires_review_disposition_identity() -> None:
    claim = load_yaml(CLAIM_EXAMPLE)
    claim["provenance"]["candidate_ref"].pop("review_disposition_id")
    with pytest.raises(jsonschema.ValidationError):
        validator(CLAIM_SCHEMA).validate(claim)


def test_project_claim_requires_certainty_independently_of_status() -> None:
    claim = load_yaml(CLAIM_EXAMPLE)
    claim.pop("certainty")
    with pytest.raises(jsonschema.ValidationError):
        validator(CLAIM_SCHEMA).validate(claim)
