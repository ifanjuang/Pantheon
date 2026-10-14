"""Read-only resource profiles for cards-first projections.

The profile describes what was observed in an existing extraction and which web
addresses are already written in Knowledge Markdown. It does not crawl a site,
fetch a URL, vectorize web content, broaden project scope or turn a link into
Evidence.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import PurePosixPath
from urllib.parse import urlsplit, urlunsplit

import psycopg
from psycopg.rows import dict_row


_URL_RE = re.compile(r"https?://[^\s<>{}\"'`]+", re.IGNORECASE)
_IMAGE_TERMS = {"image", "picture", "figure", "illustration", "graphic"}
_TABLE_TERMS = {"table"}
_TEXT_TERMS = {
    "text", "paragraph", "title", "heading", "caption", "list_item", "section",
}
_SEMANTIC_KEYS = {"type", "label", "kind", "name", "element_type", "doc_item_label"}


class ResourceProfileError(ValueError):
    """A project resource profile cannot be produced within the declared scope."""


def _normalized_term(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")


def _walk_semantic_terms(value: object) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            key_term = _normalized_term(key)
            if key_term in _SEMANTIC_KEYS and isinstance(child, (str, int, float)):
                yield _normalized_term(child)
            yield from _walk_semantic_terms(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_semantic_terms(child)


def _matches(term: str, candidates: set[str]) -> bool:
    pieces = set(filter(None, term.split("_")))
    return bool(pieces & candidates) or term in candidates


def _format_family(media_type: str, extension: str) -> str:
    media = (media_type or "").lower()
    ext = (extension or "").lower().lstrip(".")
    if media == "application/pdf" or ext == "pdf":
        return "pdf"
    if media.startswith("image/") or ext in {"jpg", "jpeg", "png", "webp", "tif", "tiff", "svg"}:
        return "image"
    if media.startswith("text/") or ext in {"md", "markdown", "txt", "csv"}:
        return "text"
    if ext in {"doc", "docx", "odt", "rtf"}:
        return "word_processing"
    if ext in {"xls", "xlsx", "ods"}:
        return "spreadsheet"
    if ext in {"ppt", "pptx", "odp"}:
        return "presentation"
    if ext in {"zip", "7z", "rar", "tar", "gz"}:
        return "archive"
    return "other"


def document_content_profile(
    *,
    source_ref: str,
    media_type: str,
    extension: str | None,
    markdown_content: str | None,
    document_json: object,
) -> dict:
    """Describe observed composition without claiming exhaustive source inspection."""
    resolved_extension = (extension or PurePosixPath(source_ref).suffix).lower().lstrip(".")
    format_family = _format_family(media_type, resolved_extension)
    terms = list(_walk_semantic_terms(document_json or {}))
    image_count = sum(1 for term in terms if _matches(term, _IMAGE_TERMS))
    table_count = sum(1 for term in terms if _matches(term, _TABLE_TERMS))
    structured_text_count = sum(1 for term in terms if _matches(term, _TEXT_TERMS))
    has_text = bool((markdown_content or "").strip())
    has_images = format_family == "image" or image_count > 0
    has_tables = table_count > 0

    if format_family == "image" and has_text:
        composition = "image_with_extracted_text"
    elif has_images and has_text:
        composition = "text_and_images"
    elif has_tables and has_text:
        composition = "structured_text"
    elif has_text:
        composition = "text_only"
    elif has_images:
        composition = "images_only"
    else:
        composition = "unknown"

    return {
        "format": {
            "extension": resolved_extension or None,
            "media_type": media_type,
            "family": format_family,
        },
        "content": {
            "composition": composition,
            "has_text": has_text,
            "has_images": has_images,
            "has_tables": has_tables,
            "observed_image_items": image_count,
            "observed_table_items": table_count,
            "observed_structured_text_items": structured_text_count,
            "basis": "derived_extraction_json_and_markdown",
            "exhaustive": False,
        },
    }


def _trim_trailing_delimiters(value: str) -> str:
    candidate = value.rstrip(".,;:!?")
    for opening, closing in (("(", ")"), ("[", "]"), ("{", "}")):
        while candidate.endswith(closing) and candidate.count(closing) > candidate.count(opening):
            candidate = candidate[:-1]
    return candidate


def _canonical_url(value: str) -> str | None:
    candidate = _trim_trailing_delimiters(value)
    parsed = urlsplit(candidate)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return None
    host = parsed.hostname.lower().rstrip(".")
    try:
        port_value = parsed.port
    except ValueError:
        return None
    authority_host = f"[{host}]" if ":" in host else host
    port = f":{port_value}" if port_value is not None else ""
    path = parsed.path or "/"
    return urlunsplit((parsed.scheme.lower(), authority_host + port, path, parsed.query, ""))


def _site_kind(host: str) -> str:
    host = host.lower()
    if host == "legifrance.gouv.fr" or host.endswith(".legifrance.gouv.fr"):
        return "legal_reference"
    if "sitesecurite" in host:
        return "safety_reference"
    if any(token in host for token in ("geodata", "geoportail", "cadastre")):
        return "geodata"
    if host == "data.gouv.fr" or host.endswith(".data.gouv.fr"):
        return "public_data"
    if host.endswith(".gouv.fr"):
        return "official_public_site"
    return "general_web"


def extract_linked_sites(markdown: str) -> list[dict]:
    """Return a stable address list; no network request is performed."""
    seen: set[str] = set()
    sites: list[dict] = []
    for raw in _URL_RE.findall(markdown or ""):
        url = _canonical_url(raw)
        if url is None or url in seen:
            continue
        seen.add(url)
        host = urlsplit(url).hostname or ""
        sites.append(
            {
                "url": url,
                "host": host,
                "site_kind": _site_kind(host),
                "retrieval_profile": {
                    "mode": "address_only",
                    "crawl_status": "not_authorized",
                    "vector_status": "not_indexed",
                    "structure_indexed": False,
                },
            }
        )
    return sites


def _knowledge_site_profiles(rows: list[dict]) -> list[dict]:
    profiles: list[dict] = []
    for row in rows:
        sites = extract_linked_sites(row.get("markdown") or "")
        if sites:
            profiles.append({"knowledge_id": row["knowledge_id"], "sites": sites})
    return profiles


def list_project_resource_profiles(
    conn: psycopg.Connection,
    parent_project_id: str,
) -> dict:
    """Return exact-project document composition and Knowledge-linked addresses."""
    parent_project_id = parent_project_id.strip()
    if not parent_project_id:
        raise ResourceProfileError("parent_project_id is required")

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT d.document_id, d.source_ref, d.media_type, n.extension,
                   e.markdown_content, e.document_json
              FROM source_documents d
              LEFT JOIN document_naming n ON n.document_id = d.document_id
              LEFT JOIN extraction_runs e ON e.extraction_id = d.current_extraction_id
             WHERE d.parent_project_id = %s
             ORDER BY d.updated_at DESC, d.document_id
            """,
            (parent_project_id,),
        )
        documents = [dict(row) for row in cur.fetchall()]
        cur.execute(
            """
            SELECT k.knowledge_id, k.markdown
              FROM knowledge_items k
              JOIN source_documents d ON d.document_id = k.document_id
             WHERE d.parent_project_id = %s
             ORDER BY k.updated_at DESC, k.knowledge_id
            """,
            (parent_project_id,),
        )
        knowledge_rows = [dict(row) for row in cur.fetchall()]

    return {
        "parent_project_id": parent_project_id,
        "scope_match": "exact_parent_project_id",
        "documents": [
            {
                "document_id": row["document_id"],
                **document_content_profile(
                    source_ref=row["source_ref"],
                    media_type=row["media_type"],
                    extension=row.get("extension"),
                    markdown_content=row.get("markdown_content"),
                    document_json=row.get("document_json"),
                ),
            }
            for row in documents
        ],
        "knowledge_sites": _knowledge_site_profiles(knowledge_rows),
        "crawl_capability": {
            "status": "documented_not_implemented",
            "candidate_modes": [
                "address_only",
                "structure_only",
                "selected_pages",
                "full_content",
            ],
            "default_mode": "address_only",
            "requires_human_scope_approval": True,
        },
    }
