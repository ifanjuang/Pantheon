"""Policy decision as data.

Classifies a described request on the GLOSSARY axes: consequence (K0-K4),
required answer verification (V0-V4) and approval ceiling (C0-C5), and
states what the chokepoint requires before the effect may happen. The
server itself performs no effect: anything asking it to act is refused.

Memory first. Evidence when consequential. Status when deciding.
Approval when acting.
"""

from __future__ import annotations

import re

from . import request_handling

# Effects the policy server must refuse to perform itself (Phase 7 posture).
REFUSED_EFFECTS = {
    "send": "sending anything externally",
    "write": "writing files or external state",
    "delete": "deleting anything",
    "merge": "merging code or content",
    "approve": "approving an output",
    "promote_memory": "promoting memory / writing the Registre Probatoire",
    "install": "installing skills or modules",
    "schedule": "scheduling jobs",
    "route_provider": "routing model providers",
    "execute": "executing a capability or tool",
}

_REFUSAL_RE = {
    "send": r"send|envoyer|envoi|transmettre|transmission",
    "write": r"write|écrire|ecrire",
    "delete": r"delete|supprimer",
    "merge": r"merge|fusionner",
    "approve": r"approve|approuver",
    "promote_memory": r"promote|promouvoir|canonize|canoniser",
    "install": r"install|installer",
    "schedule": r"schedule|planifier",
    "route_provider": r"route|router",
    "execute": r"execute|exécuter|executer",
}
_REFUSAL_RE = {
    key: re.compile(r"(?:\b|_)(" + pattern + r")(?:\b|_)", re.IGNORECASE)
    for key, pattern in _REFUSAL_RE.items()
}

_K3_TRIGGERS = re.compile(
    r"\b(cost|budget|price|amount|contract|contractual|compliance|regulat|"
    r"deadline|liabilit|responsib|surface|permit|insurance|visa|client|"
    r"plus.?value|payment|invoice|devis|march[eé]|cctp|dpgf|"
    r"contradict|authorit|autorit|quantit|supersed)\b",
    re.IGNORECASE,
)

_K4_TRIGGERS = re.compile(
    r"\b(non[- ]?conform|claim|réclamation|reclamation|liability|responsibility|"
    r"responsabilité|validate|valider|price reduction|diminution du prix|"
    r"vefa|carrez|notarial|acqu[eé]reur|purchaser)\b",
    re.IGNORECASE,
)

# Canonical GLOSSARY K0 explicitly includes orientation, formatting and harmless
# drafts. These operation hints may therefore stay K0 when no stronger semantic
# or lexical trigger is present.
_K0_TRANSFORMATIONS = {
    "rewrite",
    "wording",
    "polish",
    "format",
    "formatting",
    "summarize",
    "summary",
}

# Conditions that may still describe harmless shaping work. Any other declared
# governed condition prevents the K0 fast exit and falls back to normal
# consequence classification.
_K0_SAFE_CONDITIONS = {
    "unclear_output",
    "narrative_or_editorial_work",
    "delivery_quality_required",
    "recipient_specific_format",
}

_K_TO_V = {"K0": "V0", "K1": "V1", "K2": "V2", "K3": "V3", "K4": "V4"}

_DOCTRINE_REFS = [
    "docs/governance/GLOSSARY.md",
    "docs/governance/ANSWER_VERIFICATION_GATE.md",
    "docs/governance/APPROVALS.md",
    "docs/governance/UNIFORM_CAPABILITY_GOVERNANCE.md",
    "docs/governance/USER_DECISION_GATE.md",
    "docs/governance/TASK_CONTRACTS.md",
    "docs/governance/REQUEST_LIFECYCLE.md",
    "docs/governance/ROLE_ACTIVATION.md",
]

_AUTHORITY_NOTE = (
    "Policy decision as data. Delegated runtime work executes outside Pantheon "
    "under a Task Contract; a direct human governed effect does not acquire a "
    "Task Contract merely because it writes state. The gate decides; the human "
    "decides."
)


