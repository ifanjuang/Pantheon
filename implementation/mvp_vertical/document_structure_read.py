"""Read-only projection of persisted structured document compilations.

The PostgreSQL compilation remains the operational source. This module exposes
its native units, logical fragments and complete chunk-to-fragment provenance;
it does not parse, qualify, approve, persist or promote anything.
"""

from __future__ import annotations

from typing import Any

import psycopg

from .structured_extraction import chunk_ref, unit_id

_FRAGMENT_KIND_BY_CONTENT_TYPE = {
    "heading": "section",
    "paragraph": "text",
    "list": "text",
    "table": "table",
    "figure_caption": "figure",
    "page_fragment": "mixed",
}


def _page_unit_id(structure_id: str, page: int) -> str:
    return f"{structure_id}.page.{page:04d}"


def _fallback_unit_id(structure_id: str) -> str:
    return f"{structure_id}.section.0000"


def get_document_structure(
    conn: psycopg.Connection,
    document_id: str,
) -> dict[str, Any]:
    """Return the current compiled structure and its complete retrieval links."""

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT d.current_extraction_id, sc.compilation_id, sc.status,
                   COALESCE(sc.quality_flags, '[]'::jsonb), sc.created_at
              FROM source_documents d
              JOIN document_compilation_bindings cb ON cb.document_id = d.document_id
              JOIN structured_compilations sc ON sc.compilation_id = cb.compilation_id
             WHERE d.document_id = %s
               AND sc.extraction_id = d.current_extraction_id
            """,
            (document_id,),
        )
        header = cur.fetchone()
    if header is None:
        raise KeyError(f"unknown compiled document: {document_id}")

    extraction_ref, compilation_ref, status, quality_flags, created_at = header
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT ordinal, content_type, body, page_start, page_end,
                   structural_locator, parent_heading,
                   COALESCE(section_path, '[]'::jsonb),
                   COALESCE(quality_flags, '[]'::jsonb), table_data
              FROM extraction_units
             WHERE compilation_id = %s
               AND extraction_id = %s
             ORDER BY ordinal
            """,
            (compilation_ref, extraction_ref),
        )
        unit_rows = cur.fetchall()
    if not unit_rows:
        raise KeyError(f"compiled document has no structured units: {document_id}")

    pages = sorted(
        {
            page
            for row in unit_rows
            for page in (row[3], row[4])
            if page is not None
        }
    )
    if pages:
        native_units = [
            {
                "unit_id": _page_unit_id(compilation_ref, page),
                "unit_kind": "page",
                "ordinal": ordinal,
                "label": f"Page {page}",
            }
            for ordinal, page in enumerate(pages)
        ]
        page_refs = {page: _page_unit_id(compilation_ref, page) for page in pages}
        fallback_ref = native_units[0]["unit_id"]
    else:
        fallback_ref = _fallback_unit_id(compilation_ref)
        native_units = [
            {
                "unit_id": fallback_ref,
                "unit_kind": "section",
                "ordinal": 0,
                "label": "Document",
            }
        ]
        page_refs = {}

    fragments = []
    for (
        ordinal,
        content_type,
        body,
        page_start,
        page_end,
        locator,
        parent_heading,
        section_path,
        fragment_flags,
        table_data,
    ) in unit_rows:
        fragment = {
            "fragment_id": unit_id(compilation_ref, ordinal),
            "unit_ref": page_refs.get(page_start, fallback_ref),
            "fragment_kind": _FRAGMENT_KIND_BY_CONTENT_TYPE[content_type],
            "content_type": content_type,
            "reading_order": ordinal,
            "body": body,
            "locator": {
                "structural_locator": locator,
                "page_start": page_start,
                "page_end": page_end,
            },
            "section_path": list(section_path or []),
            "quality_flags": list(fragment_flags or []),
        }
        label = body.strip() if content_type == "heading" else parent_heading
        if label:
            fragment["label"] = label
        if table_data is not None:
            fragment["table_data"] = table_data
        fragments.append(fragment)

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT rcu.chunk_no, eu.ordinal
              FROM retrieval_chunk_units rcu
              JOIN extraction_units eu ON eu.unit_id = rcu.unit_id
             WHERE eu.compilation_id = %s
             ORDER BY rcu.chunk_no, rcu.unit_order
            """,
            (compilation_ref,),
        )
        link_rows = cur.fetchall()

    chunk_ordinals: dict[int, list[int]] = {}
    for chunk_no, unit_ordinal in link_rows:
        chunk_ordinals.setdefault(chunk_no, []).append(unit_ordinal)
    chunk_anchors = []
    for chunk_no, ordinals in sorted(chunk_ordinals.items()):
        refs = [unit_id(compilation_ref, ordinal) for ordinal in ordinals]
        chunk_anchors.append(
            {
                "chunk_ref": chunk_ref(compilation_ref, chunk_no),
                "ordinal": chunk_no,
                "fragment_ref": refs[0],
                "fragment_refs": refs,
            }
        )

    return {
        "structure_id": compilation_ref,
        "document_ref": document_id,
        "extraction_ref": extraction_ref,
        "status": status,
        "native_units": native_units,
        "fragments": fragments,
        "chunk_anchors": chunk_anchors,
        "quality_flags": list(quality_flags or []),
        "created_at": created_at.isoformat(),
        "authority": {
            "is_source": False,
            "is_evidence": False,
            "is_memory": False,
            "is_professional_validation": False,
        },
    }
