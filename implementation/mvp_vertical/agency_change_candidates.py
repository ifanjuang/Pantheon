"""Governed Project attribute ChangeCandidates.

A candidate is a proposal envelope, not a Project status and not an authorization.
It never mutates Agency Data until a human explicitly applies it against the exact
base revision. If that revision moved, the candidate becomes stale and no Project
write occurs.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Literal

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from . import agency_data, agency_schema


class ChangeCandidateError(ValueError):
    pass


class ChangeCandidateNotFound(ChangeCandidateError):
    pass


class ChangeCandidateConflict(ChangeCandidateError):
    pass


class ChangeCandidateIdempotencyConflict(ChangeCandidateError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _candidate_row(
    conn: psycopg.Connection,
    candidate_id: str,
    *,
    lock: bool = False,
) -> dict:
    suffix = " FOR UPDATE" if lock else ""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"SELECT * FROM agency_change_candidates WHERE candidate_id = %s{suffix}",
            (candidate_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise ChangeCandidateNotFound(f"unknown Agency ChangeCandidate: {candidate_id}")
    result = dict(row)
    for key in ("created_at", "decided_at"):
        if result.get(key) is not None:
            result[key] = result[key].isoformat()
    return result


def _event_by_idempotency(conn: psycopg.Connection, idempotency_key: str) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM agency_change_candidate_events WHERE idempotency_key = %s",
            (idempotency_key,),
        )
        row = cur.fetchone()
    return dict(row) if row else None


def _insert_event(
    conn: psycopg.Connection,
    *,
    candidate_id: str,
    event_type: Literal["proposed", "applied", "rejected", "stale"],
    actor: str,
    actor_kind: Literal["human", "hermes", "system"],
    idempotency_key: str,
    payload: dict[str, Any] | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO agency_change_candidate_events (
            event_id, candidate_id, event_type, actor, actor_kind, idempotency_key, payload
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            f"change-event-{uuid.uuid4().hex}",
            candidate_id,
            event_type,
            actor,
            actor_kind,
            idempotency_key,
            Jsonb(payload or {}),
        ),
    )


def _source_refs(values: list[str] | None) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for raw in values or []:
        value = str(raw or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        output.append(value)
    if len(output) > 500:
        raise ChangeCandidateError("source_refs cannot contain more than 500 entries")
    return output


def _variant_provenance(value: dict[str, Any] | None) -> dict[str, str] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ChangeCandidateError("variant_provenance must be an object")
    expected = {
        "source_execution_result_id",
        "source_result_id",
        "source_review_disposition_id",
        "variant_request_ref",
        "variant_scope_digest",
        "variant_label",
        "variant_title",
    }
    unknown = set(value) - expected
    missing = expected - set(value)
    if unknown or missing:
        details = []
        if missing:
            details.append("missing " + ", ".join(sorted(missing)))
        if unknown:
            details.append("unsupported " + ", ".join(sorted(unknown)))
        raise ChangeCandidateError("invalid variant_provenance: " + "; ".join(details))
    normalized = {key: str(value[key] or "").strip() for key in expected}
    empty = sorted(key for key, item in normalized.items() if not item)
    if empty:
        raise ChangeCandidateError(
            "variant_provenance fields must be non-empty: " + ", ".join(empty)
        )
    digest = normalized["variant_scope_digest"]
    if len(digest) != 71 or not digest.startswith("sha256:"):
        raise ChangeCandidateError("variant_scope_digest must be a sha256 digest")
    return normalized


def _proposal_changes(current: dict, proposed_attributes: dict[str, Any]) -> tuple[list[dict], dict]:
    try:
        normalized = agency_schema.normalize_project_attributes(proposed_attributes)
    except agency_schema.AgencySchemaError as exc:
        raise ChangeCandidateError(str(exc)) from exc
    if not normalized:
        raise ChangeCandidateError("at least one Project attribute must be proposed")

    current_attributes = dict(current.get("attributes") or {})
    changes: list[dict] = []
    for key, proposed in normalized.items():
        before = current_attributes.get(key)
        if before == proposed:
            continue
        changes.append({"field": key, "before": before, "proposed": proposed})
    if not changes:
        raise ChangeCandidateError("proposed Project attributes do not change the current record")
    return changes, normalized


def list_project_candidates(
    conn: psycopg.Connection,
    project_id: str,
    *,
    status: str | None = None,
    limit: int = 100,
) -> list[dict]:
    if limit < 1 or limit > 500:
        raise ChangeCandidateError("candidate list limit must be between 1 and 500")
    agency_data.get_project(conn, project_id)
    params: list[Any] = [project_id]
    where = "entity_id = %s"
    if status:
        if status not in {"pending_review", "applied", "rejected", "stale"}:
            raise ChangeCandidateError("unsupported ChangeCandidate status")
        where += " AND status = %s"
        params.append(status)
    params.append(limit)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"""
            SELECT * FROM agency_change_candidates
             WHERE {where}
             ORDER BY created_at DESC, candidate_id
             LIMIT %s
            """,
            params,
        )
        rows = [dict(row) for row in cur.fetchall()]
    for row in rows:
        for key in ("created_at", "decided_at"):
            if row.get(key) is not None:
                row[key] = row[key].isoformat()
    return rows


def create_project_candidate(
    conn: psycopg.Connection,
    *,
    project_id: str,
    base_revision: int,
    proposed_attributes: dict[str, Any],
    proposer: str,
    proposer_kind: Literal["human", "hermes", "system"],
    idempotency_key: str,
    reason: str | None = None,
    source_refs: list[str] | None = None,
    variant_provenance: dict[str, Any] | None = None,
) -> dict:
    if not proposer.strip():
        raise ChangeCandidateError("proposer is required")
    if proposer_kind not in {"human", "hermes", "system"}:
        raise ChangeCandidateError("unsupported proposer_kind")
    if base_revision < 1:
        raise ChangeCandidateError("base_revision must be at least 1")
    if len(idempotency_key.strip()) < 8:
        raise ChangeCandidateError("idempotency_key must contain at least 8 characters")

    current = agency_data.get_project(conn, project_id)
    if current["revision"] != base_revision:
        raise ChangeCandidateConflict(
            f"stale Project revision for candidate: expected {base_revision}, current {current['revision']}"
        )
    changes, normalized = _proposal_changes(current, proposed_attributes)
    sources = _source_refs(source_refs)
    provenance = _variant_provenance(variant_provenance)
    request = {
        "entity_type": "project",
        "entity_id": project_id,
        "base_revision": base_revision,
        "changes": changes,
        "reason": (reason or "").strip() or None,
        "source_refs": sources,
        "proposer": proposer.strip(),
        "proposer_kind": proposer_kind,
        "variant_provenance": provenance,
    }
    proposal_digest = _digest(request)

    with conn.transaction():
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM agency_change_candidates WHERE idempotency_key = %s",
                (idempotency_key,),
            )
            existing = cur.fetchone()
        if existing is not None:
            if existing["proposal_digest"] != proposal_digest:
                raise ChangeCandidateIdempotencyConflict(
                    "idempotency key already belongs to another ChangeCandidate proposal"
                )
            return _candidate_row(conn, existing["candidate_id"])

        candidate_id = f"change-{uuid.uuid4().hex}"
        conn.execute(
            """
            INSERT INTO agency_change_candidates (
                candidate_id, entity_type, entity_id, base_revision,
                proposer, proposer_kind, changes, reason, source_refs,
                proposal_digest, idempotency_key, status,
                source_execution_result_id, source_result_id,
                source_review_disposition_id, variant_request_ref,
                variant_scope_digest, variant_label, variant_title
            ) VALUES (
                %s, 'project', %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending_review',
                %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                candidate_id,
                project_id,
                base_revision,
                proposer.strip(),
                proposer_kind,
                Jsonb(changes),
                request["reason"],
                Jsonb(sources),
                proposal_digest,
                idempotency_key,
                provenance["source_execution_result_id"] if provenance else None,
                provenance["source_result_id"] if provenance else None,
                provenance["source_review_disposition_id"] if provenance else None,
                provenance["variant_request_ref"] if provenance else None,
                provenance["variant_scope_digest"] if provenance else None,
                provenance["variant_label"] if provenance else None,
                provenance["variant_title"] if provenance else None,
            ),
        )
        _insert_event(
            conn,
            candidate_id=candidate_id,
            event_type="proposed",
            actor=proposer.strip(),
            actor_kind=proposer_kind,
            idempotency_key=f"{idempotency_key}:proposed",
            payload={
                "base_revision": base_revision,
                "changes": changes,
                "normalized": normalized,
                "variant_provenance": provenance,
            },
        )
        return _candidate_row(conn, candidate_id)


