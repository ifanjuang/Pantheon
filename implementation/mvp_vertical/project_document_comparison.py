"""Read-only comparison of exact professional Project Document revisions.

The professional revision owner supplies stable revision identity. Retained
``extraction_runs`` / ``structured_compilations`` / ``extraction_units`` supply
one structured derivative of the exact source bytes. This module calculates a
comparison only; it does not persist impact, create work, admit Evidence or
select a professionally current revision.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from difflib import unified_diff
from typing import Any

import psycopg
from psycopg.rows import dict_row

from . import project_documents

MAX_BODY_PREVIEW = 800
MAX_DIFF_CHARS = 4000

AUTHORITY = {
    "is_source": False,
    "is_evidence": False,
    "is_decision": False,
    "is_professional_validation": False,
    "establishes_downstream_impact": False,
    "changes_current_authority": False,
    "changes_project_truth": False,
}

LIMITATIONS = [
    "fragment matching uses exact content_type + structural_locator + occurrence only",
    "moved or renamed content may appear as removed plus added",
    "comparison of extracted structure does not prove a change in original visual layout",
    "text change does not establish downstream professional impact",
]


class ProjectDocumentComparisonError(ValueError):
    pass


class CrossDocumentComparison(ProjectDocumentComparisonError):
    pass


class RevisionStructureUnavailable(ProjectDocumentComparisonError):
    pass


class RevisionStructureAmbiguous(ProjectDocumentComparisonError):
    pass


def _canonical_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _content_digest(row: dict[str, Any]) -> str:
    return _canonical_digest(
        {
            "body": row["body"],
            "table_data": row.get("table_data"),
        }
    )


def _preview(text: str) -> dict[str, Any]:
    value = str(text)
    truncated = len(value) > MAX_BODY_PREVIEW
    return {
        "text": value[:MAX_BODY_PREVIEW],
        "truncated": truncated,
        "length": len(value),
    }


def _bounded_diff(before: str, after: str) -> dict[str, Any]:
    lines = list(
        unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile="before",
            tofile="after",
            lineterm="",
        )
    )
    text = "\n".join(lines)
    truncated = len(text) > MAX_DIFF_CHARS
    return {
        "unified": text[:MAX_DIFF_CHARS],
        "truncated": truncated,
        "line_count": len(lines),
    }


def _revision(conn: psycopg.Connection, version_id: str) -> dict[str, Any]:
    return project_documents.get_revision(conn, version_id)


def _resolve_structure_candidate(
    conn: psycopg.Connection,
    revision: dict[str, Any],
) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT sc.compilation_id,
                   sc.output_digest,
                   sc.status AS compilation_status,
                   sc.quality_flags,
                   sc.created_at AS compilation_created_at,
                   er.extraction_id,
                   er.converter,
                   er.converter_version,
                   er.config_digest,
                   er.status AS extraction_status,
                   er.created_at AS extraction_created_at
              FROM extraction_runs er
              JOIN structured_compilations sc
                ON sc.extraction_id = er.extraction_id
             WHERE er.document_id = %s
               AND er.source_digest = %s
               AND sc.status IN ('ready', 'needs_review')
             ORDER BY sc.output_digest, sc.compilation_id
            """,
            (revision["source_document_id"], revision["source_digest"]),
        )
        candidates = [dict(row) for row in cur.fetchall()]

    if not candidates:
        raise RevisionStructureUnavailable(
            f"no retained structured compilation for Project Document revision {revision['version_id']}"
        )

    by_output: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        by_output[str(candidate["output_digest"])].append(candidate)
    if len(by_output) > 1:
        raise RevisionStructureAmbiguous(
            "multiple retained structured outputs exist for the exact source revision: "
            + ", ".join(sorted(by_output))
        )

    chosen = min(candidates, key=lambda row: str(row["compilation_id"]))
    return {
        "compilation_id": chosen["compilation_id"],
        "output_digest": chosen["output_digest"],
        "status": chosen["compilation_status"],
        "quality_flags": list(chosen.get("quality_flags") or []),
        "extraction_id": chosen["extraction_id"],
        "converter": chosen["converter"],
        "converter_version": chosen["converter_version"],
        "config_digest": chosen["config_digest"],
        "candidate_count": len(candidates),
        "resolution_basis": (
            "single_exact_output"
            if len(candidates) == 1
            else "content_identical_outputs_deterministic_compilation_id"
        ),
    }


