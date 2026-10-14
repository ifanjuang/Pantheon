"""Read-only tag context projection for server-validated Cockpit entities.

The caller must validate entity scope first. This module reads only owner records,
then resolves their explicit tags through the shared registry. It does not widen
scope, create tags, infer missing subjects or promote the vocabulary to Evidence.
"""

from __future__ import annotations

from typing import Any

import psycopg

from . import (
    agency_data,
    agency_information,
    knowledge,
    store,
    tag_registry,
    work_issue_read,
    work_issues,
)
from .entity_ref import EntityRef, EntityRefError


class CardTagContextError(ValueError):
    pass


def _strip_prefix(value: str, prefix: str) -> str:
    return value[len(prefix):] if value.startswith(prefix) else value


def _record_tags(record: dict[str, Any]) -> tuple[list[str], list[str]]:
    type_tags = record.get("type_tags")
    subject_tags = record.get("subject_tags") or record.get("tags")
    return (
        type_tags if isinstance(type_tags, list) else [],
        subject_tags if isinstance(subject_tags, list) else [],
    )


def _entity_record(
    conn: psycopg.Connection,
    *,
    entity_id: str,
    entity_type: str,
) -> dict[str, Any] | None:
    if entity_type == "project":
        return agency_data.get_project(conn, _strip_prefix(entity_id, "project:"))
    if entity_type == "information":
        information_id = _strip_prefix(entity_id, "information:")
        return agency_information.get_information_context(conn, information_id)["current"]
    if entity_type == "document":
        return store.get_document_card_by_id(conn, _strip_prefix(entity_id, "document:"))
    if entity_type == "knowledge":
        return knowledge.get_knowledge_card(conn, _strip_prefix(entity_id, "knowledge:"))
    if entity_type == "work_issue":
        return work_issue_read.get_issue_record(conn, _strip_prefix(entity_id, "work:"))
    if entity_type == "work_decision":
        issue_id = _strip_prefix(entity_id, "decision:work:")
        return work_issue_read.get_issue_record(conn, issue_id)
    if entity_type in {
        "project_contacts",
        "person",
        "organization",
        "cockpit_space",
    }:
        return None
    raise CardTagContextError(f"unsupported tag context entity type: {entity_type}")


def resolve_tag_context(
    conn: psycopg.Connection,
    *,
    entity_refs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Resolve bounded tag descriptions for already validated entity refs.

    Lightweight test doubles used to exercise scope policy may deliberately omit
    owner-read methods. They produce no tag context rather than accepting client
    descriptions or inventing metadata. Production PostgreSQL connections expose
    ``cursor`` and therefore execute the authoritative owner reads below.
    """

    if not callable(getattr(conn, "cursor", None)):
        return []

    contexts: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    try:
        for raw in entity_refs:
            ref = EntityRef.from_mapping(raw, label="tag context entity")
            if ref.key in seen:
                continue
            seen.add(ref.key)

            record = _entity_record(
                conn,
                entity_id=ref.entity_id,
                entity_type=ref.entity_type,
            )
            type_tags, subject_tags = _record_tags(record or {})
            context = tag_registry.resolve_entity_tag_context(
                entity_id=ref.entity_id,
                entity_type=ref.entity_type,
                type_tags=type_tags,
                subject_tags=subject_tags,
            )
            if context["tags"] or context["unregistered_tags"]:
                contexts.append(context)
    except CardTagContextError:
        raise
    except EntityRefError as exc:
        raise CardTagContextError(str(exc)) from exc
    except (
        agency_data.AgencyDataError,
        agency_information.AgencyInformationError,
        knowledge.KnowledgeError,
        work_issues.WorkIssueError,
        tag_registry.TagRegistryError,
        KeyError,
    ) as exc:
        raise CardTagContextError(str(exc)) from exc
    return contexts
