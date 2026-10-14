"""Governed admission boundary for an external Hermes runtime.

Pantheon records admissibility and runtime observations. It never dispatches,
queues, schedules, retries or routes Hermes execution.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from psycopg.rows import dict_row

from . import work_issues
from .hermes_execution_basis import HermesExecutionBasis, HermesExecutionBasisError

BASE_MIGRATION = Path(__file__).resolve().parent / "sql" / "hermes" / "004_execution_admissions.sql"
LIFECYCLE_MIGRATION = Path(__file__).resolve().parent / "sql" / "hermes" / "005_admission_lifecycle.sql"
LAUNCH_MIGRATION = Path(__file__).resolve().parent / "sql" / "hermes" / "007_run_launch_reservations.sql"
MIGRATIONS = (BASE_MIGRATION, LIFECYCLE_MIGRATION, LAUNCH_MIGRATION)
MIGRATION = BASE_MIGRATION
MIN_TTL_SECONDS = 60
MAX_TTL_SECONDS = 86_400


class HermesExecutionError(ValueError): pass
class AdmissionNotFound(HermesExecutionError): pass
class AdmissionConflict(HermesExecutionError): pass
class RuntimeStartConflict(HermesExecutionError): pass


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def _one(conn, sql: str, params: tuple, *, required: str | None = None) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
    if row is None and required:
        raise AdmissionNotFound(required)
    return dict(row) if row else None


def _work_issue_record(conn, issue_id: str) -> dict:
    """Return only the Work Issue record from the governed projection."""
    projection = work_issues.get_issue(conn, issue_id)
    issue = projection.get("work_issue")
    if not isinstance(issue, dict):
        raise HermesExecutionError("Work Issue projection is missing its work_issue record")
    return issue


def _handoff(conn, handoff_id: str, lock: bool = False) -> dict:
    return _one(
        conn,
        "SELECT * FROM cockpit_hermes_handoffs WHERE handoff_id=%s" + (" FOR UPDATE" if lock else ""),
        (handoff_id,),
        required=f"unknown Cockpit Hermes handoff: {handoff_id}",
    )


def _admission(conn, admission_id: str, lock: bool = False) -> dict:
    return _one(
        conn,
        "SELECT * FROM hermes_execution_admissions WHERE admission_id=%s" + (" FOR UPDATE" if lock else ""),
        (admission_id,),
        required=f"unknown Hermes execution admission: {admission_id}",
    )


def _run(conn, admission_id: str) -> dict | None:
    return _one(conn, "SELECT * FROM hermes_runs WHERE admission_ref=%s", (admission_id,))


def _launch_reservation(conn, admission_id: str) -> dict | None:
    return _one(
        conn,
        "SELECT * FROM hermes_run_launch_reservations WHERE admission_id=%s",
        (admission_id,),
    )


def _revocation(conn, admission_id: str) -> dict | None:
    return _one(
        conn,
        "SELECT * FROM hermes_execution_admission_events WHERE admission_id=%s AND event_type='revoked' LIMIT 1",
        (admission_id,),
    )


def _state(
    conn,
    admission: dict,
    issue: dict,
    run: dict | None,
    launch_reservation: dict | None,
) -> tuple[str, dict | None]:
    if run:
        return "consumed", None
    revoked = _revocation(conn, admission["admission_id"])
    if revoked:
        return "revoked", revoked
    if launch_reservation:
        if launch_reservation["launch_expires_at"] <= datetime.now(timezone.utc):
            return "launch_expired", None
        return "launch_reserved", None
    if not admission.get("expires_at") or not admission.get("work_issue_version") or not admission.get("ttl_seconds"):
        return "stale", None
    if admission["expires_at"] <= datetime.now(timezone.utc):
        return "expired", None
    if issue["version"] != admission["work_issue_version"]:
        return "stale", None
    if issue["status"] != "open" or issue["assigned_to"] != "hermes":
        return "stale", None
    if issue["task_contract_ref"] != admission["task_contract_ref"]:
        return "stale", None
    if issue["context_pack_ref"] != admission["context_pack_ref"]:
        return "stale", None
    return "admitted", None


def _projection(conn, admission: dict) -> dict:
    issue = _work_issue_record(conn, admission["work_issue_id"])
    run = _run(conn, admission["admission_id"])
    launch_reservation = _launch_reservation(conn, admission["admission_id"])
    state, revoked = _state(conn, admission, issue, run, launch_reservation)
    return {
        "admission_id": admission["admission_id"],
        "handoff_id": admission["handoff_id"],
        "work_issue_id": admission["work_issue_id"],
        "decision": admission["decision"],
        "requested_effect": admission["requested_effect"],
        "task_contract_ref": admission["task_contract_ref"],
        "context_pack_ref": admission["context_pack_ref"],
        "preview_digest": admission["preview_digest"],
        "admission_digest": admission["admission_digest"],
        "work_issue_version": admission.get("work_issue_version"),
        "ttl_seconds": admission.get("ttl_seconds"),
        "expires_at": admission["expires_at"].isoformat() if admission.get("expires_at") else None,
        "admitted_by": admission["admitted_by"],
        "admitted_at": admission["admitted_at"].isoformat(),
        "admission_state": state,
        "ready_for_external_runtime": state == "admitted",
        "launch_reservation_id": launch_reservation["launch_reservation_id"] if launch_reservation else None,
        "launch_reserved_at": launch_reservation["reserved_at"].isoformat() if launch_reservation else None,
        "launch_expires_at": launch_reservation["launch_expires_at"].isoformat() if launch_reservation else None,
        "consumed_by_run_id": run["run_id"] if run else None,
        "runtime_started": bool(run),
        "revoked_at": revoked["occurred_at"].isoformat() if revoked else None,
        "revocation_reason": revoked["reason"] if revoked else None,
        "work_issue": issue,
        "non_equivalences": [
            "admission != dispatch",
            "launch reservation != dispatch",
            "launch reservation != Hermes run",
            "admission != Hermes run",
            "runtime success != Evidence",
        ],
    }


def admit_handoff(conn, *, handoff_id: str, actor: str, idempotency_key: str, ttl_seconds: int) -> dict:
    if not actor.strip(): raise HermesExecutionError("human actor is required for execution admission")
    if len(idempotency_key.strip()) < 8: raise HermesExecutionError("idempotency_key must contain at least 8 characters")
    if not MIN_TTL_SECONDS <= ttl_seconds <= MAX_TTL_SECONDS:
        raise HermesExecutionError(f"ttl_seconds must be between {MIN_TTL_SECONDS} and {MAX_TTL_SECONDS}")

    with conn.transaction():
        existing = _one(conn, "SELECT * FROM hermes_execution_admissions WHERE idempotency_key=%s", (idempotency_key,))
        if existing:
            if existing["handoff_id"] != handoff_id or existing["admitted_by"] != actor.strip() or existing.get("ttl_seconds") != ttl_seconds:
                raise AdmissionConflict("idempotency key already belongs to another execution admission")
            return _projection(conn, existing)

        handoff = _handoff(conn, handoff_id, True)
        conn.execute("SELECT issue_id FROM work_issues WHERE issue_id=%s FOR UPDATE", (handoff["work_issue_id"],))
        issue = _work_issue_record(conn, handoff["work_issue_id"])
        if issue["assigned_to"] != "hermes": raise AdmissionConflict("Work Issue is not assigned to Hermes")
        if issue["requested_effect"] != "read_only" or handoff["requested_effect"] != "read_only":
            raise AdmissionConflict("first execution-admission slice accepts read_only work only")
        if issue["status"] != "open": raise AdmissionConflict("execution admission requires an open Work Issue")
        if issue["task_contract_ref"] != handoff["task_contract_ref"]: raise AdmissionConflict("Task Contract changed")
        if issue["context_pack_ref"] != handoff["context_pack_ref"]: raise AdmissionConflict("Context Pack changed")
        try:
            execution_basis = HermesExecutionBasis.from_values(
                requested_effect=handoff["requested_effect"],
                task_contract_ref=handoff["task_contract_ref"],
                context_pack_ref=handoff["context_pack_ref"],
                preview_digest=handoff["preview_digest"],
                label="immutable handoff basis",
            )
        except HermesExecutionBasisError as exc:
            raise AdmissionConflict("immutable handoff basis is incomplete") from exc
        if _one(conn, "SELECT run_id FROM hermes_runs WHERE issue_id=%s LIMIT 1", (issue["issue_id"],)):
            raise AdmissionConflict("Work Issue already has a Hermes run")
        if _one(conn, "SELECT admission_id FROM hermes_execution_admissions WHERE handoff_id=%s LIMIT 1", (handoff_id,)):
            raise AdmissionConflict("handoff already has an execution admission")

        admitted_at = conn.execute("SELECT CURRENT_TIMESTAMP").fetchone()[0]
        expires_at = admitted_at + timedelta(seconds=ttl_seconds)
        admission_id = f"admission-{uuid.uuid4().hex}"
        admission_digest_basis = {
            "handoff_id": handoff_id, "work_issue_id": issue["issue_id"], "work_issue_version": issue["version"],
            "requested_effect": execution_basis.requested_effect,
            "task_contract_ref": execution_basis.task_contract_ref,
            "context_pack_ref": execution_basis.context_pack_ref,
            "preview_digest": execution_basis.preview_digest,
            "handoff_request_digest": handoff["request_digest"], "ttl_seconds": ttl_seconds,
            "expires_at": expires_at.isoformat(), "admitted_by": actor.strip(),
        }
        conn.execute(
            """INSERT INTO hermes_execution_admissions
            (admission_id,handoff_id,work_issue_id,decision,requested_effect,task_contract_ref,context_pack_ref,
             preview_digest,handoff_request_digest,admission_digest,idempotency_key,admitted_by,
             work_issue_version,ttl_seconds,expires_at,admitted_at)
            VALUES (%s,%s,%s,'allow',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                admission_id, handoff_id, issue["issue_id"], execution_basis.requested_effect,
                execution_basis.task_contract_ref, execution_basis.context_pack_ref,
                execution_basis.preview_digest, handoff["request_digest"],
                _digest(admission_digest_basis), idempotency_key, actor.strip(),
                issue["version"], ttl_seconds, expires_at, admitted_at,
            ),
        )
        return _projection(conn, _admission(conn, admission_id))


