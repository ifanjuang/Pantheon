#!/usr/bin/env python3
"""Compact a Hindsight/MCP JSON spillover into a bounded list of records."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any, Iterable


TEXT_KEYS = ("text", "content", "memory", "excerpt", "summary", "chunk")
DOCUMENT_KEYS = ("document_id", "documentId", "source_document_id")
PATH_KEYS = ("path", "file_path", "filepath", "source")
ID_KEYS = ("id", "memory_id", "record_id")
SCORE_KEYS = ("score", "relevance", "similarity", "distance")


def parse_payload(raw: str) -> Any:
    """Parse JSON first, then a safe Python literal, else retain raw text."""
    for parser in (json.loads, ast.literal_eval):
        try:
            return parser(raw)
        except (ValueError, SyntaxError):
            pass
    return raw


def nested_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def first_value(mapping: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def scalar_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    return ""


def candidate_from(mapping: dict[str, Any], max_text: int) -> dict[str, Any] | None:
    metadata = nested_mapping(mapping.get("metadata"))

    text = scalar_text(first_value(mapping, TEXT_KEYS))
    if not text:
        text = scalar_text(first_value(metadata, TEXT_KEYS))

    document_id = scalar_text(first_value(mapping, DOCUMENT_KEYS))
    if not document_id:
        document_id = scalar_text(first_value(metadata, DOCUMENT_KEYS))

    path = scalar_text(first_value(mapping, PATH_KEYS))
    if not path:
        path = scalar_text(first_value(metadata, PATH_KEYS))

    record_id = scalar_text(first_value(mapping, ID_KEYS))
    score = first_value(mapping, SCORE_KEYS)

    if not any((text, document_id, path)):
        return None

    result: dict[str, Any] = {}
    if document_id:
        result["document_id"] = document_id
    if path and path != document_id:
        result["path"] = path
    if record_id and record_id not in (document_id, path):
        result["record_id"] = record_id
    if text:
        result["text"] = text[:max_text]
        if len(text) > max_text:
            result["text_truncated"] = True
    if isinstance(score, (int, float)):
        result["score"] = score
    return result


def walk(value: Any, max_text: int, depth: int = 0) -> Iterable[dict[str, Any]]:
    if depth > 30:
        return

    if isinstance(value, dict):
        candidate = candidate_from(value, max_text)
        if candidate:
            yield candidate
        for child in value.values():
            yield from walk(child, max_text, depth + 1)
        return

    if isinstance(value, list):
        for child in value:
            yield from walk(child, max_text, depth + 1)
        return

    if isinstance(value, str) and depth < 8:
        stripped = value.strip()
        if stripped.startswith(("{", "[")):
            parsed = parse_payload(stripped)
            if not isinstance(parsed, str):
                yield from walk(parsed, max_text, depth + 1)


def identity(record: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(record.get("document_id", "")),
        str(record.get("path", "")),
        str(record.get("text", "")),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Hindsight/MCP result file")
    parser.add_argument("--max-items", type=int, default=10)
    parser.add_argument("--max-text", type=int, default=800)
    parser.add_argument(
        "--contains",
        action="append",
        default=[],
        help="Keep records containing this literal term (repeatable, OR logic)",
    )
    args = parser.parse_args()

    if args.max_items < 1 or args.max_text < 1:
        parser.error("--max-items and --max-text must be positive")

    payload = parse_payload(args.input.read_text(encoding="utf-8", errors="replace"))
    terms = [term.casefold() for term in args.contains if term.strip()]
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    for record in walk(payload, args.max_text):
        searchable = " ".join(str(value) for value in record.values()).casefold()
        if terms and not any(term in searchable for term in terms):
            continue
        key = identity(record)
        if key in seen:
            continue
        seen.add(key)
        records.append(record)
        if len(records) >= args.max_items:
            break

    print(json.dumps({"count": len(records), "items": records}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
