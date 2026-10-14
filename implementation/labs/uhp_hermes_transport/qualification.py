from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


SCHEMA = "pantheon/uhp-hermes-transport-observation/v1"
ARMS = {"native_runs", "uhp"}
RESULT_STATUSES = {"complete", "partial", "blocked", "failed", "unknown"}
TRISTATE = {"proven", "not_proven", "unknown"}

AUTHORITY = {
    "qualification_lab_only": True,
    "dispatch_owner": False,
    "authorizes_effect": False,
    "admits_evidence": False,
    "admits_source": False,
    "owns_memory": False,
    "selects_provider": False,
    "changes_runtime_configuration": False,
}


class TransportQualificationError(ValueError):
    pass


def canonical_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TransportQualificationError(f"{field} must be a non-empty string")
    return value.strip()


def _optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _text(value, field)


def _bool_or_none(value: Any, field: str) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise TransportQualificationError(f"{field} must be boolean or null")
    return value


def _bool(value: Any, field: str, *, default: bool = False) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise TransportQualificationError(f"{field} must be boolean")
    return value


def _non_negative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TransportQualificationError(f"{field} must be a non-negative integer")
    return value


def _finite_number_or_none(value: Any, field: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TransportQualificationError(
            f"{field} must be a finite non-negative number or null"
        )
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise TransportQualificationError(
            f"{field} must be a finite non-negative number or null"
        )
    return number


def _string_list(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise TransportQualificationError(f"{field} must be an array")
    out: list[str] = []
    for idx, item in enumerate(value):
        out.append(_text(item, f"{field}[{idx}]"))
    if len(out) != len(set(out)):
        raise TransportQualificationError(f"{field} must not contain duplicates")
    return out


def _sha_or_none(value: Any, field: str) -> str | None:
    if value is None:
        return None
    value = _text(value, field).lower()
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise TransportQualificationError(
            f"{field} must be a lowercase SHA-256 hex digest"
        )
    return value


def normalize_observation(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise TransportQualificationError("observation must be an object")
    schema = _text(raw.get("schema"), "schema")
    if schema != SCHEMA:
        raise TransportQualificationError(f"schema must equal {SCHEMA}")

    arm = _text(raw.get("arm"), "arm")
    if arm not in ARMS:
        raise TransportQualificationError(f"arm must be one of {sorted(ARMS)}")

    result_status = _text(raw.get("result_status"), "result_status")
    if result_status not in RESULT_STATUSES:
        raise TransportQualificationError(
            f"result_status must be one of {sorted(RESULT_STATUSES)}"
        )

    admission_correlation = _text(
        raw.get("admission_correlation", "unknown"), "admission_correlation"
    )
    if admission_correlation not in TRISTATE:
        raise TransportQualificationError(
            f"admission_correlation must be one of {sorted(TRISTATE)}"
        )

    effective_tool_surface = _text(
        raw.get("effective_tool_surface", "unknown"), "effective_tool_surface"
    )
    allowed_tool_states = TRISTATE | {"retained_native_observer"}
    if effective_tool_surface not in allowed_tool_states:
        raise TransportQualificationError(
            "effective_tool_surface must be proven, not_proven, unknown or "
            "retained_native_observer"
        )

    transient_file_case = _bool(
        raw.get("transient_file_case"),
        "transient_file_case",
    )
    artifact_case = _bool(
        raw.get("artifact_case"),
        "artifact_case",
    )
    stream_case = _bool(
        raw.get("stream_case"),
        "stream_case",
    )
    cancellation_case = _bool(
        raw.get("cancellation_case"),
        "cancellation_case",
    )
    ambiguous_submission_case = _bool(
        raw.get("ambiguous_submission_case"),
        "ambiguous_submission_case",
    )

    out = {
        "schema": schema,
        "case_id": _text(raw.get("case_id"), "case_id"),
        "arm": arm,
        "admission_id": _text(raw.get("admission_id"), "admission_id"),
        "task_contract_ref": _text(raw.get("task_contract_ref"), "task_contract_ref"),
        "context_pack_ref": _text(raw.get("context_pack_ref"), "context_pack_ref"),
        "execution_basis_digest": _sha_or_none(
            raw.get("execution_basis_digest"), "execution_basis_digest"
        ),
        "runtime_identity": _optional_text(
            raw.get("runtime_identity"), "runtime_identity"
        ),
        "hermes_identity": _optional_text(
            raw.get("hermes_identity"), "hermes_identity"
        ),
        "profile_identity": _optional_text(
            raw.get("profile_identity"), "profile_identity"
        ),
        "model_identity": _optional_text(raw.get("model_identity"), "model_identity"),
        "protocol_version": _optional_text(
            raw.get("protocol_version"), "protocol_version"
        ),
        "result_status": result_status,
        "core_conformance": _bool_or_none(
            raw.get("core_conformance"), "core_conformance"
        ),
        "extended_conformance": _bool_or_none(
            raw.get("extended_conformance"), "extended_conformance"
        ),
        "admission_correlation": admission_correlation,
        "effective_tool_surface": effective_tool_surface,
        "consequential_surface_isolated": _bool_or_none(
            raw.get("consequential_surface_isolated"),
            "consequential_surface_isolated",
        ),
        "task_submission_count": _non_negative_int(
            raw.get("task_submission_count", 0), "task_submission_count"
        ),
        "automatic_retry_count": _non_negative_int(
            raw.get("automatic_retry_count", 0), "automatic_retry_count"
        ),
        "stream_case": stream_case,
        "stream_order_valid": _bool_or_none(
            raw.get("stream_order_valid"), "stream_order_valid"
        ),
        "reconnect_read_valid": _bool_or_none(
            raw.get("reconnect_read_valid"), "reconnect_read_valid"
        ),
        "cancellation_case": cancellation_case,
        "cancellation_valid": _bool_or_none(
            raw.get("cancellation_valid"), "cancellation_valid"
        ),
        "ambiguous_submission_case": ambiguous_submission_case,
        "ambiguous_submission_retry_refused": _bool_or_none(
            raw.get("ambiguous_submission_retry_refused"),
            "ambiguous_submission_retry_refused",
        ),
        "transient_file_case": transient_file_case,
        "transient_file_sha256": _sha_or_none(
            raw.get("transient_file_sha256"), "transient_file_sha256"
        ),
        "transient_file_basis_bound": _bool_or_none(
            raw.get("transient_file_basis_bound"), "transient_file_basis_bound"
        ),
        "transient_file_expiry_fail_closed": _bool_or_none(
            raw.get("transient_file_expiry_fail_closed"),
            "transient_file_expiry_fail_closed",
        ),
        "transient_file_persisted_to_affaires": _bool_or_none(
            raw.get("transient_file_persisted_to_affaires"),
            "transient_file_persisted_to_affaires",
        ),
        "transient_file_persisted_to_hindsight": _bool_or_none(
            raw.get("transient_file_persisted_to_hindsight"),
            "transient_file_persisted_to_hindsight",
        ),
        "transient_file_admitted_as_source": _bool_or_none(
            raw.get("transient_file_admitted_as_source"),
            "transient_file_admitted_as_source",
        ),
        "artifact_case": artifact_case,
        "artifact_sha256": _sha_or_none(
            raw.get("artifact_sha256"), "artifact_sha256"
        ),
        "artifact_auto_promoted_to_source": _bool_or_none(
            raw.get("artifact_auto_promoted_to_source"),
            "artifact_auto_promoted_to_source",
        ),
        "artifact_auto_promoted_to_knowledge": _bool_or_none(
            raw.get("artifact_auto_promoted_to_knowledge"),
            "artifact_auto_promoted_to_knowledge",
        ),
        "artifact_auto_promoted_to_evidence": _bool_or_none(
            raw.get("artifact_auto_promoted_to_evidence"),
            "artifact_auto_promoted_to_evidence",
        ),
        "elapsed_seconds": _finite_number_or_none(
            raw.get("elapsed_seconds"), "elapsed_seconds"
        ),
        "deletion_assessment_complete": _bool(
            raw.get("deletion_assessment_complete"),
            "deletion_assessment_complete",
        ),
        "deletable_native_components": _string_list(
            raw.get("deletable_native_components"),
            "deletable_native_components",
        ),
        "retained_native_components": _string_list(
            raw.get("retained_native_components"),
            "retained_native_components",
        ),
        "notes": _string_list(raw.get("notes"), "notes"),
    }

    if out["execution_basis_digest"] is None:
        raise TransportQualificationError("execution_basis_digest is required")
    if arm == "uhp" and out["protocol_version"] is None:
        raise TransportQualificationError(
            "protocol_version is required for the uhp arm"
        )
    if transient_file_case and out["transient_file_sha256"] is None:
        raise TransportQualificationError(
            "transient_file_sha256 is required for transient_file_case"
        )
    if artifact_case and out["artifact_sha256"] is None:
        raise TransportQualificationError(
            "artifact_sha256 is required for artifact_case"
        )
    return out


def _known_identity_mismatch(
    baseline: dict[str, Any], candidate: dict[str, Any], field: str
) -> str | None:
    left, right = baseline[field], candidate[field]
    if left is not None and right is not None and left != right:
        return f"{field} differs between arms"
    return None


def compare_observations(
    baseline_raw: dict[str, Any], candidate_raw: dict[str, Any]
) -> dict[str, Any]:
    baseline = normalize_observation(baseline_raw)
    candidate = normalize_observation(candidate_raw)

    errors: list[str] = []
    unknowns: list[str] = []
    failures: list[str] = []

    if baseline["arm"] != "native_runs":
        errors.append("baseline arm must be native_runs")
    if candidate["arm"] != "uhp":
        errors.append("candidate arm must be uhp")
    if baseline["case_id"] != candidate["case_id"]:
        errors.append("case_id differs between arms")
    if baseline["admission_id"] == candidate["admission_id"]:
        errors.append("A/B arms must use distinct one-shot admission IDs")
    for field in ("task_contract_ref", "context_pack_ref", "execution_basis_digest"):
        if baseline[field] != candidate[field]:
            errors.append(f"{field} differs between arms")
    for field in (
        "stream_case",
        "cancellation_case",
        "ambiguous_submission_case",
        "transient_file_case",
        "artifact_case",
    ):
        if baseline[field] != candidate[field]:
            errors.append(f"{field} differs between arms")
    for field in (
        "runtime_identity",
        "hermes_identity",
        "profile_identity",
        "model_identity",
    ):
        mismatch = _known_identity_mismatch(baseline, candidate, field)
        if mismatch:
            errors.append(mismatch)
        elif baseline[field] is None or candidate[field] is None:
            unknowns.append(f"{field} parity is unknown")

    if baseline["result_status"] != "complete":
        unknowns.append(
            f"native baseline result_status={baseline['result_status']} is not complete"
        )

    if candidate["result_status"] in {"blocked", "failed"}:
        failures.append(f"UHP arm result_status={candidate['result_status']}")
    elif candidate["result_status"] != "complete":
        unknowns.append("UHP arm is not a complete execution")

    if candidate["core_conformance"] is False:
        failures.append("tested UHP server failed Core conformance")
    elif candidate["core_conformance"] is None:
        unknowns.append("Core conformance is unobserved for tested UHP server")

    if candidate["admission_correlation"] == "not_proven":
        failures.append("host-level Pantheon admission correlation was not proven")
    elif candidate["admission_correlation"] == "unknown":
        unknowns.append("host-level Pantheon admission correlation is unknown")

    tool_state = candidate["effective_tool_surface"]
    if tool_state == "not_proven":
        failures.append("effective Hermes tool surface is not proven")
    elif tool_state == "unknown":
        unknowns.append("effective Hermes tool surface is unknown")

    if candidate["consequential_surface_isolated"] is False:
        failures.append("consequential runtime surface isolation failed")
    elif candidate["consequential_surface_isolated"] is None:
        unknowns.append("consequential runtime surface isolation is unknown")

    if candidate["task_submission_count"] != 1:
        failures.append("UHP arm did not perform exactly one task submission")
    if candidate["automatic_retry_count"] != 0:
        failures.append("UHP arm performed an automatic retry")

    if candidate["stream_case"]:
        for field in ("stream_order_valid", "reconnect_read_valid"):
            if candidate[field] is False:
                failures.append(f"{field} failed")
            elif candidate[field] is None:
                unknowns.append(f"{field} is unknown")

    if candidate["cancellation_case"]:
        if candidate["cancellation_valid"] is False:
            failures.append("cancellation behavior failed")
        elif candidate["cancellation_valid"] is None:
            unknowns.append("cancellation behavior is unknown")

    if candidate["ambiguous_submission_case"]:
        value = candidate["ambiguous_submission_retry_refused"]
        if value is False:
            failures.append(
                "ambiguous submission caused or allowed an unsafe retry"
            )
        elif value is None:
            unknowns.append(
                "ambiguous-submission retry behavior is unknown"
            )

    if candidate["transient_file_case"]:
        if (
            baseline["transient_file_sha256"]
            != candidate["transient_file_sha256"]
        ):
            errors.append("transient_file_sha256 differs between arms")
        if candidate["extended_conformance"] is False:
            failures.append("tested UHP server failed Extended conformance")
        elif candidate["extended_conformance"] is None:
            unknowns.append(
                "Extended conformance is unobserved for transient-file case"
            )
        for field in (
            "transient_file_basis_bound",
            "transient_file_expiry_fail_closed",
        ):
            if candidate[field] is False:
                failures.append(f"{field} failed")
            elif candidate[field] is None:
                unknowns.append(f"{field} is unknown")
        for field in (
            "transient_file_persisted_to_affaires",
            "transient_file_persisted_to_hindsight",
            "transient_file_admitted_as_source",
        ):
            if candidate[field] is True:
                failures.append(
                    f"{field} must remain false for ask-only transport"
                )
            elif candidate[field] is None:
                unknowns.append(f"{field} is unknown")

    if candidate["artifact_case"]:
        if baseline["artifact_sha256"] != candidate["artifact_sha256"]:
            errors.append("artifact_sha256 differs between arms")
        if candidate["extended_conformance"] is False:
            failures.append("tested UHP server failed Extended conformance")
        elif candidate["extended_conformance"] is None:
            unknowns.append("Extended conformance is unobserved for artifact case")
        for field in (
            "artifact_auto_promoted_to_source",
            "artifact_auto_promoted_to_knowledge",
            "artifact_auto_promoted_to_evidence",
        ):
            if candidate[field] is True:
                failures.append(f"{field} must remain false")
            elif candidate[field] is None:
                unknowns.append(f"{field} is unknown")

    if errors:
        decision = "inconclusive"
    elif failures:
        decision = "reject"
    elif unknowns:
        decision = "inconclusive"
    elif not candidate["deletion_assessment_complete"]:
        decision = "watch"
    elif not candidate["deletable_native_components"]:
        decision = "reject"
    elif candidate["retained_native_components"]:
        decision = "partial_transport_only"
    else:
        decision = "replace_native_binding"

    elapsed_delta = None
    if (
        baseline["elapsed_seconds"] is not None
        and candidate["elapsed_seconds"] is not None
    ):
        elapsed_delta = (
            candidate["elapsed_seconds"] - baseline["elapsed_seconds"]
        )

    return {
        "object_type": "uhp_hermes_transport_qualification_report",
        "schema": "pantheon/uhp-hermes-transport-qualification/v1",
        "authority": AUTHORITY,
        "case_id": baseline["case_id"],
        "comparability": "pass" if not errors else "fail",
        "comparability_errors": errors,
        "qualification_failures": failures,
        "qualification_unknowns": unknowns,
        "decision": decision,
        "deletable_native_components": candidate[
            "deletable_native_components"
        ],
        "retained_native_components": candidate[
            "retained_native_components"
        ],
        "elapsed_seconds_delta": elapsed_delta,
        "non_equivalences": [
            "lab receipt != Evidence",
            "UHP task accepted != Pantheon authorization",
            "UHP file != Source admission",
            "UHP artifact != professional Source",
            "runtime success != authorization",
        ],
    }


def load_observation(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TransportQualificationError(
            f"cannot read {path}: {exc}"
        ) from exc
    if not isinstance(raw, dict):
        raise TransportQualificationError(
            f"{path} must contain one JSON object"
        )
    return raw


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compare native Hermes Runs and UHP transport observations "
            "for Pantheon-Next#1141"
        )
    )
    parser.add_argument("native", type=Path)
    parser.add_argument("uhp", type=Path)
    args = parser.parse_args()
    report = compare_observations(
        load_observation(args.native),
        load_observation(args.uhp),
    )
    print(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 1 if report["decision"] == "reject" else 0


if __name__ == "__main__":
    raise SystemExit(main())
