"""Progressive request-handling projection.

Consumes governed conditions plus optional coordination relations and projects
the smallest useful governance handling. It does not parse raw language,
execute work, dispatch Roles, authorize effects, or persist workflow state.
"""

from __future__ import annotations

from typing import Any


# Implemented subset of ROLE_ACTIVATION.md mandatory_role_triggers.
ROLE_TRIGGER_MAP: dict[str, tuple[str, ...]] = {
    "complex_task": ("ATHENA",),
    "scope_split_required": ("ATHENA",),
    "multi_step_workflow": ("ATHENA",),
    "factual_claim": ("ARGOS",),
    "external_reference": ("ARGOS",),
    "source_required": ("ARGOS",),
    "evidence_gap": ("ARGOS",),
    "source_freshness_risk": ("ARGOS",),
    "provenance_unclear": ("ARGOS",),
    "memory_recall_requested": ("MNEMOSYNE",),
    "prior_decision_reuse": ("MNEMOSYNE",),
    "project_history_reuse": ("MNEMOSYNE",),
    "duplicate_or_supersession_risk": ("MNEMOSYNE",),
    "memory_candidate": ("MNEMOSYNE",),
    "memory_promotion": ("MNEMOSYNE", "THEMIS"),
    "approval_required": ("THEMIS",),
    "legal_or_professional_risk": ("THEMIS",),
    "external_effect": ("THEMIS",),
    "policy_conflict": ("THEMIS",),
    "liability_risk": ("THEMIS",),
    "unclear_output": ("APOLLO",),
    "narrative_or_editorial_work": ("APOLLO",),
    "delivery_quality_required": ("APOLLO",),
    "artifact_fabrication": ("HEPHAISTOS",),
    "external_transmission": ("IRIS",),
    "client_delivery": ("IRIS",),
    "public_output": ("IRIS",),
    "handoff_required": ("IRIS",),
    "recipient_specific_format": ("IRIS",),
}

# Compatibility only. New callers should prefer governed `conditions`.
_LEGACY_FIELD_TO_CONDITION = {
    "source_required": "source_required",
    "evidence_gap": "evidence_gap",
    "prior_state_required": "project_history_reuse",
    "version_or_supersession_risk": "duplicate_or_supersession_risk",
    "professional_position": "legal_or_professional_risk",
    "financial_or_contractual_effect": "legal_or_professional_risk",
    "liability_risk": "liability_risk",
    "external_effect": "external_effect",
    "external_transmission": "external_transmission",
    "recipient_specific_output": "recipient_specific_format",
    "artifact_required": "artifact_fabrication",
    "memory_promotion_requested": "memory_promotion",
    "complex_task": "complex_task",
    "multi_step_workflow": "multi_step_workflow",
}

_MATERIAL_RECONSULT_CONDITIONS = (
    "source_required",
    "evidence_gap",
    "source_freshness_risk",
    "provenance_unclear",
    "project_history_reuse",
    "duplicate_or_supersession_risk",
    "legal_or_professional_risk",
    "liability_risk",
    "external_effect",
    "external_transmission",
    "memory_promotion",
    "approval_required",
    "policy_conflict",
)

_SOURCE = {
    "factual_claim",
    "external_reference",
    "source_required",
    "evidence_gap",
    "source_freshness_risk",
    "provenance_unclear",
}
_CONTINUITY = {
    "memory_recall_requested",
    "prior_decision_reuse",
    "project_history_reuse",
    "duplicate_or_supersession_risk",
    "memory_candidate",
}
_RISK = {
    "approval_required",
    "legal_or_professional_risk",
    "external_effect",
    "policy_conflict",
    "liability_risk",
    "memory_promotion",
}
_STRUCTURE = {"complex_task", "scope_split_required", "multi_step_workflow"}
_DELIVERY = {
    "external_transmission",
    "client_delivery",
    "public_output",
    "handoff_required",
    "recipient_specific_format",
}

