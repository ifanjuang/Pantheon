"""Concurrency and endpoint-integrity regressions for Category classification."""

from __future__ import annotations

import threading
import time

import psycopg
import pytest
from pydantic import ValidationError

from mvp_vertical import (
    agency_classification,
    agency_data,
    project_documents,
    store,
    work_issues,
)
from mvp_vertical.agency_classification_api import CategoryUpdateBody


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
        title=category_id,
        parent_category_id=parent_category_id,
        applies_to=applies_to or ["project"],
        actor="human:test",
    )


def _project(conn, project_id: str = "project-concurrency") -> str:
    conn.execute(
        """
        INSERT INTO agency_projects (
            project_id, code, display_name, created_by, updated_by
        ) VALUES (%s, %s, %s, 'human:test', 'human:test')
        """,
        (project_id, project_id.upper(), project_id),
    )
    conn.commit()
    return project_id


def _information(conn, project_id: str, information_id: str = "information-concurrency") -> str:
    conn.execute(
        """
        INSERT INTO agency_information_cards (
            information_id, series_id, project_id, title, category,
            source_type, source_note, index_label, status
        ) VALUES (%s, %s, %s, 'Note', 'legacy', 'draft', 'Source', 'A01', 'draft')
        """,
        (information_id, f"series-{information_id}", project_id),
    )
    conn.commit()
    return information_id


def _document(conn, project_id: str, document_id: str = "document-concurrency") -> str:
    conn.execute(
        """
        INSERT INTO doc_documents (
            document_id, parent_project_id, document_type, title, created_by
        ) VALUES (%s, %s, 'regulation', 'Document', 'human:test')
        """,
        (document_id, project_id),
    )
    conn.commit()
    return document_id


