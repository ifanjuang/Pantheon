#!/usr/bin/env python3
"""Local/manual validator for the Pantheon Next MVP vertical fixture.

This script is deliberately report-only. It does not approve, send, persist,
call Hermes, call OpenWebUI, write to a database, run a scheduler, or act as a CI
merge gate.

It validates three independent layers:

1. YAML + candidate JSON Schema validation.
2. Cross-object reference validation.
3. Governance invariant validation.

Required local packages:

    python -m pip install PyYAML jsonschema

Example:

    python scripts/validate_mvp_fixture.py \
      --fixture docs/governance/examples/mvp_vertical_fixture/fixture.schema_targets.yaml \
      --schema schemas/mvp_governed_loop_objects.schema.yaml \
      --output docs/governance/examples/mvp_vertical_fixture/generated_reports/fixture.schema_targets.generated_report.yaml \
      --created-at 2026-07-13T00:00:00Z
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - local environment guard
    raise SystemExit(
        "Missing dependency: PyYAML. Install locally with `python -m pip install PyYAML`."
    ) from exc

try:
    import jsonschema
except ImportError as exc:  # pragma: no cover - local environment guard
    raise SystemExit(
        "Missing dependency: jsonschema. Install locally with `python -m pip install jsonschema`."
    ) from exc

CENTRAL_OBJECT_TYPES = {
    "task_contract",
    "result_candidate",
    "evidence_pack_candidate",
    "decision_record",
    "register_candidate",
}

ALIAS_FIELDS = {
    "task_contract": "contract_id",
    "result_candidate": "result_candidate_id",
    "evidence_pack_candidate": "evidence_pack_id",
    "decision_record": "decision_id",
    "register_candidate": "candidate_id",
}

DOES_NOT_MEAN = [
    "truth_validated",
    "approval_granted",
    "memory_admitted",
    "external_action_authorized",
    "runtime_accepted",
]

REPORT_STATUS_ALLOWED = {
    "invalid",
    "structurally_valid",
    "reviewable",
    "reviewable_with_warnings",
    "blocked",
}

FORBIDDEN_REPORT_WORDS = {
    "approved",
    "accepted",
    "safe",
    "trusted",
    "canonical",
}


def load_yaml_documents(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        raw_documents = list(yaml.safe_load_all(handle))

    documents: list[dict[str, Any]] = []
    for index, document in enumerate(raw_documents, start=1):
        if document is None:
            raise ValueError(f"empty YAML document at index {index}")
        if not isinstance(document, dict):
            raise TypeError(f"YAML document {index} must be a mapping")
        documents.append(document)
    return documents


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        document = yaml.safe_load(handle)
    if not isinstance(document, dict):
        raise TypeError(f"{path} must contain a YAML mapping")
    return document


def path_to_string(error_path: Any) -> str:
    parts = [str(part) for part in error_path]
    return ".".join(parts) if parts else "<root>"


def schema_validation(
    documents: list[dict[str, Any]], schema: dict[str, Any]
) -> dict[str, Any]:
    validator = jsonschema.Draft202012Validator(schema)
    errors: list[dict[str, Any]] = []
    object_counts: Counter[str] = Counter()

    for index, document in enumerate(documents, start=1):
        object_type = document.get("object_type")
        object_id = document.get("object_id")
        object_counts[str(object_type)] += 1

        if object_type not in CENTRAL_OBJECT_TYPES:
            errors.append(
                {
                    "document": index,
                    "object_id": object_id,
                    "path": "object_type",
                    "message": f"unsupported central object type: {object_type}",
                }
            )
            continue

        for error in sorted(validator.iter_errors(document), key=lambda item: list(item.path)):
            errors.append(
                {
                    "document": index,
                    "object_id": object_id,
                    "path": path_to_string(error.path),
                    "message": error.message,
                }
            )

    return {
        "status": "fail" if errors else "pass",
        "documents_checked": len(documents),
        "object_counts": dict(sorted(object_counts.items())),
        "errors": errors,
        "warnings": [
            "schema validation is structural only",
            "status strings are not enum-validated yet",
            "additionalProperties remains permissive",
        ],
    }


def collect_declared_sources(documents: list[dict[str, Any]]) -> set[str]:
    declared_sources: set[str] = set()
    for document in documents:
        if document.get("object_type") != "task_contract":
            continue
        scope = document.get("scope") or {}
        if not isinstance(scope, dict):
            continue
        for source in scope.get("declared_sources") or []:
            if isinstance(source, dict) and source.get("source_ref"):
                declared_sources.add(str(source["source_ref"]))
    return declared_sources


def add_reference_check(
    *,
    checked_refs: list[dict[str, Any]],
    missing_refs: list[dict[str, Any]],
    objects_by_id: dict[str, dict[str, Any]],
    from_object: dict[str, Any],
    field: str,
    expected_type: str | None = None,
) -> None:
    target = from_object.get(field)
    if not target:
        return

    from_id = str(from_object.get("object_id"))
    target_id = str(target)
    target_object = objects_by_id.get(target_id)

    if target_object is None:
        missing_refs.append(
            {
                "from": from_id,
                "field": field,
                "to": target_id,
                "reason": "referenced object_id not found",
            }
        )
        return

    if expected_type and target_object.get("object_type") != expected_type:
        missing_refs.append(
            {
                "from": from_id,
                "field": field,
                "to": target_id,
                "reason": f"expected {expected_type}, got {target_object.get('object_type')}",
            }
        )
        return

    checked_refs.append(
        {
            "from": from_id,
            "field": field,
            "to": target_id,
            "status": "pass",
        }
    )


def reference_validation(documents: list[dict[str, Any]]) -> dict[str, Any]:
    objects_by_id: dict[str, dict[str, Any]] = {}
    duplicate_ids: list[str] = []
    missing_refs: list[dict[str, Any]] = []
    checked_refs: list[dict[str, Any]] = []
    warnings: list[str] = []

    for document in documents:
        object_id = document.get("object_id")
        if not object_id:
            continue
        object_id = str(object_id)
        if object_id in objects_by_id:
            duplicate_ids.append(object_id)
        objects_by_id[object_id] = document

    declared_sources = collect_declared_sources(documents)

    for document in documents:
        object_type = document.get("object_type")
        object_id = str(document.get("object_id"))

        alias_field = ALIAS_FIELDS.get(str(object_type))
        if alias_field and document.get(alias_field) and document.get(alias_field) != object_id:
            missing_refs.append(
                {
                    "from": object_id,
                    "field": alias_field,
                    "to": str(document.get(alias_field)),
                    "reason": "object-specific alias does not match object_id",
                }
            )

        add_reference_check(
            checked_refs=checked_refs,
            missing_refs=missing_refs,
            objects_by_id=objects_by_id,
            from_object=document,
            field="applies_to",
        )
        add_reference_check(
            checked_refs=checked_refs,
            missing_refs=missing_refs,
            objects_by_id=objects_by_id,
            from_object=document,
            field="revision_of",
            expected_type="result_candidate",
        )
        add_reference_check(
            checked_refs=checked_refs,
            missing_refs=missing_refs,
            objects_by_id=objects_by_id,
            from_object=document,
            field="related_evidence_pack",
            expected_type="evidence_pack_candidate",
        )
        add_reference_check(
            checked_refs=checked_refs,
            missing_refs=missing_refs,
            objects_by_id=objects_by_id,
            from_object=document,
            field="created_because_of",
            expected_type="decision_record",
        )

        if object_type == "register_candidate":
            for basis in document.get("basis") or []:
                basis_value = str(basis)
                if basis_value in objects_by_id or basis_value in declared_sources:
                    checked_refs.append(
                        {
                            "from": object_id,
                            "field": "basis",
                            "to": basis_value,
                            "status": "pass",
                        }
                    )
                else:
                    missing_refs.append(
                        {
                            "from": object_id,
                            "field": "basis",
                            "to": basis_value,
                            "reason": "basis value is neither an object_id nor an accepted source_ref",
                        }
                    )

        if object_type == "evidence_pack_candidate":
            for item in document.get("evidence_items") or []:
                if not isinstance(item, dict):
                    continue
                source_ref = item.get("source_ref")
                if not source_ref:
                    continue
                source_ref = str(source_ref)
                if source_ref in declared_sources:
                    checked_refs.append(
                        {
                            "from": object_id,
                            "field": "evidence_items.source_ref",
                            "to": source_ref,
                            "status": "pass",
                        }
                    )
                else:
                    missing_refs.append(
                        {
                            "from": object_id,
                            "field": "evidence_items.source_ref",
                            "to": source_ref,
                            "reason": "source_ref is not declared in task contract scope",
                        }
                    )

    if duplicate_ids:
        missing_refs.extend(
            {
                "from": duplicate_id,
                "field": "object_id",
                "to": duplicate_id,
                "reason": "duplicate object_id",
            }
            for duplicate_id in sorted(set(duplicate_ids))
        )

    if len(declared_sources) > 1:
        warnings.append("source_ref values are not resolved against a canonical source registry yet")

    status = "fail" if missing_refs else "pass_with_warnings" if warnings else "pass"
    return {
        "status": status,
        "objects_indexed": len(objects_by_id),
        "missing_refs": missing_refs,
        "warnings": warnings,
        "checked_refs": checked_refs,
    }


def fail_invariant(
    failures: list[dict[str, Any]],
    *,
    invariant_id: str,
    object_id: str,
    field: str,
    observed: Any,
    expected: str,
    reason: str,
) -> None:
    failures.append(
        {
            "id": invariant_id,
            "severity": "blocking",
            "object_id": object_id,
            "field": field,
            "observed": observed,
            "expected": expected,
            "reason": reason,
        }
    )


def governance_invariant_validation(documents: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    warnings: list[str] = []
    checked_invariants: list[dict[str, Any]] = []

    results = [item for item in documents if item.get("object_type") == "result_candidate"]
    decisions = [item for item in documents if item.get("object_type") == "decision_record"]
    evidence_packs = [item for item in documents if item.get("object_type") == "evidence_pack_candidate"]
    register_candidates = [item for item in documents if item.get("object_type") == "register_candidate"]

    send_decisions_by_target = {
        decision.get("applies_to")
        for decision in decisions
        if decision.get("decision") == "authorize_external_send"
        or (decision.get("consequences") or {}).get("send_authorization") == "granted"
    }

    external_action_failures_before = len(failures)
    for result in results:
        object_id = str(result.get("object_id"))
        if result.get("external_action_authorized") is True and object_id not in send_decisions_by_target:
            fail_invariant(
                failures,
                invariant_id="no_external_action_from_draft",
                object_id=object_id,
                field="external_action_authorized",
                observed=True,
                expected="false unless a separate external-action decision exists",
                reason="draft output cannot authorize external action",
            )
    checked_invariants.append(
        {
            "id": "no_external_action_from_draft",
            "status": "fail" if len(failures) > external_action_failures_before else "pass",
        }
    )

    approve_failures_before = len(failures)
    for decision in decisions:
        if decision.get("decision") != "approve":
            continue
        object_id = str(decision.get("object_id"))
        consequences = decision.get("consequences") or {}
        if consequences.get("send_authorization") == "granted" or consequences.get("external_action") == "authorized":
            fail_invariant(
                failures,
                invariant_id="approve_does_not_authorize_send",
                object_id=object_id,
                field="consequences",
                observed=consequences,
                expected="send_authorization not_granted and external_action not_authorized",
                reason="candidate approval is not external send authorization",
            )
        else:
            warnings.append("approve is present but external action and retention remain separately governed")
    checked_invariants.append(
        {
            "id": "approve_does_not_authorize_send",
            "status": "fail" if len(failures) > approve_failures_before else "pass",
        }
    )

    memory_failures_before = len(failures)
    for decision in decisions:
        consequences = decision.get("consequences") or {}
        if consequences.get("register_candidate_creation") == "allowed" and consequences.get("memory_admission") != "not_granted":
            fail_invariant(
                failures,
                invariant_id="register_candidate_creation_is_not_memory_admission",
                object_id=str(decision.get("object_id")),
                field="consequences.memory_admission",
                observed=consequences.get("memory_admission"),
                expected="not_granted when register_candidate_creation is allowed",
                reason="creating a Register Candidate is not memory admission",
            )
    checked_invariants.append(
        {
            "id": "register_candidate_creation_is_not_memory_admission",
            "status": "fail" if len(failures) > memory_failures_before else "pass",
        }
    )

    pending_failures_before = len(failures)
    for candidate in register_candidates:
        object_id = str(candidate.get("object_id"))
        if candidate.get("status") != "pending_register_admission":
            fail_invariant(
                failures,
                invariant_id="register_candidate_must_remain_pending",
                object_id=object_id,
                field="status",
                observed=candidate.get("status"),
                expected="pending_register_admission until separate register admission exists",
                reason="Register Candidate is not admitted memory",
            )
        if candidate.get("not_memory_until_admitted") is not True:
            fail_invariant(
                failures,
                invariant_id="register_candidate_must_remain_pending",
                object_id=object_id,
                field="not_memory_until_admitted",
                observed=candidate.get("not_memory_until_admitted"),
                expected="true",
                reason="Register Candidate must explicitly remain non-memory",
            )
        if candidate.get("status") == "pending_register_admission":
            warnings.append("register_candidate remains pending_register_admission")
    checked_invariants.append(
        {
            "id": "register_candidate_must_remain_pending",
            "status": "fail" if len(failures) > pending_failures_before else "pass",
        }
    )

    human_failures_before = len(failures)
    for decision in decisions:
        if decision.get("decided_by") != "human_practitioner":
            fail_invariant(
                failures,
                invariant_id="human_decision_required",
                object_id=str(decision.get("object_id")),
                field="decided_by",
                observed=decision.get("decided_by"),
                expected="human_practitioner",
                reason="consequential decisions must name a human actor",
            )
    checked_invariants.append(
        {
            "id": "human_decision_required",
            "status": "fail" if len(failures) > human_failures_before else "pass",
        }
    )

    retrieval_failures_before = len(failures)
    forbidden_support_status = {"retrieved", "retrieval_trace", "proof", "proven_by_retrieval"}
    for evidence_pack in evidence_packs:
        for item in evidence_pack.get("evidence_items") or []:
            if not isinstance(item, dict):
                continue
            support_status = item.get("support_status")
            if support_status in forbidden_support_status:
                fail_invariant(
                    failures,
                    invariant_id="retrieval_is_not_evidence",
                    object_id=str(evidence_pack.get("object_id")),
                    field="evidence_items.support_status",
                    observed=support_status,
                    expected="support status independent from retrieval trace",
                    reason="retrieval is a finding aid, not proof",
                )
    checked_invariants.append(
        {
            "id": "retrieval_is_not_evidence",
            "status": "fail" if len(failures) > retrieval_failures_before else "pass",
        }
    )

    status = "fail" if failures else "pass_with_warnings" if warnings else "pass"
    return {
        "status": status,
        "invariant_failures": failures,
        "warnings": warnings,
        "checked_invariants": checked_invariants,
    }


def report_id_for_fixture(fixture_path: Path) -> str:
    if "failing_external_action" in fixture_path.name:
        return "mvp.fail.generated-validation-report-001"
    return "mvp.devis-reprise.generated-validation-report-001"


def determine_overall_status(
    schema_status: str, reference_status: str, governance_status: str
) -> tuple[str, str]:
    if schema_status == "fail":
        return "invalid", "schema validation failed"
    if reference_status == "fail":
        return "structurally_valid", "schema valid but references are incomplete"
    if governance_status == "fail":
        return "blocked", "structurally valid but governance-blocked"
    if "warnings" in {reference_status, governance_status} or reference_status.endswith("warnings") or governance_status.endswith("warnings"):
        return "reviewable", "structurally coherent enough for the next implementation step"
    return "structurally_valid", "structurally coherent with no validator warnings"


def build_report(fixture_path: Path, schema_path: Path, created_at: str) -> dict[str, Any]:
    documents = load_yaml_documents(fixture_path)
    schema = load_yaml_mapping(schema_path)

    schema_result = schema_validation(documents, schema)
    reference_result = reference_validation(documents)
    governance_result = governance_invariant_validation(documents)

    overall_status, overall_meaning = determine_overall_status(
        schema_result["status"], reference_result["status"], governance_result["status"]
    )

    if overall_status not in REPORT_STATUS_ALLOWED:
        raise ValueError(f"illegal report status: {overall_status}")
    if overall_status in FORBIDDEN_REPORT_WORDS:
        raise ValueError(f"forbidden report status: {overall_status}")

    return {
        "report_id": report_id_for_fixture(fixture_path),
        "status": overall_status,
        "fixture_target": str(fixture_path),
        "schema_ref": str(schema_path),
        "created_by": "scripts/validate_mvp_fixture.py",
        "created_at": created_at,
        "summary": {
            "schema_status": schema_result["status"],
            "reference_status": reference_result["status"],
            "governance_status": governance_result["status"],
            "overall_meaning": overall_meaning,
            "does_not_mean": DOES_NOT_MEAN,
        },
        "schema_validation": schema_result,
        "reference_validation": reference_result,
        "governance_invariants": governance_result,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an MVP fixture and emit a report-only YAML result.")
    parser.add_argument("--fixture", required=True, type=Path, help="Fixture YAML to validate.")
    parser.add_argument("--schema", required=True, type=Path, help="Candidate JSON Schema YAML.")
    parser.add_argument("--output", required=True, type=Path, help="Report YAML output path.")
    parser.add_argument(
        "--created-at",
        default="manual_local_run",
        help="Deterministic created_at value to include in the report.",
    )
    parser.add_argument(
        "--fail-on-blocked",
        action="store_true",
        help="Exit non-zero when the report status is blocked or invalid. Off by default to keep the tool report-only.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.fixture, args.schema, args.created_at)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(report, handle, sort_keys=False, allow_unicode=True)

    print(f"wrote {args.output} with status={report['status']}")
    if args.fail_on_blocked and report["status"] in {"blocked", "invalid"}:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
