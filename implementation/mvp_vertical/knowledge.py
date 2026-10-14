"""Transactional Document → Knowledge and offline-edit adapter.

Knowledge is reusable editorial Markdown. It is never Evidence, governed
memory, doctrine, or a replacement for the NAS original. All material writes
use exact optimistic versions and immutable idempotency keys.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import uuid
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import jsonschema
import psycopg
import yaml
from psycopg.rows import dict_row

from . import document_structure_read, pantheon_contracts
from .policy_gate import OBJECT_IDENTITY_KEY, PolicyClient, enforce_consequential
from .structured_extraction import chunk_ref


SCHEMA = pantheon_contracts.schema_path("document_knowledge_slice")
FAMILIES = {"referentiels", "responsabilite", "methodologie", "techniques", "reglementations"}
REVIEW_STATUSES = {"generated_unreviewed", "needs_review", "reviewed", "superseded"}
INSTRUCTION_KINDS = {"rewrite", "expand", "simplify", "verify", "move_to_lot"}
ACTOR_KINDS = {"human", "hermes", "system"}


class KnowledgeError(ValueError):
    """Base refusal for the bounded Knowledge adapter."""


class KnowledgeNotFound(KnowledgeError):
    pass


class StaleKnowledgeWrite(KnowledgeError):
    pass


class IdempotencyConflict(KnowledgeError):
    pass


class KnowledgeGateRefused(KnowledgeError):
    """The chokepoint refused this Knowledge write."""


class KnowledgeGatePolicyUnavailable(KnowledgeError):
    """The decision point could not be reached; the write fails closed."""


class _EditRequestConflict(Exception):
    """Internal signal: unwind the apply transaction so the conflict can persist.

    Never leaves this module. apply_edit_request() raises it to roll back a
    partially-applied edit, then records the durable `conflict` status in a
    fresh transaction and re-raises StaleKnowledgeWrite to the caller.
    """


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _payload_digest(value: dict[str, Any]) -> str:
    canonical = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return _digest(canonical)


def _gate_knowledge_write(
    policy_client: PolicyClient,
    *,
    intent: str,
    scope: dict[str, str],
    object_ref: str,
    expected_digest: str,
    decision_payload: dict[str, Any] | None,
    actor: str,
    required_ceiling: str,
) -> None:
    """Shared chokepoint call for the two Knowledge writes that need it.

    Local to this module rather than a general-purpose wrapper: each gated
    write elsewhere in the package binds its own scope and object reference,
    and the two calls in `publish_knowledge` and `apply_edit_request` share
    nothing but the shape of that binding.
    """
    expectation = {
        "required_ceiling": required_ceiling,
        "required_scope": scope,
        OBJECT_IDENTITY_KEY: object_ref,
        "expected_digest": expected_digest,
    }
    candidate = {
        "intent": intent,
        "decision_expectation": expectation,
        "request": {
            "intent": intent,
            "external_effect": False,
            "writes_state": True,
            "transmission_requested": False,
            "memory_promotion_requested": False,
            "professional_position": False,
            "financial_or_contractual_effect": False,
            "scope": scope,
        },
    }
    verdict = enforce_consequential(
        policy_client,
        candidate=candidate,
        decision_payload=dict(decision_payload or {}),
    )
    if not verdict.allowed:
        message = (
            f"policy chokepoint blocked the Knowledge write ({verdict.disposition}): "
            f"{verdict.reasons}"
        )
        if verdict.disposition == "policy_unavailable":
            raise KnowledgeGatePolicyUnavailable(message)
        raise KnowledgeGateRefused(message)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _knowledge_row(conn: psycopg.Connection, knowledge_id: str, *, lock: bool = False) -> dict:
    suffix = " FOR UPDATE" if lock else ""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(f"SELECT * FROM knowledge_items WHERE knowledge_id = %s{suffix}", (knowledge_id,))
        row = cur.fetchone()
    if row is None:
        raise KnowledgeNotFound(f"unknown Knowledge item: {knowledge_id}")
    return dict(row)


def _document_row(conn: psycopg.Connection, document_id: str) -> dict:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT d.*, e.extraction_id, e.converter, e.converter_version, e.config_digest,
                   e.status AS converter_status,
                   e.quality_flags AS converter_quality_flags, e.error,
                   e.created_at AS extraction_created_at, o.observation_kind,
                   sc.compilation_id,
                   sc.status AS compilation_status,
                   sc.compilation_id,
                   sc.quality_flags AS compilation_quality_flags,
                   (SELECT MAX(v.version) FROM document_versions v
                     WHERE v.document_id = d.document_id) AS source_version
              FROM source_documents d
              LEFT JOIN extraction_runs e ON e.extraction_id = d.current_extraction_id
              LEFT JOIN extraction_observations o ON o.extraction_id = e.extraction_id
              LEFT JOIN document_compilation_bindings cb ON cb.document_id = d.document_id
              LEFT JOIN structured_compilations sc
                ON sc.compilation_id = cb.compilation_id
               AND sc.extraction_id = e.extraction_id
             WHERE d.document_id = %s
            """,
            (document_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise KnowledgeNotFound(f"unknown source document: {document_id}")
    document = dict(row)
    document["extraction_status"] = document["analysis_status"]
    document["quality_flags"] = list(
        dict.fromkeys(
            [
                *(document.get("converter_quality_flags") or []),
                *(document.get("compilation_quality_flags") or []),
            ]
        )
    )
    return document


def _chunk_refs(conn: psycopg.Connection, document: dict) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT chunk_no
              FROM chunks
             WHERE dossier = %s
               AND source_ref = %s
               AND source_digest = %s
             ORDER BY chunk_no
            """,
            (document["dossier"], document["source_ref"], document["source_digest"]),
        )
        if not document.get("compilation_id"):
            return []
        return [chunk_ref(document["compilation_id"], row[0]) for row in cur.fetchall()]


def _split_chunk_ref(value: str) -> tuple[str, int]:
    """Parse one immutable compiled chunk reference without widening scope."""
    text = str(value or "").strip()
    if not text.startswith("chunk."):
        raise KnowledgeError(f"invalid Knowledge chunk reference: {value!r}")
    body = text.removeprefix("chunk.")
    if "." not in body:
        raise KnowledgeError(f"invalid Knowledge chunk reference: {value!r}")
    compilation_ref, ordinal_text = body.rsplit(".", 1)
    if not compilation_ref or not ordinal_text.isdigit():
        raise KnowledgeError(f"invalid Knowledge chunk reference: {value!r}")
    return compilation_ref, int(ordinal_text)


def _resolve_current_source_chunks(
    conn: psycopg.Connection,
    *,
    parent_project_id: str,
    source_chunk_refs: list[str],
) -> dict[str, dict]:
    """Resolve exact current chunks inside one already-selected Project scope.

    Chunk references carry the immutable compilation identity.  The query still
    requires that compilation to be the document's *current* binding and that
    every document belongs to the primary Knowledge item's Project.  This makes
    multi-source Knowledge additive without turning a chunk id into permission
    to cross scope or cite a superseded technical capture silently.
    """
    if not source_chunk_refs:
        raise KnowledgeError("Knowledge must cite one or more current source chunks")
    if len(set(source_chunk_refs)) != len(source_chunk_refs):
        raise KnowledgeError("Knowledge source chunk references must be unique")

    parsed = [_split_chunk_ref(value) for value in source_chunk_refs]
    compilation_refs = sorted({compilation_ref for compilation_ref, _ in parsed})
    requested = set(source_chunk_refs)

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT d.document_id, d.parent_project_id, d.source_ref, d.source_digest,
                   d.current_extraction_id AS extraction_id, d.analysis_status,
                   cb.compilation_id, c.chunk_no, c.body,
                   COALESCE(p.structural_locator, '') AS structural_locator,
                   (
                       SELECT v.version
                         FROM document_versions v
                        WHERE v.document_id = d.document_id
                          AND v.source_digest = d.source_digest
                        ORDER BY v.version DESC
                        LIMIT 1
                   ) AS source_version
              FROM document_compilation_bindings cb
              JOIN source_documents d ON d.document_id = cb.document_id
              JOIN structured_compilations sc
                ON sc.compilation_id = cb.compilation_id
               AND sc.extraction_id = d.current_extraction_id
              JOIN chunks c
                ON c.dossier = d.dossier
               AND c.source_ref = d.source_ref
               AND c.source_digest = d.source_digest
              LEFT JOIN retrieval_chunk_projections p
                ON p.dossier = c.dossier
               AND p.source_ref = c.source_ref
               AND p.source_digest = c.source_digest
               AND p.chunk_no = c.chunk_no
             WHERE d.parent_project_id = %s
               AND cb.compilation_id = ANY(%s)
             ORDER BY d.document_id, c.chunk_no
            """,
            (parent_project_id, compilation_refs),
        )
        rows = [dict(row) for row in cur.fetchall()]

    resolved: dict[str, dict] = {}
    for row in rows:
        reference = chunk_ref(row["compilation_id"], row["chunk_no"])
        if reference in requested:
            resolved[reference] = row

    missing = [reference for reference in source_chunk_refs if reference not in resolved]
    if missing:
        raise KnowledgeError(
            "Knowledge may cite only current chunks from documents inside the primary Project scope; "
            f"unresolved: {', '.join(missing)}"
        )
    return resolved


