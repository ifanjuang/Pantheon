"""Immutable launch reservation and bootstrap snapshot for one admitted Hermes run.

A launch reservation is not a dispatcher or queue item. It atomically consumes the
revocable pre-launch window for one already-admitted execution opportunity and
freezes the bounded bootstrap context that an external Hermes Run Binding may send
to Hermes. The external binding performs the actual ``POST /v1/runs``.

The reservation has a short lazy-expiry window. There is no scheduler and no retry
worker. If the external submission outcome becomes uncertain, the reservation is
left for explicit operator reconciliation rather than silently reused.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Any

import psycopg
from psycopg.rows import dict_row

from . import hermes_ephemeral_context, hermes_execution, hermes_scoped_context
from .hermes_execution_basis import HermesExecutionBasis, HermesExecutionBasisError

MAX_LAUNCH_SNAPSHOT_CHARS = 120_000
LAUNCH_RESERVATION_TTL_SECONDS = 120


class HermesLaunchContextError(ValueError):
    pass


class LaunchReservationNotFound(HermesLaunchContextError):
    pass


class LaunchReservationConflict(HermesLaunchContextError):
    pass


class LaunchContextTooLarge(HermesLaunchContextError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _one(conn: psycopg.Connection, sql: str, params: tuple[Any, ...]) -> dict[str, Any] | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
    return dict(row) if row else None


def _reservation_projection(row: dict[str, Any], *, replayed: bool) -> dict[str, Any]:
    snapshot = dict(row["snapshot_payload"] or {})
    return {
        "kind": "hermes_run_launch_reservation",
        "launch_reservation_id": row["launch_reservation_id"],
        "admission_id": row["admission_id"],
        "snapshot_id": row["snapshot_id"],
        "snapshot_digest": row["snapshot_digest"],
        "field_projection_version": row["field_projection_version"],
        "work_issue_version": row["work_issue_version"],
        "launch_expires_at": _iso(row["launch_expires_at"]),
        "reserved_by": row["reserved_by"],
        "reserved_at": _iso(row["reserved_at"]),
        "snapshot": snapshot,
        "replayed": replayed,
        "runtime_submission_performed": False,
        "dispatch_performed": False,
        "write_effect": False,
        "authority_effect": "consume_admitted_launch_window",
        "non_equivalences": [
            "launch reservation != runtime dispatch",
            "launch snapshot != Evidence",
            "launch snapshot != current owner read after launch",
            "reservation consumed != Hermes run started",
            "technical launch receipt != Evidence",
        ],
    }


def _materialize_snapshot_entities(
    conn: psycopg.Connection,
    context_pack: dict[str, Any],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for ref in hermes_scoped_context.admitted_entity_refs(context_pack):
        entity_ref = ref.as_dict()
        if ref.entity_type not in hermes_scoped_context.MATERIALIZABLE_TYPES:
            output.append({
                "entity_ref": entity_ref,
                "materializable": False,
                "record": None,
                "representation": None,
                "record_owner_system": None,
                "current_revision": None,
            })
            continue
        try:
            materialized = hermes_scoped_context.materialize_context_entity(
                conn,
                entity_type=ref.entity_type,
                entity_id=ref.entity_id,
            )
        except Exception as exc:
            raise LaunchReservationConflict(
                f"admitted launch entity could not be materialized: {ref.entity_type}:{ref.entity_id}"
            ) from exc
        record = materialized["record"]
        revision = record.get("revision", record.get("version")) if isinstance(record, dict) else None
        output.append({
            "entity_ref": entity_ref,
            "materializable": True,
            "record_owner_system": materialized["record_owner_system"],
            "current_revision": revision,
            "record": record,
            "representation": materialized["representation"],
        })
    return output


def get_launch_reservation(conn: psycopg.Connection, *, admission_id: str) -> dict[str, Any]:
    row = _one(
        conn,
        "SELECT * FROM hermes_run_launch_reservations WHERE admission_id=%s",
        (admission_id,),
    )
    if row is None:
        raise LaunchReservationNotFound(f"no launch reservation for admission: {admission_id}")
    return _reservation_projection(row, replayed=False)


def reserve_launch(
    conn: psycopg.Connection,
    *,
    admission_id: str,
    actor: str,
    idempotency_key: str,
) -> dict[str, Any]:
    """Reserve exactly one admitted launch and freeze its bootstrap context.

    Reservation is intentionally irreversible in the first slice. A replay of the
    exact idempotency key returns the same immutable reservation, but an external
    Run Binding must not interpret that replay as permission to submit Hermes again.
    """
    actor = actor.strip()
    idempotency_key = idempotency_key.strip()
    if not actor:
        raise HermesLaunchContextError("Hermes launch binding actor is required")
    if len(idempotency_key) < 8:
        raise HermesLaunchContextError("idempotency_key must contain at least 8 characters")

    with conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")

        replay = _one(
            conn,
            "SELECT * FROM hermes_run_launch_reservations WHERE idempotency_key=%s",
            (idempotency_key,),
        )
        if replay is not None:
            if replay["admission_id"] != admission_id or replay["reserved_by"] != actor:
                raise LaunchReservationConflict(
                    "idempotency key already belongs to another launch reservation"
                )
            return _reservation_projection(replay, replayed=True)

        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM hermes_execution_admissions WHERE admission_id=%s FOR UPDATE",
                (admission_id,),
            )
            admission = cur.fetchone()
        if admission is None:
            raise LaunchReservationNotFound(f"unknown execution admission: {admission_id}")
        admission = dict(admission)

        existing = _one(
            conn,
            "SELECT * FROM hermes_run_launch_reservations WHERE admission_id=%s",
            (admission_id,),
        )
        if existing is not None:
            raise LaunchReservationConflict(
                "execution admission already has a launch reservation; automatic retry is forbidden"
            )

        current = hermes_execution.get_admission(conn, admission_id)
        if current["admission_state"] != "admitted":
            raise LaunchReservationConflict(
                f"launch reservation requires admitted state; current state is {current['admission_state']}"
            )

        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM cockpit_hermes_handoffs WHERE handoff_id=%s",
                (admission["handoff_id"],),
            )
            handoff = cur.fetchone()
        if handoff is None:
            raise LaunchReservationConflict("immutable Hermes handoff is missing")
        handoff = dict(handoff)

        try:
            admission_basis = HermesExecutionBasis.from_values(
                requested_effect=admission["requested_effect"],
                task_contract_ref=admission["task_contract_ref"],
                context_pack_ref=admission["context_pack_ref"],
                preview_digest=admission["preview_digest"],
                label="execution admission basis",
            )
            handoff_basis = HermesExecutionBasis.from_values(
                requested_effect=handoff["requested_effect"],
                task_contract_ref=handoff["task_contract_ref"],
                context_pack_ref=handoff["context_pack_ref"],
                preview_digest=handoff["preview_digest"],
                label="immutable handoff basis",
            )
        except HermesExecutionBasisError as exc:
            raise LaunchReservationConflict(
                "execution admission no longer matches the immutable handoff"
            ) from exc
        if not admission_basis.is_read_only or not handoff_basis.is_read_only:
            raise LaunchReservationConflict("first launch reservation slice is read_only only")
        if admission_basis != handoff_basis:
            raise LaunchReservationConflict(
                "execution admission no longer matches the immutable handoff"
            )

        context_pack = dict(handoff["context_pack"] or {})
        task_contract = dict(handoff["task_contract"] or {})
        try:
            ephemeral_context_leases = (
                hermes_ephemeral_context.validate_context_pack_leases(context_pack)
            )
        except hermes_ephemeral_context.EphemeralContextError as exc:
            raise LaunchReservationConflict(
                "ephemeral context lease is unavailable or changed; reprepare the handoff"
            ) from exc
        reserved_at = conn.execute("SELECT CURRENT_TIMESTAMP").fetchone()[0]
        launch_expires_at = min(
            admission["expires_at"],
            reserved_at + timedelta(seconds=LAUNCH_RESERVATION_TTL_SECONDS),
        )
        if launch_expires_at <= reserved_at:
            raise LaunchReservationConflict("execution admission expired before launch reservation")

        snapshot_id = f"launch-snapshot-{uuid.uuid4().hex}"
        snapshot = {
            "kind": "hermes_launch_context_snapshot",
            "snapshot_id": snapshot_id,
            "admission_id": admission_id,
            "work_issue_id": admission["work_issue_id"],
            "work_issue_version": admission["work_issue_version"],
            "task_contract_ref": admission["task_contract_ref"],
            "context_pack_ref": admission["context_pack_ref"],
            "requested_effect": "read_only",
            "field_projection_version": hermes_scoped_context.FIELD_PROJECTION_VERSION,
            "snapshot_semantics": "immutable_owner_read_at_launch_reservation",
            "question": handoff["question"],
            "task_contract": task_contract,
            "context_manifest": {
                "root_entity": context_pack.get("root_entity"),
                "included_entities": list(context_pack.get("included_entities") or []),
                "excluded_entities": list(context_pack.get("excluded_entities") or []),
                "source_refs": list(context_pack.get("source_refs") or []),
                "ephemeral_context_leases": ephemeral_context_leases,
            },
            "entities": _materialize_snapshot_entities(conn, context_pack),
            "source_binary_included": False,
            "ephemeral_payload_included": False,
            "global_search_available": False,
            "global_listing_available": False,
            "write_effect": False,
            "snapshot_observed_at": reserved_at.isoformat(),
            "non_equivalences": [
                "launch snapshot != Evidence",
                "launch snapshot != global Agency Data",
                "launch snapshot != source binary",
                "launch snapshot != ephemeral context payload",
                "ephemeral context lease != Source admission",
                "snapshot revision != future current owner revision",
                "read_only run admission != consequential effect authorization",
            ],
        }
        canonical = _canonical(snapshot)
        if len(canonical) > MAX_LAUNCH_SNAPSHOT_CHARS:
            raise LaunchContextTooLarge(
                f"launch context snapshot exceeds {MAX_LAUNCH_SNAPSHOT_CHARS} characters; narrow the admitted context"
            )
        snapshot_digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        reservation_id = f"launch-reservation-{uuid.uuid4().hex}"

        conn.execute(
            """
            INSERT INTO hermes_run_launch_reservations (
                launch_reservation_id, admission_id, snapshot_id, snapshot_digest,
                snapshot_payload, field_projection_version, work_issue_version,
                launch_expires_at, idempotency_key, reserved_by, reserved_at
            ) VALUES (%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s)
            """,
            (
                reservation_id,
                admission_id,
                snapshot_id,
                snapshot_digest,
                canonical,
                hermes_scoped_context.FIELD_PROJECTION_VERSION,
                admission["work_issue_version"],
                launch_expires_at,
                idempotency_key,
                actor,
                reserved_at,
            ),
        )
        row = _one(
            conn,
            "SELECT * FROM hermes_run_launch_reservations WHERE launch_reservation_id=%s",
            (reservation_id,),
        )
        assert row is not None
        return _reservation_projection(row, replayed=False)


def materialize_ephemeral_context(
    conn: psycopg.Connection,
    *,
    admission_id: str,
    launch_reservation_id: str,
) -> dict[str, Any]:
    """Resolve exact transient bytes only for the currently reserved launch.

    This is a read/materialization seam for the external binding. It does not
    dispatch Hermes, start a run, write AFFAIRES/Hindsight or admit Source/Evidence.
    """
    admission_id = str(admission_id or "").strip()
    launch_reservation_id = str(launch_reservation_id or "").strip()
    if not admission_id or not launch_reservation_id:
        raise HermesLaunchContextError(
            "admission_id and launch_reservation_id are required"
        )

    current = hermes_execution.get_admission(conn, admission_id)
    if current["admission_state"] != "launch_reserved":
        raise LaunchReservationConflict(
            "ephemeral context materialization requires a live launch reservation"
        )
    if current.get("launch_reservation_id") != launch_reservation_id:
        raise LaunchReservationConflict(
            "ephemeral context materialization requires the exact launch reservation"
        )

    reservation = _one(
        conn,
        """
        SELECT * FROM hermes_run_launch_reservations
         WHERE launch_reservation_id=%s AND admission_id=%s
        """,
        (launch_reservation_id, admission_id),
    )
    if reservation is None:
        raise LaunchReservationNotFound(
            f"unknown launch reservation: {launch_reservation_id}"
        )
    if reservation["launch_expires_at"] <= datetime.now(reservation["launch_expires_at"].tzinfo):
        raise LaunchReservationConflict("launch reservation expired before context materialization")

    admission = _one(
        conn,
        "SELECT * FROM hermes_execution_admissions WHERE admission_id=%s",
        (admission_id,),
    )
    if admission is None:
        raise LaunchReservationNotFound(f"unknown execution admission: {admission_id}")
    handoff = _one(
        conn,
        "SELECT * FROM cockpit_hermes_handoffs WHERE handoff_id=%s",
        (admission["handoff_id"],),
    )
    if handoff is None:
        raise LaunchReservationConflict("immutable Hermes handoff is missing")

    context_pack = dict(handoff["context_pack"] or {})
    try:
        leases = hermes_ephemeral_context.materialize_context_pack_leases(context_pack)
    except hermes_ephemeral_context.EphemeralContextError as exc:
        raise LaunchReservationConflict(
            "ephemeral context lease is unavailable or changed; reprepare the handoff"
        ) from exc

    return {
        "kind": "hermes_ephemeral_context_materialization",
        "admission_id": admission_id,
        "launch_reservation_id": launch_reservation_id,
        "leases": leases,
        "materialized": bool(leases),
        "dispatch_performed": False,
        "runtime_start_recorded": False,
        "affaires_write_performed": False,
        "hindsight_write_performed": False,
        "source_admitted": False,
        "evidence_admitted": False,
        "non_equivalences": [
            "ephemeral context materialized != Source admission",
            "ephemeral context materialized != Hermes run started",
            "ephemeral context materialized != Evidence",
        ],
    }
