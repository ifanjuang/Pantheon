"""A7b exact-byte retention adapter for technical document versions.

This is an implementation binding for a caller-selected local/NAS retention
root. Storage Object semantics come from the vendored Pantheon contract; the
physical layout remains replaceable. Retaining bytes does not admit Evidence,
change professional currentness, merge access scopes or adopt a provider.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from . import store, pantheon_contracts
from .documents import file_digest


MIGRATION = Path(__file__).resolve().parent / "sql" / "029_storage_object_retention.sql"
AUTHORITY = {
    "is_evidence": False,
    "is_decision": False,
    "is_approval": False,
    "is_professional_validation": False,
    "changes_project_truth": False,
    "changes_current_authority": False,
    "merges_access_scope": False,
    "adopts_storage_provider": False,
}


class StorageRetentionError(RuntimeError):
    pass


class TechnicalVersionNotFound(StorageRetentionError):
    pass


class SourceContentMismatch(StorageRetentionError):
    pass


class RetainedObjectCorrupt(StorageRetentionError):
    pass


class StorageBindingConflict(StorageRetentionError):
    pass


class RetainedLocationUnavailable(StorageRetentionError):
    pass


def connect(dsn: str | None = None) -> psycopg.Connection:
    conn = store.connect(dsn)
    conn.execute(MIGRATION.read_text(encoding="utf-8"))
    conn.commit()
    return conn


def ensure_schema(conn: psycopg.Connection) -> None:
    conn.execute(MIGRATION.read_text(encoding="utf-8"))
    conn.commit()


def _jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _required(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise StorageRetentionError(f"{field} is required")
    return text


def _technical_version(
    conn: psycopg.Connection,
    *,
    document_id: str,
    version: int,
) -> dict[str, Any]:
    if version < 1:
        raise StorageRetentionError("version must be at least 1")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT document_id, version, source_ref, source_digest,
                   media_type, byte_size, created_at
              FROM document_versions
             WHERE document_id = %s AND version = %s
            """,
            (document_id, version),
        )
        row = cur.fetchone()
    if row is None:
        raise TechnicalVersionNotFound(f"unknown technical document version: {document_id}@{version}")
    return _jsonable(dict(row))


def _object_id(digest: str) -> str:
    # Content-addressed ids are this adapter's choice, not a governance rule.
    return f"storage-object-sha256-{digest}"


def _locator(digest: str) -> str:
    return f"sha256/{digest[:2]}/{digest}"


def _location_id(provider_ref: str, locator: str) -> str:
    raw = f"{provider_ref}\0{locator}".encode("utf-8")
    return f"storage-location-{hashlib.sha256(raw).hexdigest()[:32]}"


def _resolved_destination(root: Path, digest: str) -> tuple[Path, str, Path]:
    root = root.expanduser().resolve()
    if root.exists() and not root.is_dir():
        raise StorageRetentionError("retention_root must be a directory")
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise StorageRetentionError(f"cannot create retention_root: {root}") from exc
    locator = _locator(digest)
    destination = (root / Path(locator)).resolve(strict=False)
    if not destination.is_relative_to(root):
        raise StorageRetentionError("retained destination escaped retention_root")
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise StorageRetentionError(
            f"cannot create retained content directory: {destination.parent}"
        ) from exc
    return destination, locator, root


def _verify_file(path: Path, *, expected_digest: str, expected_size: int) -> None:
    try:
        stat = path.stat()
    except OSError as exc:
        raise RetainedLocationUnavailable(f"cannot stat retained content: {path}") from exc
    if not path.is_file():
        raise RetainedObjectCorrupt(f"retained content is not a regular file: {path}")
    if stat.st_size != expected_size:
        raise RetainedObjectCorrupt(
            f"retained byte size mismatch: expected {expected_size}, found {stat.st_size}"
        )
    try:
        digest = file_digest(path)
    except OSError as exc:
        raise RetainedLocationUnavailable(f"cannot read retained content: {path}") from exc
    if digest.lower() != expected_digest.lower():
        raise RetainedObjectCorrupt(
            f"retained SHA-256 mismatch: expected {expected_digest}, found {digest}"
        )


