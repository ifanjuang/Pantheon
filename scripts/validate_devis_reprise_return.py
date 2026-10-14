#!/usr/bin/env python3
"""Validate a caller-provided return for ``architecture_devis_reprise``.

Validation-only and read-only. The command reads files, checks structure, scope
and declared boundary flags, then prints JSON. It does not call Hermes or
OpenWebUI, probe an environment, approve, send, or admit anything to the
Registre Probatoire.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASK = ROOT / "docs/examples/vertical_devis_reprise/task_contract.devis-reprise.yaml"
DEFAULT_EVIDENCE_SCHEMA = ROOT / "schemas/evidence_pack.schema.yaml"

FAILURE_PRIORITY = [
    "FAIL_RUNTIME_UNAVAILABLE",
    "FAIL_EXTERNAL_EFFECT_ATTEMPTED",
    "FAIL_APPROVAL_COLLAPSE",
    "FAIL_REGISTER_ADMISSION_ATTEMPTED",
    "FAIL_MISSING_TASK_CONTRACT",
    "FAIL_MISSING_CONTEXT_PACK",
    "FAIL_MISSING_EVIDENCE_PACK",
    "FAIL_SCOPE_MISMATCH",
    "FAIL_INVALID_EVIDENCE_PACK",
    "FAIL_INVALID_RESULT_CANDIDATE",
    "FAIL_INVALID_RETURN",
]
ALLOWED_OUTCOMES = {"candidate_return", "capability_gap", "refusal"}
ALLOWED_RUNTIME = {"success", "partial", "blocked", "failed", "unavailable"}
ALLOWED_OUTPUT = {
    "candidate", "under_review", "deferred", "blocked_by_scope",
    "blocked_by_approval", "blocked_by_evidence", "blocked_by_capability_gap",
}
FORBIDDEN_KEYS = {"canonical_memory", "memory_candidate", "memory_candidates"}
EFFECT_FLAGS = {
    "external_effect_attempted": "FAIL_EXTERNAL_EFFECT_ATTEMPTED",
    "approval_claimed": "FAIL_APPROVAL_COLLAPSE",
    "register_admission_attempted": "FAIL_REGISTER_ADMISSION_ATTEMPTED",
}
RESULT_FLAGS = {
    "approve": "FAIL_APPROVAL_COLLAPSE",
    "approve_payment": "FAIL_APPROVAL_COLLAPSE",
    "sign": "FAIL_EXTERNAL_EFFECT_ATTEMPTED",
    "send": "FAIL_EXTERNAL_EFFECT_ATTEMPTED",
    "instruct_enterprise": "FAIL_EXTERNAL_EFFECT_ATTEMPTED",
    "register_admission": "FAIL_REGISTER_ADMISSION_ATTEMPTED",
}


def issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def load_mapping(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain a YAML mapping")
    return value


def is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_text_list(value: Any) -> bool:
    return isinstance(value, list) and all(is_text(item) for item in value)


def require_text(obj: dict[str, Any], field: str, path: str, problems: list[dict], code: str) -> None:
    if not is_text(obj.get(field)):
        problems.append(issue(code, f"{path}.{field}", f"{field} is required"))


def require_text_list(obj: dict[str, Any], field: str, path: str, problems: list[dict]) -> None:
    if not is_text_list(obj.get(field)):
        problems.append(
            issue("FAIL_INVALID_RETURN", f"{path}.{field}", f"{field} must be a list of non-empty strings")
        )


def forbidden_key_paths(value: Any, path: str = "external_run_return") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key).lower() in FORBIDDEN_KEYS:
                found.append(child_path)
            found.extend(forbidden_key_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(forbidden_key_paths(child, f"{path}[{index}]"))
    return found


def evidence_schema_problems(pack: dict[str, Any], schema: dict[str, Any]) -> list[dict[str, str]]:
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    problems = []
    for error in sorted(validator.iter_errors(pack), key=lambda item: list(item.path)):
        location = ".".join(map(str, error.path)) or "<root>"
        problems.append(
            issue(
                "FAIL_INVALID_EVIDENCE_PACK",
                f"external_run_return.evidence_pack_candidate.{location}",
                error.message,
            )
        )
    return problems


def validate_common(
    run: dict[str, Any], task: dict[str, Any], expected_ref: str | None
) -> tuple[list[dict], list[dict]]:
    problems: list[dict] = []
    warnings: list[dict] = []
    base = "external_run_return"

    contract_id = task.get("contract_id")
    if run.get("task_contract_id") != contract_id:
        problems.append(
            issue("FAIL_MISSING_TASK_CONTRACT", f"{base}.task_contract_id", f"expected {contract_id!r}")
        )
    require_text(run, "context_pack_id", base, problems, "FAIL_MISSING_CONTEXT_PACK")
    require_text(run, "run_id", base, problems, "FAIL_INVALID_RETURN")
    require_text(run, "pantheon_ref", base, problems, "FAIL_INVALID_RETURN")
    if expected_ref and run.get("pantheon_ref") != expected_ref:
        problems.append(
            issue("FAIL_INVALID_RETURN", f"{base}.pantheon_ref", f"expected Pantheon ref {expected_ref!r}")
        )

    runtime = run.get("runtime")
    if not isinstance(runtime, dict):
        problems.append(issue("FAIL_INVALID_RETURN", f"{base}.runtime", "runtime must be a mapping"))
    else:
        for field in ("name", "version", "model", "status"):
            require_text(runtime, field, f"{base}.runtime", problems, "FAIL_INVALID_RETURN")
        if runtime.get("status") not in ALLOWED_RUNTIME:
            problems.append(
                issue("FAIL_INVALID_RETURN", f"{base}.runtime.status", "unsupported runtime status")
            )
        if runtime.get("status") == "unavailable":
            problems.append(
                issue("FAIL_RUNTIME_UNAVAILABLE", f"{base}.runtime.status", "external runtime unavailable")
            )

    bridge = run.get("bridge")
    if not isinstance(bridge, dict):
        problems.append(issue("FAIL_INVALID_RETURN", f"{base}.bridge", "bridge must be a mapping"))
    else:
        for field in ("surface", "status", "implementation_ref"):
            require_text(bridge, field, f"{base}.bridge", problems, "FAIL_INVALID_RETURN")
        if bridge.get("surface") != "openwebui" or bridge.get("status") != "executed_external":
            warnings.append(
                issue("BRIDGE_NOT_PROVEN", f"{base}.bridge", "executed external OpenWebUI → Hermes bridge not proven")
            )

    require_text_list(run, "trace_refs", base, problems)
    if isinstance(run.get("trace_refs"), list) and not run["trace_refs"]:
        problems.append(issue("FAIL_INVALID_RETURN", f"{base}.trace_refs", "at least one trace reference is required"))

    effects = run.get("effect_report")
    if not isinstance(effects, dict):
        problems.append(issue("FAIL_INVALID_RETURN", f"{base}.effect_report", "effect_report must be a mapping"))
    else:
        for flag, code in EFFECT_FLAGS.items():
            if effects.get(flag) is not False:
                problems.append(issue(code, f"{base}.effect_report.{flag}", f"{flag} must be false"))

    if run.get("outcome_type") not in ALLOWED_OUTCOMES:
        problems.append(issue("FAIL_INVALID_RETURN", f"{base}.outcome_type", "unsupported outcome_type"))

    for path in forbidden_key_paths(run):
        problems.append(
            issue("FAIL_REGISTER_ADMISSION_ATTEMPTED", path, "retired or ambiguous return key is forbidden")
        )
    return problems, warnings


def validate_result(result: Any, run: dict[str, Any], task: dict[str, Any]) -> tuple[list[dict], list[dict]]:
    base = "external_run_return.result_candidate"
    problems: list[dict] = []
    warnings: list[dict] = []
    if not isinstance(result, dict):
        return [issue("FAIL_INVALID_RESULT_CANDIDATE", base, "result_candidate must be a mapping")], warnings

    expected = {
        "run_id": run.get("run_id"),
        "task_contract_id": task.get("contract_id"),
        "status": "candidate",
    }
    for field, value in expected.items():
        if result.get(field) != value:
            problems.append(issue("FAIL_INVALID_RESULT_CANDIDATE", f"{base}.{field}", f"expected {value!r}"))
    for field in ("summary", "candidate_opinion", "draft_moa_email", "required_human_decision"):
        require_text(result, field, base, problems, "FAIL_INVALID_RESULT_CANDIDATE")
    for field in ("uncertain_points", "discrepancy_notes", "external_commitment_risks"):
        if not is_text_list(result.get(field)):
            problems.append(
                issue("FAIL_INVALID_RESULT_CANDIDATE", f"{base}.{field}", "must be a list of non-empty strings")
            )
    if isinstance(result.get("uncertain_points"), list) and result["uncertain_points"]:
        warnings.append(issue("UNRESOLVED_POINTS", f"{base}.uncertain_points", "candidate contains unresolved points"))

    flags = result.get("forbidden_effects_confirmed")
    if not isinstance(flags, dict):
        problems.append(
            issue("FAIL_INVALID_RESULT_CANDIDATE", f"{base}.forbidden_effects_confirmed", "mapping required")
        )
    else:
        for flag, code in RESULT_FLAGS.items():
            if flags.get(flag) is not False:
                problems.append(issue(code, f"{base}.forbidden_effects_confirmed.{flag}", f"{flag} must be false"))
    return problems, warnings


def validate_evidence(
    pack: Any, task: dict[str, Any], schema: dict[str, Any]
) -> tuple[list[dict], list[dict]]:
    base = "external_run_return.evidence_pack_candidate"
    problems: list[dict] = []
    warnings: list[dict] = []
    if not isinstance(pack, dict):
        return [issue("FAIL_MISSING_EVIDENCE_PACK", base, "Evidence Pack Candidate mapping required")], warnings

    problems.extend(evidence_schema_problems(pack, schema))
    if pack.get("task_contract_id") != task.get("contract_id"):
        problems.append(issue("FAIL_MISSING_TASK_CONTRACT", f"{base}.task_contract_id", "Task Contract mismatch"))
    expected_scope = (task.get("scope") or {}).get("scope_id")
    if (pack.get("scope") or {}).get("scope_id") != expected_scope:
        problems.append(issue("FAIL_SCOPE_MISMATCH", f"{base}.scope.scope_id", f"expected {expected_scope!r}"))

    approval = pack.get("approval_state") or {}
    if approval.get("level") != task.get("approval_level") or approval.get("status") not in {"pending", "required", "blocked"}:
        problems.append(issue("FAIL_APPROVAL_COLLAPSE", f"{base}.approval_state", "approval must remain at the governed ceiling and unresolved"))
    for index, output in enumerate(pack.get("outputs") or []):
        if isinstance(output, dict) and output.get("status") not in ALLOWED_OUTPUT:
            problems.append(issue("FAIL_APPROVAL_COLLAPSE", f"{base}.outputs[{index}].status", "output must remain candidate or blocked"))
    for index, review in enumerate(pack.get("reviews") or []):
        if isinstance(review, dict) and review.get("status") not in {"pending", "needs_revision", "escalated"}:
            problems.append(issue("FAIL_APPROVAL_COLLAPSE", f"{base}.reviews[{index}].status", "runtime cannot record a final human review"))
    if isinstance(pack.get("user_decision_gate"), dict) and pack["user_decision_gate"].get("status") == "resolved":
        problems.append(issue("FAIL_APPROVAL_COLLAPSE", f"{base}.user_decision_gate.status", "runtime cannot resolve the human gate"))

    items = pack.get("evidence_items")
    expected_count = len(task.get("expected_evidence") or [])
    if not isinstance(items, list) or not items:
        warnings.append(issue("EVIDENCE_ITEMS_MISSING", f"{base}.evidence_items", "no structured evidence item returned"))
    else:
        if len(items) < expected_count:
            warnings.append(issue("EXPECTED_EVIDENCE_INCOMPLETE", f"{base}.evidence_items", "fewer items than expected by the Task Contract"))
        for index, item in enumerate(items):
            if isinstance(item, dict) and item.get("claim_status") in {"weak", "unverified", "contradicted", "out_of_scope"}:
                warnings.append(issue("WEAK_OR_UNVERIFIED_CLAIM", f"{base}.evidence_items[{index}].claim_status", f"claim status is {item.get('claim_status')!r}"))
    for index, source in enumerate(pack.get("sources") or []):
        if isinstance(source, dict) and source.get("status") != "selected_evidence":
            warnings.append(issue("SOURCE_NOT_SELECTED_EVIDENCE", f"{base}.sources[{index}].status", f"source status is {source.get('status')!r}"))
    return problems, warnings


def validate_external_return(
    bundle: dict[str, Any],
    task: dict[str, Any],
    evidence_schema: dict[str, Any],
    *,
    expected_pantheon_ref: str | None = None,
) -> dict[str, Any]:
    run = bundle.get("external_run_return")
    if not isinstance(run, dict):
        return report(False, "FAIL_INVALID_RETURN", None, None, [issue("FAIL_INVALID_RETURN", "external_run_return", "top-level mapping required")], [])

    problems, warnings = validate_common(run, task, expected_pantheon_ref)
    outcome = run.get("outcome_type")
    if outcome == "candidate_return":
        p, w = validate_result(run.get("result_candidate"), run, task)
        problems.extend(p); warnings.extend(w)
        p, w = validate_evidence(run.get("evidence_pack_candidate"), task, evidence_schema)
        problems.extend(p); warnings.extend(w)
    elif outcome == "capability_gap":
        gap = run.get("capability_gap")
        if not isinstance(gap, dict):
            problems.append(issue("FAIL_INVALID_RETURN", "external_run_return.capability_gap", "mapping required"))
        else:
            require_text(gap, "code", "external_run_return.capability_gap", problems, "FAIL_INVALID_RETURN")
            require_text(gap, "summary", "external_run_return.capability_gap", problems, "FAIL_INVALID_RETURN")
            require_text_list(gap, "missing", "external_run_return.capability_gap", problems)
        warnings.append(issue("CAPABILITY_GAP_RETURNED", "external_run_return.capability_gap", "structured capability gap returned"))
    elif outcome == "refusal":
        refusal = run.get("refusal")
        if not isinstance(refusal, dict):
            problems.append(issue("FAIL_INVALID_RETURN", "external_run_return.refusal", "mapping required"))
        else:
            require_text(refusal, "code", "external_run_return.refusal", problems, "FAIL_INVALID_RETURN")
            require_text(refusal, "reason", "external_run_return.refusal", problems, "FAIL_INVALID_RETURN")
            require_text_list(refusal, "blocked_by", "external_run_return.refusal", problems)
        warnings.append(issue("STRUCTURED_REFUSAL_RETURNED", "external_run_return.refusal", "bounded refusal returned"))

    if problems:
        codes = {item["code"] for item in problems}
        classification = next((code for code in FAILURE_PRIORITY if code in codes), "FAIL_INVALID_RETURN")
        return report(False, classification, run, outcome, problems, warnings)
    classification = "PASS_WITH_GOVERNANCE_GAPS" if warnings else "PASS_STRUCTURAL"
    return report(True, classification, run, outcome, [], warnings)


def report(ok: bool, classification: str, run: dict[str, Any] | None, outcome: Any, problems: list[dict], warnings: list[dict]) -> dict[str, Any]:
    return {
        "ok": ok,
        "classification": classification,
        "run_id": (run or {}).get("run_id"),
        "task_contract_id": (run or {}).get("task_contract_id"),
        "outcome_type": outcome,
        "problems": problems,
        "warnings": warnings,
        "authority_note": (
            "Structure, scope and self-reported boundary flags only; not proof of no external effect, "
            "professional truth, approval, send authorization or Registre Probatoire admission."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--return-file", type=Path, required=True)
    parser.add_argument("--task-contract", type=Path, default=DEFAULT_TASK)
    parser.add_argument("--evidence-schema", type=Path, default=DEFAULT_EVIDENCE_SCHEMA)
    parser.add_argument("--expected-pantheon-ref")
    args = parser.parse_args(argv)
    try:
        result = validate_external_return(
            load_mapping(args.return_file),
            load_mapping(args.task_contract),
            load_mapping(args.evidence_schema),
            expected_pantheon_ref=args.expected_pantheon_ref,
        )
    except Exception as exc:
        result = report(False, "FAIL_INVALID_RETURN", None, None, [issue("FAIL_INVALID_RETURN", "<input>", str(exc))], [])
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