def revoke_admission(conn, *, admission_id: str, actor: str, reason: str, idempotency_key: str) -> dict:
    if not actor.strip(): raise HermesExecutionError("human actor is required for admission revocation")
    if not reason.strip(): raise HermesExecutionError("revocation reason is required")
    with conn.transaction():
        replay = _one(conn, "SELECT * FROM hermes_execution_admission_events WHERE idempotency_key=%s", (idempotency_key,))
        if replay:
            if replay["admission_id"] != admission_id or replay["actor"] != actor.strip() or replay["reason"] != reason.strip():
                raise AdmissionConflict("idempotency key already belongs to another revocation")
            return _projection(conn, _admission(conn, admission_id))
        admission = _admission(conn, admission_id, True)
        current = _projection(conn, admission)
        if current["admission_state"] != "admitted":
            raise AdmissionConflict(f"admission cannot be revoked from state {current['admission_state']}")
        conn.execute(
            "INSERT INTO hermes_execution_admission_events (event_id,admission_id,event_type,actor,reason,idempotency_key) VALUES (%s,%s,'revoked',%s,%s,%s)",
            (f"admission-event-{uuid.uuid4().hex}", admission_id, actor.strip(), reason.strip(), idempotency_key),
        )
        return _projection(conn, _admission(conn, admission_id))


