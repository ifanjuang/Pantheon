"""Unit tests for server-side declared Card scope and explicit context validation."""

from __future__ import annotations

import pytest

from mvp_vertical import (
    agency_data,
    agency_information,
    card_scope,
    knowledge,
    store,
    work_issue_read,
)


class _Connection:
    pass


def test_project_scope_resolves_contacts_card_and_direct_documents(monkeypatch) -> None:
    monkeypatch.setattr(
        agency_data,
        "get_project",
        lambda _conn, project_id: {
            "project_id": project_id,
            "contacts": [
                {"group": "Bureaux d’études", "organization": "BET Exemple"},
                {"group": "Maîtrise d’ouvrage", "name": "Client Exemple"},
            ],
        },
    )
    monkeypatch.setattr(
        store,
        "list_document_cards",
        lambda _conn, project_id: [
            {"document_id": "cctp", "source_ref": f"nas://{project_id}/cctp.pdf"},
        ],
    )
    monkeypatch.setattr(
        agency_information,
        "list_project_information",
        lambda _conn, _project_id: [],
    )
    monkeypatch.setattr(
        work_issue_read,
        "list_issue_projections",
        lambda _conn, _project_id, limit=500: [],
    )

    resolved = card_scope.resolve_declared_descendants(
        _Connection(),
        root_entity={"entity_id": "project:verger", "entity_type": "project"},
    )

    assert resolved["policy"] == "project_declared_children"
    assert resolved["descendants"] == [
        {"entity_id": "project:verger:contacts", "entity_type": "project_contacts"},
        {"entity_id": "document:cctp", "entity_type": "document"},
    ]
    assert resolved["source_refs"] == ["nas://verger/cctp.pdf"]
    assert resolved["counts"] == {
        "contacts": 2,
        "information": 0,
        "documents": 1,
        "work": 0,
    }


def test_contacts_card_scope_is_project_owned_and_root_only(monkeypatch) -> None:
    monkeypatch.setattr(
        agency_data,
        "get_project",
        lambda _conn, project_id: {
            "project_id": project_id,
            "contacts": [{"group": "Autres intervenants", "name": "Contact"}],
        },
    )

    resolved = card_scope.resolve_declared_descendants(
        _Connection(),
        root_entity={
            "entity_id": "project:verger:contacts",
            "entity_type": "project_contacts",
        },
    )
    assert resolved == {
        "policy": "project_contacts_root_only",
        "root_owner_id": "verger",
        "descendants": [],
        "source_refs": [],
        "counts": {"contacts": 1},
    }
    assert card_scope.resolve_case_ref(
        _Connection(),
        root_entity={
            "entity_id": "project:verger:contacts",
            "entity_type": "project_contacts",
        },
    ) == "verger"


def test_document_scope_adds_source_but_no_implicit_relations(monkeypatch) -> None:
    monkeypatch.setattr(
        store,
        "get_document_card_by_id",
        lambda _conn, document_id: {
            "document_id": document_id,
            "source_ref": "nas://verger/cctp.pdf",
        },
    )
    resolved = card_scope.resolve_declared_descendants(
        _Connection(),
        root_entity={"entity_id": "document:cctp", "entity_type": "document"},
    )
    assert resolved["policy"] == "document_source_only"
    assert resolved["descendants"] == []
    assert resolved["source_refs"] == ["nas://verger/cctp.pdf"]


def test_known_cockpit_space_stays_root_only() -> None:
    resolved = card_scope.resolve_declared_descendants(
        _Connection(),
        root_entity={"entity_id": "space:outils", "entity_type": "cockpit_space"},
    )
    assert resolved == {
        "policy": "root_only",
        "root_owner_id": "space:outils",
        "descendants": [],
        "source_refs": [],
        "counts": {},
    }


def test_unknown_cockpit_space_is_refused() -> None:
    with pytest.raises(card_scope.CardScopeError, match="unknown Cockpit space"):
        card_scope.resolve_declared_descendants(
            _Connection(),
            root_entity={"entity_id": "space:forged", "entity_type": "cockpit_space"},
        )


def test_explicit_document_and_knowledge_context_derives_sources_server_side(monkeypatch) -> None:
    monkeypatch.setattr(
        store,
        "get_document_card_by_id",
        lambda _conn, document_id: {
            "document_id": document_id,
            "source_ref": "nas://verger/cctp.pdf",
        },
    )
    monkeypatch.setattr(
        knowledge,
        "get_knowledge_card",
        lambda _conn, knowledge_id: {
            "knowledge_id": knowledge_id,
            "source_chunk_refs": ["chunk.extract.0001", "chunk.extract.0002"],
        },
    )

    resolved = card_scope.resolve_explicit_context(
        _Connection(),
        entity_refs=[
            {"entity_id": "document:cctp", "entity_type": "document"},
            {"entity_id": "knowledge:structure", "entity_type": "knowledge"},
        ],
    )

    assert resolved["entities"] == [
        {"entity_id": "document:cctp", "entity_type": "document"},
        {"entity_id": "knowledge:structure", "entity_type": "knowledge"},
    ]
    assert resolved["source_refs"] == [
        "nas://verger/cctp.pdf",
        "chunk.extract.0001",
        "chunk.extract.0002",
    ]


def test_work_issue_case_resolution_uses_record_not_aggregate_projection(monkeypatch) -> None:
    monkeypatch.setattr(
        work_issue_read,
        "get_issue_record",
        lambda _conn, issue_id: {"issue_id": issue_id, "case_ref": "verger"},
    )
    assert card_scope.resolve_case_ref(
        _Connection(),
        root_entity={"entity_id": "work:123", "entity_type": "work_issue"},
    ) == "verger"


def test_scope_normalizes_shared_entity_ref_before_owner_resolution(monkeypatch) -> None:
    observed: list[str] = []
    monkeypatch.setattr(
        agency_data,
        "get_project",
        lambda _conn, project_id: observed.append(project_id) or {"project_id": project_id},
    )

    case_ref = card_scope.resolve_case_ref(
        _Connection(),
        root_entity={
            "entity_id": "  project:verger  ",
            "entity_type": " project ",
        },
    )

    assert case_ref == "verger"
    assert observed == ["verger"]


def test_explicit_context_deduplicates_by_shared_entity_ref_key(monkeypatch) -> None:
    monkeypatch.setattr(
        store,
        "get_document_card_by_id",
        lambda _conn, document_id: {
            "document_id": document_id,
            "source_ref": "nas://verger/cctp.pdf",
        },
    )

    resolved = card_scope.resolve_explicit_context(
        _Connection(),
        entity_refs=[
            {"entity_id": " document:cctp ", "entity_type": " document "},
            {"entity_id": "document:cctp", "entity_type": "document"},
        ],
    )

    assert resolved["entities"] == [
        {"entity_id": "document:cctp", "entity_type": "document"},
    ]
    assert resolved["source_refs"] == ["nas://verger/cctp.pdf"]


def test_entity_ref_structure_errors_remain_scope_domain_errors() -> None:
    with pytest.raises(
        card_scope.CardScopeError,
        match="root entity requires stable entity_id and entity_type",
    ):
        card_scope.resolve_case_ref(
            _Connection(),
            root_entity={"entity_id": "project:verger"},
        )

    with pytest.raises(card_scope.CardScopeError, match="root entity must be an object"):
        card_scope.resolve_case_ref(
            _Connection(),
            root_entity=None,  # type: ignore[arg-type]
        )
