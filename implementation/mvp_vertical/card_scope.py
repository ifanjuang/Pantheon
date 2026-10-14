"""Server-side resolution and validation of Cockpit Card scope.

DOM nesting and browser-supplied references are not security boundaries. The
server verifies stable identities, resolves declared descendants itself and
returns source references only from records it has resolved.
"""

from __future__ import annotations

from typing import Any

import psycopg

from . import (
    agency_data,
    agency_directory,
    agency_information,
    knowledge,
    store,
    work_issue_read,
    work_issues,
)
from .entity_ref import EntityRef, EntityRefError


class CardScopeError(ValueError):
    pass


_COCKPIT_SPACES = {
    "space:pantheon",
    "space:decisions",
    "space:affaires",
    "space:connaissances",
    "space:outils",
}


def _strip_prefix(value: str, prefix: str) -> str:
    return value[len(prefix):] if value.startswith(prefix) else value


def _entity_ref(value: dict[str, Any], *, label: str = "root entity") -> EntityRef:
    """Translate structural identity errors into the scope domain."""
    try:
        return EntityRef.from_mapping(value, label=label)
    except EntityRefError as exc:
        raise CardScopeError(str(exc)) from exc


def _contacts_project_id(entity_id: str) -> str:
    value = _strip_prefix(entity_id, "project:")
    if not value.endswith(":contacts"):
        raise CardScopeError(f"invalid Project Contacts identity: {entity_id}")
    project_id = value.removesuffix(":contacts").strip()
    if not project_id:
        raise CardScopeError(f"invalid Project Contacts identity: {entity_id}")
    return project_id


def _information_id(entity_id: str) -> str:
    value = _strip_prefix(entity_id, "information:").strip()
    if not value:
        raise CardScopeError(f"invalid Information identity: {entity_id}")
    return value


def _append_source(target: list[str], value: Any) -> None:
    if value:
        ref = str(value)
        if ref not in target:
            target.append(ref)


def _validated_entity_ref(
    conn: psycopg.Connection,
    *,
    value: dict[str, Any],
    label: str = "root entity",
) -> tuple[EntityRef, list[str]]:
    """Verify one structurally valid identity against its authoritative store."""
    ref = _entity_ref(value, label=label)
    entity_id = ref.entity_id
    entity_type = ref.entity_type
    source_refs: list[str] = []

    try:
        if entity_type == "project":
            agency_data.get_project(conn, _strip_prefix(entity_id, "project:"))
        elif entity_type == "project_contacts":
            agency_data.get_project(conn, _contacts_project_id(entity_id))
        elif entity_type == "person":
            agency_directory.get_person(conn, _strip_prefix(entity_id, "person:"))
        elif entity_type == "organization":
            organization_id = _strip_prefix(entity_id, "organization:")
            organization_id = _strip_prefix(organization_id, "org:")
            agency_directory.get_organization(conn, organization_id)
        elif entity_type == "information":
            context = agency_information.get_information_context(conn, _information_id(entity_id))
            _append_source(source_refs, context["current"].get("source_ref"))
        elif entity_type == "document":
            document_id = _strip_prefix(entity_id, "document:")
            document = store.get_document_card_by_id(conn, document_id)
            _append_source(source_refs, document.get("source_ref"))
        elif entity_type == "knowledge":
            knowledge_id = _strip_prefix(entity_id, "knowledge:")
            item = knowledge.get_knowledge_card(conn, knowledge_id)
            for source_ref in item.get("source_chunk_refs", []):
                _append_source(source_refs, source_ref)
        elif entity_type == "work_issue":
            work_issue_read.get_issue_record(conn, _strip_prefix(entity_id, "work:"))
        elif entity_type == "work_decision":
            issue_id = _strip_prefix(entity_id, "decision:work:")
            work_issue_read.get_issue_record(conn, issue_id)
        elif entity_type == "cockpit_space":
            if entity_id not in _COCKPIT_SPACES:
                raise CardScopeError(f"unknown Cockpit space: {entity_id}")
        else:
            raise CardScopeError(f"unsupported Cockpit context entity type: {entity_type}")
    except (
        agency_data.ProjectNotFound,
        agency_directory.PersonNotFound,
        agency_directory.OrganizationNotFound,
        agency_directory.AgencyDirectoryError,
        agency_information.AgencyInformationError,
        knowledge.KnowledgeNotFound,
        work_issues.WorkIssueError,
        KeyError,
    ) as exc:
        raise CardScopeError(str(exc)) from exc

    return ref, source_refs


