"""Compose existing access, document and currentness owners before retrieval.

This is a stateless integration seam, not a new authority. It may only narrow a
Task Contract's declared source perimeter. It does not grant access, decide
professional currentness, rank retrieval candidates, admit Evidence or approve
an answer.

A resolved source identity deliberately includes dossier, source ref, digest and
source version. Reducing it to ``source_ref`` before retrieval would lose the
applicable revision whenever the same path has been ingested more than once.
The existing digest-exact retrieval owner accepts that immutable identity, so
this seam may delegate ranking only after access and currentness have resolved it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import psycopg

from . import human_access, project_document_currentness, project_documents, retrieval
from .contract import TaskContract


class RetrievalScopeError(ValueError):
    """Base fail-closed result for pre-retrieval source composition."""

    status = "retrieval_scope_unavailable"


class RetrievalScopeDenied(RetrievalScopeError):
    status = "forbidden_scope"


class RetrievalScopeUnresolved(RetrievalScopeError):
    status = "applicability_unresolved"


class RetrievalScopeConflicting(RetrievalScopeError):
    status = "applicability_conflicting"


class RetrievalScopeUndeclared(RetrievalScopeError):
    status = "outside_declared_perimeter"


@dataclass(frozen=True)
class PreservedSourceIdentity:
    dossier: str
    source_ref: str
    source_digest: str
    source_version: int


@dataclass(frozen=True)
class ResolvedRetrievalSource:
    document_id: str
    purpose: str
    document_version_id: str
    dossier: str
    source_ref: str
    source_digest: str
    source_version: int
    basis_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class RetrievalScopeResolution:
    project_id: str
    principal_ref: str
    sources: tuple[ResolvedRetrievalSource, ...]


def _required(value: object, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise RetrievalScopeError(f"{field} is required")
    return text


def _contract_project_id(contract: TaskContract) -> str:
    scope = contract.raw.get("scope") or {}
    return _required(
        scope.get("parent_project_id") or scope.get("project_id") or contract.dossier,
        "contract project scope",
    )


def _source_identity_for_revision(
    conn: psycopg.Connection,
    *,
    document_version_id: str,
    project_id: str,
) -> PreservedSourceIdentity:
    """Resolve the exact preserved source behind one professional revision.

    The join is read-only composition across the existing Project Document and
    preserved-source tables. It does not select a revision; currentness must
    already have resolved one exact ``document_version_id``.
    """

    revision = project_documents.get_revision(conn, document_version_id)
    source_document_id = _required(revision.get("source_document_id"), "source_document_id")
    source_version = int(revision.get("source_version") or 0)
    if source_version < 1:
        raise RetrievalScopeError("resolved revision has no preserved source version")

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT d.dossier,
                   v.source_ref,
                   v.source_digest,
                   v.version,
                   d.parent_project_id
              FROM document_versions v
              JOIN source_documents d ON d.document_id = v.document_id
             WHERE v.document_id = %s AND v.version = %s
            """,
            (source_document_id, source_version),
        )
        row = cur.fetchone()
    if row is None:
        raise RetrievalScopeError("resolved revision source is unavailable")

    dossier = _required(row[0], "source dossier")
    source_ref = _required(row[1], "source_ref")
    source_digest = _required(row[2], "source_digest")
    resolved_source_version = int(row[3] or 0)
    source_project_id = _required(row[4], "source parent_project_id")
    if source_project_id != project_id or resolved_source_version != source_version:
        raise RetrievalScopeDenied("requested retrieval perimeter is not accessible")

    return PreservedSourceIdentity(
        dossier=dossier,
        source_ref=source_ref,
        source_digest=source_digest,
        source_version=resolved_source_version,
    )


