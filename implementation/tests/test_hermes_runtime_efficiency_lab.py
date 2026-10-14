from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import pytest


LAB = Path(__file__).resolve().parents[1] / "labs" / "hermes_runtime_efficiency" / "compare.py"
SPEC = importlib.util.spec_from_file_location("pantheon_hermes_runtime_efficiency_1047", LAB)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

RunObservation = MODULE.RunObservation
RuntimeEfficiencyQualificationError = MODULE.RuntimeEfficiencyQualificationError
compare_observations = MODULE.compare_observations


def _observation(**overrides):
    raw = {
        "case_id": "large-tool-output-01",
        "variant": "native",
        "runtime_identity": "nousresearch/hermes-agent:v2026.9.11",
        "model_identity": "qualification-model",
        "profile_identity": "pantheon-governed",
        "settings_digest": "sha256:settings-1",
        "input_tokens": 10000,
        "output_tokens": 1500,
        "llm_turns": 8,
        "tool_calls": 12,
        "elapsed_seconds": 90.0,
        "max_context_tokens": 24000,
        "repeated_context_tokens": 5000,
        "large_tool_result_count": 3,
        "large_tool_result_chars": 250000,
        "source_recall_checks": 2,
        "source_recall_passes": 2,
        "source_recall_check_ids": ["recall:S1:locator", "recall:S2:contradiction"],
        "required_quality_checks": {
            "source_locator_recoverable": True,
            "scope_unchanged": True,
        },
        "result_status": "complete",
        "retrieved_refs": ["S1", "S2", "S3"],
        "admitted_refs": ["S1", "S2"],
        "used_refs": ["S1"],
        "notes": ["synthetic qualification fixture"],
    }
    raw.update(overrides)
    return RunObservation.from_mapping(raw)


def test_candidate_with_preserved_quality_and_lower_cost_is_only_further_qualification_candidate() -> None:
    baseline = _observation()
    candidate = _observation(
        variant="candidate",
        input_tokens=7000,
        output_tokens=1200,
        llm_turns=6,
        tool_calls=10,
        elapsed_seconds=70.0,
        max_context_tokens=18000,
        repeated_context_tokens=1500,
        large_tool_result_count=2,
        large_tool_result_chars=80000,
    )

    result = compare_observations(baseline, candidate)

    assert result["comparable"] is True
    assert result["quality_gate"] == "pass"
    assert result["decision"] == "candidate_for_further_qualification"
    assert result["cost_metrics"]["input_tokens"]["delta"] == -3000
    assert result["cost_metrics"]["input_tokens"]["percent_change"] == -30.0
    assert "input_tokens" in result["improved_cost_metrics"]
    assert result["authority"]["qualification_lab_only"] is True
    assert result["authority"]["changes_runtime_configuration"] is False
    assert result["authority"]["admits_evidence"] is False


def test_lower_token_candidate_is_rejected_when_required_source_recall_regresses() -> None:
    baseline = _observation()
    candidate = _observation(
        variant="candidate",
        input_tokens=4000,
        source_recall_passes=1,
    )

    result = compare_observations(baseline, candidate)

    assert result["quality_gate"] == "regression"
    assert result["decision"] == "reject_candidate"
    assert "candidate failed one or more required source recall checks" in result["quality_regressions"]
    assert result["cost_metrics"]["input_tokens"]["delta"] == -6000


def test_failed_required_quality_check_blocks_cost_preference() -> None:
    baseline = _observation()
    candidate = _observation(
        variant="candidate",
        input_tokens=3000,
        required_quality_checks={
            "source_locator_recoverable": False,
            "scope_unchanged": True,
        },
    )

    result = compare_observations(baseline, candidate)

    assert result["quality_gate"] == "regression"
    assert result["decision"] == "reject_candidate"
    assert "candidate required quality check failed: source_locator_recoverable" in result[
        "quality_regressions"
    ]


def test_unknown_cost_metric_stays_unknown_instead_of_becoming_zero() -> None:
    baseline = _observation(max_context_tokens=None)
    candidate = _observation(variant="candidate", max_context_tokens=None, input_tokens=9000)

    result = compare_observations(baseline, candidate)

    assert result["cost_metrics"]["max_context_tokens"] == {
        "baseline": None,
        "candidate": None,
        "delta": None,
        "percent_change": None,
    }
    assert "max_context_tokens" in result["unknown_cost_metrics"]


def test_missing_candidate_quality_observation_is_inconclusive_not_cheaper_is_better() -> None:
    baseline = _observation()
    candidate = _observation(
        variant="candidate",
        input_tokens=1000,
        source_recall_checks=None,
        source_recall_passes=None,
        source_recall_check_ids=None,
    )

    result = compare_observations(baseline, candidate)

    assert result["quality_gate"] == "unknown"
    assert result["decision"] == "inconclusive"
    assert "candidate source recall is unobserved" in result["quality_unknowns"]


