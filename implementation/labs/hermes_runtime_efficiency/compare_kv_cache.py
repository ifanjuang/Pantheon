from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


CORE_PATH = Path(__file__).with_name("compare.py")
SPEC = importlib.util.spec_from_file_location("pantheon_hermes_runtime_efficiency_core", CORE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load runtime-efficiency core: {CORE_PATH}")
CORE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CORE
SPEC.loader.exec_module(CORE)

RunObservation = CORE.RunObservation
RuntimeEfficiencyQualificationError = CORE.RuntimeEfficiencyQualificationError
compare_observations = CORE.compare_observations

SUPPORTED_BASELINE = "f16"
SUPPORTED_CANDIDATE = "q8_0"
CONTROLLED_SETTING = "OLLAMA_KV_CACHE_TYPE"


def _require_text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeEfficiencyQualificationError(f"{field} must be a non-empty string")
    return value.strip()


def _require_bool(value: Any, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise RuntimeEfficiencyQualificationError(f"{field} must be boolean")
    return value


def _require_non_negative_int(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RuntimeEfficiencyQualificationError(f"{field} must be a non-negative integer")
    return value


def _load_raw(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeEfficiencyQualificationError(f"cannot load observation: {path}") from exc
    if not isinstance(raw, dict):
        raise RuntimeEfficiencyQualificationError("observation must be a JSON object")
    return raw


def _controlled_fields(raw: dict[str, Any], *, side: str) -> dict[str, Any]:
    kv_cache_type = _require_text(raw.get("kv_cache_type"), field=f"{side}.kv_cache_type")
    flash_attention = _require_bool(raw.get("flash_attention"), field=f"{side}.flash_attention")
    invariant_digest = _require_text(
        raw.get("invariant_settings_digest"),
        field=f"{side}.invariant_settings_digest",
    )
    full_digest = _require_text(raw.get("settings_digest"), field=f"{side}.settings_digest")
    peak_gpu_memory_bytes = _require_non_negative_int(
        raw.get("peak_gpu_memory_bytes"),
        field=f"{side}.peak_gpu_memory_bytes",
    )
    return {
        "kv_cache_type": kv_cache_type,
        "flash_attention": flash_attention,
        "invariant_settings_digest": invariant_digest,
        "settings_digest": full_digest,
        "peak_gpu_memory_bytes": peak_gpu_memory_bytes,
    }


def compare_kv_cache_observations(
    baseline_raw: dict[str, Any], candidate_raw: dict[str, Any]
) -> dict[str, Any]:
    baseline_control = _controlled_fields(baseline_raw, side="baseline")
    candidate_control = _controlled_fields(candidate_raw, side="candidate")

    if baseline_control["kv_cache_type"] != SUPPORTED_BASELINE:
        raise RuntimeEfficiencyQualificationError(
            f"baseline.kv_cache_type must be {SUPPORTED_BASELINE}"
        )
    if candidate_control["kv_cache_type"] != SUPPORTED_CANDIDATE:
        raise RuntimeEfficiencyQualificationError(
            f"candidate.kv_cache_type must be {SUPPORTED_CANDIDATE}"
        )
    if not baseline_control["flash_attention"] or not candidate_control["flash_attention"]:
        raise RuntimeEfficiencyQualificationError(
            "Flash Attention must be enabled for both variants"
        )
    if baseline_control["invariant_settings_digest"] != candidate_control["invariant_settings_digest"]:
        raise RuntimeEfficiencyQualificationError(
            "invariant_settings_digest differs; more than the controlled KV-cache setting may have changed"
        )
    if baseline_control["settings_digest"] == candidate_control["settings_digest"]:
        raise RuntimeEfficiencyQualificationError(
            "settings_digest must differ when OLLAMA_KV_CACHE_TYPE changes"
        )

    # The core comparator requires settings parity. For this one-variable experiment,
    # compare the digest of settings with OLLAMA_KV_CACHE_TYPE removed while retaining
    # the complete digests in the controlled-experiment report below.
    baseline_core = dict(baseline_raw)
    candidate_core = dict(candidate_raw)
    for raw in (baseline_core, candidate_core):
        for field in (
            "kv_cache_type",
            "flash_attention",
            "invariant_settings_digest",
            "peak_gpu_memory_bytes",
            "controlled_setting_key",
            "controlled_setting_value",
        ):
            raw.pop(field, None)
    baseline_core["settings_digest"] = baseline_control["invariant_settings_digest"]
    candidate_core["settings_digest"] = candidate_control["invariant_settings_digest"]

    baseline = RunObservation.from_mapping(baseline_core)
    candidate = RunObservation.from_mapping(candidate_core)
    report = compare_observations(baseline, candidate)

    baseline_peak = baseline_control["peak_gpu_memory_bytes"]
    candidate_peak = candidate_control["peak_gpu_memory_bytes"]
    memory_delta = candidate_peak - baseline_peak
    memory_percent = None if baseline_peak == 0 else (memory_delta / baseline_peak) * 100.0

    if memory_delta < 0:
        memory_qualification = "memory_gain_observed"
    elif memory_delta > 0:
        memory_qualification = "memory_regression_observed"
    else:
        memory_qualification = "no_memory_gain_observed"

    report["controlled_experiment"] = {
        "setting": CONTROLLED_SETTING,
        "baseline_value": baseline_control["kv_cache_type"],
        "candidate_value": candidate_control["kv_cache_type"],
        "flash_attention": True,
        "baseline_settings_digest": baseline_control["settings_digest"],
        "candidate_settings_digest": candidate_control["settings_digest"],
        "invariant_settings_digest": baseline_control["invariant_settings_digest"],
    }
    report["resource_metrics"] = {
        "peak_gpu_memory_bytes": {
            "baseline": baseline_peak,
            "candidate": candidate_peak,
            "delta": memory_delta,
            "percent_change": memory_percent,
        }
    }
    report["resource_qualification"] = memory_qualification
    report["non_equivalences"].extend(
        [
            "KV-cache memory gain != model quality preservation",
            "qualification result != runtime activation",
        ]
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare recorded f16 and q8_0 Ollama KV-cache observations through the governed Hermes runtime-efficiency lab."
    )
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()

    report = compare_kv_cache_observations(_load_raw(args.baseline), _load_raw(args.candidate))
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