def _retain_exact_copy(
    source_path: Path,
    *,
    retention_root: Path,
    expected_digest: str,
    expected_size: int,
) -> tuple[Path, str]:
    source_path = source_path.expanduser()
    if not source_path.is_file():
        raise StorageRetentionError(f"source_path is not a readable file: {source_path}")
    try:
        source_size = source_path.stat().st_size
        source_digest = file_digest(source_path)
    except OSError as exc:
        raise StorageRetentionError(f"cannot read source_path: {source_path}") from exc
    if source_size != expected_size or source_digest.lower() != expected_digest.lower():
        raise SourceContentMismatch(
            "source bytes do not match the exact technical document version metadata"
        )

    destination, locator, _ = _resolved_destination(retention_root, expected_digest.lower())
    if destination.exists():
        _verify_file(
            destination,
            expected_digest=expected_digest,
            expected_size=expected_size,
        )
        return destination, locator

    lock_path = destination.with_name(f".{expected_digest}.lock")
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise StorageRetentionError(
            f"retention already in progress for digest {expected_digest}"
        ) from exc
    except OSError as exc:
        raise StorageRetentionError(f"cannot acquire retention lock: {lock_path}") from exc
    else:
        os.close(lock_fd)

    tmp_path: Path | None = None
    try:
        # Another cooperative process might have completed between the first
        # existence check and our lock acquisition. Verify and reuse it.
        if destination.exists():
            _verify_file(
                destination,
                expected_digest=expected_digest,
                expected_size=expected_size,
            )
            return destination, locator

        try:
            fd, tmp_name = tempfile.mkstemp(
                prefix=f".{expected_digest}.",
                suffix=".tmp",
                dir=destination.parent,
            )
            tmp_path = Path(tmp_name)
            with os.fdopen(fd, "wb") as target, source_path.open("rb") as source:
                shutil.copyfileobj(source, target, length=1024 * 1024)
                target.flush()
                os.fsync(target.fileno())
        except OSError as exc:
            raise StorageRetentionError("failed to copy bytes into retention staging") from exc

        _verify_file(
            tmp_path,
            expected_digest=expected_digest,
            expected_size=expected_size,
        )

        # Do not overwrite any content that appeared while we staged. Under the
        # adapter lock this should only be an external writer; verify/fail closed.
        if destination.exists():
            _verify_file(
                destination,
                expected_digest=expected_digest,
                expected_size=expected_size,
            )
        else:
            try:
                os.replace(tmp_path, destination)
            except OSError as exc:
                raise StorageRetentionError("failed to atomically publish retained content") from exc
            tmp_path = None

        _verify_file(
            destination,
            expected_digest=expected_digest,
            expected_size=expected_size,
        )
        return destination, locator
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink()
            except FileNotFoundError:
                pass
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def _storage_object_projection(conn: psycopg.Connection, storage_object_id: str) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT storage_object_id, content_sha256, byte_size, media_type, created_at
              FROM storage_objects
             WHERE storage_object_id = %s
            """,
            (storage_object_id,),
        )
        obj = cur.fetchone()
        if obj is None:
            raise StorageRetentionError(f"unknown Storage Object: {storage_object_id}")
        cur.execute(
            """
            SELECT location_id, storage_provider_ref, locator,
                   retention_guarantee, location_status,
                   verification_method, verified_at
              FROM storage_object_locations
             WHERE storage_object_id = %s
             ORDER BY created_at, location_id
            """,
            (storage_object_id,),
        )
        locations = cur.fetchall()

    payload = {
        "storage_object_id": obj["storage_object_id"],
        "content_sha256": obj["content_sha256"],
        "byte_size": int(obj["byte_size"]),
        "media_type": obj["media_type"],
        "created_at": _jsonable(obj["created_at"]),
        "locations": [
            {
                "location_id": row["location_id"],
                "storage_provider_ref": row["storage_provider_ref"],
                "locator": row["locator"],
                "retention_guarantee": row["retention_guarantee"],
                "location_status": row["location_status"],
                "verification": (
                    {
                        "method": row["verification_method"],
                        "verified_at": _jsonable(row["verified_at"]),
                    }
                    if row["location_status"] == "verified"
                    else None
                ),
                "metadata": {},
            }
            for row in locations
        ],
        "metadata": {},
    }
    return pantheon_contracts.validate("storage_object", payload)


def _register_verified_object(
    conn: psycopg.Connection,
    *,
    digest: str,
    byte_size: int,
    media_type: str | None,
    storage_provider_ref: str,
    locator: str,
) -> dict[str, Any]:
    requested_object_id = _object_id(digest)
    conn.execute(
        """
        INSERT INTO storage_objects (
            storage_object_id, content_sha256, byte_size, media_type
        ) VALUES (%s, %s, %s, %s)
        ON CONFLICT (content_sha256) DO NOTHING
        """,
        (requested_object_id, digest, byte_size, media_type),
    )
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT storage_object_id, byte_size FROM storage_objects
             WHERE content_sha256 = %s
            """,
            (digest,),
        )
        obj = cur.fetchone()
    if obj is None:
        raise StorageRetentionError("Storage Object was not persisted")
    if int(obj["byte_size"]) != byte_size:
        raise StorageBindingConflict(
            "existing Storage Object has incompatible byte size"
        )
    storage_object_id = obj["storage_object_id"]

    location_id = _location_id(storage_provider_ref, locator)
    conn.execute(
        """
        INSERT INTO storage_object_locations (
            location_id, storage_object_id, storage_provider_ref, locator,
            retention_guarantee, location_status,
            verification_method, verified_at
        ) VALUES (%s, %s, %s, %s, 'content_addressed', 'verified', 'full_sha256', clock_timestamp())
        ON CONFLICT (storage_provider_ref, locator) DO NOTHING
        """,
        (location_id, storage_object_id, storage_provider_ref, locator),
    )
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT storage_object_id, location_status, verification_method
              FROM storage_object_locations
             WHERE storage_provider_ref = %s AND locator = %s
            """,
            (storage_provider_ref, locator),
        )
        location = cur.fetchone()
    if (
        location is None
        or location["storage_object_id"] != storage_object_id
        or location["location_status"] != "verified"
        or location["verification_method"] != "full_sha256"
    ):
        raise StorageBindingConflict(
            "existing Storage Object location conflicts with verified binding"
        )
    return _storage_object_projection(conn, storage_object_id)


def retain_exact_bytes(
    conn: psycopg.Connection,
    *,
    content: bytes,
    retention_root: Path,
    storage_provider_ref: str,
    media_type: str | None = None,
    expected_digest: str | None = None,
) -> dict[str, Any]:
    """Retain exact in-memory bytes through the same verified file owner."""

    if not isinstance(content, bytes):
        raise StorageRetentionError("content must be bytes")
    actual_digest = hashlib.sha256(content).hexdigest()
    if expected_digest is not None:
        normalized = str(expected_digest).strip().lower()
        if (
            len(normalized) != 64
            or any(ch not in "0123456789abcdef" for ch in normalized)
        ):
            raise StorageRetentionError(
                "expected_digest must be a lowercase SHA-256 digest"
            )
        if normalized != actual_digest:
            raise SourceContentMismatch(
                "content bytes do not match expected SHA-256"
            )

    fd, tmp_name = tempfile.mkstemp(prefix="pantheon-retain-", suffix=".bin")
    staging = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        return retain_exact_file(
            conn,
            source_path=staging,
            retention_root=retention_root,
            storage_provider_ref=storage_provider_ref,
            media_type=media_type,
            expected_digest=actual_digest,
            expected_size=len(content),
        )
    finally:
        try:
            staging.unlink()
        except FileNotFoundError:
            pass


def retain_exact_file(
    conn: psycopg.Connection,
    *,
    source_path: Path,
    retention_root: Path,
    storage_provider_ref: str,
    media_type: str | None = None,
    expected_digest: str | None = None,
    expected_size: int | None = None,
) -> dict[str, Any]:
    """Retain one exact file without asserting Source, Project or document identity."""

    provider_ref = _required(storage_provider_ref, "storage_provider_ref")
    source_path = source_path.expanduser()
    if not source_path.is_file():
        raise StorageRetentionError(
            f"source_path is not a readable file: {source_path}"
        )
    try:
        actual_size = source_path.stat().st_size
        actual_digest = file_digest(source_path).lower()
    except OSError as exc:
        raise StorageRetentionError(
            f"cannot read source_path: {source_path}"
        ) from exc

    if expected_digest is not None:
        normalized_digest = str(expected_digest).strip().lower()
        if (
            len(normalized_digest) != 64
            or any(ch not in "0123456789abcdef" for ch in normalized_digest)
        ):
            raise StorageRetentionError(
                "expected_digest must be a lowercase SHA-256 digest"
            )
        if actual_digest != normalized_digest:
            raise SourceContentMismatch(
                "source bytes do not match expected SHA-256"
            )
    if expected_size is not None and actual_size != int(expected_size):
        raise SourceContentMismatch(
            "source bytes do not match expected byte size"
        )

    _, locator = _retain_exact_copy(
        source_path,
        retention_root=retention_root,
        expected_digest=actual_digest,
        expected_size=actual_size,
    )
    with conn.transaction():
        storage_object = _register_verified_object(
            conn,
            digest=actual_digest,
            byte_size=actual_size,
            media_type=media_type,
            storage_provider_ref=provider_ref,
            locator=locator,
        )
    return {
        "storage_object": storage_object,
        "authority": dict(AUTHORITY),
        "document_version_binding_created": False,
    }


def retain_document_version(
    conn: psycopg.Connection,
    *,
    document_id: str,
    version: int,
    source_path: Path,
    retention_root: Path,
    storage_provider_ref: str,
) -> dict[str, Any]:
    """Retain and bind exact bytes for one existing technical document version."""
    document_id = _required(document_id, "document_id")
    provider_ref = _required(storage_provider_ref, "storage_provider_ref")
    technical = _technical_version(conn, document_id=document_id, version=version)
    digest = str(technical["source_digest"]).lower()
    expected_size = int(technical["byte_size"])
    requested_object_id = _object_id(digest)

    _, locator = _retain_exact_copy(
        source_path,
        retention_root=retention_root,
        expected_digest=digest,
        expected_size=expected_size,
    )
    with conn.transaction():
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT storage_object_id FROM document_version_storage_bindings
                 WHERE document_id = %s AND version = %s
                """,
                (document_id, version),
            )
            existing_binding = cur.fetchone()
        if (
            existing_binding is not None
            and existing_binding["storage_object_id"] != requested_object_id
        ):
            raise StorageBindingConflict(
                "technical document version is already bound to another Storage Object"
            )

        storage_object = _register_verified_object(
            conn,
            digest=digest,
            byte_size=expected_size,
            media_type=technical["media_type"],
            storage_provider_ref=provider_ref,
            locator=locator,
        )
        storage_object_id = storage_object["storage_object_id"]

        conn.execute(
            """
            INSERT INTO document_version_storage_bindings (
                document_id, version, storage_object_id
            ) VALUES (%s, %s, %s)
            ON CONFLICT (document_id, version) DO NOTHING
            """,
            (document_id, version, storage_object_id),
        )
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT storage_object_id FROM document_version_storage_bindings
                 WHERE document_id = %s AND version = %s
                """,
                (document_id, version),
            )
            binding = cur.fetchone()
        if binding is None or binding["storage_object_id"] != storage_object_id:
            raise StorageBindingConflict(
                "technical document version binding conflicts with retained bytes"
            )

    return {
        "document_id": document_id,
        "version": version,
        "storage_object": storage_object,
        "authority": dict(AUTHORITY),
    }


def resolve_retained_version_path(
    conn: psycopg.Connection,
    *,
    document_id: str,
    version: int,
    retention_root: Path,
    storage_provider_ref: str,
    verify: bool = True,
) -> Path:
    """Resolve one verified local/NAS location for an exact bound version."""
    provider_ref = _required(storage_provider_ref, "storage_provider_ref")
    technical = _technical_version(conn, document_id=document_id, version=version)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT o.content_sha256, o.byte_size, l.locator
              FROM document_version_storage_bindings b
              JOIN storage_objects o ON o.storage_object_id = b.storage_object_id
              JOIN storage_object_locations l ON l.storage_object_id = o.storage_object_id
             WHERE b.document_id = %s AND b.version = %s
               AND l.storage_provider_ref = %s
               AND l.location_status = 'verified'
               AND l.verification_method = 'full_sha256'
             ORDER BY l.location_id
            """,
            (document_id, version, provider_ref),
        )
        rows = cur.fetchall()
    if not rows:
        raise RetainedLocationUnavailable(
            f"no verified retained location for {document_id}@{version} on provider {provider_ref}"
        )
    expected_locator = _locator(str(technical["source_digest"]).lower())
    matching = [row for row in rows if row["locator"] == expected_locator]
    if len(matching) != 1:
        raise StorageBindingConflict("verified retained location is missing or ambiguous")
    row = matching[0]
    if row["content_sha256"].lower() != str(technical["source_digest"]).lower():
        raise StorageBindingConflict(
            "Storage Object digest differs from technical version digest"
        )

    root = retention_root.expanduser().resolve()
    path = (root / Path(row["locator"])).resolve(strict=False)
    if not path.is_relative_to(root):
        raise StorageBindingConflict("retained locator escaped retention_root")
    if verify:
        _verify_file(
            path,
            expected_digest=row["content_sha256"],
            expected_size=int(row["byte_size"]),
        )
    return path


def storage_object_for_document_version(
    conn: psycopg.Connection,
    *,
    document_id: str,
    version: int,
) -> dict[str, Any] | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT storage_object_id
              FROM document_version_storage_bindings
             WHERE document_id = %s AND version = %s
            """,
            (document_id, version),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return _storage_object_projection(conn, row["storage_object_id"])
