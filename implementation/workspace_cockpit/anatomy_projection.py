"""Read the Anatomy projection a Project owner published, for the back of an affaire card.

The implementation writes ``<WORKSPACE_ANATOMY_DIR>/<CODE>.json``
(``pantheon.anatomy.v1``) after each APU write. The Cockpit only reads it, as it
reads the OTEL snapshot: bounded size, checked schema, and a rebuilt wire shape
that forwards only what the card shows. Nothing here reaches the database.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

SCHEMA = "pantheon.anatomy.v1"
MAX_BYTES = 2 * 1024 * 1024
_CODE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


def _claim(item: dict[str, Any]) -> dict[str, Any]:
    value = item.get("value") if isinstance(item.get("value"), dict) else {}
    return {
        "key": item.get("attribute_key") or item.get("relation_type"),
        "value": value.get("value"),
        "unit": value.get("unit"),
        "certainty": item.get("certainty"),
        "proof_status": item.get("proof_status"),
        "assertion_mode": item.get("assertion_mode"),
        "object_ref": (item.get("object_ref") or {}).get("entity_id"),
        "subject_ref": (item.get("subject_ref") or {}).get("entity_id"),
        "qualifier": item.get("qualifier") if isinstance(item.get("qualifier"), dict) else {},
        "sources": list(item.get("source_representation_refs") or []),
    }


def read_anatomy(directory: Path | None, code: str) -> dict[str, Any]:
    if directory is None:
        return {"available": False, "error": "anatomy_not_configured"}
    if not _CODE.fullmatch(code or ""):
        return {"available": False, "error": "invalid_code"}
    path = directory / f"{code}.json"
    try:
        with path.open("rb") as file:
            raw = file.read(MAX_BYTES + 1)
    except FileNotFoundError:
        return {"available": False, "error": "no_anatomy"}
    except OSError:
        return {"available": False, "error": "anatomy_unavailable"}
    try:
        if len(raw) > MAX_BYTES:
            raise ValueError("oversize")
        data = json.loads(raw)
        if data.get("schema") != SCHEMA or (data.get("project") or {}).get("code") != code:
            raise ValueError("schema")
        anatomy = data["anatomy"]
        sources = {
            item.get("representation_id"): {
                "page": item.get("context", {}).get("page") if isinstance(item.get("context"), dict) else None,
                "kind": item.get("source_kind"),
                "identity_pending": not item.get("mapped_object_refs"),
            }
            for item in anatomy.get("sources") or []
        }
        objects = [
            {
                "id": item.get("object_id"),
                "family": item.get("object_family"),
                "name": item.get("display_name"),
                "code": item.get("internal_code"),
                "attributes": [_claim(claim) for claim in item.get("attribute_claims") or []],
                "relations": [_claim(claim) for claim in item.get("relations") or []],
            }
            for item in (anatomy.get("structure") or {}).get("objects") or []
        ]
        return {
            "available": True,
            "schema": SCHEMA,
            "generated_at": data.get("generated_at"),
            "project": {key: data["project"].get(key) for key in ("project_id", "code", "display_name")},
            "summary": dict(anatomy.get("summary") or {}),
            "objects": objects,
            "sources": sources,
            "phases": {"status": (anatomy.get("phases") or {}).get("status")},
        }
    except (ValueError, TypeError, KeyError, AttributeError):
        return {"available": False, "error": "anatomy_unreadable"}
