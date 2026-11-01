"""Durable, shared processing order and controls for workspace vaults.

This module intentionally has no filesystem or Hindsight dependencies. Producers
own source inspection and remote operations; the queue owns priority, pause state,
and the status projection consumed by Cockpit.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import sqlite3
from typing import Any, Iterable, Iterator
import uuid


ACTIVE_STATUSES = {"TO_PROCESS", "ANALYZING", "ANALYZED", "MEMORIZING", "MODIFIED", "STABILIZING"}
ERROR_STATUSES = {"FAILED", "VERIFY"}
TERMINAL_STATUSES = {"MEMORIZED", "ARCHIVED"}
PROCESSING_LANES = frozenset({"preflight", "ocr", "hindsight"})
PROCESSING_LANE_STATES = frozenset({"active", "paused", "disabled"})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class CoordinatorLock:
    """Host-local exclusive lock preventing two producers from owning one queue."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        if not self.path.is_absolute():
            raise ValueError("coordinator lock path must be absolute")
        self._fd: int | None = None

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o640)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            os.close(fd)
            raise RuntimeError(f"another producer coordinator holds {self.path}") from exc
        self._fd = fd

    def release(self) -> None:
        if self._fd is None:
            return
        fcntl.flock(self._fd, fcntl.LOCK_UN)
        os.close(self._fd)
        self._fd = None


