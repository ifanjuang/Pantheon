"""Phase 1 — canonical source map.

Each MCP resource maps to one repository file. Every answer carries the
source file, its effective authority-index labels, declared status header and
content fingerprint. The server never invents doctrine: a missing file is
reported as missing and an unindexed file stays unindexed.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .authority_index import load_authority_catalog, resolve_authority
from .repo import find_repo_root, read_repo_text, repo_file_exists

# key -> (relative path, short title)
SOURCES: dict[str, tuple[str, str]] = {
    "status": ("docs/governance/STATUS.md", "Repository status and posture"),
    "what-runs": ("docs/governance/WHAT_RUNS.md", "Runtime-status honesty map"),
    "authority-index": ("docs/governance/AUTHORITY_INDEX.md", "Authority map"),
    "glossary": ("docs/governance/GLOSSARY.md", "Vocabulary and the four axes (E/V/K/C)"),
    "architecture": ("docs/governance/ARCHITECTURE.md", "Pantheon architecture boundary"),
    "modules": ("docs/governance/MODULES.md", "Governance module map"),
    "capability-placement": ("docs/governance/CAPABILITY_PLACEMENT.md", "Where capabilities live"),
    "capability-registry": (
        "docs/governance/CAPABILITY_REGISTRY.md",
        "Governed capability declaration model",
    ),
    "uniform-capability-governance": (
        "docs/governance/UNIFORM_CAPABILITY_GOVERNANCE.md",
        "One law, one passport, the chokepoint",
    ),
    "task-contracts": ("docs/governance/TASK_CONTRACTS.md", "Task Contract doctrine"),
    "evidence-pack": ("docs/governance/EVIDENCE_PACK.md", "Evidence Pack doctrine"),
    "approvals": ("docs/governance/APPROVALS.md", "Approval ceilings C0-C5"),
    "memory": ("docs/governance/MEMORY.md", "Hermes memory vs Registre Probatoire"),
    "registre-probatoire": (
        "docs/governance/EVIDENCE_MEMORY_CANONICALIZATION.md",
        "Registre Probatoire central doc",
    ),
    "knowledge-ingestion-memory": (
        "docs/governance/KNOWLEDGE_INGESTION_AND_MEMORY.md",
        "Knowledge ingestion and memory boundary",
    ),
    "source-ingestion-retrieval": (
        "docs/governance/SOURCE_INGESTION_RETRIEVAL_MODEL.md",
        "Source ingestion and retrieval model",
    ),
    "answer-verification-gate": (
        "docs/governance/ANSWER_VERIFICATION_GATE.md",
        "Answer verification (V) and consequence (K)",
    ),
    "user-decision-gate": ("docs/governance/USER_DECISION_GATE.md", "Escalation to the human"),
    "target-architecture": ("docs/governance/TARGET_ARCHITECTURE.md", "Coherence compass"),
    "domain-pack-spec": ("docs/governance/DOMAIN_PACK_SPEC.md", "Domain pack specification"),
    "preflight": (
        "docs/governance/MODULE_INVOCATION_PREFLIGHT.md",
        "Invocation and connectivity preflight",
    ),
    "mcp-boundary": (
        "docs/governance/MCP_PANTHEON_MINIMAL_PROFILE.md",
        "Minimal Pantheon MCP governance boundary",
    ),
    "hermes-runtime-governance": (
        "docs/governance/HERMES_RUNTIME_GOVERNANCE.md",
        "Hermes runtime governance projection",
    ),
    "control-boundary": (
        "docs/governance/PANTHEON_CONTROL_BOUNDARY.md",
        "Pantheon Control boundary (dashboard/)",
    ),
    "control-plane-boundary": (
        "docs/governance/PANTHEON_CONTROL_PLANE_BOUNDARY.md",
        "Pantheon Control operational-state boundary",
    ),
    "passport-template": ("templates/mcp_capability_passport.yaml", "Capability passport template"),
}

STRUCTURE_SECTIONS: tuple[dict, ...] = (
    {
        "key": "orientation",
        "title": "Orientation and authority",
        "reason": (
            "Locate the repository posture, controlled vocabulary, governance "
            "areas and the authority that may be relied upon."
        ),
        "sources": ("status", "authority-index", "glossary", "modules"),
    },
    {
        "key": "delegation-and-decision",
        "title": "Delegation and decision boundaries",
        "reason": (
            "Separate bounded Hermes execution from evidence, approval and "
            "explicit human escalation."
        ),
        "sources": (
            "task-contracts",
            "evidence-pack",
            "approvals",
            "user-decision-gate",
        ),
    },
    {
        "key": "truth-and-records",
        "title": "Truth, verification and governed records",
        "reason": (
            "Keep runtime memory non-authoritative while making consequential "
            "claims traceable and reviewable."
        ),
        "sources": (
            "memory",
            "registre-probatoire",
            "knowledge-ingestion-memory",
            "source-ingestion-retrieval",
            "answer-verification-gate",
        ),
    },
    {
        "key": "capabilities-and-architecture",
        "title": "Capabilities and architecture",
        "reason": (
            "Place capabilities in the correct layer and expose their governed "
            "admission contract without turning Pantheon into a runtime."
        ),
        "sources": (
            "capability-placement",
            "capability-registry",
            "uniform-capability-governance",
            "target-architecture",
            "domain-pack-spec",
            "preflight",
            "control-plane-boundary",
            "passport-template",
        ),
    },
    {
        "key": "policy-interface",
        "title": "Read-only policy interface",
        "reason": (
            "Give Hermes a traceable view of governance while preserving the "
            "one-way boundary: Pantheon governs and Hermes executes."
        ),
        "sources": (
            "mcp-boundary",
            "hermes-runtime-governance",
            "control-boundary",
        ),
    },
)

# Condition-driven policy routing. These mappings point only to governance
# doctrine; they do not select business records or infer a domain workflow.
CONDITION_SOURCE_KEYS: dict[str, tuple[str, ...]] = {
    "complex_task": ("task-contracts", "preflight"),
    "multi_step_workflow": ("task-contracts", "preflight"),
    "source_required": ("source-ingestion-retrieval", "answer-verification-gate", "evidence-pack"),
    "factual_claim": ("answer-verification-gate", "evidence-pack"),
    "evidence_gap": ("evidence-pack", "answer-verification-gate"),
    "source_freshness_risk": ("source-ingestion-retrieval", "answer-verification-gate"),
    "memory_recall_requested": ("memory", "knowledge-ingestion-memory"),
    "prior_decision_reuse": ("memory", "registre-probatoire"),
    "project_history_reuse": ("memory", "registre-probatoire"),
    "legal_or_professional_risk": ("approvals", "user-decision-gate", "evidence-pack"),
    "liability_risk": ("approvals", "user-decision-gate"),
    "external_transmission": ("approvals", "user-decision-gate", "task-contracts"),
    "external_effect": ("approvals", "user-decision-gate", "task-contracts"),
    "delivery_quality_required": ("answer-verification-gate", "evidence-pack"),
    "artifact_fabrication": ("task-contracts", "evidence-pack"),
    "capability_change": ("capability-registry", "uniform-capability-governance", "capability-placement"),
}

_SOURCE_SEARCH_STOPWORDS = {
    "and", "avec", "dans", "des", "for", "from", "les", "pour", "sur", "the", "une",
}


def load_authority_index(root: Path | None = None) -> dict[str, dict[str, str]]:
    """Compatibility view of exact rows across the effective authority map."""
    root = root or find_repo_root()
    catalog = load_authority_catalog(root)
    return {
        record["path"]: {
            "authority": record["authority"],
            "status": record["repo_state"],
            "source_index": record["source_index"],
            "source_line": record["source_line"],
        }
        for record in catalog["records"]
    }


_STATUS_HEADER = re.compile(r"^Status:\s*(?P<status>.+?)\s*$", re.MULTILINE)


def _first_paragraph(text: str) -> str:
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#") or not s:
            if lines:
                break
            continue
        lines.append(s)
        if len(lines) >= 2:
            break
    return " ".join(lines)[:400]


def repository_version(root: Path | None = None) -> str:
    """Return the declared repository release version, or ``unknown``."""
    root = root or find_repo_root()
    try:
        return read_repo_text("VERSION", root).strip() or "unknown"
    except FileNotFoundError:
        return "unknown"


def describe_source(
    key: str,
    root: Path | None = None,
    *,
    catalog: dict | None = None,
) -> dict:
    """Return the governed description of one source, without its body."""
    root = root or find_repo_root()
    if key not in SOURCES:
        return {
            "key": key,
            "error": "unknown source key",
            "known_keys": sorted(SOURCES),
        }
    rel, title = SOURCES[key]
    resolution = resolve_authority(rel, catalog or load_authority_catalog(root))
    exists = repo_file_exists(rel, root)
    info = {
        "uri": f"pantheon://{key}",
        "title": title,
        "source_file": rel,
        "exists": exists,
        "authority": resolution["authority"],
        "status": resolution["repo_state"],
        "authority_resolution": resolution["resolution"],
        "authority_ok": resolution["resolution"] == "resolved",
        "authority_source": {
            "index": resolution["source_index"],
            "line": resolution["source_line"],
            "entry": resolution["entry"],
            "matched_path": resolution.get("matched_path"),
            "match_type": resolution.get("match_type"),
        },
        "authority_diagnostics": resolution["diagnostics"],
    }
    if exists:
        text = read_repo_text(rel, root)
        status_header = _STATUS_HEADER.search(text)
        info["declared_status"] = (
            status_header.group("status") if status_header else "not declared"
        )
        info["content_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        info["summary"] = _first_paragraph(text)
    else:
        info["declared_status"] = "not available"
        info["content_sha256"] = None
        info["summary"] = (
            "source file absent in this checkout; "
            "treat as documented elsewhere or pending"
        )
    return info


def read_source(key: str, root: Path | None = None) -> dict:
    """Return one source with its full body, labeled with authority/status."""
    info = describe_source(key, root)
    if info.get("exists"):
        info["body"] = read_repo_text(SOURCES[key][0], root)
    return info


def list_sources(root: Path | None = None) -> list[dict]:
    root = root or find_repo_root()
    catalog = load_authority_catalog(root)
    return [describe_source(k, root, catalog=catalog) for k in sorted(SOURCES)]


def find_relevant_sources(request: dict, root: Path | None = None) -> dict:
    """Return a small, explainable doctrine shortlist from material conditions.

    The result is deliberately compact. A candidate only becomes an opened
    source after a separate ``read_doctrine`` call.
    """
    root = root or find_repo_root()
    conditions = request.get("conditions", [])
    if not isinstance(conditions, list):
        conditions = []
    conditions = [str(item).strip() for item in conditions if str(item).strip()]

    raw_terms = request.get("terms", request.get("query", ""))
    if isinstance(raw_terms, list):
        raw_terms = " ".join(str(item) for item in raw_terms)
    tokens = {
        token
        for token in re.findall(r"[a-z0-9]+", str(raw_terms).lower())
        if len(token) > 2 and token not in _SOURCE_SEARCH_STOPWORDS
    }

    try:
        limit = int(request.get("limit", 3))
    except (TypeError, ValueError):
        limit = 3
    limit = max(1, min(limit, 8))

    scores: dict[str, int] = {}
    reasons: dict[str, list[str]] = {}
    for condition in conditions:
        for position, key in enumerate(CONDITION_SOURCE_KEYS.get(condition, ())):
            scores[key] = scores.get(key, 0) + max(1, 6 - position)
            reasons.setdefault(key, []).append(f"condition:{condition}")

    for key, (source_file, title) in SOURCES.items():
        haystack = f"{key} {source_file} {title}".lower()
        matched = sorted(token for token in tokens if token in haystack)
        if matched:
            scores[key] = scores.get(key, 0) + 2 * len(matched)
            reasons.setdefault(key, []).extend(f"term:{token}" for token in matched)

    ranked = sorted(scores, key=lambda key: (-scores[key], key))[:limit]
    catalog = load_authority_catalog(root)
    candidates = []
    for key in ranked:
        info = describe_source(key, root, catalog=catalog)
        candidates.append(
            {
                "key": key,
                "uri": info["uri"],
                "title": info["title"],
                "source_file": info["source_file"],
                "exists": info["exists"],
                "authority": info["authority"],
                "status": info["status"],
                "score": scores[key],
                "matched_on": reasons[key],
            }
        )

    return {
        "result": "shortlisted" if candidates else "no_match",
        "conditions": conditions,
        "terms": sorted(tokens),
        "limit": limit,
        "candidates": candidates,
        "next_action": (
            "read_doctrine for only the candidate keys needed by the request"
            if candidates
            else "clarify the material condition or use list_sources for explicit catalog inspection"
        ),
        "boundary": "shortlisted candidate != exact source opened",
    }


def explain_structure(key: str = "", root: Path | None = None) -> dict:
    """Explain the governed document structure without creating new doctrine."""
    root = root or find_repo_root()
    if key and key not in SOURCES:
        return {
            "key": key,
            "error": "unknown source key",
            "known_keys": sorted(SOURCES),
        }

    sections = [
        {
            **section,
            "sources": [
                {
                    "key": source_key,
                    "title": SOURCES[source_key][1],
                    "uri": f"pantheon://{source_key}",
                }
                for source_key in section["sources"]
            ],
        }
        for section in STRUCTURE_SECTIONS
        if not key or key in section["sources"]
    ]
    response = {
        "purpose": (
            "Read-only governance wiki for Hermes: locate a rule, understand why "
            "it sits in the structure, then follow its traced repository source."
        ),
        "boundary": {
            "interaction": "Hermes Web/dashboard or a compatible replaceable Hermes client interacts",
            "execution": "Hermes Agent executes",
            "governance": "Pantheon governs",
            "projection": "Pantheon Cockpit exposes governed status, decisions and navigation",
            "effect": "informational only; this response grants no authority",
        },
        "sections": sections,
    }
    if key:
        response["focus"] = describe_source(key, root)
    return response
