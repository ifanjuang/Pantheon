"""Transport-neutral, read-only consultation projections.

The functions in this module are shared policy projections that an MCP tool
can expose today and a bounded HTTP adapter may expose later.  They read
governed repository sources or qualify caller-provided status candidates.
They never probe a runtime, retrieve private knowledge, authorize a task or
write state.
"""

from __future__ import annotations

import re
from typing import Any

from . import source_map

CONTRACT_VERSION = "pantheon.consultation.v1"

NON_EQUIVALENCES = [
    "listed != installed",
    "detected != configured",
    "configured != enabled",
    "enabled != reachable",
    "reachable != healthy",
    "installed != approved",
    "hermes_enabled != pantheon_governance_activation",
    "healthy != safe",
    "governance_eligible != task_authorized",
    "update_available != update_authorized",
    "runtime_success != evidence",
    "binding_selected != dependency_adopted",
    "retrieved != evidence",
]

STATUS_VOCABULARIES: dict[str, set[str]] = {
    "health": {
        "unknown",
        "healthy",
        "unhealthy",
        "degraded",
        "stale",
    },
    "update_status": {
        "unknown",
        "up_to_date",
        "update_available",
        "security_update_available",
        "breaking_update_available",
        "deprecated",
        "abandoned",
    },
    "rollback_status": {
        "unknown",
        "not_required",
        "available",
        "not_available",
        "tested",
        "failed",
        "required_before_activation",
    },
    "governance_status": {
        "external_reference",
        "candidate",
        "to_verify",
        "approved_for_sandbox",
        "approved_for_project",
        "approved_for_production",
        "blocked",
        "refused",
        "superseded",
    },
    "task_use_status": {
        "not_established",
        "requires_task_contract",
        "requires_approval",
        "eligible_under_reviewed_contract",
        "blocked",
    },
}

RUNTIME_BOOLEAN_AXES = (
    "listed",
    "detected",
    "installed",
    "configured",
    "enabled",
    "reachable",
)

