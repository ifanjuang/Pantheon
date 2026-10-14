"""Canonical Capability Passport validation and eligibility qualification.

This module validates the current flat Capability Passport schema from the
repository. It is read-only: validation and eligibility qualification are data,
not admission persistence, scoped activation or task authorization.
"""

from __future__ import annotations

from typing import Any

import yaml
from jsonschema import Draft202012Validator

from .repo import find_repo_root, read_repo_text


APPROVAL_LEVELS = ["C0", "C1", "C2", "C3", "C4", "C5"]
APPROVED_REVIEW_STATUS = "reviewed"
IMMUTABLE_ANCHORS = ("commit_ref", "content_digest", "package_digest")
OPERATION_FLAGS = (
    "reads_private_data",
    "writes_external_state",
    "can_execute_code",
    "can_send_to_external_party",
    "can_change_register",
    "can_promote_memory",
)


def _schema() -> dict[str, Any]:
    root = find_repo_root()
    loaded = yaml.safe_load(read_repo_text("schemas/capability_passport.schema.yaml", root))
    if not isinstance(loaded, dict):
        raise ValueError("Capability Passport schema must be a mapping")
    return loaded


def _path(error: Any) -> str:
    return ".".join(str(part) for part in error.absolute_path)


def _approval_at_least(value: Any, floor: str) -> bool:
    try:
        return APPROVAL_LEVELS.index(str(value)) >= APPROVAL_LEVELS.index(floor)
    except ValueError:
        return False


def _is_true(value: Any) -> bool:
    return value is True or value == "true"


def _immutable_anchor(candidate: dict[str, Any]) -> dict[str, str] | None:
    provenance = candidate.get("implementation_provenance")
    if not isinstance(provenance, dict):
        return None
    for kind in IMMUTABLE_ANCHORS:
        value = provenance.get(kind)
        if isinstance(value, str) and value.strip():
            return {"kind": kind, "value": value.strip()}
    return None


def validate_passport(candidate: dict[str, Any] | None) -> dict[str, Any]:
    """Validate one current Capability Passport and qualify review eligibility.

    A reviewed Passport is eligible for governance review only when it pins an
    exact implementation release. This function never activates a binding or
    authorizes task/run use.
    """

    candidate = candidate if isinstance(candidate, dict) else {}
    schema = _schema()
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(candidate), key=_path)
    problems = [{"path": _path(error), "message": error.message} for error in errors]

    gaps: list[str] = []
    status = candidate.get("status")
    anchor = _immutable_anchor(candidate)
    operation = candidate.get("operation")
    operation = operation if isinstance(operation, dict) else {}
    governance = candidate.get("governance")
    governance = governance if isinstance(governance, dict) else {}
    legacy_activation_state = governance.get("activation_state")
    legacy_task_authorization = governance.get("task_authorization")
    approval_required = governance.get("approval_required")

    if _is_true(operation.get("can_send_to_external_party")):
        if not _approval_at_least(approval_required, "C3"):
            gaps.append("can_send_to_external_party=true requires approval_required >= C3")
        if governance.get("user_decision_gate_required") is not True:
            gaps.append(
                "can_send_to_external_party=true requires user_decision_gate_required: true"
            )
    if _is_true(operation.get("writes_external_state")) and not _approval_at_least(
        approval_required, "C2"
    ):
        gaps.append("writes_external_state=true requires approval_required >= C2")
    if _is_true(operation.get("can_promote_memory")) and governance.get(
        "memory_behavior"
    ) not in {"candidate_only", "never_canonical"}:
        gaps.append(
            "can_promote_memory=true requires memory_behavior candidate_only or never_canonical"
        )

    unknowns = [name for name in OPERATION_FLAGS if operation.get(name) == "unknown"]
    if unknowns:
        gaps.append(
            "operation flags still unknown; review before eligibility: "
            + ", ".join(unknowns)
        )

    if status == APPROVED_REVIEW_STATUS and anchor is None:
        gaps.append(
            "reviewed Capability Passport requires exact implementation provenance "
            "with commit_ref, content_digest or package_digest"
        )

    # Preserve the explicit governance diagnostic even though the canonical schema
    # now rejects a positive Passport task authorization. Invalid shape and the
    # semantic non-equivalence are both useful to callers.
    if legacy_task_authorization == "task_authorized":
        gaps.append(
            "Capability Passport must not be task-authorized (visible != admitted; "
            "task authorization belongs to Task Contract / Execution Admission)"
        )

    valid = not problems
    exact_release_qualified = valid and status == APPROVED_REVIEW_STATUS and anchor is not None
    eligibility_posture = (
        "invalid"
        if not valid
        else "reviewed_exact_release"
        if exact_release_qualified and not gaps
        else "reviewed_with_governance_gaps"
        if status == APPROVED_REVIEW_STATUS
        else "candidate_or_nonreviewed"
    )

    return {
        "valid": valid,
        "ready_for_review": valid and not gaps,
        "passport_id": candidate.get("passport_id"),
        "status": status,
        "implementation_anchor": anchor,
        "exact_release_qualified": exact_release_qualified,
        "eligibility_posture": eligibility_posture,
        "problems": problems,
        "governance_gaps": gaps,
        "legacy_activation_state": legacy_activation_state,
        "task_authorization": legacy_task_authorization,
        "activation_owner": "CapabilityActivation exact-binding record",
        "task_authorization_owner": "Task Contract / Execution Admission",
        "authorization_effect": "none",
        "activation_effect": "none",
        "write_effect": False,
        "runtime_probe_performed": False,
        "next_human_decision": (
            "review exact release eligibility and any remaining governance gaps"
            if valid
            else "fix the Passport shape against the canonical schema"
        ),
        "non_equivalences": [
            "schema valid != admitted",
            "reviewed != task-authorized",
            "exact release known != safe",
            "Passport legacy activation hint != CapabilityActivation",
            "eligibility != activation",
            "eligibility != task authorization",
            "Capability Passport != Task Contract / Execution Admission",
            "runtime success != Evidence",
        ],
        "doctrine_refs": [
            "schemas/capability_passport.schema.yaml",
            "catalog/schemas/capability-activation.schema.json",
            "docs/governance/UNIFORM_CAPABILITY_GOVERNANCE.md",
            "docs/governance/CAPABILITY_REGISTRY.md",
            "docs/governance/TASK_CONTRACTS.md",
        ],
        "authority_note": (
            "Validation is not authorization. Passport eligibility qualification is data; "
            "scoped binding activation belongs to CapabilityActivation and task/run "
            "legitimacy remains downstream in Task Contract / Execution Admission."
        ),
    }