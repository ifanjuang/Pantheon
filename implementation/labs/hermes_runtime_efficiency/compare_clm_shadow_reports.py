#!/usr/bin/env python3
"""Compare two passive CLM shadow-ranking reports without selecting a winner.

The intended use is reference BF16/vLLM vs a quantized local encoder using the
same CLM head and the same corpus.  This tool reports numerical/ranking drift
only.  It does not activate a model, select a Hermes action, admit Evidence or
authorize any effect.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

REPORT_SCHEMA_ID = "pantheon.clm_shadow_rank_report"
COMPARISON_SCHEMA_ID = "pantheon.clm_shadow_rank_comparison"
COMPARISON_REVISION = 1

AUTHORITY = {
    "qualification_lab_only": True,
    "selects_encoder": False,
    "selects_hermes_action": False,
    "dispatches_task": False,
    "authorizes_effect": False,
    "admits_evidence": False,
    "owns_persistence": False,
}


class CLMShadowComparisonError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CLMShadowComparisonError(f"cannot read CLM report: {exc}") from exc
    if not isinstance(raw, dict) or raw.get("schema_id") != REPORT_SCHEMA_ID:
        raise CLMShadowComparisonError("unexpected CLM shadow report schema")
    if raw.get("status") != "shadow_observation_only":
        raise CLMShadowComparisonError("CLM report is not a passive shadow observation")
    if not isinstance(raw.get("cases"), list) or not raw["cases"]:
        raise CLMShadowComparisonError("CLM report has no cases")
    return raw


def _pin_identity(report: dict[str, Any]) -> tuple[str, ...]:
    pin = report.get("qualification_pin") or {}
    fields = ("repository", "ref", "encoder_model", "encoder_revision", "head_sha256", "api_surface")
    values = tuple(str(pin.get(field) or "") for field in fields)
    if not all(values):
        raise CLMShadowComparisonError("CLM report lacks canonical pin identity")
    return values


def _case_map(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for case in report["cases"]:
        case_id = str(case.get("case_id") or "")
        if not case_id or case_id in out:
            raise CLMShadowComparisonError("CLM report case ids must be non-empty and unique")
        runs = case.get("runs")
        if not isinstance(runs, list) or not runs:
            raise CLMShadowComparisonError(f"CLM case {case_id} has no runs")
        out[case_id] = case
    return out


def _run_map(case: dict[str, Any]) -> dict[tuple[str, ...], dict[str, Any]]:
    out: dict[tuple[str, ...], dict[str, Any]] = {}
    for run in case["runs"]:
        order = run.get("input_order")
        if not isinstance(order, list) or not all(isinstance(item, str) for item in order):
            raise CLMShadowComparisonError("CLM run input_order must be a string list")
        key = tuple(order)
        if key in out:
            raise CLMShadowComparisonError("CLM case contains duplicate input order")
        out[key] = run
    return out


def _ranked_names(run: dict[str, Any]) -> list[str]:
    ranked = run.get("ranked")
    if not isinstance(ranked, list) or not ranked:
        raise CLMShadowComparisonError("CLM run has no ranked rows")
    names: list[str] = []
    for row in ranked:
        if not isinstance(row, dict) or not isinstance(row.get("candidate"), str):
            raise CLMShadowComparisonError("CLM ranked row is malformed")
        names.append(row["candidate"])
    if len(names) != len(set(names)):
        raise CLMShadowComparisonError("CLM ranked candidates must be unique")
    return names


def _probabilities(run: dict[str, Any]) -> dict[str, float]:
    ranked = run.get("ranked") or []
    out: dict[str, float] = {}
    for row in ranked:
        candidate = row.get("candidate")
        prob = row.get("prob")
        if not isinstance(candidate, str) or not isinstance(prob, (int, float)):
            raise CLMShadowComparisonError("CLM ranked probability is malformed")
        value = float(prob)
        if not math.isfinite(value):
            raise CLMShadowComparisonError("CLM ranked probability must be finite")
        out[candidate] = value
    return out


def compare_reports(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    base_corpus = baseline.get("corpus") or {}
    cand_corpus = candidate.get("corpus") or {}
    if base_corpus.get("sha256") != cand_corpus.get("sha256"):
        raise CLMShadowComparisonError("baseline and candidate corpus SHA-256 differ")
    if _pin_identity(baseline) != _pin_identity(candidate):
        raise CLMShadowComparisonError("baseline and candidate canonical CLM/head identity differ")

    candidate_runtime = candidate.get("runtime_metadata") or {}
    required_quantized = (
        "encoder_backend",
        "encoder_backend_version",
        "encoder_backend_ref",
        "encoder_artifact_repository",
        "encoder_artifact_revision",
        "encoder_artifact_file",
        "encoder_artifact_sha256",
        "encoder_quantization",
        "encoder_pooling",
    )
    missing = [field for field in required_quantized if not candidate_runtime.get(field)]
    if missing:
        raise CLMShadowComparisonError(
            "candidate report lacks quantized encoder identity: " + ", ".join(missing)
        )

    base_cases = _case_map(baseline)
    cand_cases = _case_map(candidate)
    if set(base_cases) != set(cand_cases):
        raise CLMShadowComparisonError("baseline and candidate case sets differ")

    total_runs = 0
    top1_agree = 0
    full_rank_agree = 0
    probability_abs_delta_sum = 0.0
    probability_value_count = 0
    max_abs_probability_delta = 0.0
    case_rows: list[dict[str, Any]] = []
    stability_regressions = 0
    expected_top1_regressions = 0

    for case_id in sorted(base_cases):
        base_case = base_cases[case_id]
        cand_case = cand_cases[case_id]
        base_runs = _run_map(base_case)
        cand_runs = _run_map(cand_case)
        if set(base_runs) != set(cand_runs):
            raise CLMShadowComparisonError(f"input-order set differs for case {case_id}")

        case_top1_agree = 0
        case_full_rank_agree = 0
        case_max_delta = 0.0
        for order in base_runs:
            base_run = base_runs[order]
            cand_run = cand_runs[order]
            base_names = _ranked_names(base_run)
            cand_names = _ranked_names(cand_run)
            if set(base_names) != set(cand_names):
                raise CLMShadowComparisonError(
                    f"ranked candidate set differs for case {case_id}"
                )
            total_runs += 1
            if base_names[0] == cand_names[0]:
                top1_agree += 1
                case_top1_agree += 1
            if base_names == cand_names:
                full_rank_agree += 1
                case_full_rank_agree += 1

            base_probs = _probabilities(base_run)
            cand_probs = _probabilities(cand_run)
            for name in base_names:
                delta = abs(base_probs[name] - cand_probs[name])
                probability_abs_delta_sum += delta
                probability_value_count += 1
                max_abs_probability_delta = max(max_abs_probability_delta, delta)
                case_max_delta = max(case_max_delta, delta)

        stability_regression = (
            bool(base_case.get("top_candidate_order_stable"))
            and not bool(cand_case.get("top_candidate_order_stable"))
        )
        expected_regression = (
            bool(base_case.get("expected_top1_all_orderings"))
            and not bool(cand_case.get("expected_top1_all_orderings"))
        )
        stability_regressions += int(stability_regression)
        expected_top1_regressions += int(expected_regression)
        run_count = len(base_runs)
        case_rows.append(
            {
                "case_id": case_id,
                "run_count": run_count,
                "top1_agreement_rate": case_top1_agree / run_count,
                "full_ranking_agreement_rate": case_full_rank_agree / run_count,
                "max_abs_probability_delta": case_max_delta,
                "order_stability_regression": stability_regression,
                "expected_top1_regression": expected_regression,
            }
        )

    if total_runs == 0 or probability_value_count == 0:
        raise CLMShadowComparisonError("comparison produced no observations")

    return {
        "schema_id": COMPARISON_SCHEMA_ID,
        "revision": COMPARISON_REVISION,
        "status": "comparison_observation_only",
        "corpus_sha256": base_corpus["sha256"],
        "canonical_identity": {
            "repository": baseline["qualification_pin"]["repository"],
            "ref": baseline["qualification_pin"]["ref"],
            "encoder_model": baseline["qualification_pin"]["encoder_model"],
            "encoder_revision": baseline["qualification_pin"]["encoder_revision"],
            "head_sha256": baseline["qualification_pin"]["head_sha256"],
        },
        "baseline_runtime_metadata": baseline.get("runtime_metadata") or {},
        "candidate_runtime_metadata": candidate_runtime,
        "summary": {
            "case_count": len(base_cases),
            "run_count": total_runs,
            "top1_agreement_count": top1_agree,
            "top1_agreement_rate": top1_agree / total_runs,
            "full_ranking_agreement_count": full_rank_agree,
            "full_ranking_agreement_rate": full_rank_agree / total_runs,
            "mean_abs_probability_delta": probability_abs_delta_sum / probability_value_count,
            "max_abs_probability_delta": max_abs_probability_delta,
            "order_stability_regression_count": stability_regressions,
            "expected_top1_regression_count": expected_top1_regressions,
        },
        "cases": case_rows,
        "authority": dict(AUTHORITY),
        "non_equivalences": [
            "ranking agreement != encoder equivalence",
            "synthetic fixture agreement != professional correctness",
            "lower VRAM != better model",
            "comparison observation != Evidence",
            "qualification != activation",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = compare_reports(_load(args.baseline), _load(args.candidate))
    payload = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