# First deterministic front edge from RITE_TRIGGER_CATALOGUE.md.
# The signal may surface attention only. It does not activate or authorize a Rite.
RITE_ATTENTION_SIGNALS: dict[str, dict[str, str]] = {
    "tests_pass_completion": {
        "signal_source": "completion_requirements:tests_pass",
        "question": "What would passing these tests still not establish?",
        "attention_failure": "tests_pass_treated_as_claim_proven",
        "related_rite": "autocritique_contradictoire",
        "default_mode": "mode_light",
        "effect": "attention_only",
    },
}


def _observations(request: dict[str, Any]) -> dict[str, Any]:
    value = request.get("observations")
    return value if isinstance(value, dict) else {}


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return []


def _conditions(request: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for value in _strings(request.get("conditions")):
        if value in ROLE_TRIGGER_MAP and value not in out:
            out.append(value)

    observations = _observations(request)
    for condition in ROLE_TRIGGER_MAP:
        if observations.get(condition) is True and condition not in out:
            out.append(condition)

    for field, condition in _LEGACY_FIELD_TO_CONDITION.items():
        if observations.get(field, request.get(field)) is True and condition not in out:
            out.append(condition)

    if request.get("transmission_requested") is True and "external_transmission" not in out:
        out.append("external_transmission")
    return out


def _viewpoints(conditions: list[str]) -> list[str]:
    roles: list[str] = []
    for condition in conditions:
        for role in ROLE_TRIGGER_MAP.get(condition, ()):
            if role not in roles:
                roles.append(role)
    return roles


def _pairs(value: Any) -> list[list[str]]:
    if not isinstance(value, list):
        return []
    out: list[list[str]] = []
    for item in value:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            pair = [str(item[0]), str(item[1])]
            if pair not in out:
                out.append(pair)
    return out


def _groups(value: Any) -> list[list[str]]:
    if not isinstance(value, list):
        return []
    out: list[list[str]] = []
    for item in value:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            group = [str(member) for member in item]
            if group not in out:
                out.append(group)
    return out


def _coordination(request: dict[str, Any]) -> dict[str, Any]:
    raw = request.get("coordination")
    if not isinstance(raw, dict):
        return {}

    result: dict[str, Any] = {}
    requires = _pairs(raw.get("requires"))
    independent = _groups(raw.get("independent"))
    branch_on = _strings(raw.get("branch_on"))
    repeat_until = _strings(raw.get("repeat_until"))

    if requires:
        result["requires"] = requires
    if independent:
        result["independent"] = independent
    if bool(raw.get("synthesize", False)):
        result["synthesize"] = True
    if branch_on:
        result["branch_on"] = branch_on
    if repeat_until:
        result["repeat_until"] = repeat_until
    return result


def _topology(coordination: dict[str, Any]) -> dict[str, str] | None:
    """Derive existing topology from generic relations, never from Role names."""
    if coordination.get("requires"):
        return {
            "suggested": "sequential_handoff",
            "reason": "explicit dependency requires one state to precede another",
        }
    if coordination.get("branch_on"):
        return {
            "suggested": "router",
            "reason": "next path depends on an explicit observed condition",
        }
    if coordination.get("independent") and coordination.get("synthesize"):
        return {
            "suggested": "fanout_extract_then_single_synthesis",
            "reason": "independent work precedes one shared synthesis",
        }
    if coordination.get("independent"):
        return {
            "suggested": "parallel_independent_workers",
            "reason": "declared work items are independent",
        }
    return None


def _fallback_completion(conditions: list[str]) -> list[str]:
    result: list[str] = []
    if _STRUCTURE.intersection(conditions):
        result.append("scope_and_method_bounded")
    if _SOURCE.intersection(conditions):
        result.append("supporting_basis_qualified")
    if _CONTINUITY.intersection(conditions):
        result.append("current_state_qualified")
    if _RISK.intersection(conditions):
        result.append("consequence_boundary_reviewed")
    if _DELIVERY.intersection(conditions):
        result.append("delivery_boundary_qualified")
    return result


def _completion(request: dict[str, Any], conditions: list[str]) -> list[str]:
    explicit = _strings(request.get("completion_requirements"))
    return explicit or _fallback_completion(conditions)


def _metathoughts(completion: list[str]) -> list[dict[str, str]]:
    """Surface deterministic attention questions without selecting or running a Rite."""
    out: list[dict[str, str]] = []
    if "tests_pass" in completion:
        out.append(
            {
                "signal_id": "tests_pass_completion",
                **RITE_ATTENTION_SIGNALS["tests_pass_completion"],
            }
        )
    return out


def _effect_requested(request: dict[str, Any], conditions: list[str]) -> bool:
    observations = _observations(request)
    return bool(
        "external_effect" in conditions
        or "external_transmission" in conditions
        or "client_delivery" in conditions
        or "public_output" in conditions
        or "memory_promotion" in conditions
        or observations.get("external_effect", request.get("external_effect")) is True
        or request.get("writes_state") is True
        or observations.get("writes_state") is True
    )


def recommend_handling(request: dict[str, Any], classification: dict[str, Any]) -> dict[str, Any]:
    conditions = _conditions(request)
    viewpoints = _viewpoints(conditions)
    coordination = _coordination(request)
    topology = _topology(coordination)
    completion = _completion(request, conditions)
    metathoughts = _metathoughts(completion)
    effect_requested = _effect_requested(request, conditions)
    observations = _observations(request)
    conflict = bool(
        request.get("conflict_detected") is True
        or observations.get("conflict_detected") is True
        or observations.get("contradiction_detected") is True
    )

    needs_consult = bool(
        viewpoints
        or completion
        or coordination
        or conflict
        or classification.get("blocked_until_gate")
    )

    if classification.get("blocked_until_gate") and effect_requested:
        disposition = "GATE"
    elif needs_consult:
        disposition = "CONSULT"
    else:
        disposition = "PROCEED"

    constraints: list[str] = []
    if request.get("conditions") or request.get("observations") or coordination:
        constraints.append("declared_conditions_and_relations_are_candidates_not_truth")
    if _RISK.intersection(conditions):
        constraints.append("do_not_increase_claim_authority_without_support")
    if request.get("requested_transformation") in {"rewrite", "wording", "polish"}:
        constraints.append("preserve_claim_status_and_meaning")
    if classification.get("evidence_required"):
        constraints.append("retrieved_material_is_not_evidence_until_qualified")
    if metathoughts:
        constraints.append("metathought_question_does_not_activate_rite")

    handling: dict[str, Any] = {
        "disposition": disposition,
        "conditions": conditions,
        "role_viewpoints": viewpoints,
        "completion_requirements": completion,
        "constraints": constraints,
        "reconsult_if": [
            condition
            for condition in _MATERIAL_RECONSULT_CONDITIONS
            if condition not in conditions
        ],
        "authority_note": (
            "Handling is policy guidance only. Conditions and coordination relations "
            "are candidate inputs, a viewpoint is not an agent, topology is not "
            "dispatch, completion is not approval, a metathought is a question not "
            "a verdict or Rite activation, and Hermes remains the external executor."
        ),
    }

    if coordination:
        handling["coordination"] = coordination
    if topology:
        handling["topology"] = topology
    if metathoughts:
        handling["metathoughts"] = metathoughts
    if request.get("current_state") is not None:
        handling["current_state"] = request.get("current_state")
    if request.get("target_state") is not None:
        handling["target_state"] = request.get("target_state")
    if conflict:
        handling["rite_candidate"] = "concordance_des_sources"
    if classification.get("blocked_until_gate"):
        handling["effect_gate"] = {
            "required_approval_ceiling": classification.get("required_approval_ceiling"),
            "required_before_effect": True,
            "effect_requested_now": effect_requested,
        }
    return handling