def _write_knowledge_source_bindings(
    conn: psycopg.Connection,
    *,
    knowledge_id: str,
    source_chunk_refs: list[str],
    resolved_chunks: dict[str, dict],
    replace_existing: bool,
) -> None:
    """Persist exact source dependencies under the existing Knowledge owner."""
    if replace_existing:
        conn.execute(
            "DELETE FROM knowledge_source_chunks WHERE knowledge_id = %s",
            (knowledge_id,),
        )
    for chunk_reference in source_chunk_refs:
        source_chunk = resolved_chunks[chunk_reference]
        ordinal = int(source_chunk["chunk_no"])
        conn.execute(
            """
            INSERT INTO knowledge_source_chunks (
                knowledge_id, chunk_ref, document_id, extraction_id, ordinal,
                text_digest, body_snapshot, source_ref, source_digest, structural_locator
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                knowledge_id,
                chunk_reference,
                source_chunk["document_id"],
                source_chunk["extraction_id"],
                ordinal,
                _digest(source_chunk["body"]),
                source_chunk["body"],
                source_chunk["source_ref"],
                source_chunk["source_digest"],
                source_chunk["structural_locator"] or f"chunk/{ordinal}",
            ),
        )


def _event_replay(
    conn: psycopg.Connection,
    *,
    idempotency_key: str,
    aggregate_ref: str,
    payload_digest: str,
) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT aggregate_ref, payload_digest, result_snapshot FROM knowledge_events "
            "WHERE idempotency_key = %s",
            (idempotency_key,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    if row["aggregate_ref"] != aggregate_ref or row["payload_digest"] != payload_digest:
        raise IdempotencyConflict("idempotency key already belongs to a different immutable effect")
    return row["result_snapshot"]


def _card_from_row(conn: psycopg.Connection, row: dict) -> dict:
    document = _document_row(conn, row["document_id"])
    refs = row["source_chunk_refs"]
    return {
        "card_type": "knowledge",
        "card_id": f"card-{row['knowledge_id']}",
        "knowledge_id": row["knowledge_id"],
        "document_ref": row["document_id"],
        "parent_project_id": document["parent_project_id"],
        "title": row["title"],
        "family": row["family"],
        "markdown_digest": row["markdown_digest"],
        "source_chunk_refs": list(refs),
        "review_status": row["review_status"],
        "version": row["version"],
        "created_by": row["created_by"],
        "created_at": _iso(row["created_at"]),
        "updated_at": _iso(row["updated_at"]),
        "authority": {"is_evidence": False, "is_memory": False, "is_doctrine": False},
    }


def get_knowledge_card(conn: psycopg.Connection, knowledge_id: str) -> dict:
    return _card_from_row(conn, _knowledge_row(conn, knowledge_id))


def get_knowledge_markdown(conn: psycopg.Connection, knowledge_id: str) -> str:
    return str(_knowledge_row(conn, knowledge_id)["markdown"])


def list_knowledge_cards(conn: psycopg.Connection, parent_project_id: str) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT k.* FROM knowledge_items k
            JOIN source_documents d ON d.document_id = k.document_id
            WHERE d.parent_project_id = %s
            ORDER BY k.updated_at DESC, k.knowledge_id
            """,
            (parent_project_id,),
        )
        rows = [dict(row) for row in cur.fetchall()]
    return [_card_from_row(conn, row) for row in rows]


def get_knowledge_source_state(conn: psycopg.Connection, knowledge_id: str) -> dict:
    """Calculate whether frozen Knowledge provenance still matches current sources.

    This is a read-only maintenance projection.  It does not revise, supersede,
    review or republish Knowledge merely because a technical source changed.
    """
    item = _knowledge_row(conn, knowledge_id)
    primary = _document_row(conn, item["document_id"])
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT ksc.chunk_ref, ksc.document_id,
                   ksc.extraction_id AS bound_extraction_id,
                   ksc.source_ref AS bound_source_ref,
                   ksc.source_digest AS bound_source_digest,
                   ksc.ordinal,
                   d.source_ref AS current_source_ref,
                   d.source_digest AS current_source_digest,
                   d.current_extraction_id,
                   d.analysis_status,
                   (
                       SELECT v.version
                         FROM document_versions v
                        WHERE v.document_id = ksc.document_id
                          AND v.source_digest = ksc.source_digest
                        ORDER BY v.version DESC
                        LIMIT 1
                   ) AS bound_source_version,
                   (
                       SELECT v.version
                         FROM document_versions v
                        WHERE v.document_id = d.document_id
                          AND v.source_digest = d.source_digest
                        ORDER BY v.version DESC
                        LIMIT 1
                   ) AS current_source_version
              FROM knowledge_source_chunks ksc
              JOIN source_documents d ON d.document_id = ksc.document_id
             WHERE ksc.knowledge_id = %s
             ORDER BY ksc.document_id, ksc.ordinal, ksc.chunk_ref
            """,
            (knowledge_id,),
        )
        rows = [dict(row) for row in cur.fetchall()]

    if not rows:
        raise KnowledgeError("Knowledge has no persisted source provenance")

    grouped: dict[tuple[str, str, str], dict] = {}
    for row in rows:
        key = (
            row["document_id"],
            row["bound_extraction_id"],
            row["bound_source_digest"],
        )
        dependency = grouped.setdefault(
            key,
            {
                "document_id": row["document_id"],
                "is_primary": row["document_id"] == item["document_id"],
                "bound_source_ref": row["bound_source_ref"],
                "bound_source_digest": row["bound_source_digest"],
                "bound_source_version": row["bound_source_version"],
                "bound_extraction_id": row["bound_extraction_id"],
                "current_source_ref": row["current_source_ref"],
                "current_source_digest": row["current_source_digest"],
                "current_source_version": row["current_source_version"],
                "current_extraction_id": row["current_extraction_id"],
                "analysis_status": row["analysis_status"],
                "chunk_refs": [],
            },
        )
        dependency["chunk_refs"].append(row["chunk_ref"])

    dependencies: list[dict] = []
    for dependency in grouped.values():
        source_changed = (
            dependency["bound_source_digest"] != dependency["current_source_digest"]
        )
        extraction_changed = (
            dependency["bound_extraction_id"] != dependency["current_extraction_id"]
        )
        analysis_status = dependency["analysis_status"]
        if analysis_status == "failed":
            state = "source_failed"
        elif source_changed:
            state = "source_changed"
        elif extraction_changed:
            state = "extraction_changed"
        elif analysis_status == "needs_review":
            state = "source_needs_review"
        else:
            state = "current"
        dependency["source_changed"] = source_changed
        dependency["extraction_changed"] = extraction_changed
        dependency["state"] = state
        dependencies.append(dependency)

    dependencies.sort(
        key=lambda value: (
            not value["is_primary"],
            value["document_id"],
            value["bound_source_digest"],
        )
    )
    needs_recompile = any(
        dependency["source_changed"] or dependency["extraction_changed"]
        for dependency in dependencies
    )
    has_failed_source = any(
        dependency["state"] == "source_failed" for dependency in dependencies
    )
    has_review_source = any(
        dependency["state"] == "source_needs_review" for dependency in dependencies
    )
    if has_failed_source:
        status = "blocked_by_source"
    elif needs_recompile:
        status = "needs_recompile"
    elif has_review_source:
        status = "needs_review"
    else:
        status = "current"

    return {
        "knowledge_id": knowledge_id,
        "parent_project_id": primary["parent_project_id"],
        "knowledge_version": item["version"],
        "status": status,
        "needs_recompile": needs_recompile,
        "dependency_count": len(dependencies),
        "dependencies": dependencies,
        "authority": {
            "changes_knowledge": False,
            "is_evidence": False,
            "is_memory": False,
        },
    }


def list_document_knowledge_impacts(
    conn: psycopg.Connection, document_id: str
) -> dict:
    """List Knowledge items whose frozen provenance cites one technical document."""
    document = _document_row(conn, document_id)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT knowledge_id
              FROM knowledge_source_chunks
             WHERE document_id = %s
             ORDER BY knowledge_id
            """,
            (document_id,),
        )
        knowledge_ids = [row[0] for row in cur.fetchall()]
    return {
        "document_id": document_id,
        "parent_project_id": document["parent_project_id"],
        "knowledge": [
            get_knowledge_source_state(conn, knowledge_id)
            for knowledge_id in knowledge_ids
        ],
        "authority": {
            "changes_knowledge": False,
            "is_evidence": False,
            "is_memory": False,
        },
    }


