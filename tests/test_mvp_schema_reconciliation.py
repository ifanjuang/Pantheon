"""Validation-only checks for the MVP decision/schema reconciliation (Pantheon-Next#359)."""

from __future__ import annotations

import copy
from pathlib import Path

import jsonschema
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "mvp_governed_loop_objects.schema.yaml"
REQUEST_REF = "mvp.case.tc.001"
REQUEST_SCOPE_DIGEST = "sha256:" + "4" * 64


def _validator() -> jsonschema.Draft202012Validator:
    schema = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )


def _digest(char: str = "a") -> dict:
    return {"algorithm": "sha256", "value": char * 64}


def _decision_record() -> dict:
    return {
        "object_type": "decision_record",
        "object_id": "mvp.case.decision.001",
        "decision_id": "mvp.case.decision.001",
        "status": "recorded",
        "applies_to": "mvp.case.result.001",
        "decision": "request_revision",
        "decided_by": "practitioner",
        "identity_assurance": "declared",
        "recorded_at": "2026-07-13T02:30:00Z",
        "candidate_digest": _digest("a"),
        "evidence_pack_digest": _digest("b"),
        "decision_surface": "terminal_gate_standin",
        "consequences": {
            "external_action": "none",
            "memory_admission": "not_granted",
        },
    }


def _result_candidate() -> dict:
    return {
        "object_type": "result_candidate",
        "object_id": "mvp.case.result.001",
        "status": "draft_to_review",
        "request_ref": REQUEST_REF,
        "request_scope_digest": REQUEST_SCOPE_DIGEST,
        "body": "Nous acceptons la reprise.",
        "commitment_flags": [
            {
                "phrase": "Nous acceptons",
                "risk": "external commitment if sent as-is",
            }
        ],
        "grounding_review": {
            "citation_count": 0,
            "retrieved_chunk_count": 2,
            "uncited_claim_flags": ["Nous acceptons la reprise."],
            "note": "Advisory visibility only; not a score, approval, or truth verdict.",
        },
        "external_action_authorized": False,
    }


def _register_candidate() -> dict:
    return {
        "object_type": "register_candidate",
        "object_id": "mvp.case.register.001",
        "status": "candidate",
        "created_because_of": "mvp.case.decision.002",
        "statement": "Scoped reviewed statement.",
        "scope": "project:case",
        "retention_authorization": {
            "authorized": True,
            "authorized_by": "practitioner",
            "identity_assurance": "declared",
            "recorded_at": "2026-07-13T02:35:00Z",
            "decision_id": "mvp.case.decision.002",
        },
        "not_memory_until_admitted": True,
    }


def test_decision_vocabulary_is_closed_and_semantically_declared() -> None:
    schema = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
    expected = ["approve", "refuse", "request_revision", "request_more_evidence"]

    assert schema["$defs"]["decision_value"]["enum"] == expected
    assert schema["x-decision-vocabulary"]["source"] == "#/$defs/decision_value/enum"
    assert list(schema["x-decision-vocabulary"]["semantics"]) == expected

    validator = _validator()
    record = _decision_record()
    validator.validate(record)
    record["decision"] = "send_now"
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(record)


def test_possible_decisions_use_the_same_closed_vocabulary() -> None:
    validator = _validator()
    evidence_pack = {
        "object_type": "evidence_pack_candidate",
        "object_id": "mvp.case.evidence.001",
        "status": "candidate",
        "request_ref": REQUEST_REF,
        "request_scope_digest": REQUEST_SCOPE_DIGEST,
        "applies_to": "mvp.case.result.001",
        "evidence_items": [
            {"claim": "Claim", "source_ref": "src.001", "support_status": "unverified"}
        ],
        "possible_decisions": ["approve", "request_more_evidence"],
    }
    validator.validate(evidence_pack)
    evidence_pack["possible_decisions"].append("send_now")
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(evidence_pack)


def test_commitment_flags_and_grounding_review_are_structured() -> None:
    validator = _validator()
    candidate = _result_candidate()
    validator.validate(candidate)

    string_flag = copy.deepcopy(candidate)
    string_flag["commitment_flags"] = ["Nous acceptons"]
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(string_flag)

    scored_grounding = copy.deepcopy(candidate)
    scored_grounding["grounding_review"]["score"] = 0.9
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(scored_grounding)


def test_decision_integrity_and_identity_assurance_are_formalized() -> None:
    validator = _validator()
    declared = _decision_record()
    validator.validate(declared)

    missing_digest = copy.deepcopy(declared)
    del missing_digest["candidate_digest"]
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(missing_digest)

    bad_digest = copy.deepcopy(declared)
    bad_digest["candidate_digest"] = {"algorithm": "md5", "value": "a" * 64}
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(bad_digest)

    missing_evidence_digest = copy.deepcopy(declared)
    missing_evidence_digest["related_evidence_pack"] = "mvp.case.evidence.001"
    missing_evidence_digest.pop("evidence_pack_digest")
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(missing_evidence_digest)

    fabricated_principal = copy.deepcopy(declared)
    fabricated_principal["authenticated_principal"] = {
        "user_id": "u-1",
        "identity_provider": "openwebui",
    }
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(fabricated_principal)

    authenticated = copy.deepcopy(declared)
    authenticated["identity_assurance"] = "authenticated"
    authenticated["decision_surface"] = "openwebui"
    authenticated["authenticated_principal"] = {
        "user_id": "u-1",
        "display_name": "Practitioner",
        "identity_provider": "openwebui",
    }
    validator.validate(authenticated)


def test_register_candidate_requires_separate_retention_authorization() -> None:
    validator = _validator()
    candidate = _register_candidate()
    validator.validate(candidate)

    missing = copy.deepcopy(candidate)
    del missing["retention_authorization"]
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(missing)

    not_authorized = copy.deepcopy(candidate)
    not_authorized["retention_authorization"]["authorized"] = False
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(not_authorized)


def test_documented_mvp_fixtures_follow_the_reconciled_schema() -> None:
    validator = _validator()
    fixture_root = (
        ROOT / "docs" / "governance" / "examples" / "mvp_vertical_fixture"
    )

    for name in (
        "fixture.schema_targets.yaml",
        "failing_external_action.fixture.yaml",
    ):
        documents = list(
            yaml.safe_load_all((fixture_root / name).read_text(encoding="utf-8"))
        )
        assert documents
        for document in documents:
            validator.validate(document)

    target_text = (fixture_root / "fixture.schema_targets.yaml").read_text(
        encoding="utf-8"
    )
    assert "approve_for_internal_draft" not in target_text
    assert "retention_authorization:" in target_text


def test_generated_fixture_reports_match_the_reconciled_vocabulary() -> None:
    reports = (
        ROOT
        / "docs"
        / "governance"
        / "examples"
        / "mvp_vertical_fixture"
        / "generated_reports"
    )
    expected = {
        "fixture.schema_targets.generated_report.yaml": "reviewable",
        "failing_external_action.generated_report.yaml": "blocked",
    }
    for name, status in expected.items():
        report = yaml.safe_load((reports / name).read_text(encoding="utf-8"))
        assert report["status"] == status
        assert report["summary"]["schema_status"] == "pass"
        rendered = yaml.safe_dump(report)
        assert "approve_for_internal_draft" not in rendered
        assert "approve_does_not_authorize_send" in rendered


def test_schema_remains_validation_only() -> None:
    schema = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["x-boundary"]["runtime_execution"] is False
    assert schema["x-boundary"]["automatic_dispatch"] is False
    assert schema["x-boundary"]["memory_promotion"] is False
    assert schema["x-boundary"]["automatic_approval"] is False
