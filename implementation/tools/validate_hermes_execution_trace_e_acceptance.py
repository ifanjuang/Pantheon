#!/usr/bin/env python3
"""Post-hoc Phase E acceptance for the existing Hermes Runtime Lab artifacts.

This validator does not execute Hermes, mutate Pantheon, rebuild a trace, or create
an authority. It checks the bounded Runtime Return summary against artifacts already
produced by the governed synthetic lab, derives context-tool/refusal counts only from
Pantheon fixture routes, and verifies the active return contract still cannot turn a
runtime success into Work Issue closure or a governance promotion.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

ADMISSION_PREFIX = "/hermes/execution-admissions/"
EXPECTED_TOOL_IDS = ("pantheon_context_manifest", "pantheon_context_entity")
CORRELATION_FIELDS = (
    "admission_id",
    "launch_reservation_id",
    "snapshot_id",
    "snapshot_digest",
    "run_id",
)


class PhaseEAcceptanceError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PhaseEAcceptanceError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PhaseEAcceptanceError(f"{path} must contain a JSON object")
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PhaseEAcceptanceError(message)


def _assignment_literal(source: str, name: str) -> Any:
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(isinstance(target, ast.Name) and target.id == name for target in targets):
            try:
                return ast.literal_eval(node.value)
            except (TypeError, ValueError) as exc:
                raise PhaseEAcceptanceError(f"{name} is not a literal contract") from exc
    raise PhaseEAcceptanceError(f"{name} contract is missing")


def _imported_modules(source: str) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            prefix = node.module or ""
            if prefix:
                modules.add(prefix)
            modules.update(
                f"{prefix}.{alias.name}".strip(".")
                for alias in node.names
            )
    return modules


def validate(
    *,
    artifacts: Path,
    runtime_return_source: Path,
    work_issues_source: Path,
) -> dict[str, Any]:
    artifacts = artifacts.resolve()
    launch = _load_json(artifacts / "launch-receipt.json")
    reconciliation = _load_json(artifacts / "return-receipt.json")
    fixture_state = _load_json(artifacts / "fixture-state.json")

    run_id = str(launch.get("run_id") or "").strip()
    admission_id = str(launch.get("admission_id") or "").strip()
    _require(bool(run_id), "launch receipt has no run_id")
    _require(bool(admission_id), "launch receipt has no admission_id")
    _require(
        launch.get("automatic_retry_performed") is False,
        "launch receipt does not prove zero automatic retries",
    )
    _require(reconciliation.get("pantheon_return_recorded") is True, "Runtime Return was not recorded")

    trace = reconciliation.get("execution_trace_summary")
    _require(isinstance(trace, dict), "reconciliation did not expose execution_trace_summary")
    _require(trace.get("schema_version") == "hermes-execution-trace-summary-v1", "wrong trace schema")
    correlation = trace.get("correlation") or {}
    _require(isinstance(correlation, dict), "trace correlation is missing")
    _require(set(correlation) == set(CORRELATION_FIELDS), "trace correlation is not exact")
    for field in CORRELATION_FIELDS:
        _require(correlation.get(field) == launch.get(field), f"trace correlation mismatch: {field}")

    execution = trace.get("execution") or {}
    _require(execution.get("terminal_status") == "completed", "trace terminal status is not completed")
    _require(execution.get("retry_count") == 0, "trace retry_count is not the observed zero")
    provenance = trace.get("provenance") or {}
    _require(
        "execution.retry_count" in (provenance.get("binding_observed") or []),
        "retry_count is not classified as binding_observed",
    )
    _require(
        "execution.terminal_status" in (provenance.get("runtime_reported") or []),
        "terminal status is not classified as runtime_reported",
    )
    _require(trace.get("trace_refs") == [f"hermes://runs/{run_id}"], "trace ref does not match run_id")

    reads = [str(path) for path in fixture_state.get("pantheon_reads") or []]
    manifest_path = f"{ADMISSION_PREFIX}{admission_id}/active-context"
    admitted_entity_path = manifest_path + "/entities/project/project-lab"
    refused_entity_path = manifest_path + "/entities/project/project-outside"
    expected_reads = [manifest_path, admitted_entity_path, refused_entity_path]
    _require(
        sorted(reads) == sorted(expected_reads),
        "synthetic run performed an unexpected or repeated Pantheon context read",
    )
    manifest_count = reads.count(manifest_path)
    admitted_entity_count = reads.count(admitted_entity_path)
    refused_entity_count = reads.count(refused_entity_path)
    _require(manifest_count == 1, f"expected one manifest read, observed {manifest_count}")
    _require(admitted_entity_count == 1, f"expected one admitted entity read, observed {admitted_entity_count}")
    _require(refused_entity_count == 1, f"expected one refused entity read, observed {refused_entity_count}")

    tools = [
        {
            "tool_id": EXPECTED_TOOL_IDS[0],
            "call_count": manifest_count,
            "terminal_status": "completed",
        },
        {
            "tool_id": EXPECTED_TOOL_IDS[1],
            "call_count": admitted_entity_count + refused_entity_count,
            "terminal_status": "completed",
        },
    ]
    refusals = [{"code": "context_entity_not_admitted", "count": refused_entity_count}]

    writes = [str(path) for path in fixture_state.get("pantheon_writes") or []]
    expected_writes = {
        f"{ADMISSION_PREFIX}{admission_id}/launch-reservations",
        f"{ADMISSION_PREFIX}{admission_id}/runs/start",
        f"{ADMISSION_PREFIX}{admission_id}/runs/{run_id}/return",
    }
    _require(set(writes) == expected_writes, "synthetic run performed an unexpected Pantheon write")
    _require(len(writes) == len(expected_writes), "synthetic run repeated a Pantheon write")

    recorded = reconciliation.get("recorded") or {}
    _require(recorded.get("result_accepted") is False, "synthetic result was accepted")
    _require(recorded.get("evidence_admitted") is False, "synthetic return admitted Evidence")
    _require(recorded.get("project_mutated") is False, "synthetic return mutated the Project")

    try:
        runtime_source = runtime_return_source.read_text(encoding="utf-8")
        issue_source = work_issues_source.read_text(encoding="utf-8")
    except OSError as exc:
        raise PhaseEAcceptanceError(f"cannot read active return contract source: {exc}") from exc

    return_targets = _assignment_literal(issue_source, "RETURN_TO_ISSUE_STATUS")
    _require(isinstance(return_targets, dict), "RETURN_TO_ISSUE_STATUS is not a mapping")
    _require(return_targets.get("result_candidate") == "review", "runtime candidate no longer targets review")
    _require(return_targets.get("result_candidate") not in {"done", "cancelled"}, "runtime candidate auto-resolves Work Issue")

    _require('"decision_created": False' in runtime_source, "Runtime Return no longer states Decision non-creation")
    _require('"evidence_admitted": False' in runtime_source, "Runtime Return no longer states Evidence non-admission")
    _require('"external_effect_authorized": False' in runtime_source, "Runtime Return no longer states effect non-authorization")
    imported = {name.casefold() for name in _imported_modules(runtime_source)}
    _require(not any("knowledge" in name for name in imported), "Runtime Return imports a Knowledge owner")
    _require(not any("memory" in name for name in imported), "Runtime Return imports a memory owner")

    return {
        "kind": "hermes_execution_trace_phase_e_acceptance",
        "status": "passed",
        "run_id": run_id,
        "admission_id": admission_id,
        "exact_correlation_retained": True,
        "retry_count": 0,
        "governed_tools": tools,
        "refusals": refusals,
        "runtime_return_recorded": True,
        "work_issue_target_status": "review",
        "work_issue_auto_resolved": False,
        "evidence_admitted": False,
        "decision_created": False,
        "knowledge_or_memory_owner_reached": False,
        "external_effect_authorized": False,
        "unexpected_pantheon_writes": [],
        "provenance_notes": {
            "correlation": "persisted Runtime Return summary checked against launch receipt",
            "retry_count": "binding_observed from explicit automatic_retry_performed=false",
            "terminal_status": "runtime_reported in the persisted summary",
            "tools": "binding-observed from exact synthetic Pantheon context read routes",
            "refusals": "binding-observed from the exact out-of-scope Pantheon context read",
            "governance_non_effects": "bounded return contract plus exact synthetic Pantheon write set",
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--runtime-return-source", type=Path, required=True)
    parser.add_argument("--work-issues-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = validate(
        artifacts=args.artifacts,
        runtime_return_source=args.runtime_return_source,
        work_issues_source=args.work_issues_source,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PhaseEAcceptanceError as exc:
        print(f"Hermes execution trace Phase E acceptance refused: {exc}")
        raise SystemExit(1) from exc