def _replayed_decision(
    conn: psycopg.Connection,
    *,
    candidate_id: str,
    idempotency_key: str,
    expected_event_type: str,
) -> dict | None:
    event = _event_by_idempotency(conn, idempotency_key)
    if event is None:
        return None
    if event["candidate_id"] != candidate_id or event["event_type"] != expected_event_type:
        raise ChangeCandidateIdempotencyConflict(
            "idempotency key already belongs to another ChangeCandidate decision"
        )
    return _candidate_row(conn, candidate_id)


def apply_project_candidate(
    conn: psycopg.Connection,
    *,
    candidate_id: str,
    actor: str,
    idempotency_key: str,
) -> dict:
    if not actor.strip():
        raise ChangeCandidateError("human actor is required")
    replayed = _replayed_decision(
        conn,
        candidate_id=candidate_id,
        idempotency_key=idempotency_key,
        expected_event_type="applied",
    )
    if replayed is not None:
        return replayed

    with conn.transaction():
        candidate = _candidate_row(conn, candidate_id, lock=True)
        if candidate["status"] != "pending_review":
            raise ChangeCandidateConflict(
                f"ChangeCandidate cannot be applied from status {candidate['status']}"
            )

        current = agency_data.get_project(conn, candidate["entity_id"])
        if current["revision"] != candidate["base_revision"]:
            conn.execute(
                """
                UPDATE agency_change_candidates
                   SET status='stale', decided_at=CURRENT_TIMESTAMP, decided_by=%s
                 WHERE candidate_id=%s
                """,
                (actor.strip(), candidate_id),
            )
            _insert_event(
                conn,
                candidate_id=candidate_id,
                event_type="stale",
                actor=actor.strip(),
                actor_kind="human",
                idempotency_key=idempotency_key,
                payload={
                    "base_revision": candidate["base_revision"],
                    "current_revision": current["revision"],
                },
            )
            return _candidate_row(conn, candidate_id)

        merged = dict(current.get("attributes") or {})
        for change in candidate["changes"]:
            merged[change["field"]] = change["proposed"]

        try:
            updated = agency_data.update_project(
                conn,
                project_id=candidate["entity_id"],
                changes={"attributes": merged},
                actor=actor.strip(),
                actor_kind="human",
                expected_revision=candidate["base_revision"],
                idempotency_key=f"{idempotency_key}:project-apply",
            )
        except agency_data.StaleProjectWrite:
            latest = agency_data.get_project(conn, candidate["entity_id"])
            conn.execute(
                """
                UPDATE agency_change_candidates
                   SET status='stale', decided_at=CURRENT_TIMESTAMP, decided_by=%s
                 WHERE candidate_id=%s
                """,
                (actor.strip(), candidate_id),
            )
            _insert_event(
                conn,
                candidate_id=candidate_id,
                event_type="stale",
                actor=actor.strip(),
                actor_kind="human",
                idempotency_key=idempotency_key,
                payload={
                    "base_revision": candidate["base_revision"],
                    "current_revision": latest["revision"],
                },
            )
            return _candidate_row(conn, candidate_id)

        conn.execute(
            """
            UPDATE agency_change_candidates
               SET status='applied', decided_at=CURRENT_TIMESTAMP, decided_by=%s,
                   applied_revision=%s
             WHERE candidate_id=%s
            """,
            (actor.strip(), updated["revision"], candidate_id),
        )
        _insert_event(
            conn,
            candidate_id=candidate_id,
            event_type="applied",
            actor=actor.strip(),
            actor_kind="human",
            idempotency_key=idempotency_key,
            payload={"applied_revision": updated["revision"]},
        )
        return _candidate_row(conn, candidate_id)


