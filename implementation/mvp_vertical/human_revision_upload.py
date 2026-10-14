"""B2 contextual human revision-upload orchestration.

This module composes existing owners. It does not create a second Source owner,
parser, technical document store, Storage Object model or professional revision
model. Durable stages remain truthful when a later stage fails.
"""

from __future__ import annotations

import hashlib
import mimetypes
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO

import psycopg
import yaml
from psycopg.rows import dict_row

from . import (
    human_access,
    project_document_admission,
    project_documents,
    source_intake,
    storage_retention,
    store,
)
from .contract import TaskContract, load_contract
from .documents import DocumentConversionError, DocumentConverter, file_digest

DEFAULT_MAX_BYTES = 100 * 1024 * 1024
_SUFFIX = re.compile(r"^\.[A-Za-z0-9]{1,12}$")


class RevisionUploadError(RuntimeError):
    pass


class RevisionUploadConfigurationError(RevisionUploadError):
    pass


class RevisionUploadRejected(RevisionUploadError):
    pass


class RevisionUploadConflict(RevisionUploadError):
    pass


@dataclass(frozen=True)
class RevisionUploadConfig:
    source_root: Path
    retention_root: Path
    retention_provider_ref: str
    max_bytes: int = DEFAULT_MAX_BYTES

    @classmethod
    def from_env_optional(cls) -> "RevisionUploadConfig | None":
        source_root = os.getenv("MVP_HUMAN_SOURCE_ROOT", "").strip()
        retention_root = os.getenv("MVP_RETENTION_ROOT", "").strip()
        provider_ref = os.getenv("MVP_RETENTION_PROVIDER_REF", "").strip()
        configured = [bool(source_root), bool(retention_root), bool(provider_ref)]
        if not any(configured):
            return None
        if not all(configured):
            raise RevisionUploadConfigurationError(
                "MVP_HUMAN_SOURCE_ROOT, MVP_RETENTION_ROOT and MVP_RETENTION_PROVIDER_REF must be configured together"
            )
        raw_limit = os.getenv("MVP_HUMAN_UPLOAD_MAX_BYTES", str(DEFAULT_MAX_BYTES)).strip()
        try:
            max_bytes = int(raw_limit)
        except ValueError as exc:
            raise RevisionUploadConfigurationError(
                "MVP_HUMAN_UPLOAD_MAX_BYTES must be an integer"
            ) from exc
        if max_bytes < 1:
            raise RevisionUploadConfigurationError(
                "MVP_HUMAN_UPLOAD_MAX_BYTES must be positive"
            )
        return cls(
            source_root=Path(source_root),
            retention_root=Path(retention_root),
            retention_provider_ref=provider_ref,
            max_bytes=max_bytes,
        )


def ensure_schema(conn: psycopg.Connection) -> None:
    source_intake.initialize(conn)
    project_document_admission.ensure_schema(conn)
    storage_retention.ensure_schema(conn)
    human_access.ensure_schema(conn)


def _safe_suffix(filename: str | None) -> str:
    suffix = Path(filename or "").suffix
    if _SUFFIX.fullmatch(suffix):
        return suffix.lower()
    return ".bin"


def _upload_identity(
    *,
    principal_ref: str,
    project_id: str,
    document_id: str,
    idempotency_key: str,
) -> str:
    material = "\0".join((principal_ref, project_id, document_id, idempotency_key))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _source_id(identity: str) -> str:
    return f"human-upload-{identity[:40]}"


def _contract_id(identity: str) -> str:
    return f"upload.{identity[:40]}"


def _verify_exact(path: Path, *, digest: str, size: int) -> None:
    if not path.is_file() or path.stat().st_size != size or file_digest(path) != digest:
        raise RevisionUploadConflict("preserved upload bytes do not match their exact digest")