def _refusals_in(request: dict) -> list[str]:
    asked = request.get("perform") or request.get("actions_requested") or []
    if isinstance(asked, str):
        asked = [asked]
    hits = []
    for action in asked:
        a = str(action).strip().lower().replace(" ", "_")
        for key, label in REFUSED_EFFECTS.items():
            if key in a or _REFUSAL_RE[key].search(str(action)):
                hits.append(label)
    return sorted(set(hits))


def _semantic_observations(request: dict) -> dict:
    observations = request.get("observations")
    return observations if isinstance(observations, dict) else {}


def _declared_conditions(request: dict, observations: dict) -> set[str]:
    """Collect declared condition names without treating them as truth."""
    conditions: set[str] = set()
    raw = request.get("conditions") or []
    if isinstance(raw, str):
        raw = [raw]
    if isinstance(raw, list):
        conditions.update(str(item) for item in raw if str(item))

    # Semantic intake may also provide condition booleans in observations.
    for key, value in observations.items():
        if value is True and key in request_handling.ROLE_TRIGGER_MAP:
            conditions.add(str(key))
    return conditions


def _semantic_bool(request: dict, observations: dict, name: str) -> bool:
    """Compose a caller observation with the legacy field.

    Intake vocabularies raise consequence; they never lower it. A caller that
    omits an observation says nothing about it, and a caller that sends ``False``
    is reporting its own reading, not overruling a signal the request already
    carries. Letting the observation win would allow a described request to talk
    its way under the gate -- which ``conditions`` already refuses to allow (see
    ``condition_external`` in ``classify_request``).
    """
    return observations.get(name) is True or bool(request.get(name, False))


