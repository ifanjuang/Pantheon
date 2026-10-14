"""Deterministic structured extraction and table-integrity regression tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from mvp_vertical.structured_extraction import (
    chunk_ref,
    compilation_id,
    compile_document,
    unit_id,
)
from mvp_vertical.store import normalize_subject_tags


def _docling_document(*, invalid_span: bool = False) -> dict:
    span = 9 if invalid_span else 2
    return {
        "schema_name": "DoclingDocument",
        "version": "1.7.0",
        "body": {
            "self_ref": "#/body",
            "children": [
                {"$ref": "#/texts/0"},
                {"$ref": "#/texts/1"},
                {"$ref": "#/tables/0"},
            ],
        },
        "texts": [
            {
                "self_ref": "#/texts/0",
                "label": "section_header",
                "text": "Décomposition du prix",
                "prov": [{"page_no": 1}],
            },
            {
                "self_ref": "#/texts/1",
                "label": "text",
                "text": "Les montants sont exprimés en euros.",
                "prov": [{"page_no": 1}],
            },
        ],
        "tables": [
            {
                "self_ref": "#/tables/0",
                "label": "table",
                "prov": [{"page_no": 2}],
                "data": {
                    "num_rows": 3,
                    "num_cols": 3,
                    "table_cells": [
                        {
                            "start_row_offset_idx": 0,
                            "end_row_offset_idx": 2,
                            "start_col_offset_idx": 0,
                            "end_col_offset_idx": 1,
                            "row_span": 2,
                            "col_span": 1,
                            "text": "Lot",
                            "column_header": True,
                        },
                        {
                            "start_row_offset_idx": 0,
                            "end_row_offset_idx": 1,
                            "start_col_offset_idx": 1,
                            "end_col_offset_idx": 3,
                            "row_span": 1,
                            "col_span": span,
                            "text": "Montants",
                            "column_header": True,
                        },
                        {
                            "start_row_offset_idx": 1,
                            "end_row_offset_idx": 2,
                            "start_col_offset_idx": 1,
                            "end_col_offset_idx": 2,
                            "row_span": 1,
                            "col_span": 1,
                            "text": "HT",
                            "column_header": True,
                        },
                        {
                            "start_row_offset_idx": 1,
                            "end_row_offset_idx": 2,
                            "start_col_offset_idx": 2,
                            "end_col_offset_idx": 3,
                            "row_span": 1,
                            "col_span": 1,
                            "text": "TTC",
                            "column_header": True,
                        },
                        {
                            "start_row_offset_idx": 2,
                            "end_row_offset_idx": 3,
                            "start_col_offset_idx": 0,
                            "end_col_offset_idx": 1,
                            "row_span": 1,
                            "col_span": 1,
                            "text": "Maçonnerie",
                        },
                        {
                            "start_row_offset_idx": 2,
                            "end_row_offset_idx": 3,
                            "start_col_offset_idx": 1,
                            "end_col_offset_idx": 2,
                            "row_span": 1,
                            "col_span": 1,
                            "text": "10 000",
                        },
                        {
                            "start_row_offset_idx": 2,
                            "end_row_offset_idx": 3,
                            "start_col_offset_idx": 2,
                            "end_col_offset_idx": 3,
                            "row_span": 1,
                            "col_span": 1,
                            "text": "12 000",
                        },
                    ],
                },
            }
        ],
        "pictures": [],
        "groups": [],
        "pages": {"1": {"page_no": 1}, "2": {"page_no": 2}},
    }


def test_docling_structure_preserves_order_pages_and_merged_table() -> None:
    result = compile_document(
        markdown="# Décomposition du prix\n\nTexte\n\n| Lot | HT | TTC |",
        document_json=_docling_document(),
        converter="docling_serve",
    )

    assert result.status == "ready"
    assert [unit.content_type for unit in result.units] == [
        "heading",
        "paragraph",
        "table",
    ]
    assert result.units[1].parent_heading == "Décomposition du prix"
    assert result.units[2].page_start == result.units[2].page_end == 2
    assert result.page_count == 2
    assert result.table_count == 1
    assert result.anomaly_count == 0
    assert (
        len(result.chunks) == 2
    )  # headings remain structural, not tiny retrieval chunks

    table = result.units[2]
    assert table.table_data is not None
    assert table.table_data["cells"][1]["colspan"] == 2
    assert table.table_data["header_paths"][1] == ["Montants", "HT"]
    assert table.table_data["repair_operations"] == []
    assert table.table_data["synthetic_content_flags"] == []
    assert "dito" not in table.text.lower()
    assert table.text.splitlines()[-1] == "| Maçonnerie | 10 000 | 12 000 |"


def test_invalid_table_span_is_repaired_but_forces_review() -> None:
    result = compile_document(
        markdown="fallback",
        document_json=_docling_document(invalid_span=True),
        converter="docling_serve",
    )

    assert result.status == "needs_review"
    assert "table_span_offset_mismatch" in result.quality_flags
    assert result.anomaly_count == 1
    table = result.units[2]
    assert table.table_data is not None
    assert table.table_data["repair_operations"]
    assert table.table_data["integrity_score"] < 1.0


def test_offset_span_mismatch_is_explicitly_reconciled() -> None:
    document = _docling_document()
    cell = document["tables"][0]["data"]["table_cells"][0]
    cell["row_span"] = 1

    result = compile_document(
        markdown="fallback",
        document_json=document,
        converter="docling_serve",
    )

    table = result.units[2]
    assert result.status == "needs_review"
    assert result.anomaly_count == 1
    assert table.table_data is not None
    assert table.table_data["cells"][0]["rowspan"] == 2
    assert table.table_data["repair_operations"][0] == {
        "operation": "reconcile_span_with_offsets",
        "source_index": 0,
        "mismatches": {"row": {"declared_span": 1, "offset_span": 2}},
    }


def test_unresolved_reference_has_one_explicit_diagnostic() -> None:
    document = _docling_document()
    document["body"]["children"].append({"$ref": "#/texts/404"})

    result = compile_document(
        markdown="fallback",
        document_json=document,
        converter="docling_serve",
    )

    assert result.status == "needs_review"
    assert result.anomaly_count == 1
    assert result.diagnostics == (
        {"code": "docling_unresolved_reference", "scope": "compilation"},
    )


def test_heading_stack_preserves_siblings_and_retrieval_context() -> None:
    result = compile_document(
        markdown=(
            "# Mission\n\n## Honoraires\n\nClause A.\n\n"
            "## Révision\n\nClause B."
        ),
        document_json={"schema_name": "direct_text"},
        converter="direct_text",
    )

    mission, honoraires, clause_a, revision, clause_b = result.units
    assert mission.heading_level == 1
    assert honoraires.parent_heading == "Mission"
    assert honoraires.section_path == ("Mission", "Honoraires")
    assert revision.parent_heading == "Mission"
    assert revision.section_path == ("Mission", "Révision")
    assert clause_a.section_path == ("Mission", "Honoraires")
    assert clause_b.section_path == ("Mission", "Révision")
    assert result.chunks[0].text.startswith("Section: Mission > Honoraires\n\n")
    assert result.chunks[1].text.startswith("Section: Mission > Révision\n\n")


def test_unusable_docling_json_falls_back_visibly_to_markdown() -> None:
    result = compile_document(
        markdown="# Contrat\n\nClause 1.",
        document_json={"schema_name": "DoclingDocument", "texts": []},
        converter="docling_serve",
    )

    assert result.status == "needs_review"
    assert result.quality_flags == ("structured_json_fallback",)
    assert [unit.content_type for unit in result.units] == ["heading", "paragraph"]
    assert len(result.chunks) == 1


def test_direct_text_markdown_compiles_without_false_docling_warning() -> None:
    result = compile_document(
        markdown="# CCTP\n\n- Purger le support\n- Dépoussiérer",
        document_json={"schema_name": "direct_text"},
        converter="direct_text",
    )

    assert result.status == "ready"
    assert result.quality_flags == ()
    assert [unit.content_type for unit in result.units] == ["heading", "list"]
    assert result.chunks[0].parent_heading == "CCTP"


def test_compilation_and_unit_identities_are_stable() -> None:
    first = compile_document(
        markdown="Texte stable.",
        document_json={"schema_name": "direct_text"},
        converter="direct_text",
    )
    second = compile_document(
        markdown="Texte stable.",
        document_json={"schema_name": "direct_text"},
        converter="direct_text",
    )
    cref = compilation_id("ext-test")

    assert first.output_digest == second.output_digest
    assert cref == compilation_id("ext-test")
    assert unit_id(cref, 0) == unit_id(cref, 0)


def test_chunk_identity_is_scoped_to_immutable_compilation() -> None:
    assert chunk_ref("cmp-first", 0) == "chunk.cmp-first.0000"
    assert chunk_ref("cmp-first", 12) == "chunk.cmp-first.0012"
    assert chunk_ref("cmp-first", 0) != chunk_ref("cmp-second", 0)


def test_structured_migration_keeps_sources_and_authority_out_of_scope() -> None:
    sql = (
        Path(__file__).resolve().parents[1]
        / "mvp_vertical"
        / "sql"
        / "008_structured_extraction.sql"
    ).read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS structured_compilations" in sql
    assert "CREATE TABLE IF NOT EXISTS document_classifications" in sql
    assert "CREATE TABLE IF NOT EXISTS extraction_units" in sql
    assert "CREATE TABLE IF NOT EXISTS retrieval_chunk_projections" in sql
    assert "FOREIGN KEY (compilation_id, extraction_id)" in sql
    assert "section_path JSONB" in sql
    assert "ALTER TABLE source_documents" not in sql
    assert "CREATE TABLE EVIDENCE" not in sql.upper()


def test_document_subject_tags_are_explicit_normalized_metadata() -> None:
    assert normalize_subject_tags([" structure ", "budget", "Structure", ""]) == [
        "structure",
        "budget",
    ]
    with pytest.raises(ValueError, match="list"):
        normalize_subject_tags("structure")  # type: ignore[arg-type]
