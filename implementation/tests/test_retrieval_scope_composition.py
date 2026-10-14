from pathlib import Path

import pytest

from mvp_vertical import human_access, retrieval_scope
from mvp_vertical.contract import TaskContract


def _contract(*sources: str) -> TaskContract:
    return TaskContract(
        raw={
            "task_contract_id": "task-test",
            "scope": {
                "parent_project_id": "project-a",
                "declared_sources": list(sources),
            },
        },
        path=Path("task.yaml"),
        dossier="dossier-a",
        sources=tuple(sources),
        forbidden=(),
    )


def _principal() -> human_access.PrincipalContext:
    return human_access.PrincipalContext(
        principal_ref="human:test",
        issuer="https://issuer.example",
        subject="subject-1",
    )


def _install_happy_owners(
    monkeypatch,
    *,
    source_ref: str = "sources/applicable.pdf",
    dossier: str = "dossier-a",
    source_digest: str = "sha256:applicable-old",
    source_version: int = 2,
) -> list[str]:
    calls: list[str] = []

    def require_access(conn, **kwargs):
        calls.append(f"access:{kwargs['resource_type']}:{kwargs['resource_id']}")

    def get_document(conn, document_id):
        calls.append(f"document:{document_id}")
        return {"document_id": document_id, "parent_project_id": "project-a"}

    def resolve_currentness(conn, *, document_id, purpose):
        calls.append(f"currentness:{document_id}:{purpose}")
        return {
            "document_id": document_id,
            "purpose": purpose,
            "resolution_status": "resolved",
            "document_version_id": "pdv-1",
            "basis": {"basis_refs": ["event:approved"]},
        }

    def source_identity(conn, *, document_version_id, project_id):
        calls.append(f"source:{document_version_id}:{project_id}")
        return retrieval_scope.PreservedSourceIdentity(
            dossier=dossier,
            source_ref=source_ref,
            source_digest=source_digest,
            source_version=source_version,
        )

    monkeypatch.setattr(retrieval_scope.human_access, "require_access", require_access)
    monkeypatch.setattr(retrieval_scope.project_documents, "get_document", get_document)
    monkeypatch.setattr(
        retrieval_scope.project_document_currentness,
        "resolve_currentness",
        resolve_currentness,
    )
    monkeypatch.setattr(retrieval_scope, "_source_identity_for_revision", source_identity)
    return calls


def test_scope_composes_access_currentness_and_exact_preserved_source_identity(monkeypatch) -> None:
    calls = _install_happy_owners(monkeypatch)

    resolution = retrieval_scope.resolve_accessible_applicable_sources(
        object(),
        _principal(),
        contract=_contract("sources/applicable.pdf", "sources/other.pdf"),
        project_id="project-a",
        requested_documents=[("project-document-1", "current_for_coordination")],
    )

    assert resolution.project_id == "project-a"
    assert resolution.principal_ref == "human:test"
    assert len(resolution.sources) == 1
    source = resolution.sources[0]
    assert source.document_version_id == "pdv-1"
    assert source.dossier == "dossier-a"
    assert source.source_ref == "sources/applicable.pdf"
    assert source.source_digest == "sha256:applicable-old"
    assert source.source_version == 2
    assert source.basis_refs == ("event:approved",)
    assert calls == [
        "access:project:project-a",
        "access:project_document:project-document-1",
        "document:project-document-1",
        "currentness:project-document-1:current_for_coordination",
        "source:pdv-1:project-a",
    ]


def test_document_denial_fails_before_metadata_or_currentness_and_does_not_leak(monkeypatch) -> None:
    touched: list[str] = []

    def require_access(conn, **kwargs):
        if kwargs["resource_type"] == "project_document":
            raise human_access.AccessDenied("secret-project-document exists")

    def forbidden_touch(*args, **kwargs):
        touched.append("called")
        raise AssertionError("metadata/currentness must not be touched after access denial")

    monkeypatch.setattr(retrieval_scope.human_access, "require_access", require_access)
    monkeypatch.setattr(retrieval_scope.project_documents, "get_document", forbidden_touch)
    monkeypatch.setattr(
        retrieval_scope.project_document_currentness,
        "resolve_currentness",
        forbidden_touch,
    )

    with pytest.raises(retrieval_scope.RetrievalScopeDenied) as exc:
        retrieval_scope.resolve_accessible_applicable_sources(
            object(),
            _principal(),
            contract=_contract("sources/secret.pdf"),
            project_id="project-a",
            requested_documents=[("secret-project-document", "current_working")],
        )

    assert touched == []
    assert "secret" not in str(exc.value).lower()


