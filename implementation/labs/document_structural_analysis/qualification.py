from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
STATUSES = {"complete", "partial", "blocked", "failed", "not_executed"}
CHECK_RESULTS = {"pass", "fail", "not_observed", "not_applicable"}

PROFILE_KEYS = {
    "profile_id",
    "candidate",
    "release_identity",
    "implementation_identity",
    "code_license",
    "model_terms",
    "dependency_chain",
    "supported_formats",
    "runtime_requirements",
    "external_dependencies",
    "identity_limitations",
}
CASE_KEYS = {"case_id", "source_digest", "page_count", "traits", "required_checks"}
OBSERVATION_KEYS = {
    "profile_id",
    "case_id",
    "attempt",
    "status",
    "status_reason",
    "observed_source_digest",
    "config_digest",
    "output_digest",
    "elapsed_seconds",
    "peak_ram_mb",
    "peak_vram_mb",
    "page_count_observed",
    "checks",
    "warnings",
    "errors",
    "output_locator_kinds",
}
CAMPAIGN_KEYS = {"campaign_id", "repository_ref", "profiles", "cases", "observations"}


class StructuralQualificationError(ValueError):
    pass


def _fail(message: str) -> None:
    raise StructuralQualificationError(message)


def _require_exact_keys(value: dict[str, Any], allowed: set[str], label: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        _fail(f"{label} contains unsupported fields: {', '.join(sorted(unknown))}")


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(f"{label} must be a non-empty string")
    return value.strip()


def _require_string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        _fail(f"{label} must be a list of strings")
    return value


def _require_digest(value: Any, label: str) -> str:
    digest = _require_text(value, label)
    if not DIGEST_RE.fullmatch(digest):
        _fail(f"{label} must be a lowercase sha256:<64-hex> digest")
    return digest


def _optional_measure(value: Any, label: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(f"{label} must be null or a number")
    parsed = float(value)
    if not math.isfinite(parsed) or parsed < 0:
        _fail(f"{label} must be finite and non-negative")
    return parsed


def _validate_profile(raw: Any, index: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        _fail(f"profiles[{index}] must be an object")
    _require_exact_keys(raw, PROFILE_KEYS, f"profiles[{index}]")
    required_text = (
        "profile_id",
        "candidate",
        "release_identity",
        "implementation_identity",
        "code_license",
        "model_terms",
    )
    for key in required_text:
        _require_text(raw.get(key), f"profiles[{index}].{key}")
    for key in (
        "dependency_chain",
        "supported_formats",
        "runtime_requirements",
        "external_dependencies",
        "identity_limitations",
    ):
        _require_string_list(raw.get(key), f"profiles[{index}].{key}")
    return raw


def _validate_case(raw: Any, index: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        _fail(f"cases[{index}] must be an object")
    _require_exact_keys(raw, CASE_KEYS, f"cases[{index}]")
    _require_text(raw.get("case_id"), f"cases[{index}].case_id")
    _require_digest(raw.get("source_digest"), f"cases[{index}].source_digest")
    page_count = raw.get("page_count")
    if isinstance(page_count, bool) or not isinstance(page_count, int) or page_count <= 0:
        _fail(f"cases[{index}].page_count must be a positive integer")
    _require_string_list(raw.get("traits"), f"cases[{index}].traits")
    checks = _require_string_list(raw.get("required_checks"), f"cases[{index}].required_checks")
    if not checks or len(checks) != len(set(checks)):
        _fail(f"cases[{index}].required_checks must be non-empty and unique")
    return raw


def _validate_observation(
    raw: Any,
    index: int,
    *,
    profiles: dict[str, dict[str, Any]],
    cases: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(raw, dict):
        _fail(f"observations[{index}] must be an object")
    _require_exact_keys(raw, OBSERVATION_KEYS, f"observations[{index}]")
    profile_id = _require_text(raw.get("profile_id"), f"observations[{index}].profile_id")
    case_id = _require_text(raw.get("case_id"), f"observations[{index}].case_id")
    if profile_id not in profiles:
        _fail(f"observations[{index}] references unknown profile_id {profile_id!r}")
    if case_id not in cases:
        _fail(f"observations[{index}] references unknown case_id {case_id!r}")

    attempt = raw.get("attempt")
    if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
        _fail(f"observations[{index}].attempt must be an integer >= 1")

    status = _require_text(raw.get("status"), f"observations[{index}].status")
    if status not in STATUSES:
        _fail(f"observations[{index}].status must be one of {sorted(STATUSES)}")
    reason = raw.get("status_reason")
    if status == "complete":
        if reason not in (None, ""):
            _fail(f"observations[{index}].status_reason must be null for complete runs")
    else:
        _require_text(reason, f"observations[{index}].status_reason")

    source_digest = _require_digest(
        raw.get("observed_source_digest"), f"observations[{index}].observed_source_digest"
    )
    if source_digest != cases[case_id]["source_digest"]:
        _fail(
            f"observations[{index}] source digest does not match immutable case {case_id!r}"
        )
    _require_digest(raw.get("config_digest"), f"observations[{index}].config_digest")

    output_digest = raw.get("output_digest")
    if status in {"complete", "partial"}:
        _require_digest(output_digest, f"observations[{index}].output_digest")
    elif output_digest is not None:
        _require_digest(output_digest, f"observations[{index}].output_digest")

    elapsed = _optional_measure(raw.get("elapsed_seconds"), f"observations[{index}].elapsed_seconds")
    _optional_measure(raw.get("peak_ram_mb"), f"observations[{index}].peak_ram_mb")
    _optional_measure(raw.get("peak_vram_mb"), f"observations[{index}].peak_vram_mb")
    if status == "complete" and elapsed is None:
        _fail(f"observations[{index}].elapsed_seconds is required for complete runs")

    page_count = raw.get("page_count_observed")
    if page_count is not None and (
        isinstance(page_count, bool) or not isinstance(page_count, int) or page_count < 0
    ):
        _fail(f"observations[{index}].page_count_observed must be null or an integer >= 0")
    if status == "complete" and page_count is None:
        _fail(f"observations[{index}].page_count_observed is required for complete runs")

    checks = raw.get("checks")
    if not isinstance(checks, dict):
        _fail(f"observations[{index}].checks must be an object")
    for check_id, result in checks.items():
        _require_text(check_id, f"observations[{index}].checks key")
        if result not in CHECK_RESULTS:
            _fail(
                f"observations[{index}].checks[{check_id!r}] must be one of {sorted(CHECK_RESULTS)}"
            )
    missing_checks = set(cases[case_id]["required_checks"]) - set(checks)
    if missing_checks:
        _fail(
            f"observations[{index}] omits required checks: {', '.join(sorted(missing_checks))}"
        )

    _require_string_list(raw.get("warnings"), f"observations[{index}].warnings")
    _require_string_list(raw.get("errors"), f"observations[{index}].errors")
    _require_string_list(
        raw.get("output_locator_kinds"), f"observations[{index}].output_locator_kinds"
    )
    return raw


def validate_campaign(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        _fail("campaign must be an object")
    _require_exact_keys(raw, CAMPAIGN_KEYS, "campaign")
    _require_text(raw.get("campaign_id"), "campaign.campaign_id")
    _require_text(raw.get("repository_ref"), "campaign.repository_ref")

    raw_profiles = raw.get("profiles")
    raw_cases = raw.get("cases")
    raw_observations = raw.get("observations")
    if not isinstance(raw_profiles, list) or not raw_profiles:
        _fail("campaign.profiles must be a non-empty list")
    if not isinstance(raw_cases, list) or not raw_cases:
        _fail("campaign.cases must be a non-empty list")
    if not isinstance(raw_observations, list):
        _fail("campaign.observations must be a list")

    profiles_list = [_validate_profile(item, index) for index, item in enumerate(raw_profiles)]
    cases_list = [_validate_case(item, index) for index, item in enumerate(raw_cases)]
    profiles = {item["profile_id"]: item for item in profiles_list}
    cases = {item["case_id"]: item for item in cases_list}
    if len(profiles) != len(profiles_list):
        _fail("profile_id values must be unique")
    if len(cases) != len(cases_list):
        _fail("case_id values must be unique")

    observations = [
        _validate_observation(item, index, profiles=profiles, cases=cases)
        for index, item in enumerate(raw_observations)
    ]
    identities = [(item["profile_id"], item["case_id"], item["attempt"]) for item in observations]
    if len(identities) != len(set(identities)):
        _fail("(profile_id, case_id, attempt) observation identities must be unique")
    return raw


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def summarize_campaign(raw: Any) -> dict[str, Any]:
    campaign = validate_campaign(raw)
    cases = {item["case_id"]: item for item in campaign["cases"]}
    observations_by_profile: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for observation in campaign["observations"]:
        observations_by_profile[observation["profile_id"]].append(observation)

    profile_reports: dict[str, Any] = {}
    all_matrix_rows_present = True
    all_required_checks_observed = True

    for profile in campaign["profiles"]:
        profile_id = profile["profile_id"]
        observations = observations_by_profile.get(profile_id, [])
        by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for observation in observations:
            by_case[observation["case_id"]].append(observation)

        missing_cases = sorted(set(cases) - set(by_case))
        if missing_cases:
            all_matrix_rows_present = False

        status_counts = Counter(item["status"] for item in observations)
        required_failures: list[dict[str, str]] = []
        required_not_observed: list[dict[str, str]] = []
        page_count_mismatches: list[dict[str, int | str]] = []
        repeatability_mismatches: list[dict[str, Any]] = []

        elapsed_values: list[float] = []
        ram_values: list[float] = []
        vram_values: list[float] = []

        for case_id, case_observations in by_case.items():
            case = cases[case_id]
            for observation in case_observations:
                if observation["elapsed_seconds"] is not None:
                    elapsed_values.append(float(observation["elapsed_seconds"]))
                if observation["peak_ram_mb"] is not None:
                    ram_values.append(float(observation["peak_ram_mb"]))
                if observation["peak_vram_mb"] is not None:
                    vram_values.append(float(observation["peak_vram_mb"]))
                if (
                    observation["page_count_observed"] is not None
                    and observation["page_count_observed"] != case["page_count"]
                ):
                    page_count_mismatches.append(
                        {
                            "case_id": case_id,
                            "attempt": observation["attempt"],
                            "expected": case["page_count"],
                            "observed": observation["page_count_observed"],
                        }
                    )
                for check_id in case["required_checks"]:
                    result = observation["checks"][check_id]
                    if result == "fail":
                        required_failures.append({"case_id": case_id, "check_id": check_id})
                    elif result == "not_observed":
                        required_not_observed.append({"case_id": case_id, "check_id": check_id})

            complete_by_config: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for observation in case_observations:
                if observation["status"] == "complete":
                    complete_by_config[observation["config_digest"]].append(observation)
            for config_digest, complete_runs in complete_by_config.items():
                digests = {item["output_digest"] for item in complete_runs}
                if len(complete_runs) > 1 and len(digests) > 1:
                    repeatability_mismatches.append(
                        {
                            "case_id": case_id,
                            "config_digest": config_digest,
                            "attempts": sorted(item["attempt"] for item in complete_runs),
                        }
                    )

        if required_not_observed:
            all_required_checks_observed = False

        profile_reports[profile_id] = {
            "candidate": profile["candidate"],
            "matrix_cases_present": sorted(by_case),
            "missing_cases": missing_cases,
            "status_counts": dict(sorted(status_counts.items())),
            "required_check_failures": required_failures,
            "required_checks_not_observed": required_not_observed,
            "page_count_mismatches": page_count_mismatches,
            "repeatability_mismatches": repeatability_mismatches,
            "median_elapsed_seconds": _median(elapsed_values),
            "median_peak_ram_mb": _median(ram_values),
            "median_peak_vram_mb": _median(vram_values),
        }

    return {
        "campaign_id": campaign["campaign_id"],
        "repository_ref": campaign["repository_ref"],
        "case_ids": sorted(cases),
        "profile_reports": profile_reports,
        "matrix_complete": all_matrix_rows_present,
        "required_checks_fully_observed": all_required_checks_observed,
        "decision_note": (
            "comparison evidence is structurally complete; assign preferred/fallback/watch/rejected "
            "only after human review of quality, provenance, operational cost and replacement complexity"
            if all_matrix_rows_present and all_required_checks_observed
            else "qualification remains incomplete; do not infer a winner from missing or not-observed data"
        ),
        "authority": {
            "selects_binding": False,
            "adopts_dependency": False,
            "admits_evidence": False,
            "replaces_source": False,
        },
    }


def _main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and summarize local document structural-analysis qualification observations."
    )
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    raw = json.loads(args.campaign.read_text(encoding="utf-8"))
    report = summarize_campaign(raw)
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
