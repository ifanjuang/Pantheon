#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from typing import Any


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def record_scope(record: dict[str, Any]) -> dict[str, Any] | None:
    spec = record["spec"]
    return spec.get("authorized_scope") or spec.get("reviewed_scope")


def unique_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the first record for each identifier so projections remain schema-valid."""
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for record in records:
        record_id = record["metadata"]["id"]
        if record_id in seen:
            continue
        seen.add(record_id)
        result.append(record)
    return result


def invalid_projection(
    subject: str,
    scope: dict[str, Any],
    evaluation_time: str,
    records: list[dict[str, Any]],
    reason: str,
) -> dict[str, Any]:
    return build_projection(
        subject,
        scope,
        evaluation_time,
        "invalid-record-set",
        None,
        None,
        unique_records(records),
        [],
        [reason],
        ["Fail closed; the record set requires human review."],
    )


def build_projection(
    subject: str,
    scope: dict[str, Any],
    evaluation_time: str,
    outcome: str,
    decision_type: str | None,
    applicable_record_id: str | None,
    considered: list[dict[str, Any]],
    excluded: list[dict[str, str]],
    reasons: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    suffix = subject.removeprefix("handoff_candidate_")
    return {
        "api_version": "pantheon.next/v0alpha1",
        "kind": "CurrentDecisionProjection",
        "metadata": {
            "id": f"current_decision_projection_{suffix}",
            "created_at": evaluation_time,
            "status": "derived",
        },
        "spec": {
            "subject": subject,
            "scope": scope,
            "evaluation_time": evaluation_time,
            "outcome": outcome,
            "decision_type": decision_type,
            "applicable_record_id": applicable_record_id,
            "considered_record_ids": [r["metadata"]["id"] for r in unique_records(considered)],
            "excluded_records": excluded,
            "reasons": reasons,
            "warnings": warnings,
        },
        "governance": {
            "read_only": True,
            "execution_authorized": False,
            "activation_authorized": False,
            "permission_token": False,
        },
    }


def resolve_current_decision(
    records: list[dict[str, Any]],
    subject: str,
    scope: dict[str, Any],
    evaluation_time: str,
) -> dict[str, Any]:
    evaluation = parse_dt(evaluation_time)
    ids = [r["metadata"]["id"] for r in records]
    if len(ids) != len(set(ids)):
        return invalid_projection(subject, scope, evaluation_time, records, "Duplicate decision identifiers.")

    by_id = {r["metadata"]["id"]: r for r in records}
    for record in records:
        supersedes = record["spec"].get("supersedes")
        if supersedes is not None and supersedes not in by_id:
            return invalid_projection(
                subject,
                scope,
                evaluation_time,
                records,
                f"Orphan supersedes reference: {supersedes}.",
            )

    for start in ids:
        seen: set[str] = set()
        current = start
        while current:
            if current in seen:
                return invalid_projection(subject, scope, evaluation_time, records, "Supersession cycle detected.")
            seen.add(current)
            current = by_id[current]["spec"].get("supersedes")

    excluded: list[dict[str, str]] = []
    exact: list[dict[str, Any]] = []
    for record in records:
        record_id = record["metadata"]["id"]
        if record["spec"]["handoff_candidate"] != subject:
            excluded.append({"record_id": record_id, "reason": "subject-mismatch"})
            continue
        if record_scope(record) != scope:
            excluded.append({"record_id": record_id, "reason": "scope-mismatch"})
            continue
        if parse_dt(record["spec"]["effective_at"]) > evaluation:
            excluded.append({"record_id": record_id, "reason": "not-yet-effective"})
            continue
        exact.append(record)

    blockers: list[dict[str, Any]] = []
    active_approvals: list[dict[str, Any]] = []
    superseded_approval_ids: set[str] = set()
    for record in exact:
        kind = record["spec"]["decision"]
        if kind in {"revoke", "expire"}:
            target_id = record["spec"].get("supersedes")
            target = by_id.get(target_id)
            if (
                target is None
                or target["spec"]["decision"] != "approve"
                or target["spec"]["handoff_candidate"] != subject
                or record_scope(target) != scope
                or parse_dt(record["spec"]["effective_at"]) <= parse_dt(target["spec"]["effective_at"])
            ):
                return invalid_projection(
                    subject,
                    scope,
                    evaluation_time,
                    records,
                    "Invalid revocation or expiration target.",
                )
            superseded_approval_ids.add(target_id)
            blockers.append(record)
        elif kind == "refuse":
            blockers.append(record)

    for record in exact:
        if record["spec"]["decision"] != "approve":
            continue
        record_id = record["metadata"]["id"]
        if record_id in superseded_approval_ids:
            excluded.append({"record_id": record_id, "reason": "superseded"})
            continue
        expires_at = parse_dt(record["spec"]["expires_at"])
        if expires_at <= evaluation:
            excluded.append({"record_id": record_id, "reason": "naturally-expired"})
            continue
        active_approvals.append(record)

    applicable = active_approvals + blockers
    if len(applicable) > 1:
        return build_projection(
            subject,
            scope,
            evaluation_time,
            "ambiguous",
            None,
            None,
            exact,
            excluded,
            ["Multiple incompatible decisions are concurrently applicable."],
            ["Fail closed; human review required."],
        )
    if active_approvals:
        record = active_approvals[0]
        return build_projection(
            subject,
            scope,
            evaluation_time,
            "current",
            "approve",
            record["metadata"]["id"],
            exact,
            excluded,
            ["Exactly one approval is effective, unexpired and not superseded."],
            [],
        )
    if blockers:
        record = blockers[0]
        return build_projection(
            subject,
            scope,
            evaluation_time,
            "blocked",
            record["spec"]["decision"],
            record["metadata"]["id"],
            exact,
            excluded,
            [f"An effective {record['spec']['decision']} decision blocks the exact scope."],
            [],
        )
    return build_projection(
        subject,
        scope,
        evaluation_time,
        "none",
        None,
        None,
        exact,
        excluded,
        ["No decision is currently applicable to the exact subject and scope."],
        [],
    )


if __name__ == "__main__":
    raise SystemExit("Import resolve_current_decision from a read-only checker or local review tool.")
