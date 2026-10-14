#!/usr/bin/env python3
"""Validation layer for the qualified Hermes Project variant laboratory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import run_hermes_runtime_lab_acceptance as base


class VariantLabAcceptanceError(base.LabAcceptanceError):
    pass


def _load(path: Path) -> dict[str, Any]:
    return base._load_json(path)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise VariantLabAcceptanceError(message)


def validate(artifacts: Path) -> dict[str, Any]:
    artifacts = artifacts.resolve()
    baseline = base.validate(artifacts)
    expected_version = str(baseline["hermes_version"])
    reconciliation = _load(artifacts / "return-receipt.json")
    fixture_state = _load(artifacts / "fixture-state.json")

    _require(
        reconciliation.get("kind") == "hermes_run_reconciliation",
        "variant run did not use the canonical reconciliation path",
    )
    _require(
        reconciliation.get("execution_result_stored") is True,
        "typed Execution Result was not stored",
    )
    _require(
        reconciliation.get("execution_result_id")
        == "execution-result.hermes-020-variant-lab",
        "wrong Execution Result identity",
    )
    _require(
        reconciliation.get("project_change_variant_count") == 2,
        "the real Hermes run did not produce exactly two alternatives",
    )
    _require(
        reconciliation.get("result_refs")
        == ["result.variant.zinc", "result.variant.ardoise"],
        "variant result references differ",
    )
    for key in (
        "variant_selected",
        "project_mutated",
        "decision_created",
        "evidence_admitted",
        "external_effect_authorized",
        "technical_receipt_is_evidence",
        "scheduler_effect",
        "retry_effect",
    ):
        _require(reconciliation.get(key) is False, f"unexpected true posture: {key}")

    recorded = reconciliation.get("recorded") or {}
    _require(recorded.get("execution_result_stored") is True, "fixture did not retain result")
    for key in (
        "variant_selected",
        "project_mutated",
        "decision_created",
        "evidence_admitted",
        "external_effect_authorized",
    ):
        _require(recorded.get(key) is False, f"fixture claims authority: {key}")

    returns = fixture_state.get("execution_result_returns") or []
    _require(len(returns) == 1, "fixture did not observe exactly one typed return")
    observed = returns[0]
    _require(
        observed.get("execution_result_id") == "execution-result.hermes-020-variant-lab",
        "fixture observed the wrong Execution Result",
    )
    _require(
        observed.get("task_contract_ref") == "task-contract-hermes-020-variant-lab",
        "fixture observed the wrong Task Contract",
    )
    _require(observed.get("project_ref") == "project-lab", "wrong Project scope")
    _require(observed.get("producer_version") == expected_version, "wrong producer version")
    _require(
        observed.get("result_kinds")
        == ["project_change_variant", "project_change_variant"],
        "wrong result kinds",
    )
    _require(
        observed.get("variant_labels") == ["option-zinc", "option-ardoise"],
        "wrong variant labels",
    )
    _require(
        observed.get("review_dispositions_present") is False,
        "Hermes returned a selection disposition",
    )

    summary = {
        **baseline,
        "kind": "hermes_project_change_variant_lab_acceptance",
        "project_change_variants_produced": 2,
        "execution_result_stored": True,
        "variant_selected": False,
        "project_mutated": False,
        "decision_created": False,
        "evidence_admitted": False,
        "external_effect_authorized": False,
        "limits": [
            "This qualifies an ephemeral GitHub-hosted laboratory installation only.",
            "The agency/NAS installation and production OpenWebUI path remain unobserved.",
            "The provider and Pantheon endpoint were deterministic local fixtures.",
            "The laboratory proves structured production, not human selection or Project application.",
        ],
    }
    (artifacts / "acceptance-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def _emit(payload: dict[str, Any], output: Path | None) -> None:
    rendered = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if output is None:
        print(rendered, end="")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    configure = sub.add_parser("configure")
    configure.add_argument("--hermes-home", type=Path, required=True)
    configure.add_argument("--fixture-url", required=True)
    configure.add_argument("--output", type=Path)

    wait_http = sub.add_parser("wait-http")
    wait_http.add_argument("--url", required=True)
    wait_http.add_argument("--bearer")
    wait_http.add_argument("--timeout", type=float, default=60.0)
    wait_http.add_argument("--output", type=Path)

    wait_run = sub.add_parser("wait-run")
    wait_run.add_argument("--base-url", required=True)
    wait_run.add_argument("--api-key", required=True)
    wait_run.add_argument("--run-id", required=True)
    wait_run.add_argument("--timeout", type=float, default=120.0)
    wait_run.add_argument("--output", type=Path, required=True)

    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("--artifacts", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "configure":
        _emit(base.configure(args.hermes_home, args.fixture_url), args.output)
    elif args.command == "wait-http":
        _emit(base.wait_http(args.url, args.bearer, args.timeout), args.output)
    elif args.command == "wait-run":
        _emit(
            base.wait_run(args.base_url, args.api_key, args.run_id, args.timeout),
            args.output,
        )
    elif args.command == "validate":
        _emit(validate(args.artifacts), None)
    else:  # pragma: no cover
        raise VariantLabAcceptanceError(f"unsupported command: {args.command}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except base.LabAcceptanceError as exc:
        print(f"Hermes Project variant lab acceptance refused: {exc}")
        raise SystemExit(1) from exc