def _publish_stream(
    stream: BinaryIO,
    *,
    original_filename: str | None,
    source_root: Path,
    max_bytes: int,
) -> tuple[Path, str, str, int]:
    if max_bytes < 1:
        raise RevisionUploadConfigurationError("max_bytes must be positive")
    root = source_root.expanduser().resolve()
    if root.exists() and not root.is_dir():
        raise RevisionUploadConfigurationError("source_root must be a directory")
    root.mkdir(parents=True, exist_ok=True)
    staging = root / ".staging"
    staging.mkdir(parents=True, exist_ok=True)

    digest = hashlib.sha256()
    size = 0
    temp_path: Path | None = None
    lock_path: Path | None = None
    lock_fd: int | None = None
    try:
        fd, temp_name = tempfile.mkstemp(prefix="upload-", suffix=".tmp", dir=staging)
        temp_path = Path(temp_name)
        with os.fdopen(fd, "wb") as target:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                if not isinstance(chunk, (bytes, bytearray)):
                    raise RevisionUploadRejected("uploaded stream did not yield bytes")
                size += len(chunk)
                if size > max_bytes:
                    raise RevisionUploadRejected(
                        f"upload exceeds maximum allowed size of {max_bytes} bytes"
                    )
                digest.update(chunk)
                target.write(chunk)
            target.flush()
            os.fsync(target.fileno())
        if size == 0:
            raise RevisionUploadRejected("empty upload is not accepted")

        hexdigest = digest.hexdigest()
        suffix = _safe_suffix(original_filename)
        source_ref = f"human_uploads/sha256/{hexdigest[:2]}/{hexdigest}/source{suffix}"
        destination = (root / source_ref).resolve(strict=False)
        if not destination.is_relative_to(root):
            raise RevisionUploadRejected("generated upload destination escaped source_root")
        destination.parent.mkdir(parents=True, exist_ok=True)

        lock_path = destination.parent / f".{hexdigest}.upload.lock"
        try:
            lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise RevisionUploadConflict(
                f"another upload publication is in progress for digest {hexdigest}"
            ) from exc
        finally:
            if lock_fd is not None:
                os.close(lock_fd)
                lock_fd = None

        if destination.exists():
            _verify_exact(destination, digest=hexdigest, size=size)
        else:
            os.replace(temp_path, destination)
            temp_path = None
            _verify_exact(destination, digest=hexdigest, size=size)
        return destination, source_ref, hexdigest, size
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass
        if lock_path is not None:
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass


def _write_contract(
    *,
    config: RevisionUploadConfig,
    identity: str,
    principal_ref: str,
    project_id: str,
    source_ref: str,
    original_filename: str | None,
) -> TaskContract:
    contract_id = _contract_id(identity)
    payload = {
        "object_type": "task_contract",
        "object_id": contract_id,
        "contract_id": contract_id,
        "status": "active",
        "requested_by": principal_ref,
        "exposure_surface": "human_oidc_revision_upload",
        "approval_ceiling": "technical_access_only",
        "intent": {"summary": "Contextual Project Document revision upload"},
        "scope": {
            "dossier": project_id,
            "parent_project_id": project_id,
            "declared_sources": [
                {
                    "source_ref": source_ref,
                    "title": original_filename or "uploaded document",
                    "traceable": True,
                }
            ],
        },
        "expected_outputs": ["technical_document_capture"],
        "forbidden_scope": [
            "project_scope_expansion",
            "professional_approval",
            "external_send",
        ],
    }
    contracts_root = config.source_root.expanduser().resolve() / ".contracts"
    contracts_root.mkdir(parents=True, exist_ok=True)
    path = contracts_root / f"{_source_id(identity)}.yaml"
    encoded = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    if path.exists():
        if path.read_text(encoding="utf-8") != encoded:
            raise RevisionUploadConflict(
                "idempotent upload contract identity already belongs to different metadata"
            )
    else:
        path.write_text(encoded, encoding="utf-8")
        with path.open("rb") as handle:
            os.fsync(handle.fileno())
    return load_contract(path)