def resolve_accessible_applicable_sources(
    conn: psycopg.Connection,
    principal: human_access.PrincipalContext,
    *,
    contract: TaskContract,
    project_id: str,
    requested_documents: Iterable[tuple[str, str]],
) -> RetrievalScopeResolution:
    """Resolve exact source identities eligible for retrieval.

    Order is deliberate and fail-closed:

    1. require project access;
    2. require document access before reading document metadata;
    3. prove the document belongs to the declared Project;
    4. ask the existing currentness owner for the requested purpose;
    5. accept only ``resolved`` currentness;
    6. map that exact professional revision to its preserved source identity;
    7. require the source dossier to equal the Task Contract dossier;
    8. require the source ref to already be declared by the Task Contract.

    The returned identity MUST NOT be collapsed to ``source_ref``. Digest-exact
    semantic and lexical retrieval already exist and can consume the preserved
    ``(source_ref, source_digest)`` pair directly.

    Nothing here widens the Task Contract or changes any persisted authority.
    """

    project_id = _required(project_id, "project_id")
    if _contract_project_id(contract) != project_id:
        raise RetrievalScopeDenied("requested retrieval perimeter is not accessible")

    try:
        human_access.require_access(
            conn,
            principal_ref=principal.principal_ref,
            project_id=project_id,
            resource_type="project",
            resource_id=project_id,
            action="project.read",
        )
    except human_access.HumanAccessError:
        raise RetrievalScopeDenied("requested retrieval perimeter is not accessible") from None

    declared = set(contract.sources)
    resolved_sources: list[ResolvedRetrievalSource] = []
    seen_identities: set[tuple[str, str, str, int]] = set()

    for raw_document_id, raw_purpose in requested_documents:
        document_id = _required(raw_document_id, "document_id")
        purpose = _required(raw_purpose, "purpose")

        try:
            human_access.require_access(
                conn,
                principal_ref=principal.principal_ref,
                project_id=project_id,
                resource_type="project_document",
                resource_id=document_id,
                action="document.read",
            )
        except human_access.HumanAccessError:
            # Do not expose whether an inaccessible document exists.
            raise RetrievalScopeDenied("requested retrieval perimeter is not accessible") from None

        document = project_documents.get_document(conn, document_id)
        if str(document.get("parent_project_id") or "") != project_id:
            raise RetrievalScopeDenied("requested retrieval perimeter is not accessible")

        currentness = project_document_currentness.resolve_currentness(
            conn,
            document_id=document_id,
            purpose=purpose,
        )
        resolution_status = str(currentness.get("resolution_status") or "")
        if resolution_status == "unresolved":
            raise RetrievalScopeUnresolved(
                "no applicable document revision is resolved for the requested purpose"
            )
        if resolution_status == "conflicting":
            raise RetrievalScopeConflicting(
                "applicable document revision is conflicting for the requested purpose"
            )
        if resolution_status != "resolved":
            raise RetrievalScopeError("currentness returned an unsupported resolution status")

        document_version_id = _required(
            currentness.get("document_version_id"),
            "document_version_id",
        )
        identity = _source_identity_for_revision(
            conn,
            document_version_id=document_version_id,
            project_id=project_id,
        )
        if identity.dossier != contract.dossier:
            raise RetrievalScopeDenied("requested retrieval perimeter is not accessible")
        if identity.source_ref not in declared:
            raise RetrievalScopeUndeclared(
                "resolved source is outside the Task Contract declared perimeter"
            )

        identity_key = (
            identity.dossier,
            identity.source_ref,
            identity.source_digest,
            identity.source_version,
        )
        if identity_key in seen_identities:
            continue
        seen_identities.add(identity_key)

        basis = currentness.get("basis") or {}
        basis_refs = tuple(str(ref) for ref in basis.get("basis_refs") or () if str(ref).strip())
        resolved_sources.append(
            ResolvedRetrievalSource(
                document_id=document_id,
                purpose=purpose,
                document_version_id=document_version_id,
                dossier=identity.dossier,
                source_ref=identity.source_ref,
                source_digest=identity.source_digest,
                source_version=identity.source_version,
                basis_refs=basis_refs,
            )
        )

    return RetrievalScopeResolution(
        project_id=project_id,
        principal_ref=principal.principal_ref,
        sources=tuple(resolved_sources),
    )


def retrieve_accessible_applicable_hybrid(
    conn: psycopg.Connection,
    principal: human_access.PrincipalContext,
    *,
    contract: TaskContract,
    project_id: str,
    requested_documents: Iterable[tuple[str, str]],
    query: str,
    top_k: int = 4,
    candidate_k: int = 12,
    rrf_k: int = 60,
    semantic_weight: float = 1.0,
    lexical_weight: float = 1.0,
) -> tuple[RetrievalScopeResolution, list[retrieval.HybridRetrievedChunk]]:
    """Resolve access/applicability first, then delegate exact ranking.

    The composition owner does not rank. It passes only the already-authorized,
    already-resolved immutable identities to the existing retrieval owner. Empty
    exact retrieval stays empty; there is no fallback to current-path content.
    """

    resolution = resolve_accessible_applicable_sources(
        conn,
        principal,
        contract=contract,
        project_id=project_id,
        requested_documents=requested_documents,
    )
    exact_sources = tuple(
        (source.source_ref, source.source_digest) for source in resolution.sources
    )
    hits = retrieval.retrieve_hybrid_exact_scoped(
        conn,
        contract,
        query,
        sources=exact_sources,
        top_k=top_k,
        candidate_k=candidate_k,
        rrf_k=rrf_k,
        semantic_weight=semantic_weight,
        lexical_weight=lexical_weight,
    )
    return resolution, hits


AUTHORITY = {
    "composition_only": True,
    "grants_access": False,
    "decides_currentness": False,
    "widens_task_contract": False,
    "ranks_retrieval": False,
    "source_ref_only_retrieval_safe": False,
    "admits_evidence": False,
    "approves": False,
    "persists_state": False,
}
