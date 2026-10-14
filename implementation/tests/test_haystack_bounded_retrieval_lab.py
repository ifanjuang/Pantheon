from __future__ import annotations

from importlib.metadata import version as package_version
import importlib.util
import os
from pathlib import Path
import sys

import pytest

pytest.importorskip("haystack")

from haystack import Document
from haystack.document_stores.in_memory import InMemoryDocumentStore

from mvp_vertical.retrieval_scope import ResolvedRetrievalSource, RetrievalScopeResolution


LAB = Path(__file__).resolve().parents[1] / "labs" / "haystack_retrieval" / "adapter.py"
SPEC = importlib.util.spec_from_file_location("pantheon_haystack_908_adapter", LAB)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

BoundedSourceMaterial = MODULE.BoundedSourceMaterial
HaystackBoundedRetrievalAdapter = MODULE.HaystackBoundedRetrievalAdapter
HaystackBoundaryViolation = MODULE.HaystackBoundaryViolation
HaystackQualificationError = MODULE.HaystackQualificationError


def _source(
    *,
    source_ref: str = "sources/cctp.pdf",
    source_digest: str = "sha256:current",
    source_version: int = 2,
    document_version_id: str = "pdv-current",
) -> ResolvedRetrievalSource:
    return ResolvedRetrievalSource(
        document_id="project-document-cctp",
        purpose="current_contractual",
        document_version_id=document_version_id,
        dossier="dossier-a",
        source_ref=source_ref,
        source_digest=source_digest,
        source_version=source_version,
        basis_refs=("event:approved",),
    )


def _resolution(*sources: ResolvedRetrievalSource) -> RetrievalScopeResolution:
    return RetrievalScopeResolution(
        project_id="project-a",
        principal_ref="human:test",
        sources=tuple(sources),
    )


def _identity_key(source: ResolvedRetrievalSource) -> str:
    return MODULE._identity_key(source)


def test_exact_provenance_survives_projection_and_runtime_contract_is_provider_neutral() -> None:
    source = _source()
    adapter = HaystackBoundedRetrievalAdapter(binding_instance_id="lab-908-project-a")
    adapter.reconcile(
        _resolution(source),
        [BoundedSourceMaterial(source=source, content="Le lot structure impose un acier S355 pour la poutre principale.")],
    )

    result = adapter.retrieve(_resolution(source), query="acier poutre", top_k=3)

    assert result.provider == "haystack"
    assert result.provider_version == package_version("haystack-ai")
    assert result.project_id == "project-a"
    assert result.evidence_admitted is False
    assert result.authorized_effect is False
    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.document_id == source.document_id
    assert candidate.document_version_id == source.document_version_id
    assert candidate.dossier == source.dossier
    assert candidate.source_ref == source.source_ref
    assert candidate.source_digest == source.source_digest
    assert candidate.source_version == source.source_version
    assert candidate.purpose == source.purpose
    assert candidate.basis_refs == source.basis_refs
    assert type(candidate).__name__ == "BoundedRetrievalCandidate"
    assert not isinstance(candidate, Document)
    assert not hasattr(candidate, "meta")
    assert not hasattr(candidate, "embedding")


def test_provider_store_can_contain_out_of_scope_document_without_widening_results() -> None:
    source = _source()
    store = InMemoryDocumentStore()
    adapter = HaystackBoundedRetrievalAdapter(
        binding_instance_id="lab-908-project-a",
        document_store=store,
    )
    adapter.reconcile(
        _resolution(source),
        [BoundedSourceMaterial(source=source, content="Structure autorisée avec poutre acier S355.")],
    )

    store.write_documents(
        [
            Document(
                id="poisoned-out-of-scope",
                content="SECRET poutre acier interdite hors périmètre",
                meta={
                    "pantheon_binding_instance_id": "lab-908-project-a",
                    "pantheon_project_id": "project-a",
                    "pantheon_identity_key": '["dossier-a","sources/secret.pdf","sha256:secret",1]',
                    "document_id": "project-document-secret",
                    "document_version_id": "pdv-secret",
                    "dossier": "dossier-a",
                    "source_ref": "sources/secret.pdf",
                    "source_digest": "sha256:secret",
                    "source_version": 1,
                    "purpose": "current_contractual",
                },
            )
        ]
    )

    result = adapter.retrieve(_resolution(source), query="poutre acier", top_k=10)

    assert [candidate.source_ref for candidate in result.candidates] == [source.source_ref]
    assert all("SECRET" not in candidate.content for candidate in result.candidates)


