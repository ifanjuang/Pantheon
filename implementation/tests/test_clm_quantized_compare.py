from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "labs"
    / "hermes_runtime_efficiency"
    / "compare_clm_shadow_reports.py"
)
SPEC = importlib.util.spec_from_file_location("pantheon_compare_clm_shadow_reports", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

CLMShadowComparisonError = MODULE.CLMShadowComparisonError
compare_reports = MODULE.compare_reports


def _report(*, quantized: bool, corpus_sha: str = "a" * 64, head_sha: str = "b" * 64):
    runtime = {
        "encoder_placement": "remote" if not quantized else "local",
        "encoder_transport": "ssh_local_forward" if not quantized else "loopback_direct",
        "encoder_node_label": "gpu-node/WSL" if not quantized else "linux-local",
    }
    if quantized:
        runtime.update(
            {
                "encoder_backend": "llama.cpp",
                "encoder_backend_version": "0.5.0",
                "encoder_backend_ref": "c" * 40,
                "encoder_artifact_repository": "Qwen/Qwen3-8B-GGUF",
                "encoder_artifact_revision": "a" * 40,
                "encoder_artifact_file": "Qwen3-8B-Q8_0.gguf",
                "encoder_artifact_sha256": "d" * 64,
                "encoder_quantization": "Q8_0",
                "encoder_pooling": "last",
            }
        )
    return {
        "schema_id": MODULE.REPORT_SCHEMA_ID,
        "status": "shadow_observation_only",
        "corpus": {"sha256": corpus_sha},
        "qualification_pin": {
            "repository": "Contrastive-LM/CLM",
            "ref": "e" * 40,
            "encoder_model": "Qwen/Qwen3-8B",
            "encoder_revision": "f" * 40,
            "head_sha256": head_sha,
            "api_surface": "/v1/rank",
        },
        "runtime_metadata": runtime,
        "cases": [
            {
                "case_id": "case-1",
                "top_candidate_order_stable": True,
                "expected_top1_all_orderings": True,
                "runs": [
                    {
                        "input_order": ["a", "b", "c"],
                        "top_candidate": "a",
                        "ranked": [
                            {"rank": 1, "candidate": "a", "prob": 0.8 if not quantized else 0.78},
                            {"rank": 2, "candidate": "b", "prob": 0.15 if not quantized else 0.17},
                            {"rank": 3, "candidate": "c", "prob": 0.05},
                        ],
                    },
                    {
                        "input_order": ["c", "b", "a"],
                        "top_candidate": "a",
                        "ranked": [
                            {"rank": 1, "candidate": "a", "prob": 0.75 if not quantized else 0.73},
                            {"rank": 2, "candidate": "b", "prob": 0.2 if not quantized else 0.22},
                            {"rank": 3, "candidate": "c", "prob": 0.05},
                        ],
                    },
                ],
            }
        ],
    }


def test_comparison_reports_rank_and_probability_drift_without_selecting() -> None:
    report = compare_reports(_report(quantized=False), _report(quantized=True))

    assert report["status"] == "comparison_observation_only"
    assert report["summary"]["top1_agreement_rate"] == 1.0
    assert report["summary"]["full_ranking_agreement_rate"] == 1.0
    assert report["summary"]["max_abs_probability_delta"] == pytest.approx(0.02)
    assert report["summary"]["order_stability_regression_count"] == 0
    assert report["summary"]["expected_top1_regression_count"] == 0
    assert report["authority"]["selects_encoder"] is False
    assert report["authority"]["authorizes_effect"] is False


def test_comparison_exposes_top1_and_stability_regression() -> None:
    candidate = _report(quantized=True)
    candidate["cases"][0]["top_candidate_order_stable"] = False
    candidate["cases"][0]["expected_top1_all_orderings"] = False
    candidate["cases"][0]["runs"][1]["top_candidate"] = "b"
    candidate["cases"][0]["runs"][1]["ranked"] = [
        {"rank": 1, "candidate": "b", "prob": 0.51},
        {"rank": 2, "candidate": "a", "prob": 0.44},
        {"rank": 3, "candidate": "c", "prob": 0.05},
    ]

    report = compare_reports(_report(quantized=False), candidate)

    assert report["summary"]["top1_agreement_rate"] == 0.5
    assert report["summary"]["order_stability_regression_count"] == 1
    assert report["summary"]["expected_top1_regression_count"] == 1


def test_comparison_requires_same_corpus_and_canonical_head() -> None:
    with pytest.raises(CLMShadowComparisonError, match="corpus SHA-256"):
        compare_reports(
            _report(quantized=False),
            _report(quantized=True, corpus_sha="9" * 64),
        )

    with pytest.raises(CLMShadowComparisonError, match="canonical CLM/head identity"):
        compare_reports(
            _report(quantized=False),
            _report(quantized=True, head_sha="1" * 64),
        )


def test_candidate_must_record_quantized_encoder_identity() -> None:
    candidate = _report(quantized=True)
    del candidate["runtime_metadata"]["encoder_artifact_sha256"]

    with pytest.raises(CLMShadowComparisonError, match="quantized encoder identity"):
        compare_reports(_report(quantized=False), candidate)