def _load_fragments(
    conn: psycopg.Connection,
    structure: dict[str, Any],
) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT ordinal, content_type, body, text_digest,
                   structural_locator, page_start, page_end, parent_heading,
                   COALESCE(section_path, '[]'::jsonb) AS section_path,
                   COALESCE(quality_flags, '[]'::jsonb) AS quality_flags,
                   table_data
              FROM extraction_units
             WHERE compilation_id = %s
             ORDER BY ordinal
            """,
            (structure["compilation_id"],),
        )
        rows = [dict(row) for row in cur.fetchall()]
    if not rows:
        raise RevisionStructureUnavailable(
            f"structured compilation has no fragments: {structure['compilation_id']}"
        )
    return rows


def _indexed_fragments(rows: list[dict[str, Any]]) -> dict[tuple[str, str, int], dict[str, Any]]:
    occurrences: dict[tuple[str, str], int] = defaultdict(int)
    indexed: dict[tuple[str, str, int], dict[str, Any]] = {}
    for row in rows:
        base = (str(row["content_type"]), str(row["structural_locator"]))
        occurrence = occurrences[base]
        occurrences[base] += 1
        key = (base[0], base[1], occurrence)
        indexed[key] = row
    return indexed


def _fragment_projection(
    key: tuple[str, str, int],
    row: dict[str, Any],
) -> dict[str, Any]:
    return {
        "key": {
            "content_type": key[0],
            "structural_locator": key[1],
            "occurrence": key[2],
        },
        "ordinal": int(row["ordinal"]),
        "content_digest": _content_digest(row),
        "text_digest": row["text_digest"],
        "body": _preview(row["body"]),
        "page_start": row.get("page_start"),
        "page_end": row.get("page_end"),
        "parent_heading": row.get("parent_heading"),
        "section_path": list(row.get("section_path") or []),
        "quality_flags": list(row.get("quality_flags") or []),
        "has_table_data": row.get("table_data") is not None,
    }


def compare_revisions(
    conn: psycopg.Connection,
    *,
    before_version_id: str,
    after_version_id: str,
) -> dict[str, Any]:
    """Calculate a conservative comparison between two exact revisions."""
    before = _revision(conn, before_version_id)
    after = _revision(conn, after_version_id)
    if before["document_id"] != after["document_id"]:
        raise CrossDocumentComparison(
            "Project Document comparison requires two revisions of the same logical document"
        )

    before_structure = _resolve_structure_candidate(conn, before)
    after_structure = _resolve_structure_candidate(conn, after)
    before_rows = _load_fragments(conn, before_structure)
    after_rows = _load_fragments(conn, after_structure)

    before_index = _indexed_fragments(before_rows)
    after_index = _indexed_fragments(after_rows)
    all_keys = sorted(set(before_index) | set(after_index))

    added: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    modified: list[dict[str, Any]] = []
    unchanged = 0

    for key in all_keys:
        old = before_index.get(key)
        new = after_index.get(key)
        if old is None:
            added.append(_fragment_projection(key, new))
            continue
        if new is None:
            removed.append(_fragment_projection(key, old))
            continue
        old_digest = _content_digest(old)
        new_digest = _content_digest(new)
        if old_digest == new_digest:
            unchanged += 1
            continue
        modified.append(
            {
                "key": {
                    "content_type": key[0],
                    "structural_locator": key[1],
                    "occurrence": key[2],
                },
                "before": _fragment_projection(key, old),
                "after": _fragment_projection(key, new),
                "diff": _bounded_diff(str(old["body"]), str(new["body"])),
            }
        )

    return {
        "document_id": before["document_id"],
        "before_revision": {
            "version_id": before["version_id"],
            "version_seq": int(before["version_seq"]),
            "revision_label": before.get("revision_label"),
            "source_document_id": before["source_document_id"],
            "source_version": int(before["source_version"]),
            "source_digest": before["source_digest"],
            "structure": before_structure,
        },
        "after_revision": {
            "version_id": after["version_id"],
            "version_seq": int(after["version_seq"]),
            "revision_label": after.get("revision_label"),
            "source_document_id": after["source_document_id"],
            "source_version": int(after["source_version"]),
            "source_digest": after["source_digest"],
            "structure": after_structure,
        },
        "summary": {
            "before_fragment_count": len(before_rows),
            "after_fragment_count": len(after_rows),
            "unchanged": unchanged,
            "modified": len(modified),
            "added": len(added),
            "removed": len(removed),
            "has_changes": bool(modified or added or removed),
        },
        "modified": modified,
        "added": added,
        "removed": removed,
        "limitations": list(LIMITATIONS),
        "authority": dict(AUTHORITY),
    }
