from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


LAB = Path(__file__).resolve().parents[1] / "labs" / "hermes_runtime_efficiency" / "compare_kv_cache.py"
SPEC = importlib.util.spec_from_file_location("pantheon_kv_cache_qualification", LAB)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

RuntimeEfficiencyQualificationError = MODULE.RuntimeEfficiencyQualificationError
compare_kv_cache_observations = MODULE.compare_kv_cache_observations


def _observation(**overrides):
    raw = {
        "case_id": "long-context-kv-cache-01",
        "variant": "f16",
        "runtime_identity": "nousresearch/hermes-agent:v2026.8.31",
        "model_identity": "qwen3.5:27b",
        "profile_identity": "pantheon-governed",
        "settings_digest": "sha256:full-f16",
        "invariant_settings_digest": "sha256:same-except-kv-cache",
        "kv_cache_type": "f16",
        "flash_attention": True,
        "peak_gpu_memory_bytes": 22_000_000_000,
        "input_tokens": 12000,
        "output_tokens": 1000,
        "llm_turns": 4,
        "tool_calls": 3,
        "elapsed_seconds": 40.0,
        "max_context_tokens": 65536,
        "repeated_context_tokens": 1000,
        "large_tool_result_count": 1,
        "large_tool_result_chars": 100000,
        "source_recall_checks": 2,
        "source_recall_passes": 2,
        "source_recall_check_ids": ["recall:S1:locator", "recall:S2:contradiction"],
        "required_quality_checks": {
            "source_locator_recoverable": True,
            "scope_unchanged": True,
        },
        "result_status": "complete",
        "retrieved_refs": ["S1", "S2"],
        "admitted_refs": ["S1", "S2"],
        "used_refs": ["S1"],
        "notes": ["synthetic KV-cache qualification fixture"],
    }
    raw.update(overrides)
    return raw


def test_q8_candidate_can_be_compared_when_only_controlled_setting_changes() -> None:
    report = compare_kv_cache_observations(
        _observation(),
        _observation(
            variant="q8_0",
            kv_cache_type="q8_0",
            settings_digest="sha256:full-q8",
            peak_gpu_memory_bytes=16_000_000_000,
            elapsed_seconds=39.0,
        ),
    )

    assert report["comparable"] is True
    assert report["quality_gate"] == "pass"
    assert report["controlled_experiment"]["setting"] == "OLLAMA_KV_CACHE_TYPE"
    assert report["controlled_experiment"]["baseline_value"] == "f16"
    assert report["controlled_experiment"]["candidate_value"] == "q8_0"
    assert report["resource_metrics"]["peak_gpu_memory_bytes"]["delta"] == -6_000_000_000
    assert report["resource_qualification"] == "memory_gain_observed"


def test_invariant_settings_mismatch_fails_closed() -> None:
    with pytest.raises(RuntimeEfficiencyQualificationError, match="invariant_settings_digest differs"):
        compare_kv_cache_observations(
            _observation(),
            _observation(
                variant="q8_0",
                kv_cache_type="q8_0",
                settings_digest="sha256:full-q8",
                invariant_settings_digest="sha256:different-common-settings",
            ),
        )


def test_flash_attention_is_required_on_both_variants() -> None:
    with pytest.raises(RuntimeEfficiencyQualificationError, match="Flash Attention must be enabled"):
        compare_kv_cache_observations(
            _observation(),
            _observation(
                variant="q8_0",
                kv_cache_type="q8_0",
                settings_digest="sha256:full-q8",
                flash_attention=False,
            ),
        )


def test_full_settings_digest_must_show_the_controlled_change() -> None:
    with pytest.raises(RuntimeEfficiencyQualificationError, match="settings_digest must differ"):
        compare_kv_cache_observations(
            _observation(),
            _observation(
                variant="q8_0",
                kv_cache_type="q8_0",
                settings_digest="sha256:full-f16",
            ),
        )


def test_only_f16_to_q8_0_pair_is_accepted() -> None:
    with pytest.raises(RuntimeEfficiencyQualificationError, match="candidate.kv_cache_type must be q8_0"):
        compare_kv_cache_observations(
            _observation(),
            _observation(
                variant="q4_0",
                kv_cache_type="q4_0",
                settings_digest="sha256:full-q4",
            ),
        )


def test_adapter_has_no_runtime_or_network_mutation_path() -> None:
    source = LAB.read_text(encoding="utf-8")
    for token in ("subprocess", "requests", "httpx", "systemctl", "OLLAMA_HOST="):
        assert token not in source