class ProcessingQueue:
    """SQLite-backed queue API. Calls are short transactions safe for worker/UI use."""

    def __init__(self, database: Path | str) -> None:
        self.database = Path(database)
        if not self.database.is_absolute():
            raise ValueError("processing queue database path must be absolute")
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        self.database.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=10000")
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Use a queue connection as a transaction and always release its file handles."""
        connection = self._connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _ensure_schema(self) -> None:
        with self._connection() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS processing_queue (
                    workspace TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    source_sha256 TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    preflight_status TEXT NOT NULL DEFAULT 'TO_PROCESS',
                    hindsight_status TEXT NOT NULL DEFAULT 'NOT_SENT',
                    operation_id TEXT,
                    error TEXT,
                    verification_requested_at TEXT,
                    user_decision TEXT NOT NULL DEFAULT 'AUTO',
                    ocr_status TEXT NOT NULL DEFAULT 'NONE',
                    ocr_requested_at TEXT,
                    ocr_filename TEXT,
                    ocr_output_path TEXT,
                    ocr_engine TEXT,
                    ocr_error TEXT,
                    ocr_is_revision INTEGER NOT NULL DEFAULT 0,
                    ocr_revision_origin_status TEXT,
                    ocr_preflight_source_sha256 TEXT,
                    ocr_replace_approved INTEGER NOT NULL DEFAULT 0,
                    revision INTEGER NOT NULL DEFAULT 1,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(workspace, document_id)
                );
                CREATE INDEX IF NOT EXISTS idx_processing_queue_order
                    ON processing_queue(priority, workspace, document_id);
                CREATE INDEX IF NOT EXISTS idx_processing_queue_status
                    ON processing_queue(hindsight_status, preflight_status);
                CREATE TABLE IF NOT EXISTS processing_controls (
                    scope TEXT PRIMARY KEY,
                    paused INTEGER NOT NULL CHECK(paused IN (0, 1)),
                    revision INTEGER NOT NULL DEFAULT 1,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS processing_item_controls (
                    workspace TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    lane TEXT NOT NULL CHECK(lane IN ('preflight', 'ocr', 'hindsight')),
                    paused INTEGER NOT NULL CHECK(paused IN (0, 1)),
                    revision INTEGER NOT NULL DEFAULT 1,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(workspace, document_id, lane)
                );
                CREATE TABLE IF NOT EXISTS processing_lane_controls (
                    lane TEXT PRIMARY KEY CHECK(lane IN ('preflight', 'ocr', 'hindsight')),
                    state TEXT NOT NULL CHECK(state IN ('active', 'paused', 'disabled')),
                    revision INTEGER NOT NULL DEFAULT 1,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS processing_worker_health (
                    worker_name TEXT PRIMARY KEY,
                    status_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS hindsight_tag_sync_requests (
                    request_id TEXT PRIMARY KEY,
                    mode TEXT NOT NULL DEFAULT 'tags',
                    workspace TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    hindsight_document_id TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    source_sha256 TEXT NOT NULL,
                    values_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error TEXT,
                    updated_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_hindsight_tag_sync_pending
                    ON hindsight_tag_sync_requests(status, created_at);
                CREATE UNIQUE INDEX IF NOT EXISTS idx_hindsight_tag_sync_one_active
                    ON hindsight_tag_sync_requests(workspace, document_id)
                    WHERE status IN ('PENDING', 'PROCESSING', 'SUBMITTED');
                INSERT OR IGNORE INTO processing_controls(scope, paused, updated_at)
                    VALUES ('global', 0, '');
                """
            )
            sync_columns = {
                str(row["name"])
                for row in connection.execute("PRAGMA table_info(hindsight_tag_sync_requests)").fetchall()
            }
            if "mode" not in sync_columns:
                connection.execute(
                    "ALTER TABLE hindsight_tag_sync_requests ADD COLUMN mode TEXT NOT NULL DEFAULT 'tags'"
                )
            connection.execute("DROP INDEX IF EXISTS idx_hindsight_tag_sync_one_active")
            connection.execute(
                "CREATE UNIQUE INDEX idx_hindsight_tag_sync_one_active "
                "ON hindsight_tag_sync_requests(workspace, document_id) "
                "WHERE status IN ('PENDING', 'PROCESSING', 'SUBMITTED')"
            )
            columns = {
                str(row["name"])
                for row in connection.execute("PRAGMA table_info(processing_queue)").fetchall()
            }
            if "verification_requested_at" not in columns:
                connection.execute(
                    "ALTER TABLE processing_queue ADD COLUMN verification_requested_at TEXT"
                )
            for column, definition in (
                ("user_decision", "TEXT NOT NULL DEFAULT 'AUTO'"),
                ("ocr_status", "TEXT NOT NULL DEFAULT 'NONE'"),
                ("ocr_requested_at", "TEXT"),
                ("ocr_filename", "TEXT"),
                ("ocr_output_path", "TEXT"),
                ("ocr_engine", "TEXT"),
                ("ocr_error", "TEXT"),
                ("ocr_is_revision", "INTEGER NOT NULL DEFAULT 0"),
                ("ocr_revision_origin_status", "TEXT"),
                ("ocr_preflight_source_sha256", "TEXT"),
                ("ocr_replace_approved", "INTEGER NOT NULL DEFAULT 0"),
                ("request_action", "TEXT"),
                ("request_note", "TEXT"),
            ):
                if column not in columns:
                    connection.execute(f"ALTER TABLE processing_queue ADD COLUMN {column} {definition}")

            # Older versions persisted an absolute cache path. Migrate that value
            # to a portable basename and stop exposing/storing the directory.
            legacy_paths = connection.execute(
                "SELECT workspace, document_id, ocr_output_path FROM processing_queue "
                "WHERE ocr_filename IS NULL AND ocr_output_path IS NOT NULL"
            ).fetchall()
            for row in legacy_paths:
                filename = Path(str(row["ocr_output_path"])).name
                portable_name = filename if filename.endswith(".md") and filename not in {".", ".."} else None
                connection.execute(
                    "UPDATE processing_queue SET ocr_filename=?, ocr_output_path=NULL "
                    "WHERE workspace=? AND document_id=?",
                    (portable_name, row["workspace"], row["document_id"]),
                )

    def publish_worker_health(self, worker_name: str, status: dict[str, Any]) -> None:
        """Persist a small, credential-free heartbeat for workers sharing this queue."""
        name = worker_name.strip()
        if not name or len(name) > 80:
            raise ValueError("worker_name must contain 1..80 characters")
        now = _now()
        payload = json.dumps(status, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        with self._connection() as connection:
            connection.execute(
                """INSERT INTO processing_worker_health(worker_name, status_json, updated_at)
                   VALUES (?, ?, ?) ON CONFLICT(worker_name) DO UPDATE SET
                   status_json=excluded.status_json, updated_at=excluded.updated_at""",
                (name, payload, now),
            )

    def worker_health(self, *, stale_after_seconds: float = 90.0) -> list[dict[str, Any]]:
        """Read worker heartbeats and flag stale reports without claiming liveness."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT worker_name, status_json, updated_at FROM processing_worker_health ORDER BY worker_name"
            ).fetchall()
        now = datetime.now(timezone.utc)
        result: list[dict[str, Any]] = []
        for row in rows:
            try:
                status = json.loads(row["status_json"])
            except (TypeError, json.JSONDecodeError):
                status = {"state_error": "invalid_status_json"}
            if not isinstance(status, dict):
                status = {"state_error": "invalid_status_shape"}
            try:
                updated = datetime.fromisoformat(str(row["updated_at"]).replace("Z", "+00:00"))
                age = max(0.0, (now - updated).total_seconds())
            except (TypeError, ValueError):
                age = None
            result.append({
                **status,
                "worker": str(row["worker_name"]),
                "heartbeat_at": row["updated_at"],
                "heartbeat_age_seconds": round(age, 1) if age is not None else None,
                "stale": age is None or age > max(1.0, float(stale_after_seconds)),
            })
        return result

    def upsert_candidate(
        self,
        *,
        workspace: str,
        document_id: str,
        source_path: str,
        source_sha256: str,
        preflight_status: str = "ANALYZED",
        hindsight_status: str = "NOT_SENT",
    ) -> dict[str, Any]:
        """Register a candidate without changing its user-set priority."""
        if not all(isinstance(value, str) and value.strip() for value in (workspace, document_id, source_path, source_sha256)):
            raise ValueError("workspace, document_id, source_path and source_sha256 are required")
        now = _now()
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            old = connection.execute(
                "SELECT * FROM processing_queue WHERE workspace=? AND document_id=?",
                (workspace, document_id),
            ).fetchone()
            if old is None:
                priority = int(connection.execute(
                    "SELECT COALESCE(MAX(priority), 0) + 1000 FROM processing_queue"
                ).fetchone()[0])
                connection.execute(
                    """INSERT INTO processing_queue(
                        workspace, document_id, source_path, source_sha256, priority,
                        preflight_status, hindsight_status, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (workspace, document_id, source_path, source_sha256, priority,
                     preflight_status, hindsight_status, now),
                )
            elif old["source_sha256"] != source_sha256 or old["source_path"] != source_path:
                # Preserve the identity and priority; invalidate work bound to the old source.
                connection.execute(
                    """UPDATE processing_queue SET source_path=?, source_sha256=?,
                        preflight_status='STABILIZING', hindsight_status='MODIFIED',
                        operation_id=NULL, error=NULL, verification_requested_at=NULL,
                        request_action=NULL, request_note=NULL,
                        user_decision='AUTO', ocr_status='NONE', ocr_requested_at=NULL,
                        ocr_filename=NULL, ocr_output_path=NULL, ocr_engine=NULL, ocr_error=NULL,
                        ocr_is_revision=0, ocr_revision_origin_status=NULL,
                        ocr_preflight_source_sha256=NULL, ocr_replace_approved=0,
                        revision=revision+1, updated_at=?
                        WHERE workspace=? AND document_id=?""",
                    (source_path, source_sha256, now, workspace, document_id),
                )
            elif old["hindsight_status"] == "ARCHIVED":
                # A source that reappears after the two-observation archive is a
                # fresh ingestion candidate. Keep its priority but clear the old
                # terminal result and let the producer re-check source stability.
                connection.execute(
                    """UPDATE processing_queue SET preflight_status='STABILIZING',
                        hindsight_status='MODIFIED', operation_id=NULL, error=NULL,
                        verification_requested_at=NULL, request_action=NULL, request_note=NULL,
                        user_decision='AUTO',
                        ocr_status='NONE', ocr_requested_at=NULL, ocr_filename=NULL, ocr_output_path=NULL,
                        ocr_engine=NULL, ocr_error=NULL, ocr_is_revision=0,
                        ocr_revision_origin_status=NULL, ocr_preflight_source_sha256=NULL,
                        ocr_replace_approved=0,
                        revision=revision+1, updated_at=?
                        WHERE workspace=? AND document_id=?""",
                    (now, workspace, document_id),
                )
            elif old["hindsight_status"] == "QUEUED" and hindsight_status == "FAILED":
                # A manual retry is durable intent. Keep it queued when the sync
                # table still carries the previous terminal error; the producer
                # will atomically move it to MEMORIZING before the remote submit.
                pass
            elif old["hindsight_status"] in {"NOT_SENT", "QUEUED"}:
                connection.execute(
                    """UPDATE processing_queue SET
                        preflight_status=CASE WHEN preflight_status IN ('ANALYZING','ANALYZED','FAILED')
                            THEN preflight_status ELSE ? END,
                        hindsight_status=?, updated_at=?
                        WHERE workspace=? AND document_id=?""",
                    (preflight_status, hindsight_status, now, workspace, document_id),
                )
            connection.commit()
            row = connection.execute(
                "SELECT * FROM processing_queue WHERE workspace=? AND document_id=?",
                (workspace, document_id),
            ).fetchone()
            return dict(row)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def set_status(
        self,
        workspace: str,
        document_id: str,
        *,
        preflight_status: str | None = None,
        hindsight_status: str | None = None,
        operation_id: str | None = None,
        error: str | None = None,
        clear_operation_id: bool = False,
        clear_error: bool = False,
    ) -> None:
        assignments = ["revision=revision+1", "updated_at=?"]
        values: list[Any] = [_now()]
        for column, value in (
            ("preflight_status", preflight_status),
            ("hindsight_status", hindsight_status),
            ("operation_id", operation_id),
            ("error", error),
        ):
            if value is not None:
                assignments.append(f"{column}=?")
                values.append(value)
        if hindsight_status is not None and hindsight_status != "VERIFY":
            assignments.append("verification_requested_at=NULL")
        if clear_operation_id:
            assignments.append("operation_id=NULL")
        if clear_error:
            assignments.append("error=NULL")
        values.extend((workspace, document_id))
        with self._connection() as connection:
            connection.execute(
                f"UPDATE processing_queue SET {', '.join(assignments)} WHERE workspace=? AND document_id=?",
                values,
            )

    def list_items(self, *, workspace: str | None = None, include_memorized: bool = False) -> dict[str, Any]:
        clauses: list[str] = []
        values: list[Any] = []
        if workspace:
            clauses.append("q.workspace=?")
            values.append(workspace)
        if not include_memorized:
            clauses.append("q.hindsight_status NOT IN ('MEMORIZED','ARCHIVED')")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connection() as connection:
            rows = connection.execute(
                f"""SELECT q.*,
                    COALESCE((SELECT paused FROM processing_item_controls c
                        WHERE c.workspace=q.workspace AND c.document_id=q.document_id AND c.lane='preflight'), 0)
                        AS paused_preflight,
                    COALESCE((SELECT paused FROM processing_item_controls c
                        WHERE c.workspace=q.workspace AND c.document_id=q.document_id AND c.lane='ocr'), 0)
                        AS paused_ocr,
                    COALESCE((SELECT paused FROM processing_item_controls c
                        WHERE c.workspace=q.workspace AND c.document_id=q.document_id AND c.lane='hindsight'), 0)
                        AS paused_hindsight
                    FROM processing_queue q {where}
                    ORDER BY q.priority, q.workspace, q.document_id""",
                values,
            ).fetchall()
            controls = connection.execute(
                "SELECT scope, paused, revision, updated_at FROM processing_controls ORDER BY scope"
            ).fetchall()
            queue_revision = int(connection.execute(
                "SELECT COALESCE(MAX(revision), 0) FROM processing_queue "
                "WHERE hindsight_status NOT IN ('MEMORIZED','ARCHIVED')"
            ).fetchone()[0])
        return {
            "items": [dict(row) for row in rows],
            "controls": [dict(row) for row in controls],
            "revision": queue_revision,
        }

    def status_summary(self) -> dict[str, Any]:
        """Return global worker/service state for the Cockpit header, never per-item state."""
        with self._connection() as connection:
            controls = connection.execute(
                "SELECT scope, paused, revision, updated_at FROM processing_controls ORDER BY scope"
            ).fetchall()
            lane_controls = {
                str(row["lane"]): dict(row)
                for row in connection.execute(
                    "SELECT lane, state, revision, updated_at FROM processing_lane_controls"
                ).fetchall()
            }
        global_paused = any(row["scope"] == "global" and bool(row["paused"]) for row in controls)
        workers = {row["worker"]: row for row in self.worker_health()}
        lanes: dict[str, dict[str, Any]] = {}
        for lane_name, worker_name in (
            ("preflight", "preflight"),
            ("ocr", "ocr"),
            ("hindsight", "hindsight"),
        ):
            worker = workers.get(worker_name)
            control = lane_controls.get(lane_name) or {"state": "active", "revision": 0, "updated_at": None}
            control_state = str(control["state"])
            enabled = bool(worker and worker.get("enabled", True)) and control_state != "disabled"
            running = bool(worker and worker.get("running"))
            stale = worker is None or bool(worker.get("stale"))
            healthy = bool(worker and worker.get("healthy", True))
            state = (
                "disabled" if control_state == "disabled" or (worker is not None and not worker.get("enabled", True))
                else "error" if stale or not running or not healthy
                else "paused" if global_paused or control_state == "paused"
                else "active"
            )
            lanes[lane_name] = {
                "state": state,
                "control_state": control_state,
                "control_revision": int(control["revision"]),
                "enabled": enabled,
                "running": running,
                "healthy": healthy,
                "heartbeat_at": worker.get("heartbeat_at") if worker else None,
                "last_error": worker.get("last_error") if worker else "État global du worker indisponible",
            }
        return {
            "global_paused": global_paused,
            "controls": [dict(row) for row in controls],
            "lanes": lanes,
        }

    def request_hindsight_metadata_sync(
        self,
        *,
        mode: str,
        workspace: str,
        document_id: str,
        hindsight_document_id: str,
        source_path: str,
        source_sha256: str,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        """Queue a confirmed tag update or explicit reingestion request."""
        if mode not in {"tags", "reingest"}:
            raise ValueError("invalid_hindsight_metadata_sync_mode")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            active = connection.execute(
                "SELECT request_id, status, mode FROM hindsight_tag_sync_requests "
                "WHERE workspace=? AND document_id=? AND status IN ('PENDING','PROCESSING','SUBMITTED')",
                (workspace, document_id),
            ).fetchone()
            if active is not None:
                connection.commit()
                return {"request_id": active["request_id"], "status": active["status"], "mode": active["mode"]}
            request_id = uuid.uuid4().hex
            now = _now()
            connection.execute(
                """INSERT INTO hindsight_tag_sync_requests(
                       request_id, mode, workspace, document_id, hindsight_document_id, source_path,
                       source_sha256, values_json, status, updated_at, created_at
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?, ?)""",
                (request_id, mode, workspace, document_id, hindsight_document_id, source_path,
                 source_sha256, json.dumps(values, ensure_ascii=False, sort_keys=True), now, now),
            )
            connection.commit()
        return {"request_id": request_id, "status": "PENDING", "mode": mode}

    def claim_hindsight_metadata_sync(self) -> dict[str, Any] | None:
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT request.* FROM hindsight_tag_sync_requests AS request "
                "WHERE request.status='PENDING' "
                "AND NOT EXISTS (SELECT 1 FROM processing_controls AS control "
                "WHERE control.paused=1 AND control.scope IN ('global', request.workspace)) "
                "AND COALESCE((SELECT state FROM processing_lane_controls WHERE lane='hindsight'), 'active')='active' "
                "AND NOT EXISTS (SELECT 1 FROM processing_item_controls AS item_control "
                "WHERE item_control.paused=1 AND item_control.workspace=request.workspace "
                "AND item_control.document_id=request.document_id AND item_control.lane='hindsight') "
                "ORDER BY request.created_at, request.request_id LIMIT 1"
            ).fetchone()
            if row is None:
                connection.commit()
                return None
            updated = connection.execute(
                "UPDATE hindsight_tag_sync_requests SET status='PROCESSING', error=NULL, updated_at=? "
                "WHERE request_id=? AND status='PENDING'",
                (_now(), row["request_id"]),
            )
            connection.commit()
            if updated.rowcount != 1:
                return None
            return dict(row) | {"status": "PROCESSING"}

    def recover_interrupted_hindsight_metadata_sync(self) -> int:
        with self._connection() as connection:
            cursor = connection.execute(
                "UPDATE hindsight_tag_sync_requests SET "
                "status=CASE WHEN mode='reingest' THEN 'FAILED' ELSE 'PENDING' END, "
                "error=CASE WHEN mode='reingest' THEN 'Issue de réingestion interrompue; vérifiez Hindsight avant de réessayer.' ELSE NULL END, "
                "updated_at=? "
                "WHERE status='PROCESSING'",
                (_now(),),
            )
            return int(cursor.rowcount)

    def finish_hindsight_metadata_sync(self, request_id: str, *, status: str, error: str | None = None) -> None:
        if status not in {"SUBMITTED", "COMPLETED", "FAILED"}:
            raise ValueError("metadata_sync_status_invalid")
        with self._connection() as connection:
            connection.execute(
                "UPDATE hindsight_tag_sync_requests SET status=?, error=?, updated_at=? "
                "WHERE request_id=? AND status='PROCESSING'",
                (status, error, _now(), request_id),
            )

    def pending_hindsight_metadata_sync_submissions(self) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT request_id, workspace, document_id, hindsight_document_id "
                "FROM hindsight_tag_sync_requests WHERE status='SUBMITTED' ORDER BY created_at"
            ).fetchall()
            return [dict(row) for row in rows]

    def finish_submitted_hindsight_metadata_sync(
        self, request_id: str, *, status: str, error: str | None = None
    ) -> None:
        if status not in {"COMPLETED", "FAILED"}:
            raise ValueError("metadata_sync_terminal_status_required")
        with self._connection() as connection:
            connection.execute(
                "UPDATE hindsight_tag_sync_requests SET status=?, error=?, updated_at=? "
                "WHERE request_id=? AND status='SUBMITTED'",
                (status, error, _now(), request_id),
            )

    def get_hindsight_tag_sync(self, request_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT request_id, workspace, document_id, mode, status, error, updated_at "
                "FROM hindsight_tag_sync_requests WHERE request_id=?",
                (request_id,),
            ).fetchone()
            return dict(row) if row is not None else None

    def latest_hindsight_tag_sync(self, workspace: str, document_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT request_id, status, error, updated_at FROM hindsight_tag_sync_requests "
                "WHERE workspace=? AND document_id=? ORDER BY created_at DESC, request_id DESC LIMIT 1",
                (workspace, document_id),
            ).fetchone()
            return dict(row) if row is not None else None

    def reorder(self, ordered_ids: Iterable[tuple[str, str]], *, expected_revision: int | None = None) -> dict[str, Any]:
        order = list(ordered_ids)
        if not order or len(set(order)) != len(order):
            raise ValueError("order must contain unique workspace/document pairs")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            current = connection.execute(
                "SELECT workspace, document_id, revision FROM processing_queue "
                "WHERE hindsight_status NOT IN ('MEMORIZED','ARCHIVED') "
                "ORDER BY priority, workspace, document_id"
            ).fetchall()
            current_ids = [(row["workspace"], row["document_id"]) for row in current]
            revision = max((int(row["revision"]) for row in current), default=0)
            if expected_revision is not None and revision != expected_revision:
                raise RuntimeError("queue_revision_conflict")
            if set(order) != set(current_ids):
                raise ValueError("order must include every active queue item exactly once")
            now = _now()
            for index, (workspace, document_id) in enumerate(order, start=1):
                connection.execute(
                    "UPDATE processing_queue SET priority=?, revision=revision+1, updated_at=? "
                    "WHERE workspace=? AND document_id=?",
                    (index * 1000, now, workspace, document_id),
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return self.list_items(include_memorized=False)

    def move(
        self,
        item_id: tuple[str, str],
        position: int,
        *,
        expected_revision: int | None = None,
    ) -> dict[str, Any]:
        """Move one item by index without sending the whole queue over HTTP."""
        if not isinstance(position, int) or isinstance(position, bool) or position < 0:
            raise ValueError("position_must_be_nonnegative_integer")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute(
                "SELECT workspace, document_id, revision FROM processing_queue "
                "WHERE hindsight_status NOT IN ('MEMORIZED','ARCHIVED') "
                "ORDER BY priority, workspace, document_id"
            ).fetchall()
            order = [(row["workspace"], row["document_id"]) for row in rows]
            revision = max((int(row["revision"]) for row in rows), default=0)
            if expected_revision is not None and revision != expected_revision:
                raise RuntimeError("queue_revision_conflict")
            if item_id not in order:
                raise ValueError("queue_item_not_found")
            if position >= len(order):
                raise ValueError("position_out_of_range")
            order.remove(item_id)
            order.insert(position, item_id)
            now = _now()
            for index, (workspace, document_id) in enumerate(order, start=1):
                connection.execute(
                    "UPDATE processing_queue SET priority=?, revision=revision+1, updated_at=? "
                    "WHERE workspace=? AND document_id=?",
                    (index * 1000, now, workspace, document_id),
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return self.list_items(include_memorized=False)

    def set_paused(self, scope: str, paused: bool, *, expected_revision: int | None = None) -> dict[str, Any]:
        if scope != "global" and (not scope.startswith("vault:") or not scope[6:].strip()):
            raise ValueError("scope must be global or vault:<name>")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            current = connection.execute(
                "SELECT revision FROM processing_controls WHERE scope=?", (scope,)
            ).fetchone()
            revision = int(current["revision"]) if current else 0
            if expected_revision is not None and revision != expected_revision:
                raise RuntimeError("control_revision_conflict")
            connection.execute(
                """INSERT INTO processing_controls(scope, paused, revision, updated_at)
                   VALUES (?, ?, 1, ?) ON CONFLICT(scope) DO UPDATE SET
                   paused=excluded.paused, revision=processing_controls.revision+1,
                   updated_at=excluded.updated_at""",
                (scope, int(paused), _now()),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return self.list_items()

    def set_lane_state(
        self,
        lane: str,
        state: str,
        *,
        expected_revision: int | None = None,
    ) -> dict[str, Any]:
        """Set global admission state for one processing lane."""
        if lane not in PROCESSING_LANES:
            raise ValueError("invalid_processing_lane")
        if state not in PROCESSING_LANE_STATES:
            raise ValueError("invalid_processing_lane_state")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            current = connection.execute(
                "SELECT revision FROM processing_lane_controls WHERE lane=?", (lane,)
            ).fetchone()
            revision = int(current["revision"]) if current else 0
            if expected_revision is not None and revision != expected_revision:
                raise RuntimeError("control_revision_conflict")
            connection.execute(
                """INSERT INTO processing_lane_controls(lane, state, revision, updated_at)
                   VALUES (?, ?, 1, ?) ON CONFLICT(lane) DO UPDATE SET
                   state=excluded.state, revision=processing_lane_controls.revision+1,
                   updated_at=excluded.updated_at""",
                (lane, state, _now()),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return self.status_summary()

    def is_paused(self, workspace: str) -> bool:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT scope, paused FROM processing_controls WHERE scope IN ('global', ?) ",
                (f"vault:{workspace}",),
            ).fetchall()
        return any(bool(row["paused"]) for row in rows)

    def set_items_paused(
        self,
        items: Iterable[tuple[str, str]],
        lane: str,
        paused: bool,
    ) -> dict[str, Any]:
        """Pause or resume one lane for exactly the supplied queue rows."""
        if lane not in {"preflight", "ocr", "hindsight"}:
            raise ValueError("invalid_processing_lane")
        selected = list(items)
        if not selected or len(selected) > 4096 or len(set(selected)) != len(selected):
            raise ValueError("items_must_be_nonempty_unique_queue_ids")
        if any(
            not isinstance(workspace, str) or not workspace.strip()
            or not isinstance(document_id, str) or not document_id.strip()
            for workspace, document_id in selected
        ):
            raise ValueError("invalid_queue_item_id")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            for workspace, document_id in selected:
                exists = connection.execute(
                    "SELECT 1 FROM processing_queue WHERE workspace=? AND document_id=?",
                    (workspace, document_id),
                ).fetchone()
                if exists is None:
                    raise ValueError("queue_item_not_found")
            now = _now()
            for workspace, document_id in selected:
                connection.execute(
                    """INSERT INTO processing_item_controls(
                        workspace, document_id, lane, paused, revision, updated_at
                    ) VALUES (?, ?, ?, ?, 1, ?)
                    ON CONFLICT(workspace, document_id, lane) DO UPDATE SET
                        paused=excluded.paused,
                        revision=processing_item_controls.revision+1,
                        updated_at=excluded.updated_at""",
                    (workspace, document_id, lane, int(paused), now),
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return self.list_items()

    def is_item_paused(self, workspace: str, document_id: str, lane: str) -> bool:
        """Return whether global, lane, vault, or item-specific control blocks work."""
        if lane not in PROCESSING_LANES:
            raise ValueError("invalid_processing_lane")
        connection = self._connect()
        try:
            controls = connection.execute(
                "SELECT paused FROM processing_controls WHERE scope IN ('global', ?) ",
                (f"vault:{workspace}",),
            ).fetchall()
            lane_control = connection.execute(
                "SELECT state FROM processing_lane_controls WHERE lane=?", (lane,)
            ).fetchone()
            item_control = connection.execute(
                """SELECT paused FROM processing_item_controls
                   WHERE workspace=? AND document_id=? AND lane=?""",
                (workspace, document_id, lane),
            ).fetchone()
        finally:
            connection.close()
        return bool(lane_control and lane_control["state"] != "active") or any(bool(row["paused"]) for row in controls) or bool(
            item_control and item_control["paused"]
        )

    def retry(self, workspace: str, document_id: str, *, note: str | None = None) -> None:
        requested_at = _now()
        with self._connection() as connection:
            cursor = connection.execute(
                """UPDATE processing_queue SET preflight_status='TO_PROCESS',
                    hindsight_status=CASE
                        WHEN ocr_status='FAILED' AND lower(source_path) LIKE '%.pdf' THEN 'OCR_QUEUED'
                        WHEN ocr_status IN ('READY','SUBMITTED') AND ocr_filename IS NOT NULL THEN 'OCR_READY'
                        ELSE 'QUEUED' END,
                    ocr_status=CASE WHEN ocr_status='FAILED' AND lower(source_path) LIKE '%.pdf'
                        THEN 'QUEUED' ELSE ocr_status END,
                    ocr_requested_at=CASE WHEN ocr_status='FAILED' AND lower(source_path) LIKE '%.pdf'
                        THEN ? ELSE ocr_requested_at END,
                    ocr_error=CASE WHEN ocr_status='FAILED' AND lower(source_path) LIKE '%.pdf'
                        THEN NULL ELSE ocr_error END,
                    operation_id=NULL, error=NULL, request_action='memorize', request_note=?,
                    revision=revision+1, updated_at=?
                    WHERE workspace=? AND document_id=? AND hindsight_status='FAILED'""",
                (requested_at, note, requested_at, workspace, document_id),
            )
            if cursor.rowcount == 0:
                row = connection.execute(
                    "SELECT hindsight_status FROM processing_queue WHERE workspace=? AND document_id=?",
                    (workspace, document_id),
                ).fetchone()
                if row is None:
                    raise ValueError("queue_item_not_found")
                if row["hindsight_status"] == "VERIFY":
                    raise RuntimeError("remote_outcome_requires_verification_before_retry")
                raise RuntimeError("queue_item_not_retryable")

    def continue_after_error(self, workspace: str, document_id: str) -> None:
        """Skip a terminal error while preserving its diagnostics and OCR artifact."""
        with self._connection() as connection:
            cursor = connection.execute(
                """UPDATE processing_queue SET user_decision='DO_NOT_SEND',
                    hindsight_status='NOT_MEMORIZED', operation_id=NULL,
                    revision=revision+1, updated_at=?
                    WHERE workspace=? AND document_id=?
                      AND operation_id IS NULL
                      AND (hindsight_status IN ('FAILED','OCR_NEEDED')
                           OR preflight_status='FAILED' OR ocr_status='FAILED')
                      AND ocr_status NOT IN ('PROCESSING','SUBMITTED')""",
                (_now(), workspace, document_id),
            )
            if cursor.rowcount == 0:
                row = connection.execute(
                    "SELECT hindsight_status, preflight_status, ocr_status, operation_id "
                    "FROM processing_queue WHERE workspace=? AND document_id=?",
                    (workspace, document_id),
                ).fetchone()
                if row is None:
                    raise ValueError("queue_item_not_found")
                if row["operation_id"] or row["hindsight_status"] == "VERIFY":
                    raise RuntimeError("active_or_uncertain_operation_cannot_be_skipped")
                raise RuntimeError("queue_item_has_no_skippable_error")

    def preflight_requests(self, *, limit: int = 4096) -> list[dict[str, Any]]:
        """Return pending preflight work in the shared user-defined queue order."""
        with self._connection() as connection:
            rows = connection.execute(
                """SELECT workspace, document_id, source_path, source_sha256,
                          preflight_status, hindsight_status, ocr_status, ocr_filename
                   FROM processing_queue
                   WHERE preflight_status IN ('TO_PROCESS','STABILIZING')
                     AND hindsight_status NOT IN ('MEMORIZED','ARCHIVED')
                   ORDER BY priority, workspace, document_id LIMIT ?""",
                (max(1, min(int(limit), 4096)),),
            ).fetchall()
        return [dict(row) for row in rows]

    def request_preflight(self, workspace: str, document_id: str, *, note: str | None = None) -> None:
        """Explicitly re-run metadata analysis without requesting Hindsight ingestion."""
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT hindsight_status, preflight_status, operation_id, ocr_status FROM processing_queue "
                "WHERE workspace=? AND document_id=?",
                (workspace, document_id),
            ).fetchone()
            if row is None:
                raise ValueError("queue_item_not_found")
            if (
                row["hindsight_status"] in {"MEMORIZING", "MEMORIZED", "ARCHIVED", "VERIFY"}
                or row["preflight_status"] == "ANALYZING"
                or row["operation_id"] is not None
                or row["ocr_status"] in {"PROCESSING", "SUBMITTED"}
            ):
                raise RuntimeError("queue_item_not_reanalyzable_while_active_or_memorized")
            connection.execute(
                """UPDATE processing_queue SET preflight_status='TO_PROCESS',
                    request_action='reanalyze', request_note=?,
                    error=CASE WHEN error LIKE 'Analyse :%' THEN NULL ELSE error END,
                    revision=revision+1, updated_at=?
                   WHERE workspace=? AND document_id=? AND preflight_status!='ANALYZING'""",
                (note, _now(), workspace, document_id),
            )

    def queue_missing_ocr_preflights(self) -> None:
        """Queue OCR-ready artifacts that have not had metadata preflight on this source version."""
        with self._connection() as connection:
            connection.execute(
                """UPDATE processing_queue SET preflight_status='TO_PROCESS',
                    revision=revision+1, updated_at=?
                   WHERE ocr_status='READY' AND ocr_filename IS NOT NULL
                     AND preflight_status='ANALYZED'
                     AND (hindsight_status='OCR_READY'
                          OR (hindsight_status='MODIFIED' AND ocr_is_revision=1))
                     AND COALESCE(ocr_preflight_source_sha256,'') != source_sha256""",
                (_now(),),
            )

    def queue_ocr_after_empty_analysis(
        self, workspace: str, document_id: str, source_sha256: str
    ) -> bool:
        """Continue analysis with OCR when a PDF has no native text layer."""
        requested_at = _now()
        with self._connection() as connection:
            cursor = connection.execute(
                """UPDATE processing_queue SET preflight_status='ANALYZED',
                    hindsight_status='OCR_QUEUED', ocr_status='QUEUED',
                    ocr_requested_at=?, ocr_engine=NULL, ocr_error=NULL, error=NULL,
                    revision=revision+1, updated_at=?
                   WHERE workspace=? AND document_id=? AND source_sha256=?
                     AND preflight_status='ANALYZING' AND ocr_status='NONE'
                     AND lower(source_path) LIKE '%.pdf'
                     AND user_decision='AUTO'""",
                (requested_at, requested_at, workspace, document_id, source_sha256),
            )
        return cursor.rowcount == 1

    def mark_ocr_preflight_done(
        self, workspace: str, document_id: str, source_sha256: str
    ) -> None:
        with self._connection() as connection:
            connection.execute(
                """UPDATE processing_queue SET ocr_preflight_source_sha256=?,
                    revision=revision+1, updated_at=?
                   WHERE workspace=? AND document_id=? AND source_sha256=?
                     AND ocr_status='READY'""",
                (source_sha256, _now(), workspace, document_id, source_sha256),
            )

    def claim_preflight(self, workspace: str, document_id: str, source_sha256: str) -> bool:
        """Atomically claim preflight only for the source version still in the queue."""
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            controls = connection.execute(
                "SELECT scope, paused FROM processing_controls WHERE scope IN ('global', ?)",
                (f"vault:{workspace}",),
            ).fetchall()
            item_control = connection.execute(
                """SELECT paused FROM processing_item_controls
                   WHERE workspace=? AND document_id=? AND lane='preflight'""",
                (workspace, document_id),
            ).fetchone()
            if any(bool(row["paused"]) for row in controls) or bool(
                item_control and item_control["paused"]
            ):
                connection.rollback()
                return False
            cursor = connection.execute(
                """UPDATE processing_queue SET preflight_status='ANALYZING',
                    revision=revision+1, updated_at=?
                   WHERE workspace=? AND document_id=? AND source_sha256=?
                     AND preflight_status IN ('TO_PROCESS','STABILIZING')
                     AND hindsight_status NOT IN ('MEMORIZED','ARCHIVED')""",
                (_now(), workspace, document_id, source_sha256),
            )
            connection.commit()
            return cursor.rowcount == 1
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def recover_interrupted_preflight(self) -> None:
        """Make a lost in-memory preflight retryable after producer restart."""
        with self._connection() as connection:
            connection.execute(
                """UPDATE processing_queue SET preflight_status='TO_PROCESS',
                    revision=revision+1, updated_at=? WHERE preflight_status='ANALYZING'""",
                (_now(),),
            )

    def request_ocr(self, workspace: str, document_id: str, *, note: str | None = None) -> str:
        """Persist an explicit OCR run, including replacing an existing OCR revision."""
        requested_at = _now()
        with self._connection() as connection:
            current = connection.execute(
                "SELECT hindsight_status, ocr_status, ocr_revision_origin_status FROM processing_queue WHERE workspace=? AND document_id=?",
                (workspace, document_id),
            ).fetchone()
            if current is None:
                raise ValueError("queue_item_not_found")
            failed_retry = current["hindsight_status"] in {"FAILED", "OCR_NEEDED"}
            replace_existing = current["hindsight_status"] in {"MEMORIZED", "MODIFIED"} and current["ocr_status"] in {"DONE", "READY", "FAILED"}
            if not (failed_retry or replace_existing):
                raise RuntimeError("queue_item_not_ocr_retryable")
            cursor = connection.execute(
                """UPDATE processing_queue SET hindsight_status='OCR_QUEUED', ocr_status='QUEUED',
                    ocr_replace_approved=0,
                    request_action='ocr', request_note=?,
                    ocr_requested_at=?, ocr_is_revision=?,
                    ocr_revision_origin_status=CASE WHEN ?=1 THEN ? ELSE NULL END,
                    ocr_engine=NULL, ocr_error=NULL, ocr_preflight_source_sha256=NULL,
                    revision=revision+1, updated_at=?
                    WHERE workspace=? AND document_id=?
                    AND ((hindsight_status IN ('FAILED','OCR_NEEDED'))
                         OR (hindsight_status IN ('MEMORIZED','MODIFIED') AND ocr_status IN ('DONE','READY','FAILED') AND ocr_filename IS NOT NULL))
                    AND lower(source_path) LIKE '%.pdf'
                    AND (lower(COALESCE(error,'')) LIKE '%no content extracted%'
                         OR lower(COALESCE(error,'')) LIKE '%no text extracted%'
                         OR lower(COALESCE(error,'')) LIKE '%ocr_needed%'
                         OR ocr_status IN ('DONE','READY','FAILED'))""",
                (note, requested_at, int(replace_existing), int(replace_existing), current["hindsight_status"], requested_at, workspace, document_id),
            )
            if cursor.rowcount == 0:
                row = connection.execute(
                    "SELECT hindsight_status, source_path, error FROM processing_queue WHERE workspace=? AND document_id=?",
                    (workspace, document_id),
                ).fetchone()
                if row is None:
                    raise ValueError("queue_item_not_found")
                raise RuntimeError("queue_item_not_ocr_retryable")
        return requested_at

    def approve_ocr_replacement(
        self, workspace: str, document_id: str, *, mode: str, note: str | None = None
    ) -> None:
        """Authorize OCR replacement, optionally after refreshing its metadata preflight."""
        if mode not in {"analyze_and_ingest", "ingest_only"}:
            raise ValueError("ocr_replacement_mode_invalid")
        if mode == "analyze_and_ingest":
            assignments = """preflight_status='TO_PROCESS', hindsight_status='VERIFY',
                ocr_status='READY', ocr_preflight_source_sha256=NULL,
                ocr_replace_approved=0, operation_id=NULL,
                verification_requested_at=NULL,
                request_action='replace_ocr_after_analysis', request_note=?,
                revision=revision+1, updated_at=?"""
            values: tuple[Any, ...] = (note, _now(), workspace, document_id)
            preflight_guard = ""
        else:
            assignments = """preflight_status='ANALYZED', hindsight_status='OCR_READY',
                ocr_status='READY', ocr_replace_approved=1, operation_id=NULL,
                verification_requested_at=NULL, error=NULL,
                request_action='replace_ocr', request_note=?,
                revision=revision+1, updated_at=?"""
            values = (note, _now(), workspace, document_id)
            preflight_guard = "AND ocr_preflight_source_sha256=source_sha256"
        with self._connection() as connection:
            cursor = connection.execute(
                f"""UPDATE processing_queue SET {assignments}
                   WHERE workspace=? AND document_id=?
                     AND hindsight_status='VERIFY'
                     AND (error LIKE '%Hindsight document already exists; OCR replacement requires operator review%'
                          OR request_action='replace_ocr_after_analysis')
                     AND ocr_status IN ('READY','SUBMITTED')
                     AND ocr_filename IS NOT NULL AND ocr_filename LIKE '%.md'
                     {preflight_guard}
                     AND user_decision!='DO_NOT_SEND'""",
                values,
            )
            if cursor.rowcount == 0:
                row = connection.execute(
                    "SELECT hindsight_status, error FROM processing_queue WHERE workspace=? AND document_id=?",
                    (workspace, document_id),
                ).fetchone()
                if row is None:
                    raise ValueError("queue_item_not_found")
                raise RuntimeError("ocr_replacement_not_awaiting_approval")

    def complete_preflight(
        self, workspace: str, document_id: str, source_sha256: str
    ) -> bool:
        """Complete analysis and arm a reviewed OCR replacement only for this source version."""
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """SELECT request_action, hindsight_status, ocr_status,
                          ocr_preflight_source_sha256
                   FROM processing_queue WHERE workspace=? AND document_id=?
                     AND source_sha256=? AND preflight_status='ANALYZING'""",
                (workspace, document_id, source_sha256),
            ).fetchone()
            if row is None:
                connection.rollback()
                return False
            if row["request_action"] == "replace_ocr_after_analysis":
                if not (
                    row["hindsight_status"] == "VERIFY"
                    and row["ocr_status"] == "READY"
                    and row["ocr_preflight_source_sha256"] == source_sha256
                ):
                    connection.rollback()
                    return False
                connection.execute(
                    """UPDATE processing_queue SET preflight_status='ANALYZED',
                        hindsight_status='OCR_READY', ocr_replace_approved=1,
                        request_action='replace_ocr', error=NULL,
                        revision=revision+1, updated_at=?
                       WHERE workspace=? AND document_id=? AND source_sha256=?
                         AND preflight_status='ANALYZING'
                         AND request_action='replace_ocr_after_analysis'""",
                    (_now(), workspace, document_id, source_sha256),
                )
            else:
                connection.execute(
                    """UPDATE processing_queue SET preflight_status='ANALYZED',
                        error=CASE WHEN hindsight_status IN ('FAILED','OCR_NEEDED','VERIFY')
                                   THEN error ELSE NULL END,
                        revision=revision+1, updated_at=?
                       WHERE workspace=? AND document_id=? AND source_sha256=?
                         AND preflight_status='ANALYZING'""",
                    (_now(), workspace, document_id, source_sha256),
                )
            connection.commit()
            return True

    def consume_ocr_replacement_approval(self, workspace: str, document_id: str) -> None:
        """Consume the one-shot replacement approval before contacting Hindsight."""
        with self._connection() as connection:
            connection.execute(
                """UPDATE processing_queue SET ocr_replace_approved=0,
                    revision=revision+1, updated_at=?
                   WHERE workspace=? AND document_id=? AND ocr_replace_approved=1""",
                (_now(), workspace, document_id),
            )

    def ocr_requests(self) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                """SELECT workspace, document_id, source_path, source_sha256,
                          ocr_requested_at, ocr_status, ocr_filename, ocr_is_revision,
                          ocr_revision_origin_status
                   FROM processing_queue WHERE ocr_status IN ('QUEUED','PROCESSING')
                   ORDER BY priority, workspace, document_id"""
            ).fetchall()
        return [dict(row) for row in rows]

    def set_ocr_status(
        self,
        workspace: str,
        document_id: str,
        *,
        status: str,
        output_filename: str | None = None,
        engine: str | None = None,
        error: str | None = None,
        queue_status: str | None = None,
    ) -> None:
        if status not in {"NONE", "QUEUED", "PROCESSING", "READY", "SUBMITTED", "DONE", "FAILED"}:
            raise ValueError("invalid_ocr_status")
        assignments = ["ocr_status=?", "revision=revision+1", "updated_at=?"]
        values: list[Any] = [status, _now()]
        if output_filename is not None:
            filename = Path(output_filename).name
            if filename != output_filename or not filename.endswith(".md"):
                raise ValueError("ocr_output_filename_must_be_a_markdown_basename")
            assignments.append("ocr_filename=?")
            values.append(filename)
            assignments.append("ocr_output_path=NULL")
            assignments.append("ocr_preflight_source_sha256=NULL")
        if engine is not None:
            assignments.append("ocr_engine=?")
            values.append(engine)
        if error is not None:
            assignments.append("ocr_error=?")
            values.append(error)
        elif status in {"QUEUED", "PROCESSING", "READY", "SUBMITTED", "DONE"}:
            assignments.append("ocr_error=NULL")
            if status == "READY" and queue_status == "OCR_READY":
                # A successful OCR artifact supersedes the original PDF parse error.
                assignments.append("error=NULL")
        if status in {"DONE", "FAILED", "NONE"}:
            assignments.append("ocr_requested_at=NULL")
        if status == "NONE" and output_filename is None:
            assignments.append("ocr_filename=NULL")
            assignments.append("ocr_output_path=NULL")
        if status == "NONE" and engine is None:
            assignments.append("ocr_engine=NULL")
        if status == "DONE":
            assignments.append("ocr_is_revision=0")
            assignments.append("ocr_revision_origin_status=NULL")
        elif status == "NONE":
            assignments.append("ocr_is_revision=0")
            assignments.append("ocr_revision_origin_status=NULL")
        elif status == "FAILED" and queue_status == "MEMORIZED":
            assignments.append("ocr_is_revision=0")
            assignments.append("ocr_revision_origin_status=NULL")
        if queue_status is not None:
            assignments.append("hindsight_status=?")
            values.append(queue_status)
        values.extend((workspace, document_id))
        with self._connection() as connection:
            connection.execute(
                f"UPDATE processing_queue SET {', '.join(assignments)} WHERE workspace=? AND document_id=?",
                values,
            )

    def recover_interrupted_ocr(self) -> None:
        """Make a lost in-memory OCR task retryable after producer restart."""
        with self._connection() as connection:
            connection.execute(
                """UPDATE processing_queue SET ocr_status='QUEUED', hindsight_status='OCR_QUEUED',
                    revision=revision+1, updated_at=? WHERE ocr_status='PROCESSING'""",
                (_now(),),
            )

    def do_not_memorize(self, workspace: str, document_id: str) -> None:
        """Record an explicit, reversible exclusion while keeping the row visible."""
        with self._connection() as connection:
            cursor = connection.execute(
                """UPDATE processing_queue SET user_decision='DO_NOT_SEND',
                    hindsight_status='NOT_MEMORIZED', error='Exclu par l’utilisateur',
                    operation_id=NULL, ocr_status='NONE', ocr_requested_at=NULL,
                    ocr_filename=NULL, ocr_output_path=NULL, ocr_engine=NULL, ocr_error=NULL, ocr_is_revision=0,
                    ocr_revision_origin_status=NULL, ocr_preflight_source_sha256=NULL,
                    revision=revision+1, updated_at=?
                    WHERE workspace=? AND document_id=?
                    AND (
                        hindsight_status IN ('NOT_SENT','FAILED','OCR_NEEDED','OCR_READY','OCR_QUEUED')
                        OR (hindsight_status='QUEUED' AND operation_id IS NULL)
                    )
                    AND operation_id IS NULL
                    AND ocr_status NOT IN ('PROCESSING','SUBMITTED')""",
                (_now(), workspace, document_id),
            )
            if cursor.rowcount == 0:
                row = connection.execute(
                    "SELECT hindsight_status FROM processing_queue WHERE workspace=? AND document_id=?",
                    (workspace, document_id),
                ).fetchone()
                if row is None:
                    raise ValueError("queue_item_not_found")
                raise RuntimeError("queue_item_not_excludable")

    def reinclude(self, workspace: str, document_id: str, *, note: str | None = None) -> None:
        with self._connection() as connection:
            cursor = connection.execute(
                """UPDATE processing_queue SET user_decision='AUTO', preflight_status='TO_PROCESS',
                    request_action='memorize', request_note=?,
                    hindsight_status='NOT_SENT', error=NULL, ocr_status='NONE',
                    ocr_requested_at=NULL, ocr_filename=NULL, ocr_output_path=NULL, ocr_engine=NULL, ocr_error=NULL,
                    ocr_is_revision=0, ocr_revision_origin_status=NULL, ocr_preflight_source_sha256=NULL,
                    revision=revision+1, updated_at=?
                    WHERE workspace=? AND document_id=? AND hindsight_status='NOT_MEMORIZED'""",
                (note, _now(), workspace, document_id),
            )
            if cursor.rowcount == 0:
                row = connection.execute(
                    "SELECT hindsight_status FROM processing_queue WHERE workspace=? AND document_id=?",
                    (workspace, document_id),
                ).fetchone()
                if row is None:
                    raise ValueError("queue_item_not_found")
                raise RuntimeError("queue_item_not_excluded")

    def get_item(self, workspace: str, document_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM processing_queue WHERE workspace=? AND document_id=?",
                (workspace, document_id),
            ).fetchone()
        return dict(row) if row is not None else None

    def get_item_by_path(self, workspace: str, source_path: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM processing_queue WHERE workspace=? AND source_path=?",
                (workspace, source_path),
            ).fetchone()
        return dict(row) if row is not None else None

    def request_verification(self, workspace: str, document_id: str, *, note: str | None = None) -> str:
        """Queue a remote status/read-back check; this never authorizes a retain."""
        requested_at = _now()
        with self._connection() as connection:
            cursor = connection.execute(
                """UPDATE processing_queue SET verification_requested_at=?,
                    request_action='verify', request_note=?,
                    revision=revision+1, updated_at=?
                    WHERE workspace=? AND document_id=? AND hindsight_status='VERIFY'""",
                (requested_at, note, requested_at, workspace, document_id),
            )
            if cursor.rowcount == 0:
                row = connection.execute(
                    "SELECT hindsight_status FROM processing_queue WHERE workspace=? AND document_id=?",
                    (workspace, document_id),
                ).fetchone()
                if row is None:
                    raise ValueError("queue_item_not_found")
                raise RuntimeError("queue_item_not_awaiting_verification")
        return requested_at

    def verification_requests(self) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                """SELECT workspace, document_id, verification_requested_at
                   FROM processing_queue
                   WHERE hindsight_status='VERIFY' AND verification_requested_at IS NOT NULL
                   ORDER BY priority, workspace, document_id"""
            ).fetchall()
        return [dict(row) for row in rows]

    def clear_verification_request(
        self, workspace: str, document_id: str, requested_at: str
    ) -> bool:
        """Clear only the request the worker consumed, preserving newer clicks."""
        with self._connection() as connection:
            cursor = connection.execute(
                """UPDATE processing_queue SET verification_requested_at=NULL,
                    revision=revision+1, updated_at=?
                    WHERE workspace=? AND document_id=? AND verification_requested_at=?""",
                (_now(), workspace, document_id, requested_at),
            )
        return cursor.rowcount == 1
