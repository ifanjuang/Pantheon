"""Read-only Card collection composition for persisted Categories.

Category and CategoryAssignment remain owned by ``agency_classification``. This
adapter composes existing bounded owner reads and projects them through the
Cockpit Card projection seam so clients receive homogeneous Collections. It
creates no Card record, changes no owner, infers no authorization and does not
qualify Evidence.
"""

from __future__ import annotations

from typing import Any, Callable

import psycopg

from . import (
    agency_classification,
    agency_data,
    cockpit_card_projection,
    information_projection,
    knowledge,
    project_documents,
    work_issue_read,
    work_issues,
)
from .entity_ref import EntityRef, EntityRefError


class CategoryCollectionReadError(ValueError):
    """Base refusal for Category collection read composition."""


class CategoryCollectionIntegrityError(CategoryCollectionReadError):
    """A persisted assignment no longer resolves to its declared owner."""


OwnerReader = Callable[[psycopg.Connection, str], dict[str, Any]]


def _information_read(conn: psycopg.Connection, information_id: str) -> dict[str, Any]:
    return information_projection.get_projection(conn, information_id)


def _work_issue_read(conn: psycopg.Connection, issue_id: str) -> dict[str, Any]:
    return work_issue_read.get_issue_record(conn, issue_id)


_OWNER_READERS: dict[str, OwnerReader] = {
    "project": agency_data.get_project,
    "information": _information_read,
    "document": project_documents.get_document,
    "knowledge": knowledge.get_knowledge_card,
    "work_issue": _work_issue_read,
}

_OWNER_NOT_FOUND = (
    agency_data.ProjectNotFound,
    information_projection.InformationProjectionNotFound,
    project_documents.ProjectDocumentNotFound,
    knowledge.KnowledgeNotFound,
    work_issues.IssueNotFound,
)


def _collection_response(
    *,
    collection_id: str,
    parent_entity_id: str,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "collection": {
            "collection_id": collection_id,
            "parent_entity_id": parent_entity_id,
            "state": "loaded" if items else "empty",
            "items": items,
            "can_add": False,
        },
        "cards_are_projections": True,
        "classification_is_not_authorization": True,
        "authorization_inferred": False,
    }


def _resolve_assignment_card(
    conn: psycopg.Connection,
    assignment: dict[str, Any],
) -> dict[str, Any]:
    try:
        ref = EntityRef.from_mapping(assignment, label="CategoryAssignment")
    except EntityRefError as exc:
        raise CategoryCollectionReadError(str(exc)) from exc

    reader = _OWNER_READERS.get(ref.entity_type)
    if reader is None:
        raise CategoryCollectionReadError(
            f"unsupported CategoryAssignment entity type: {ref.entity_type}"
        )

    try:
        read_model = reader(conn, ref.entity_id)
    except _OWNER_NOT_FOUND as exc:
        raise CategoryCollectionIntegrityError(
            f"active CategoryAssignment references missing owner: {ref.entity_type}:{ref.entity_id}"
        ) from exc

    try:
        card = cockpit_card_projection.project_owner_card(ref.entity_type, read_model)
    except (KeyError, TypeError, ValueError) as exc:
        raise CategoryCollectionIntegrityError(
            f"owner read model cannot be projected as a Card: {ref.entity_type}:{ref.entity_id}"
        ) from exc

    if card.get("source_entity_ref") != ref.as_dict():
        raise CategoryCollectionIntegrityError(
            f"Card projection changed owner identity: {ref.entity_type}:{ref.entity_id}"
        )

    return {
        **card,
        "collection_membership": {
            "kind": "category_assignment",
            "assignment": assignment,
        },
    }


def get_root_category_card_collection(conn: psycopg.Connection) -> dict[str, Any]:
    """Project persisted root Categories under the Cockpit Knowledge space.

    The owner still decides which Category records are roots. The Cockpit only
    projects those existing records as container Cards; it does not infer a
    hierarchy from names, folders, tags or retrieval results.
    """

    items = [
        cockpit_card_projection.project_category(category)
        for category in agency_classification.list_root_categories(conn)
    ]
    return _collection_response(
        collection_id="children:space:connaissances",
        parent_entity_id="space:connaissances",
        items=items,
    )


def get_category_card_collection(
    conn: psycopg.Connection,
    category_id: str,
) -> dict[str, Any]:
    """Project one Category's direct children into a homogeneous Card Collection.

    Child Categories are projected as container Cards. Direct assignments are
    resolved through existing owner readers and then projected as Cards. The
    same owner may therefore appear in several Collections with one stable Card
    identity and different contextual membership provenance.
    """

    source = agency_classification.get_category_collection(conn, category_id)
    child_cards = [
        cockpit_card_projection.project_category(category)
        for category in source["child_categories"]
    ]
    member_cards = [
        _resolve_assignment_card(conn, assignment)
        for assignment in source["assignments"]
    ]
    return _collection_response(
        collection_id=f"children:category:{category_id}",
        parent_entity_id=f"category:{category_id}",
        items=[*child_cards, *member_cards],
    )
