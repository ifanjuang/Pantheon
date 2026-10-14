"""Contract projection tests for structured document compilations."""

from __future__ import annotations

from datetime import UTC, datetime

from mvp_vertical.document_structure import (
    fragment_refs_for_chunk,
    primary_fragment_ref,
    project_document_structure,
)
from mvp_vertical.structured_extraction import compile_document, compilation_id


def _compiled():
    document = {
        "schema_name": "DoclingDocument",
        "version": "1.7.0",
        "body": {
            "self_ref": "#/body",
            "children": [
                {"$ref": "#/texts/0"},
                {"$ref": "#/texts/1"},
                {"$ref": "#/texts/2"},
            ],
        },
        "texts": [
            {
                "self_ref": "#/texts/0",
                "label": "section_header",
                "text": "Variante A",
                "prov": [{"page_no": 1}],
            },
            {
                "self_ref": "#/texts/1",
                "label": "text",
                "text": "La variante conserve la façade existante.",
                "prov": [{"page_no": 1}],
            },
            {
                "self_ref": "#/texts/2",
                "label": "text",
                "text": "Elle modifie la distribution intérieure.",
                "prov": [{"page_no": 2}],
            },
        ],
        "tables": [],
        "pictures": [],
        "groups": [],
        "pages": {"1": {"page_no": 1}, "2": {"page_no": 2}},
    }
    return compile_document(
        markdown="# Variante A\n\nTexte",
        document_json=document,
        converter="docling_serve",
    )


def test_projection_reuses_compiled_units_as_fragments() -> None:
    compiled = _compiled()
    cref = compilation_id("extraction.demo")
    projected = project_document_structure(
        document_ref="document.demo",
        extraction_ref="extraction.demo",
        compilation_ref=cref,
        compiled=compiled,
        created_at=datetime(2026, 8, 4, 12, 0, tzinfo=UTC),
    )
    assert projected["structure_id"] == cref
    assert [unit["unit_kind"] for unit in projected["native_units"]] == ["page", "page"]
    assert [fragment["fragment_kind"] for fragment in projected["fragments"]] == [
        "section", "text", "text"
    ]
    assert projected["fragments"][0]["label"] == "Variante A"
    assert projected["fragments"][1]["unit_ref"].endswith("page.0001")
    assert projected["fragments"][2]["unit_ref"].endswith("page.0002")
    assert "qualification" not in projected["fragments"][1]


def test_chunk_keeps_all_source_fragments_and_one_contract_anchor() -> None:
    compiled = _compiled()
    cref = compilation_id("extraction.demo")
    chunk = compiled.chunks[0]
    refs = fragment_refs_for_chunk(cref, chunk)
    assert len(refs) == len(chunk.unit_ordinals)
    assert primary_fragment_ref(cref, chunk) == refs[0]
    assert len(set(refs)) == len(refs)


def test_page_less_document_uses_one_neutral_native_unit() -> None:
    compiled = compile_document(
        markdown="# Introduction\n\nContenu sans page.",
        document_json={},
        converter="direct_text",
    )
    cref = compilation_id("extraction.markdown")
    projected = project_document_structure(
        document_ref="document.markdown",
        extraction_ref="extraction.markdown",
        compilation_ref=cref,
        compiled=compiled,
        created_at="2026-08-04T12:00:00+00:00",
    )
    assert projected["native_units"] == [
        {
            "unit_id": f"{cref}.section.0000",
            "unit_kind": "section",
            "ordinal": 0,
            "label": "Document",
        }
    ]
    assert {fragment["unit_ref"] for fragment in projected["fragments"]} == {
        f"{cref}.section.0000"
    }
