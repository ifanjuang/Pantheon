"""Contract tests for advisory P4 document-identity candidates."""

from __future__ import annotations

import pytest

from mvp_vertical import project_document_inbox, project_documents, source_intake


SOURCE = {
    "source_id": "source-1",
    "project_link_status": "linked",
    "project_id": "project-a",
    "checksum": "a" * 64,
    "raw_source_ref": "upload/new.pdf",
    "origin_external_ref": "portal:new",
}

CAPTURE = {
    "document_id": "source-document-1",
    "version": 1,
    "source_ref": "captured/new.pdf",
    "source_digest": "a" * 64,
    "media_type": "application/pdf",
    "byte_size": 1234,
}


def _candidate(document_id: str, score: float, *, producer: str = "hermes:test") -> dict:
    return {
        "document_id": document_id,
        "score": score,
        "basis": ["semantic similarity over bounded project document metadata"],
        "producer": producer,
        "created_at": "2026-09-04T20:45:00+02:00",
    }


def _document(document_id: str, project_id: str = "project-a") -> dict:
    return {
        "document_id": document_id,
        "parent_project_id": project_id,
        "document_type": "ETUDE",
        "title": f"Document {document_id}",
        "lot_id": None,
        "discipline_code": "THERMIQUE",
    }


def _install_unresolved(monkeypatch: pytest.MonkeyPatch, documents: dict[str, dict]) -> None:
    monkeypatch.setattr(source_intake, "get_source", lambda conn, source_id: dict(SOURCE))
    monkeypatch.setattr(project_document_inbox, "_admitted_binding", lambda conn, source_id: None)
    monkeypatch.setattr(
        project_document_inbox,
        "_technical_candidates",
        lambda conn, source: ("checksum", [dict(CAPTURE)]),
    )
    monkeypatch.setattr(
        project_document_inbox,
        "_professional_digest_matches",
        lambda conn, project_id, digest: [],
    )
    monkeypatch.setattr(
        project_document_inbox,
        "_professional_lineage",
        lambda conn, project_id, source_document_id: [],
    )

    def get_document(conn, document_id: str) -> dict:
        try:
            return dict(documents[document_id])
        except KeyError as exc:
            raise project_documents.ProjectDocumentNotFound(document_id) from exc

    monkeypatch.setattr(project_documents, "get_document", get_document)


def test_semantic_candidates_are_advisory_sorted_and_do_not_confirm_identity(monkeypatch) -> None:
    _install_unresolved(
        monkeypatch,
        {
            "project-document-a": _document("project-document-a"),
            "project-document-b": _document("project-document-b"),
        },
    )

    result = project_document_inbox.reconcile_source(
        object(),
        source_id="source-1",
        semantic_candidates=[
            _candidate("project-document-b", 0.72),
            _candidate("project-document-a", 0.91),
        ],
    )

    assert result["status"] == "document_identity_candidates"
    assert [row["document_id"] for row in result["professional_candidates"]] == [
        "project-document-a",
        "project-document-b",
    ]
    assert result["candidate_basis"] == "semantic_candidate_projection"
    assert result["authority"]["professional_identity_confirmed"] is False
    assert result["authority"]["revision_admitted"] is False
    assert result["authority"]["is_evidence"] is False
    assert "selected_document_id" not in result


def test_equal_scores_have_deterministic_order_but_no_winner(monkeypatch) -> None:
    _install_unresolved(
        monkeypatch,
        {
            "project-document-a": _document("project-document-a"),
            "project-document-b": _document("project-document-b"),
        },
    )

    result = project_document_inbox.reconcile_source(
        object(),
        source_id="source-1",
        semantic_candidates=[
            _candidate("project-document-b", 0.8),
            _candidate("project-document-a", 0.8),
        ],
    )

    assert [row["document_id"] for row in result["professional_candidates"]] == [
        "project-document-a",
        "project-document-b",
    ]
    assert result["authority"]["professional_identity_confirmed"] is False


def test_unknown_duplicate_or_cross_project_candidate_fails_closed(monkeypatch) -> None:
    _install_unresolved(
        monkeypatch,
        {
            "project-document-a": _document("project-document-a"),
            "project-document-other": _document("project-document-other", "project-b"),
        },
    )

    with pytest.raises(project_document_inbox.ProjectDocumentInboxError, match="unknown semantic candidate"):
        project_document_inbox.reconcile_source(
            object(),
            source_id="source-1",
            semantic_candidates=[_candidate("missing", 0.8)],
        )

    with pytest.raises(project_document_inbox.ProjectDocumentInboxError, match="another Project"):
        project_document_inbox.reconcile_source(
            object(),
            source_id="source-1",
            semantic_candidates=[_candidate("project-document-other", 0.8)],
        )

    with pytest.raises(project_document_inbox.ProjectDocumentInboxError, match="non-empty and unique"):
        project_document_inbox.reconcile_source(
            object(),
            source_id="source-1",
            semantic_candidates=[
                _candidate("project-document-a", 0.8),
                _candidate("project-document-a", 0.7),
            ],
        )


def test_malformed_candidate_metadata_fails_closed(monkeypatch) -> None:
    _install_unresolved(
        monkeypatch,
        {"project-document-a": _document("project-document-a")},
    )

    malformed = _candidate("project-document-a", 0.8)
    malformed["basis"] = "not-a-list"
    with pytest.raises(project_document_inbox.ProjectDocumentInboxError, match="basis must be a list"):
        project_document_inbox.reconcile_source(
            object(), source_id="source-1", semantic_candidates=[malformed]
        )

    out_of_range = _candidate("project-document-a", 1.1)
    with pytest.raises(project_document_inbox.ProjectDocumentInboxError, match="between 0 and 1"):
        project_document_inbox.reconcile_source(
            object(), source_id="source-1", semantic_candidates=[out_of_range]
        )


def test_exact_professional_match_precedes_and_ignores_semantic_ranking(monkeypatch) -> None:
    monkeypatch.setattr(source_intake, "get_source", lambda conn, source_id: dict(SOURCE))
    monkeypatch.setattr(project_document_inbox, "_admitted_binding", lambda conn, source_id: None)
    monkeypatch.setattr(
        project_document_inbox,
        "_technical_candidates",
        lambda conn, source: ("checksum", [dict(CAPTURE)]),
    )
    monkeypatch.setattr(
        project_document_inbox,
        "_professional_digest_matches",
        lambda conn, project_id, digest: [
            {
                "version_id": "version-exact",
                "document_id": "project-document-exact",
                "version_seq": 1,
                "revision_label": "A",
                "source_document_id": "source-document-1",
                "source_version": 1,
                "source_digest": "a" * 64,
                "document_type": "ETUDE",
                "title": "Exact",
                "lot_id": None,
                "discipline_code": "THERMIQUE",
            }
        ],
    )

    def semantic_lookup_must_not_run(conn, document_id: str) -> dict:
        raise AssertionError("semantic candidates must not override an exact identity signal")

    monkeypatch.setattr(project_documents, "get_document", semantic_lookup_must_not_run)

    result = project_document_inbox.reconcile_source(
        object(),
        source_id="source-1",
        semantic_candidates=[_candidate("project-document-high-score", 1.0)],
    )

    assert result["status"] == "probable_duplicate_receipt"
    assert result["professional_candidate"]["document_id"] == "project-document-exact"
    assert result["candidate_basis"] == "exact_professional_content_digest"