_TOPICS: dict[str, dict[str, Any]] = {
    "pantheon": {
        "aliases": {"kernel", "governance", "pantheon-next"},
        "placement": "tool-agnostic governance and policy layer",
        "purpose": "define authority, scope, evidence, approval and status rules",
        "why": [
            "keep governance independent from any model or execution runtime",
            "preserve one vocabulary and one decision boundary across clients",
        ],
        "must_not": [
            "execute tasks",
            "route providers",
            "auto-approve",
            "auto-promote memory",
        ],
        "sources": ["architecture", "status", "capability-placement"],
    },
    "hermes": {
        "aliases": {"execution", "execution-runtime", "runtime"},
        "placement": "external execution runtime governed through contracts and gates",
        "purpose": "perform authorized work and return candidates, traces and evidence material",
        "why": [
            "execution capabilities belong where tools and runtime state already live",
            "runtime success must stay separate from governance approval and proof",
        ],
        "must_not": [
            "redefine Pantheon doctrine",
            "approve itself",
            "promote Registre Probatoire entries",
        ],
        "sources": ["hermes-runtime-governance", "target-architecture", "task-contracts"],
    },
    "hermes-client": {
        "aliases": {"hermes-web", "runtime-client", "runtime-ui", "chat-client", "sessions"},
        "placement": "replaceable Hermes-compatible runtime interaction client",
        "purpose": "provide chat, sessions, attachments and runtime controls without becoming a Pantheon authority",
        "why": [
            "runtime interaction belongs with the execution ecosystem rather than a second Pantheon WebUI",
            "compatible Web, PWA or mobile clients can remain replaceable without changing governance",
        ],
        "must_not": [
            "become governance authority",
            "turn runtime success into approval",
            "make client persistence a Pantheon governed record",
        ],
        "sources": ["architecture", "status", "what-runs"],
    },
    "pantheon-cockpit": {
        "aliases": {"cockpit", "pantheon-cockpit", "cards", "governed-projection"},
        "placement": "Pantheon governed projection surface for Cards, navigation, status, review and decisions",
        "purpose": "project governed state and human decision surfaces without becoming a generic chat/session runtime",
        "why": [
            "governed projections need product-specific composition distinct from generic runtime interaction",
            "projection must stay separate from persistence, execution and approval authority",
        ],
        "must_not": [
            "become a second general-purpose chat frontend",
            "execute external work",
            "treat displayed state as persisted or approved state",
        ],
        "sources": ["architecture", "modules", "what-runs"],
    },
    "pantheon-control": {
        "aliases": {"control", "dashboard", "control-plane"},
        "placement": (
            "thin governed control surface: a static public preview plus an "
            "installable external Hermes dashboard-plugin candidate"
        ),
        "purpose": "display and qualify operational-state candidates and human decision surfaces",
        "why": [
            "operational visibility is necessary without moving execution into Pantheon",
            "install, health, activation and approval must remain separate statuses",
        ],
        "must_not": [
            "become a Pantheon backend",
            "hold secrets",
            "auto-install",
            "auto-approve",
        ],
        "sources": ["control-boundary", "control-plane-boundary", "what-runs"],
    },
    "mcp": {
        "aliases": {"mcp-server", "policy-server"},
        "placement": "read-only policy and validation adapter for AI clients",
        "purpose": "serve governed sources and return policy or status qualification as data",
        "why": [
            "Hermes, Claude, ChatGPT and future MCP clients can consult one governed surface",
            "the same importable logic can remain independent from transport",
        ],
        "must_not": ["execute", "send", "write state", "install", "promote memory"],
        "sources": ["mcp-boundary", "mcp-development", "what-runs"],
    },
    "api": {
        "aliases": {"http-api", "consultation-api", "rest"},
        "placement": "future bounded transport adapter outside the governance kernel",
        "purpose": "project the same consultation contract to a dashboard or non-MCP client",
        "why": [
            "avoid duplicating policy logic between the dashboard and MCP",
            "support authentication and scoped projections at the transport edge",
        ],
        "must_not": [
            "be claimed as implemented today",
            "become a runtime or unrestricted data gateway",
        ],
        "sources": ["mcp-boundary", "control-plane-boundary", "what-runs"],
    },
    "capabilities": {
        "aliases": {"capability", "modules", "skills"},
        "placement": "governed declarations in Pantheon; implementations in external runtimes",
        "purpose": "describe purpose, scope, risk, dependencies, evidence and admission status",
        "why": [
            "composition needs a reviewable declaration before implementation is invoked",
            "availability, installation, activation and authorization are different facts",
        ],
        "must_not": ["install skills", "dispatch tools", "treat catalog popularity as safety"],
        "sources": [
            "capability-registry",
            "uniform-capability-governance",
            "control-plane-boundary",
        ],
    },
    "knowledge": {
        "aliases": {"rag", "documents", "retrieval", "memvid"},
        "placement": "external scoped source and retrieval layers governed by Pantheon",
        "purpose": "retrieve attributable project or general knowledge for a bounded task",
        "why": [
            "large corpora should be retrieved progressively instead of copied into every prompt",
            "source provenance and project isolation must survive retrieval",
        ],
        "must_not": ["collapse all projects into one index", "treat retrieval as proof"],
        "sources": ["source-ingestion-retrieval", "knowledge-ingestion-memory", "memory"],
    },
    "memory": {
        "aliases": {"mem0", "recall"},
        "placement": "Hermes-side operational recall, separate from the Registre Probatoire",
        "purpose": "reuse contextual preferences and prior operational material within scope",
        "why": [
            "free runtime recall is useful but cannot carry probative authority",
            "validated, citeable material needs a separate governed admission path",
        ],
        "must_not": ["be cited as proof by default", "auto-promote into the register"],
        "sources": ["memory", "registre-probatoire", "knowledge-ingestion-memory"],
    },
    "evidence": {
        "aliases": {"evidence-pack", "proof", "registre", "registre-probatoire"},
        "placement": "task-scoped evidence candidates and a separately governed probative register",
        "purpose": "link consequential claims to attributable, reviewable support",
        "why": [
            "a model statement, runtime trace or retrieved chunk is not proof by itself",
            "certainty and human validation must remain visible",
        ],
        "must_not": ["auto-validate truth", "silently canonize", "hide weak or missing support"],
        "sources": ["evidence-pack", "registre-probatoire", "answer-verification-gate"],
    },
}


def _base(object_name: str, source_mode: str) -> dict[str, Any]:
    return {
        "contract": CONTRACT_VERSION,
        "repository_version": source_map.repository_version(),
        "object": object_name,
        "source_mode": source_mode,
        "authority_effect": "none",
        "write_effect": False,
    }