def classify_request(request: dict) -> dict:
    """Classify a described request.

    ``conditions`` is the preferred generic semantic intake vocabulary. It uses
    existing governed Role Activation trigger names and remains candidate input,
    not truth or authorization. Legacy semantic fields remain supported during
    migration.

    ``requested_transformation`` may identify a harmless formatting/draft
    operation such as ``rewrite`` or ``formatting``. It stays K0 only while no
    stronger lexical, semantic or governed condition is present.

    ``delegated_execution`` defaults to True. Only an operational PEP that knows
    an effect is a direct human action should send False; the policy HTTP API is
    read-only, so the flag never authorizes an effect by itself.
    """
    refused = _refusals_in(request)
    if refused:
        return {
            "result": "refused",
            "refused_effects": refused,
            "reason": (
                "the MCP policy server may frame the work; it may not do the "
                "work. Requested effects must run in the execution runtime "
                "under the applicable governed boundary and pass the gate."
            ),
            "doctrine_refs": _DOCTRINE_REFS,
            "authority_note": _AUTHORITY_NOTE,
        }

    raw_delegated = request.get("delegated_execution", True)
    if not isinstance(raw_delegated, bool):
        return {
            "result": "refused",
            "refused_effects": [],
            "reason": "delegated_execution must be a boolean when provided",
            "doctrine_refs": _DOCTRINE_REFS,
            "authority_note": _AUTHORITY_NOTE,
        }
    delegated_execution = raw_delegated

    observations = _semantic_observations(request)
    conditions = _declared_conditions(request, observations)
    intent = str(request.get("intent", ""))
    requested_transformation = str(request.get("requested_transformation", "")).strip().lower()

    condition_external = "external_effect" in conditions
    condition_transmission = bool(
        {"external_transmission", "client_delivery", "public_output"}.intersection(conditions)
    )
    condition_memory = "memory_promotion" in conditions
    condition_professional = bool(
        {"legal_or_professional_risk", "liability_risk"}.intersection(conditions)
    )

    # ``external_effect`` is tri-state: False, True, or "unknown" -- and
    # "unknown" is itself an escalation to K4. Like every other intake signal it
    # composes upward only.
    external = request.get("external_effect", False)
    observed_external = observations.get("external_effect")
    if observed_external is True or observed_external == "unknown":
        external = observed_external
    if condition_external:
        external = True

    transmission = (
        _semantic_bool(request, observations, "transmission_requested")
        or _semantic_bool(request, observations, "external_transmission")
        or condition_transmission
    )
    memory = _semantic_bool(request, observations, "memory_promotion_requested") or condition_memory
    writes = _semantic_bool(request, observations, "writes_state")
    professional_position = (
        _semantic_bool(request, observations, "professional_position")
        or condition_professional
    )
    financial_or_contractual = _semantic_bool(
        request, observations, "financial_or_contractual_effect"
    )

    register_material = bool(request.get("register_candidates"))
    scope = request.get("scope") or {}
    k4_intent_trigger = bool(_K4_TRIGGERS.search(intent))
    k3_intent_trigger = bool(_K3_TRIGGERS.search(intent))
    k0_conditions_safe = not conditions.difference(_K0_SAFE_CONDITIONS)

    if external is True or transmission or memory or professional_position or financial_or_contractual:
        consequence = "K4"
    elif external == "unknown":
        consequence = "K4"
    elif k4_intent_trigger:
        consequence = "K4"
    elif writes or register_material or k3_intent_trigger:
        consequence = "K3"
    elif requested_transformation in _K0_TRANSFORMATIONS and k0_conditions_safe:
        consequence = "K0"
    elif intent.strip():
        consequence = "K2"
    else:
        consequence = "K1"

    verification = _K_TO_V[consequence]
    approval = {
        "K4": "C3",
        "K3": "C2",
        "K2": "C1",
        "K1": "C0",
        "K0": "C0",
    }[consequence]
    if transmission or memory or professional_position or financial_or_contractual:
        approval = "C4"
    elif consequence == "K4" and k4_intent_trigger:
        approval = "C4"

    task_contract_required = consequence in ("K2", "K3", "K4") and delegated_execution

    evidence_required = consequence in ("K3", "K4") and bool(
        delegated_execution
        or external is True
        or external == "unknown"
        or transmission
        or memory
        or professional_position
        or financial_or_contractual
        or register_material
        or k3_intent_trigger
        or k4_intent_trigger
    )

    blocked_until_gate = consequence == "K4" or (not delegated_execution and writes)

    gates: list[str] = []
    if evidence_required:
        gates.append("evidence required (Registre Probatoire citation for assertions)")
    if blocked_until_gate:
        if consequence == "K4":
            gates.append("User Decision Gate before any external effect or Registre write")
        else:
            gates.append("User Decision Gate before direct human governed-state effect")
    if not scope and task_contract_required:
        gates.append("scope missing: declare scope_type/scope_id before work starts")

    report = {
        "result": "classified",
        "consequence_level": consequence,
        "required_verification": verification,
        "required_approval_ceiling": approval,
        "delegated_execution": delegated_execution,
        "task_contract_required": task_contract_required,
        "evidence_required": evidence_required,
        "blocked_until_gate": blocked_until_gate,
        "required_gates": gates,
        "allowed_output": "candidate only (Result Candidate + Evidence Pack Candidate)",
        "scope_seen": scope or None,
        "conditions_seen": sorted(conditions),
        "doctrine_refs": _DOCTRINE_REFS,
        "authority_note": _AUTHORITY_NOTE,
    }
    report["handling"] = request_handling.recommend_handling(request, report)
    return report


def check_external_action(description: str) -> dict:
    """An external action is blocked by default; the report states what
    legitimizing it would require. The server never performs it."""
    return {
        "action": description,
        "status": "blocked_by_default",
        "requires": [
            "Task Contract naming the action and its scope",
            "approval at C3 or above (C4 for transmission or Registre writes)",
            "Evidence Pack Candidate prepared for review",
            "User Decision Gate: the human decides",
        ],
        "doctrine_refs": _DOCTRINE_REFS,
        "authority_note": _AUTHORITY_NOTE,
    }