@pytest.mark.parametrize(
    ("status", "expected_error"),
    [
        ("unresolved", retrieval_scope.RetrievalScopeUnresolved),
        ("conflicting", retrieval_scope.RetrievalScopeConflicting),
    ],
)
def test_unresolved_or_conflicting_currentness_never_selects_a_source(
    monkeypatch,
    status,
    expected_error,
) -> None:
    _install_happy_owners(monkeypatch)

    def resolve_currentness(conn, *, document_id, purpose):
        return {
            "document_id": document_id,
            "purpose": purpose,
            "resolution_status": status,
            "document_version_id": None,
            "basis": {},
        }

    source_calls: list[str] = []

    def source_identity(*args, **kwargs):
        source_calls.append("called")
        raise AssertionError("source resolution must not run for unresolved currentness")

    monkeypatch.setattr(
        retrieval_scope.project_document_currentness,
        "resolve_currentness",
        resolve_currentness,
    )
    monkeypatch.setattr(retrieval_scope, "_source_identity_for_revision", source_identity)

    with pytest.raises(expected_error):
        retrieval_scope.resolve_accessible_applicable_sources(
            object(),
            _principal(),
            contract=_contract("sources/applicable.pdf"),
            project_id="project-a",
            requested_documents=[("project-document-1", "current_contractual")],
        )

    assert source_calls == []


def test_resolved_source_cannot_expand_task_contract(monkeypatch) -> None:
    _install_happy_owners(monkeypatch, source_ref="sources/not-declared.pdf")

    with pytest.raises(retrieval_scope.RetrievalScopeUndeclared):
        retrieval_scope.resolve_accessible_applicable_sources(
            object(),
            _principal(),
            contract=_contract("sources/declared.pdf"),
            project_id="project-a",
            requested_documents=[("project-document-1", "current_working")],
        )


def test_same_source_ref_in_another_dossier_is_rejected(monkeypatch) -> None:
    _install_happy_owners(
        monkeypatch,
        dossier="dossier-b",
        source_ref="sources/shared-name.pdf",
    )

    with pytest.raises(retrieval_scope.RetrievalScopeDenied):
        retrieval_scope.resolve_accessible_applicable_sources(
            object(),
            _principal(),
            contract=_contract("sources/shared-name.pdf"),
            project_id="project-a",
            requested_documents=[("project-document-b", "current_working")],
        )


def test_two_revisions_at_same_path_keep_distinct_digests(monkeypatch) -> None:
    _install_happy_owners(
        monkeypatch,
        source_ref="sources/reused-path.pdf",
        source_digest="sha256:older-applicable",
        source_version=1,
    )

    resolution = retrieval_scope.resolve_accessible_applicable_sources(
        object(),
        _principal(),
        contract=_contract("sources/reused-path.pdf"),
        project_id="project-a",
        requested_documents=[("project-document-1", "current_contractual")],
    )

    assert resolution.sources[0].source_ref == "sources/reused-path.pdf"
    assert resolution.sources[0].source_digest == "sha256:older-applicable"
    assert resolution.sources[0].source_version == 1
    assert not hasattr(resolution, "source_refs")


def test_contract_project_mismatch_fails_before_any_access_lookup(monkeypatch) -> None:
    touched: list[str] = []

    def forbidden_touch(*args, **kwargs):
        touched.append("called")
        raise AssertionError("access lookup must not run for a mismatched contract project")

    monkeypatch.setattr(retrieval_scope.human_access, "require_access", forbidden_touch)

    with pytest.raises(retrieval_scope.RetrievalScopeDenied):
        retrieval_scope.resolve_accessible_applicable_sources(
            object(),
            _principal(),
            contract=_contract("sources/a.pdf"),
            project_id="project-b",
            requested_documents=[("project-document-1", "current_working")],
        )

    assert touched == []
