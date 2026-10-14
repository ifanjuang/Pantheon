"""Build bounded Pantheon policy/decision payloads for the runtime PEP.

Runtime adapters know the concrete effect being attempted (Paperless metadata
update, project-document intake, capability action). The Pantheon HTTP API is
intentionally generic. This module translates runtime facts into that generic
contract without letting a caller redefine the object, digest, scope or known
external-effect status that the human Decision must cover.
"""

from __future__ import annotations

from typing import Any


class PolicyRequestError(ValueError):
    """A policy request cannot preserve the required governance boundary."""


_REQUEST_FIELDS = frozenset(
    {
        "intent",
        "external_effect",
        "writes_state",
        "delegated_execution",
        "transmission_requested",
        "memory_promotion_requested",
        "professional_position",
        "financial_or_contractual_effect",
        "scope",
    }
)

_GATE_FIELDS = frozenset(
    {
        "task_contract_ref",
        "evidence_pack_candidate_ref",
        "human_decision_ref",
        "human_decision_level",
    }
)

_EXPECTATION_FIELDS = frozenset(
    {
        "required_ceiling",
        "required_scope",
        "object_identity",
        "expected_digest",
    }
)

_PAPERLESS_EXTERNAL_EFFECT_KINDS = frozenset(
    {
        "external_document_upload",
        "external_document_metadata_update",
    }
)

# Closed class of already-wired human-originated Cockpit/CLI writes. They are
# not delegated Hermes tasks, so manufacturing a Task Contract for them would
# violate TASK_CONTRACTS. Unknown/new effects remain delegated/fail-conservative.
_DIRECT_HUMAN_EFFECT_INTENTS = frozenset(
    {
        "bind_oidc_identity",
        "store_reviewed_dossier",
        "publish_knowledge_reviewed",
        "apply_edit_request",
        "act_working_information",
    }
)

# For a direct-human consequential effect the PEP accepts only the complete
# credential projected from a persisted canonical DecisionRecord. Effect owners
# may derive EffectExpectation; they may not fill any Decision field.
_DIRECT_HUMAN_DECISION_FIELDS = frozenset(
    {
        "decision_id",
        "decided_by",
        "approval_level",
        "scope",
        "object_identity",
        "content_digest",
        "expires_at",
        "signature",
    }
)

# Issue Pantheon-Next#664 qualification fixture. Only this synthetic intent carries the
# already-bound human decision into preflight so Pantheon can compose signed
# gate validation before emitting the one bounded external-effect permission.
_QUALIFICATION_EXTERNAL_EFFECT_INTENT = "qualification_external_effect"


def _candidate_intent(candidate: dict[str, Any]) -> str:
    request = candidate.get("request")
    if isinstance(request, dict) and request.get("intent") not in (None, ""):
        return str(request["intent"]).strip()
    return str(
        candidate.get("intent")
        or candidate.get("effect_kind")
        or candidate.get("action")
        or ""
    ).strip()


def requires_authenticated_human_decision(candidate: dict[str, Any]) -> bool:
    """Whether this closed direct-human effect class requires issuer proof."""
    return _candidate_intent(candidate) in _DIRECT_HUMAN_EFFECT_INTENTS


def _require_complete_direct_human_decision(
    candidate: dict[str, Any],
    decision: dict[str, Any],
) -> None:
    if not requires_authenticated_human_decision(candidate):
        return
    missing = sorted(
        field
        for field in _DIRECT_HUMAN_DECISION_FIELDS
        if decision.get(field) in (None, "")
    )
    if missing:
        raise PolicyRequestError(
            "direct human consequential effect requires a complete canonical "
            "signed Decision credential; missing: " + ", ".join(missing)
        )


def _scope_from_decision(decision_payload: dict[str, Any]) -> dict[str, Any] | None:
    expectation = decision_payload.get("expectation") or {}
    decision = decision_payload.get("decision") or {}
    scope = expectation.get("required_scope") or decision.get("scope")
    return dict(scope) if isinstance(scope, dict) else None


def _pep_owned_request_overrides(candidate: dict[str, Any]) -> dict[str, bool]:
    """Return effect facts that a runtime caller is not allowed to downgrade."""
    kind = str(candidate.get("effect_kind") or "").strip()
    paperless_upload_shape = "filename" in candidate and "content_hash" in candidate
    paperless_metadata_shape = "document_id" in candidate and "changed_fields" in candidate
    if (
        kind in _PAPERLESS_EXTERNAL_EFFECT_KINDS
        or paperless_upload_shape
        or paperless_metadata_shape
    ):
        return {"external_effect": True, "writes_state": True}
    return {}


