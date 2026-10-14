#!/usr/bin/env python3
"""Bounded filesystem workspace -> Hindsight producer used by the Workspace daemon.

The professional source stays on the mounted filesystem. This module only reads an
explicitly projected source file, uploads transient request bytes to Hindsight, and
persists reconstructible/technical synchronization state in SQLite.

Missing sources follow a two-observation lifecycle: the first confirmed absence removes
the document from active recall, and the second deletes the derived Hindsight document.
The mounted professional source is always read-only and is never deleted here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import mimetypes
from pathlib import Path
import re
import sqlite3
from typing import Any
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen
import uuid


ACTIVE_STATUSES = {"SUBMITTED", "PENDING", "PROCESSING"}
TERMINAL_STATUSES = {"COMPLETED", "FAILED", "CANCELLED", "OCR_NEEDED"}
SYNC_TABLE = "hindsight_sync"
IDENTITY_TABLE = "workspace_document_identity"
OBSERVATION_TABLE = "hindsight_source_observation"
QUALITY_TABLE = "hindsight_extraction_quality"
TAG_SAFE_RE = re.compile(r"[^a-z0-9._-]+")


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tag_value(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.strip().casefold())
    without_marks = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    normalized = TAG_SAFE_RE.sub("-", without_marks).strip("-")
    return normalized[:96]


def _project_scope_token(value: str) -> str:
    canonical = unicodedata.normalize("NFKC", value.strip()).casefold()
    slug = _tag_value(value) or "project"
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
    return f"{slug[:80]}-{digest}"


def _metadata_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return None


def _needs_ocr(text: str) -> bool:
    """Detect unusable PDF text without treating ordinary short documents as failures."""
    if not text.strip():
        return True
    cid_markers = text.casefold().count("(cid:")
    if cid_markers >= 3 and cid_markers * 5 >= max(1, len(text) // 20):
        return True
    alphanumeric = sum(character.isalnum() for character in text)
    return len(text) >= 200 and alphanumeric / len(text) < 0.08


def _with_raw_ocr_status(tags: list[str]) -> list[str]:
    """Mark usable native text once, without replacing an OCR result."""
    normalized = {tag for tag in tags if isinstance(tag, str) and tag}
    if normalized.intersection({"ocr:raw", "ocr:partial", "ocr:complete"}):
        return sorted(normalized)
    normalized.add("ocr:raw")
    return sorted(normalized)


def _path_project(relative_path: str) -> str | None:
    parts = Path(relative_path).parts
    return parts[0] if len(parts) > 1 else None


def _same_project(left: str | None, right: str | None) -> bool:
    if left is None or right is None:
        return left is right
    return _tag_value(left) == _tag_value(right)


class ProjectReclassificationRequired(RuntimeError):
    def __init__(self, document_id: str, previous_project: str | None, new_project: str | None) -> None:
        super().__init__("cross-project move requires explicit confirmation")
        self.document_id = document_id
        self.previous_project = previous_project
        self.new_project = new_project


@dataclass(frozen=True)
class ProducerCandidate:
    workspace: str
    document_id: str
    hindsight_document_id: str
    source_path: Path
    relative_path: str
    source_sha256: str
    fingerprint: str
    context: str
    tags: list[str]
    metadata: dict[str, str]


class HindsightHTTPClient:
    """Small Hindsight 0.10.2 HTTP adapter with no third-party dependency."""

    def __init__(
        self,
        base_url: str,
        bank_id: str,
        *,
        authorization: str = "",
        timeout_seconds: float = 30.0,
        parser: str = "markitdown",
        max_file_bytes: int = 100 * 1024 * 1024,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.bank_id = bank_id
        self.authorization = authorization.strip()
        self.timeout_seconds = float(timeout_seconds)
        self.parser = parser.strip() or "markitdown"
        self.max_file_bytes = max(1, int(max_file_bytes))
        parsed = urlparse(self.base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Hindsight URL must be an absolute HTTP(S) URL")

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "User-Agent": "pantheon-workspace-producer/1"}
        if self.authorization:
            headers["Authorization"] = self.authorization
        return headers

    def _json_response(self, request: Request) -> dict[str, Any]:
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read()
        except HTTPError as exc:
            detail = exc.read(4096).decode("utf-8", errors="replace")
            raise RuntimeError(f"Hindsight HTTP {exc.code}: {detail}") from exc
        except (OSError, URLError) as exc:
            raise RuntimeError(f"Hindsight unavailable: {exc}") from exc
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Hindsight returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("Hindsight returned an unexpected response")
        return payload

    def retain_file(
        self,
        source: Path,
        *,
        document_id: str,
        context: str,
        tags: list[str],
        metadata: dict[str, str],
    ) -> str:
        boundary = f"----pantheon-{uuid.uuid4().hex}"
        request_payload = json.dumps(
            {
                "parser": self.parser,
                "files_metadata": [
                    {
                        "context": context,
                        "document_id": document_id,
                        "tags": tags,
                        "metadata": metadata,
                        "timestamp": "unset",
                    }
                ],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        try:
            file_size = source.stat().st_size
        except OSError as exc:
            raise RuntimeError(f"Source unavailable before Hindsight upload: {exc}") from exc
        if file_size > self.max_file_bytes:
            raise RuntimeError(
                f"Source exceeds Hindsight upload bound: {file_size} > {self.max_file_bytes} bytes"
            )
        file_bytes = source.read_bytes()
        content_type = mimetypes.guess_type(source.name)[0] or "application/octet-stream"

        parts = [
            f"--{boundary}\r\n".encode(),
            b'Content-Disposition: form-data; name="request"\r\n',
            b"Content-Type: application/json; charset=utf-8\r\n\r\n",
            request_payload,
            b"\r\n",
            f"--{boundary}\r\n".encode(),
            (
                f'Content-Disposition: form-data; name="files"; filename="{source.name}"\r\n'
            ).encode("utf-8"),
            f"Content-Type: {content_type}\r\n\r\n".encode(),
            file_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
        body = b"".join(parts)
        path = (
            f"/v1/default/banks/{quote(self.bank_id, safe='')}/files/retain"
        )
        headers = self._headers()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        request = Request(f"{self.base_url}{path}", data=body, headers=headers, method="POST")
        payload = self._json_response(request)
        operation_ids = payload.get("operation_ids")
        if (
            not isinstance(operation_ids, list)
            or len(operation_ids) != 1
            or not isinstance(operation_ids[0], str)
            or not operation_ids[0]
        ):
            raise RuntimeError("Hindsight file retain returned no unique operation_id")
        return operation_ids[0]

    def operation_status(self, operation_id: str) -> dict[str, Any]:
        path = (
            f"/v1/default/banks/{quote(self.bank_id, safe='')}/operations/"
            f"{quote(operation_id, safe='')}"
        )
        request = Request(f"{self.base_url}{path}", headers=self._headers(), method="GET")
        payload = self._json_response(request)
        status = payload.get("status")
        if status not in {"pending", "processing", "completed", "failed", "cancelled"}:
            raise RuntimeError(f"Unexpected Hindsight operation status: {status!r}")
        return payload

    def update_document_tags(self, document_id: str, tags: list[str]) -> None:
        body = json.dumps({"tags": tags}, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
        headers = self._headers()
        headers["Content-Type"] = "application/json"
        path = (
            f"/v1/default/banks/{quote(self.bank_id, safe='')}/documents/"
            f"{quote(document_id, safe='')}"
        )
        payload = self._json_response(
            Request(f"{self.base_url}{path}", data=body, headers=headers, method="PATCH")
        )
        if payload.get("success") is not True:
            raise RuntimeError("Hindsight document tag update was not successful")

    def delete_document(self, document_id: str) -> None:
        """Delete one exact derived document; an already absent document is success."""
        path = (
            f"/v1/default/banks/{quote(self.bank_id, safe='')}/documents/"
            f"{quote(document_id, safe='')}"
        )
        request = Request(f"{self.base_url}{path}", headers=self._headers(), method="DELETE")
        try:
            payload = self._json_response(request)
        except RuntimeError as exc:
            if "Hindsight HTTP 404:" in str(exc):
                return
            raise
        if payload.get("success") is not True:
            raise RuntimeError("Hindsight document deletion was not successful")

    def get_document(self, document_id: str) -> dict[str, Any]:
        """Read one exact retained document. This method performs no mutation."""
        path = (
            f"/v1/default/banks/{quote(self.bank_id, safe='')}/documents/"
            f"{quote(document_id, safe='')}"
        )
        request = Request(f"{self.base_url}{path}", headers=self._headers(), method="GET")
        return self._json_response(request)

    def list_document_chunks(
        self,
        document_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Read chunks for one exact retained document, never a bank-wide search."""
        query = urlencode({"limit": max(1, min(int(limit), 100)), "offset": max(0, int(offset))})
        path = (
            f"/v1/default/banks/{quote(self.bank_id, safe='')}/documents/"
            f"{quote(document_id, safe='')}/chunks?{query}"
        )
        request = Request(f"{self.base_url}{path}", headers=self._headers(), method="GET")
        return self._json_response(request)

    def list_memories(
        self,
        document_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Read memory units linked by Hindsight to one exact source document."""
        query = urlencode(
            {
                "document_id": document_id,
                "limit": max(1, min(int(limit), 100)),
                "offset": max(0, int(offset)),
            }
        )
        path = (
            f"/v1/default/banks/{quote(self.bank_id, safe='')}/memories/list?{query}"
        )
        request = Request(f"{self.base_url}{path}", headers=self._headers(), method="GET")
        return self._json_response(request)
class HindsightProducer:
    """One bounded producer owned by the Workspace daemon."""

    def __init__(
        self,
        *,
        roots: list[tuple[str, Path]],
        state_db: Path,
        client: HindsightHTTPClient,
        max_submits_per_reconcile: int = 4,
        settle_observations: int = 1,
        source_kind: str = "",
    ) -> None:
        self.roots = {name: root for name, root in roots}
        self.state_db = state_db
        self.client = client
        self.max_submits_per_reconcile = max(1, int(max_submits_per_reconcile))
        self.settle_observations = max(1, int(settle_observations))
        self.source_kind = _tag_value(source_kind) if source_kind else ""
        self._last_summary: dict[str, Any] = {
            "enabled": True,
            "bank_id": client.bank_id,
            "mode": "source-only",
            "delete_missing": "two-observation-quarantine",
            "ocr_mode": "manual-per-file",
            "submitted": 0,
            "completed": 0,
            "pending": 0,
            "failed": 0,
            "blocked": 0,
            "stale": 0,
            "quarantined": 0,
            "archived": 0,
            "queued": 0,
            "settling": 0,
            "ocr_needed": 0,
            "last_error": None,
        }
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        self.state_db.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.state_db, timeout=5)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        connection = self._connect()
        try:
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {SYNC_TABLE} (
                    hindsight_document_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    workspace TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    source_sha256 TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    operation_id TEXT,
                    status TEXT NOT NULL,
                    last_error TEXT,
                    missing_observations INTEGER NOT NULL DEFAULT 0,
                    tags_json TEXT,
                    updated_at TEXT NOT NULL
                )
                """
            )
            sync_columns = {
                str(row[1])
                for row in connection.execute(f"PRAGMA table_info({SYNC_TABLE})").fetchall()
            }
            if "missing_observations" not in sync_columns:
                connection.execute(
                    f"ALTER TABLE {SYNC_TABLE} "
                    "ADD COLUMN missing_observations INTEGER NOT NULL DEFAULT 0"
                )
            if "tags_json" not in sync_columns:
                connection.execute(f"ALTER TABLE {SYNC_TABLE} ADD COLUMN tags_json TEXT")
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {IDENTITY_TABLE} (
                    document_id TEXT PRIMARY KEY,
                    workspace TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    source_sha256 TEXT NOT NULL,
                    scope_project TEXT,
                    updated_at TEXT NOT NULL
                )
                """
            )
            identity_columns = {
                str(row[1])
                for row in connection.execute(f"PRAGMA table_info({IDENTITY_TABLE})").fetchall()
            }
            if "scope_project" not in identity_columns:
                connection.execute(f"ALTER TABLE {IDENTITY_TABLE} ADD COLUMN scope_project TEXT")
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {OBSERVATION_TABLE} (
                    hindsight_document_id TEXT PRIMARY KEY,
                    fingerprint TEXT NOT NULL,
                    observations INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {QUALITY_TABLE} (
                    hindsight_document_id TEXT PRIMARY KEY,
                    fingerprint TEXT NOT NULL,
                    status TEXT NOT NULL,
                    detail TEXT,
                    checked_at TEXT NOT NULL
                )
                """
            )
            connection.commit()
        finally:
            connection.close()

    def _states(self) -> dict[str, dict[str, Any]]:
        connection = self._connect()
        try:
            rows = connection.execute(f"SELECT * FROM {SYNC_TABLE}").fetchall()
            return {row["hindsight_document_id"]: dict(row) for row in rows}
        finally:
            connection.close()

    def _identity_rows(self) -> list[dict[str, Any]]:
        connection = self._connect()
        try:
            rows = connection.execute(f"SELECT * FROM {IDENTITY_TABLE}").fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def _quality_states(self) -> dict[str, dict[str, Any]]:
        connection = self._connect()
        try:
            rows = connection.execute(f"SELECT * FROM {QUALITY_TABLE}").fetchall()
            return {row["hindsight_document_id"]: dict(row) for row in rows}
        finally:
            connection.close()

    def _save_quality(
        self,
        *,
        hindsight_document_id: str,
        fingerprint: str,
        status: str,
        detail: str | None,
    ) -> None:
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    f"""
                    INSERT INTO {QUALITY_TABLE}(
                        hindsight_document_id, fingerprint, status, detail, checked_at
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(hindsight_document_id) DO UPDATE SET
                        fingerprint=excluded.fingerprint,
                        status=excluded.status,
                        detail=excluded.detail,
                        checked_at=excluded.checked_at
                    """,
                    (hindsight_document_id, fingerprint, status, detail, _utc_now()),
                )
        finally:
            connection.close()

    def _delete_quality(self, hindsight_document_id: str) -> None:
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    f"DELETE FROM {QUALITY_TABLE} WHERE hindsight_document_id = ?",
                    (hindsight_document_id,),
                )
        finally:
            connection.close()

    def _save_identity(
        self,
        *,
        document_id: str,
        workspace: str,
        source_path: str,
        source_sha256: str,
        scope_project: str | None,
    ) -> None:
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    f"""
                    INSERT INTO {IDENTITY_TABLE}(
                        document_id, workspace, source_path, source_sha256, scope_project, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(document_id) DO UPDATE SET
                        workspace=excluded.workspace,
                        source_path=excluded.source_path,
                        source_sha256=excluded.source_sha256,
                        scope_project=excluded.scope_project,
                        updated_at=excluded.updated_at
                    """,
                    (
                        document_id,
                        workspace,
                        source_path,
                        source_sha256,
                        scope_project,
                        _utc_now(),
                    ),
                )
        finally:
            connection.close()

    def _resolve_document_id(
        self,
        *,
        workspace: str,
        relative_path: str,
        source_sha256: str,
        scope_project: str | None,
        declared_document_id: str | None,
        scope_move_confirmed: bool,
        current_paths: set[tuple[str, str]],
        claimed_auto_ids: set[str],
    ) -> tuple[str, str]:
        rows = self._identity_rows()
        if declared_document_id:
            prior = next(
                (row for row in rows if row["document_id"] == declared_document_id),
                None,
            )
            if prior is None:
                prior = next(
                    (
                        row
                        for row in self._states().values()
                        if row["document_id"] == declared_document_id
                    ),
                    None,
                )
            previous_project = (
                prior.get("scope_project") or _path_project(str(prior["source_path"]))
                if prior is not None
                else None
            )
            if (
                prior is not None
                and not _same_project(previous_project, scope_project)
                and not scope_move_confirmed
            ):
                raise ProjectReclassificationRequired(
                    declared_document_id, previous_project, scope_project
                )
            self._save_identity(
                document_id=declared_document_id,
                workspace=workspace,
                source_path=relative_path,
                source_sha256=source_sha256,
                scope_project=scope_project,
            )
            return declared_document_id, "declared"

        exact = next(
            (
                row
                for row in rows
                if row["workspace"] == workspace and row["source_path"] == relative_path
            ),
            None,
        )
        if exact is not None:
            document_id = str(exact["document_id"])
            claimed_auto_ids.add(document_id)
            self._save_identity(
                document_id=document_id,
                workspace=workspace,
                source_path=relative_path,
                source_sha256=source_sha256,
                scope_project=scope_project,
            )
            return document_id, "technical"

        # Upgrade an existing pre-identity-table producer state without changing
        # the Hindsight document id or retaining the same NAS file twice.
        legacy = next(
            (
                row
                for row in self._states().values()
                if row["workspace"] == workspace and row["source_path"] == relative_path
            ),
            None,
        )
        if legacy is not None:
            document_id = str(legacy["document_id"])
            claimed_auto_ids.add(document_id)
            self._save_identity(
                document_id=document_id,
                workspace=workspace,
                source_path=relative_path,
                source_sha256=source_sha256,
                scope_project=scope_project,
            )
            return document_id, "technical"

        move_candidates = [
            row
            for row in rows
            if row["workspace"] == workspace
            and row["source_sha256"] == source_sha256
            and (workspace, row["source_path"]) not in current_paths
            and row["document_id"] not in claimed_auto_ids
        ]
        same_project_moves = [
            row
            for row in move_candidates
            if _same_project(
                row.get("scope_project") or _path_project(str(row["source_path"])),
                scope_project,
            )
        ]
        cross_project_moves = [row for row in move_candidates if row not in same_project_moves]
        if len(same_project_moves) == 0 and len(cross_project_moves) == 1:
            row = cross_project_moves[0]
            raise ProjectReclassificationRequired(
                str(row["document_id"]),
                row.get("scope_project") or _path_project(str(row["source_path"])),
                scope_project,
            )
        document_id = (
            str(same_project_moves[0]["document_id"])
            if len(same_project_moves) == 1
            else f"doc_auto_{uuid.uuid4().hex}"
        )
        claimed_auto_ids.add(document_id)
        self._save_identity(
            document_id=document_id,
            workspace=workspace,
            source_path=relative_path,
            source_sha256=source_sha256,
            scope_project=scope_project,
        )
        return document_id, "technical"

    def _observe_stability(self, candidate: ProducerCandidate) -> bool:
        """Require identical complete bytes/context across consecutive reconciles."""
        if self.settle_observations <= 1:
            return True
        connection = self._connect()
        try:
            row = connection.execute(
                f"SELECT fingerprint, observations FROM {OBSERVATION_TABLE} "
                "WHERE hindsight_document_id = ?",
                (candidate.hindsight_document_id,),
            ).fetchone()
            observations = (
                int(row["observations"]) + 1
                if row is not None and row["fingerprint"] == candidate.fingerprint
                else 1
            )
            with connection:
                connection.execute(
                    f"""
                    INSERT INTO {OBSERVATION_TABLE}(
                        hindsight_document_id, fingerprint, observations, updated_at
                    ) VALUES (?, ?, ?, ?)
                    ON CONFLICT(hindsight_document_id) DO UPDATE SET
                        fingerprint=excluded.fingerprint,
                        observations=excluded.observations,
                        updated_at=excluded.updated_at
                    """,
                    (
                        candidate.hindsight_document_id,
                        candidate.fingerprint,
                        observations,
                        _utc_now(),
                    ),
                )
            return observations >= self.settle_observations
        finally:
            connection.close()
    def _save(
        self,
        candidate: ProducerCandidate | None,
        *,
        hindsight_document_id: str,
        document_id: str,
        workspace: str,
        source_path: str,
        source_sha256: str,
        fingerprint: str,
        operation_id: str | None,
        status: str,
        last_error: str | None = None,
        missing_observations: int = 0,
        tags: list[str] | None = None,
    ) -> None:
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    f"""
                    INSERT INTO {SYNC_TABLE}(
                        hindsight_document_id, document_id, workspace, source_path,
                        source_sha256, fingerprint, operation_id, status, last_error,
                        missing_observations, tags_json, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(hindsight_document_id) DO UPDATE SET
                        document_id=excluded.document_id,
                        workspace=excluded.workspace,
                        source_path=excluded.source_path,
                        source_sha256=excluded.source_sha256,
                        fingerprint=excluded.fingerprint,
                        operation_id=excluded.operation_id,
                        status=excluded.status,
                        last_error=excluded.last_error,
                        missing_observations=excluded.missing_observations,
                        tags_json=COALESCE(excluded.tags_json, {SYNC_TABLE}.tags_json),
                        updated_at=excluded.updated_at
                    """,
                    (
                        hindsight_document_id,
                        document_id,
                        workspace,
                        source_path,
                        source_sha256,
                        fingerprint,
                        operation_id,
                        status,
                        last_error,
                        max(0, int(missing_observations)),
                        json.dumps(
                            tags if tags is not None else candidate.tags,
                            ensure_ascii=False,
                        ) if tags is not None or candidate is not None else None,
                        _utc_now(),
                    ),
                )
        finally:
            connection.close()

    def _candidate(
        self,
        card: dict[str, Any],
        *,
        current_paths: set[tuple[str, str]],
        claimed_auto_ids: set[str],
    ) -> ProducerCandidate | None:
        if card.get("kind") != "document":
            return None
        if card.get("hindsight_eligible") is not True:
            return None
        # The productive route is source-only. A cartouche can enrich context but is
        # no longer an admission gate for an otherwise supported source.
        if card.get("hindsight_representation_candidate") != "source":
            return None

        workspace = card.get("workspace")
        relative_path = card.get("path")
        if not isinstance(workspace, str) or workspace not in self.roots:
            return None
        if not isinstance(relative_path, str) or not relative_path:
            return None

        root = self.roots[workspace]
        source = root / relative_path
        try:
            root_resolved = root.resolve(strict=True)
            source_resolved = source.resolve(strict=True)
            source_resolved.relative_to(root_resolved)
            if not source.is_file() or source.is_symlink():
                return None
        except (OSError, RuntimeError, ValueError):
            return None

        declared_sha = card.get("source_sha256")
        if card.get("source_sha256_verified") is True and isinstance(declared_sha, str):
            source_sha256 = declared_sha
        else:
            source_sha256 = _sha256(source)

        raw_document_id = card.get("document_id")
        declared_document_id = (
            raw_document_id.strip()
            if isinstance(raw_document_id, str) and raw_document_id.strip()
            else None
        )
        scope_project = _metadata_value(card.get("scope_project"))
        document_id, identity_origin = self._resolve_document_id(
            workspace=workspace,
            relative_path=relative_path,
            source_sha256=source_sha256,
            scope_project=scope_project,
            declared_document_id=declared_document_id,
            scope_move_confirmed=card.get("scope_move_confirmed") is True,
            current_paths=current_paths,
            claimed_auto_ids=claimed_auto_ids,
        )
        card["technical_document_id"] = document_id
        card["hindsight_document_id"] = f"{document_id}:source"
        card["identity_origin"] = identity_origin

        metadata: dict[str, str] = {
            "pantheon_document_id": document_id,
            "identity_origin": identity_origin,
            "workspace": workspace,
            "source_path": relative_path,
            "source_sha256": source_sha256,
            "source_space": _tag_value(workspace),
        }
        parent_path = _metadata_value(card.get("parent_path"))
        if parent_path is not None:
            metadata["parent_path"] = parent_path
        folder_ancestry = [
            value.strip()
            for value in (card.get("folder_ancestry") or [])
            if isinstance(value, str) and value.strip()
        ]
        if folder_ancestry:
            metadata["folder_ancestry"] = " / ".join(folder_ancestry)
        identity_source = _metadata_value(card.get("document_identity_source"))
        if identity_source is not None:
            metadata["document_identity_source"] = identity_source
        project_scope_source = _metadata_value(card.get("project_scope_source"))
        if project_scope_source is not None:
            metadata["project_scope_source"] = project_scope_source
        if scope_project is not None:
            metadata["scope_project"] = scope_project
        project_declared = _metadata_value(card.get("project_declared"))
        if project_declared is not None:
            metadata["project_declared"] = project_declared
        if card.get("project_scope_conflict") is True:
            metadata["project_scope_conflict"] = "true"
        document_family_hint = _metadata_value(card.get("document_family_hint"))
        if document_family_hint is not None:
            metadata["document_family_hint"] = document_family_hint
        filename_revision_hint = _metadata_value(card.get("filename_revision_hint"))
        if filename_revision_hint is not None:
            metadata["filename_revision_hint"] = filename_revision_hint
        if self.source_kind:
            metadata["source_kind"] = self.source_kind
        if card.get("cartouche_enrichment_admitted") is True:
            cartouche_path = _metadata_value(card.get("cartouche"))
            if cartouche_path is not None:
                metadata["cartouche_path"] = cartouche_path
            metadata["cartouche_document_id"] = document_id
            for target_key, card_key in (
                ("cartouche_project", "project_declared"),
                ("cartouche_phase", "phase"),
                ("cartouche_document_type", "document_type"),
                ("cartouche_index", "index"),
                ("cartouche_document_date", "document_date"),
                ("cartouche_issuer", "issuer"),
                ("cartouche_revision_mode", "revision_mode"),
                ("cartouche_revision_of", "revision_of"),
            ):
                value = _metadata_value(card.get(card_key))
                if value is not None:
                    metadata[target_key] = value
        for target_key, card_key in (
            ("title", "title"),
            ("project_hint", "project"),
            ("phase_hint", "phase"),
            ("document_type", "document_type"),
            ("issuer", "issuer"),
        ):
            value = _metadata_value(card.get(card_key))
            if value is not None:
                metadata[target_key] = value

        context_parts = [f"{workspace} professional source document"]
        if metadata.get("title"):
            context_parts.append(f"title={metadata['title']}")
        if metadata.get("document_type"):
            context_parts.append(f"type={metadata['document_type']}")
        if metadata.get("phase_hint"):
            context_parts.append(f"phase hint={metadata['phase_hint']}")
        if metadata.get("project_hint"):
            context_parts.append(f"project hint={metadata['project_hint']}")
        if metadata.get("folder_ancestry"):
            context_parts.append(f"folder ancestry={metadata['folder_ancestry']}")
        context = "; ".join(context_parts)

        tags = [f"workspace:{_tag_value(workspace)}"]
        if self.source_kind:
            tags.append(f"source:{self.source_kind}")
        for prefix, value in (
            ("project_hint", metadata.get("project_hint")),
            ("phase_hint", metadata.get("phase_hint")),
        ):
            if value:
                normalized = _tag_value(value)
                if normalized:
                    tags.append(f"{prefix}:{normalized}")
        if metadata.get("scope_project"):
            tags.append(f"scope:project:{_project_scope_token(metadata['scope_project'])}")
        elif metadata.get("project_scope_source") == "pending_identification":
            tags.append("scope:pending-identification")
        if metadata.get("document_family_hint"):
            tags.append(f"family:{_tag_value(metadata['document_family_hint'])}")
        if metadata.get("filename_revision_hint"):
            tags.append(f"revision_hint:{_tag_value(metadata['filename_revision_hint'])}")
        cumulative: list[str] = []
        for folder in folder_ancestry:
            cumulative.append(folder)
            normalized_path = _tag_value("/".join(cumulative))
            if normalized_path:
                tags.append(f"folder:{normalized_path}")
        for value in card.get("tags") or []:
            if isinstance(value, str):
                normalized = _tag_value(value)
                if normalized:
                    tags.append(f"tag:{normalized}")
        tags = list(dict.fromkeys(tags))

        fingerprint_payload = {
            "source_sha256": source_sha256,
            "context": context,
            "metadata": metadata,
            "tags": tags,
        }
        fingerprint = hashlib.sha256(
            json.dumps(
                fingerprint_payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return ProducerCandidate(
            workspace=workspace,
            document_id=document_id,
            hindsight_document_id=f"{document_id}:source",
            source_path=source,
            relative_path=relative_path,
            source_sha256=source_sha256,
            fingerprint=fingerprint,
            context=context,
            tags=tags,
            metadata=metadata,
        )

    def _poll(self, row: dict[str, Any]) -> dict[str, Any]:
        operation_id = row.get("operation_id")
        if not operation_id:
            return row
        try:
            payload = self.client.operation_status(str(operation_id))
        except RuntimeError as exc:
            row["last_error"] = str(exc)
            self._save(
                None,
                hindsight_document_id=row["hindsight_document_id"],
                document_id=row["document_id"],
                workspace=row["workspace"],
                source_path=row["source_path"],
                source_sha256=row["source_sha256"],
                fingerprint=row["fingerprint"],
                operation_id=row.get("operation_id"),
                status=row["status"],
                last_error=row["last_error"],
            )
            return row

        mapped = str(payload["status"]).upper()
        last_error = (
            str(payload.get("error_message"))
            if payload.get("error_message") is not None
            else None
        )
        if (
            mapped == "FAILED"
            and Path(str(row.get("source_path") or "")).suffix.casefold() == ".pdf"
            and last_error is not None
            and any(
                marker in last_error.casefold()
                for marker in ("no content extracted", "no text extracted")
            )
        ):
            mapped = "OCR_NEEDED"
            self._save_quality(
                hindsight_document_id=row["hindsight_document_id"],
                fingerprint=row["fingerprint"],
                status="OCR_NEEDED",
                detail="Aucun texte extrait; OCR manuel proposé.",
            )
        row["status"] = mapped
        row["last_error"] = last_error
        self._save(
            None,
            hindsight_document_id=row["hindsight_document_id"],
            document_id=row["document_id"],
            workspace=row["workspace"],
            source_path=row["source_path"],
            source_sha256=row["source_sha256"],
            fingerprint=row["fingerprint"],
            operation_id=row.get("operation_id"),
            status=mapped,
            last_error=row.get("last_error"),
        )
        return row

    def reconcile(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        states = self._states()
        for key, row in list(states.items()):
            if row.get("status") in ACTIVE_STATUSES:
                states[key] = self._poll(row)

        candidates: dict[str, ProducerCandidate] = {}
        seen_document_ids: set[str] = set()
        current_paths: set[tuple[str, str]] = set()

        for workspace in snapshot.get("workspaces") or []:
            for card in workspace.get("cards") or []:
                if (
                    card.get("kind") == "document"
                    and isinstance(card.get("workspace"), str)
                    and isinstance(card.get("path"), str)
                    and card.get("source_present") is True
                ):
                    current_paths.add((card["workspace"], card["path"]))

        claimed_auto_ids: set[str] = set()
        for workspace in snapshot.get("workspaces") or []:
            for card in workspace.get("cards") or []:
                document_id = card.get("document_id")
                if isinstance(document_id, str) and document_id:
                    seen_document_ids.add(document_id)
                try:
                    candidate = self._candidate(
                        card,
                        current_paths=current_paths,
                        claimed_auto_ids=claimed_auto_ids,
                    )
                except ProjectReclassificationRequired as exc:
                    card["technical_document_id"] = exc.document_id
                    card["hindsight_document_id"] = f"{exc.document_id}:source"
                    card["hindsight_status"] = "RECLASSIFICATION_REQUIRED"
                    card["hindsight_reclassification_required"] = True
                    card["hindsight_previous_project"] = exc.previous_project
                    card["hindsight_requested_project"] = exc.new_project
                    seen_document_ids.add(exc.document_id)
                    candidate = None
                except OSError:
                    candidate = None
                if candidate is not None:
                    seen_document_ids.add(candidate.document_id)
                    candidates[candidate.hindsight_document_id] = candidate

        quality_states = self._quality_states()
        projected_tags = {key: candidate.tags for key, candidate in candidates.items()}
        for key, candidate in candidates.items():
            row = states.get(key)
            previous_quality = quality_states.get(key)
            if candidate.source_path.suffix.casefold() != ".pdf":
                continue
            if (
                row is None
                or row.get("status") != "COMPLETED"
                or row.get("fingerprint") != candidate.fingerprint
            ):
                continue
            if (
                previous_quality
                and previous_quality.get("fingerprint") == candidate.fingerprint
                and previous_quality.get("status") != "CHECK_ERROR"
            ):
                continue
            try:
                retained = self.client.get_document(key)
                original_text = retained.get("original_text")
                text = original_text if isinstance(original_text, str) else ""
                needs_ocr = _needs_ocr(text)
                quality_status = "OCR_NEEDED" if needs_ocr else "GOOD"
                quality_detail = (
                    "Extraction texte illisible ou vide; OCR manuel proposé."
                    if needs_ocr
                    else None
                )
                if not needs_ocr:
                    existing_tags = retained.get("tags")
                    preserved_tags = (
                        existing_tags
                        if isinstance(existing_tags, list)
                        and all(isinstance(tag, str) for tag in existing_tags)
                        else []
                    )
                    updated_tags = _with_raw_ocr_status(projected_tags[key] + preserved_tags)
                    if sorted(set(preserved_tags)) != updated_tags:
                        self.client.update_document_tags(key, updated_tags)
                    projected_tags[key] = updated_tags
            except RuntimeError as exc:
                quality_status = "CHECK_ERROR"
                quality_detail = str(exc)
            self._save_quality(
                hindsight_document_id=key,
                fingerprint=candidate.fingerprint,
                status=quality_status,
                detail=quality_detail,
            )
            quality_states[key] = {
                "hindsight_document_id": key,
                "fingerprint": candidate.fingerprint,
                "status": quality_status,
                "detail": quality_detail,
            }

        submitted = 0
        settling = 0
        last_error: str | None = None

        for key, candidate in candidates.items():
            tags = projected_tags.get(key, candidate.tags)
            row = states.get(key)
            # Active rows were already polled exactly once at the start of this reconcile.
            # Never double-poll an operation in the same pass: a fast PENDING -> COMPLETED
            # transition must not also trigger a replacement submit before the next snapshot.
            if row and row.get("status") in ACTIVE_STATUSES:
                continue

            stable_content_move = bool(
                row
                and row.get("status") == "COMPLETED"
                and row.get("source_sha256") == candidate.source_sha256
                and row.get("source_path") != candidate.relative_path
            )
            if stable_content_move:
                try:
                    self.client.update_document_tags(key, tags)
                except RuntimeError as exc:
                    last_error = str(exc)
                    continue
                self._save(
                    candidate,
                    hindsight_document_id=key,
                    document_id=candidate.document_id,
                    workspace=candidate.workspace,
                    source_path=candidate.relative_path,
                    source_sha256=candidate.source_sha256,
                    fingerprint=candidate.fingerprint,
                    operation_id=row.get("operation_id"),
                    status="COMPLETED",
                    tags=tags,
                )
                row.update(
                    source_path=candidate.relative_path,
                    fingerprint=candidate.fingerprint,
                    last_error=None,
                    tags_json=json.dumps(tags, ensure_ascii=False),
                )
                states[key] = row
                continue

            if row and row.get("fingerprint") == candidate.fingerprint:
                if row.get("status") == "QUARANTINED":
                    try:
                        self.client.update_document_tags(key, tags)
                    except RuntimeError as exc:
                        # A remotely absent document must be retained again. Other
                        # failures are transient and must not risk a duplicate retain.
                        if "404" not in str(exc):
                            last_error = str(exc)
                            continue
                    else:
                        self._save(
                            candidate,
                            hindsight_document_id=key,
                            document_id=candidate.document_id,
                            workspace=candidate.workspace,
                            source_path=candidate.relative_path,
                            source_sha256=candidate.source_sha256,
                            fingerprint=candidate.fingerprint,
                            operation_id=row.get("operation_id"),
                            status="COMPLETED",
                            tags=tags,
                        )
                        row.update(
                            status="COMPLETED",
                            missing_observations=0,
                            last_error=None,
                            tags_json=json.dumps(tags, ensure_ascii=False),
                        )
                        states[key] = row
                        continue
                if row.get("status") in {"COMPLETED", "STALE", "BLOCKED"}:
                    stored_tags = row.get("tags_json")
                    try:
                        tags_match = json.loads(str(stored_tags)) == tags if stored_tags is not None else False
                    except json.JSONDecodeError:
                        tags_match = False
                    if row.get("status") != "COMPLETED" or not tags_match:
                        self._save(
                            candidate,
                            hindsight_document_id=key,
                            document_id=candidate.document_id,
                            workspace=candidate.workspace,
                            source_path=candidate.relative_path,
                            source_sha256=candidate.source_sha256,
                            fingerprint=candidate.fingerprint,
                            operation_id=row.get("operation_id"),
                            status="COMPLETED",
                            tags=tags,
                        )
                        row.update(status="COMPLETED", tags_json=json.dumps(tags, ensure_ascii=False))
                    states[key] = row
                    continue
                if row.get("status") in {"FAILED", "CANCELLED", "OCR_NEEDED"}:
                    continue

            if not self._observe_stability(candidate):
                settling += 1
                continue

            if submitted >= self.max_submits_per_reconcile:
                self._save(
                    candidate,
                    hindsight_document_id=key,
                    document_id=candidate.document_id,
                    workspace=candidate.workspace,
                    source_path=candidate.relative_path,
                    source_sha256=candidate.source_sha256,
                    fingerprint=candidate.fingerprint,
                    operation_id=None,
                    status="QUEUED",
                    tags=tags,
                )
                states[key] = {
                    "hindsight_document_id": key,
                    "document_id": candidate.document_id,
                    "workspace": candidate.workspace,
                    "source_path": candidate.relative_path,
                    "source_sha256": candidate.source_sha256,
                    "fingerprint": candidate.fingerprint,
                    "operation_id": None,
                    "status": "QUEUED",
                    "last_error": None,
                    "tags_json": json.dumps(tags, ensure_ascii=False),
                }
                continue

            try:
                operation_id = self.client.retain_file(
                    candidate.source_path,
                    document_id=candidate.hindsight_document_id,
                    context=candidate.context,
                    tags=tags,
                    metadata=candidate.metadata,
                )
            except (OSError, RuntimeError) as exc:
                last_error = str(exc)
                self._save(
                    candidate,
                    hindsight_document_id=key,
                    document_id=candidate.document_id,
                    workspace=candidate.workspace,
                    source_path=candidate.relative_path,
                    source_sha256=candidate.source_sha256,
                    fingerprint=candidate.fingerprint,
                    operation_id=None,
                    status="SUBMIT_ERROR",
                    last_error=last_error,
                    tags=tags,
                )
                states[key] = {
                    "hindsight_document_id": key,
                    "document_id": candidate.document_id,
                    "workspace": candidate.workspace,
                    "source_path": candidate.relative_path,
                    "source_sha256": candidate.source_sha256,
                    "fingerprint": candidate.fingerprint,
                    "operation_id": None,
                    "status": "SUBMIT_ERROR",
                    "last_error": last_error,
                    "tags_json": json.dumps(tags, ensure_ascii=False),
                }
                continue

            submitted += 1
            self._save(
                candidate,
                hindsight_document_id=key,
                document_id=candidate.document_id,
                workspace=candidate.workspace,
                source_path=candidate.relative_path,
                source_sha256=candidate.source_sha256,
                fingerprint=candidate.fingerprint,
                operation_id=operation_id,
                status="SUBMITTED",
                tags=tags,
            )
            states[key] = {
                "hindsight_document_id": key,
                "document_id": candidate.document_id,
                "workspace": candidate.workspace,
                "source_path": candidate.relative_path,
                "source_sha256": candidate.source_sha256,
                "fingerprint": candidate.fingerprint,
                "operation_id": operation_id,
                "status": "SUBMITTED",
                "last_error": None,
                "tags_json": json.dumps(tags, ensure_ascii=False),
            }

        available_workspaces = {
            str(workspace.get("name"))
            for workspace in snapshot.get("workspaces") or []
            if workspace.get("available") is True
        }
        historical_by_workspace: dict[str, int] = {}
        missing_by_workspace: dict[str, int] = {}
        for key, row in states.items():
            workspace = str(row.get("workspace") or "")
            if row.get("status") != "ARCHIVED":
                historical_by_workspace[workspace] = historical_by_workspace.get(workspace, 0) + 1
            if (
                key not in candidates
                and row.get("status") != "ARCHIVED"
                and row.get("status") not in ACTIVE_STATUSES
                and row.get("document_id") not in seen_document_ids
            ):
                missing_by_workspace[workspace] = missing_by_workspace.get(workspace, 0) + 1

        for key, row in list(states.items()):
            if key in candidates or row.get("status") in ACTIVE_STATUSES:
                continue
            if row.get("document_id") in seen_document_ids:
                desired = "BLOCKED"
                if row.get("status") != desired:
                    self._save(
                        None,
                        hindsight_document_id=key,
                        document_id=row["document_id"],
                        workspace=row["workspace"],
                        source_path=row["source_path"],
                        source_sha256=row["source_sha256"],
                        fingerprint=row["fingerprint"],
                        operation_id=row.get("operation_id"),
                        status=desired,
                        last_error=row.get("last_error"),
                    )
                    row["status"] = desired
                continue

            workspace = str(row.get("workspace") or "")
            if workspace not in available_workspaces or row.get("status") == "ARCHIVED":
                continue

            historical = historical_by_workspace.get(workspace, 0)
            missing = missing_by_workspace.get(workspace, 0)
            if historical >= 20 and missing >= 20 and missing * 4 > historical:
                last_error = (
                    f"Mass-disappearance safety blocked lifecycle for {workspace}: "
                    f"{missing}/{historical} sources absent"
                )
                continue

            observations = int(row.get("missing_observations") or 0) + 1
            if observations == 1:
                try:
                    self.client.update_document_tags(
                        key,
                        [
                            "lifecycle:quarantined",
                            f"workspace:{_tag_value(workspace)}",
                            "reason:source-missing",
                        ],
                    )
                except RuntimeError as exc:
                    if "404" not in str(exc):
                        last_error = str(exc)
                        continue
                self._save(
                    None,
                    hindsight_document_id=key,
                    document_id=row["document_id"],
                    workspace=row["workspace"],
                    source_path=row["source_path"],
                    source_sha256=row["source_sha256"],
                    fingerprint=row["fingerprint"],
                    operation_id=row.get("operation_id"),
                    status="QUARANTINED",
                    missing_observations=observations,
                )
                row.update(status="QUARANTINED", missing_observations=observations)
            else:
                try:
                    self.client.delete_document(key)
                except RuntimeError as exc:
                    last_error = str(exc)
                    continue
                self._delete_quality(key)
                self._save(
                    None,
                    hindsight_document_id=key,
                    document_id=row["document_id"],
                    workspace=row["workspace"],
                    source_path=row["source_path"],
                    source_sha256=row["source_sha256"],
                    fingerprint=row["fingerprint"],
                    operation_id=None,
                    status="ARCHIVED",
                    missing_observations=observations,
                )
                row.update(status="ARCHIVED", missing_observations=observations)

        states = self._states()
        quality_states = self._quality_states()
        state_by_path = {
            (row.get("workspace"), row.get("source_path")): row
            for row in states.values()
        }
        for workspace in snapshot.get("workspaces") or []:
            for card in workspace.get("cards") or []:
                if card.get("kind") != "document":
                    continue
                row = state_by_path.get((card.get("workspace"), card.get("path")))
                if row is None:
                    if card.get("hindsight_reclassification_required") is True:
                        continue
                    card["hindsight_status"] = (
                        "NOT_ELIGIBLE"
                        if card.get("hindsight_eligible") is not True
                        else "NOT_RETAINED"
                    )
                    continue
                try:
                    raw_projected_tags = row.get("tags_json")
                    projected_tags = (
                        json.loads(str(raw_projected_tags))
                        if raw_projected_tags is not None
                        else None
                    )
                except (TypeError, json.JSONDecodeError):
                    projected_tags = None
                card["hindsight_tags_projected"] = (
                    [tag for tag in projected_tags if isinstance(tag, str)]
                    if isinstance(projected_tags, list) else None
                )
                card["hindsight_tags_projection_state"] = (
                    "LOCAL_PRODUCER_STATE"
                    if row.get("status") == "COMPLETED" and isinstance(projected_tags, list)
                    else "LOCAL_PRODUCER_INTENT" if isinstance(projected_tags, list) else "UNKNOWN_LEGACY_STATE"
                )
                card["technical_document_id"] = row.get("document_id")
                card["hindsight_document_id"] = row.get("hindsight_document_id")
                card["hindsight_status"] = row.get("status")
                card["hindsight_last_error"] = row.get("last_error")
                quality = quality_states.get(str(row.get("hindsight_document_id")))
                card["hindsight_extraction_quality"] = (
                    quality.get("status") if quality is not None else "NOT_CHECKED"
                )
                card["hindsight_ocr_needed"] = (
                    quality is not None and quality.get("status") == "OCR_NEEDED"
                )
                card["hindsight_ocr_mode"] = "manual-per-file"

        counts = {
            "submitted": 0,
            "completed": 0,
            "pending": 0,
            "failed": 0,
            "blocked": 0,
            "stale": 0,
            "quarantined": 0,
            "archived": 0,
            "queued": 0,
            "settling": settling,
            "ocr_needed": sum(
                1 for row in quality_states.values() if row.get("status") == "OCR_NEEDED"
            ),
        }
        for row in states.values():
            status = row.get("status")
            if status == "SUBMITTED":
                counts["submitted"] += 1
            elif status in {"PENDING", "PROCESSING"}:
                counts["pending"] += 1
            elif status == "COMPLETED":
                counts["completed"] += 1
            elif status in {"FAILED", "CANCELLED", "SUBMIT_ERROR"}:
                counts["failed"] += 1
            elif status == "BLOCKED":
                counts["blocked"] += 1
            elif status == "STALE":
                counts["stale"] += 1
            elif status == "QUARANTINED":
                counts["quarantined"] += 1
            elif status == "ARCHIVED":
                counts["archived"] += 1
            elif status == "QUEUED":
                counts["queued"] += 1

        self._last_summary = {
            "enabled": True,
            "bank_id": self.client.bank_id,
            "mode": "source-only",
            "delete_missing": "two-observation-quarantine",
            "ocr_mode": "manual-per-file",
            **counts,
            "last_error": last_error,
            "last_reconcile_at": _utc_now(),
        }
        return dict(self._last_summary)

    def health(self) -> dict[str, Any]:
        return dict(self._last_summary)