def _source_ref(key: str) -> dict[str, Any]:
    info = source_map.describe_source(key)
    return {
        field: info.get(field)
        for field in (
            "uri",
            "title",
            "source_file",
            "exists",
            "authority",
            "status",
            "declared_status",
            "content_sha256",
        )
    }


def _normalise_topic(topic: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(topic or "").strip().lower()).strip("-")


def _resolve_topic(topic: str) -> str | None:
    wanted = _normalise_topic(topic)
    if wanted in _TOPICS:
        return wanted
    for key, definition in _TOPICS.items():
        if wanted in definition["aliases"]:
            return key
    return None


def consultation_catalog() -> dict[str, Any]:
    """Return the honest availability map for consultation surfaces."""
    out = _base("CONSULTATION_CATALOG", "repository_and_implementation_status")
    out.update(
        {
            "result": "listed",
            "surfaces": [
                {
                    "id": "governance_sources",
                    "status": "implemented_read_only",
                    "interface": [
                        "MCP resources",
                        "find_relevant_sources",
                        "list_sources",
                        "read_doctrine",
                    ],
                },
                {
                    "id": "architecture_explanations",
                    "status": "implemented_read_only",
                    "interface": ["explain_architecture"],
                },
                {
                    "id": "capability_status_qualification",
                    "status": "implemented_read_only_partial",
                    "interface": ["get_capability_status"],
                    "limitation": (
                        "qualifies caller-provided status only; "
                        "performs no runtime probe"
                    ),
                },
                {
                    "id": "runtime_inventory",
                    "status": "implemented_external_read_only_partial",
                    "interface": ["external Hermes dashboard plugin"],
                    "limitation": (
                        "the Hermes plugin produces live observations; the MCP "
                        "does not inventory or probe a runtime"
                    ),
                },
                {
                    "id": "evidence_instance_query",
                    "status": "documented_non_implemented",
                },
                {
                    "id": "knowledge_and_document_retrieval",
                    "status": "documented_non_implemented",
                },
                {
                    "id": "mem0_or_memvid_retrieval",
                    "status": "documented_non_implemented",
                },
                {
                    "id": "scoped_user_project_permissions",
                    "status": "documented_non_implemented",
                },
                {
                    "id": "http_consultation_api",
                    "status": "documented_non_implemented",
                },
                {
                    "id": "remote_mcp_transport",
                    "status": "documented_non_implemented",
                },
            ],
            "known_architecture_topics": sorted(_TOPICS),
            "non_equivalences": NON_EQUIVALENCES,
            "sources": [
                _source_ref("what-runs"),
                _source_ref("mcp-boundary"),
                _source_ref("control-plane-boundary"),
            ],
        }
    )
    return out


def explain_architecture(topic: str) -> dict[str, Any]:
    """Explain placement and rationale for one allowlisted architecture topic."""
    key = _resolve_topic(topic)
    out = _base("ARCHITECTURE_EXPLANATION", "governed_sources_and_bounded_projection")
    if key is None:
        out.update(
            {
                "result": "unknown_topic",
                "requested_topic": str(topic or ""),
                "known_topics": sorted(_TOPICS),
                "limits": ["No free-path repository read or invented architecture explanation."],
            }
        )
        return out

    definition = _TOPICS[key]
    out.update(
        {
            "result": "explained",
            "topic": key,
            "placement": definition["placement"],
            "purpose": definition["purpose"],
            "why": definition["why"],
            "must_not": definition["must_not"],
            "sources": [_source_ref(source) for source in definition["sources"]],
            "authority_note": (
                "This explanation is a bounded implementation projection. "
                "The cited repository sources retain their declared authority and status."
            ),
        }
    )
    return out


