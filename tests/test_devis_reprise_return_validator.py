"""Validation-only tests for the external devis-reprise return contract."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_devis_reprise_return.py"
SPEC = importlib.util.spec_from_file_location("devis_return_validator", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

TASK = yaml.safe_load(
    (ROOT / "docs/examples/vertical_devis_reprise/task_contract.devis-reprise.yaml").read_text(
        encoding="utf-8"
    )
)
SCHEMA = yaml.safe_load(
    (ROOT / "schemas/evidence_pack.schema.yaml").read_text(encoding="utf-8")
)
FIXTURE = yaml.safe_load(
    (
        ROOT
        / "docs/examples/external_run_returns/architecture_devis_reprise.example.yaml"
    ).read_text(encoding="utf-8")
)
EXPECTED_REF = "replace-with-audited-tag-or-commit"


def validate(bundle: dict) -> dict:
    return MODULE.validate_external_return(
        bundle,
        TASK,
        SCHEMA,
        expected_pantheon_ref=EXPECTED_REF,
    )


def test_fictional_fixture_is_reviewable_with_explicit_gaps() -> None:
    report = validate(copy.deepcopy(FIXTURE))
    assert report["ok"] is True
    assert report["classification"] == "PASS_WITH_GOVERNANCE_GAPS"
    assert {item["code"] for item in report["warnings"]} == {
        "BRIDGE_NOT_PROVEN",
        "UNRESOLVED_POINTS",
    }


def test_full_structural_candidate_can_pass_without_claiming_approval() -> None:
    bundle = copy.deepcopy(FIXTURE)
    run = bundle["external_run_return"]
    run["bridge"]["status"] = "executed_external"
    run["result_candidate"]["uncertain_points"] = []
    report = validate(bundle)
    assert report["ok"] is True
    assert report["classification"] == "PASS_STRUCTURAL"
    assert report["warnings"] == []


def test_wrong_task_contract_fails_closed() -> None:
    bundle = copy.deepcopy(FIXTURE)
    bundle["external_run_return"]["task_contract_id"] = "other.contract"
    report = validate(bundle)
    assert report["ok"] is False
    assert report["classification"] == "FAIL_MISSING_TASK_CONTRACT"


def test_candidate_return_requires_evidence_pack() -> None:
    bundle = copy.deepcopy(FIXTURE)
    del bundle["external_run_return"]["evidence_pack_candidate"]
    report = validate(bundle)
    assert report["ok"] is False
    assert report["classification"] == "FAIL_MISSING_EVIDENCE_PACK"


def test_external_effect_attempt_fails_before_other_shape_gaps() -> None:
    bundle = copy.deepcopy(FIXTURE)
    bundle["external_run_return"]["effect_report"]["external_effect_attempted"] = True
    report = validate(bundle)
    assert report["ok"] is False
    assert report["classification"] == "FAIL_EXTERNAL_EFFECT_ATTEMPTED"


def test_runtime_cannot_mark_output_approved() -> None:
    bundle = copy.deepcopy(FIXTURE)
    pack = bundle["external_run_return"]["evidence_pack_candidate"]
    pack["outputs"][0]["status"] = "approved"
    report = validate(bundle)
    assert report["ok"] is False
    assert report["classification"] == "FAIL_APPROVAL_COLLAPSE"


def test_retired_memory_key_is_refused_as_register_admission_risk() -> None:
    bundle = copy.deepcopy(FIXTURE)
    bundle["external_run_return"]["memory_candidates"] = ["forbidden"]
    report = validate(bundle)
    assert report["ok"] is False
    assert report["classification"] == "FAIL_REGISTER_ADMISSION_ATTEMPTED"


def test_structured_capability_gap_is_valid_but_not_a_candidate_pass() -> None:
    bundle = copy.deepcopy(FIXTURE)
    run = bundle["external_run_return"]
    run["outcome_type"] = "capability_gap"
    run.pop("result_candidate")
    run.pop("evidence_pack_candidate")
    run["capability_gap"] = {
        "code": "missing_source",
        "summary": "One expected source is unavailable.",
        "missing": ["prior signed amendment"],
    }
    report = validate(bundle)
    assert report["ok"] is True
    assert report["classification"] == "PASS_WITH_GOVERNANCE_GAPS"
    assert "CAPABILITY_GAP_RETURNED" in {
        item["code"] for item in report["warnings"]
    }