def _knowledge(conn, project_id: str, knowledge_id: str = "knowledge-concurrency") -> str:
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
        ) VALUES (%s, %s, 1, %s, %s, 'Knowledge', 'reglementations',
                  '# Knowledge', 'markdown-digest', '[]'::jsonb,
                  'reviewed', 1, 'human:test')
        """,
        (knowledge_id, source_id, f"digest-{source_id}", extraction_id),
    )
    conn.commit()
    return knowledge_id


def _work_issue(conn, issue_id: str = "work-concurrency") -> str:
    conn.execute(
        """
        INSERT INTO work_issues (
            issue_id, case_ref, title, description, origin, issue_type,
            priority, requested_effect, status, created_by
        ) VALUES (%s, 'case-test', 'Work', 'Work', 'human', 'verification',
                  'normal', 'read_only', 'open', 'human:test')
        """,
        (issue_id,),
    )
    conn.commit()
    return issue_id


def _new_connection() -> psycopg.Connection:
    connection = psycopg.connect(store.dsn_from_env())
    connection.execute("SET lock_timeout = '5s'")
    connection.execute("SET statement_timeout = '5s'")
    connection.commit()
    return connection


def _waits_on_lock(observer: psycopg.Connection, backend_pid: int, *, timeout: float = 2.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        row = observer.execute(
            "SELECT wait_event_type FROM pg_stat_activity WHERE pid = %s",
            (backend_pid,),
        ).fetchone()
        observer.commit()
        if row and row[0] == "Lock":
            return True
        time.sleep(0.02)
    return False


def test_opposite_parent_moves_serialize_before_cycle_validation(conn) -> None:
    _category(conn, "category-a")
    _category(conn, "category-b")
    first = _new_connection()
    second = _new_connection()
    error: list[BaseException] = []
    started = threading.Event()

    try:
        first.execute(
            """
            UPDATE agency_categories
               SET parent_category_id = 'category-b',
                   updated_by = 'human:first',
                   updated_at = clock_timestamp(),
                   revision = revision + 1
             WHERE category_id = 'category-a'
            """
        )

        def move_other_direction() -> None:
            started.set()
            try:
                second.execute(
                    """
                    UPDATE agency_categories
                       SET parent_category_id = 'category-a',
                           updated_by = 'human:second',
                           updated_at = clock_timestamp(),
                           revision = revision + 1
                     WHERE category_id = 'category-b'
                    """
                )
                second.commit()
            except BaseException as exc:  # captured for assertion in the test thread
                error.append(exc)
                second.rollback()

        worker = threading.Thread(target=move_other_direction)
        worker.start()
        assert started.wait(timeout=1.0)
        assert _waits_on_lock(conn, second.info.backend_pid), (
            "the second hierarchy mutation must wait for the transaction-level hierarchy lock"
        )
        first.commit()
        worker.join(timeout=5.0)
        assert not worker.is_alive()
        assert len(error) == 1
        assert isinstance(error[0], psycopg.errors.RaiseException)
        assert "cycle is forbidden" in str(error[0])

        rows = conn.execute(
            "SELECT category_id, parent_category_id FROM agency_categories ORDER BY category_id"
        ).fetchall()
        conn.commit()
        assert rows == [("category-a", "category-b"), ("category-b", None)]
    finally:
        first.rollback()
        second.rollback()
        first.close()
        second.close()


def test_parent_relation_serializes_with_parent_archive(conn) -> None:
    _category(conn, "category-parent")
    _category(conn, "category-child")
    first = _new_connection()
    second = _new_connection()
    error: list[BaseException] = []
    started = threading.Event()

    try:
        first.execute(
            """
            UPDATE agency_categories
               SET parent_category_id = 'category-parent',
                   updated_by = 'human:first',
                   updated_at = clock_timestamp(),
                   revision = revision + 1
             WHERE category_id = 'category-child'
            """
        )

        def archive_parent() -> None:
            started.set()
            try:
                second.execute(
                    """
                    UPDATE agency_categories
                       SET archived_at = clock_timestamp(),
                           updated_by = 'human:second',
                           updated_at = clock_timestamp(),
                           revision = revision + 1
                     WHERE category_id = 'category-parent'
                    """
                )
                second.commit()
            except BaseException as exc:  # captured for assertion in the test thread
                error.append(exc)
                second.rollback()

        worker = threading.Thread(target=archive_parent)
        worker.start()
        assert started.wait(timeout=1.0)
        assert _waits_on_lock(conn, second.info.backend_pid), (
            "parent archive must wait while a child relation holds the parent row"
        )
        first.commit()
        worker.join(timeout=5.0)
        assert not worker.is_alive()
        assert len(error) == 1
        assert isinstance(error[0], psycopg.errors.RaiseException)
        assert "active child Categories cannot be archived" in str(error[0])

        rows = conn.execute(
            """
            SELECT category_id, parent_category_id, archived_at
              FROM agency_categories
             ORDER BY category_id
            """
        ).fetchall()
        conn.commit()
        assert rows == [
            ("category-child", "category-parent", None),
            ("category-parent", None, None),
        ]
    finally:
        first.rollback()
        second.rollback()
        first.close()
        second.close()


def test_assignment_admission_serializes_with_category_archive(conn) -> None:
    project_id = _project(conn)
    _category(conn, "category-locked", applies_to=["project"])
    first = _new_connection()
    second = _new_connection()
    error: list[BaseException] = []
    started = threading.Event()

    try:
        first.execute(
            """
            INSERT INTO agency_category_assignments (
                assignment_id, category_id, entity_type, entity_id, assigned_by
            ) VALUES (
                'assignment-concurrent', 'category-locked', 'project', %s, 'human:first'
            )
            """,
            (project_id,),
        )

        def archive_category() -> None:
            started.set()
            try:
                second.execute(
                    """
                    UPDATE agency_categories
                       SET archived_at = clock_timestamp(),
                           updated_by = 'human:second',
                           updated_at = clock_timestamp(),
                           revision = revision + 1
                     WHERE category_id = 'category-locked'
                    """
                )
                second.commit()
            except BaseException as exc:  # captured for assertion in the test thread
                error.append(exc)
                second.rollback()

        worker = threading.Thread(target=archive_category)
        worker.start()
        assert started.wait(timeout=1.0)
        assert _waits_on_lock(conn, second.info.backend_pid), (
            "Category archive must wait while assignment admission holds the Category row"
        )
        first.commit()
        worker.join(timeout=5.0)
        assert not worker.is_alive()
        assert len(error) == 1
        assert isinstance(error[0], psycopg.errors.RaiseException)
        assert "active assignments cannot be archived" in str(error[0])

        category = conn.execute(
            "SELECT archived_at FROM agency_categories WHERE category_id = 'category-locked'"
        ).fetchone()
        assignment_count = conn.execute(
            """
            SELECT count(*) FROM agency_category_assignments
             WHERE category_id = 'category-locked' AND retired_at IS NULL
            """
        ).fetchone()[0]
        conn.commit()
        assert category == (None,)
        assert assignment_count == 1
    finally:
        first.rollback()
        second.rollback()
        first.close()
        second.close()


def test_assignment_admission_serializes_with_owner_delete(conn) -> None:
    project_id = _project(conn, "project-delete-race")
    _category(conn, "category-delete-race", applies_to=["project"])
    first = _new_connection()
    second = _new_connection()
    error: list[BaseException] = []
    started = threading.Event()

    try:
        first.execute(
            """
            INSERT INTO agency_category_assignments (
                assignment_id, category_id, entity_type, entity_id, assigned_by
            ) VALUES (
                'assignment-delete-race', 'category-delete-race', 'project', %s, 'human:first'
            )
            """,
            (project_id,),
        )

        def delete_owner() -> None:
            started.set()
            try:
                second.execute(
                    "DELETE FROM agency_projects WHERE project_id = %s",
                    (project_id,),
                )
                second.commit()
            except BaseException as exc:  # captured for assertion in the test thread
                error.append(exc)
                second.rollback()

        worker = threading.Thread(target=delete_owner)
        worker.start()
        assert started.wait(timeout=1.0)
        assert _waits_on_lock(conn, second.info.backend_pid), (
            "owner deletion must wait while assignment admission holds the owner identity"
        )
        first.commit()
        worker.join(timeout=5.0)
        assert not worker.is_alive()
        assert len(error) == 1
        assert isinstance(error[0], psycopg.errors.RaiseException)
        assert "active CategoryAssignment must be retired before deleting" in str(error[0])

        owner_count = conn.execute(
            "SELECT count(*) FROM agency_projects WHERE project_id = %s",
            (project_id,),
        ).fetchone()[0]
        assignment_count = conn.execute(
            """
            SELECT count(*) FROM agency_category_assignments
             WHERE entity_type = 'project' AND entity_id = %s AND retired_at IS NULL
            """,
            (project_id,),
        ).fetchone()[0]
        conn.commit()
        assert owner_count == 1
        assert assignment_count == 1
    finally:
        first.rollback()
        second.rollback()
        first.close()
        second.close()


def test_active_assignments_protect_each_supported_owner_identity(conn) -> None:
    project_id = _project(conn, "project-owner-guard")
    information_id = _information(conn, project_id, "information-owner-guard")
    document_id = _document(conn, project_id, "document-owner-guard")
    knowledge_id = _knowledge(conn, project_id, "knowledge-owner-guard")
    issue_id = _work_issue(conn, "work-owner-guard")
    endpoints = [
        ("project", "agency_projects", "project_id", project_id),
        ("information", "agency_information_cards", "information_id", information_id),
        ("document", "doc_documents", "document_id", document_id),
        ("knowledge", "knowledge_items", "knowledge_id", knowledge_id),
        ("work_issue", "work_issues", "issue_id", issue_id),
    ]
    _category(conn, "category-owner-guard", applies_to=[item[0] for item in endpoints])

    assignment_ids: dict[str, str] = {}
    for entity_type, _table, _column, entity_id in endpoints:
        assignment_id = f"assignment-{entity_type}"
        assignment_ids[entity_type] = assignment_id
        agency_classification.assign_category(
            conn,
            assignment_id=assignment_id,
            category_id="category-owner-guard",
            entity_type=entity_type,
            entity_id=entity_id,
            actor="human:test",
        )

    for entity_type, table, column, entity_id in endpoints:
        with pytest.raises(
            psycopg.errors.RaiseException,
            match="active CategoryAssignment must be retired before deleting",
        ):
            with conn.transaction():
                conn.execute(f"DELETE FROM {table} WHERE {column} = %s", (entity_id,))

    agency_classification.retire_category_assignment(
        conn,
        assignment_id=assignment_ids["work_issue"],
        actor="human:test",
        expected_revision=1,
    )
    with conn.transaction():
        deleted = conn.execute(
            "DELETE FROM work_issues WHERE issue_id = %s RETURNING issue_id",
            (issue_id,),
        ).fetchone()
    assert deleted == (issue_id,)


def test_category_update_model_rejects_explicit_null_sort_order() -> None:
    with pytest.raises(ValidationError, match="sort_order cannot be null"):
        CategoryUpdateBody(expected_revision=1, sort_order=None)

    body = CategoryUpdateBody(expected_revision=1)
    assert body.model_dump(exclude_unset=True) == {"expected_revision": 1}
