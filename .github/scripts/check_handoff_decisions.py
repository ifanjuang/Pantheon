#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "catalog" / "schemas"
EXAMPLE_DIR = ROOT / "catalog" / "examples"

STATUS_BY_DECISION = {
    "approve": "approved",
    "refuse": "refused",
    "revoke": "revoked",
    "expire": "expired",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def parse_dt(value: str | None):
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_approval_history(path: Path, approvals: list[dict]) -> None:
    """Allow historical multiplicity, reject overlapping approval windows."""
    grouped: dict[tuple[str, str], list[tuple[datetime, datetime, str]]] = {}
    for approval in approvals:
        spec = approval["spec"]
        scope_key = json.dumps(spec["authorized_scope"], sort_keys=True, separators=(",", ":"))
        key = (spec["handoff_candidate"], scope_key)
        grouped.setdefault(key, []).append(
            (
                parse_dt(spec["effective_at"]),
                parse_dt(spec["expires_at"]),
                approval["metadata"]["id"],
            )
        )

    for windows in grouped.values():
        windows.sort(key=lambda item: item[0])
        for previous, current in zip(windows, windows[1:]):
            previous_start, previous_end, previous_id = previous
            current_start, _, current_id = current
            if previous_end > current_start:
                raise SystemExit(
                    f"{path.name}: approval windows overlap for {previous_id} and {current_id}; "
                    "historical multiplicity is allowed, concurrent applicability is not"
                )


def validate_example(path: Path) -> None:
    installation_schema = load(SCHEMA_DIR / "installation-candidate.schema.json")
    handoff_schema = load(SCHEMA_DIR / "provisioner-handoff-candidate.schema.json")
    decision_schema = load(SCHEMA_DIR / "handoff-decision.schema.json")
    data = load(path)

    installation = data["installation_candidate"]
    handoff = data["handoff_candidate"]
    decisions = [
        value
        for value in data.values()
        if isinstance(value, dict) and value.get("kind") == "HandoffDecision"
    ]

    Draft202012Validator(installation_schema, format_checker=FormatChecker()).validate(installation)
    Draft202012Validator(handoff_schema, format_checker=FormatChecker()).validate(handoff)
    validator = Draft202012Validator(decision_schema, format_checker=FormatChecker())
    for decision in decisions:
        validator.validate(decision)

    installation_id = installation["metadata"]["id"]
    handoff_id = handoff["metadata"]["id"]
    if handoff["metadata"]["installation_candidate_id"] != installation_id:
        raise SystemExit(f"{path.name}: handoff does not reference the installation candidate")

    selected_provisioner = handoff["spec"]["selected_provisioner"]
    if selected_provisioner not in installation["spec"]["allowed_provisioners"]:
        raise SystemExit(f"{path.name}: selected provisioner is not allowed by the installation candidate")

    decision_ids = [decision["metadata"]["id"] for decision in decisions]
    if len(decision_ids) != len(set(decision_ids)):
        raise SystemExit(f"{path.name}: duplicate handoff decision identifiers")

    by_id = {decision["metadata"]["id"]: decision for decision in decisions}
    approvals = []
    for decision in decisions:
        spec = decision["spec"]
        metadata = decision["metadata"]
        kind = spec["decision"]
        if metadata["status"] != STATUS_BY_DECISION[kind]:
            raise SystemExit(f"{path.name}: metadata.status does not match spec.decision for {metadata['id']}")
        if spec["handoff_candidate"] != handoff_id:
            raise SystemExit(f"{path.name}: decision does not reference the handoff candidate")
        if decision["governance"]["activation_authorized"]:
            raise SystemExit(f"{path.name}: handoff decision must not authorize activation")
        if decision["governance"]["approval_is_execution"]:
            raise SystemExit(f"{path.name}: approval must not be represented as execution")
        if decision["governance"]["automatic_approval"]:
            raise SystemExit(f"{path.name}: automatic approval is forbidden")

        effective = parse_dt(spec["effective_at"])
        created = parse_dt(metadata["created_at"])
        if effective is None or created is None or effective < created:
            raise SystemExit(f"{path.name}: effective_at must not precede created_at")

        if kind == "approve":
            approvals.append(decision)
            scope = spec["authorized_scope"]
            expires = parse_dt(spec["expires_at"])
            if expires is None or expires <= effective:
                raise SystemExit(f"{path.name}: approved handoff must expire after it becomes effective")
            if spec["decision_level"] not in {"C4", "C5"}:
                raise SystemExit(f"{path.name}: provisioner handoff approval requires C4 or C5")
            if spec["supersedes"] is not None:
                raise SystemExit(f"{path.name}: approval supersession is not supported by the current contract")
            if scope["resource"] != installation["spec"]["resource"]:
                raise SystemExit(f"{path.name}: approved resource differs from the installation candidate")
            if scope["configuration_ref"] != installation_id:
                raise SystemExit(f"{path.name}: approved configuration differs from the installation candidate")
            if scope["provisioner"] != selected_provisioner:
                raise SystemExit(f"{path.name}: approved provisioner differs from the handoff candidate")
            if scope["one_time"] is not True:
                raise SystemExit(f"{path.name}: handoff approval must remain one-time")
        else:
            supersedes = spec["supersedes"]
            if kind in {"revoke", "expire"}:
                if supersedes not in by_id:
                    raise SystemExit(f"{path.name}: {kind} must supersede an existing decision")
                previous = by_id[supersedes]
                if previous["spec"]["decision"] != "approve":
                    raise SystemExit(f"{path.name}: {kind} must supersede an approval")
                if effective <= parse_dt(previous["spec"]["effective_at"]):
                    raise SystemExit(f"{path.name}: {kind} must occur after approval")
                if spec["reviewed_scope"] != previous["spec"]["authorized_scope"]:
                    raise SystemExit(f"{path.name}: reviewed scope must exactly match the superseded approval")

    validate_approval_history(path, approvals)


def main() -> int:
    examples = sorted(EXAMPLE_DIR.glob("*handoff-decision*.json"))
    if not examples:
        raise SystemExit("no handoff decision fixtures found")
    for path in examples:
        validate_example(path)
    print(f"OK: {len(examples)} handoff decision fixture(s) are valid and bounded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
