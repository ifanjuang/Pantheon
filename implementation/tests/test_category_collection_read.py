"""Acceptance tests for read-only Category Card collections."""

from __future__ import annotations

import pytest

from mvp_vertical import (
    agency_classification,
    agency_data,
    category_collection_read,
    cockpit_composed,
    information_projection,
    project_documents,
    store,
    work_issues,
)


@pytest.fixture
def conn():
    try:
        connection = store.connect()
    except Exception as exc:  # pragma: no cover - local unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(work_issues.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(agency_data.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(project_documents.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(information_projection.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(agency_classification.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(
        """
        TRUNCATE agency_category_assignments, agency_categories,
                 agency_information_projection_events,
                 agency_information_document_links,
                 agency_information_projection_metadata,
                 knowledge_items, extraction_runs, document_versions, source_documents,
                 doc_document_events, doc_document_versions, doc_documents,
                 issue_events, hermes_runs, issue_comments, work_card_metadata, work_issues,
                 agency_information_cards, agency_people, agency_organizations, agency_projects
        RESTART IDENTITY CASCADE
        """
    )
    connection.commit()
    yield connection
    connection.close()


def _project(conn, project_id: str = "project-category-read") -> str:
    conn.execute(
        """
        INSERT INTO agency_projects (
            project_id, code, display_name, phase, location, created_by, updated_by
        ) VALUES (%s, %s, %s, 'PRO', 'Rouen', 'human:test', 'human:test')
        """,
        (project_id, project_id.upper(), "Projet Category Read"),
    )
    conn.commit()
    return project_id


def _information(conn, project_id: str, information_id: str = "information-category-read") -> str:
    conn.execute(
        """
        INSERT INTO agency_information_cards (
            information_id, series_id, project_id, title, category,
            source_type, source_note, index_label, status
        ) VALUES (%s, %s, %s, 'Information', 'legacy', 'draft',
                  'Source', 'A01', 'draft')
        """,
        (information_id, f"series-{information_id}", project_id),
    )
    conn.commit()
    return information_id


def _document(conn, project_id: str, document_id: str = "document-category-read") -> str:
    conn.execute(
        """
        INSERT INTO doc_documents (
            document_id, parent_project_id, document_type, title, created_by
        ) VALUES (%s, %s, 'regulation', 'PLUi Métropole', 'human:test')
        """,
        (document_id, project_id),
    )
    conn.commit()
    return document_id


def _knowledge(conn, project_id: str, knowledge_id: str = "knowledge-category-read") -> str:
    source_id = f"source-{knowledge_id}"
    extraction_id = f"extraction-{knowledge_id}"
    conn.execute(
        """
        INSERT INTO source_documents (
            document_id, dossier, parent_project_id, source_ref, source_digest,
            media_type, byte_size, analysis_status
        ) VALUES (%s, %s, %s, %s, %s, 'text/plain', 20, 'extracted')
        """,
        (source_id, project_id, project_id, f"nas://{source_id}", f"digest-{source_id}"),
    )
    conn.execute(
        """
        INSERT INTO extraction_runs (
            extraction_id, document_id, contract_id, contract_digest, source_digest,
            converter, converter_version, config_digest, status
        ) VALUES (%s, %s, 'contract-test', 'contract-digest', %s,
                  'fixture', '1', 'config-digest', 'complete')
        """,
        (extraction_id, source_id, f"digest-{source_id}"),
    )
    conn.execute(
        """
        INSERT INTO knowledge_items (
            knowledge_id, document_id, source_version, source_digest, extraction_id,
            title, family, markdown, markdown_digest, source_chunk_refs,
            review_status, version, created_by
        ) VALUES (%s, %s, 1, %s, %s, 'Règles PLUi', 'reglementations',
                  '# Règles', 'markdown-digest', '[]'::jsonb,
                  'reviewed', 1, 'human:test')
        """,
        (knowledge_id, source_id, f"digest-{source_id}", extraction_id),
    )
    conn.commit()
    return knowledge_id


def _work_issue(conn, issue_id: str = "work-category-read") -> str:
    conn.execute(
        """
        INSERT INTO work_issues (
            issue_id, case_ref, title, description, origin, issue_type,
            priority, requested_effect, status, created_by
        ) VALUES (%s, 'case-category-read', 'Vérifier', 'Vérification',
                  'human', 'verification', 'normal', 'read_only', 'open', 'human:test')
        """,
        (issue_id,),
    )
    conn.commit()
    return issue_id


def _category(
    conn,
    category_id: str,
    *,
    parent_category_id: str | None = None,
    applies_to: list[str] | None = None,
) -> None:
    agency_classification.create_category(
        conn,
        category_id=category_id,
        title=category_id.replace("-", " ").title(),
        parent_category_id=parent_category_id,
        applies_to=applies_to or ["document"],
        actor="human:test",
    )


