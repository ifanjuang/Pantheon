from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


AUTHORITY = {
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

COST_METRICS = (
    "input_tokens",
    "output_tokens",
    "llm_turns",
    "tool_calls",
    "elapsed_seconds",
    "max_context_tokens",
    "repeated_context_tokens",
    "large_tool_result_count",
    "large_tool_result_chars",
)

ALLOWED_RESULT_STATUS = {"complete", "partial", "blocked", "failed", "unknown"}


class RuntimeEfficiencyQualificationError(ValueError):
    pass


def _require_text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeEfficiencyQualificationError(f"{field} must be a non-empty string")
    return value.strip()


def _optional_text(value: Any, *, field: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field=field)


def _optional_int(value: Any, *, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RuntimeEfficiencyQualificationError(f"{field} must be a non-negative integer or null")
    return value


def _optional_number(value: Any, *, field: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeEfficiencyQualificationError(f"{field} must be a finite non-negative number or null")
    number = float(value)
    if number < 0 or not math.isfinite(number):
        raise RuntimeEfficiencyQualificationError(f"{field} must be a finite non-negative number or null")
    return number


def _refs(value: Any, *, field: str) -> tuple[str, ...] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise RuntimeEfficiencyQualificationError(f"{field} must be a list of opaque refs or null")
    refs = tuple(_require_text(item, field=field) for item in value)
    if len(set(refs)) != len(refs):
        raise RuntimeEfficiencyQualificationError(f"{field} contains duplicate refs")
    return refs


def _required_quality_checks(value: Any) -> tuple[tuple[str, bool], ...]:
    if value is None:
        return ()
    if not isinstance(value, dict):
        raise RuntimeEfficiencyQualificationError("required_quality_checks must be an object")
    checks: list[tuple[str, bool]] = []
    for raw_name, raw_passed in sorted(value.items()):
        name = _require_text(raw_name, field="required_quality_checks key")
        if not isinstance(raw_passed, bool):
            raise RuntimeEfficiencyQualificationError(
                f"required_quality_checks.{name} must be boolean"
            )
        checks.append((name, raw_passed))
    return tuple(checks)


def _notes(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise RuntimeEfficiencyQualificationError("notes must be a list of strings")
    return tuple(_require_text(item, field="notes item") for item in value)


@dataclass(frozen=True)
class RunObservation:
    case_id: str
    variant: str
    runtime_identity: str
    model_identity: str | None
    profile_identity: str | None
    settings_digest: str | None
    input_tokens: int | None
    output_tokens: int | None
    llm_turns: int | None
    tool_calls: int | None
    elapsed_seconds: float | None
    max_context_tokens: int | None
    repeated_context_tokens: int | None
    large_tool_result_count: int | None
    large_tool_result_chars: int | None
    source_recall_checks: int | None
    source_recall_passes: int | None
    source_recall_check_ids: tuple[str, ...] | None
    required_quality_checks: tuple[tuple[str, bool], ...]
    result_status: str
    retrieved_refs: tuple[str, ...] | None
    admitted_refs: tuple[str, ...] | None
    used_refs: tuple[str, ...] | None
    notes: tuple[str, ...]

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> "RunObservation":
        if not isinstance(raw, dict):
            raise RuntimeEfficiencyQualificationError("observation must be a JSON object")

        status = _require_text(raw.get("result_status", "unknown"), field="result_status")
        if status not in ALLOWED_RESULT_STATUS:
            raise RuntimeEfficiencyQualificationError(f"unsupported result_status: {status}")

        source_checks = _optional_int(raw.get("source_recall_checks"), field="source_recall_checks")
        source_passes = _optional_int(raw.get("source_recall_passes"), field="source_recall_passes")
        source_check_ids = _refs(raw.get("source_recall_check_ids"), field="source_recall_check_ids")
        if (source_checks is None) != (source_passes is None):
            raise RuntimeEfficiencyQualificationError(
                "source_recall_checks and source_recall_passes must both be known or both be null"
            )
        if source_checks is not None and source_passes is not None and source_passes > source_checks:
            raise RuntimeEfficiencyQualificationError(
                "source_recall_passes cannot exceed source_recall_checks"
            )
        if source_checks is None and source_check_ids is not None:
            raise RuntimeEfficiencyQualificationError(
                "source_recall_check_ids require source_recall_checks/source_recall_passes"
            )
        if source_checks is not None:
            if source_check_ids is None:
                raise RuntimeEfficiencyQualificationError(
                    "source_recall_check_ids are required when source recall is observed"
                )
            if len(source_check_ids) != source_checks:
                raise RuntimeEfficiencyQualificationError(
                    "source_recall_check_ids length must equal source_recall_checks"
                )

        retrieved = _refs(raw.get("retrieved_refs"), field="retrieved_refs")
        admitted = _refs(raw.get("admitted_refs"), field="admitted_refs")
        used = _refs(raw.get("used_refs"), field="used_refs")
        lineage_known = (retrieved is not None, admitted is not None, used is not None)
        if any(lineage_known) and not all(lineage_known):
            raise RuntimeEfficiencyQualificationError(
                "retrieved_refs, admitted_refs and used_refs must be recorded together or all be null"
            )
        if retrieved is not None and admitted is not None and used is not None:
            if not set(admitted).issubset(retrieved):
                raise RuntimeEfficiencyQualificationError(
                    "lineage invariant violated: admitted must be a subset of retrieved"
                )
            if not set(used).issubset(admitted):
                raise RuntimeEfficiencyQualificationError(
                    "lineage invariant violated: used must be a subset of admitted"
                )

        return cls(
            case_id=_require_text(raw.get("case_id"), field="case_id"),
            variant=_require_text(raw.get("variant"), field="variant"),
            runtime_identity=_require_text(raw.get("runtime_identity"), field="runtime_identity"),
            model_identity=_optional_text(raw.get("model_identity"), field="model_identity"),
            profile_identity=_optional_text(raw.get("profile_identity"), field="profile_identity"),
            settings_digest=_optional_text(raw.get("settings_digest"), field="settings_digest"),
            input_tokens=_optional_int(raw.get("input_tokens"), field="input_tokens"),
            output_tokens=_optional_int(raw.get("output_tokens"), field="output_tokens"),
            llm_turns=_optional_int(raw.get("llm_turns"), field="llm_turns"),
            tool_calls=_optional_int(raw.get("tool_calls"), field="tool_calls"),
            elapsed_seconds=_optional_number(raw.get("elapsed_seconds"), field="elapsed_seconds"),
            max_context_tokens=_optional_int(raw.get("max_context_tokens"), field="max_context_tokens"),
            repeated_context_tokens=_optional_int(
                raw.get("repeated_context_tokens"), field="repeated_context_tokens"
            ),
            large_tool_result_count=_optional_int(
                raw.get("large_tool_result_count"), field="large_tool_result_count"
            ),
            large_tool_result_chars=_optional_int(
                raw.get("large_tool_result_chars"), field="large_tool_result_chars"
            ),
            source_recall_checks=source_checks,
            source_recall_passes=source_passes,
            source_recall_check_ids=source_check_ids,
            required_quality_checks=_required_quality_checks(raw.get("required_quality_checks")),
            result_status=status,
            retrieved_refs=retrieved,
            admitted_refs=admitted,
            used_refs=used,
            notes=_notes(raw.get("notes")),
        )

    def quality_check_map(self) -> dict[str, bool]:
        return dict(self.required_quality_checks)

    def as_jsonable(self) -> dict[str, Any]:
        result = asdict(self)
        result["required_quality_checks"] = self.quality_check_map()
        for field in (
            "source_recall_check_ids",
            "retrieved_refs",
            "admitted_refs",
            "used_refs",
            "notes",
        ):
            value = result[field]
            if value is not None:
                result[field] = list(value)
        return result


def _identity_comparability(
    baseline: RunObservation, candidate: RunObservation
) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    if baseline.case_id != candidate.case_id:
        raise RuntimeEfficiencyQualificationError("A/B comparison requires the exact same case_id")
    if baseline.variant == candidate.variant:
        raise RuntimeEfficiencyQualificationError("A/B comparison requires distinct variant names")
    if baseline.runtime_identity != candidate.runtime_identity:
        blockers.append("runtime_identity differs")

    for field in ("model_identity", "profile_identity", "settings_digest"):
        left = getattr(baseline, field)
        right = getattr(candidate, field)
        if left is not None and right is not None and left != right:
            blockers.append(f"{field} differs")
        elif left is None or right is None:
            warnings.append(f"{field} is not fully observed")
    return blockers, warnings


def _candidate_quality(
    baseline: RunObservation, candidate: RunObservation
) -> tuple[str, list[str], list[str]]:
    regressions: list[str] = []
    unknowns: list[str] = []

    if baseline.result_status != "complete":
        unknowns.append(f"baseline result_status is {baseline.result_status}; cost comparison requires complete")
    if candidate.result_status in {"blocked", "failed"}:
        regressions.append(f"candidate result_status is {candidate.result_status}")
    elif candidate.result_status != "complete":
        unknowns.append(f"candidate result_status is {candidate.result_status}; cost comparison requires complete")

    if candidate.source_recall_checks is None:
        unknowns.append("candidate source recall is unobserved")
    elif candidate.source_recall_passes != candidate.source_recall_checks:
        regressions.append("candidate failed one or more required source recall checks")

    baseline_quality = baseline.quality_check_map()
    candidate_quality = candidate.quality_check_map()
    for name, passed in candidate_quality.items():
        if not passed:
            regressions.append(f"candidate required quality check failed: {name}")
    for name, baseline_passed in baseline_quality.items():
        if name not in candidate_quality:
            unknowns.append(f"candidate missing baseline quality check: {name}")
        elif baseline_passed and not candidate_quality[name]:
            marker = f"candidate required quality check failed: {name}"
            if marker not in regressions:
                regressions.append(marker)

    if baseline.source_recall_checks is not None:
        if candidate.source_recall_checks is None:
            unknowns.append("candidate source recall cannot be compared with baseline")
        elif baseline.source_recall_check_ids != candidate.source_recall_check_ids:
            unknowns.append("source recall check perimeter differs between variants")
        elif (
            baseline.source_recall_passes is not None
            and candidate.source_recall_passes is not None
            and candidate.source_recall_passes < baseline.source_recall_passes
        ):
            regressions.append("candidate source recall regressed versus baseline")

    if regressions:
        return "regression", sorted(set(regressions)), sorted(set(unknowns))
    if unknowns:
        return "unknown", [], sorted(set(unknowns))
    return "pass", [], []


def _metric_delta(
    baseline: int | float | None, candidate: int | float | None
) -> dict[str, Any]:
    if baseline is None or candidate is None:
        return {
            "baseline": baseline,
            "candidate": candidate,
            "delta": None,
            "percent_change": None,
        }
    delta = candidate - baseline
    percent = None if baseline == 0 else (delta / baseline) * 100.0
    return {
        "baseline": baseline,
        "candidate": candidate,
        "delta": delta,
        "percent_change": percent,
    }


def compare_observations(
    baseline: RunObservation, candidate: RunObservation
) -> dict[str, Any]:
    blockers, warnings = _identity_comparability(baseline, candidate)
    quality_gate, quality_regressions, quality_unknowns = _candidate_quality(
        baseline, candidate
    )

    costs = {
        metric: _metric_delta(getattr(baseline, metric), getattr(candidate, metric))
        for metric in COST_METRICS
    }
    improved = [
        metric
        for metric, values in costs.items()
        if values["delta"] is not None and values["delta"] < 0
    ]
    worsened = [
        metric
        for metric, values in costs.items()
        if values["delta"] is not None and values["delta"] > 0
    ]
    unchanged = [metric for metric, values in costs.items() if values["delta"] == 0]
    unknown_costs = [metric for metric, values in costs.items() if values["delta"] is None]

    if blockers:
        decision = "inconclusive"
    elif quality_gate == "regression":
        decision = "reject_candidate"
    elif quality_gate == "unknown":
        decision = "inconclusive"
    elif not improved:
        decision = "no_measured_gain"
    elif worsened:
        decision = "mixed_cost_tradeoff"
    else:
        decision = "candidate_for_further_qualification"

    return {
        "kind": "hermes_runtime_efficiency_comparison",
        "case_id": baseline.case_id,
        "baseline_variant": baseline.variant,
        "candidate_variant": candidate.variant,
        "comparable": not blockers,
        "comparability_blockers": blockers,
        "comparability_warnings": warnings,
        "quality_gate": quality_gate,
        "quality_regressions": quality_regressions,
        "quality_unknowns": quality_unknowns,
        "cost_metrics": costs,
        "improved_cost_metrics": improved,
        "worsened_cost_metrics": worsened,
        "unchanged_cost_metrics": unchanged,
        "unknown_cost_metrics": unknown_costs,
        "decision": decision,
        "authority": AUTHORITY,
        "non_equivalences": [
            "fewer tokens != better result",
            "summary != source",
            "reduced context != Evidence",
            "runtime success != result validity",
            "compression != authorization",
            "fusion of tool calls != fusion of permissions",
            "projection != persistence",
        ],
    }


def load_observation(path: Path) -> RunObservation:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeEfficiencyQualificationError(f"cannot load observation: {path}") from exc
    return RunObservation.from_mapping(raw)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare two recorded governed-Hermes runtime observations."
    )
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()

    comparison = compare_observations(
        load_observation(args.baseline),
        load_observation(args.candidate),
    )
    print(json.dumps(comparison, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
