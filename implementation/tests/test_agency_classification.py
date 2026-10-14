"""PostgreSQL acceptance tests for hierarchical Agency Data classification."""

from __future__ import annotations

import uuid

import psycopg
import pytest

from mvp_vertical import (
    agency_classification,
    agency_data,
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
    connection.execute(agency_classification.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(
        """
        TRUNCATE agency_category_assignments, agency_categories,
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


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _project(conn, project_id: str = "project-alpha") -> str:
    conn.execute(
        """
        INSERT INTO agency_projects (
            project_id, code, display_name, created_by, updated_by
        ) VALUES (%s, %s, %s, 'human:ifj', 'human:ifj')
        """,
        (project_id, project_id.upper(), "Projet Alpha"),
    )
    conn.commit()
    return project_id


def _information(conn, project_id: str, information_id: str = "information-alpha") -> str:
    conn.execute(
        """
        INSERT INTO agency_information_cards (
            information_id, series_id, project_id, title, category,
            source_type, source_note, index_label, status
        ) VALUES (%s, %s, %s, 'Note projet', 'legacy-category', 'draft',
                  'Texte source', 'A01', 'draft')
        """,
        (information_id, f"series-{information_id}", project_id),
    )
    conn.commit()
    return information_id


def _professional_document(
    conn,
    project_id: str,
    document_id: str = "document-alpha",
) -> str:
    conn.execute(
        """
        INSERT INTO doc_documents (
            document_id, parent_project_id, document_type, title, created_by
        ) VALUES (%s, %s, 'regulation', 'PLUi Métropole', 'human:ifj')
        """,
        (document_id, project_id),
    )
    conn.commit()
    return document_id


def _work_issue(conn, issue_id: str = "issue-alpha") -> str:
    conn.execute(
        """
        INSERT INTO work_issues (
            issue_id, case_ref, title, description, origin, issue_type,
            priority, requested_effect, status, created_by
        ) VALUES (%s, 'project-alpha', 'Vérifier', 'Vérification documentaire',
                  'human', 'verification', 'normal', 'read_only', 'open', 'human:ifj')
        """,
        (issue_id,),
    )
    conn.commit()
    return issue_id


def _knowledge(conn, project_id: str, knowledge_id: str = "knowledge-alpha") -> str:
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
                  '# Règles', 'markdown-digest', '[]'::jsonb, 'reviewed', 1, 'human:ifj')
        """,
        (knowledge_id, source_id, f"digest-{source_id}", extraction_id),
    )
    conn.commit()
    return knowledge_id


def _category(
    conn,
    category_id: str,
    *,
    parent_category_id: str | None = None,
    applies_to: list[str] | None = None,
    sort_order: int = 0,
) -> dict:
    return agency_classification.create_category(
        conn,
        category_id=category_id,
        title=category_id.replace("-", " ").title(),
        parent_category_id=parent_category_id,
        applies_to=applies_to or ["document"],
        sort_order=sort_order,
        actor="human:ifj",
    )


def test_category_tree_and_collection_read_are_recursive_projection_inputs(conn) -> None:
    root = _category(conn, "reglementations", applies_to=["document", "knowledge"])
    urbanisme = _category(
        conn,
        "urbanisme",
        parent_category_id=root["category_id"],
        applies_to=["document", "knowledge"],
    )
    plu = _category(
        conn,
        "plu-plui",
        parent_category_id=urbanisme["category_id"],
        applies_to=["document", "knowledge"],
    )

    assert [item["category_id"] for item in agency_classification.list_root_categories(conn)] == [
        "reglementations"
    ]
    assert [
        item["category_id"]
        for item in agency_classification.list_child_categories(conn, "reglementations")
    ] == ["urbanisme"]
    collection = agency_classification.get_category_collection(conn, "urbanisme")
    assert [item["category_id"] for item in collection["child_categories"]] == ["plu-plui"]
    assert collection["collection_is_projection_input"] is True
    assert collection["classification_is_not_authorization"] is True
    assert plu["authority"]["is_authorization"] is False


def test_category_cycle_is_refused_without_advancing_revision(conn) -> None:
    _category(conn, "reglementations")
    _category(conn, "urbanisme", parent_category_id="reglementations")
    _category(conn, "plu-plui", parent_category_id="urbanisme")

    with pytest.raises(psycopg.errors.RaiseException, match="cycle is forbidden"):
        agency_classification.update_category(
            conn,
            category_id="reglementations",
            changes={"parent_category_id": "plu-plui"},
            actor="human:ifj",
            expected_revision=1,
        )

    root = agency_classification.get_category(conn, "reglementations")
    assert root["parent_category_id"] is None
    assert root["revision"] == 1


def test_same_document_identity_can_appear_in_multiple_categories(conn) -> None:
    project_id = _project(conn)
    document_id = _professional_document(conn, project_id, "document:plui-metropole")
    _category(conn, "plu-plui", applies_to=["document"])
    _category(conn, "referentiels", applies_to=["document", "knowledge"])

    agency_classification.assign_category(
        conn,
        assignment_id="assignment:plui:urbanisme",
        category_id="plu-plui",
        entity_type="document",
        entity_id=document_id,
        actor="human:ifj",
    )
    agency_classification.assign_category(
        conn,
        assignment_id="assignment:plui:referentiels",
        category_id="referentiels",
        entity_type="document",
        entity_id=document_id,
        actor="human:ifj",
    )

    assignments = agency_classification.list_entity_category_assignments(
        conn,
        entity_type="document",
        entity_id=document_id,
    )
    assert {item["category_id"] for item in assignments} == {"plu-plui", "referentiels"}
    assert {item["entity_id"] for item in assignments} == {document_id}
    assert conn.execute(
        "SELECT count(*) FROM doc_documents WHERE document_id = %s", (document_id,)
    ).fetchone()[0] == 1


def test_supported_owner_endpoints_are_resolved_by_existing_identity(conn) -> None:
    project_id = _project(conn)
    information_id = _information(conn, project_id)
    document_id = _professional_document(conn, project_id)
    knowledge_id = _knowledge(conn, project_id)
    issue_id = _work_issue(conn)
    endpoints = {
        "project": project_id,
        "information": information_id,
        "document": document_id,
        "knowledge": knowledge_id,
        "work_issue": issue_id,
    }
    _category(conn, "transversal", applies_to=list(endpoints))

    for entity_type, entity_id in endpoints.items():
        result = agency_classification.assign_category(
            conn,
            assignment_id=f"assignment-{entity_type}",
            category_id="transversal",
            entity_type=entity_type,
            entity_id=entity_id,
            actor="human:ifj",
        )
        assert result["entity_type"] == entity_type
        assert result["entity_id"] == entity_id
        assert result["authority"]["transfers_ownership"] is False


def test_assignment_refuses_wrong_type_unknown_endpoint_and_direct_hermes_write(conn) -> None:
    project_id = _project(conn)
    document_id = _professional_document(conn, project_id)
    _category(conn, "urbanisme", applies_to=["information"])

    with pytest.raises(psycopg.errors.RaiseException, match="does not apply"):
        agency_classification.assign_category(
            conn,
            assignment_id="assignment-wrong-type",
            category_id="urbanisme",
            entity_type="document",
            entity_id=document_id,
            actor="human:ifj",
        )

    _category(conn, "documents", applies_to=["document"])
    with pytest.raises(psycopg.errors.RaiseException, match="unknown CategoryAssignment endpoint"):
        agency_classification.assign_category(
            conn,
            assignment_id="assignment-missing-document",
            category_id="documents",
            entity_type="document",
            entity_id="document-missing",
            actor="human:ifj",
        )

    with pytest.raises(agency_classification.AgencyClassificationError, match="Hermes"):
        agency_classification.create_category(
            conn,
            category_id="hermes-category",
            title="Hermes Category",
            applies_to=["document"],
            actor="hermes:agent",
            actor_kind="hermes",
        )


def test_active_assignment_is_unique_but_retirement_allows_later_reassignment(conn) -> None:
    project_id = _project(conn)
    document_id = _professional_document(conn, project_id)
    _category(conn, "urbanisme", applies_to=["document"])
    first = agency_classification.assign_category(
        conn,
        assignment_id="assignment-first",
        category_id="urbanisme",
        entity_type="document",
        entity_id=document_id,
        actor="human:ifj",
    )

    with pytest.raises(psycopg.errors.UniqueViolation):
        agency_classification.assign_category(
            conn,
            assignment_id="assignment-duplicate",
            category_id="urbanisme",
            entity_type="document",
            entity_id=document_id,
            actor="human:ifj",
        )

    retired = agency_classification.retire_category_assignment(
        conn,
        assignment_id=first["assignment_id"],
        actor="human:ifj",
        expected_revision=1,
    )
    assert retired["retired_at"] is not None
    assert retired["revision"] == 2

    replacement = agency_classification.assign_category(
        conn,
        assignment_id="assignment-replacement",
        category_id="urbanisme",
        entity_type="document",
        entity_id=document_id,
        actor="human:ifj",
    )
    assert replacement["entity_id"] == document_id


def test_applies_to_cannot_exclude_an_active_assignment(conn) -> None:
    project_id = _project(conn)
    document_id = _professional_document(conn, project_id)
    category = _category(conn, "mixed", applies_to=["document", "information"])
    agency_classification.assign_category(
        conn,
        assignment_id="assignment-document",
        category_id="mixed",
        entity_type="document",
        entity_id=document_id,
        actor="human:ifj",
    )

    with pytest.raises(psycopg.errors.RaiseException, match="cannot exclude"):
        agency_classification.update_category(
            conn,
            category_id="mixed",
            changes={"applies_to": ["information"]},
            actor="human:ifj",
            expected_revision=category["revision"],
        )
    assert agency_classification.get_category(conn, "mixed")["applies_to"] == [
        "document",
        "information",
    ]


def test_archive_requires_no_active_children_or_assignments(conn) -> None:
    project_id = _project(conn)
    document_id = _professional_document(conn, project_id)
    parent = _category(conn, "parent", applies_to=["document"])
    child = _category(conn, "child", parent_category_id="parent", applies_to=["document"])

    with pytest.raises(psycopg.errors.RaiseException, match="active child Categories"):
        agency_classification.archive_category(
            conn,
            category_id="parent",
            actor="human:ifj",
            expected_revision=parent["revision"],
        )

    assignment = agency_classification.assign_category(
        conn,
        assignment_id="assignment-child",
        category_id="child",
        entity_type="document",
        entity_id=document_id,
        actor="human:ifj",
    )
    with pytest.raises(psycopg.errors.RaiseException, match="active assignments"):
        agency_classification.archive_category(
            conn,
            category_id="child",
            actor="human:ifj",
            expected_revision=child["revision"],
        )

    agency_classification.retire_category_assignment(
        conn,
        assignment_id=assignment["assignment_id"],
        actor="human:ifj",
        expected_revision=assignment["revision"],
    )
    archived_child = agency_classification.archive_category(
        conn,
        category_id="child",
        actor="human:ifj",
        expected_revision=child["revision"],
    )
    assert archived_child["archived_at"] is not None
    archived_parent = agency_classification.archive_category(
        conn,
        category_id="parent",
        actor="human:ifj",
        expected_revision=parent["revision"],
    )
    assert archived_parent["archived_at"] is not None


def test_assignment_history_is_retire_only_and_not_entity_relation_storage(conn) -> None:
    migration = agency_classification.MIGRATION.read_text(encoding="utf-8")
    assert "agency_entity_relations" not in migration
    assert "agency_category_assignments" in migration

    project_id = _project(conn)
    document_id = _professional_document(conn, project_id)
    _category(conn, "documents", applies_to=["document"])
    assignment = agency_classification.assign_category(
        conn,
        assignment_id="assignment-history",
        category_id="documents",
        entity_type="document",
        entity_id=document_id,
        actor="human:ifj",
    )

    with pytest.raises(psycopg.errors.RaiseException, match="retire instead of deleting"):
        conn.execute(
            "DELETE FROM agency_category_assignments WHERE assignment_id = %s",
            (assignment["assignment_id"],),
        )
    conn.rollback()


def test_stale_category_and_assignment_updates_are_refused(conn) -> None:
    project_id = _project(conn)
    document_id = _professional_document(conn, project_id)
    category = _category(conn, "documents", applies_to=["document"])
    updated = agency_classification.update_category(
        conn,
        category_id="documents",
        changes={"title": "Documents utiles"},
        actor="human:ifj",
        expected_revision=category["revision"],
    )
    assert updated["revision"] == 2
    with pytest.raises(agency_classification.StaleCategoryWrite):
        agency_classification.update_category(
            conn,
            category_id="documents",
            changes={"title": "Titre obsolète"},
            actor="human:ifj",
            expected_revision=1,
        )

    assignment = agency_classification.assign_category(
        conn,
        assignment_id="assignment-stale",
        category_id="documents",
        entity_type="document",
        entity_id=document_id,
        actor="human:ifj",
    )
    agency_classification.retire_category_assignment(
        conn,
        assignment_id=assignment["assignment_id"],
        actor="human:ifj",
        expected_revision=1,
    )
    with pytest.raises(agency_classification.StaleCategoryAssignmentWrite):
        agency_classification.retire_category_assignment(
            conn,
            assignment_id=assignment["assignment_id"],
            actor="human:ifj",
            expected_revision=1,
        )