def validate_entity_ref(
    conn: psycopg.Connection,
    *,
    entity_ref: dict[str, Any],
) -> dict:
    """Verify one requested entity against its authoritative store."""
    ref, source_refs = _validated_entity_ref(conn, value=entity_ref)
    return {**ref.as_dict(), "source_refs": source_refs}


def resolve_explicit_context(
    conn: psycopg.Connection,
    *,
    entity_refs: list[dict[str, Any]],
) -> dict:
    """Validate explicit Context Resolver selections and derive their sources."""
    entities: list[dict[str, str]] = []
    source_refs: list[str] = []
    seen_entities: set[tuple[str, str]] = set()
    seen_sources: set[str] = set()

    for raw in entity_refs:
        ref, resolved_sources = _validated_entity_ref(
            conn,
            value=raw,
            label="explicit context entity",
        )
        if ref.key not in seen_entities:
            seen_entities.add(ref.key)
            entities.append(ref.as_dict())
        for source_ref in resolved_sources:
            if source_ref not in seen_sources:
                seen_sources.add(source_ref)
                source_refs.append(source_ref)

    return {"entities": entities, "source_refs": source_refs}


def resolve_declared_descendants(
    conn: psycopg.Connection,
    *,
    root_entity: dict[str, Any],
) -> dict:
    root = _entity_ref(root_entity)
    entity_id = root.entity_id
    entity_type = root.entity_type

    if entity_type == "project":
        project_id = _strip_prefix(entity_id, "project:")
        try:
            project = agency_data.get_project(conn, project_id)
        except agency_data.ProjectNotFound as exc:
            raise CardScopeError(str(exc)) from exc

        documents = store.list_document_cards(conn, project_id)
        information = agency_information.list_project_information(conn, project_id)
        try:
            work = work_issue_read.list_issue_projections(conn, project_id, limit=500)
        except work_issues.WorkIssueError as exc:
            raise CardScopeError(str(exc)) from exc

        descendants = [
            {
                "entity_id": f"project:{project_id}:contacts",
                "entity_type": "project_contacts",
            }
        ]
        descendants.extend(
            {
                "entity_id": f"information:{item['information_id']}",
                "entity_type": "information",
            }
            for item in information
        )
        descendants.extend(
            {
                "entity_id": f"document:{item['document_id']}",
                "entity_type": "document",
            }
            for item in documents
        )
        descendants.extend(
            {
                "entity_id": f"work:{item['work_issue']['issue_id']}",
                "entity_type": "work_issue",
            }
            for item in work
        )

        source_refs: list[str] = []
        for item in information:
            _append_source(source_refs, item.get("source_ref"))
        for item in documents:
            _append_source(source_refs, item.get("source_ref"))

        return {
            "policy": "project_declared_children",
            "root_owner_id": project_id,
            "descendants": descendants,
            "source_refs": source_refs,
            "counts": {
                "contacts": len(project.get("contacts") or []),
                "information": len(information),
                "documents": len(documents),
                "work": len(work),
            },
        }

    if entity_type == "project_contacts":
        project_id = _contacts_project_id(entity_id)
        try:
            project = agency_data.get_project(conn, project_id)
        except agency_data.ProjectNotFound as exc:
            raise CardScopeError(str(exc)) from exc
        return {
            "policy": "project_contacts_root_only",
            "root_owner_id": project_id,
            "descendants": [],
            "source_refs": [],
            "counts": {"contacts": len(project.get("contacts") or [])},
        }

    if entity_type == "information":
        try:
            context = agency_information.get_information_context(conn, _information_id(entity_id))
        except agency_information.AgencyInformationError as exc:
            raise CardScopeError(str(exc)) from exc

        current = context["current"]
        acted = context.get("last_acted")
        descendants: list[dict[str, str]] = []
        source_refs: list[str] = []
        _append_source(source_refs, current.get("source_ref"))

        if (
            current.get("status") in agency_information.WORKING_STATUSES
            and acted
            and acted.get("information_id") != current.get("information_id")
        ):
            descendants.append(
                {
                    "entity_id": f"information:{acted['information_id']}",
                    "entity_type": "information",
                }
            )
            _append_source(source_refs, acted.get("source_ref"))

        return {
            "policy": "information_current_plus_last_acted",
            "root_owner_id": current["project_id"],
            "descendants": descendants,
            "source_refs": source_refs,
            "counts": {
                "working": 1 if current.get("status") in agency_information.WORKING_STATUSES else 0,
                "acted_reference": len(descendants),
            },
        }

    if entity_type == "document":
        document_id = _strip_prefix(entity_id, "document:")
        try:
            document = store.get_document_card_by_id(conn, document_id)
        except KeyError as exc:
            raise CardScopeError(str(exc)) from exc
        return {
            "policy": "document_source_only",
            "root_owner_id": document_id,
            "descendants": [],
            "source_refs": [document["source_ref"]] if document.get("source_ref") else [],
            "counts": {"documents": 1},
        }

    validate_entity_ref(conn, entity_ref=root.as_dict())
    return {
        "policy": "root_only",
        "root_owner_id": entity_id,
        "descendants": [],
        "source_refs": [],
        "counts": {},
    }


