"""PostgreSQL acceptance for A3a read-only professional revision comparison."""

from __future__ import annotations

import hashlib
import json
import uuid

import pytest

from mvp_vertical import (
    project_document_admission,
    project_document_comparison,
    project_documents,
)


@pytest.fixture
def conn():
    try:
        connection = project_document_admission.connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(
        "TRUNCATE doc_document_version_sources, doc_document_events, "
        "doc_document_versions, doc_documents, extraction_units, "
        "structured_compilations, extraction_runs, document_versions, "
        "source_documents RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _logical_document(conn, project_id: str = "project-alpha", title: str = "Étude") -> dict:
    return project_documents.create_document(
        conn,
        document_id=_id("project-document"),
        parent_project_id=project_id,
        document_type="ETUDE",
        title=title,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("create-document"),
    )


def _technical_source(
    conn,
    *,
    project_id: str,
    source_ref: str,
    digest: str,
) -> tuple[str, int]:
    document_id = _id("source-document")
    conn.execute(
        """
        INSERT INTO source_documents (
            document_id, dossier, parent_project_id, source_ref, source_digest,
            media_type, byte_size, analysis_status
        ) VALUES (%s, %s, %s, %s, %s, 'application/pdf', 1234, 'ready')
        """,
        (document_id, project_id, project_id, source_ref, digest),
    )
    conn.execute(
        """
        INSERT INTO document_versions (
            document_id, version, source_ref, source_digest, media_type, byte_size
        ) VALUES (%s, 1, %s, %s, 'application/pdf', 1234)
        """,
        (document_id, source_ref, digest),
    )
    conn.commit()
    return document_id, 1


def _persist_structure(
    conn,
    *,
    source_document_id: str,
    source_digest: str,
    units: list[dict],
    output_digest: str | None = None,
    compilation_id: str | None = None,
) -> str:
    extraction_id = _id("extraction")
    compilation_id = compilation_id or _id("compilation")
    output_digest = output_digest or _sha(
        json.dumps(units, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    )
    conn.execute(
        """
        INSERT INTO extraction_runs (
            extraction_id, document_id, contract_id, contract_digest,
            source_digest, converter, converter_version, config_digest,
            status, markdown_content, chunk_count, quality_flags
        ) VALUES (%s, %s, 'contract-test', %s, %s, 'fixture', '1', %s,
                  'ready', '# fixture', 0, '[]'::jsonb)
        """,
        (extraction_id, source_document_id, "c" * 64, source_digest, "f" * 64),
    )
    conn.execute(
        """
        INSERT INTO structured_compilations (
            compilation_id, extraction_id, compiler, compiler_version,
            config_digest, output_digest, status, quality_flags, diagnostics,
            unit_count, chunk_count, page_count, table_count, anomaly_count
        ) VALUES (%s, %s, 'pantheon_structured_extraction', '2', %s, %s,
                  'ready', '[]'::jsonb, '[]'::jsonb, %s, 0, 1, %s, 0)
        """,
        (
            compilation_id,
            extraction_id,
            "f" * 64,
            output_digest,
            len(units),
            sum(1 for unit in units if unit["content_type"] == "table"),
        ),
    )
    for ordinal, unit in enumerate(units):
        body = unit["body"]
        conn.execute(
            """
            INSERT INTO extraction_units (
                unit_id, compilation_id, extraction_id, ordinal, content_type,
                body, text_digest, page_start, page_end, structural_locator,
                parent_heading, section_path, quality_flags, table_data
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 1, 1, %s, %s,
                      %s::jsonb, %s::jsonb, %s::jsonb)
            """,
            (
                _id("unit"),
                compilation_id,
                extraction_id,
                ordinal,
                unit["content_type"],
                body,
                _sha(body),
                unit["locator"],
                unit.get("parent_heading"),
                json.dumps(unit.get("section_path") or []),
                json.dumps(unit.get("quality_flags") or []),
                json.dumps(unit.get("table_data")) if unit.get("table_data") is not None else None,
            ),
        )
    conn.commit()
    return compilation_id


def _revision(
    conn,
    *,
    logical_document: dict,
    source_ref: str,
    revision_label: str,
    digest: str,
    units: list[dict] | None,
    supersedes_version_id: str | None = None,
) -> dict:
    source_document_id, source_version = _technical_source(
        conn,
        project_id=logical_document["parent_project_id"],
        source_ref=source_ref,
        digest=digest,
    )
    if units is not None:
        _persist_structure(
            conn,
            source_document_id=source_document_id,
            source_digest=digest,
            units=units,
        )
    return project_documents.link_revision(
        conn,
        document_id=logical_document["document_id"],
        source_document_id=source_document_id,
        source_version=source_version,
        revision_label=revision_label,
        supersedes_version_id=supersedes_version_id,
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("link-revision"),
    )


def test_compare_b_to_c_uses_exact_retained_structures_across_different_filenames(conn) -> None:
    document = _logical_document(conn)
    units_b = [
        {"content_type": "heading", "locator": "section:menuiseries", "body": "Menuiseries"},
        {"content_type": "paragraph", "locator": "section:menuiseries/p:uw", "body": "Uw = 1,4 W/m².K"},
        {"content_type": "paragraph", "locator": "section:menuiseries/p:old", "body": "Ancienne clause"},
        {
            "content_type": "table",
            "locator": "section:menuiseries/table:1",
            "body": "Type | Qté\nA | 2",
            "table_data": {"rows": [["Type", "Qté"], ["A", "2"]]},
        },
    ]
    units_c = [
        {"content_type": "heading", "locator": "section:menuiseries", "body": "Menuiseries"},
        {"content_type": "paragraph", "locator": "section:menuiseries/p:uw", "body": "Uw = 1,3 W/m².K"},
        {
            "content_type": "table",
            "locator": "section:menuiseries/table:1",
            "body": "Type | Qté\nA | 2",
            "table_data": {"rows": [["Type", "Qté"], ["A", "3"]]},
        },
        {"content_type": "paragraph", "locator": "section:menuiseries/p:new", "body": "Nouvelle clause"},
    ]
    rev_b = _revision(
        conn,
        logical_document=document,
        source_ref="BET/etude_B.pdf",
        revision_label="B",
        digest="b" * 64,
        units=units_b,
    )
    rev_c = _revision(
        conn,
        logical_document=document,
        source_ref="BET/renamed_etude_C.pdf",
        revision_label="C",
        digest="c" * 64,
        units=units_c,
        supersedes_version_id=rev_b["version_id"],
    )

    before_counts = {
        "versions": conn.execute("SELECT count(*) FROM doc_document_versions").fetchone()[0],
        "units": conn.execute("SELECT count(*) FROM extraction_units").fetchone()[0],
    }
    comparison = project_document_comparison.compare_revisions(
        conn,
        before_version_id=rev_b["version_id"],
        after_version_id=rev_c["version_id"],
    )
    assert comparison["before_revision"]["revision_label"] == "B"
    assert comparison["after_revision"]["revision_label"] == "C"
    assert comparison["summary"] == {
        "before_fragment_count": 4,
        "after_fragment_count": 4,
        "unchanged": 1,
        "modified": 2,
        "added": 1,
        "removed": 1,
        "has_changes": True,
    }
    modified_locators = {item["key"]["structural_locator"] for item in comparison["modified"]}
    assert modified_locators == {"section:menuiseries/p:uw", "section:menuiseries/table:1"}
    assert comparison["modified"][0]["diff"]["unified"].startswith("--- before\n+++ after")
    assert {item["key"]["structural_locator"] for item in comparison["added"]} == {
        "section:menuiseries/p:new"
    }
    assert {item["key"]["structural_locator"] for item in comparison["removed"]} == {
        "section:menuiseries/p:old"
    }
    assert comparison["authority"]["establishes_downstream_impact"] is False
    assert "moved or renamed content may appear as removed plus added" in comparison["limitations"]
    assert before_counts == {
        "versions": conn.execute("SELECT count(*) FROM doc_document_versions").fetchone()[0],
        "units": conn.execute("SELECT count(*) FROM extraction_units").fetchone()[0],
    }
    assert project_document_comparison.compare_revisions(
        conn,
        before_version_id=rev_b["version_id"],
        after_version_id=rev_c["version_id"],
    ) == comparison


def test_cross_document_comparison_is_refused(conn) -> None:
    first_document = _logical_document(conn, title="Étude 1")
    second_document = _logical_document(conn, title="Étude 2")
    units = [{"content_type": "paragraph", "locator": "p:1", "body": "Texte"}]
    first = _revision(
        conn,
        logical_document=first_document,
        source_ref="one.pdf",
        revision_label="A",
        digest="1" * 64,
        units=units,
    )
    second = _revision(
        conn,
        logical_document=second_document,
        source_ref="two.pdf",
        revision_label="A",
        digest="2" * 64,
        units=units,
    )
    with pytest.raises(project_document_comparison.CrossDocumentComparison):
        project_document_comparison.compare_revisions(
            conn,
            before_version_id=first["version_id"],
            after_version_id=second["version_id"],
        )


def test_missing_historical_structure_is_explicitly_unavailable(conn) -> None:
    document = _logical_document(conn)
    missing = _revision(
        conn,
        logical_document=document,
        source_ref="missing.pdf",
        revision_label="A",
        digest="3" * 64,
        units=None,
    )
    with pytest.raises(project_document_comparison.RevisionStructureUnavailable, match="no retained"):
        project_document_comparison.compare_revisions(
            conn,
            before_version_id=missing["version_id"],
            after_version_id=missing["version_id"],
        )


def test_distinct_structured_outputs_for_same_exact_revision_are_ambiguous(conn) -> None:
    document = _logical_document(conn)
    source_document_id, source_version = _technical_source(
        conn,
        project_id=document["parent_project_id"],
        source_ref="ambiguous.pdf",
        digest="4" * 64,
    )
    _persist_structure(
        conn,
        source_document_id=source_document_id,
        source_digest="4" * 64,
        units=[{"content_type": "paragraph", "locator": "p:1", "body": "Version X"}],
        output_digest="a" * 64,
    )
    _persist_structure(
        conn,
        source_document_id=source_document_id,
        source_digest="4" * 64,
        units=[{"content_type": "paragraph", "locator": "p:1", "body": "Version Y"}],
        output_digest="d" * 64,
    )
    revision = project_documents.link_revision(
        conn,
        document_id=document["document_id"],
        source_document_id=source_document_id,
        source_version=source_version,
        revision_label="A",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("ambiguous"),
    )
    with pytest.raises(project_document_comparison.RevisionStructureAmbiguous, match="multiple retained"):
        project_document_comparison.compare_revisions(
            conn,
            before_version_id=revision["version_id"],
            after_version_id=revision["version_id"],
        )


def test_identical_structured_outputs_resolve_deterministically(conn) -> None:
    document = _logical_document(conn)
    source_document_id, source_version = _technical_source(
        conn,
        project_id=document["parent_project_id"],
        source_ref="duplicate-structure.pdf",
        digest="5" * 64,
    )
    units = [{"content_type": "paragraph", "locator": "p:1", "body": "Même contenu"}]
    output_digest = "e" * 64
    _persist_structure(
        conn,
        source_document_id=source_document_id,
        source_digest="5" * 64,
        units=units,
        output_digest=output_digest,
        compilation_id="compilation-z",
    )
    _persist_structure(
        conn,
        source_document_id=source_document_id,
        source_digest="5" * 64,
        units=units,
        output_digest=output_digest,
        compilation_id="compilation-a",
    )
    revision = project_documents.link_revision(
        conn,
        document_id=document["document_id"],
        source_document_id=source_document_id,
        source_version=source_version,
        revision_label="A",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("link"),
    )
    result = project_document_comparison.compare_revisions(
        conn,
        before_version_id=revision["version_id"],
        after_version_id=revision["version_id"],
    )
    assert result["before_revision"]["structure"]["compilation_id"] == "compilation-a"
    assert result["before_revision"]["structure"]["candidate_count"] == 2
    assert result["before_revision"]["structure"]["resolution_basis"] == (
        "content_identical_outputs_deterministic_compilation_id"
    )
    assert result["summary"]["has_changes"] is False
