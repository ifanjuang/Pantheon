"""Steps 4-5 of the governed loop: scoped retrieval → candidate return.

STAND-IN (GOVERNANCE_STATUS.md stand-in rule): this module occupies the
Hermes-side execution seat for the proof loop. It is NOT the Hermes Agent:

    stand_in_runner != Hermes Agent

It exists to prove the governance cage end to end; the real runtime actor is
the governed Hermes profile. The LLM slot (a Hermes-side Drafter) plugs into the
Block 2 seam below — this repository never wires or routes a provider.

The runner produces exactly two kinds of output, both as data:

- a Result Candidate + Evidence Pack Candidate (status draft_to_review), or
- a refusal / capability-gap report, when the request falls outside the
  contract's perimeter or the perimeter cannot support an answer.

It approves nothing, sends nothing, remembers nothing.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass

import yaml

from . import human_access, retrieval_scope
from .contract import TaskContract, _schema
from .drafting import (
    Drafter,
    DeterministicDrafter,
    claim_support_review,
    duty_of_care_flags,
    grounding_review,
    review_flags,
    verify_draft,
)
from .retrieval import HybridRetrievedChunk, retrieve_hybrid_scoped
from .store import RetrievedChunk, retrieve_scoped


class RunnerInvariantError(RuntimeError):
    """The runner was about to emit an object that breaks a governance invariant."""


COMMITMENT_PATTERNS = (
    r"nous acceptons",
    r"nous validons",
    r"vous pouvez (lancer|démarrer)",
    r"bon pour accord",
    r"nous confirmons",
)

SEND_INTENT_TERMS = (
    "envoie", "envoyer", "envoi",
    "transmet", "transmiss",
    "expédi",
    "diffus",
    "fais suivre",
    "send", "forward",
)

MAX_USEFUL_DISTANCE = 0.85
HYBRID_TOP_K = 4
HYBRID_CANDIDATE_K = 12
HYBRID_RRF_K = 60
_ORIGINAL_RETRIEVE_SCOPED = retrieve_scoped


@dataclass(frozen=True)
class RunOutput:
    kind: str
    documents: list

    def to_yaml(self) -> str:
        return yaml.safe_dump_all(self.documents, sort_keys=False, allow_unicode=True)


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _request_scope_digest(contract: TaskContract, question: str) -> str:
    """Bind one candidate stream to the exact bounded request it executed."""
    payload = {
        "contract_id": contract.contract_id,
        "question": question,
        "dossier": contract.dossier,
        "sources": list(contract.sources),
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _request_provenance(contract: TaskContract, question: str) -> dict[str, str]:
    return {
        "request_ref": contract.contract_id,
        "request_scope_digest": _request_scope_digest(contract, question),
    }


def _refusal(contract: TaskContract, question: str, reason: str, detail: str) -> RunOutput:
    return RunOutput(
        kind="refusal",
        documents=[
            {
                "object_type": "result_candidate",
                "object_id": f"{contract.contract_id}.refusal",
                "result_candidate_id": f"{contract.contract_id}.refusal",
                "applies_to": contract.contract_id,
                "status": "refused_capability_gap",
                **_request_provenance(contract, question),
                "created_at": _now(),
                "body": f"Refus : {detail}",
                "external_action_authorized": False,
                "refusal": {
                    "question": question,
                    "reason": reason,
                    "detail": detail,
                    "boundary": "the perimeter decides what can be answered; "
                                "the runner does not improvise beyond it",
                },
                "governance_refs": ["docs/governance/MVP_GOVERNED_TASK_LOOP.md"],
            }
        ],
    )


def _detect_commitments(text: str) -> list[dict]:
    flags = []
    for pattern in COMMITMENT_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            flags.append(
                {
                    "phrase": match.group(0),
                    "risk": "engagement externe si envoyé tel quel",
                }
            )
    return flags


_FORBIDDEN_STATUSES = frozenset({"sent", "approved", "authorized", "validated"})


def _assert_no_external_authorization(documents: list) -> None:
    for document in documents:
        if document.get("external_action_authorized", False):
            raise RunnerInvariantError(
                f"runner emitted external_action_authorized=True on {document.get('object_id')!r}"
            )
        status = str(document.get("status", ""))
        if status in _FORBIDDEN_STATUSES:
            raise RunnerInvariantError(
                f"runner emitted forbidden status {status!r} on {document.get('object_id')!r}"
            )


def _assert_conforms_to_schema(documents: list) -> None:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover
        raise RunnerInvariantError("cannot validate runner output — jsonschema not installed") from exc
    schema = _schema()
    for document in documents:
        try:
            jsonschema.validate(document, schema)
        except jsonschema.ValidationError as exc:
            raise RunnerInvariantError(
                f"runner emitted a non-conforming {document.get('object_type')!r} "
                f"({document.get('object_id')!r}): {exc.message}"
            ) from exc


def _is_useful(hit: HybridRetrievedChunk) -> bool:
    """Admit a scoped lexical match or a useful semantic match.

    RRF orders candidates. It is not a truth, confidence or Evidence-quality
    threshold.
    """
    if hit.lexical_rank is not None:
        return True
    return hit.semantic_rank is not None and hit.chunk.distance <= MAX_USEFUL_DISTANCE


def _select_useful_context_hits(
    hits: list[HybridRetrievedChunk],
    *,
    required_sources: tuple[tuple[str, str], ...] = (),
    limit: int = HYBRID_TOP_K,
) -> list[HybridRetrievedChunk]:
    """Select useful context without silently dropping a resolved source.

    The global fused order remains authoritative for ranking. On the project-aware
    exact-source path only, one already-useful candidate from each explicitly
    resolved source is retained when the fixed context budget permits it, then
    remaining slots are filled in the original fused order.

    A source with no useful candidate is never forced into context. This is a
    final context-selection rule, not a retrieval floor, truth signal or Evidence
    admission rule.
    """
    if limit < 1:
        raise ValueError("context selection limit must be at least 1")

    useful_hits = [hit for hit in hits if _is_useful(hit)]
    if not useful_hits or not required_sources:
        return useful_hits[:limit]

    required = set(required_sources)
    selected: list[HybridRetrievedChunk] = []
    selected_keys: set[tuple[str, str, int]] = set()
    covered_sources: set[tuple[str, str]] = set()

    for hit in useful_hits:
        source_key = (hit.chunk.source_ref, hit.chunk.source_digest)
        if source_key not in required or source_key in covered_sources:
            continue
        selected.append(hit)
        selected_keys.add((hit.chunk.source_ref, hit.chunk.source_digest, hit.chunk.chunk_no))
        covered_sources.add(source_key)
        if len(selected) == limit:
            break

    for hit in useful_hits:
        if len(selected) == limit:
            break
        hit_key = (hit.chunk.source_ref, hit.chunk.source_digest, hit.chunk.chunk_no)
        if hit_key in selected_keys:
            continue
        selected.append(hit)
        selected_keys.add(hit_key)

    rank = {id(hit): index for index, hit in enumerate(useful_hits)}
    selected.sort(key=lambda hit: rank[id(hit)])
    return selected


def _metric_profile(hit: HybridRetrievedChunk) -> str:
    semantic = hit.semantic_rank if hit.semantic_rank is not None else "none"
    lexical = hit.lexical_rank if hit.lexical_rank is not None else "none"
    return (
        "weighted_rrf_v1"
        f";semantic_rank={semantic}"
        f";lexical_rank={lexical}"
        f";hybrid_score={hit.hybrid_score:.12f}"
    )


def _retrieve_hits(conn, contract: TaskContract, question: str) -> list[HybridRetrievedChunk]:
    """Use hybrid retrieval while retaining the former injectable test seam."""
    if retrieve_scoped is not _ORIGINAL_RETRIEVE_SCOPED:
        chunks = retrieve_scoped(conn, contract, question)
        return [
            HybridRetrievedChunk(
                chunk=chunk,
                hybrid_score=1.0 / (HYBRID_RRF_K + rank),
                semantic_rank=rank,
                lexical_rank=None,
            )
            for rank, chunk in enumerate(chunks, start=1)
        ]
    return retrieve_hybrid_scoped(
        conn,
        contract,
        question,
        top_k=HYBRID_TOP_K,
        candidate_k=HYBRID_CANDIDATE_K,
        rrf_k=HYBRID_RRF_K,
    )


def _evidence_id(chunk: RetrievedChunk) -> str:
    stem = chunk.source_ref.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    digest = (chunk.source_digest or "legacy-no-digest")[:12]
    return f"ei-{stem}-{chunk.chunk_no}-{digest}"


def _bind_evidence_refs(claim_review: dict, chunks: list[RetrievedChunk]) -> list[dict]:
    evidence_ids = {
        (chunk.source_ref, chunk.chunk_no, chunk.source_digest): _evidence_id(chunk)
        for chunk in chunks
    }
    bindings: list[dict] = []
    for claim in claim_review["supported_claims"]:
        supports = []
        for support in claim["supports"]:
            enriched = dict(support)
            enriched["evidence_item_ref"] = evidence_ids[
                (support["source_ref"], support["chunk_no"], support["source_digest"])
            ]
            supports.append(enriched)
        bindings.append(
            {
                "claim": claim["claim"],
                "support_status": "sourced_not_verified",
                "supports": supports,
            }
        )
    return bindings


def _preflight_refusal(contract: TaskContract, question: str) -> RunOutput | None:
    lowered = question.lower()
    if "external_send" in contract.forbidden and any(
        term in lowered for term in SEND_INTENT_TERMS
    ):
        return _refusal(
            contract,
            question,
            "forbidden_scope",
            "external_send is forbidden by the contract; transmission is a human decision",
        )
    return None


def _scope_resolution_projection(
    resolution: retrieval_scope.RetrievalScopeResolution,
) -> dict:
    """Project resolved applicability as provenance, never as approval."""
    return {
        "project_id": resolution.project_id,
        "resolution_status": "resolved_for_retrieval",
        "sources": [
            {
                "document_id": source.document_id,
                "purpose": source.purpose,
                "document_version_id": source.document_version_id,
                "source_ref": source.source_ref,
                "source_digest": source.source_digest,
                "source_version": source.source_version,
                "basis_refs": list(source.basis_refs),
            }
            for source in resolution.sources
        ],
        "authority": {
            "decides_professional_approval": False,
            "admits_evidence": False,
            "widens_task_contract": False,
        },
    }


def run(
    conn,
    contract: TaskContract,
    question: str,
    drafter: Drafter | None = None,
) -> RunOutput:
    output = _run(conn, contract, question, drafter or DeterministicDrafter())
    _assert_no_external_authorization(output.documents)
    _assert_conforms_to_schema(output.documents)
    return output


def run_accessible_applicable(
    conn,
    principal: human_access.PrincipalContext,
    contract: TaskContract,
    question: str,
    *,
    project_id: str,
    requested_documents: Iterable[tuple[str, str]],
    drafter: Drafter | None = None,
) -> RunOutput:
    """Run the same candidate path after access + professional currentness.

    This entry point is the project-aware composition for Pantheon-Next#827-style review. It
    delegates access and applicability to their existing owners, then delegates
    ranking to the existing exact hybrid retrieval path. A resolved source is
    recorded as provenance only: resolved for retrieval does not mean approved,
    admitted as Evidence, or professionally validated.
    """
    preflight = _preflight_refusal(contract, question)
    if preflight is not None:
        output = preflight
    else:
        try:
            resolution, hits = retrieval_scope.retrieve_accessible_applicable_hybrid(
                conn,
                principal,
                contract=contract,
                project_id=project_id,
                requested_documents=requested_documents,
                query=question,
                top_k=HYBRID_CANDIDATE_K,
                candidate_k=HYBRID_CANDIDATE_K,
                rrf_k=HYBRID_RRF_K,
            )
        except retrieval_scope.RetrievalScopeUndeclared:
            output = _refusal(
                contract,
                question,
                "outside_perimeter",
                "the resolved applicable source is outside the Task Contract declared perimeter; "
                "widening the perimeter is a contract revision, not a runner decision",
            )
        except retrieval_scope.RetrievalScopeUnresolved:
            output = _refusal(
                contract,
                question,
                "applicability_unresolved",
                "no applicable document revision is resolved for the requested purpose",
            )
        except retrieval_scope.RetrievalScopeConflicting:
            output = _refusal(
                contract,
                question,
                "applicability_conflicting",
                "applicable document revision is conflicting for the requested purpose",
            )
        except retrieval_scope.RetrievalScopeDenied:
            output = _refusal(
                contract,
                question,
                "forbidden_scope",
                "the requested project/document retrieval scope is not accessible",
            )
        except retrieval_scope.RetrievalScopeError:
            output = _refusal(
                contract,
                question,
                "retrieval_scope_unavailable",
                "the project/document retrieval scope could not be resolved safely",
            )
        else:
            required_sources = tuple(
                (source.source_ref, source.source_digest) for source in resolution.sources
            )
            selected_hits = _select_useful_context_hits(
                hits,
                required_sources=required_sources,
                limit=HYBRID_TOP_K,
            )
            output = _run_with_hits(
                contract,
                question,
                drafter or DeterministicDrafter(),
                selected_hits,
                scope_resolution=resolution,
            )

    _assert_no_external_authorization(output.documents)
    _assert_conforms_to_schema(output.documents)
    return output


def _run(
    conn,
    contract: TaskContract,
    question: str,
    drafter: Drafter,
) -> RunOutput:
    preflight = _preflight_refusal(contract, question)
    if preflight is not None:
        return preflight
    return _run_with_hits(contract, question, drafter, _retrieve_hits(conn, contract, question))


def _run_with_hits(
    contract: TaskContract,
    question: str,
    drafter: Drafter,
    hits: list[HybridRetrievedChunk],
    *,
    scope_resolution: retrieval_scope.RetrievalScopeResolution | None = None,
) -> RunOutput:
    useful_hits = [hit for hit in hits if _is_useful(hit)]
    useful = [hit.chunk for hit in useful_hits]
    if not useful:
        return _refusal(
            contract,
            question,
            "outside_perimeter",
            "no declared source supports this question; widening the perimeter is a contract revision, not a runner decision",
        )

    draft = drafter.draft(intent=contract.intent, question=question, chunks=useful)
    verify_draft(draft, useful)
    claim_review = claim_support_review(draft, useful)
    if claim_review["unsupported_claims"]:
        return _refusal(
            contract,
            question,
            "unsupported_claim",
            "the draft contains an assertive claim without exact retrieved support; "
            "the runner refuses rather than fill the gap from model knowledge",
        )

    now = _now()
    request_provenance = _request_provenance(contract, question)
    rc_id = f"{contract.contract_id}.rc-001"
    ep_id = f"{contract.contract_id}.ep-001"
    claim_bindings = _bind_evidence_refs(claim_review, useful)
    result_candidate = {
        "object_type": "result_candidate",
        "object_id": rc_id,
        "result_candidate_id": rc_id,
        "applies_to": contract.contract_id,
        "status": "draft_to_review",
        **request_provenance,
        "created_at": now,
        "body": draft,
        "external_action_authorized": False,
        "citation_integrity_verified": True,
        "claim_support_review": {
            "status": claim_review["status"],
            "supported_claim_count": len(claim_bindings),
            "unsupported_claim_count": 0,
            "evidence_pack_ref": ep_id,
            "note": claim_review["note"],
        },
        "commitment_flags": _detect_commitments(draft),
        "professional_assertion_flags": review_flags(draft),
        "duty_of_care_flags": duty_of_care_flags(draft),
        "grounding_review": grounding_review(draft, useful),
        "governance_refs": [
            "docs/governance/MVP_GOVERNED_TASK_LOOP.md",
            "docs/governance/PROFESSIONAL_DUTY_OF_CARE.md",
            "docs/governance/RAG_INGESTION_AND_EVIDENCE_BOUNDARIES.md",
        ],
    }
    evidence_pack = {
        "object_type": "evidence_pack_candidate",
        "object_id": ep_id,
        "evidence_pack_id": ep_id,
        "applies_to": contract.contract_id,
        "supports": rc_id,
        "status": "candidate",
        **request_provenance,
        "created_at": now,
        "evidence_items": [
            {
                "evidence_id": _evidence_id(hit.chunk),
                "claim": hit.chunk.body[:160],
                "source_ref": hit.chunk.source_ref,
                "retrieval_trace": hit.chunk.retrieval_trace,
                "retrieval_audit": hit.chunk.retrieval_audit,
                "retrieval_provenance": hit.chunk.retrieval_provenance,
                "retrieval_metrics": {
                    "rank": rank,
                    "distance": hit.chunk.distance,
                    "metric": "cosine_distance",
                    "useful_distance_threshold": MAX_USEFUL_DISTANCE,
                    "profile": _metric_profile(hit),
                    "interpretation": "lower_is_closer_not_truth_probability",
                },
                "support_status": "sourced_not_verified",
            }
            for rank, hit in enumerate(useful_hits, start=1)
        ],
        "claim_support_bindings": claim_bindings,
        "assumptions": [
            "aucune hypothèse ajoutée par le runner ; toute hypothèse relève de la décision humaine"
        ],
        "limitations": [
            "seuls les extraits déclarés au contrat ont été lus",
            "le classement hybride combine des rangs lexicaux et sémantiques ; son score ne mesure ni la vérité ni la qualité d'une Evidence",
            "une liaison claim/support prouve seulement l'origine récupérée ; elle ne vaut ni validation ni admission comme Evidence",
        ],
        "contradictions_preserved": [
            "le runner restitue les passages sans arbitrer entre eux ; toute contradiction entre sources est conservée pour la décision humaine, non résolue"
        ],
        "open_risks": ["toute formulation d'accord engagerait le praticien si envoyée"],
        "possible_decisions": [
            "approve",
            "refuse",
            "request_revision",
            "request_more_evidence",
        ],
        "governance_refs": [
            "docs/governance/MVP_GOVERNED_TASK_LOOP.md",
            "docs/governance/RAG_INGESTION_AND_EVIDENCE_BOUNDARIES.md",
        ],
    }
    if scope_resolution is not None:
        evidence_pack["source_scope_resolution"] = _scope_resolution_projection(scope_resolution)
        evidence_pack["limitations"].append(
            "la résolution de currentness borne la révision interrogée ; elle ne vaut ni approbation professionnelle ni admission comme Evidence"
        )
    return RunOutput(kind="candidates", documents=[result_candidate, evidence_pack])
