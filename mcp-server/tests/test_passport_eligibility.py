"""I4/I9 regression tests for exact-release Capability eligibility."""

from __future__ import annotations

import copy
from pathlib import Path

import yaml

from pantheon_mcp.passports import validate_passport


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "schemas" / "examples" / "capability_passport.skill.example.yaml"


def _passport() -> dict:
    value = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_current_flat_skill_passport_is_validated_by_canonical_schema() -> None:
    passport = _passport()
    report = validate_passport(passport)

    assert report["valid"] is True
    assert report["passport_id"] == passport["passport_id"]
    assert passport["capability"]["primitive"] == "skill"
    assert report["authorization_effect"] == "none"
    assert report["runtime_probe_performed"] is False


def test_reviewed_passport_requires_exact_immutable_release_for_eligibility() -> None:
    passport = _passport()
    passport["status"] = "reviewed"
    passport.pop("implementation_provenance")

    report = validate_passport(passport)

    assert report["valid"] is True
    assert report["ready_for_review"] is False
    assert report["exact_release_qualified"] is False
    assert report["eligibility_posture"] == "reviewed_with_governance_gaps"
    assert any("exact implementation provenance" in gap for gap in report["governance_gaps"])
    assert report["authorization_effect"] == "none"


def test_reviewed_exact_release_is_eligible_but_never_task_authorized_by_validation() -> None:
    passport = _passport()
    passport["status"] = "reviewed"
    passport["governance"]["task_authorization"] = "unauthorized"

    report = validate_passport(passport)

    assert report["valid"] is True
    assert report["ready_for_review"] is True
    assert report["exact_release_qualified"] is True
    assert report["eligibility_posture"] == "reviewed_exact_release"
    assert report["task_authorization"] == "unauthorized"
    assert report["authorization_effect"] == "none"
    assert report["activation_effect"] == "none"
    assert report["activation_owner"] == "CapabilityActivation exact-binding record"
    assert report["task_authorization_owner"] == "Task Contract / Execution Admission"


def test_reviewed_passport_does_not_require_legacy_activation_or_task_fields() -> None:
    passport = _passport()
    passport["status"] = "reviewed"
    passport["governance"].pop("activation_state", None)
    passport["governance"].pop("task_authorization", None)

    report = validate_passport(passport)

    assert report["valid"] is True
    assert report["ready_for_review"] is True
    assert report["exact_release_qualified"] is True
    assert report["legacy_activation_state"] is None
    assert report["task_authorization"] is None
    assert report["authorization_effect"] == "none"
    assert report["activation_effect"] == "none"


def test_passport_schema_rejects_positive_task_authorization() -> None:
    passport = _passport()
    passport["status"] = "reviewed"
    passport["governance"]["task_authorization"] = "task_authorized"

    report = validate_passport(passport)

    assert report["valid"] is False
    assert report["ready_for_review"] is False
    assert report["eligibility_posture"] == "invalid"
    assert any(problem["path"] == "governance.task_authorization" for problem in report["problems"])
    assert report["authorization_effect"] == "none"


def test_replacement_release_does_not_inherit_exact_release_qualification_by_name() -> None:
    release_a = _passport()
    release_a["status"] = "reviewed"
    release_a["governance"]["task_authorization"] = "unauthorized"

    release_b = copy.deepcopy(release_a)
    release_b["implementation_provenance"]["content_digest"] = "sha256:" + "b" * 64
    release_b["implementation_provenance"]["commit_ref"] = (
        "fedcba9876543210fedcba9876543210fedcba98"
    )

    report_a = validate_passport(release_a)
    report_b = validate_passport(release_b)

    assert release_a["passport_id"] == release_b["passport_id"]
    assert report_a["implementation_anchor"] != report_b["implementation_anchor"]
    assert report_a["authorization_effect"] == "none"
    assert report_b["authorization_effect"] == "none"