def qualify_capability_status(candidate: dict[str, Any] | None) -> dict[str, Any]:
    """Qualify a caller-provided operational-status candidate.

    This is deliberately not a probe and not an authorization check.  It keeps
    each status axis separate and reports missing provenance or evidence.
    """
    candidate = candidate if isinstance(candidate, dict) else {}
    out = _base("CAPABILITY_STATUS_QUALIFICATION", "provided_status_candidate")
    problems: list[str] = []
    gaps: list[str] = []
    warnings: list[str] = []

    capability_id = candidate.get("capability_id")
    if not isinstance(capability_id, str) or not capability_id.strip():
        problems.append("capability_id must be a non-empty string")

    observed: dict[str, Any] = {}
    for field in RUNTIME_BOOLEAN_AXES:
        if field not in candidate:
            gaps.append(f"{field} not reported")
            continue
        value = candidate[field]
        if value is not None and not isinstance(value, bool):
            problems.append(f"{field} must be boolean or null")
            continue
        observed[field] = value

    for field, allowed in STATUS_VOCABULARIES.items():
        if field not in candidate:
            gaps.append(f"{field} not reported")
            continue
        value = candidate[field]
        if not isinstance(value, str) or value not in allowed:
            problems.append(
                f"{field} must be one of: {', '.join(sorted(allowed))}"
            )
            continue
        observed[field] = value

    producer = candidate.get("producer")
    if producer is None:
        gaps.append("producer not reported; observation origin is not established")
    elif not isinstance(producer, str) or not producer.strip():
        problems.append("producer must be a non-empty string when supplied")

    evidence_refs = candidate.get("evidence_refs")
    if evidence_refs is None:
        evidence_refs = []
    elif not (
        isinstance(evidence_refs, list)
        and all(isinstance(item, str) and item.strip() for item in evidence_refs)
    ):
        problems.append("evidence_refs must be a list of non-empty strings")
        evidence_refs = []
    if not evidence_refs:
        gaps.append("no evidence_refs supplied; reported statuses remain unsupported candidates")

    observed_at = candidate.get("observed_at")
    if not observed_at:
        gaps.append("observed_at not reported; freshness cannot be assessed")
    elif not isinstance(observed_at, str):
        problems.append("observed_at must be a non-empty string when supplied")

    scope = candidate.get("scope")
    if not scope:
        gaps.append("scope not reported; project or user eligibility cannot be assessed")
    elif not isinstance(scope, (dict, str)):
        problems.append("scope must be a mapping or non-empty string when supplied")

    governance = observed.get("governance_status")
    installed = observed.get("installed")
    detected = observed.get("detected")
    configured = observed.get("configured")
    enabled = observed.get("enabled")
    reachable = observed.get("reachable")
    health = observed.get("health")
    update = observed.get("update_status")
    task_use = observed.get("task_use_status")

    approved = {
        "approved_for_sandbox",
        "approved_for_project",
        "approved_for_production",
    }
    if installed is True and governance not in approved:
        warnings.append("installed != approved")
    if health == "healthy":
        warnings.append("healthy != safe")
    if update in {
        "update_available",
        "security_update_available",
        "breaking_update_available",
    }:
        warnings.append("update_available != update_authorized")
    if governance in approved and task_use != "eligible_under_reviewed_contract":
        warnings.append("governance_eligible != task_authorized")
    if enabled is True and governance not in approved:
        warnings.append("hermes_enabled != pantheon_governance_activation")

    if detected is False and installed is True:
        problems.append("installed cannot be true when detected is false")
    if installed is not True and enabled is True:
        problems.append("enabled cannot be true unless installed is true")
    if configured is False and enabled is True:
        problems.append("enabled cannot be true when configured is false")
    if detected is False and reachable is True:
        problems.append("reachable cannot be true when detected is false")

    if (
        governance in {"blocked", "refused", "superseded"}
        or task_use == "blocked"
        or health == "unhealthy"
    ):
        use_posture = "blocked_by_reported_status"
    else:
        use_posture = "requires_task_preflight_and_any_applicable_human_decision"
    if problems:
        use_posture = "blocked_invalid_candidate"

    out.update(
        {
            "result": "invalid" if problems else "qualified_candidate",
            "capability_id": capability_id.strip() if isinstance(capability_id, str) else None,
            "producer": producer.strip() if isinstance(producer, str) else None,
            "observed": observed,
            "observed_at": observed_at,
            "scope": scope,
            "evidence_refs": evidence_refs,
            "problems": problems,
            "capability_gaps": gaps,
            "warnings": list(dict.fromkeys(warnings)),
            "use_posture": use_posture,
            "authorization_effect": "none",
            "runtime_probe_performed": False,
            "non_equivalences": NON_EQUIVALENCES,
            "sources": [
                _source_ref("control-plane-boundary"),
                _source_ref("capability-registry"),
                _source_ref("uniform-capability-governance"),
            ],
        }
    )
    return out