def test_category_collection_returns_only_homogeneous_cards_with_owner_identity(conn) -> None:
    project_id = _project(conn)
    information_id = _information(conn, project_id)
    document_id = _document(conn, project_id)
    knowledge_id = _knowledge(conn, project_id)
    issue_id = _work_issue(conn)
    endpoints = {
        "project": project_id,
        "information": information_id,
        "document": document_id,
        "knowledge": knowledge_id,
        "work_issue": issue_id,
    }

    _category(conn, "reglementations", applies_to=list(endpoints))
    _category(
        conn,
        "urbanisme",
        parent_category_id="reglementations",
        applies_to=["document", "knowledge"],
    )
    for entity_type, entity_id in endpoints.items():
        agency_classification.assign_category(
            conn,
            assignment_id=f"assignment-{entity_type}",
            category_id="reglementations",
            entity_type=entity_type,
            entity_id=entity_id,
            actor="human:test",
        )

    projection = category_collection_read.get_category_card_collection(
        conn,
        "reglementations",
    )

    assert projection["cards_are_projections"] is True
    assert projection["classification_is_not_authorization"] is True
    assert projection["authorization_inferred"] is False
    collection = projection["collection"]
    assert collection["collection_id"] == "children:category:reglementations"
    assert collection["parent_entity_id"] == "category:reglementations"
    assert collection["state"] == "loaded"
    assert collection["can_add"] is False
    assert "members" not in collection
    assert "child_categories" not in collection

    items = collection["items"]
    child = items[0]
    assert child["entity_id"] == "category:urbanisme"
    assert child["entity_type"] == "category"
    assert child["role"] == "container"
    assert child["child_collection"] == {
        "state": "available",
        "collection_id": "children:category:urbanisme",
        "load_action": {
            "kind": "collection_read",
            "href": "/cockpit/category-collections/urbanisme",
        },
        "can_add": False,
        "create_action": None,
    }

    members = {
        item["source_entity_ref"]["entity_type"]: item
        for item in items[1:]
    }
    assert set(members) == set(endpoints)
    assert members["project"]["entity_id"] == f"project:{project_id}"
    assert members["information"]["entity_id"] == f"information:{information_id}"
    assert members["document"]["entity_id"] == f"document:{document_id}"
    assert members["knowledge"]["entity_id"] == f"knowledge:{knowledge_id}"
    assert members["work_issue"]["entity_id"] == f"work:{issue_id}"

    for entity_type, entity_id in endpoints.items():
        card = members[entity_type]
        assert card["source_entity_ref"] == {
            "entity_type": entity_type,
            "entity_id": entity_id,
        }
        assert card["collection_membership"]["kind"] == "category_assignment"
        assert card["collection_membership"]["assignment"]["category_id"] == "reglementations"
        assert card["available_actions"] == []
        assert "read_model" not in card

    assert members["project"]["child_collection"]["load_action"] == {
        "kind": "project_bundle",
        "context_id": project_id,
    }


def test_recursive_category_cards_keep_the_same_collection_contract_at_arbitrary_depth(conn) -> None:
    _category(conn, "reglementations")
    _category(conn, "urbanisme", parent_category_id="reglementations")
    _category(conn, "plu-plui", parent_category_id="urbanisme")

    root = category_collection_read.get_category_card_collection(conn, "reglementations")
    child = root["collection"]["items"][0]
    assert child["entity_id"] == "category:urbanisme"
    assert child["child_collection"]["collection_id"] == "children:category:urbanisme"

    second = category_collection_read.get_category_card_collection(conn, "urbanisme")
    grandchild = second["collection"]["items"][0]
    assert grandchild["entity_id"] == "category:plu-plui"
    assert grandchild["child_collection"]["collection_id"] == "children:category:plu-plui"

    third = category_collection_read.get_category_card_collection(conn, "plu-plui")
    assert third["collection"]["state"] == "empty"
    assert third["collection"]["items"] == []


def test_same_owner_card_identity_appears_in_multiple_categories_without_duplication(conn) -> None:
    project_id = _project(conn, "project-multi-category")
    document_id = _document(conn, project_id, "plui-metropole")
    _category(conn, "urbanisme")
    _category(conn, "referentiels")

    for category_id in ("urbanisme", "referentiels"):
        agency_classification.assign_category(
            conn,
            assignment_id=f"assignment:{category_id}",
            category_id=category_id,
            entity_type="document",
            entity_id=document_id,
            actor="human:test",
        )

    first = category_collection_read.get_category_card_collection(conn, "urbanisme")
    second = category_collection_read.get_category_card_collection(conn, "referentiels")
    first_card = first["collection"]["items"][0]
    second_card = second["collection"]["items"][0]

    assert first_card["entity_id"] == second_card["entity_id"] == "document:plui-metropole"
    assert first_card["source_entity_ref"] == second_card["source_entity_ref"] == {
        "entity_type": "document",
        "entity_id": document_id,
    }
    assert first_card["collection_membership"]["assignment"]["category_id"] == "urbanisme"
    assert second_card["collection_membership"]["assignment"]["category_id"] == "referentiels"
    assert conn.execute(
        "SELECT count(*) FROM doc_documents WHERE document_id = %s",
        (document_id,),
    ).fetchone()[0] == 1


def test_empty_category_projects_an_explicit_empty_card_collection(conn) -> None:
    _category(conn, "empty-category")
    projection = category_collection_read.get_category_card_collection(
        conn,
        "empty-category",
    )
    assert projection["collection"]["state"] == "empty"
    assert projection["collection"]["items"] == []
    assert projection["collection"]["can_add"] is False


def test_category_card_collection_route_is_mounted_on_cockpit_surface() -> None:
    app = cockpit_composed.create_composed_cockpit_app(
        connect_fn=lambda: None,
        initialize_fn=None,
        api_key="read-secret",
        editor_api_key="editor-secret",
        hermes_api_key="hermes-secret",
    )
    methods_by_path: dict[str, set[str]] = {}
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            methods_by_path.setdefault(route.path, set()).update(route.methods or set())

    assert "GET" in methods_by_path[
        "/cockpit/category-collections/{category_id}"
    ]
    assert "/agency/categories/{category_id}/resolved-collection" not in methods_by_path
