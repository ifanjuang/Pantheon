"""Deterministic Docling/Markdown structure compiler.

The converter output remains the observed derivative.  This module compiles it
into versioned, provenance-bearing units and retrieval projections; it does not
promote either representation to Evidence or professional truth.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


COMPILER = "pantheon_structured_extraction"
COMPILER_VERSION = "3"
MAX_RETRIEVAL_CHARS = 1200
MAX_TABLE_SCHEMA_CHARS = 320
MAX_TABLE_DIMENSION = 1000
MAX_TABLE_CELLS = 50_000
MAX_TABLE_OCCUPANCY = 2_000_000
COMPILER_CONFIG = {
    "max_retrieval_chars": MAX_RETRIEVAL_CHARS,
    "retrieval_boundary_policy": "section_then_unit_then_sentence",
    "oversized_table_policy": "row_groups_with_repeated_header_schema",
    "max_table_schema_chars": MAX_TABLE_SCHEMA_CHARS,
    "preserve_tables": True,
    "repeat_spanned_values": False,
    "synthetic_ditto": False,
    "include_section_context": True,
    "max_table_dimension": MAX_TABLE_DIMENSION,
    "max_table_cells": MAX_TABLE_CELLS,
    "max_table_occupancy": MAX_TABLE_OCCUPANCY,
}
CONFIG_DIGEST = hashlib.sha256(
    json.dumps(COMPILER_CONFIG, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()

CONTENT_TYPES = {
    "heading",
    "paragraph",
    "list",
    "table",
    "figure_caption",
    "page_fragment",
}


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


@dataclass(frozen=True)
class StructuredUnit:
    content_type: str
    text: str
    structural_locator: str
    page_start: int | None = None
    page_end: int | None = None
    parent_heading: str | None = None
    heading_level: int | None = None
    section_path: tuple[str, ...] = ()
    quality_flags: tuple[str, ...] = ()
    table_data: dict[str, Any] | None = None

    @property
    def text_digest(self) -> str:
        return _digest(self.text)


@dataclass(frozen=True)
class RetrievalProjection:
    text: str
    content_type: str
    structural_locator: str
    unit_ordinals: tuple[int, ...]
    page_start: int | None = None
    page_end: int | None = None
    parent_heading: str | None = None
    section_path: tuple[str, ...] = ()
    quality_flags: tuple[str, ...] = ()

    @property
    def text_digest(self) -> str:
        return _digest(self.text)


@dataclass(frozen=True)
class CompilationResult:
    units: tuple[StructuredUnit, ...]
    chunks: tuple[RetrievalProjection, ...]
    status: str
    quality_flags: tuple[str, ...]
    page_count: int
    table_count: int
    anomaly_count: int
    diagnostics: tuple[dict[str, Any], ...] = ()
    compiler: str = COMPILER
    compiler_version: str = COMPILER_VERSION
    config_digest: str = CONFIG_DIGEST

    @property
    def output_digest(self) -> str:
        value = {
            "units": [
                {
                    "content_type": unit.content_type,
                    "text": unit.text,
                    "structural_locator": unit.structural_locator,
                    "page_start": unit.page_start,
                    "page_end": unit.page_end,
                    "parent_heading": unit.parent_heading,
                    "heading_level": unit.heading_level,
                    "section_path": unit.section_path,
                    "quality_flags": unit.quality_flags,
                    "table_data": unit.table_data,
                }
                for unit in self.units
            ],
            "chunks": [
                {
                    "text": chunk.text,
                    "content_type": chunk.content_type,
                    "structural_locator": chunk.structural_locator,
                    "unit_ordinals": chunk.unit_ordinals,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "parent_heading": chunk.parent_heading,
                    "section_path": chunk.section_path,
                    "quality_flags": chunk.quality_flags,
                }
                for chunk in self.chunks
            ],
            "diagnostics": self.diagnostics,
        }
        canonical = json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return _digest(canonical)


def compilation_id(extraction_id: str) -> str:
    identity = "\0".join((extraction_id, COMPILER, COMPILER_VERSION, CONFIG_DIGEST))
    return f"cmp-{_digest(identity)[:24]}"


def unit_id(compilation_ref: str, ordinal: int) -> str:
    identity = f"{compilation_ref}\0{ordinal}"
    return f"unit-{_digest(identity)[:24]}"


def chunk_ref(compilation_ref: str, ordinal: int) -> str:
    """Return the immutable public identity of one compiled retrieval chunk."""
    return f"chunk.{compilation_ref}.{ordinal:04d}"


def _positive_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= 0 else default


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _pages(item: dict[str, Any]) -> tuple[int | None, int | None]:
    pages = []
    for prov in item.get("prov") or []:
        if not isinstance(prov, dict):
            continue
        page = _positive_int(prov.get("page_no"))
        if page > 0:
            pages.append(page)
    return (min(pages), max(pages)) if pages else (None, None)


def _escape_table_text(value: str) -> str:
    return value.replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def _normalise_table(
    item: dict[str, Any],
) -> tuple[str, dict[str, Any], tuple[str, ...]]:
    data = item.get("data") if isinstance(item.get("data"), dict) else {}
    raw_cells = data.get("table_cells")
    if not isinstance(raw_cells, list):
        raw_cells = []
    num_rows = _positive_int(data.get("num_rows"))
    num_cols = _positive_int(data.get("num_cols"))
    flags: list[str] = []
    repairs: list[dict[str, Any]] = []

    if len(raw_cells) > MAX_TABLE_CELLS:
        raw_cells = raw_cells[:MAX_TABLE_CELLS]
        flags.append("table_cell_limit_exceeded")

    inferred_rows = 0
    inferred_cols = 0
    for raw in raw_cells:
        if not isinstance(raw, dict):
            continue
        start_row = _positive_int(raw.get("start_row_offset_idx"))
        start_col = _positive_int(raw.get("start_col_offset_idx"))
        end_row = _positive_int(raw.get("end_row_offset_idx"), start_row + 1)
        end_col = _positive_int(raw.get("end_col_offset_idx"), start_col + 1)
        inferred_rows = max(
            inferred_rows, end_row, start_row + _positive_int(raw.get("row_span"), 1)
        )
        inferred_cols = max(
            inferred_cols, end_col, start_col + _positive_int(raw.get("col_span"), 1)
        )
    num_rows = num_rows or inferred_rows
    num_cols = num_cols or inferred_cols

    if num_rows <= 0 or num_cols <= 0:
        flags.append("table_invalid_dimensions")
        text = "\n".join(
            str(cell.get("text") or "").strip()
            for cell in raw_cells
            if isinstance(cell, dict) and str(cell.get("text") or "").strip()
        )
        payload = {
            "num_rows": num_rows,
            "num_cols": num_cols,
            "cells": [],
            "header_paths": [],
            "repair_operations": [],
            "synthetic_content_flags": [],
            "integrity_score": 0.0,
        }
        return text, payload, _unique(flags)

    if num_rows > MAX_TABLE_DIMENSION or num_cols > MAX_TABLE_DIMENSION:
        flags.append("table_dimension_limit_exceeded")
        num_rows = min(num_rows, MAX_TABLE_DIMENSION)
        num_cols = min(num_cols, MAX_TABLE_DIMENSION)

    grid: list[list[int | None]] = [
        [None for _ in range(num_cols)] for _ in range(num_rows)
    ]
    cells: list[dict[str, Any]] = []
    occupied_work = 0
    for source_index, raw in enumerate(raw_cells):
        if not isinstance(raw, dict):
            flags.append("table_invalid_cell")
            continue
        row = _positive_int(raw.get("start_row_offset_idx"))
        col = _positive_int(raw.get("start_col_offset_idx"))
        end_row = _positive_int(raw.get("end_row_offset_idx"), row + 1)
        end_col = _positive_int(raw.get("end_col_offset_idx"), col + 1)
        row_span = _positive_int(raw.get("row_span"), end_row - row or 1)
        col_span = _positive_int(raw.get("col_span"), end_col - col or 1)
        declared_row_span = _int_or_none(raw.get("row_span"))
        declared_col_span = _int_or_none(raw.get("col_span"))
        offset_row_span = end_row - row if end_row > row else None
        offset_col_span = end_col - col if end_col > col else None
        mismatches: dict[str, dict[str, int]] = {}
        if (
            declared_row_span is not None
            and offset_row_span is not None
            and declared_row_span != offset_row_span
        ):
            mismatches["row"] = {
                "declared_span": declared_row_span,
                "offset_span": offset_row_span,
            }
            row_span = offset_row_span
        if (
            declared_col_span is not None
            and offset_col_span is not None
            and declared_col_span != offset_col_span
        ):
            mismatches["column"] = {
                "declared_span": declared_col_span,
                "offset_span": offset_col_span,
            }
            col_span = offset_col_span
        if mismatches:
            flags.append("table_span_offset_mismatch")
            repairs.append(
                {
                    "operation": "reconcile_span_with_offsets",
                    "source_index": source_index,
                    "mismatches": mismatches,
                }
            )
        original = (row, col, row_span, col_span)
        row_span = max(1, row_span)
        col_span = max(1, col_span)
        if row >= num_rows or col >= num_cols:
            flags.append("table_cell_out_of_bounds")
            repairs.append(
                {"operation": "drop_out_of_bounds_cell", "source_index": source_index}
            )
            continue
        row_span = min(row_span, num_rows - row)
        col_span = min(col_span, num_cols - col)
        if original != (row, col, row_span, col_span):
            flags.append("table_span_repaired")
            repairs.append(
                {
                    "operation": "clamp_span",
                    "source_index": source_index,
                    "from": list(original),
                    "to": [row, col, row_span, col_span],
                }
            )
        cell_area = row_span * col_span
        if occupied_work + cell_area > MAX_TABLE_OCCUPANCY:
            flags.append("table_occupancy_limit_exceeded")
            repairs.append(
                {
                    "operation": "limit_occupancy_projection",
                    "source_index": source_index,
                    "declared_area": cell_area,
                }
            )
            positions = [(row, col)]
        else:
            occupied_work += cell_area
            positions = [
                (r, c)
                for r in range(row, row + row_span)
                for c in range(col, col + col_span)
            ]
        occupied = [(r, c) for r, c in positions if grid[r][c] is not None]
        if occupied:
            flags.append("table_cell_overlap")
            repairs.append(
                {
                    "operation": "preserve_cell_without_overwriting",
                    "source_index": source_index,
                    "occupied": [list(position) for position in occupied[:20]],
                }
            )
        cell = {
            "row": row,
            "column": col,
            "rowspan": row_span,
            "colspan": col_span,
            "source_offsets": {
                "start_row": _positive_int(raw.get("start_row_offset_idx")),
                "end_row": _positive_int(raw.get("end_row_offset_idx"), row + row_span),
                "start_column": _positive_int(raw.get("start_col_offset_idx")),
                "end_column": _positive_int(
                    raw.get("end_col_offset_idx"), col + col_span
                ),
            },
            "bbox": raw.get("bbox") if isinstance(raw.get("bbox"), dict) else None,
            "text": str(raw.get("text") or ""),
            "column_header": bool(raw.get("column_header")),
            "row_header": bool(raw.get("row_header")),
            "row_section": bool(raw.get("row_section")),
        }
        cell_index = len(cells)
        cells.append(cell)
        for r, c in positions:
            if grid[r][c] is None:
                grid[r][c] = cell_index

    holes = sum(value is None for row in grid for value in row)
    if holes:
        flags.append("table_grid_holes")

    rendered: list[list[str]] = []
    for row_index in range(num_rows):
        rendered_row: list[str] = []
        for col_index in range(num_cols):
            cell_index = grid[row_index][col_index]
            if cell_index is None:
                rendered_row.append("")
                continue
            cell = cells[cell_index]
            is_anchor = cell["row"] == row_index and cell["column"] == col_index
            rendered_row.append(_escape_table_text(cell["text"]) if is_anchor else "")
        rendered.append(rendered_row)

    header_rows = sorted({cell["row"] for cell in cells if cell["column_header"]})
    synthetic_flags: list[str] = []
    if not header_rows:
        synthetic_flags.append("markdown_empty_header")
        ordered_rows = [["" for _ in range(num_cols)], *rendered]
    else:
        ordered_rows = rendered
        if header_rows[0] != 0:
            synthetic_flags.append("markdown_first_row_header_projection")

    markdown_lines = ["| " + " | ".join(row) + " |" for row in ordered_rows[:1]]
    markdown_lines.append("| " + " | ".join("---" for _ in range(num_cols)) + " |")
    markdown_lines.extend("| " + " | ".join(row) + " |" for row in ordered_rows[1:])

    header_paths: list[list[str]] = []
    for col in range(num_cols):
        path = []
        for cell in cells:
            if (
                cell["column_header"]
                and cell["column"] <= col < cell["column"] + cell["colspan"]
                and cell["text"].strip()
            ):
                path.append(cell["text"].strip())
        header_paths.append(list(dict.fromkeys(path)))

    penalty = min(0.75, 0.12 * len(repairs))
    if holes:
        penalty += min(0.2, holes / max(1, num_rows * num_cols) * 0.2)
    integrity_score = round(max(0.0, 1.0 - penalty), 3)
    payload = {
        "num_rows": num_rows,
        "num_cols": num_cols,
        "cells": cells,
        "header_paths": header_paths,
        "repair_operations": repairs,
        "synthetic_content_flags": synthetic_flags,
        "integrity_score": integrity_score,
    }
    return "\n".join(markdown_lines), payload, _unique(flags)


def _ref(value: Any) -> str | None:
    if isinstance(value, dict):
        candidate = value.get("$ref") or value.get("cref")
        return candidate if isinstance(candidate, str) else None
    return value if isinstance(value, str) else None


def _docling_heading_level(item: dict[str, Any], label: str) -> int:
    for key in ("level", "heading_level"):
        level = _positive_int(item.get(key))
        if level > 0:
            return min(level, 6)
    return 1 if label == "title" else 2


def _docling_units(
    document: dict[str, Any],
) -> tuple[list[StructuredUnit], list[str]] | None:
    body = document.get("body")
    if not isinstance(body, dict) or not isinstance(body.get("children"), list):
        return None

    ref_map: dict[str, dict[str, Any]] = {}
    for collection_name in (
        "texts",
        "tables",
        "pictures",
        "groups",
        "key_value_items",
        "form_items",
    ):
        collection = document.get(collection_name) or []
        if not isinstance(collection, list):
            continue
        for item in collection:
            if isinstance(item, dict) and isinstance(item.get("self_ref"), str):
                ref_map[item["self_ref"]] = item

    units: list[StructuredUnit] = []
    flags: list[str] = []
    visited: set[str] = set()
    heading_stack: list[tuple[int, str]] = []

    def visit(reference: Any) -> None:
        locator = _ref(reference)
        if not locator or locator in visited:
            return
        visited.add(locator)
        item = ref_map.get(locator)
        if item is None:
            flags.append("docling_unresolved_reference")
            return
        label = str(item.get("label") or "").lower()
        page_start, page_end = _pages(item)

        if locator.startswith("#/groups/") or label in {
            "list",
            "ordered_list",
            "unordered_list",
            "chapter",
            "section",
        }:
            for child in item.get("children") or []:
                visit(child)
            return

        if locator.startswith("#/tables/") or label == "table":
            text, table_data, table_flags = _normalise_table(item)
            if text.strip():
                units.append(
                    StructuredUnit(
                        content_type="table",
                        text=text,
                        structural_locator=locator,
                        page_start=page_start,
                        page_end=page_end,
                        parent_heading=(heading_stack[-1][1] if heading_stack else None),
                        section_path=tuple(text for _, text in heading_stack),
                        quality_flags=table_flags,
                        table_data=table_data,
                    )
                )
            else:
                flags.append("table_without_retrievable_text")
            for child in [
                *(item.get("captions") or []),
                *(item.get("footnotes") or []),
            ]:
                visit(child)
            return

        if locator.startswith("#/pictures/") or label == "picture":
            for child in [
                *(item.get("captions") or []),
                *(item.get("children") or []),
                *(item.get("footnotes") or []),
            ]:
                visit(child)
            return

        text = str(item.get("text") or "").strip()
        if text:
            if label in {"title", "section_header", "heading", "subtitle"}:
                content_type = "heading"
            elif label == "list_item":
                content_type = "list"
            elif label in {"caption", "figure_caption"}:
                content_type = "figure_caption"
            else:
                content_type = "paragraph"
            heading_level = None
            section_path = tuple(value for _, value in heading_stack)
            parent_heading = heading_stack[-1][1] if heading_stack else None
            if content_type == "heading":
                heading_level = _docling_heading_level(item, label)
                while heading_stack and heading_stack[-1][0] >= heading_level:
                    heading_stack.pop()
                parent_heading = heading_stack[-1][1] if heading_stack else None
                section_path = (*[value for _, value in heading_stack], text)
            units.append(
                StructuredUnit(
                    content_type=content_type,
                    text=text,
                    structural_locator=locator,
                    page_start=page_start,
                    page_end=page_end,
                    parent_heading=parent_heading,
                    heading_level=heading_level,
                    section_path=tuple(section_path),
                )
            )
            if content_type == "heading":
                heading_stack.append((heading_level or 1, text))
        for child in item.get("children") or []:
            visit(child)

    for child in body["children"]:
        visit(child)
    if not units:
        return None
    return units, flags


_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_LIST_ITEM = re.compile(r"^\s*(?:[-*+] |\d+[.)] ).+")
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?…])(?:[ \t]+|\n+)")


def _looks_like_table(lines: list[str]) -> bool:
    if len(lines) < 2 or not all("|" in line for line in lines):
        return False
    separator = lines[1].strip().strip("|").split("|")
    return bool(separator) and all(
        re.fullmatch(r"\s*:?-{3,}:?\s*", cell) for cell in separator
    )


def _markdown_table(lines: list[str]) -> dict[str, Any]:
    rows = [line.strip().strip("|").split("|") for line in lines]
    if len(rows) >= 2:
        rows.pop(1)
    width = max((len(row) for row in rows), default=0)
    cells = []
    for row_index, row in enumerate(rows):
        for col_index in range(width):
            cells.append(
                {
                    "row": row_index,
                    "column": col_index,
                    "rowspan": 1,
                    "colspan": 1,
                    "text": row[col_index].strip() if col_index < len(row) else "",
                    "column_header": row_index == 0,
                    "row_header": False,
                    "row_section": False,
                }
            )
    return {
        "num_rows": len(rows),
        "num_cols": width,
        "cells": cells,
        "header_paths": [
            [rows[0][col].strip()] if rows and col < len(rows[0]) else []
            for col in range(width)
        ],
        "repair_operations": [],
        "synthetic_content_flags": [],
        "integrity_score": 1.0,
    }


def _markdown_units(markdown: str) -> list[StructuredUnit]:
    lines = markdown.splitlines()
    units: list[StructuredUnit] = []
    heading_stack: list[tuple[int, str]] = []
    index = 0
    block_no = 0
    while index < len(lines):
        if not lines[index].strip():
            index += 1
            continue
        line = lines[index]
        heading = _HEADING.match(line)
        locator = f"markdown:block-{block_no}"
        block_no += 1
        if heading:
            text = heading.group(2).strip()
            heading_level = len(heading.group(1))
            while heading_stack and heading_stack[-1][0] >= heading_level:
                heading_stack.pop()
            parent_heading = heading_stack[-1][1] if heading_stack else None
            section_path = (*[value for _, value in heading_stack], text)
            units.append(
                StructuredUnit(
                    content_type="heading",
                    text=text,
                    structural_locator=locator,
                    parent_heading=parent_heading,
                    heading_level=heading_level,
                    section_path=tuple(section_path),
                )
            )
            heading_stack.append((heading_level, text))
            index += 1
            continue
        block = [line]
        index += 1
        while index < len(lines) and lines[index].strip():
            if _HEADING.match(lines[index]):
                break
            block.append(lines[index])
            index += 1
        if _looks_like_table(block):
            content_type = "table"
            table_data = _markdown_table(block)
        elif all(_LIST_ITEM.match(value) for value in block):
            content_type = "list"
            table_data = None
        else:
            content_type = "paragraph"
            table_data = None
        text = "\n".join(block).strip()
        if text:
            units.append(
                StructuredUnit(
                    content_type=content_type,
                    text=text,
                    structural_locator=locator,
                    parent_heading=(heading_stack[-1][1] if heading_stack else None),
                    section_path=tuple(value for _, value in heading_stack),
                    table_data=table_data,
                )
            )
    return units


def _projection_locator(units: list[StructuredUnit], ordinals: list[int]) -> str:
    first = units[ordinals[0]].structural_locator
    last = units[ordinals[-1]].structural_locator
    return first if first == last else f"{first}..{last}"


def _with_section_context(text: str, section_path: tuple[str, ...]) -> str:
    if not section_path:
        return text
    return f"Section: {' > '.join(section_path)}\n\n{text}"


def _content_budget(section_path: tuple[str, ...]) -> int:
    prefix_length = len(_with_section_context("", section_path))
    return max(1, MAX_RETRIEVAL_CHARS - prefix_length)


def _hard_wrap_text(text: str, limit: int) -> list[str]:
    remaining = text.strip()
    if not remaining:
        return []
    if limit <= 0:
        return [remaining]
    parts: list[str] = []
    while len(remaining) > limit:
        cut = max(
            remaining.rfind("\n", 0, limit + 1),
            remaining.rfind(" ", 0, limit + 1),
            remaining.rfind("\t", 0, limit + 1),
        )
        if cut < max(1, limit // 3):
            cut = limit
        part = remaining[:cut].strip()
        if part:
            parts.append(part)
        remaining = remaining[cut:].strip()
    if remaining:
        parts.append(remaining)
    return parts


def _pack_segments(segments: list[str], limit: int, separator: str) -> list[str]:
    expanded: list[str] = []
    for segment in segments:
        cleaned = segment.strip()
        if not cleaned:
            continue
        if len(cleaned) <= limit:
            expanded.append(cleaned)
        else:
            expanded.extend(_hard_wrap_text(cleaned, limit))

    parts: list[str] = []
    current: list[str] = []
    for segment in expanded:
        candidate = separator.join([*current, segment])
        if current and len(candidate) > limit:
            parts.append(separator.join(current))
            current = [segment]
        else:
            current.append(segment)
    if current:
        parts.append(separator.join(current))
    return parts


def _split_text_unit(unit: StructuredUnit) -> list[str]:
    limit = _content_budget(unit.section_path)
    if len(unit.text) <= limit:
        return [unit.text]
    if unit.content_type == "list":
        return _pack_segments(
            [line for line in unit.text.splitlines() if line.strip()],
            limit,
            "\n",
        )

    sentences = [
        value.strip() for value in _SENTENCE_BOUNDARY.split(unit.text) if value.strip()
    ]
    if len(sentences) <= 1 and "\n" in unit.text:
        sentences = [line.strip() for line in unit.text.splitlines() if line.strip()]
    if len(sentences) <= 1:
        return _hard_wrap_text(unit.text, limit)
    return _pack_segments(sentences, limit, " ")


def _table_schema_text(unit: StructuredUnit) -> str:
    if not isinstance(unit.table_data, dict):
        return ""
    header_paths = unit.table_data.get("header_paths")
    if not isinstance(header_paths, list):
        return ""
    labels: list[str] = []
    for path in header_paths:
        if not isinstance(path, list):
            continue
        parts = [str(value).strip() for value in path if str(value).strip()]
        if parts:
            labels.append(" > ".join(parts))
    if not labels:
        return ""
    schema = "Table schema: " + " | ".join(labels)
    if len(schema) > MAX_TABLE_SCHEMA_CHARS:
        return schema[: MAX_TABLE_SCHEMA_CHARS - 3].rstrip() + "..."
    return schema


def _table_projection_parts(
    unit: StructuredUnit,
) -> list[tuple[str, tuple[str, ...]]]:
    full_text = _with_section_context(unit.text, unit.section_path)
    if len(full_text) <= MAX_RETRIEVAL_CHARS:
        return [(full_text, unit.quality_flags)]

    lines = unit.text.splitlines()
    if len(lines) < 2:
        return [
            (
                full_text,
                _unique([*unit.quality_flags, "retrieval_limit_exceeded"]),
            )
        ]

    header, separator, *rows = lines
    schema = _table_schema_text(unit)
    repeated_prefix = [value for value in (schema, header, separator) if value]

    def render(selected_rows: list[str]) -> str:
        return _with_section_context(
            "\n".join([*repeated_prefix, *selected_rows]), unit.section_path
        )

    if not rows:
        rendered = render([])
        flags = unit.quality_flags
        if len(rendered) > MAX_RETRIEVAL_CHARS:
            flags = _unique([*flags, "retrieval_limit_exceeded"])
        return [(rendered, flags)]

    parts: list[tuple[str, tuple[str, ...]]] = []
    current_rows: list[str] = []
    for row in rows:
        candidate = render([*current_rows, row])
        if current_rows and len(candidate) > MAX_RETRIEVAL_CHARS:
            parts.append((render(current_rows), unit.quality_flags))
            current_rows = [row]
        else:
            current_rows.append(row)

        if current_rows and len(render(current_rows)) > MAX_RETRIEVAL_CHARS:
            parts.append(
                (
                    render(current_rows),
                    _unique([*unit.quality_flags, "retrieval_limit_exceeded"]),
                )
            )
            current_rows = []

    if current_rows:
        parts.append((render(current_rows), unit.quality_flags))
    return parts


def _single_unit_projection(
    unit: StructuredUnit,
    ordinal: int,
    *,
    text: str,
    quality_flags: tuple[str, ...] | None = None,
) -> RetrievalProjection:
    return RetrievalProjection(
        text=text,
        content_type=unit.content_type,
        structural_locator=unit.structural_locator,
        unit_ordinals=(ordinal,),
        page_start=unit.page_start,
        page_end=unit.page_end,
        parent_heading=unit.parent_heading,
        section_path=unit.section_path,
        quality_flags=unit.quality_flags if quality_flags is None else quality_flags,
    )


def _build_projections(units: list[StructuredUnit]) -> list[RetrievalProjection]:
    projections: list[RetrievalProjection] = []
    pending_ordinals: list[int] = []
    pending_text: list[str] = []
    pending_type: str | None = None
    pending_heading: str | None = None
    pending_section_path: tuple[str, ...] = ()

    def flush() -> None:
        nonlocal pending_ordinals, pending_text, pending_type, pending_heading
        nonlocal pending_section_path
        if not pending_ordinals:
            return
        selected = [units[ordinal] for ordinal in pending_ordinals]
        pages = [
            page
            for unit in selected
            for page in (unit.page_start, unit.page_end)
            if page
        ]
        flags = _unique(flag for unit in selected for flag in unit.quality_flags)
        projections.append(
            RetrievalProjection(
                text=_with_section_context(
                    "\n\n".join(pending_text), pending_section_path
                ),
                content_type=pending_type or "page_fragment",
                structural_locator=_projection_locator(units, pending_ordinals),
                unit_ordinals=tuple(pending_ordinals),
                page_start=min(pages) if pages else None,
                page_end=max(pages) if pages else None,
                parent_heading=pending_heading,
                section_path=pending_section_path,
                quality_flags=flags,
            )
        )
        pending_ordinals = []
        pending_text = []
        pending_type = None
        pending_heading = None
        pending_section_path = ()

    headings: list[int] = []
    for ordinal, unit in enumerate(units):
        if unit.content_type == "heading":
            headings.append(ordinal)
            continue
        if unit.content_type == "table":
            flush()
            for text, flags in _table_projection_parts(unit):
                projections.append(
                    _single_unit_projection(
                        unit,
                        ordinal,
                        text=text,
                        quality_flags=flags,
                    )
                )
            continue

        unit_projection = _with_section_context(unit.text, unit.section_path)
        if len(unit_projection) > MAX_RETRIEVAL_CHARS:
            flush()
            for part in _split_text_unit(unit):
                text = _with_section_context(part, unit.section_path)
                flags = unit.quality_flags
                if len(text) > MAX_RETRIEVAL_CHARS:
                    flags = _unique([*flags, "retrieval_limit_exceeded"])
                projections.append(
                    _single_unit_projection(
                        unit,
                        ordinal,
                        text=text,
                        quality_flags=flags,
                    )
                )
            continue

        candidate_length = len(
            _with_section_context(
                "\n\n".join([*pending_text, unit.text]), unit.section_path
            )
        )
        same_context = (
            pending_section_path == unit.section_path if pending_ordinals else True
        )
        if pending_ordinals and (
            candidate_length > MAX_RETRIEVAL_CHARS or not same_context
        ):
            flush()
        pending_ordinals.append(ordinal)
        pending_text.append(unit.text)
        pending_heading = unit.parent_heading
        pending_section_path = unit.section_path
        pending_type = (
            unit.content_type
            if pending_type in {None, unit.content_type}
            else "page_fragment"
        )
    flush()
    if not projections and headings:
        selected = [units[ordinal] for ordinal in headings]
        projections.append(
            RetrievalProjection(
                text="\n\n".join(unit.text for unit in selected),
                content_type="heading",
                structural_locator=_projection_locator(units, headings),
                unit_ordinals=tuple(headings),
            )
        )
    return projections


def compile_document(
    *,
    markdown: str,
    document_json: dict[str, Any],
    converter: str,
) -> CompilationResult:
    """Compile one observed conversion without reaching outside its payload."""
    quality_flags: list[str] = []
    parsed = None
    if (
        converter == "docling_serve"
        or document_json.get("schema_name") == "DoclingDocument"
    ):
        parsed = _docling_units(document_json)
        if parsed is None:
            quality_flags.append("structured_json_fallback")
    if parsed is None:
        units = _markdown_units(markdown)
        structural_flags: list[str] = []
    else:
        units, structural_flags = parsed
        quality_flags.extend(structural_flags)
    if not units:
        raise ValueError("structured compilation produced no retrievable units")
    chunks = _build_projections(units)
    if not chunks:
        raise ValueError("structured compilation produced no retrieval projections")
    global_flags = _unique(quality_flags)
    unit_flags = [flag for unit in units for flag in unit.quality_flags]
    quality_flags = list(_unique([*quality_flags, *unit_flags]))
    diagnostics = [
        {"code": flag, "scope": "compilation"} for flag in global_flags
    ]
    diagnostics.extend(
        {
            "code": flag,
            "scope": "unit",
            "unit_ordinal": ordinal,
            "structural_locator": unit.structural_locator,
        }
        for ordinal, unit in enumerate(units)
        for flag in unit.quality_flags
    )
    pages = [
        page for unit in units for page in (unit.page_start, unit.page_end) if page
    ]
    declared_pages = document_json.get("pages")
    page_count = (
        len(declared_pages)
        if isinstance(declared_pages, dict)
        else (max(pages) if pages else 0)
    )
    table_count = sum(unit.content_type == "table" for unit in units)
    return CompilationResult(
        units=tuple(units),
        chunks=tuple(chunks),
        status="needs_review" if quality_flags else "ready",
        quality_flags=tuple(quality_flags),
        page_count=page_count,
        table_count=table_count,
        anomaly_count=len(diagnostics),
        diagnostics=tuple(diagnostics),
    )
