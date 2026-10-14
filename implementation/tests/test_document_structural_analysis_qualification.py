from __future__ import annotations

import importlib.util
import sys
from copy import deepcopy
from pathlib import Path

import pytest


LAB = (
    Path(__file__).resolve().parents[1]
    / "labs"
    / "document_structural_analysis"
    / "qualification.py"
)
SPEC = importlib.util.spec_from_file_location("pantheon_document_structural_analysis_662", LAB)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

StructuralQualificationError = MODULE.StructuralQualificationError
summarize_campaign = MODULE.summarize_campaign
validate_campaign = MODULE.validate_campaign


def _digest(char: str) -> str:
    return "sha256:" + char * 64


def _profile(profile_id: str, candidate: str) -> dict:
    return {
        "profile_id": profile_id,
        "candidate": candidate,
        "release_identity": f"{candidate}:test-release",
        "implementation_identity": f"{candidate}:test-implementation@immutable",
        "code_license": "test-license",
        "model_terms": "none in synthetic fixture",
        "dependency_chain": [f"{candidate}:test-dependency"],
        "supported_formats": ["pdf"],
        "runtime_requirements": ["cpu"],
        "external_dependencies": [],
        "identity_limitations": [],
    }


def _case(case_id: str, source_digest: str, *, pages: int = 3) -> dict:
    return {
        "case_id": case_id,
        "source_digest": source_digest,
        "page_count": pages,
        "traits": ["synthetic", "tables"],
        "required_checks": ["reading_order", "table_topology", "page_coverage"],
    }


def _observation(
    profile_id: str,
    case_id: str,
    source_digest: str,
    *,
    attempt: int = 1,
    status: str = "complete",
    output_digest: str | None = None,
    checks: dict[str, str] | None = None,
    pages: int | None = 3,
) -> dict:
    complete = status == "complete"
    return {
        "profile_id": profile_id,
        "case_id": case_id,
        "attempt": attempt,
        "status": status,
        "status_reason": None if complete else "synthetic runtime limitation",
        "observed_source_digest": source_digest,
        "config_digest": _digest("c"),
        "output_digest": output_digest if output_digest is not None else (_digest("d") if complete else None),
        "elapsed_seconds": 2.5 if complete else None,
        "peak_ram_mb": 512.0 if complete else None,
        "peak_vram_mb": None,
        "page_count_observed": pages if complete else None,
        "checks": checks
        or {
            "reading_order": "pass" if complete else "not_observed",
            "table_topology": "pass" if complete else "not_observed",
            "page_coverage": "pass" if complete else "not_observed",
        },
        "warnings": [],
        "errors": [],
        "output_locator_kinds": ["page", "section"] if complete else [],
    }


def _campaign() -> dict:
    case_a_digest = _digest("a")
    case_b_digest = _digest("b")
    profiles = [_profile("docling-baseline", "docling"), _profile("marker-fast", "marker")]
    cases = [_case("case-01", case_a_digest), _case("case-02", case_b_digest)]
    observations = []
    for profile in profiles:
        observations.extend(
            [
                _observation(profile["profile_id"], "case-01", case_a_digest),
                _observation(profile["profile_id"], "case-02", case_b_digest),
            ]
        )
    return {
        "campaign_id": "synthetic-structural-qualification",
        "repository_ref": "388e382583930ed42aad5ee3354b6049c962c804",
        "profiles": profiles,
        "cases": cases,
        "observations": observations,
    }


def test_complete_same_corpus_campaign_is_reported_without_selecting_binding() -> None:
    report = summarize_campaign(_campaign())

    assert report["matrix_complete"] is True
    assert report["required_checks_fully_observed"] is True
    assert report["profile_reports"]["docling-baseline"]["missing_cases"] == []
    assert report["profile_reports"]["marker-fast"]["required_check_failures"] == []
    assert report["authority"] == {
        "selects_binding": False,
        "adopts_dependency": False,
        "admits_evidence": False,
        "replaces_source": False,
    }
    assert "preferred/fallback/watch/rejected" in report["decision_note"]


def test_source_digest_mismatch_fails_closed() -> None:
    campaign = _campaign()
    campaign["observations"][0]["observed_source_digest"] = _digest("e")

    with pytest.raises(StructuralQualificationError, match="source digest does not match"):
        validate_campaign(campaign)


def test_private_locator_or_content_fields_are_not_accepted() -> None:
    campaign = _campaign()
    campaign["cases"][0]["source_path"] = "/private/client/document.pdf"

    with pytest.raises(StructuralQualificationError, match="unsupported fields: source_path"):
        validate_campaign(campaign)


def test_not_executed_is_explicit_uncertainty_not_parser_failure() -> None:
    campaign = _campaign()
    digest = campaign["cases"][0]["source_digest"]
    campaign["observations"][2] = _observation(
        "marker-fast",
        "case-01",
        digest,
        status="not_executed",
    )

    report = summarize_campaign(campaign)
    marker = report["profile_reports"]["marker-fast"]

    assert report["matrix_complete"] is True
    assert report["required_checks_fully_observed"] is False
    assert marker["status_counts"]["not_executed"] == 1
    assert marker["required_check_failures"] == []
    assert len(marker["required_checks_not_observed"]) == 3
    assert "do not infer a winner" in report["decision_note"]


def test_repeatability_mismatch_is_visible_for_same_source_and_config() -> None:
    campaign = _campaign()
    original = campaign["observations"][0]
    repeated = deepcopy(original)
    repeated["attempt"] = 2
    repeated["output_digest"] = _digest("f")
    campaign["observations"].append(repeated)

    report = summarize_campaign(campaign)
    mismatches = report["profile_reports"]["docling-baseline"]["repeatability_mismatches"]

    assert mismatches == [
        {
            "case_id": "case-01",
            "config_digest": _digest("c"),
            "attempts": [1, 2],
        }
    ]


def test_page_loss_and_required_quality_failure_are_reported_separately() -> None:
    campaign = _campaign()
    campaign["observations"][0]["page_count_observed"] = 2
    campaign["observations"][0]["checks"]["table_topology"] = "fail"

    report = summarize_campaign(campaign)
    docling = report["profile_reports"]["docling-baseline"]

    assert docling["required_check_failures"] == [
        {"case_id": "case-01", "check_id": "table_topology"}
    ]
    assert docling["page_count_mismatches"] == [
        {"case_id": "case-01", "attempt": 1, "expected": 3, "observed": 2}
    ]


def test_missing_profile_case_row_keeps_matrix_incomplete() -> None:
    campaign = _campaign()
    campaign["observations"] = [
        observation
        for observation in campaign["observations"]
        if not (
            observation["profile_id"] == "marker-fast"
            and observation["case_id"] == "case-02"
        )
    ]

    report = summarize_campaign(campaign)

    assert report["matrix_complete"] is False
    assert report["profile_reports"]["marker-fast"]["missing_cases"] == ["case-02"]
    assert "do not infer a winner" in report["decision_note"]
