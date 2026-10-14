"""Bounded Haystack qualification adapter for Pantheon issue Pantheon-Next#908.

This module is a lab candidate, not a product owner. Pantheon resolves access,
currentness and exact source identity before this adapter is called. Haystack is
used only as a replaceable projection/retrieval implementation.

The adapter deliberately validates the provider response after provider-side
filtering. A provider bug, stale row or poisoned store therefore fails closed
instead of widening the Pantheon retrieval perimeter.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from importlib.metadata import version as package_version
import json
import os
from typing import Iterable

from haystack import Document
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.document_stores.types import DuplicatePolicy

from mvp_vertical.retrieval_scope import ResolvedRetrievalSource, RetrievalScopeResolution


class HaystackQualificationError(RuntimeError):
    """Base fail-closed error for the qualification adapter."""


class HaystackBoundaryViolation(HaystackQualificationError):
    """Raised when provider material does not match the Pantheon-resolved perimeter."""


@dataclass(frozen=True)
class BoundedSourceMaterial:
    """Exact Pantheon-resolved source plus the derivative text to project."""

    source: ResolvedRetrievalSource
    content: str


@dataclass(frozen=True)
class BoundedRetrievalCandidate:
    """Provider-neutral candidate returned to Hermes or another runtime consumer."""

    document_id: str
    document_version_id: str
    dossier: str
    source_ref: str
    source_digest: str
    source_version: int
    purpose: str
    basis_refs: tuple[str, ...]
    content: str
    provider_score: float | None


@dataclass(frozen=True)
class BoundedRetrievalResult:
    """One bounded retrieval response; it carries no Evidence or approval claim."""

    provider: str
    provider_version: str
    query: str
    project_id: str
    candidates: tuple[BoundedRetrievalCandidate, ...]
    evidence_admitted: bool = False
    authorized_effect: bool = False


def _identity_key(source: ResolvedRetrievalSource) -> str:
    return json.dumps(
        [
            source.dossier,
            source.source_ref,
            source.source_digest,
            source.source_version,
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _document_id(binding_instance_id: str, source: ResolvedRetrievalSource) -> str:
    payload = f"{binding_instance_id}\0{_identity_key(source)}".encode("utf-8")
    return f"pantheon-haystack-{sha256(payload).hexdigest()}"


def _assert_safe_deserialization_posture() -> None:
    raw = os.environ.get("HAYSTACK_UNSAFE_DESERIALIZATION", "").strip().lower()
    if raw in {"1", "true"}:
        raise HaystackQualificationError(
            "HAYSTACK_UNSAFE_DESERIALIZATION must remain disabled for the bounded qualification"
        )


class HaystackBoundedRetrievalAdapter:
    """Project and query only exact identities already resolved by Pantheon.

    ``binding_instance_id`` is operational projection identity only. It is not a
    Project, dossier, Source or CapabilityBinding identity and must never be used
    to grant access or decide currentness.
    """

    def __init__(
        self,
        *,
        binding_instance_id: str,
        document_store: InMemoryDocumentStore | None = None,
    ) -> None:
        _assert_safe_deserialization_posture()
        binding_instance_id = str(binding_instance_id or "").strip()
        if not binding_instance_id:
            raise HaystackQualificationError("binding_instance_id is required")
        self.binding_instance_id = binding_instance_id
        self.document_store = document_store or InMemoryDocumentStore()
        self.retriever = InMemoryBM25Retriever(self.document_store)

    @property
    def provider_version(self) -> str:
        return package_version("haystack-ai")

    def _projection_filter(self) -> dict[str, object]:
        return {
            "field": "meta.pantheon_binding_instance_id",
            "operator": "==",
            "value": self.binding_instance_id,
        }

    def reconcile(
        self,
        resolution: RetrievalScopeResolution,
        materials: Iterable[BoundedSourceMaterial],
    ) -> None:
        """Replace this binding instance's provider projection with current inputs.

        Currentness is not decided here. The caller supplies a fresh Pantheon
        ``RetrievalScopeResolution``. Any previously projected row for this
        binding instance is removed before the current exact set is written.
        """

        _assert_safe_deserialization_posture()
        allowed = {_identity_key(source): source for source in resolution.sources}
        prepared: list[Document] = []
        seen: set[str] = set()

        for material in materials:
            key = _identity_key(material.source)
            expected = allowed.get(key)
            if expected is None or material.source != expected:
                raise HaystackBoundaryViolation(
                    "projection material is outside the Pantheon-resolved retrieval perimeter"
                )
            if key in seen:
                raise HaystackQualificationError("duplicate exact source material")
            seen.add(key)
            if not isinstance(material.content, str):
                raise HaystackQualificationError("projected content must be text")

            source = material.source
            prepared.append(
                Document(
                    id=_document_id(self.binding_instance_id, source),
                    content=material.content,
                    meta={
                        "pantheon_binding_instance_id": self.binding_instance_id,
                        "pantheon_project_id": resolution.project_id,
                        "pantheon_identity_key": key,
                        "document_id": source.document_id,
                        "document_version_id": source.document_version_id,
                        "dossier": source.dossier,
                        "source_ref": source.source_ref,
                        "source_digest": source.source_digest,
                        "source_version": source.source_version,
                        "purpose": source.purpose,
                        "basis_refs": list(source.basis_refs),
                    },
                )
            )

        previous = self.document_store.filter_documents(filters=self._projection_filter())
        if previous:
            self.document_store.delete_documents([document.id for document in previous])
        if prepared:
            self.document_store.write_documents(prepared, policy=DuplicatePolicy.OVERWRITE)

    def retrieve(
        self,
        resolution: RetrievalScopeResolution,
        *,
        query: str,
        top_k: int = 4,
    ) -> BoundedRetrievalResult:
        """Retrieve candidates through an exact runtime filter and post-validation."""

        _assert_safe_deserialization_posture()
        query = str(query or "").strip()
        if not query:
            raise HaystackQualificationError("query is required")
        if top_k < 1:
            raise HaystackQualificationError("top_k must be positive")

        allowed = {_identity_key(source): source for source in resolution.sources}
        if not allowed:
            return BoundedRetrievalResult(
                provider="haystack",
                provider_version=self.provider_version,
                query=query,
                project_id=resolution.project_id,
                candidates=(),
            )

        filters = {
            "operator": "AND",
            "conditions": [
                self._projection_filter(),
                {
                    "field": "meta.pantheon_identity_key",
                    "operator": "in",
                    "value": list(allowed),
                },
            ],
        }
        provider_documents = self.retriever.run(
            query=query,
            filters=filters,
            top_k=top_k,
        )["documents"]

        candidates: list[BoundedRetrievalCandidate] = []
        for document in provider_documents:
            meta = document.meta or {}
            key = str(meta.get("pantheon_identity_key") or "")
            source = allowed.get(key)
            if source is None:
                raise HaystackBoundaryViolation(
                    "provider returned a source outside the Pantheon-resolved perimeter"
                )

            expected = {
                "pantheon_binding_instance_id": self.binding_instance_id,
                "pantheon_project_id": resolution.project_id,
                "document_id": source.document_id,
                "document_version_id": source.document_version_id,
                "dossier": source.dossier,
                "source_ref": source.source_ref,
                "source_digest": source.source_digest,
                "source_version": source.source_version,
                "purpose": source.purpose,
            }
            if any(meta.get(field) != value for field, value in expected.items()):
                raise HaystackBoundaryViolation(
                    "provider provenance does not match the exact Pantheon source identity"
                )

            candidates.append(
                BoundedRetrievalCandidate(
                    document_id=source.document_id,
                    document_version_id=source.document_version_id,
                    dossier=source.dossier,
                    source_ref=source.source_ref,
                    source_digest=source.source_digest,
                    source_version=source.source_version,
                    purpose=source.purpose,
                    basis_refs=source.basis_refs,
                    content=document.content or "",
                    provider_score=float(document.score) if document.score is not None else None,
                )
            )

        return BoundedRetrievalResult(
            provider="haystack",
            provider_version=self.provider_version,
            query=query,
            project_id=resolution.project_id,
            candidates=tuple(candidates),
        )


AUTHORITY = {
    "qualification_lab_only": True,
    "grants_access": False,
    "decides_currentness": False,
    "owns_source_identity": False,
    "owns_source_persistence": False,
    "admits_evidence": False,
    "approves": False,
    "runtime_agent_surface_exposed": False,
    "unsafe_deserialization_allowed": False,
}