def test_post_validation_fails_closed_if_provider_ignores_runtime_filter(monkeypatch) -> None:
    source = _source()
    adapter = HaystackBoundedRetrievalAdapter(binding_instance_id="lab-908-project-a")
    adapter.reconcile(
        _resolution(source),
        [BoundedSourceMaterial(source=source, content="Source autorisée")],
    )
    poisoned = Document(
        id="provider-bypass",
        content="provider returned an undeclared source",
        meta={
            "pantheon_binding_instance_id": "lab-908-project-a",
            "pantheon_project_id": "project-a",
            "pantheon_identity_key": '["dossier-a","sources/secret.pdf","sha256:secret",1]',
        },
    )

    monkeypatch.setattr(adapter.retriever, "run", lambda **kwargs: {"documents": [poisoned]})

    with pytest.raises(HaystackBoundaryViolation):
        adapter.retrieve(_resolution(source), query="anything")


def test_revision_replacement_removes_stale_projection_and_accepts_only_current_digest() -> None:
    old = _source(
        source_digest="sha256:old",
        source_version=1,
        document_version_id="pdv-old",
    )
    current = _source(
        source_digest="sha256:new",
        source_version=2,
        document_version_id="pdv-new",
    )
    store = InMemoryDocumentStore()
    adapter = HaystackBoundedRetrievalAdapter(
        binding_instance_id="lab-908-project-a",
        document_store=store,
    )

    adapter.reconcile(
        _resolution(old),
        [BoundedSourceMaterial(source=old, content="ancienne prescription garde-corps 90 cm")],
    )
    adapter.reconcile(
        _resolution(current),
        [BoundedSourceMaterial(source=current, content="prescription courante garde-corps 110 cm")],
    )

    projected = store.filter_documents(filters=adapter._projection_filter())
    assert len(projected) == 1
    assert projected[0].meta["source_digest"] == "sha256:new"
    assert projected[0].meta["source_version"] == 2

    result = adapter.retrieve(_resolution(current), query="garde-corps", top_k=10)
    assert len(result.candidates) == 1
    assert result.candidates[0].source_digest == "sha256:new"
    assert "110 cm" in result.candidates[0].content
    assert "90 cm" not in result.candidates[0].content


def test_delete_or_revoke_reconciles_to_empty_and_cannot_return_stale_context() -> None:
    source = _source()
    store = InMemoryDocumentStore()
    adapter = HaystackBoundedRetrievalAdapter(
        binding_instance_id="lab-908-project-a",
        document_store=store,
    )
    adapter.reconcile(
        _resolution(source),
        [BoundedSourceMaterial(source=source, content="document ensuite révoqué")],
    )

    adapter.reconcile(_resolution(), [])

    assert store.filter_documents(filters=adapter._projection_filter()) == []
    result = adapter.retrieve(_resolution(), query="révoqué", top_k=10)
    assert result.candidates == ()


def test_projection_rejects_material_not_present_in_pantheon_resolution() -> None:
    allowed = _source()
    undeclared = _source(
        source_ref="sources/undeclared.pdf",
        source_digest="sha256:undeclared",
        source_version=1,
        document_version_id="pdv-undeclared",
    )
    adapter = HaystackBoundedRetrievalAdapter(binding_instance_id="lab-908-project-a")

    with pytest.raises(HaystackBoundaryViolation):
        adapter.reconcile(
            _resolution(allowed),
            [BoundedSourceMaterial(source=undeclared, content="must not be projected")],
        )


def test_unsafe_deserialization_posture_is_refused(monkeypatch) -> None:
    monkeypatch.setenv("HAYSTACK_UNSAFE_DESERIALIZATION", "true")

    with pytest.raises(HaystackQualificationError, match="must remain disabled"):
        HaystackBoundedRetrievalAdapter(binding_instance_id="lab-908-project-a")


def test_authority_manifest_keeps_haystack_outside_governed_owners() -> None:
    authority = MODULE.AUTHORITY
    assert authority == {
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
    assert os.environ.get("HAYSTACK_UNSAFE_DESERIALIZATION", "").lower() not in {"1", "true"}