def bind_decision_payload(
    candidate: dict[str, Any],
    decision_payload: dict[str, Any],
) -> dict[str, Any]:
    """Bind a canonical Decision credential to PEP-owned effect facts.

    ``decision`` is caller-provided transport material only because the domain
    owner has already loaded it from the canonical Decision store. For the closed
    direct-human consequential class it must be complete before the effect owner
    reaches this seam. ``expectation`` is different: it states what the effect
    actually requires and is therefore owned by the effect adapter.
    """
    if not isinstance(decision_payload, dict):
        raise PolicyRequestError("decision_payload must be a mapping")
    decision = decision_payload.get("decision")
    if not isinstance(decision, dict):
        raise PolicyRequestError("decision_payload.decision must be a mapping")

    _require_complete_direct_human_decision(candidate, decision)

    explicit = candidate.get("decision_expectation")
    if explicit is not None:
        if not isinstance(explicit, dict):
            raise PolicyRequestError("candidate.decision_expectation must be a mapping")
        expectation = {
            key: explicit[key]
            for key in _EXPECTATION_FIELDS
            if explicit.get(key) not in (None, "")
        }
        missing = sorted(_EXPECTATION_FIELDS - set(expectation))
        if missing:
            raise PolicyRequestError(
                "candidate.decision_expectation is incomplete: " + ", ".join(missing)
            )
    else:
        caller_expectation = decision_payload.get("expectation")
        if not isinstance(caller_expectation, dict):
            raise PolicyRequestError("decision_payload.expectation must be a mapping")
        expectation = dict(caller_expectation)

    return {
        "decision": dict(decision),
        "expectation": expectation,
    }


def build_preflight_payload(
    candidate: dict[str, Any],
    decision_payload: dict[str, Any],
) -> dict[str, Any]:
    """Translate one runtime candidate to ``pantheon.policy.v1`` preflight input."""
    explicit_request = candidate.get("request")
    if explicit_request is not None and not isinstance(explicit_request, dict):
        raise PolicyRequestError("candidate.request must be a mapping")

    source_request = explicit_request or {}
    request: dict[str, Any] = {
        key: source_request[key]
        for key in _REQUEST_FIELDS
        if key in source_request
    }

    request.setdefault(
        "intent",
        str(
            candidate.get("intent")
            or candidate.get("effect_kind")
            or candidate.get("action")
            or "consequential_effect"
        ),
    )
    request.setdefault("external_effect", bool(candidate.get("external_effect", True)))
    request.setdefault("writes_state", bool(candidate.get("writes_state", True)))

    intent = str(request.get("intent") or "").strip()
    if intent in _DIRECT_HUMAN_EFFECT_INTENTS:
        request["delegated_execution"] = False
    else:
        request["delegated_execution"] = True

    request.setdefault(
        "transmission_requested", bool(candidate.get("transmission_requested", False))
    )
    request.setdefault(
        "memory_promotion_requested", bool(candidate.get("memory_promotion_requested", False))
    )
    request.setdefault(
        "professional_position", bool(candidate.get("professional_position", False))
    )
    request.setdefault(
        "financial_or_contractual_effect",
        bool(candidate.get("financial_or_contractual_effect", False)),
    )

    if "scope" not in request:
        scope = candidate.get("scope")
        if isinstance(scope, dict):
            request["scope"] = dict(scope)
        else:
            inferred_scope = _scope_from_decision(decision_payload)
            if inferred_scope is not None:
                request["scope"] = inferred_scope

    request.update(_pep_owned_request_overrides(candidate))

    explicit_signals = candidate.get("gate_signals")
    if explicit_signals is not None and not isinstance(explicit_signals, dict):
        raise PolicyRequestError("candidate.gate_signals must be a mapping")

    source_signals = explicit_signals or {}
    gate_signals: dict[str, Any] = {
        key: source_signals[key]
        for key in _GATE_FIELDS
        if source_signals.get(key) not in (None, "")
    }

    for key in ("task_contract_ref", "evidence_pack_candidate_ref"):
        if key not in gate_signals and candidate.get(key) not in (None, ""):
            gate_signals[key] = candidate[key]

    decision = decision_payload.get("decision") or {}
    if gate_signals.get("human_decision_ref") in (None, "") and decision.get("decision_id"):
        gate_signals["human_decision_ref"] = decision["decision_id"]
    if gate_signals.get("human_decision_level") in (None, "") and decision.get("approval_level"):
        gate_signals["human_decision_level"] = decision["approval_level"]

    payload: dict[str, Any] = {
        "request": request,
        "gate_signals": gate_signals,
    }
    if request.get("intent") == _QUALIFICATION_EXTERNAL_EFFECT_INTENT:
        decision = decision_payload.get("decision")
        expectation = decision_payload.get("expectation")
        if not isinstance(decision, dict) or not isinstance(expectation, dict):
            raise PolicyRequestError(
                "qualification_external_effect requires a bound decision validation payload"
            )
        payload["decision_validation"] = {
            "decision": dict(decision),
            "expectation": dict(expectation),
        }
    return payload