def test_non_complete_baseline_or_candidate_cannot_win_on_lower_cost() -> None:
    partial_candidate = compare_observations(
        _observation(),
        _observation(variant="candidate", input_tokens=1000, result_status="partial"),
    )
    blocked_baseline = compare_observations(
        _observation(result_status="blocked"),
        _observation(variant="candidate", input_tokens=1000),
    )

    assert partial_candidate["quality_gate"] == "unknown"
    assert partial_candidate["decision"] == "inconclusive"
    assert any("candidate result_status is partial" in item for item in partial_candidate["quality_unknowns"])

    assert blocked_baseline["quality_gate"] == "unknown"
    assert blocked_baseline["decision"] == "inconclusive"
    assert any("baseline result_status is blocked" in item for item in blocked_baseline["quality_unknowns"])


def test_different_runtime_or_known_model_profile_settings_block_causal_comparison() -> None:
    baseline = _observation()
    candidate = _observation(
        variant="candidate",
        runtime_identity="nousresearch/hermes-agent:other",
        model_identity="other-model",
        profile_identity="other-profile",
        settings_digest="sha256:other-settings",
    )

    result = compare_observations(baseline, candidate)

    assert result["comparable"] is False
    assert result["decision"] == "inconclusive"
    assert set(result["comparability_blockers"]) == {
        "runtime_identity differs",
        "model_identity differs",
        "profile_identity differs",
        "settings_digest differs",
    }


def test_unknown_model_profile_or_settings_are_visible_warnings_not_silent_parity() -> None:
    baseline = _observation(model_identity=None, profile_identity=None, settings_digest=None)
    candidate = _observation(
        variant="candidate",
        model_identity=None,
        profile_identity=None,
        settings_digest=None,
        input_tokens=9000,
    )

    result = compare_observations(baseline, candidate)

    assert result["comparable"] is True
    assert set(result["comparability_warnings"]) == {
        "model_identity is not fully observed",
        "profile_identity is not fully observed",
        "settings_digest is not fully observed",
    }


def test_lineage_invariant_used_subset_admitted_subset_retrieved_is_enforced() -> None:
    with pytest.raises(
        RuntimeEfficiencyQualificationError,
        match="admitted must be a subset of retrieved",
    ):
        _observation(
            retrieved_refs=["S1"],
            admitted_refs=["S1", "S2"],
            used_refs=["S1"],
        )

    with pytest.raises(
        RuntimeEfficiencyQualificationError,
        match="used must be a subset of admitted",
    ):
        _observation(
            retrieved_refs=["S1", "S2"],
            admitted_refs=["S1"],
            used_refs=["S2"],
        )


def test_partial_lineage_observation_fails_closed() -> None:
    with pytest.raises(
        RuntimeEfficiencyQualificationError,
        match="must be recorded together",
    ):
        _observation(retrieved_refs=["S1"], admitted_refs=None, used_refs=None)


def test_same_case_is_required_and_variant_names_must_differ() -> None:
    baseline = _observation()

    with pytest.raises(
        RuntimeEfficiencyQualificationError,
        match="exact same case_id",
    ):
        compare_observations(
            baseline,
            _observation(case_id="other-case", variant="candidate"),
        )

    with pytest.raises(
        RuntimeEfficiencyQualificationError,
        match="distinct variant names",
    ):
        compare_observations(baseline, _observation())


def test_source_recall_perimeter_uses_stable_ids_not_only_count() -> None:
    baseline = _observation()
    candidate = _observation(
        variant="candidate",
        source_recall_checks=2,
        source_recall_passes=2,
        source_recall_check_ids=["recall:S1:locator", "recall:S3:different"],
        input_tokens=8000,
    )

    result = compare_observations(baseline, candidate)

    assert result["quality_gate"] == "unknown"
    assert result["decision"] == "inconclusive"
    assert "source recall check perimeter differs between variants" in result["quality_unknowns"]


def test_source_recall_check_ids_are_required_and_match_check_count() -> None:
    with pytest.raises(
        RuntimeEfficiencyQualificationError,
        match="source_recall_check_ids are required",
    ):
        _observation(source_recall_check_ids=None)

    with pytest.raises(
        RuntimeEfficiencyQualificationError,
        match="length must equal source_recall_checks",
    ):
        _observation(source_recall_check_ids=["only-one"])


def test_non_finite_elapsed_seconds_are_rejected() -> None:
    for value in (math.inf, -math.inf, math.nan):
        with pytest.raises(
            RuntimeEfficiencyQualificationError,
            match="finite non-negative number",
        ):
            _observation(elapsed_seconds=value)


def test_lab_has_no_product_or_runtime_integration_path() -> None:
    source = LAB.read_text(encoding="utf-8")
    forbidden = (
        "mvp_vertical",
        "subprocess",
        "requests",
        "httpx",
        "psycopg",
        "sol_pi",
        "@earendil-works/pi-coding-agent",
    )
    for token in forbidden:
        assert token not in source

    assert MODULE.AUTHORITY == {
        "qualification_lab_only": True,
        "installs_runtime": False,
        "changes_runtime_configuration": False,
        "owns_context": False,
        "owns_memory": False,
        "admits_evidence": False,
        "owns_persistence": False,
        "authorizes_effect": False,
        "selects_provider": False,
    }