def resolve_case_ref(
    conn: psycopg.Connection,
    *,
    root_entity: dict[str, Any],
) -> str:
    """Resolve the owning project/case before an internal Work Issue is created."""
    root = _entity_ref(root_entity)
    entity_id = root.entity_id
    entity_type = root.entity_type

    if entity_type == "project":
        project_id = _strip_prefix(entity_id, "project:")
        try:
            agency_data.get_project(conn, project_id)
        except agency_data.ProjectNotFound as exc:
            raise CardScopeError(str(exc)) from exc
        return project_id

    if entity_type == "project_contacts":
        project_id = _contacts_project_id(entity_id)
        try:
            agency_data.get_project(conn, project_id)
        except agency_data.ProjectNotFound as exc:
            raise CardScopeError(str(exc)) from exc
        return project_id

    if entity_type == "information":
        try:
            context = agency_information.get_information_context(conn, _information_id(entity_id))
            return str(context["current"]["project_id"])
        except agency_information.AgencyInformationError as exc:
            raise CardScopeError(str(exc)) from exc

    if entity_type == "document":
        document_id = _strip_prefix(entity_id, "document:")
        try:
            return str(store.get_document_card_by_id(conn, document_id)["parent_project_id"])
        except KeyError as exc:
            raise CardScopeError(str(exc)) from exc

    if entity_type == "knowledge":
        knowledge_id = _strip_prefix(entity_id, "knowledge:")
        try:
            return str(knowledge.get_knowledge_card(conn, knowledge_id)["parent_project_id"])
        except knowledge.KnowledgeNotFound as exc:
            raise CardScopeError(str(exc)) from exc

    if entity_type == "work_issue":
        issue_id = _strip_prefix(entity_id, "work:")
        try:
            return str(work_issue_read.get_issue_record(conn, issue_id)["case_ref"])
        except work_issues.WorkIssueError as exc:
            raise CardScopeError(str(exc)) from exc

    if entity_type == "work_decision":
        issue_id = _strip_prefix(entity_id, "decision:work:")
        try:
            return str(work_issue_read.get_issue_record(conn, issue_id)["case_ref"])
        except work_issues.WorkIssueError as exc:
            raise CardScopeError(str(exc)) from exc

    raise CardScopeError(
        f"Hermes handoff submission requires a project-scoped root; unsupported root type: {entity_type}"
    )
