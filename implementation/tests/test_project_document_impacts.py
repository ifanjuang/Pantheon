"""PostgreSQL acceptance for A3b explicit old-revision impact candidates."""

from __future__ import annotations

import hashlib
import json
import uuid

import pytest

from mvp_vertical import (
    agency_data,
    information_projection,
    project_document_admission,
    project_document_impacts,
    project_documents,
)


@pytest.fixture
def conn():
    try:
        connection = project_document_admission.connect()
        information_projection.initialize(connection)
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(
        "TRUNCATE agency_information_projection_events, "
        "agency_information_document_links, agency_information_projection_metadata, "
        "agency_information_cards, knowledge_items, doc_document_version_sources, "
        "doc_document_events, doc_document_versions, doc_documents, extraction_units, "
        "structured_compilations, extraction_runs, document_versions, source_documents, "
        "agency_project_events, agency_projects RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _project(conn) -> str:
    project_id = _id("project")
    agency_data.create_project(
        conn,
        project_id=project_id,
        code=f"P-{uuid.uuid4().hex[:10]}",
        display_name="Impact test",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("project-create"),
    )
    conn.commit()
    return project_id


def _logical_document(conn, project_id: str) -> dict:
    document = project_documents.create_document(
        conn,
        document_id=_id("project-document"),
        parent_project_id=project_id,
        document_type="ETUDE",
        title="Étude thermique",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("document-create"),
    )
    conn.commit()
    return document


def _technical_with_structure(
    conn,
    *,
    project_id: str,
    source_ref: str,
    digest: str,
    body: str,
) -> tuple[str, int, str]:
    source_document_id = _id("source-document")
    extraction_id = _id("extraction")
    compilation_id = _id("compilation")
    conn.execute(
        """
        INSERT INTO source_documents (
            document_id, dossier, parent_project_id, source_ref, source_digest,
            media_type, byte_size, analysis_status
        ) VALUES (%s, %s, %s, %s, %s, 'application/pdf', 1234, 'ready')
        """,
        (source_document_id, project_id, project_id, source_ref, digest),
    )
    conn.execute(
        """
        INSERT INTO document_versions (
            document_id, version, source_ref, source_digest, media_type, byte_size
        ) VALUES (%s, 1, %s, %s, 'application/pdf', 1234)
        """,
        (source_document_id, source_ref, digest),
    )
    conn.execute(
        """
        INSERT INTO extraction_runs (
            extraction_id, document_id, contract_id, contract_digest,
            source_digest, converter, converter_version, config_digest,
            status, markdown_content, chunk_count, quality_flags
        ) VALUES (%s, %s, 'contract-impact', %s, %s, 'fixture', '1', %s,
                  'ready', %s, 0, '[]'::jsonb)
        """,
        (extraction_id, source_document_id, "c" * 64, digest, "f" * 64, body),
    )
    conn.execute(
        """
        INSERT INTO structured_compilations (
            compilation_id, extraction_id, compiler, compiler_version,
            config_digest, output_digest, status, quality_flags, diagnostics,
            unit_count, chunk_count, page_count, table_count, anomaly_count
        ) VALUES (%s, %s, 'pantheon_structured_extraction', '2', %s, %s,
                  'ready', '[]'::jsonb, '[]'::jsonb, 1, 0, 1, 0, 0)
        """,
        (compilation_id, extraction_id, "f" * 64, _sha(body)),
    )
    conn.execute(
        """
        INSERT INTO extraction_units (
            unit_id, compilation_id, extraction_id, ordinal, content_type,
            body, text_digest, page_start, page_end, structural_locator,
            section_path, quality_flags
        ) VALUES (%s, %s, %s, 0, 'paragraph', %s, %s, 1, 1,
                  'section:thermal/p:1', '[]'::jsonb, '[]'::jsonb)
        """,
        (_id("unit"), compilation_id, extraction_id, body, _sha(body)),
    )
    conn.commit()
    return source_document_id, 1, extraction_id


def _revisions(conn, *, same_content: bool = False) -> tuple[dict, dict, str]:
    project_id = _project(conn)
    logical = _logical_document(conn, project_id)
    before_doc, before_source_version, before_extraction = _technical_with_structure(
        conn,
        project_id=project_id,
        source_ref="BET/thermal_B.pdf",
        digest="b" * 64,
        body="Uw = 1,4 W/m².K",
    )
    after_doc, after_source_version, _ = _technical_with_structure(
        conn,
        project_id=project_id,
        source_ref="BET/thermal_C.pdf",
        digest="c" * 64,
        body="Uw = 1,4 W/m².K" if same_content else "Uw = 1,3 W/m².K",
    )
    before = project_documents.link_revision(
        conn,
        document_id=logical["document_id"],
        source_document_id=before_doc,
        source_version=before_source_version,
        revision_label="B",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("link-b"),
    )
    after = project_documents.link_revision(
        conn,
        document_id=logical["document_id"],
        source_document_id=after_doc,
        source_version=after_source_version,
        revision_label="C",
        supersedes_version_id=before["version_id"],
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("link-c"),
    )
    conn.commit()
    return before, after, before_extraction


def _information(conn, project_id: str, title: str) -> str:
    information_id = _id("information")
    conn.execute(
        """
        INSERT INTO agency_information_cards (
            information_id, series_id, project_id, title, category, source_type,
            source_ref, index_label, status
        ) VALUES (%s, %s, %s, %s, 'note', 'document', %s, 'A', 'draft')
        """,
        (information_id, _id("series"), project_id, title, f"manual:{information_id}"),
    )
    conn.commit()
    return information_id


def _link_information(
    conn,
    *,
    information_id: str,
    source_document_id: str,
    observed_version: int | None,
    observed_digest: str | None,
) -> None:
    information_projection.add_document_link(
        conn,
        information_id=information_id,
        document_id=source_document_id,
        role="supporting",
        observed_version=observed_version,
        observed_digest=observed_digest,
        expected_revision=0,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("information-link"),
    )
    conn.commit()


def _knowledge(
    conn,
    *,
    source_document_id: str,
    source_version: int,
    source_digest: str,
    extraction_id: str,
) -> str:
    knowledge_id = _id("knowledge")
    markdown = "Méthode issue de la révision B"
    conn.execute(
        """
        INSERT INTO knowledge_items (
            knowledge_id, document_id, source_version, source_digest,
            extraction_id, title, family, markdown, markdown_digest,
            source_chunk_refs, review_status, version, created_by
        ) VALUES (%s, %s, %s, %s, %s, 'Thermique', 'techniques', %s, %s,
                  '[]'::jsonb, 'reviewed', 1, 'reviewer')
        """,
        (
            knowledge_id,
            source_document_id,
            source_version,
            source_digest,
            extraction_id,
            markdown,
            _sha(markdown),
        ),
    )
    conn.commit()
    return knowledge_id


def test_changed_revision_projects_only_explicit_information_and_knowledge_consumers(conn) -> None:
    before, after, before_extraction = _revisions(conn)
    project_id = project_documents.get_document(conn, before["document_id"])["parent_project_id"]

    exact_information = _information(conn, project_id, "Information exacte")
    _link_information(
        conn,
        information_id=exact_information,
        source_document_id=before["source_document_id"],
        observed_version=before["source_version"],
        observed_digest=before["source_digest"],
    )
    unversioned_information = _information(conn, project_id, "Information non versionnée")
    _link_information(
        conn,
        information_id=unversioned_information,
        source_document_id=before["source_document_id"],
        observed_version=None,
        observed_digest=None,
    )
    conflicting_information = _information(conn, project_id, "Information contradictoire")
    _link_information(
        conn,
        information_id=conflicting_information,
        source_document_id=before["source_document_id"],
        observed_version=before["source_version"],
        observed_digest="0" * 64,
    )
    knowledge_id = _knowledge(
        conn,
        source_document_id=before["source_document_id"],
        source_version=before["source_version"],
        source_digest=before["source_digest"],
        extraction_id=before_extraction,
    )

    before_counts = {
        "information_links": conn.execute(
            "SELECT count(*) FROM agency_information_document_links"
        ).fetchone()[0],
        "knowledge": conn.execute("SELECT count(*) FROM knowledge_items").fetchone()[0],
    }
    result = project_document_impacts.project_impact_candidates(
        conn,
        before_version_id=before["version_id"],
        after_version_id=after["version_id"],
    )
    targets = {
        (item["target"]["entity_type"], item["target"]["entity_id"]): item
        for item in result["impact_candidates"]
    }
    assert set(targets) == {
        ("information", exact_information),
        ("information", unversioned_information),
        ("knowledge", knowledge_id),
    }
    assert targets[("information", exact_information)]["basis"]["strength"] == "exact_digest"
    assert targets[("information", exact_information)]["review_posture"] == "review_recommended"
    assert targets[("information", unversioned_information)]["basis"]["strength"] == "unversioned_document_link"
    assert targets[("information", unversioned_information)]["review_posture"] == "needs_scope_confirmation"
    assert targets[("knowledge", knowledge_id)]["basis"]["strength"] == "exact_source_triple"
    assert all(item["impact_established"] is False for item in targets.values())
    assert any(
        item.get("target_id") == conflicting_information
        and item["reason"] == "declared_observed_revision_does_not_match_before_revision"
        for item in result["excluded_or_unresolved"]
    )
    assert result["authority"]["is_work_issue"] is False
    assert result["excluded_surfaces"]["document_relation"].startswith("canonical Entity Relation")
    assert before_counts == {
        "information_links": conn.execute(
            "SELECT count(*) FROM agency_information_document_links"
        ).fetchone()[0],
        "knowledge": conn.execute("SELECT count(*) FROM knowledge_items").fetchone()[0],
    }
    assert project_document_impacts.project_impact_candidates(
        conn,
        before_version_id=before["version_id"],
        after_version_id=after["version_id"],
    ) == result


def test_unchanged_structured_content_produces_no_impact_candidates(conn) -> None:
    before, after, before_extraction = _revisions(conn, same_content=True)
    project_id = project_documents.get_document(conn, before["document_id"])["parent_project_id"]
    information_id = _information(conn, project_id, "Consumer")
    _link_information(
        conn,
        information_id=information_id,
        source_document_id=before["source_document_id"],
        observed_version=before["source_version"],
        observed_digest=before["source_digest"],
    )
    _knowledge(
        conn,
        source_document_id=before["source_document_id"],
        source_version=before["source_version"],
        source_digest=before["source_digest"],
        extraction_id=before_extraction,
    )

    result = project_document_impacts.project_impact_candidates(
        conn,
        before_version_id=before["version_id"],
        after_version_id=after["version_id"],
    )
    assert result["comparison_summary"]["has_changes"] is False
    assert result["impact_candidates"] == []
    assert result["reason"] == "no_structural_content_change_detected"


def test_information_declared_version_mismatch_is_excluded_even_without_digest(conn) -> None:
    before, after, _ = _revisions(conn)
    project_id = project_documents.get_document(conn, before["document_id"])["parent_project_id"]
    information_id = _information(conn, project_id, "Wrong version")
    _link_information(
        conn,
        information_id=information_id,
        source_document_id=before["source_document_id"],
        observed_version=before["source_version"] + 1,
        observed_digest=None,
    )
    result = project_document_impacts.project_impact_candidates(
        conn,
        before_version_id=before["version_id"],
        after_version_id=after["version_id"],
    )
    assert not any(
        item["target"]["entity_id"] == information_id
        for item in result["impact_candidates"]
    )
    assert any(item.get("target_id") == information_id for item in result["excluded_or_unresolved"])