def _lock_knowledge_source_dependencies(
    conn: psycopg.Connection,
    knowledge_id: str,
) -> list[str]:
    """Serialize recompile apply against technical source/binding replacement.

    Ingestion updates source_documents before document_compilation_bindings in
    one transaction. Taking the same locks in that order makes the accepted
    recompile observe either the complete previous technical state or the
    complete next one, never a mixture across the policy/persistence window.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT ksc.document_id
              FROM knowledge_source_chunks ksc
             WHERE ksc.knowledge_id = %s
             ORDER BY ksc.document_id
            """,
            (knowledge_id,),
        )
        document_ids = [row[0] for row in cur.fetchall()]
    if not document_ids:
        raise KnowledgeError("Knowledge has no source dependencies to lock")

    # Lock one row at a time in explicit document-id order. The ingestion owner
    # writes documents in this same order, preventing a multi-source deadlock.
    for document_id in document_ids:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT document_id FROM source_documents "
                "WHERE document_id = %s FOR UPDATE",
                (document_id,),
            )
            if cur.fetchone() is None:
                raise KnowledgeError(
                    f"Knowledge source dependency disappeared: {document_id}"
                )
    for document_id in document_ids:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT document_id FROM document_compilation_bindings "
                "WHERE document_id = %s FOR UPDATE",
                (document_id,),
            )
            # A missing binding is handled by the context-ready check below;
            # the source row lock prevents ingestion from installing one midway.
            cur.fetchone()
    return document_ids


def build_knowledge_recompile_context(
    conn: psycopg.Connection, knowledge_id: str
) -> dict:
    """Build exact old/new context for the Knowledge's existing dependencies.

    The old side is the exact body snapshot of every chunk the Knowledge cited.
    For each changed dependency the new side is the complete current technical
    chunk version. The bound is the Knowledge's already-cited documents, never
    a broad Project retrieval.
    """
    item = _knowledge_row(conn, knowledge_id)
    state = get_knowledge_source_state(conn, knowledge_id)
    markdown = str(item["markdown"])

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT ksc.document_id, ksc.chunk_ref, ksc.extraction_id,
                   ksc.source_ref, ksc.source_digest, ksc.ordinal,
                   ksc.text_digest, ksc.body_snapshot, ksc.structural_locator,
                   oldc.body AS old_body
              FROM knowledge_source_chunks ksc
              JOIN source_documents d ON d.document_id = ksc.document_id
              LEFT JOIN chunks oldc
                ON oldc.dossier = d.dossier
               AND oldc.source_ref = ksc.source_ref
               AND oldc.source_digest = ksc.source_digest
               AND oldc.chunk_no = ksc.ordinal
             WHERE ksc.knowledge_id = %s
             ORDER BY ksc.document_id, ksc.ordinal, ksc.chunk_ref
            """,
            (knowledge_id,),
        )
        frozen_rows = [dict(row) for row in cur.fetchall()]

    if not frozen_rows:
        raise KnowledgeError("Knowledge has no source dependencies to recompile")

    dependency_state = {
        dependency["document_id"]: dependency
        for dependency in state["dependencies"]
    }
    document_ids = sorted(dependency_state)

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT d.document_id, d.source_ref, d.source_digest,
                   d.current_extraction_id AS extraction_id,
                   d.analysis_status, cb.compilation_id,
                   c.chunk_no, c.body,
                   COALESCE(p.structural_locator, '') AS structural_locator
              FROM source_documents d
              JOIN document_compilation_bindings cb
                ON cb.document_id = d.document_id
              JOIN structured_compilations sc
                ON sc.compilation_id = cb.compilation_id
               AND sc.extraction_id = d.current_extraction_id
              JOIN chunks c
                ON c.dossier = d.dossier
               AND c.source_ref = d.source_ref
               AND c.source_digest = d.source_digest
              LEFT JOIN retrieval_chunk_projections p
                ON p.dossier = c.dossier
               AND p.source_ref = c.source_ref
               AND p.source_digest = c.source_digest
               AND p.chunk_no = c.chunk_no
             WHERE d.document_id = ANY(%s)
             ORDER BY d.document_id, c.chunk_no
            """,
            (document_ids,),
        )
        current_rows = [dict(row) for row in cur.fetchall()]

    frozen_by_document: dict[str, list[dict]] = {}
    for row in frozen_rows:
        frozen_by_document.setdefault(row["document_id"], []).append(row)

    current_by_document: dict[str, list[dict]] = {}
    for row in current_rows:
        current_by_document.setdefault(row["document_id"], []).append(row)

    projected_dependencies: list[dict] = []
    allowed_source_chunk_refs: list[str] = []
    # The old side of the diff is part of the candidate basis too. A missing
    # historical chunk or a body that no longer matches the frozen provenance
    # digest makes the context incomplete rather than silently compiling from
    # an unverifiable prior state.
    context_complete = all(
        (row["body_snapshot"] if row["body_snapshot"] is not None else row["old_body"])
        is not None
        and _digest(
            row["body_snapshot"]
            if row["body_snapshot"] is not None
            else row["old_body"]
        )
        == row["text_digest"]
        for row in frozen_rows
    )

    for document_id in document_ids:
        dependency = dependency_state[document_id]
        frozen = frozen_by_document.get(document_id, [])
        current = current_by_document.get(document_id, [])
        selected_current: list[dict] = []

        if dependency["state"] == "current":
            selected_refs = set(dependency["chunk_refs"])
            for row in current:
                reference = chunk_ref(row["compilation_id"], row["chunk_no"])
                if reference in selected_refs:
                    selected_current.append(row)
        elif dependency["state"] in {
            "source_changed",
            "extraction_changed",
            "source_needs_review",
        }:
            # Exact new side: expose the complete current version of the
            # already-dependent document. This catches moved/new sections that
            # no locator/ordinal-neighbour heuristic can prove equivalent.
            selected_current = list(current)
        else:
            selected_current = []

        if dependency["state"] != "source_failed" and not selected_current:
            context_complete = False
        frozen_projection = [
            {
                "chunk_ref": row["chunk_ref"],
                "source_ref": row["source_ref"],
                "source_digest": row["source_digest"],
                "extraction_id": row["extraction_id"],
                "ordinal": int(row["ordinal"]),
                "text_digest": row["text_digest"],
                "structural_locator": row["structural_locator"],
                "body": (
                    row["body_snapshot"]
                    if row["body_snapshot"] is not None
                    else row["old_body"]
                ),
            }
            for row in frozen
        ]
        current_projection: list[dict] = []
        for row in selected_current:
            reference = chunk_ref(row["compilation_id"], row["chunk_no"])
            allowed_source_chunk_refs.append(reference)
            current_projection.append(
                {
                    "chunk_ref": reference,
                    "source_ref": row["source_ref"],
                    "source_digest": row["source_digest"],
                    "extraction_id": row["extraction_id"],
                    "ordinal": int(row["chunk_no"]),
                    "text_digest": _digest(row["body"]),
                    "structural_locator": row["structural_locator"],
                    "body": row["body"],
                }
            )

        projected_dependencies.append(
            {
                **dependency,
                "frozen_chunks": frozen_projection,
                "current_candidate_chunks": current_projection,
            }
        )

    allowed_source_chunk_refs = list(dict.fromkeys(allowed_source_chunk_refs))
    basis = {
        "knowledge_id": knowledge_id,
        "knowledge_version": item["version"],
        "markdown_digest": item["markdown_digest"],
        "source_state_status": state["status"],
        "dependencies": [
            {
                "document_id": dependency["document_id"],
                "state": dependency["state"],
                "bound_source_digest": dependency["bound_source_digest"],
                "bound_extraction_id": dependency["bound_extraction_id"],
                "current_source_digest": dependency["current_source_digest"],
                "current_extraction_id": dependency["current_extraction_id"],
                "analysis_status": dependency["analysis_status"],
                "frozen_chunks": [
                    {
                        "chunk_ref": chunk["chunk_ref"],
                        "text_digest": chunk["text_digest"],
                        "observed_body_digest": (
                            _digest(chunk["body"])
                            if chunk["body"] is not None
                            else None
                        ),
                        "structural_locator": chunk["structural_locator"],
                    }
                    for chunk in dependency["frozen_chunks"]
                ],
                "current_candidate_chunks": [
                    {
                        "chunk_ref": chunk["chunk_ref"],
                        "text_digest": chunk["text_digest"],
                        "structural_locator": chunk["structural_locator"],
                    }
                    for chunk in dependency["current_candidate_chunks"]
                ],
            }
            for dependency in projected_dependencies
        ],
    }
    context_digest = _payload_digest(basis)
    ready = (
        state["needs_recompile"]
        and state["status"] != "blocked_by_source"
        and context_complete
        and bool(allowed_source_chunk_refs)
    )

    return {
        "knowledge_id": knowledge_id,
        "parent_project_id": state["parent_project_id"],
        "base_version": item["version"],
        "base_markdown": markdown,
        "base_markdown_digest": item["markdown_digest"],
        "source_state_status": state["status"],
        "needs_recompile": state["needs_recompile"],
        "ready_for_candidate": ready,
        "context_complete": context_complete,
        "context_digest": context_digest,
        "allowed_source_chunk_refs": allowed_source_chunk_refs,
        "dependencies": projected_dependencies,
        "authority": {
            "changes_knowledge": False,
            "selects_sources": False,
            "is_evidence": False,
            "is_memory": False,
        },
    }


