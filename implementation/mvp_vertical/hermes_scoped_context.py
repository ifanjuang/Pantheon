"""Admission-bound read-only context access for a running Hermes execution.

This module is intentionally not a general Agency Data API. It exposes only the
stable entity identities already admitted in one immutable Context Pack and only
to the exact Hermes run that consumed that admission.

The Context Pack authorizes identity/scope, not a frozen business-data snapshot.
Each entity read therefore re-reads the current owner record and reports that
freshness explicitly. Source references are provenance identifiers only in this
slice; they cannot be dereferenced here.

Returned Agency fields are frozen by explicit named projections. Project and
Information use their respective `hermes_context` views; adding a future owner
column therefore cannot silently widen what Hermes can read.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg.rows import dict_row

from . import (
    agency_data,
    agency_directory,
    agency_information,
    agency_schema,
    apu_object_read,
    knowledge,
    store,
    work_issue_read,
    work_issues,
)
from .entity_ref import EntityRef, EntityRefError, unique_entity_refs
from .hermes_execution_basis import HermesExecutionBasis, HermesExecutionBasisError

MAX_RICH_TEXT_CHARS = 500_000
FIELD_PROJECTION_VERSION = "scoped-context-v1"
MATERIALIZABLE_TYPES = {
    "project",
    "person",
    "organization",
    "information",
    "document",
    "knowledge",
    "work_issue",
    "stable_object",
}

PERSON_FIELDS = (
    "person_id",
    "display_name",
    "email",
    "phone",
    "address",
    "owner_system",
    "revision",
    "updated_at",
)
ORGANIZATION_FIELDS = (
    "organization_id",
    "name",
    "email",
    "phone",
    "address",
    "siret",
    "owner_system",
    "revision",
    "updated_at",
)
DOCUMENT_FIELDS = (
    "card_type",
    "card_id",
    "document_id",
    "parent_project_id",
    "title",
    "source_ref",
    "source_digest",
    "media_type",
    "byte_size",
    "analysis_status",
    "naming",
    "extraction",
    "authority",
)
KNOWLEDGE_FIELDS = (
    "card_type",
    "card_id",
    "knowledge_id",
    "document_ref",
    "parent_project_id",
    "title",
    "family",
    "markdown_digest",
    "source_chunk_refs",
    "review_status",
    "version",
    "created_by",
    "created_at",
    "updated_at",
    "authority",
)
WORK_ISSUE_FIELDS = (
    "issue_id",
    "case_ref",
    "title",
    "description",
    "origin",
    "parent_issue_ref",
    "primary_card_ref",
    "issue_type",
    "priority",
    "assigned_to",
    "requested_effect",
    "status",
    "close_reason",
    "task_contract_ref",
    "context_pack_ref",
    "version",
    "created_by",
    "created_at",
    "updated_at",
)


class HermesScopedContextError(ValueError):
    pass


class ScopedContextNotFound(HermesScopedContextError):
    pass


class ScopedContextConflict(HermesScopedContextError):
    pass


class ScopedContextContentTooLarge(HermesScopedContextError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _strip_prefix(value: str, *prefixes: str) -> str:
    for prefix in prefixes:
        if value.startswith(prefix):
            return value[len(prefix):]
    return value


def _bounded_projection(record: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    """Project only reviewed v1 fields; schema growth cannot widen runtime access."""
    return {field: record.get(field) for field in fields if field in record}


def _runtime_scope(
    conn: psycopg.Connection,
    *,
    admission_id: str,
    run_id: str,
) -> dict[str, Any]:
    """Resolve one exact running run and its immutable admitted Context Pack."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT a.admission_id,
                   a.handoff_id,
                   a.work_issue_id,
                   a.requested_effect,
                   a.task_contract_ref AS admission_task_contract_ref,
                   a.context_pack_ref AS admission_context_pack_ref,
                   h.requested_effect AS handoff_requested_effect,
                   h.task_contract,
                   h.context_pack,
                   h.preview_digest AS handoff_preview_digest,
                   a.preview_digest AS admission_preview_digest,
                   r.run_id,
                   r.status AS run_status,
                   r.requested_effect AS run_requested_effect,
                   r.task_contract_ref AS run_task_contract_ref,
                   r.context_pack_ref AS run_context_pack_ref
              FROM hermes_execution_admissions a
              JOIN cockpit_hermes_handoffs h ON h.handoff_id = a.handoff_id
              JOIN hermes_runs r ON r.admission_ref = a.admission_id
             WHERE a.admission_id = %s
               AND r.run_id = %s
            """,
            (admission_id, run_id),
        )
        row = cur.fetchone()
    if row is None:
        raise ScopedContextNotFound(
            "no Hermes run matches this execution admission and run_id"
        )

    scope = dict(row)
    if scope["run_status"] != "running":
        raise ScopedContextConflict(
            f"Scoped Hermes Data Access requires a running Hermes run; current status is {scope['run_status']}"
        )

    context_pack = dict(scope.get("context_pack") or {})
    task_contract = dict(scope.get("task_contract") or {})
    context_ref = str(context_pack.get("context_pack_ref") or "")
    task_ref = str(task_contract.get("task_contract_ref") or "")
    if not context_ref or not task_ref:
        raise ScopedContextConflict("stored handoff is missing its Task Contract or Context Pack identity")

    try:
        admission_basis = HermesExecutionBasis.from_values(
            requested_effect=scope["requested_effect"],
            task_contract_ref=scope["admission_task_contract_ref"],
            context_pack_ref=scope["admission_context_pack_ref"],
            preview_digest=scope["admission_preview_digest"],
            label="execution admission basis",
        )
        handoff_basis = HermesExecutionBasis.from_values(
            requested_effect=scope["handoff_requested_effect"],
            task_contract_ref=task_ref,
            context_pack_ref=context_ref,
            preview_digest=scope["handoff_preview_digest"],
            label="immutable handoff basis",
        )
    except HermesExecutionBasisError as exc:
        raise ScopedContextConflict(
            "running Hermes context no longer matches the immutable admitted handoff"
        ) from exc

    if not (
        admission_basis.is_read_only
        and handoff_basis.is_read_only
        and scope["run_requested_effect"] == "read_only"
    ):
        raise ScopedContextConflict(
            "Scoped Hermes Data Access first slice requires read_only effect consistency"
        )
    if admission_basis != handoff_basis:
        raise ScopedContextConflict(
            "running Hermes context no longer matches the immutable admitted handoff"
        )
    if not (
        scope["run_context_pack_ref"] == admission_basis.context_pack_ref
        and scope["run_task_contract_ref"] == admission_basis.task_contract_ref
    ):
        raise ScopedContextConflict(
            "running Hermes context no longer matches the immutable admitted handoff"
        )

    scope["context_pack"] = context_pack
    scope["task_contract"] = task_contract
    return scope


def admitted_entity_refs(context_pack: dict[str, Any]) -> list[EntityRef]:
    """Return normalized identities from one immutable admitted Context Pack."""
    try:
        refs = unique_entity_refs(
            context_pack.get("included_entities") or [],
            label="stored Context Pack entity reference",
        )
    except EntityRefError as exc:
        detail = str(exc)
        if "requires stable entity_id and entity_type" in detail:
            message = "stored Context Pack contains an incomplete entity reference"
        else:
            message = "stored Context Pack contains an invalid entity reference"
        raise ScopedContextConflict(message) from exc
    if not refs:
        raise ScopedContextConflict("stored Context Pack contains no admitted entity")
    return refs


def require_admitted_entity(
    context_pack: dict[str, Any],
    *,
    entity_type: str,
    entity_id: str,
) -> EntityRef:
    """Require an exact identity match inside the admitted Context Pack."""
    try:
        wanted = EntityRef.from_mapping(
            {"entity_type": entity_type, "entity_id": entity_id},
            label="requested entity",
        )
    except EntityRefError as exc:
        raise ScopedContextConflict(
            "requested entity is outside the exact admitted Context Pack"
        ) from exc
    for ref in admitted_entity_refs(context_pack):
        if ref.key == wanted.key:
            return ref
    raise ScopedContextConflict(
        "requested entity is outside the exact admitted Context Pack"
    )


def _bounded_text(value: str, *, label: str) -> str:
    if len(value) > MAX_RICH_TEXT_CHARS:
        raise ScopedContextContentTooLarge(
            f"{label} exceeds the first-slice limit of {MAX_RICH_TEXT_CHARS} characters"
        )
    return value


def materialize_context_entity(
    conn: psycopg.Connection,
    *,
    entity_type: str,
    entity_id: str,
) -> dict[str, Any]:
    """Read one admitted identity through its bounded owner projection."""
    if entity_type == "project":
        raw = agency_data.get_project(conn, _strip_prefix(entity_id, "project:"))
        return {
            "record": agency_schema.project_record_for_view(raw, "hermes_context"),
            "representation": None,
            "record_owner_system": "postgres",
        }

    if entity_type == "stable_object":
        raw = apu_object_read.get_stable_object_context(
            conn,
            object_id=_strip_prefix(entity_id, "stable_object:"),
        )
        return {
            "record": raw,
            "representation": None,
            "record_owner_system": "postgres_apu_object_projection",
        }

    if entity_type == "person":
        raw = agency_directory.get_person(conn, _strip_prefix(entity_id, "person:"))
        return {
            "record": _bounded_projection(raw, PERSON_FIELDS),
            "representation": None,
            "record_owner_system": "postgres",
        }

    if entity_type == "organization":
        raw = agency_directory.get_organization(
            conn,
            _strip_prefix(entity_id, "organization:", "org:"),
        )
        return {
            "record": _bounded_projection(raw, ORGANIZATION_FIELDS),
            "representation": None,
            "record_owner_system": "postgres",
        }

    if entity_type == "information":
        information_id = _strip_prefix(entity_id, "information:")
        raw = agency_information.get_information_context(conn, information_id)["current"]
        record = agency_schema.information_record_for_view(raw, "hermes_context")
        details = _bounded_text(str(raw.get("details") or ""), label="Information details")
        source_note = _bounded_text(str(raw.get("source_note") or ""), label="Information source note")
        return {
            "record": record,
            "representation": {
                "kind": "agency_information_text",
                "summary": str(raw.get("summary") or ""),
                "details": details,
                "source_note": source_note,
                "working_assumptions_are_not_acted": raw.get("status") in {"draft", "in_progress"},
            },
            "record_owner_system": "postgres_agency_information",
        }

    if entity_type == "document":
        document_id = _strip_prefix(entity_id, "document:")
        raw = store.get_document_card_by_id(conn, document_id)
        record = _bounded_projection(raw, DOCUMENT_FIELDS)
        try:
            markdown = _bounded_text(
                store.get_document_markdown(conn, document_id),
                label="document derived Markdown",
            )
            representation: dict[str, Any] | None = {
                "kind": "derived_markdown",
                "content": markdown,
                "source_binary_included": False,
            }
        except KeyError:
            representation = None
        return {
            "record": record,
            "representation": representation,
            "record_owner_system": "postgres_document_projection",
        }

    if entity_type == "knowledge":
        knowledge_id = _strip_prefix(entity_id, "knowledge:")
        raw = knowledge.get_knowledge_card(conn, knowledge_id)
        record = _bounded_projection(raw, KNOWLEDGE_FIELDS)
        markdown = _bounded_text(
            knowledge.get_knowledge_markdown(conn, knowledge_id),
            label="Knowledge Markdown",
        )
        return {
            "record": record,
            "representation": {
                "kind": "knowledge_markdown",
                "content": markdown,
                "source_binary_included": False,
            },
            "record_owner_system": "postgres_knowledge_projection",
        }

    if entity_type == "work_issue":
        issue_id = _strip_prefix(entity_id, "work:")
        raw = work_issue_read.get_issue_record(conn, issue_id)
        return {
            "record": _bounded_projection(raw, WORK_ISSUE_FIELDS),
            "representation": None,
            "record_owner_system": "postgres",
        }

    if entity_type == "cockpit_space":
        raise HermesScopedContextError(
            "Cockpit spaces may appear in a Context Pack but are not materializable business data"
        )

    raise HermesScopedContextError(
        f"unsupported scoped Hermes context entity type: {entity_type}"
    )


def get_context_manifest(
    conn: psycopg.Connection,
    *,
    admission_id: str,
    run_id: str,
    actor: str,
) -> dict[str, Any]:
    if not actor.strip():
        raise HermesScopedContextError("Hermes actor is required for scoped context access")
    scope = _runtime_scope(conn, admission_id=admission_id, run_id=run_id)
    context_pack = scope["context_pack"]
    entities = [
        {
            **ref.as_dict(),
            "materializable": ref.entity_type in MATERIALIZABLE_TYPES,
        }
        for ref in admitted_entity_refs(context_pack)
    ]
    return {
        "kind": "hermes_scoped_context_manifest",
        "admission_id": admission_id,
        "run_id": run_id,
        "context_pack_ref": scope["admission_context_pack_ref"],
        "task_contract_ref": scope["admission_task_contract_ref"],
        "requested_effect": scope["requested_effect"],
        "run_status": scope["run_status"],
        "field_projection_version": FIELD_PROJECTION_VERSION,
        "entities": entities,
        "source_refs": list(context_pack.get("source_refs") or []),
        "source_dereference_available": False,
        "global_search_available": False,
        "global_listing_available": False,
        "write_effect": False,
        "read_semantics": "current_owner_read",
        "context_pack_authorizes_identity_not_snapshot": True,
        "observed_at": _now(),
        "requested_by": actor.strip(),
        "non_equivalences": [
            "Context Pack inclusion != Evidence",
            "current owner read != admission-time snapshot",
            "source_ref != source dereference authority",
            "field projection != full owner record",
            "read access != write authority",
            "runtime success != Evidence",
        ],
    }


def get_context_entity(
    conn: psycopg.Connection,
    *,
    admission_id: str,
    run_id: str,
    entity_type: str,
    entity_id: str,
    actor: str,
) -> dict[str, Any]:
    if not actor.strip():
        raise HermesScopedContextError("Hermes actor is required for scoped context access")
    scope = _runtime_scope(conn, admission_id=admission_id, run_id=run_id)
    ref = require_admitted_entity(
        scope["context_pack"],
        entity_type=entity_type,
        entity_id=entity_id,
    )
    try:
        materialized = materialize_context_entity(
            conn,
            entity_type=ref.entity_type,
            entity_id=ref.entity_id,
        )
    except (
        agency_data.ProjectNotFound,
        agency_directory.AgencyDirectoryError,
        agency_information.AgencyInformationError,
        agency_schema.AgencySchemaError,
        apu_object_read.ApuObjectReadError,
        knowledge.KnowledgeNotFound,
        work_issues.WorkIssueError,
        KeyError,
    ) as exc:
        raise ScopedContextNotFound(str(exc)) from exc

    record = materialized["record"]
    revision = record.get("revision", record.get("version")) if isinstance(record, dict) else None

    return {
        "kind": "hermes_scoped_context_entity",
        "admission_id": admission_id,
        "run_id": run_id,
        "context_pack_ref": scope["admission_context_pack_ref"],
        "entity_ref": ref.as_dict(),
        "field_projection_version": FIELD_PROJECTION_VERSION,
        "record_owner_system": materialized["record_owner_system"],
        "current_revision": revision,
        "record": record,
        "representation": materialized["representation"],
        "read_semantics": "current_owner_read",
        "context_pack_authorizes_identity_not_snapshot": True,
        "source_binary_included": False,
        "write_effect": False,
        "observed_at": _now(),
        "requested_by": actor.strip(),
        "non_equivalences": [
            "entity admitted != entity is Evidence",
            "current owner read != admission-time snapshot",
            "field projection != full owner record",
            "derived representation != source binary",
            "read access != write authority",
        ],
    }
