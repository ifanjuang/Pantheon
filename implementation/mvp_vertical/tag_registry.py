"""Validated contextual tag vocabulary shared by Cockpit and Hermes handoffs.

Tags orient presentation and bounded context. They do not establish truth,
Evidence, approval, scope expansion or task authorization.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


REGISTRY = (
    Path(__file__).resolve().parent
    / "cockpit"
    / "registries"
    / "tag_registry.json"
)
SCHEMA_ID = "cockpit.tag_registry"
REVISION = 1
MAX_SUBJECT_TAGS = 5


class TagRegistryError(ValueError):
    """The shared tag vocabulary is unavailable or structurally invalid."""


def _slug(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = (
        text.replace("à", "a")
        .replace("â", "a")
        .replace("ä", "a")
        .replace("ç", "c")
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("ë", "e")
        .replace("î", "i")
        .replace("ï", "i")
        .replace("ô", "o")
        .replace("ö", "o")
        .replace("ù", "u")
        .replace("û", "u")
        .replace("ü", "u")
    )
    return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", text))


def _string_list(value: Any, *, limit: int | None = None) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    seen: set[str] = set()
    for raw in value:
        item = _slug(raw)
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
        if limit is not None and len(result) >= limit:
            break
    return result


@lru_cache(maxsize=1)
def load_registry() -> dict[str, Any]:
    try:
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TagRegistryError(f"tag registry is unavailable or invalid: {exc}") from exc

    if payload.get("schema_id") != SCHEMA_ID or payload.get("revision") != REVISION:
        raise TagRegistryError("unsupported tag registry identity")
    groups = payload.get("groups")
    tags = payload.get("tags")
    if not isinstance(groups, list) or not isinstance(tags, list):
        raise TagRegistryError("tag registry requires groups and tags arrays")

    group_ids: set[str] = set()
    group_map: dict[str, dict[str, Any]] = {}
    for raw in groups:
        if not isinstance(raw, dict):
            raise TagRegistryError("tag groups must be objects")
        group_id = str(raw.get("id") or "").strip()
        if not group_id or group_id in group_ids:
            raise TagRegistryError("tag group identities must be unique")
        if not str(raw.get("description") or "").strip():
            raise TagRegistryError(f"tag group {group_id} requires a description")
        if not str(raw.get("hermes_context_role") or "").strip():
            raise TagRegistryError(f"tag group {group_id} requires hermes_context_role")
        group_ids.add(group_id)
        group_map[group_id] = raw
    if {"type", "subject"} - group_ids:
        raise TagRegistryError("tag registry requires type and subject groups")
    if group_map["subject"].get("max_per_card") != MAX_SUBJECT_TAGS:
        raise TagRegistryError("subject group max_per_card must be 5")

    entries: dict[tuple[str, str], dict[str, Any]] = {}
    aliases: dict[tuple[str, str], str] = {}
    for raw in tags:
        if not isinstance(raw, dict):
            raise TagRegistryError("tag entries must be objects")
        group = str(raw.get("group") or "").strip()
        tag_slug = _slug(raw.get("slug"))
        if group not in group_ids or not tag_slug:
            raise TagRegistryError("each tag requires a registered group and stable slug")
        key = (group, tag_slug)
        if key in entries:
            raise TagRegistryError(f"duplicate tag: {group}:{tag_slug}")
        for field in ("title", "description", "hermes_context"):
            if not str(raw.get(field) or "").strip():
                raise TagRegistryError(f"tag {group}:{tag_slug} requires {field}")
        presentation = raw.get("presentation")
        if not isinstance(presentation, dict) or not presentation.get("icon_key"):
            raise TagRegistryError(f"tag {group}:{tag_slug} requires presentation")
        normalized = {
            "slug": tag_slug,
            "group": group,
            "title": str(raw["title"]),
            "description": str(raw["description"]),
            "hermes_context": str(raw["hermes_context"]),
            "aliases": [str(item) for item in raw.get("aliases") or []],
            "applies_to": [str(item) for item in raw.get("applies_to") or []],
            "presentation": dict(presentation),
        }
        entries[key] = normalized
        aliases[key] = tag_slug
        for alias in normalized["aliases"]:
            alias_slug = _slug(alias)
            alias_key = (group, alias_slug)
            existing = aliases.get(alias_key)
            if existing and existing != tag_slug:
                raise TagRegistryError(f"ambiguous tag alias: {group}:{alias_slug}")
            aliases[alias_key] = tag_slug

    return {
        "schema_id": SCHEMA_ID,
        "revision": REVISION,
        "groups": group_map,
        "entries": entries,
        "aliases": aliases,
    }


def resolve_entity_tag_context(
    *,
    entity_id: str,
    entity_type: str,
    type_tags: Any = None,
    subject_tags: Any = None,
) -> dict[str, Any]:
    """Resolve only declared tags; unknown tags remain explicit and undescribed."""

    registry = load_registry()
    requested = {
        "type": _string_list(type_tags),
        "subject": _string_list(subject_tags, limit=MAX_SUBJECT_TAGS),
    }
    resolved: list[dict[str, Any]] = []
    unregistered: list[dict[str, str]] = []

    for group, values in requested.items():
        for value in values:
            canonical = registry["aliases"].get((group, value))
            entry = registry["entries"].get((group, canonical)) if canonical else None
            if entry is None:
                unregistered.append({"group": group, "slug": value})
                continue
            resolved.append(
                {
                    "slug": entry["slug"],
                    "group": entry["group"],
                    "title": entry["title"],
                    "description": entry["description"],
                    "hermes_context": entry["hermes_context"],
                    "applies_to": list(entry["applies_to"]),
                }
            )

    return {
        "entity_ref": {"entity_id": entity_id, "entity_type": entity_type},
        "tags": resolved,
        "unregistered_tags": unregistered,
        "subject_limit": MAX_SUBJECT_TAGS,
        "limits": [
            "tag description != source truth",
            "tag presence != Evidence",
            "tag context != scope expansion",
            "tag context != task authorization",
        ],
    }