def create_recompile_request(
    conn: psycopg.Connection,
    *,
    request_id: str,
    knowledge_id: str,
    requested_by: str,
    idempotency_key: str,
) -> dict:
    """Record one full-document recompile through the existing edit-request owner."""

    # Own the outer transaction. Context reads happen before create_edit_request();
    # without this boundary they would start an implicit transaction and turn the
    # inner transaction into a savepoint that cockpit_api.with_connection() would
    # roll back when it closes the connection.
    with conn.transaction():
        # Replays must be stable even when the Knowledge/source state has moved
        # after the original request was created. The request row is the durable
        # effect; the potentially stale source context is read separately through
        # get_recompile_context_for_request().
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT request_id, knowledge_id, requested_by, recompile_context_digest
                  FROM knowledge_edit_requests
                 WHERE request_idempotency_key = %s
                """,
                (idempotency_key,),
            )
            replay = cur.fetchone()
        if replay is not None:
            if (
                replay["request_id"] != request_id
                or replay["knowledge_id"] != knowledge_id
                or replay["requested_by"] != requested_by
                or not replay["recompile_context_digest"]
            ):
                raise IdempotencyConflict(
                    "recompile request idempotency key belongs to a different immutable effect"
                )
            request = get_edit_request(conn, request_id)
            result = {
                "edit_request": request,
                "recompile_context_digest": request["recompile_context_digest"],
                "candidate_only": True,
                "applies_automatically": False,
            }
        else:
            context = build_knowledge_recompile_context(conn, knowledge_id)
            if not context["needs_recompile"]:
                raise KnowledgeError("Knowledge is current; no recompile request is needed")
            if not context["ready_for_candidate"]:
                raise KnowledgeError(
                    "Knowledge recompile context is incomplete or blocked by a source"
                )
            markdown = context["base_markdown"]
            request = create_edit_request(
                conn,
                request_id=request_id,
                knowledge_id=knowledge_id,
                instruction_kind="verify",
                instruction=(
                    "Recompile the complete Knowledge Markdown against the bounded current "
                    "source context. Preserve supported content, revise superseded claims, "
                    "keep unresolved contradictions explicit, and cite only source chunk "
                    "references admitted by the recompile context."
                ),
                base_version=context["base_version"],
                selection_start=0,
                selection_end=len(markdown),
                selected_text=markdown,
                requested_by=requested_by,
                idempotency_key=idempotency_key,
                recompile_context_digest=context["context_digest"],
            )
            result = {
                "edit_request": request,
                "recompile_context_digest": context["context_digest"],
                "candidate_only": True,
                "applies_automatically": False,
            }
    return result


def get_recompile_context_for_request(
    conn: psycopg.Connection, request_id: str
) -> dict:
    request = get_edit_request(conn, request_id)
    expected = request.get("recompile_context_digest")
    if not expected:
        raise KnowledgeError("edit request is not a Knowledge recompile request")
    context = build_knowledge_recompile_context(conn, request["knowledge_id"])
    if context["context_digest"] != expected or not context["ready_for_candidate"]:
        raise StaleKnowledgeWrite(
            "Knowledge recompile source context changed after the request was queued"
        )
    return context


def get_recompile_candidate(
    conn: psycopg.Connection, request_id: str
) -> dict:
    """Project one proposed recompile as a human-readable candidate/diff."""
    request = get_edit_request(conn, request_id)
    if not request.get("recompile_context_digest"):
        raise KnowledgeError("edit request is not a Knowledge recompile request")
    if request["status"] != "proposed" or not request.get("replacement_markdown"):
        raise KnowledgeError("Knowledge recompile request has no reviewable proposal")

    context = get_recompile_context_for_request(conn, request_id)
    replacement = str(request["replacement_markdown"])
    diff = "".join(
        difflib.unified_diff(
            context["base_markdown"].splitlines(keepends=True),
            replacement.splitlines(keepends=True),
            fromfile=f"{request['knowledge_id']}@v{request['base_version']}",
            tofile=f"{request['knowledge_id']}@candidate-v{request['base_version'] + 1}",
        )
    )
    return {
        "request_id": request_id,
        "knowledge_id": request["knowledge_id"],
        "base_version": request["base_version"],
        "recompile_context_digest": request["recompile_context_digest"],
        "replacement_markdown": replacement,
        "replacement_source_chunk_refs": list(
            request.get("replacement_source_chunk_refs") or []
        ),
        "diff": diff,
        "authority": {
            "changes_knowledge": False,
            "accepts_candidate": False,
            "is_evidence": False,
            "is_memory": False,
        },
    }


def _knowledge_content_snapshot(
    conn: psycopg.Connection,
    knowledge_id: str,
) -> dict:
    """Freeze editorial content and exact source bindings for revision history."""
    item = _knowledge_row(conn, knowledge_id)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT chunk_ref, document_id, extraction_id, ordinal, text_digest,
                   body_snapshot, source_ref, source_digest, structural_locator
              FROM knowledge_source_chunks
             WHERE knowledge_id = %s
             ORDER BY document_id, ordinal, chunk_ref
            """,
            (knowledge_id,),
        )
        sources = [dict(row) for row in cur.fetchall()]
    return {
        "knowledge_id": knowledge_id,
        "version": item["version"],
        "title": item["title"],
        "family": item["family"],
        "review_status": item["review_status"],
        "markdown": item["markdown"],
        "markdown_digest": item["markdown_digest"],
        "source_chunk_refs": list(item["source_chunk_refs"]),
        "source_dependencies": sources,
    }