def _technical_capture(
    conn: psycopg.Connection,
    *,
    project_id: str,
    source_ref: str,
    expected_digest: str,
) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT document_id, dossier, parent_project_id, source_ref,
                   source_digest, media_type, byte_size, analysis_status,
                   current_extraction_id
              FROM source_documents
             WHERE dossier = %s AND source_ref = %s
            """,
            (project_id, source_ref),
        )
        document = cur.fetchone()
    if document is None:
        raise RevisionUploadError("technical ingestion did not create a source document capture")
    if document["parent_project_id"] != project_id:
        raise RevisionUploadConflict("technical capture escaped the requested Project scope")
    if str(document["source_digest"]).lower() != expected_digest.lower():
        raise RevisionUploadConflict("technical capture digest differs from preserved upload")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT version, source_digest, media_type, byte_size, created_at
              FROM document_versions
             WHERE document_id = %s AND source_digest = %s
            """,
            (document["document_id"], expected_digest),
        )
        version = cur.fetchone()
    if version is None:
        raise RevisionUploadError("technical ingestion did not retain an exact document version")
    return {
        "document_id": document["document_id"],
        "version": int(version["version"]),
        "source_digest": str(version["source_digest"]),
        "media_type": version["media_type"],
        "byte_size": int(version["byte_size"]),
        "analysis_status": document["analysis_status"],
        "current_extraction_id": document["current_extraction_id"],
    }


def _received_at_for_replay(conn: psycopg.Connection, source_id: str) -> str | datetime:
    try:
        return source_intake.get_source(conn, source_id)["received_at"]
    except source_intake.SourceNotFound:
        return datetime.now(timezone.utc)


