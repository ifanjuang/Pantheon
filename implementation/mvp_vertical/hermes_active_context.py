"""Resolve scoped context from an admission-bound active Hermes session.

The external Run Binding sets Hermes ``session_id`` to the exact ``admission_id``.
A Hermes plugin can therefore derive the admission from its own task/session context
instead of accepting an arbitrary admission id from the model. This module resolves
the single linked running run server-side and delegates to the exact run-bound
Scoped Hermes Data Access implementation.
"""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row

from . import hermes_scoped_context


class HermesActiveContextError(ValueError):
    pass


class ActiveContextNotFound(HermesActiveContextError):
    pass


class ActiveContextConflict(HermesActiveContextError):
    pass


def _active_run_id(conn: psycopg.Connection, admission_id: str) -> str:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT run_id, status FROM hermes_runs WHERE admission_ref=%s",
            (admission_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise ActiveContextNotFound(
            f"no Hermes run is linked to execution admission: {admission_id}"
        )
    if row["status"] != "running":
        raise ActiveContextConflict(
            f"admission-bound context requires a running Hermes run; current status is {row['status']}"
        )
    return str(row["run_id"])


def get_active_context_manifest(
    conn: psycopg.Connection,
    *,
    admission_id: str,
    actor: str,
) -> dict[str, Any]:
    run_id = _active_run_id(conn, admission_id)
    result = hermes_scoped_context.get_context_manifest(
        conn,
        admission_id=admission_id,
        run_id=run_id,
        actor=actor,
    )
    return {
        **result,
        "access_path": "admission_session_resolved_to_exact_running_run",
        "caller_supplied_run_id": False,
    }


def get_active_context_entity(
    conn: psycopg.Connection,
    *,
    admission_id: str,
    entity_type: str,
    entity_id: str,
    actor: str,
) -> dict[str, Any]:
    run_id = _active_run_id(conn, admission_id)
    result = hermes_scoped_context.get_context_entity(
        conn,
        admission_id=admission_id,
        run_id=run_id,
        entity_type=entity_type,
        entity_id=entity_id,
        actor=actor,
    )
    return {
        **result,
        "access_path": "admission_session_resolved_to_exact_running_run",
        "caller_supplied_run_id": False,
    }