def _insert_event(
    conn: psycopg.Connection,
    *,
    aggregate_ref: str,
    event_type: str,
    actor: str,
    actor_kind: str,
    expected_version: int,
    idempotency_key: str,
    payload_digest: str,
    snapshot: dict,
    base_content_snapshot: dict | None = None,
    resulting_content_snapshot: dict | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO knowledge_events (
            event_id, aggregate_ref, event_type, actor, actor_kind,
            expected_version, resulting_version, idempotency_key,
            payload_digest, result_snapshot, base_content_snapshot,
            resulting_content_snapshot
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb
        )
        """,
        (
            f"event-{uuid.uuid4().hex}", aggregate_ref, event_type, actor, actor_kind,
            expected_version, expected_version + 1, idempotency_key,
            payload_digest,
            json.dumps(snapshot, ensure_ascii=False),
            (
                json.dumps(base_content_snapshot, ensure_ascii=False)
                if base_content_snapshot is not None
                else None
            ),
            (
                json.dumps(resulting_content_snapshot, ensure_ascii=False)
                if resulting_content_snapshot is not None
                else None
            ),
        ),
    )


def publish_knowledge(
    conn: psycopg.Connection,
    *,
    knowledge_id: str,
    document_id: str,
    title: str,
    family: str,
    markdown: str,
    source_chunk_refs: list[str],
    created_by: str,
    actor_kind: str,
    idempotency_key: str,
    expected_version: int = 0,
    review_status: str = "generated_unreviewed",
    policy_client: PolicyClient | None = None,
    decision_payload: dict[str, Any] | None = None,
    required_ceiling: str = "C2",
) -> dict:
    """Publish a Knowledge item; `review_status="reviewed"` is a claim, not a fact.

    `document_id` remains the primary source anchor for compatibility, while
    `source_chunk_refs` may cite additional current technical documents inside
    that same Project.  Every cited chunk is frozen independently in
    `knowledge_source_chunks`; at least one citation must belong to the primary
    anchor.  This adds multi-source synthesis without creating a second source
    graph or allowing cross-project citation by chunk identity alone.

    `family`, `actor_kind` and `review_status` are each checked only against a
    vocabulary of permitted strings. A holder of the editor key could
    otherwise publish a Knowledge item that already reads as professionally
    reviewed, attributed to anyone. Candidate publication —
    `generated_unreviewed`, `needs_review`, `superseded` — asserts nothing a
    reader would take as a professional claim, so it needs no gate. Asserting
    `review_status="reviewed"` at publication is the professional claim this
    module cannot verify on its own, so that specific request routes through
    the chokepoint when `policy_client` is supplied; every other
    `review_status` publishes exactly as before.
    """
    if expected_version != 0:
        raise StaleKnowledgeWrite("first publication requires expected_version 0")
    if not title.strip() or not markdown.strip() or not knowledge_id:
        raise KnowledgeError("knowledge_id, title and Markdown are required")
    if family not in FAMILIES or review_status not in REVIEW_STATUSES or actor_kind not in ACTOR_KINDS:
        raise KnowledgeError("invalid Knowledge family, review status or actor kind")
    payload = {
        "knowledge_id": knowledge_id, "document_id": document_id, "title": title,
        "family": family, "markdown": markdown, "source_chunk_refs": source_chunk_refs,
        "created_by": created_by, "actor_kind": actor_kind, "review_status": review_status,
        "expected_version": expected_version,
    }
    pdigest = _payload_digest(payload)
    with conn.transaction():
        replay = _event_replay(
            conn, idempotency_key=idempotency_key, aggregate_ref=knowledge_id, payload_digest=pdigest
        )
        if replay is not None:
            return replay
        document = _document_row(conn, document_id)
        resolved_chunks = _resolve_current_source_chunks(
            conn,
            parent_project_id=document["parent_project_id"],
            source_chunk_refs=source_chunk_refs,
        )
        if not any(
            chunk["document_id"] == document_id
            for chunk in resolved_chunks.values()
        ):
            raise KnowledgeError(
                "Knowledge must cite at least one current chunk from its primary source document"
            )
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM knowledge_items WHERE knowledge_id = %s", (knowledge_id,))
            if cur.fetchone() is not None:
                raise IdempotencyConflict(
                    "Knowledge identity already exists; retry the original immutable idempotency key"
                )
        if review_status == "reviewed" and policy_client is not None:
            _gate_knowledge_write(
                policy_client,
                intent="publish_knowledge_reviewed",
                scope={"scope_type": "project", "scope_id": document["parent_project_id"]},
                object_ref=f"knowledge_item:{knowledge_id}",
                expected_digest=pdigest,
                decision_payload=decision_payload,
                actor=created_by,
                required_ceiling=required_ceiling,
            )
        conn.execute(
            """
            INSERT INTO knowledge_items (
                knowledge_id, document_id, source_version, source_digest, extraction_id,
                title, family, markdown, markdown_digest,
                source_chunk_refs, review_status, version, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, 1, %s)
            """,
            (
                knowledge_id, document_id, document["source_version"],
                document["source_digest"], document["extraction_id"],
                title.strip(), family, markdown, _digest(markdown),
                json.dumps(source_chunk_refs), review_status, created_by,
            ),
        )
        _write_knowledge_source_bindings(
            conn,
            knowledge_id=knowledge_id,
            source_chunk_refs=source_chunk_refs,
            resolved_chunks=resolved_chunks,
            replace_existing=False,
        )
        snapshot = get_knowledge_card(conn, knowledge_id)
        resulting_content_snapshot = _knowledge_content_snapshot(conn, knowledge_id)
        _insert_event(
            conn, aggregate_ref=knowledge_id, event_type="knowledge_published",
            actor=created_by, actor_kind=actor_kind, expected_version=0,
            idempotency_key=idempotency_key, payload_digest=pdigest, snapshot=snapshot,
            resulting_content_snapshot=resulting_content_snapshot,
        )
        validate_document_knowledge_slice(conn, knowledge_id)
    return snapshot


def revise_knowledge(
    conn: psycopg.Connection,
    *,
    knowledge_id: str,
    markdown: str,
    expected_version: int,
    actor: str,
    actor_kind: str,
    idempotency_key: str,
    review_status: str | None = None,
    source_chunk_refs: list[str] | None = None,
) -> dict:
    if not markdown.strip() or actor_kind not in ACTOR_KINDS:
        raise KnowledgeError("non-empty Markdown and a valid actor kind are required")
    if review_status is not None and review_status not in REVIEW_STATUSES:
        raise KnowledgeError("invalid Knowledge review status")
    payload = {
        "knowledge_id": knowledge_id, "markdown": markdown,
        "expected_version": expected_version, "actor": actor, "actor_kind": actor_kind,
        "review_status": review_status,
    }
    # Preserve the pre-Slice-2 idempotency digest for ordinary revisions.
    # Provenance participates in the immutable effect only when this is an
    # actual recompile/rebind.
    if source_chunk_refs is not None:
        payload["source_chunk_refs"] = source_chunk_refs
    pdigest = _payload_digest(payload)
    with conn.transaction():
        replay = _event_replay(
            conn, idempotency_key=idempotency_key, aggregate_ref=knowledge_id, payload_digest=pdigest
        )
        if replay is not None:
            return replay
        row = _knowledge_row(conn, knowledge_id, lock=True)
        if row["version"] != expected_version:
            raise StaleKnowledgeWrite(
                f"stale Knowledge version: expected {expected_version}, current {row['version']}"
            )
        base_content_snapshot = _knowledge_content_snapshot(conn, knowledge_id)
        next_status = review_status or row["review_status"]
        resolved_chunks: dict[str, dict] | None = None
        primary_document: dict | None = None
        if source_chunk_refs is not None:
            primary_document = _document_row(conn, row["document_id"])
            resolved_chunks = _resolve_current_source_chunks(
                conn,
                parent_project_id=primary_document["parent_project_id"],
                source_chunk_refs=source_chunk_refs,
            )
            if not any(
                chunk["document_id"] == row["document_id"]
                for chunk in resolved_chunks.values()
            ):
                raise KnowledgeError(
                    "Knowledge recompile must retain at least one current chunk "
                    "from its primary source document"
                )

        with conn.cursor() as cur:
            if source_chunk_refs is None:
                cur.execute(
                    """
                    UPDATE knowledge_items
                       SET markdown = %s, markdown_digest = %s, review_status = %s,
                           version = version + 1, updated_at = CURRENT_TIMESTAMP
                     WHERE knowledge_id = %s AND version = %s
                    """,
                    (markdown, _digest(markdown), next_status, knowledge_id, expected_version),
                )
            else:
                assert primary_document is not None
                cur.execute(
                    """
                    UPDATE knowledge_items
                       SET markdown = %s, markdown_digest = %s, review_status = %s,
                           source_version = %s, source_digest = %s, extraction_id = %s,
                           source_chunk_refs = %s::jsonb,
                           version = version + 1, updated_at = CURRENT_TIMESTAMP
                     WHERE knowledge_id = %s AND version = %s
                    """,
                    (
                        markdown,
                        _digest(markdown),
                        next_status,
                        primary_document["source_version"],
                        primary_document["source_digest"],
                        primary_document["extraction_id"],
                        json.dumps(source_chunk_refs),
                        knowledge_id,
                        expected_version,
                    ),
                )
            if cur.rowcount != 1:
                raise StaleKnowledgeWrite("Knowledge changed before the revision was persisted")

        if source_chunk_refs is not None:
            assert resolved_chunks is not None
            _write_knowledge_source_bindings(
                conn,
                knowledge_id=knowledge_id,
                source_chunk_refs=source_chunk_refs,
                resolved_chunks=resolved_chunks,
                replace_existing=True,
            )

        snapshot = get_knowledge_card(conn, knowledge_id)
        resulting_content_snapshot = _knowledge_content_snapshot(conn, knowledge_id)
        event_type = (
            "knowledge_review_status_changed"
            if (
                markdown == row["markdown"]
                and next_status != row["review_status"]
                and source_chunk_refs is None
            )
            else "knowledge_revised"
        )
        _insert_event(
            conn, aggregate_ref=knowledge_id, event_type=event_type,
            actor=actor, actor_kind=actor_kind, expected_version=expected_version,
            idempotency_key=idempotency_key, payload_digest=pdigest, snapshot=snapshot,
            base_content_snapshot=base_content_snapshot,
            resulting_content_snapshot=resulting_content_snapshot,
        )
        validate_document_knowledge_slice(conn, knowledge_id)
    return snapshot


def create_edit_request(
    conn: psycopg.Connection,
    *,
    request_id: str,
    knowledge_id: str,
    instruction_kind: str,
    instruction: str,
    base_version: int,
    selection_start: int,
    selection_end: int,
    selected_text: str,
    requested_by: str,
    idempotency_key: str,
    replacement_markdown: str | None = None,
    recompile_context_digest: str | None = None,
) -> dict:
    if instruction_kind not in INSTRUCTION_KINDS or not instruction.strip():
        raise KnowledgeError("invalid or empty intelligent-edit instruction")
    payload = {
        "request_id": request_id, "knowledge_id": knowledge_id,
        "instruction_kind": instruction_kind, "instruction": instruction,
        "base_version": base_version, "selection_start": selection_start,
        "selection_end": selection_end, "selected_text": selected_text,
        "requested_by": requested_by, "replacement_markdown": replacement_markdown,
    }
    # Existing ordinary edit requests keep their historical payload digest.
    # Only recompile requests bind the additional source-context identity.
    if recompile_context_digest is not None:
        payload["recompile_context_digest"] = recompile_context_digest
    pdigest = _payload_digest(payload)
    with conn.transaction():
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT request_payload_digest FROM knowledge_edit_requests "
                "WHERE request_idempotency_key = %s",
                (idempotency_key,),
            )
            replay = cur.fetchone()
        if replay is not None:
            if replay["request_payload_digest"] != pdigest:
                raise IdempotencyConflict("edit request idempotency key has different content")
            return get_edit_request(conn, request_id)
        item = _knowledge_row(conn, knowledge_id, lock=True)
        if item["version"] != base_version:
            raise StaleKnowledgeWrite(
                f"offline edit is based on version {base_version}; current version is {item['version']}"
            )
        markdown = item["markdown"]
        if selection_start < 0 or selection_end < selection_start or selection_end > len(markdown):
            raise KnowledgeError("selection range is outside the Markdown snapshot")
        if markdown[selection_start:selection_end] != selected_text:
            raise StaleKnowledgeWrite("selected text no longer matches the declared base snapshot")
        status = "proposed" if replacement_markdown is not None else "queued_for_hermes"
        conn.execute(
            """
            INSERT INTO knowledge_edit_requests (
                request_id, knowledge_id, instruction_kind, instruction, base_version,
                selection_start, selection_end, selected_text_digest,
                replacement_markdown, recompile_context_digest, status, requested_by,
                request_idempotency_key, request_payload_digest
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                request_id, knowledge_id, instruction_kind, instruction, base_version,
                selection_start, selection_end, _digest(selected_text), replacement_markdown,
                recompile_context_digest, status, requested_by, idempotency_key, pdigest,
            ),
        )
    return get_edit_request(conn, request_id)


