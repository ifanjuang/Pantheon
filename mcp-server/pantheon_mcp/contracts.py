"""Candidate skeleton builders for Hermes integration.

The helpers return reviewable candidates only. They do not create an executable
Task Contract, do not approve an Evidence Pack, do not call tools and do not
perform any external effect.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from . import policy

_ALLOWED_STATUS_TERMS = [
    "candidate",
    "requires approval",
    "scope unclear",
    "blocked pending evidence",
    "human decision required",
]

_AUTHORITY_NOTE = (
    "Candidate skeleton only. The execution runtime may perform work outside "
    "Pantheon only under a reviewed Task Contract. The gate decides; the human decides."
)

_FORBIDDEN_BEHAVIORS = [
    "no external transmission from the policy server",
    "no file or state write from the policy server",
    "no approval or professional conclusion from the policy server",
    "no Registre Probatoire write or memory promotion",
    "no provider routing, scheduling, queueing or tool execution",
]

_DEFAULT_EXPECTED_OUTPUTS = [
    "RESULT_CANDIDATE",
    "EVIDENCE_PACK_CANDIDATE",
    "STATUS",
    "SCOPE_USED",
    "APPROVAL_NEEDED",
    "REGISTER_CANDIDATE_PROPOSAL",
    "LIMITS_AND_UNCERTAINTIES",
]


def _coerce_request(request: dict[str, Any] | None) -> dict[str, Any]:
    if request is None:
        return {}
    if not isinstance(request, dict):
        return {"intent": str(request)}
    return deepcopy(request)


def _scope_status(scope: dict[str, Any] | None) -> str:
    if not scope or not scope.get("scope_type") or not scope.get("scope_id"):
        return "scope unclear"
    return "candidate"


def _capabilities(request: dict[str, Any], classification: dict[str, Any]) -> list[str]:
    explicit = request.get("capabilities") or request.get("requested_capabilities")
    if isinstance(explicit, str):
        return [explicit]
    if isinstance(explicit, list) and explicit:
        return [str(item) for item in explicit]
    if classification.get("evidence_required"):
        return ["document_intelligence_candidate", "evidence_pack_candidate_preparation"]
    return ["request_classification", "candidate_preparation"]


def _evidence_requirements(classification: dict[str, Any]) -> list[str]:
    if classification.get("evidence_required"):
        return [
            "dated source references",
            "scope-specific source authority notes",
            "contradictions to resolve before position",
            "Registre Probatoire citations where assertions are consequential",
        ]
    return ["state evidence requirement explicitly, even when minimal"]


def _recommended_rites(classification: dict[str, Any]) -> list[str]:
    rites: list[str] = []
    if classification.get("blocked_until_gate"):
        rites.append("User Decision Gate")
    if classification.get("evidence_required"):
        rites.append("Evidence review before answer")
    if any("scope missing" in gate for gate in classification.get("required_gates", [])):
        rites.append("Scope clarification")
    return rites or ["Light review"]


def _candidate_status(classification: dict[str, Any]) -> str:
    if classification.get("result") == "refused":
        return "human decision required"
    if classification.get("blocked_until_gate"):
        return "blocked pending evidence"
    if any("scope missing" in gate for gate in classification.get("required_gates", [])):
        return "scope unclear"
    if classification.get("evidence_required"):
        return "requires approval"
    return "candidate"


def prepare_task_contract_skeleton(request: dict[str, Any] | None) -> dict[str, Any]:
    """Return a Task Contract candidate skeleton for human review."""
    req = _coerce_request(request)
    classification = policy.classify_request(req)
    scope = req.get("scope") if isinstance(req.get("scope"), dict) else {}

    return {
        "object": "TASK_CONTRACT_CANDIDATE_SKELETON",
        "status": _candidate_status(classification),
        "allowed_status_terms": _ALLOWED_STATUS_TERMS,
        "request_summary": req.get("intent") or req.get("summary") or "",
        "scope": scope or {"status": "scope unclear", "required": ["scope_type", "scope_id"]},
        "scope_status": _scope_status(scope),
        "classification": {
            "consequence_level": classification.get("consequence_level"),
            "required_verification": classification.get("required_verification"),
            "approval_ceiling": classification.get("required_approval_ceiling"),
            "blocked_until_gate": classification.get("blocked_until_gate", False),
            "required_gates": classification.get("required_gates", []),
        },
        "capabilities_solicited": _capabilities(req, classification),
        "recommended_rites": _recommended_rites(classification),
        "evidence_requirements": _evidence_requirements(classification),
        "expected_outputs": _DEFAULT_EXPECTED_OUTPUTS,
        "forbidden_behaviors": _FORBIDDEN_BEHAVIORS,
        "review_required": True,
        "authority_note": _AUTHORITY_NOTE,
        "doctrine_refs": [
            "docs/governance/TASK_CONTRACTS.md",
            "schemas/task_contract.schema.yaml",
            "docs/governance/HERMES_INTEGRATION.md",
            "docs/governance/USER_DECISION_GATE.md",
        ],
    }


def prepare_evidence_pack_skeleton(request: dict[str, Any] | None) -> dict[str, Any]:
    """Return an Evidence Pack candidate skeleton for human review."""
    req = _coerce_request(request)
    classification = policy.classify_request(req)
    sources = req.get("sources_expected") or req.get("sources") or []
    if isinstance(sources, str):
        sources = [sources]

    return {
        "object": "EVIDENCE_PACK_CANDIDATE_SKELETON",
        "status": "blocked pending evidence" if classification.get("evidence_required") else "candidate",
        "allowed_status_terms": _ALLOWED_STATUS_TERMS,
        "request_summary": req.get("intent") or req.get("summary") or "",
        "classification": {
            "consequence_level": classification.get("consequence_level"),
            "required_verification": classification.get("required_verification"),
            "approval_ceiling": classification.get("required_approval_ceiling"),
        },
        "sources_expected": sources,
        "assumptions_to_state": req.get("assumptions_to_state") or [
            "source authority must be checked before relying on a document",
            "latest file is not automatically contractual authority",
        ],
        "contradictions_to_resolve": req.get("contradictions_to_resolve") or [],
        "claims_to_support": req.get("claims_to_support") or [
            "all consequential assertions require dated source support",
        ],
        "register_candidates": req.get("register_candidates") or [
            {
                "status": "candidate",
                "claim": "to be proposed only after evidence review",
                "promotion": "never automatic",
            }
        ],
        "limits_and_uncertainties": req.get("limits_and_uncertainties") or [
            "candidate skeleton, not validated truth",
            "human decision required for external or consequential use",
        ],
        "forbidden_behaviors": _FORBIDDEN_BEHAVIORS,
        "review_required": True,
        "authority_note": _AUTHORITY_NOTE,
        "doctrine_refs": [
            "docs/governance/EVIDENCE_PACK.md",
            "schemas/evidence_pack.schema.yaml",
            "docs/governance/EVIDENCE_MEMORY_CANONICALIZATION.md",
            "docs/governance/USER_DECISION_GATE.md",
        ],
    }