def get_admission(conn, admission_id: str) -> dict:
    return _projection(conn, _admission(conn, admission_id))


def get_execution_envelope(conn, admission_id: str) -> dict:
    admission = _admission(conn, admission_id)
    handoff = _handoff(conn, admission["handoff_id"])
    projection = _projection(conn, admission)
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
        raise AdmissionConflict(
            "execution admission no longer matches immutable handoff"
        ) from exc
    if admission_basis != handoff_basis:
        raise AdmissionConflict("execution admission no longer matches immutable handoff")
    if not projection["ready_for_external_runtime"]:
        raise AdmissionConflict(f"execution admission is not consumable; current state is {projection['admission_state']}")
    return {"kind":"hermes_execution_envelope","admission":projection,"task_contract":handoff["task_contract"],
            "context_pack":handoff["context_pack"],"question":handoff["question"],
            "selected_context":list(handoff["selected_context"] or []),"runtime_instruction":None,"dispatch_requested":False}


def record_external_runtime_start(
    conn,
    *,
    admission_id: str,
    run_id: str,
    actor: str,
    expected_issue_version: int,
    idempotency_key: str,
    launch_reservation_id: str | None = None,
) -> dict:
    if not run_id.strip(): raise HermesExecutionError("external Hermes run_id is required")
    if not actor.strip(): raise HermesExecutionError("Hermes actor is required")
    with conn.transaction():
        admission = _admission(conn, admission_id, True)
        existing = _run(conn, admission_id)
        if existing:
            if existing["run_id"] != run_id: raise RuntimeStartConflict("admission already consumed by another run")
            return {"admission_id":admission_id,"run_id":run_id,"runtime_start_recorded":True,"replayed":True,
                    "launch_reservation_id":existing.get("launch_reservation_ref"),
                    "work_issue":_work_issue_record(conn, admission["work_issue_id"])}

        launch_reservation = _launch_reservation(conn, admission_id)
        current = _projection(conn, admission)
        if launch_reservation:
            if current["admission_state"] != "launch_reserved":
                raise RuntimeStartConflict(
                    f"reserved execution admission cannot start from state {current['admission_state']}"
                )
            if launch_reservation_id != launch_reservation["launch_reservation_id"]:
                raise RuntimeStartConflict("runtime start does not match the exact launch reservation")
            if expected_issue_version != launch_reservation["work_issue_version"]:
                raise RuntimeStartConflict(
                    f"runtime callback version {expected_issue_version} != reserved version {launch_reservation['work_issue_version']}"
                )
            issue = _work_issue_record(conn, admission["work_issue_id"])
            transition_expected_version = issue["version"]
        else:
            if launch_reservation_id is not None:
                raise RuntimeStartConflict("runtime start references an unknown launch reservation")
            if current["admission_state"] != "admitted":
                raise RuntimeStartConflict(f"execution admission is not consumable; current state is {current['admission_state']}")
            admitted_version = admission["work_issue_version"]
            if expected_issue_version != admitted_version:
                raise RuntimeStartConflict(f"runtime callback version {expected_issue_version} != admitted version {admitted_version}")
            issue = current["work_issue"]
            transition_expected_version = admitted_version

        started = work_issues.start_hermes_run(
            conn, issue_id=issue["issue_id"], run_id=run_id, task_contract_ref=admission["task_contract_ref"],
            context_pack_ref=admission["context_pack_ref"], actor=actor.strip(), expected_version=transition_expected_version,
            idempotency_key=idempotency_key,
        )
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE hermes_runs SET admission_ref=%s, launch_reservation_ref=%s WHERE run_id=%s AND admission_ref IS NULL",
                (
                    admission_id,
                    launch_reservation["launch_reservation_id"] if launch_reservation else None,
                    run_id,
                ),
            )
            if cur.rowcount != 1: raise RuntimeStartConflict("Hermes run admission linkage could not be recorded")
        return {
            "admission_id": admission_id,
            "run_id": run_id,
            "runtime_start_recorded": True,
            "replayed": False,
            "launch_reservation_id": launch_reservation["launch_reservation_id"] if launch_reservation else None,
            "reserved_work_issue_version": launch_reservation["work_issue_version"] if launch_reservation else None,
            "work_issue": started["work_issue"],
            "non_equivalences": [
                "runtime start recorded != Evidence",
                "launch reservation != dispatch",
                "running != task success",
            ],
        }
