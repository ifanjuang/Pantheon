"""Deterministic preview of a scoped Cockpit -> Hermes handoff.

This module prepares governance-facing candidate objects only. It does not
persist a Work Issue, dispatch Hermes, authorize execution, create Evidence or
promote memory.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .entity_ref import EntityRef, EntityRefError, unique_entity_refs


MAX_CONTEXT_REFS = 250
MAX_SOURCE_REFS = 500
MAX_TAG_CONTEXT_ENTITIES = 250
MAX_EPHEMERAL_CONTEXT_LEASES = 20


class HandoffPreviewError(ValueError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _entity_ref(value: dict, *, label: str) -> dict[str, str]:
    try:
        return EntityRef.from_mapping(value, label=label).as_dict()
    except EntityRefError as exc:
        raise HandoffPreviewError(str(exc)) from exc


def _unique_refs(values: list[dict], *, label: str) -> list[dict[str, str]]:
    try:
        return [
            ref.as_dict()
            for ref in unique_entity_refs(
                values,
                label=label,
                limit=MAX_CONTEXT_REFS,
            )
        ]
    except EntityRefError as exc:
        raise HandoffPreviewError(str(exc)) from exc


def _source_refs(values: list[str]) -> list[str]:
    if len(values) > MAX_SOURCE_REFS:
        raise HandoffPreviewError(f"source_refs exceeds {MAX_SOURCE_REFS} entries")
    output: list[str] = []
    seen: set[str] = set()
    for raw in values:
        ref = str(raw or "").strip()
        if not ref or ref in seen:
            continue
        seen.add(ref)
        output.append(ref)
    return output


def _tag_context(values: Any) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        raise HandoffPreviewError("tag_context must be an array")
    if len(values) > MAX_TAG_CONTEXT_ENTITIES:
        raise HandoffPreviewError(
            f"tag_context exceeds {MAX_TAG_CONTEXT_ENTITIES} entity entries"
        )

    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for raw in values:
        if not isinstance(raw, dict):
            raise HandoffPreviewError("tag_context entries must be objects")
        try:
            ref = EntityRef.from_mapping(
                raw.get("entity_ref") or {},
                label="tag_context.entity_ref",
            )
        except EntityRefError as exc:
            raise HandoffPreviewError(str(exc)) from exc
        if ref.key in seen:
            raise HandoffPreviewError("tag_context contains a duplicate entity")
        seen.add(ref.key)

        tags = raw.get("tags")
        unregistered = raw.get("unregistered_tags")
        limits = raw.get("limits")
        if not isinstance(tags, list) or not isinstance(unregistered, list):
            raise HandoffPreviewError(
                "tag_context requires tags and unregistered_tags arrays"
            )
        if raw.get("subject_limit") != 5:
            raise HandoffPreviewError("tag_context subject_limit must be 5")
        if not isinstance(limits, list):
            raise HandoffPreviewError("tag_context requires limits")

        normalized_tags: list[dict[str, Any]] = []
        for tag in tags:
            if not isinstance(tag, dict):
                raise HandoffPreviewError("tag context definitions must be objects")
            group = str(tag.get("group") or "").strip()
            slug = str(tag.get("slug") or "").strip()
            title = str(tag.get("title") or "").strip()
            description = str(tag.get("description") or "").strip()
            hermes_context = str(tag.get("hermes_context") or "").strip()
            if group not in {"type", "subject"}:
                raise HandoffPreviewError("tag context group must be type or subject")
            if not all((slug, title, description, hermes_context)):
                raise HandoffPreviewError("registered tag context is incomplete")
            normalized_tags.append(
                {
                    "slug": slug,
                    "group": group,
                    "title": title,
                    "description": description,
                    "hermes_context": hermes_context,
                    "applies_to": [str(item) for item in tag.get("applies_to") or []],
                }
            )

        normalized_unregistered: list[dict[str, str]] = []
        for item in unregistered:
            if not isinstance(item, dict):
                raise HandoffPreviewError("unregistered tag entries must be objects")
            group = str(item.get("group") or "").strip()
            slug = str(item.get("slug") or "").strip()
            if group not in {"type", "subject"} or not slug:
                raise HandoffPreviewError("unregistered tag entry is invalid")
            normalized_unregistered.append({"group": group, "slug": slug})

        output.append(
            {
                "entity_ref": ref.as_dict(),
                "tags": normalized_tags,
                "unregistered_tags": normalized_unregistered,
                "subject_limit": 5,
                "limits": [str(item) for item in limits if str(item).strip()],
            }
        )
    return output



def _ephemeral_context_leases(values: Any) -> list[dict[str, Any]]:
    if values is None:
        return []
    if not isinstance(values, list):
        raise HandoffPreviewError("ephemeral_context_leases must be an array")
    if len(values) > MAX_EPHEMERAL_CONTEXT_LEASES:
        raise HandoffPreviewError(
            f"ephemeral_context_leases exceeds {MAX_EPHEMERAL_CONTEXT_LEASES} entries"
        )
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(values):
        if not isinstance(raw, dict):
            raise HandoffPreviewError(
                f"ephemeral_context_leases[{index}] must be an object"
            )
        if "content_utf8" in raw or "content" in raw or "payload" in raw:
            raise HandoffPreviewError(
                "ephemeral context payload may not be persisted in the handoff preview"
            )
        lease_ref = str(raw.get("lease_ref") or "").strip()
        lease_digest = str(raw.get("lease_digest") or "").strip().lower()
        created_at = str(raw.get("created_at") or "").strip()
        expires_at = str(raw.get("expires_at") or "").strip()
        items = raw.get("items")
        if not lease_ref or not lease_ref.startswith("ephemeral-context-"):
            raise HandoffPreviewError("ephemeral context lease_ref is invalid")
        if lease_ref in seen:
            raise HandoffPreviewError("ephemeral_context_leases contains a duplicate lease")
        seen.add(lease_ref)
        if len(lease_digest) != 64 or any(
            char not in "0123456789abcdef" for char in lease_digest
        ):
            raise HandoffPreviewError("ephemeral context lease_digest is invalid")
        if not created_at or not expires_at:
            raise HandoffPreviewError("ephemeral context lease timestamps are required")
        if raw.get("transient") is not True or raw.get("professional_persistence") is not False:
            raise HandoffPreviewError("ephemeral context lease posture is invalid")
        if not isinstance(items, list) or not items:
            raise HandoffPreviewError("ephemeral context lease items are required")
        normalized_items: list[dict[str, Any]] = []
        for item_index, item in enumerate(items):
            if not isinstance(item, dict):
                raise HandoffPreviewError("ephemeral context lease item must be an object")
            if "content_utf8" in item or "content" in item or "payload" in item:
                raise HandoffPreviewError(
                    "ephemeral context item payload may not be persisted in the handoff preview"
                )
            item_id = str(item.get("item_id") or "").strip()
            content_sha256 = str(item.get("content_sha256") or "").strip().lower()
            byte_size = item.get("byte_size")
            media_type = str(item.get("media_type") or "").strip()
            representation_kind = str(item.get("representation_kind") or "").strip()
            role = str(item.get("role") or "").strip()
            provenance = item.get("source_provenance")
            if not item_id:
                raise HandoffPreviewError("ephemeral context item_id is required")
            if len(content_sha256) != 64 or any(
                char not in "0123456789abcdef" for char in content_sha256
            ):
                raise HandoffPreviewError("ephemeral context item digest is invalid")
            if (
                isinstance(byte_size, bool)
                or not isinstance(byte_size, int)
                or byte_size <= 0
            ):
                raise HandoffPreviewError("ephemeral context item byte_size is invalid")
            if not media_type or representation_kind != "utf8_text":
                raise HandoffPreviewError("ephemeral context item representation is invalid")
            if role not in {"target", "context", "provider_item"}:
                raise HandoffPreviewError("ephemeral context item role is invalid")
            if not isinstance(provenance, list):
                raise HandoffPreviewError("ephemeral context source_provenance must be an array")
            normalized_items.append(
                {
                    "item_id": item_id,
                    "content_sha256": content_sha256,
                    "byte_size": byte_size,
                    "media_type": media_type,
                    "representation_kind": representation_kind,
                    "role": role,
                    "source_provenance": provenance,
                }
            )
        item_count = raw.get("item_count")
        total_bytes = raw.get("total_bytes")
        if item_count != len(normalized_items):
            raise HandoffPreviewError("ephemeral context item_count does not match items")
        if total_bytes != sum(item["byte_size"] for item in normalized_items):
            raise HandoffPreviewError("ephemeral context total_bytes does not match items")
        output.append(
            {
                "lease_ref": lease_ref,
                "lease_digest": lease_digest,
                "created_at": created_at,
                "expires_at": expires_at,
                "item_count": item_count,
                "total_bytes": total_bytes,
                "items": normalized_items,
                "transient": True,
                "professional_persistence": False,
            }
        )
    return output

def build_preview(
    *,
    question: str,
    card_context_envelope: dict,
    selected_context: list[dict] | None = None,
    ephemeral_context_leases: list[dict] | None = None,
) -> dict:
    intent = question.strip()
    if len(intent) < 3:
        raise HandoffPreviewError("Hermes handoff question must contain at least 3 characters")
    if len(intent) > 8_000:
        raise HandoffPreviewError("Hermes handoff question exceeds 8000 characters")

    root = _entity_ref(card_context_envelope.get("root_entity") or {}, label="root_entity")
    descendants = _unique_refs(card_context_envelope.get("descendants") or [], label="descendants")
    explicit_additions = _unique_refs(
        card_context_envelope.get("explicit_additions") or [],
        label="explicit_additions",
    )
    explicit_exclusions = _unique_refs(
        card_context_envelope.get("explicit_exclusions") or [],
        label="explicit_exclusions",
    )
    selected = _unique_refs(selected_context or [], label="selected_context")
    sources = _source_refs(card_context_envelope.get("source_refs") or [])
    tag_context = _tag_context(card_context_envelope.get("tag_context") or [])
    transient_leases = _ephemeral_context_leases(ephemeral_context_leases)

    excluded_keys = {
        EntityRef.from_mapping(item, label="excluded_entity").key
        for item in explicit_exclusions
    }
    admitted: list[dict[str, str]] = []
    admitted_keys: set[tuple[str, str]] = set()
    for item in [root, *descendants, *explicit_additions, *selected]:
        ref = EntityRef.from_mapping(item, label="included_entity")
        if ref.key in excluded_keys or ref.key in admitted_keys:
            continue
        admitted_keys.add(ref.key)
        admitted.append(ref.as_dict())

    context_core = {
        "purpose": "answer one Cockpit question within the visible Card context",
        "target_surface": "hermes_task_contract",
        "root_entity": root,
        "included_entities": admitted,
        "excluded_entities": explicit_exclusions,
        "source_refs": sources,
        "tag_context": tag_context,
        "ephemeral_context_leases": transient_leases,
        "scope_widened_implicitly": False,
        "staleness_note": "runtime must re-read current owner records when freshness is consequential",
        "forbidden_assumptions": [
            "selected context is Evidence",
            "runtime success establishes truth",
            "a read-only question authorizes a write or external effect",
            "a tag description establishes truth, authority or professional validation",
            "an unregistered tag may be assigned an invented meaning",
            "an ephemeral context lease is a durable Source, Evidence or Hindsight memory",
        ],
    }
    context_digest = _digest(context_core)
    context_pack_ref = f"context-pack-candidate:{context_digest[:24]}"

    task_core = {
        "intent": intent,
        "scope_ref": context_pack_ref,
        "requested_effect": "read_only",
        "constraints": [
            "do not widen scope implicitly",
            "do not mutate Agency Data",
            "do not perform an external effect",
            "do not promote memory or Evidence automatically",
            "surface missing, stale or contradictory information",
            "use tag descriptions only as contextual orientation",
            "do not infer a meaning for unregistered tags",
            "treat ephemeral context as bounded transient input only",
        ],
        "approval_expectations": "a new gate is required before any consequential follow-up",
        "expected_evidence": ["source_refs", "trace_refs", "limitations", "assumptions"],
        "allowed_outputs": ["answer_candidate", "source_references", "limitations", "open_questions"],
        "forbidden_outputs": ["external_effect", "canonical_effect", "memory_promotion", "agency_data_mutation"],
    }
    task_digest = _digest(task_core)
    task_contract_ref = f"task-contract-candidate:{task_digest[:24]}"

    preview = {
        "kind": "hermes_handoff_preview",
        "status": "candidate",
        "requested_effect": "read_only",
        "execution_authorized": False,
        "task_contract": {
            "task_contract_ref": task_contract_ref,
            "digest": task_digest,
            **task_core,
        },
        "context_pack": {
            "context_pack_ref": context_pack_ref,
            "digest": context_digest,
            **context_core,
        },
        "non_equivalences": [
            "preview != Task Contract admission",
            "context selection != Evidence",
            "tag context != source authority",
            "ephemeral context lease != Source admission",
            "ephemeral context lease != Hindsight memory",
            "execution_authorized=false",
            "handoff preview != Hermes run",
        ],
    }
    preview["preview_digest"] = _digest(preview)
    return preview