def upload_revision(
    conn: psycopg.Connection,
    *,
    principal_ref: str,
    project_id: str,
    document_id: str,
    stream: BinaryIO,
    original_filename: str | None,
    idempotency_key: str,
    config: RevisionUploadConfig,
    revision_label: str | None = None,
    supersedes_version_id: str | None = None,
    docling: DocumentConverter | None = None,
) -> dict[str, Any]:
    """Compose transport -> Source -> technical capture -> A7 -> A2.

    Filesystem and database stages are intentionally not presented as one
    transaction. If analysis fails after preservation, the preserved Source and
    exact technical capture remain truthful and may be reviewed/retried.
    """
    principal_ref = str(principal_ref or "").strip()
    project_id = str(project_id or "").strip()
    document_id = str(document_id or "").strip()
    idempotency_key = str(idempotency_key or "").strip()
    if not all((principal_ref, project_id, document_id, idempotency_key)):
        raise RevisionUploadRejected(
            "principal_ref, project_id, document_id and idempotency_key are required"
        )

    with conn.transaction():
        human_access.require_access(
            conn,
            principal_ref=principal_ref,
            project_id=project_id,
            resource_type="project",
            resource_id=project_id,
            action="project.read",
        )
        human_access.require_access(
            conn,
            principal_ref=principal_ref,
            project_id=project_id,
            resource_type="project_document",
            resource_id=document_id,
            action="document.read",
        )
        human_access.require_access(
            conn,
            principal_ref=principal_ref,
            project_id=project_id,
            resource_type="project_document",
            resource_id=document_id,
            action="document.revision.submit",
        )
        document = project_documents.get_document(conn, document_id)
        if document["parent_project_id"] != project_id:
            raise human_access.AccessDenied(
                "Project Document is outside the requested Project scope"
            )

    identity = _upload_identity(
        principal_ref=principal_ref,
        project_id=project_id,
        document_id=document_id,
        idempotency_key=idempotency_key,
    )
    preserved_path, source_ref, digest, byte_size = _publish_stream(
        stream,
        original_filename=original_filename,
        source_root=config.source_root,
        max_bytes=config.max_bytes,
    )
    media_type = mimetypes.guess_type(original_filename or preserved_path.name)[0]

    source_id = _source_id(identity)
    with conn.transaction():
        received_at = _received_at_for_replay(conn, source_id)
        source = source_intake.create_source(
            conn,
            source_id=source_id,
            source_kind="document",
            origin_system="human_oidc_upload",
            origin_external_ref=f"human-upload:{source_id}",
            origin_producer=principal_ref,
            received_by=principal_ref,
            raw_source_ref=source_ref,
            received_at=received_at,
            actor=principal_ref,
            actor_kind="human",
            idempotency_key=f"{idempotency_key}:source",
            mime_type=media_type,
            checksum=digest,
            metadata={
                "original_filename": original_filename,
                "target_document_id": document_id,
                "declared_revision_label": revision_label,
                "declared_supersedes_version_id": supersedes_version_id,
                "transport": "human_oidc_revision_upload",
                "byte_size": byte_size,
            },
        )
        source = source_intake.link_project(
            conn,
            source_id=source_id,
            project_id=project_id,
            expected_revision=int(source["revision"]),
            actor=principal_ref,
            actor_kind="human",
            idempotency_key=f"{idempotency_key}:project",
        )

    contract = _write_contract(
        config=config,
        identity=identity,
        principal_ref=principal_ref,
        project_id=project_id,
        source_ref=source_ref,
        original_filename=original_filename,
    )

    analysis_error: str | None = None
    try:
        store.ingest(
            conn,
            contract,
            config.source_root,
            ingestion_id=f"human-upload-{identity[:32]}",
            docling=docling,
            source_refs=(source_ref,),
        )
    except DocumentConversionError as exc:
        # The existing store records exact failed technical capture first.
        analysis_error = str(exc)

    technical = _technical_capture(
        conn,
        project_id=project_id,
        source_ref=source_ref,
        expected_digest=digest,
    )
    conn.commit()

    try:
        retained = storage_retention.retain_document_version(
            conn,
            document_id=technical["document_id"],
            version=technical["version"],
            source_path=preserved_path,
            retention_root=config.retention_root,
            storage_provider_ref=config.retention_provider_ref,
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    # Re-check after potentially long conversion/retention. Revoked access can
    # stop professional admission without erasing already-truthful intake stages.
    with conn.transaction():
        human_access.require_access(
            conn,
            principal_ref=principal_ref,
            project_id=project_id,
            resource_type="project",
            resource_id=project_id,
            action="project.read",
        )
        human_access.require_access(
            conn,
            principal_ref=principal_ref,
            project_id=project_id,
            resource_type="project_document",
            resource_id=document_id,
            action="document.read",
        )
        human_access.require_access(
            conn,
            principal_ref=principal_ref,
            project_id=project_id,
            resource_type="project_document",
            resource_id=document_id,
            action="document.revision.submit",
        )
        admission = project_document_admission.admit_source_as_revision(
            conn,
            source_id=source_id,
            document_id=document_id,
            source_document_id=technical["document_id"],
            source_version=technical["version"],
            revision_label=revision_label,
            supersedes_version_id=supersedes_version_id,
            actor=principal_ref,
            actor_kind="human",
            idempotency_key=f"{idempotency_key}:admission",
        )

    storage_object = retained["storage_object"]
    return {
        "source": {
            "source_id": source_id,
            "project_id": source["project_id"],
            "checksum": digest,
            "byte_size": byte_size,
        },
        "technical_capture": {
            **technical,
            "analysis_error": analysis_error,
        },
        "retention": {
            "storage_object_id": storage_object["storage_object_id"],
            "verified": any(
                location.get("location_status") == "verified"
                for location in storage_object.get("locations", [])
            ),
        },
        "revision": admission["revision"],
        "duplicate_content_reused": admission["duplicate_content_reused"],
        "authority": {
            "source_preserved": True,
            "technical_capture_persisted": True,
            "bytes_retained": True,
            "revision_persisted": True,
            "is_evidence": False,
            "is_approval": False,
            "is_professional_validation": False,
            "changes_current_authority": False,
        },
    }
