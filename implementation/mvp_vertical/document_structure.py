"""Project existing structured compilations onto Pantheon's document structure contract.

The structured compiler and PostgreSQL tables remain the operational source for
units and retrieval links.  This module only exposes their transport-neutral
projection.  It does not parse documents, infer professional truth, create
cards, admit Evidence or promote Knowledge.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .structured_extraction import CompilationResult, RetrievalProjection, unit_id


_FRAGMENT_KIND_BY_CONTENT_TYPE = {
    "heading": "section",
    "paragraph": "text",
    "list": "text",
    "table": "table",
    "figure_caption": "figure",
    "page_fragment": "mixed",
}


def _timestamp(value: datetime | str) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if not value:
        raise ValueError("created_at is required")
    return value


def _page_unit_id(structure_id: str, page: int) -> str:
    return f"{structure_id}.page.{page:04d}"


def _fallback_unit_id(structure_id: str) -> str:
    return f"{structure_id}.section.0000"


def fragment_refs_for_chunk(
    compilation_ref: str,
    chunk: RetrievalProjection,
) -> tuple[str, ...]:
    """Return every source fragment in the compiler's preserved order.

    The current governance slice requires one primary ``fragment_ref`` on a
    chunk.  MVP persistence remains richer: ``retrieval_chunk_units`` keeps all
    source-unit links.  Callers may use the first value as the transport anchor
    while retaining this full tuple for audit and reconstruction.
    """

    refs = tuple(unit_id(compilation_ref, ordinal) for ordinal in chunk.unit_ordinals)
    if not refs:
        raise ValueError("a retrieval chunk must reference at least one structured unit")
    return refs


def primary_fragment_ref(
    compilation_ref: str,
    chunk: RetrievalProjection,
) -> str:
    """Return the contract's primary fragment anchor for one retrieval chunk."""

    return fragment_refs_for_chunk(compilation_ref, chunk)[0]


def project_document_structure(
    *,
    document_ref: str,
    extraction_ref: str,
    compilation_ref: str,
    compiled: CompilationResult,
    created_at: datetime | str,
) -> dict[str, Any]:
    """Build a ``document_structure`` value accepted by Pantheon Next.

    Existing ``StructuredUnit`` rows become stable logical fragments.  PDF page
    numbers become native units when available; documents without page
    provenance receive one neutral section unit.  Candidate semantic
    qualification is deliberately omitted here because the deterministic
    compiler does not infer discipline, project state or architectural meaning.
    """

    if not compiled.units:
        raise ValueError("document structure requires at least one structured unit")

    pages = sorted(
        {
            page
            for unit in compiled.units
            for page in (unit.page_start, unit.page_end)
            if page is not None
        }
    )
    if pages:
        native_units = [
            {
                "unit_id": _page_unit_id(compilation_ref, page),
                "unit_kind": "page",
                "ordinal": index,
                "label": f"Page {page}",
            }
            for index, page in enumerate(pages)
        ]
        page_refs = {
            page: _page_unit_id(compilation_ref, page)
            for page in pages
        }
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

    fragments: list[dict[str, Any]] = []
    for ordinal, source_unit in enumerate(compiled.units):
        fragment: dict[str, Any] = {
            "fragment_id": unit_id(compilation_ref, ordinal),
            "unit_ref": page_refs.get(source_unit.page_start, fallback_ref),
            "fragment_kind": _FRAGMENT_KIND_BY_CONTENT_TYPE[source_unit.content_type],
            "reading_order": ordinal,
            "locator": {
                "structural_locator": source_unit.structural_locator,
            },
        }
        label = source_unit.parent_heading
        if source_unit.content_type == "heading":
            label = source_unit.text.strip()
        if label:
            fragment["label"] = label
        fragments.append(fragment)

    return {
        "structure_id": compilation_ref,
        "document_ref": document_ref,
        "extraction_ref": extraction_ref,
        "status": compiled.status,
        "native_units": native_units,
        "fragments": fragments,
        "quality_flags": list(compiled.quality_flags),
        "created_at": _timestamp(created_at),
    }