def get_edit_request(
    conn: psycopg.Connection,
    request_id: str,
    *,
    lock: bool = False,
) -> dict:
    suffix = " FOR UPDATE" if lock else ""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"SELECT * FROM knowledge_edit_requests WHERE request_id = %s{suffix}",
            (request_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise KnowledgeNotFound(f"unknown intelligent edit request: {request_id}")
    result = dict(row)
    for key in ("created_at", "updated_at"):
        result[key] = _iso(result[key])
    return result


def list_edit_requests(
    conn: psycopg.Connection,
    *,
    status: str = "queued_for_hermes",
    limit: int = 100,
) -> list[dict]:
    if status not in {"queued_for_hermes", "proposed", "applied", "conflict", "rejected"}:
        raise KnowledgeError("invalid intelligent edit request status")
    if limit < 1 or limit > 500:
        raise KnowledgeError("edit request limit must be between 1 and 500")
    with conn.cursor() as cur:
        cur.execute(
            "SELECT request_id FROM knowledge_edit_requests WHERE status = %s "
            "ORDER BY created_at ASC LIMIT %s",
            (status, limit),
        )
        request_ids = [row[0] for row in cur.fetchall()]
    return [get_edit_request(conn, request_id) for request_id in request_ids]


def complete_edit_request(
    conn: psycopg.Connection,
    *,
    request_id: str,
    replacement_markdown: str,
    replacement_source_chunk_refs: list[str] | None = None,
) -> dict:
    """Hermes fills in the proposal it was queued for; nothing else may call this.

    The only status this may act from is `queued_for_hermes` — the one status
    `create_edit_request` sets when it queues a request without a proposal
    already in hand. Without this guard, a request that a human had already
    moved to `rejected` (`knowledge_edit_variants.reject_request`) could be
    completed again here, silently returning it to `proposed` and reaching the
    editor-keyed apply route — un-rejecting a decision with no trace beside
    the rejection event that was overwritten.
    """
    if not replacement_markdown:
        raise KnowledgeError("Hermes proposal must contain replacement Markdown")
    with conn.transaction():
        # The terminal-status check and proposal transition share the request
        # row lock. A concurrent human reject/select/apply cannot race this
        # read and then be overwritten by the Hermes proposal update.
        request = get_edit_request(conn, request_id, lock=True)
        normalized_refs = (
            list(replacement_source_chunk_refs)
            if replacement_source_chunk_refs is not None
            else None
        )
        if (
            request["status"] == "proposed"
            and request["replacement_markdown"] == replacement_markdown
            and request.get("replacement_source_chunk_refs") == normalized_refs
        ):
            return request
        if request["status"] != "queued_for_hermes":
            raise KnowledgeError(
                f"edit request {request_id} is not awaiting a Hermes proposal "
                f"(status: {request['status']!r}); a decided request cannot be "
                "reopened through this path"
            )
        item = _knowledge_row(conn, request["knowledge_id"], lock=True)
        status = "proposed" if item["version"] == request["base_version"] else "conflict"

        recompile_digest = request.get("recompile_context_digest")
        if recompile_digest:
            if not normalized_refs:
                raise KnowledgeError(
                    "Knowledge recompile proposal must declare replacement source chunk refs"
                )
            context = build_knowledge_recompile_context(conn, request["knowledge_id"])
            if (
                context["context_digest"] != recompile_digest
                or not context["ready_for_candidate"]
            ):
                status = "conflict"
            else:
                allowed = set(context["allowed_source_chunk_refs"])
                if not set(normalized_refs).issubset(allowed):
                    raise KnowledgeError(
                        "Knowledge recompile proposal cites chunks outside its bounded context"
                    )
                primary = _knowledge_row(conn, request["knowledge_id"])
                if not any(
                    chunk["document_id"] == primary["document_id"]
                    for chunk in _resolve_current_source_chunks(
                        conn,
                        parent_project_id=context["parent_project_id"],
                        source_chunk_refs=normalized_refs,
                    ).values()
                ):
                    raise KnowledgeError(
                        "Knowledge recompile proposal must retain a primary-source chunk"
                    )
        elif normalized_refs is not None:
            raise KnowledgeError(
                "ordinary intelligent edits cannot replace Knowledge source provenance"
            )

        conn.execute(
            "UPDATE knowledge_edit_requests SET replacement_markdown = %s, "
            "replacement_source_chunk_refs = %s::jsonb, status = %s, "
            "updated_at = CURRENT_TIMESTAMP WHERE request_id = %s",
            (
                replacement_markdown,
                json.dumps(normalized_refs) if normalized_refs is not None else None,
                status,
                request_id,
            ),
        )
    return get_edit_request(conn, request_id)


def apply_edit_request(
    conn: psycopg.Connection,
    *,
    request_id: str,
    actor: str,
    actor_kind: str,
    idempotency_key: str,
    on_applied: Callable[[psycopg.Connection, dict], None] | None = None,
    policy_client: PolicyClient | None = None,
    decision_payload: dict[str, Any] | None = None,
    required_ceiling: str = "C2",
) -> dict:
    """Apply a proposed edit request; the whole effect commits or none of it does.

    ``on_applied`` runs inside the apply transaction, after the Knowledge
    revision and the status transition, receiving the connection and the result.
    A caller that must record its own audit of the application — the A/B variant
    review does — uses it so that audit cannot survive a rolled-back apply, or
    be lost by one that succeeded.

    This is the point where the Knowledge Markdown actually changes, which is
    why the chokepoint belongs here rather than at `create_edit_request` (a
    candidate proposal, consequential of nothing) or `complete_edit_request`
    (Hermes filling in what it was asked for, not deciding anything). Nothing
    upstream of this function has to decide anything for a request to arrive
    here `proposed`; when `policy_client` is supplied, the decision it
    validates must cover this exact replacement applied to this exact
    selection of this exact Knowledge version.
    """
    apply_payload_digest = _payload_digest(
        {
            "request_id": request_id,
            "actor": actor,
            "actor_kind": actor_kind,
            "idempotency_key": idempotency_key,
        }
    )
    # The Knowledge revision, the request's status transition and the stored
    # result snapshot are one effect and commit together. Splitting them across
    # transactions left two windows in which a crash produced a revised
    # Knowledge item whose edit request still read `proposed`, so the same
    # replacement could be applied a second time.
    #
    # A staleness conflict is the opposite requirement: it must *survive* the
    # rollback of the attempt that discovered it, otherwise the request stays
    # `proposed` and is retried forever against a Knowledge item that moved. It
    # is therefore recorded in its own transaction, after the attempt unwinds,
    # rather than by committing the caller's work first.
    try:
        with conn.transaction():
            # Own the transaction before the first database read. On psycopg's
            # default autocommit=False a SELECT performed first would create an
            # implicit outer transaction and reduce this block to a savepoint;
            # cockpit_api then closes the connection and would roll the applied
            # Knowledge back despite returning success.
            # Serialize all applies and review-state changes on the request
            # before locking the Knowledge item. Without this row lock, two apply
            # calls can both observe "proposed"; the loser may later mark an
            # already-applied request as conflict after waiting on Knowledge.
            request = get_edit_request(conn, request_id, lock=True)
            if request["status"] == "applied":
                if (
                    request["apply_idempotency_key"] != idempotency_key
                    or request["apply_payload_digest"] != apply_payload_digest
                ):
                    raise IdempotencyConflict(
                        "edit request was already applied by a different effect"
                    )
                return request["apply_result_snapshot"]
            if request["status"] == "conflict":
                raise StaleKnowledgeWrite(
                    "edit request already conflicts with a newer Knowledge version"
                )
            if request["status"] != "proposed" or request["replacement_markdown"] is None:
                raise KnowledgeError("edit request has no applicable Hermes proposal")

            item = _knowledge_row(conn, request["knowledge_id"], lock=True)
            start, end = request["selection_start"], request["selection_end"]
            selected = item["markdown"][start:end]
            if (
                item["version"] != request["base_version"]
                or _digest(selected) != request["selected_text_digest"]
            ):
                raise _EditRequestConflict

            recompile_digest = request.get("recompile_context_digest")
            replacement_source_chunk_refs = request.get("replacement_source_chunk_refs")
            if recompile_digest:
                # Hold the existing technical source owners stable from final
                # context verification through authorization and provenance
                # persistence. Ingestion takes these locks in the same order.
                _lock_knowledge_source_dependencies(conn, request["knowledge_id"])
                context = build_knowledge_recompile_context(
                    conn, request["knowledge_id"]
                )
                if (
                    context["context_digest"] != recompile_digest
                    or not context["ready_for_candidate"]
                    or not replacement_source_chunk_refs
                    or not set(replacement_source_chunk_refs).issubset(
                        set(context["allowed_source_chunk_refs"])
                    )
                ):
                    raise _EditRequestConflict

            # All staleness checks, including the recompile source basis, are
            # complete before asking the decision point to authorize the exact
            # effect. The recompile digest is part of that effect identity.
            if policy_client is not None:
                document = _document_row(conn, item["document_id"])
                apply_payload = {
                    "request_id": request_id,
                    "knowledge_id": request["knowledge_id"],
                    "base_version": request["base_version"],
                    "selected_text_digest": request["selected_text_digest"],
                    "replacement_markdown": request["replacement_markdown"],
                }
                if recompile_digest:
                    apply_payload["recompile_context_digest"] = recompile_digest
                    apply_payload["replacement_source_chunk_refs"] = (
                        replacement_source_chunk_refs
                    )
                apply_digest = _payload_digest(apply_payload)
                _gate_knowledge_write(
                    policy_client,
                    intent="apply_edit_request",
                    scope={
                        "scope_type": "project",
                        "scope_id": document["parent_project_id"],
                    },
                    object_ref=f"knowledge_edit_request:{request_id}",
                    expected_digest=apply_digest,
                    decision_payload=decision_payload,
                    actor=actor,
                    required_ceiling=required_ceiling,
                )

            revised = (
                item["markdown"][:start]
                + request["replacement_markdown"]
                + item["markdown"][end:]
            )
            snapshot = revise_knowledge(
                conn,
                knowledge_id=request["knowledge_id"],
                markdown=revised,
                expected_version=request["base_version"],
                actor=actor,
                actor_kind=actor_kind,
                idempotency_key=idempotency_key,
                source_chunk_refs=(
                    list(replacement_source_chunk_refs)
                    if recompile_digest
                    else None
                ),
            )
            conn.execute(
                "UPDATE knowledge_edit_requests SET status = 'applied', applied_version = %s, "
                "apply_idempotency_key = %s, apply_payload_digest = %s, "
                "updated_at = CURRENT_TIMESTAMP WHERE request_id = %s",
                (snapshot["version"], idempotency_key, apply_payload_digest, request_id),
            )
            # The transaction sees its own writes, so the applied request can be
            # read back here instead of needing a second pass to store the
            # snapshot that embeds it.
            result = {
                "knowledge": snapshot,
                "edit_request": get_edit_request(conn, request_id),
            }
            conn.execute(
                "UPDATE knowledge_edit_requests SET apply_result_snapshot = %s::jsonb "
                "WHERE request_id = %s",
                (json.dumps(result, ensure_ascii=False), request_id),
            )
            if on_applied is not None:
                on_applied(conn, result)
    except _EditRequestConflict:
        with conn.transaction():
            # The failed attempt has released its request lock. Preserve a
            # terminal decision made in the meantime; only the still-proposed
            # request discovered stale by this attempt may become conflict.
            conn.execute(
                "UPDATE knowledge_edit_requests SET status = 'conflict', "
                "updated_at = CURRENT_TIMESTAMP "
                "WHERE request_id = %s AND status = 'proposed'",
                (request_id,),
            )
        raise StaleKnowledgeWrite(
            "Knowledge changed after the intelligent edit was proposed"
        ) from None
    return result


def _schema() -> dict:
    value = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise KnowledgeError("vendored Document → Knowledge schema is invalid")
    return value


def build_document_knowledge_slice(conn: psycopg.Connection, knowledge_id: str) -> dict:
    item = _knowledge_row(conn, knowledge_id)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT d.document_id, d.parent_project_id, d.analysis_status,
                   v.source_ref, v.source_digest,
                   v.media_type, v.byte_size, d.created_at,
                   v.created_at AS version_created_at,
                   e.extraction_id, e.converter, e.converter_version, e.config_digest,
                   e.status AS converter_status,
                   e.quality_flags AS converter_quality_flags, e.error,
                   e.created_at AS extraction_created_at, o.observation_kind,
                   sc.status AS compilation_status,
                   sc.quality_flags AS compilation_quality_flags
              FROM source_documents d
              JOIN document_versions v ON v.document_id = d.document_id AND v.version = %s
              JOIN extraction_runs e ON e.extraction_id = %s AND e.document_id = d.document_id
              LEFT JOIN extraction_observations o ON o.extraction_id = e.extraction_id
              LEFT JOIN document_compilation_bindings cb ON cb.document_id = d.document_id
              LEFT JOIN structured_compilations sc
                ON sc.compilation_id = cb.compilation_id
               AND sc.extraction_id = e.extraction_id
             WHERE d.document_id = %s AND v.source_digest = %s
            """,
            (
                item["source_version"], item["extraction_id"],
                item["document_id"], item["source_digest"],
            ),
        )
        row = cur.fetchone()
    if row is None:
        raise KnowledgeError("Knowledge source snapshot is no longer internally consistent")
    document = dict(row)
    document["source_version"] = item["source_version"]
    document["extraction_status"] = document["analysis_status"]
    document["quality_flags"] = list(
        dict.fromkeys(
            [
                *(document.get("converter_quality_flags") or []),
                *(document.get("compilation_quality_flags") or []),
            ]
        )
    )
    if not document["observation_kind"]:
        raise KnowledgeError("source document lacks a complete extraction observation or version")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM knowledge_source_chunks WHERE knowledge_id = %s ORDER BY ordinal",
            (knowledge_id,),
        )
        all_chunk_rows = [dict(row) for row in cur.fetchall()]
        # The transport-neutral Document -> Knowledge slice remains a
        # single-primary-document compatibility view.  Cross-source dependencies
        # are persisted and exposed by get_knowledge_source_state(); they are not
        # misrepresented as fragments of the primary document structure.
        chunk_rows = [
            row for row in all_chunk_rows
            if row["document_id"] == document["document_id"]
        ]
        if not chunk_rows:
            raise KnowledgeError(
                "Knowledge primary source anchor has no persisted source chunks"
            )
        cur.execute(
            "SELECT * FROM knowledge_events WHERE aggregate_ref = %s ORDER BY occurred_at, event_id",
            (knowledge_id,),
        )
        event_rows = [dict(row) for row in cur.fetchall()]
    card = _card_from_row(conn, item)

    # The contract requires the document's structure and binds every chunk to a
    # fragment of it. Both are computed already — `document_structure_read` has
    # served them to its own API since Pantheon-Next#229 — but the slice never carried them, so
    # conformance was asserted rather than shown. Only the declared fields are
    # projected: the read API also returns `chunk_anchors` and an `authority`
    # block, and the contract closes `additionalProperties`.
    try:
        structure = document_structure_read.get_document_structure(
            conn, document["document_id"]
        )
    except KeyError as exc:
        # The contract makes the structure required, so a document that was never
        # compiled cannot produce a conforming slice. Saying that plainly beats
        # letting a bare KeyError surface from three layers down, and it names the
        # missing step rather than the missing key.
        raise KnowledgeError(
            "Document → Knowledge contract requires a compiled document structure; "
            f"{document['document_id']} has none"
        ) from exc
    fragment_by_chunk = {
        anchor["chunk_ref"]: anchor["fragment_ref"]
        for anchor in structure.get("chunk_anchors") or []
    }

    def _declared(value: dict, keys: tuple[str, ...]) -> dict:
        """Keep only what the contract declares.

        The read API is this repository's own richer shape — its fragments carry
        `page_start` and `page_end` beside the contract's fields. The contract
        closes `additionalProperties`, so projecting rather than passing through is
        what lets the two evolve separately instead of one silently constraining
        the other.
        """
        return {key: value[key] for key in keys if key in value}

    _UNIT_KEYS = ("unit_id", "unit_kind", "ordinal", "label")
    _FRAGMENT_KEYS = (
        "fragment_id", "parent_fragment_ref", "unit_ref", "fragment_kind",
        "label", "reading_order", "locator", "qualification",
    )
    return {
        "source_document": {
            "document_id": document["document_id"],
            "parent_project_id": document["parent_project_id"],
            "source_ref": document["source_ref"],
            "source_digest": document["source_digest"],
            "media_type": document["media_type"],
            "byte_size": document["byte_size"],
            "analysis_status": document["analysis_status"],
            "version": document["source_version"],
            "created_at": _iso(document["created_at"]),
            "updated_at": _iso(document["version_created_at"]),
        },
        "extraction": {
            "extraction_id": document["extraction_id"],
            "document_ref": document["document_id"],
            "source_digest": document["source_digest"],
            "converter": document["converter"],
            "converter_version": document["converter_version"],
            "config_digest": document["config_digest"],
            "observation_kind": document["observation_kind"],
            "status": document["extraction_status"],
            "quality_flags": document["quality_flags"] or [],
            "created_at": _iso(document["extraction_created_at"]),
            **({"error": document["error"]} if document["error"] else {}),
        },
        "document_structure": {
            **_declared(
                structure,
                ("structure_id", "document_ref", "extraction_ref", "status",
                 "quality_flags", "created_at"),
            ),
            "native_units": [
                _declared(unit, _UNIT_KEYS) for unit in structure["native_units"]
            ],
            "fragments": [
                {
                    **_declared(fragment, _FRAGMENT_KEYS),
                    # The locator needs projecting too: this repository records
                    # page_start/page_end there, while the contract carries the page
                    # through the native unit the fragment references. Nothing is
                    # lost — it is said once, in the place the contract says it.
                    "locator": _declared(
                        fragment["locator"], ("structural_locator", "region")
                    ),
                }
                for fragment in structure["fragments"]
            ],
        },
        "chunks": [
            {
                "chunk_id": chunk["chunk_ref"],
                "document_ref": chunk["document_id"],
                "extraction_ref": chunk["extraction_id"],
                "fragment_ref": fragment_by_chunk[chunk["chunk_ref"]],
                "ordinal": chunk["ordinal"],
                "text_digest": chunk["text_digest"],
                "provenance": {
                    "source_ref": chunk["source_ref"],
                    "source_digest": chunk["source_digest"],
                    "extraction_ref": chunk["extraction_id"],
                    "structural_locator": chunk["structural_locator"],
                },
            }
            for chunk in chunk_rows
        ],
        "document_card": {
            "card_id": f"card-{document['document_id']}",
            "document_ref": document["document_id"],
            "parent_project_id": document["parent_project_id"],
            "source_ref": document["source_ref"],
            "title": Path(document["source_ref"]).name,
            "analysis_status": document["analysis_status"],
            "source_version": document["source_version"],
            "authority": {"is_source": False, "is_evidence": False, "is_memory": False},
        },
        "knowledge_publications": [
            {
                "knowledge_id": card["knowledge_id"],
                "document_ref": card["document_ref"],
                "title": card["title"],
                "family": card["family"],
                "markdown_digest": card["markdown_digest"],
                "source_chunk_refs": card["source_chunk_refs"],
                "review_status": card["review_status"],
                "version": card["version"],
                "created_by": card["created_by"],
                "created_at": card["created_at"],
                "updated_at": card["updated_at"],
                "authority": card["authority"],
            }
        ],
        "events": [
            {
                "event_id": event["event_id"],
                "aggregate_kind": event["aggregate_kind"],
                "aggregate_ref": event["aggregate_ref"],
                "event_type": event["event_type"],
                "actor": event["actor"],
                "actor_kind": event["actor_kind"],
                "expected_version": event["expected_version"],
                "resulting_version": event["resulting_version"],
                "idempotency_key": event["idempotency_key"],
                "occurred_at": _iso(event["occurred_at"]),
            }
            for event in event_rows
        ],
        "governance_refs": [
            "docs/governance/DOCUMENT_KNOWLEDGE_SLICE_CONTRACT.md",
            "docs/domain-packs/architecture/DOCUMENT_AND_KNOWLEDGE_ORGANIZATION.md",
        ],
    }


def validate_document_knowledge_slice(conn: psycopg.Connection, knowledge_id: str) -> dict:
    snapshot = build_document_knowledge_slice(conn, knowledge_id)
    try:
        jsonschema.Draft202012Validator(
            _schema(), format_checker=jsonschema.FormatChecker()
        ).validate(snapshot)
    except jsonschema.ValidationError as exc:
        raise KnowledgeError(f"Document → Knowledge contract refusal: {exc.message}") from exc
    return snapshot