def reject_project_candidate(
    conn: psycopg.Connection,
    *,
    candidate_id: str,
    actor: str,
    reason: str,
    idempotency_key: str,
) -> dict:
    if not actor.strip():
        raise ChangeCandidateError("human actor is required")
    if not reason.strip():
        raise ChangeCandidateError("rejection reason is required")
    replayed = _replayed_decision(
        conn,
        candidate_id=candidate_id,
        idempotency_key=idempotency_key,
        expected_event_type="rejected",
    )
    if replayed is not None:
        return replayed

    with conn.transaction():
        candidate = _candidate_row(conn, candidate_id, lock=True)
        if candidate["status"] != "pending_review":
            raise ChangeCandidateConflict(
                f"ChangeCandidate cannot be rejected from status {candidate['status']}"
            )
        conn.execute(
            """
            UPDATE agency_change_candidates
               SET status='rejected', decided_at=CURRENT_TIMESTAMP, decided_by=%s
             WHERE candidate_id=%s
            """,
            (actor.strip(), candidate_id),
        )
        _insert_event(
            conn,
            candidate_id=candidate_id,
            event_type="rejected",
            actor=actor.strip(),
            actor_kind="human",
            idempotency_key=idempotency_key,
            payload={"reason": reason.strip()},
        )
        return _candidate_row(conn, candidate_id)
