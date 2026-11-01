#!/usr/bin/env python3
"""Bounded filesystem workspace -> Hindsight producer used by the Workspace daemon.

The professional source stays on the mounted filesystem. This module only reads an
explicitly projected source file, uploads transient request bytes to Hindsight, and
persists reconstructible/technical synchronization state in SQLite.

Missing sources are only eligible for lifecycle changes after a complete workspace scan.
The first confirmed absence quarantines the derived Hindsight document; deletion waits
through a grace period. The mounted professional source is always read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from concurrent.futures import Future, ThreadPoolExecutor
import hashlib
import io
import json
import logging
import mimetypes
from pathlib import Path
import re
import sqlite3
import threading
import time
from typing import Any, Mapping, Sequence
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen
import uuid
import zipfile

from document_metadata_preflight import (
    PreflightResult,
    _read_pdf_creation_date,
    preflight_ocr_markdown,
    preflight_pdf_metadata,
)
from document_ocr import OcrResult, PdfOcr
from processing_queue import ProcessingQueue


ACTIVE_STATUSES = {"SUBMITTING", "SUBMITTED", "PENDING", "PROCESSING", "VERIFYING"}
TERMINAL_STATUSES = {"COMPLETED", "FAILED", "CANCELLED", "OCR_NEEDED"}
SUBMISSION_RECOVERY_GRACE_SECONDS = 300
MISSING_SOURCE_GRACE_SECONDS = 24 * 60 * 60
SYNC_TABLE = "hindsight_sync"
IDENTITY_TABLE = "workspace_document_identity"
OBSERVATION_TABLE = "hindsight_source_observation"
QUALITY_TABLE = "hindsight_extraction_quality"
PREFLIGHT_TABLE = "hindsight_metadata_preflight"
PREFLIGHT_SOURCE_TABLE = "hindsight_metadata_preflight_source"
DOCUMENT_NOTES_TABLE = "workspace_document_notes"
DOCUMENT_METADATA_OVERRIDES_TABLE = "workspace_document_metadata_overrides"
PROJECT_OVERVIEW_TABLE = "hindsight_project_overview"
SOURCE_HASH_CACHE_TABLE = "workspace_source_hash_cache"
PREFLIGHT_CACHE_VERSION = "10"
TAG_SAFE_RE = re.compile(r"[^a-z0-9._-]+")
LOGGER = logging.getLogger(__name__)


class SourceChangedDuringPreflight(RuntimeError):
    """A preflight result must not be attached to a different source version."""


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _submission_outcome_uncertain(error: str) -> bool:
    """Conservatively distinguish rejected HTTP requests from ambiguous outcomes."""
    # Content inspection fails before any network request, so never enter VERIFY.
    if error.startswith("Source format"):
        return False
    if any(
        marker in error.casefold()
        for marker in (
            "source unavailable before hindsight upload",
            "source changed before hindsight upload",
            "source exceeds hindsight upload bound",
        )
    ):
        return False
    match = re.search(r"Hindsight HTTP (\d{3}):", error)
    if match is None:
        if any(
            marker in error.casefold()
            for marker in (
                "connection refused",
                "name or service not known",
                "temporary failure in name resolution",
                "no route to host",
                "network is unreachable",
            )
        ):
            return False
        return True
    status = int(match.group(1))
    return status in {408, 409, 425, 429} or status >= 500


def _hindsight_connection_unavailable(error: str) -> bool:
    """Identify a refused/unreachable Hindsight endpoint before advancing the lane."""
    message = error.casefold()
    return message.startswith("hindsight unavailable:") and any(
        marker in message
        for marker in (
            "connection refused",
            "name or service not known",
            "temporary failure in name resolution",
            "no route to host",
            "network is unreachable",
        )
    )


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
    preflight_loaded: bool = True


def _source_upload_format(data: bytes, filename: str) -> tuple[str, str, str]:
    """Choose a parser filename from bounded content inspection, never rename a source.

    This identifies a container, not its validity, extractability or professional type.
    No archive member is extracted and no OCR/model is invoked here.
    """
    if not data:
        raise RuntimeError("Source format: empty file; nothing to extract")
    declared = Path(filename).suffix.casefold()
    sample = data[:65536]
    detected = ""
    mime = ""
    if data[:1024].lstrip().startswith(b"%PDF-"):
        detected, mime = ".pdf", "application/pdf"
    elif data.startswith(b"PK\x03\x04"):
        # Bound ZIP directory parsing before allocating a ZipInfo per entry.
        end = data.rfind(b"PK\x05\x06", max(0, len(data) - 65557))
        if end < 0 or end + 22 > len(data):
            raise RuntimeError("Source format: incomplete ZIP/Office container")
        count = int.from_bytes(data[end + 10:end + 12], "little")
        directory_bytes = int.from_bytes(data[end + 12:end + 16], "little")
        if count > 4096 or directory_bytes > 2 * 1024 * 1024:
            raise RuntimeError("Source format: ZIP directory exceeds inspection bound")
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                names = set(archive.namelist())
                matches = [(ext, kind) for marker, ext, kind in (
                    ("word/document.xml", ".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
                    ("xl/workbook.xml", ".xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                    ("ppt/presentation.xml", ".pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
                    ("META-INF/container.xml", ".epub", "application/epub+zip"),
                ) if marker in names]
        except (zipfile.BadZipFile, OSError, ValueError) as exc:
            raise RuntimeError("Source format: unreadable ZIP/Office container") from exc
        if len(matches) != 1:
            raise RuntimeError("Source format: ZIP container unrecognized or ambiguous; extraction route required")
        detected, mime = matches[0]
        # Macro-enabled Office needs a specific route; never disguise it as DOCX/XLSX.
        if any(name.casefold().endswith("vbaproject.bin") for name in names):
            raise RuntimeError("Source format: macro-enabled Office container requires an explicit extraction route")
    elif data.startswith(bytes.fromhex("d0cf11e0a1b11ae1")):
        if declared not in {".xls", ".msg"}:
            raise RuntimeError("Source format: legacy OLE container; exact document format unresolved")
        detected = declared
        mime = "application/vnd.ms-excel" if declared == ".xls" else "application/vnd.ms-outlook"
    elif data.startswith((b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"GIF87a", b"GIF89a", b"II*\x00", b"MM\x00*")):
        raise RuntimeError("Source format: image content; an image OCR/vision extraction route is required")
    elif sample.lstrip().startswith(b"{\\rtf"):
        raise RuntimeError("Source format: RTF content; an RTF extraction route is required")
    else:
        try:
            # Ignore an incomplete final UTF-8 codepoint at the sample boundary only.
            import codecs
            encoding = "utf-16" if sample.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
            text = codecs.getincrementaldecoder(encoding)().decode(sample, final=len(data) <= len(sample))
        except UnicodeDecodeError as exc:
            if declared not in {".txt", ".md", ".markdown", ".csv", ".tsv", ".html", ".htm", ".xml"}:
                raise RuntimeError("Source format not identified: binary content or unsupported encoding; check original file") from exc
            try:
                text = sample.decode("cp1252", errors="strict")
            except UnicodeDecodeError as legacy_exc:
                raise RuntimeError("Source format not identified: unsupported text encoding") from legacy_exc
        if not text.strip() or any(ord(c) < 32 and c not in "\r\n\t\f" for c in text):
            raise RuntimeError("Source format not identified: non-text content; check original file")
        lead = text.lstrip().casefold()
        if lead.startswith(("<!doctype html", "<html", "<head", "<body")):
            detected, mime = ".html", "text/html"
        else:
            # Text structure such as CSV/Markdown is not inferred from prose.
            detected = declared if declared in {".txt", ".md", ".markdown", ".csv", ".tsv", ".json", ".xml"} else ".txt"
            mime = mimetypes.guess_type("document" + detected)[0] or "text/plain"
    upload_name = Path(filename).name
    if Path(upload_name).suffix.casefold() != detected:
        upload_name = Path(upload_name).stem + detected
    # A source filename may contain quotes/newlines, but multipart headers must not.
    upload_name = upload_name.replace('"', "_").replace("\r", "_").replace("\n", "_")
    return upload_name, mime, detected.removeprefix(".")


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
        expected_source_sha256: str | None = None,
    ) -> str:
        return self.retain_files_batch([{
            "source": source,
            "document_id": document_id,
            "context": context,
            "tags": tags,
            "metadata": metadata,
            "expected_source_sha256": expected_source_sha256,
        }])[0]

    def retain_files_batch(self, files: Sequence[Mapping[str, Any]]) -> list[str]:
        """Submit several distinct documents in one durable Hindsight file operation."""
        return self.submit_prepared_files(self.prepare_retain_files_batch(files))

    def prepare_retain_files_batch(
        self, files: Sequence[Mapping[str, Any]]
    ) -> list[dict[str, Any]]:
        """Validate and buffer a batch before the durable SUBMITTING intent is written."""
        if not files or len(files) > 10:
            raise ValueError("Hindsight file batches must contain between 1 and 10 files")
        prepared: list[dict[str, Any]] = []
        total_bytes = 0
        for item in files:
            source = Path(item["source"])
            try:
                file_size = source.stat().st_size
            except OSError as exc:
                raise RuntimeError(f"Source unavailable before Hindsight upload: {exc}") from exc
            if file_size > self.max_file_bytes:
                raise RuntimeError(
                    f"Source exceeds Hindsight upload bound: {file_size} > {self.max_file_bytes} bytes"
                )
            try:
                with source.open("rb") as source_handle:
                    file_bytes = source_handle.read(self.max_file_bytes + 1)
            except OSError as exc:
                raise RuntimeError(f"Source unavailable before Hindsight upload: {exc}") from exc
            if len(file_bytes) > self.max_file_bytes:
                raise RuntimeError(
                    f"Source exceeds Hindsight upload bound: more than {self.max_file_bytes} bytes"
                )
            total_bytes += len(file_bytes)
            if total_bytes > 100 * 1024 * 1024:
                raise RuntimeError("Hindsight file batch exceeds 104857600 bytes")
            actual_sha256 = hashlib.sha256(file_bytes).hexdigest()
            expected_sha256 = item.get("expected_source_sha256")
            if expected_sha256 and actual_sha256 != expected_sha256:
                raise RuntimeError("Source changed before Hindsight upload; re-scan required")
            upload_name, content_type, detected_format = _source_upload_format(file_bytes, source.name)
            metadata = dict(item.get("metadata") or {})
            metadata["source_detected_format"] = detected_format
            if upload_name != source.name:
                metadata["extraction_filename"] = upload_name
            prepared.append({
                "file_bytes": file_bytes,
                "upload_name": upload_name,
                "content_type": content_type,
                "document_id": str(item["document_id"]),
                "context": str(item.get("context") or ""),
                "tags": list(item.get("tags") or []),
                "metadata": metadata,
            })
        return prepared

    def submit_prepared_files(self, prepared: Sequence[Mapping[str, Any]]) -> list[str]:
        """POST a previously validated payload so callers can persist intent first."""
        if not prepared or len(prepared) > 10:
            raise ValueError("Hindsight file batches must contain between 1 and 10 files")
        boundary = f"----pantheon-{uuid.uuid4().hex}"
        request_payload = json.dumps(
            {
                "parser": self.parser,
                "files_metadata": [
                    {
                        "context": item["context"],
                        "document_id": item["document_id"],
                        "tags": item["tags"],
                        "metadata": item["metadata"],
                        "timestamp": "unset",
                    }
                    for item in prepared
                ],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

        parts = [
            f"--{boundary}\r\n".encode(),
            b'Content-Disposition: form-data; name="request"\r\n',
            b"Content-Type: application/json; charset=utf-8\r\n\r\n",
            request_payload,
            b"\r\n",
        ]
        for item in prepared:
            parts.extend([
                f"--{boundary}\r\n".encode(),
                (f'Content-Disposition: form-data; name="files"; filename="{item["upload_name"]}"\r\n').encode("utf-8"),
                f"Content-Type: {item['content_type']}\r\n\r\n".encode(),
                item["file_bytes"],
                b"\r\n",
            ])
        parts.append(f"--{boundary}--\r\n".encode())
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
            or len(operation_ids) != len(prepared)
            or any(not isinstance(value, str) or not value for value in operation_ids)
            or len(set(operation_ids)) != len(operation_ids)
        ):
            raise RuntimeError("Hindsight file retain returned an unexpected operation_ids list")
        return operation_ids

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

    def service_health(self) -> dict[str, Any]:
        """Read the service-wide health endpoint, independent of document jobs."""
        request = Request(f"{self.base_url}/health", headers=self._headers(), method="GET")
        payload = self._json_response(request)
        if payload.get("status") != "healthy":
            raise RuntimeError(f"Hindsight service is not healthy: {payload.get('status')!r}")
        return payload

    def list_file_retain_operations(self, *, limit: int = 100) -> list[dict[str, Any]]:
        """List recent file-retain operations for crash recovery by document ID."""
        query = urlencode({"type": "file_convert_retain", "limit": max(1, min(int(limit), 100))})
        path = f"/v1/default/banks/{quote(self.bank_id, safe='')}/operations?{query}"
        request = Request(f"{self.base_url}{path}", headers=self._headers(), method="GET")
        payload = self._json_response(request)
        operations = payload.get("operations")
        if not isinstance(operations, list):
            raise RuntimeError("Hindsight operation list returned an unexpected response")
        return [operation for operation in operations if isinstance(operation, dict)]

    def knowledge_base_tree(self, scope_tag: str) -> list[dict[str, Any]]:
        """List only pages whose memory scope exactly matches one project tag."""
        query = urlencode({"tags": scope_tag, "tags_match": "all_strict"})
        path = (
            f"/v1/default/banks/{quote(self.bank_id, safe='')}/knowledge-base/tree?{query}"
        )
        payload = self._json_response(
            Request(f"{self.base_url}{path}", headers=self._headers(), method="GET")
        )
        roots = payload.get("roots")
        if not isinstance(roots, list):
            raise RuntimeError("Hindsight knowledge-page tree returned an unexpected response")
        pages: list[dict[str, Any]] = []
        pending = list(roots)
        while pending:
            node = pending.pop()
            if not isinstance(node, dict):
                continue
            tags = node.get("tags")
            if node.get("kind") == "page" and isinstance(tags, list) and scope_tag in tags:
                pages.append(node)
            children = node.get("children")
            if isinstance(children, list):
                pending.extend(children)
        return pages

    def has_project_observations(self, scope_tag: str) -> bool:
        """Avoid creating an empty page until this exact project has consolidated knowledge."""
        offset = 0
        while True:
            path = (
                f"/v1/default/banks/{quote(self.bank_id, safe='')}/observations/scopes?"
                + urlencode({"limit": 1000, "offset": offset})
            )
            payload = self._json_response(
                Request(f"{self.base_url}{path}", headers=self._headers(), method="GET")
            )
            scopes = payload.get("scopes")
            total = payload.get("total")
            if not isinstance(scopes, list) or not isinstance(total, int):
                raise RuntimeError("Hindsight observation scopes returned an unexpected response")
            if any(
                isinstance(scope, dict)
                and isinstance(scope.get("tags"), list)
                and scope_tag in scope["tags"]
                and isinstance(scope.get("count"), int)
                and scope["count"] > 0
                for scope in scopes
            ):
                return True
            offset += len(scopes)
            if not scopes or offset >= total:
                return False

    def create_knowledge_page(
        self, *, name: str, source_query: str, scope_tag: str, max_tokens: int = 1400
    ) -> dict[str, Any]:
        body = json.dumps(
            {
                "name": name,
                "source_query": source_query,
                "tags": [scope_tag],
                "max_tokens": max_tokens,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        headers = self._headers()
        headers["Content-Type"] = "application/json"
        path = f"/v1/default/banks/{quote(self.bank_id, safe='')}/knowledge-base/pages"
        payload = self._json_response(
            Request(f"{self.base_url}{path}", data=body, headers=headers, method="POST")
        )
        page_id = payload.get("page_id")
        operation_id = payload.get("operation_id")
        if not isinstance(page_id, str) or not page_id.startswith("kp-"):
            raise RuntimeError("Hindsight knowledge-page create returned no valid page_id")
        if operation_id is not None and not isinstance(operation_id, str):
            raise RuntimeError("Hindsight knowledge-page create returned an invalid operation_id")
        return {"page_id": page_id, "operation_id": operation_id}

    def update_knowledge_page_prompt(self, page_id: str, source_query: str) -> dict[str, Any]:
        body = json.dumps({"source_query": source_query}, ensure_ascii=False).encode("utf-8")
        headers = self._headers()
        headers["Content-Type"] = "application/json"
        path = (
            f"/v1/default/banks/{quote(self.bank_id, safe='')}/knowledge-base/pages/"
            f"{quote(page_id, safe='')}"
        )
        payload = self._json_response(
            Request(f"{self.base_url}{path}", data=body, headers=headers, method="PATCH")
        )
        operation_id = payload.get("operation_id")
        if operation_id is not None and not isinstance(operation_id, str):
            raise RuntimeError("Hindsight knowledge-page update returned an invalid operation_id")
        return {"operation_id": operation_id}

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
        client: HindsightHTTPClient | None = None,
        clients: Mapping[str, HindsightHTTPClient] | None = None,
        max_submits_per_reconcile: int = 4,
        max_active_hindsight_operations: int = 3,
        settle_observations: int = 1,
        source_kind: str = "",
        source_kinds: Mapping[str, str] | None = None,
        metadata_profiles: Mapping[str, str] | None = None,
        project_overview_prompts: Mapping[str, str] | None = None,
        processing_queue_db: Path | None = None,
        ocr_processor: PdfOcr | None = None,
        missing_source_grace_seconds: float = MISSING_SOURCE_GRACE_SECONDS,
    ) -> None:
        self.roots = {name: root for name, root in roots}
        self.state_db = state_db
        self.clients = dict(clients or {})
        if client is not None:
            self.client = client
        elif self.clients:
            self.client = next(iter(self.clients.values()))
        else:
            raise ValueError("a default Hindsight client or per-workspace clients are required")
        if self.clients and set(self.clients) != set(self.roots):
            raise ValueError("per-workspace Hindsight clients must match configured roots")
        self.max_submits_per_reconcile = max(1, int(max_submits_per_reconcile))
        self.max_active_hindsight_operations = max(1, min(3, int(max_active_hindsight_operations)))
        self.settle_observations = max(1, int(settle_observations))
        self.missing_source_grace_seconds = max(0.0, float(missing_source_grace_seconds))
        self.source_kind = _tag_value(source_kind) if source_kind else ""
        self.source_kinds = {
            name: _tag_value(value) if value else self.source_kind
            for name, value in (source_kinds or {}).items()
        }
        self.source_kinds.update({name: self.source_kind for name in self.roots if name not in self.source_kinds})
        self.metadata_profiles = {
            name: str(value).strip().casefold()
            for name, value in (metadata_profiles or {}).items()
        }
        if set(self.metadata_profiles) - set(self.roots) or any(
            value not in {"affaires", "bibliotheque"} for value in self.metadata_profiles.values()
        ):
            raise ValueError("metadata profiles must be affaires/bibliotheque and match configured roots")
        self.project_overview_prompts = {
            name: str(prompt).strip()
            for name, prompt in (project_overview_prompts or {}).items()
            if isinstance(prompt, str) and prompt.strip()
        }
        if set(self.project_overview_prompts) - set(self.roots):
            raise ValueError("project overview prompts must match configured roots")
        self.processing_queue = (
            ProcessingQueue(processing_queue_db) if processing_queue_db is not None else None
        )
        self._operation_poll_lock = threading.Lock()
        self._submission_dispatch_lock = threading.Lock()
        self._submission_cache_lock = threading.Lock()
        self._submission_candidates: dict[str, ProducerCandidate] = {}
        self._submission_inflight: set[str] = set()
        self._submission_dispatcher_stop = threading.Event()
        self._submission_dispatcher_wake = threading.Event()
        self._submission_dispatcher_thread: threading.Thread | None = None
        self._submission_dispatcher_last_error: str | None = None
        self._status_poller_stop = threading.Event()
        self._status_poller_thread: threading.Thread | None = None
        self._status_poller_interval_seconds = 30.0
        self._status_poller_last_error: str | None = None
        self._hindsight_health_error: str | None = None
        self.ocr_processor = ocr_processor
        self._ocr_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="workspace-ocr") if ocr_processor else None
        self._ocr_futures: dict[tuple[str, str], Future[OcrResult]] = {}
        self._ocr_waiting_source: dict[tuple[str, str], tuple[str, float, int]] = {}
        self._last_summary: dict[str, Any] = {
            "enabled": True,
            "bank_ids": {
                name: item.bank_id for name, item in self.clients.items()
            } if self.clients else {name: self.client.bank_id for name in self.roots},
            "mode": "source-only",
            "delete_missing": "complete-scan-quarantine-then-grace",
            "missing_source_grace_seconds": self.missing_source_grace_seconds,
            "ocr_mode": "manual-per-file",
            "submitted": 0,
            "completed": 0,
            "pending": 0,
            "failed": 0,
            "unavailable": 0,
            "blocked": 0,
            "stale": 0,
            "quarantined": 0,
            "archived": 0,
            "queued": 0,
            "settling": 0,
            "ocr_needed": 0,
            "last_error": None,
        }
        self._source_hash_cache_lock = threading.Lock()
        self._source_hash_cache: dict[tuple[str, str], tuple[tuple[int, int, int, int], str]] = {}
        self._ensure_schema()
        self._load_source_hash_cache()
        if self.processing_queue is not None:
            self.processing_queue.recover_interrupted_preflight()
            self.processing_queue.recover_interrupted_ocr()
            self.processing_queue.recover_interrupted_hindsight_metadata_sync()
            # A changed/missing source can be transient on a network mount. Keep
            # bounded retry state in memory instead of suppressing the same digest
            # until the next daemon restart.
            self._preflight_waiting_source: dict[tuple[str, str], tuple[str, float, int]] = {}
            self._preflight_health_lock = threading.Lock()
            self._preflight_last_error: str | None = None
            self._preflight_last_error_at: str | None = None
            self._preflight_last_success_at: str | None = None
            self._preflight_active_document: dict[str, str] | None = None
            self._preflight_last_heartbeat = 0.0
            self._preflight_health_warning_at = 0.0
            self.on_work_available = None
            self._preflight_stop = threading.Event()
            self._preflight_thread = threading.Thread(
                target=self._preflight_worker_loop,
                name="workspace-preflight-queue",
                daemon=True,
            )
            self._preflight_thread.start()
            self._metadata_tag_sync_stop = threading.Event()
            self._metadata_tag_sync_thread = threading.Thread(
                target=self._metadata_sync_worker_loop,
                name="workspace-metadata-sync",
                daemon=True,
            )
            self._metadata_tag_sync_thread.start()
        else:
            self._preflight_stop = None
            self._preflight_thread = None
            self._metadata_tag_sync_stop = None
            self._metadata_tag_sync_thread = None

    def _client_for(self, workspace: str) -> HindsightHTTPClient:
        if self.clients:
            try:
                return self.clients[workspace]
            except KeyError as exc:
                raise ValueError(f"no Hindsight client configured for vault {workspace}") from exc
        return self.client

    @staticmethod
    def _metadata_sync_tags(current: list[str], values: dict[str, Any]) -> list[str]:
        managed_prefixes = []
        for field, prefix in (
            ("family", "family:"), ("document_type", "document_type:"),
            ("corps_etat", "corps_etat:"), ("sujet_technique", "sujet_technique:"),
        ):
            if field in values:
                managed_prefixes.append(prefix)
        tags = [tag for tag in current if not tag.startswith(tuple(managed_prefixes))] if managed_prefixes else list(current)
        fields = (
            ("family", "family"),
            ("document_type", "document_type"),
        )
        for field, prefix in fields:
            value = values.get(field)
            if isinstance(value, str) and value.strip():
                token = _tag_value(value)
                if token:
                    tags.append(f"{prefix}:{token}")
        for field, prefix in (("corps_etat", "corps_etat"), ("sujet_technique", "sujet_technique")):
            entries = values.get(field)
            if isinstance(entries, list):
                for value in entries:
                    if isinstance(value, str) and value.strip():
                        token = _tag_value(value)
                        if token:
                            tags.append(f"{prefix}:{token}")
        return sorted(set(tags))

    def _metadata_sync_worker_loop(self) -> None:
        assert self.processing_queue is not None
        while self._metadata_tag_sync_stop is not None and not self._metadata_tag_sync_stop.is_set():
            try:
                self._complete_submitted_metadata_syncs()
                request = self.processing_queue.claim_hindsight_metadata_sync()
                if request is not None:
                    self._execute_metadata_sync(request)
            except Exception:
                LOGGER.exception("Hindsight metadata synchronization worker failed")
            self._metadata_tag_sync_stop.wait(1.0)

    def _complete_submitted_metadata_syncs(self) -> None:
        assert self.processing_queue is not None
        states = self._states()
        for request in self.processing_queue.pending_hindsight_metadata_sync_submissions():
            state = states.get(str(request["hindsight_document_id"]))
            if state is None:
                self.processing_queue.finish_submitted_hindsight_metadata_sync(
                    str(request["request_id"]), status="FAILED", error="Hindsight sync state disappeared"
                )
            elif state.get("status") == "COMPLETED":
                self.processing_queue.finish_submitted_hindsight_metadata_sync(
                    str(request["request_id"]), status="COMPLETED"
                )
            elif state.get("status") in {"FAILED", "CANCELLED", "OCR_NEEDED", "SUBMIT_ERROR"}:
                self.processing_queue.finish_submitted_hindsight_metadata_sync(
                    str(request["request_id"]), status="FAILED",
                    error=str(state.get("last_error") or state.get("status"))[:1200],
                )
            elif state.get("status") in {"VERIFY", "BLOCKED"}:
                self.processing_queue.finish_submitted_hindsight_metadata_sync(
                    str(request["request_id"]), status="FAILED",
                    error="Issue de réingestion incertaine; vérifiez Hindsight avant toute nouvelle tentative.",
                )

    def _execute_metadata_sync(self, request: dict[str, Any]) -> None:
        assert self.processing_queue is not None
        request_id = str(request["request_id"])
        workspace = str(request["workspace"])
        document_id = str(request["document_id"])
        hindsight_document_id = str(request["hindsight_document_id"])
        try:
            if workspace not in self.roots:
                raise RuntimeError("Vault no longer configured")
            values = json.loads(str(request["values_json"]))
            if not isinstance(values, dict):
                raise RuntimeError("Saved metadata is invalid")
            mode = str(request.get("mode") or "tags")
            state = self._states().get(hindsight_document_id)
            queued = self.processing_queue.get_item(workspace, document_id)
            ocr_review_only = (
                mode == "tags"
                and queued is not None
                and queued.get("hindsight_status") == "VERIFY"
                and "Hindsight document already exists; OCR replacement requires operator review"
                in str(queued.get("error") or "")
                and str(queued.get("ocr_status") or "").upper() in {"READY", "SUBMITTED"}
                and queued.get("ocr_preflight_source_sha256") == request.get("source_sha256")
                and queued.get("user_decision") != "DO_NOT_SEND"
                and state is not None
                and state.get("status") == "SUBMIT_ERROR"
                and state.get("last_error") == "Hindsight document already exists; OCR replacement requires operator review"
                and not state.get("operation_id")
            )
            if (
                state is None
                or state.get("workspace") != workspace
                or state.get("document_id") != document_id
                or state.get("source_path") != request.get("source_path")
                or state.get("source_sha256") != request.get("source_sha256")
                or (state.get("status") != "COMPLETED" and not ocr_review_only)
                or state.get("operation_id")
            ):
                raise RuntimeError("Document identity or completed Hindsight state changed; refresh the card")
            if (
                queued is None
                or queued.get("source_path") != request.get("source_path")
                or queued.get("source_sha256") != request.get("source_sha256")
                or (queued.get("hindsight_status") != "MEMORIZED" and not ocr_review_only)
            ):
                raise RuntimeError("Document is no longer ready for metadata synchronization")
            root = self.roots[workspace].resolve(strict=True)
            unresolved_source = root / str(request["source_path"])
            if unresolved_source.is_symlink():
                raise RuntimeError("Source path is a symbolic link; synchronization refused")
            source = unresolved_source.resolve(strict=True)
            source.relative_to(root)
            if not source.is_file() or source.is_symlink() or _sha256(source) != request["source_sha256"]:
                raise RuntimeError("Source file changed or disappeared; refresh the document first")
            states = self._states()
            if any(
                row.get("status") in ACTIVE_STATUSES
                for key, row in states.items()
                if key != hindsight_document_id
            ):
                # Keep the request pending until the shared single-operation lane is free.
                self.processing_queue.finish_hindsight_metadata_sync(request_id, status="FAILED", error="Hindsight is processing another document; retry when the queue is idle")
                return
            client = self._client_for(workspace)
            remote = client.get_document(hindsight_document_id)
            if remote.get("id") != hindsight_document_id:
                raise RuntimeError("Hindsight returned a different document identity")
            old_tags = remote.get("tags")
            if not isinstance(old_tags, list) or any(not isinstance(tag, str) for tag in old_tags):
                raise RuntimeError("Hindsight document tags could not be read safely")
            tags = self._metadata_sync_tags(old_tags, values)
            if mode == "tags":
                tag_values = {key: value for key, value in values.items() if key in {"family", "document_type", "corps_etat", "sujet_technique"}}
                if not tag_values:
                    raise RuntimeError("No classification tags were saved for this document")
                client.update_document_tags(hindsight_document_id, tags)
                verified = client.get_document(hindsight_document_id)
                verified_tags = verified.get("tags")
                if (
                    verified.get("id") != hindsight_document_id
                    or not isinstance(verified_tags, list)
                    or any(not isinstance(tag, str) for tag in verified_tags)
                    or sorted(set(verified_tags)) != tags
                ):
                    raise RuntimeError("Hindsight tag update read-back did not match")
                self._save(
                    None, hindsight_document_id=hindsight_document_id, document_id=document_id,
                    workspace=workspace, source_path=str(request["source_path"]),
                    source_sha256=str(request["source_sha256"]), fingerprint=str(state["fingerprint"]),
                    operation_id=None, status="COMPLETED", tags=tags,
                )
                if ocr_review_only:
                    self.processing_queue.set_status(
                        workspace, document_id, preflight_status="ANALYZED",
                        hindsight_status="MEMORIZED", operation_id=None, clear_error=True,
                    )
                self.processing_queue.finish_hindsight_metadata_sync(request_id, status="COMPLETED")
                return
            if mode != "reingest":
                raise RuntimeError("Unknown metadata synchronization mode")
            existing_metadata = remote.get("document_metadata", remote.get("metadata"))
            if not isinstance(existing_metadata, dict) or any(not isinstance(k, str) for k in existing_metadata):
                raise RuntimeError("Hindsight document metadata could not be preserved safely")
            retain_params = remote.get("retain_params")
            existing_context = (
                retain_params.get("context") if isinstance(retain_params, dict) else remote.get("context")
            )
            if not isinstance(existing_context, str):
                raise RuntimeError("Hindsight document context could not be preserved safely")
            metadata = {str(key): str(value) for key, value in existing_metadata.items() if value is not None}
            metadata_keys = {
                "title": "title",
                "document_date": "document_date",
                "index": "document_indice",
                "issuer": "document_emetteur",
                "recipient": "document_destinataire",
                "family": "document_family",
                "document_type": "document_type",
                "summary": "document_summary",
            }
            for field, key in metadata_keys.items():
                if field in values and values[field] is None:
                    metadata.pop(key, None)
                    continue
                value = values.get(field)
                if isinstance(value, str) and value.strip():
                    metadata[key] = value.strip()
            for field, key in (("corps_etat", "corps_etat"), ("sujet_technique", "sujets_techniques")):
                if field in values and values[field] is None:
                    metadata.pop(key, None)
                    continue
                value = values.get(field)
                if isinstance(value, list):
                    cleaned = [item.strip() for item in value if isinstance(item, str) and item.strip()]
                    if cleaned:
                        metadata[key] = ", ".join(cleaned)
            context_marker = "User-confirmed Cockpit metadata: "
            context_base = existing_context.split(context_marker, 1)[0].rstrip("; ")
            context_items = [
                f"{metadata_keys[field]}={values[field].strip()}"
                for field in metadata_keys
                if isinstance(values.get(field), str) and values[field].strip()
            ]
            for field, meta_key in (("corps_etat", "corps_etat"), ("sujet_technique", "sujets_techniques")):
                value = values.get(field)
                if isinstance(value, list):
                    entries = [item.strip() for item in value if isinstance(item, str) and item.strip()]
                    if entries:
                        context_items.append(f"{field}={', '.join(entries)}")
            context = "; ".join(filter(None, (context_base, context_marker + "; ".join(context_items))))
            self._save(
                None, hindsight_document_id=hindsight_document_id, document_id=document_id,
                workspace=workspace, source_path=str(request["source_path"]),
                source_sha256=str(request["source_sha256"]), fingerprint=str(state["fingerprint"]),
                operation_id=None, status="SUBMITTING", tags=tags,
            )
            self.processing_queue.set_status(
                workspace, document_id, preflight_status="ANALYZED",
                hindsight_status="MEMORIZING", operation_id=None, clear_error=True,
            )
            try:
                operation_id = client.retain_file(
                    source, document_id=hindsight_document_id, context=context, tags=tags,
                    metadata=metadata, expected_source_sha256=str(request["source_sha256"]),
                )
            except RuntimeError as exc:
                if _submission_outcome_uncertain(str(exc)):
                    # Reconcile recovers the exact operation by this stable document ID.
                    self.processing_queue.finish_hindsight_metadata_sync(request_id, status="SUBMITTED")
                else:
                    self._save(
                        None, hindsight_document_id=hindsight_document_id, document_id=document_id,
                        workspace=workspace, source_path=str(request["source_path"]),
                        source_sha256=str(request["source_sha256"]), fingerprint=str(state["fingerprint"]),
                        operation_id=None, status="COMPLETED", tags=old_tags,
                    )
                    self.processing_queue.set_status(
                        workspace, document_id, preflight_status="ANALYZED",
                        hindsight_status="MEMORIZED", operation_id=None, clear_error=True,
                    )
                    raise
                return
            self._save(
                None, hindsight_document_id=hindsight_document_id, document_id=document_id,
                workspace=workspace, source_path=str(request["source_path"]),
                source_sha256=str(request["source_sha256"]), fingerprint=str(state["fingerprint"]),
                operation_id=operation_id, status="SUBMITTED", tags=tags,
            )
            self.processing_queue.set_status(
                workspace, document_id, preflight_status="ANALYZED",
                hindsight_status="MEMORIZING", operation_id=operation_id, clear_error=True,
            )
            self.processing_queue.finish_hindsight_metadata_sync(request_id, status="SUBMITTED")
        except (OSError, RuntimeError, ValueError, TypeError, json.JSONDecodeError) as exc:
            self.processing_queue.finish_hindsight_metadata_sync(
                request_id, status="FAILED", error=str(exc)[:1200]
            )

    def close(self) -> None:
        """Stop bounded worker lanes before the owning daemon exits."""
        self._submission_dispatcher_stop.set()
        self._submission_dispatcher_wake.set()
        if self._submission_dispatcher_thread is not None:
            self._submission_dispatcher_thread.join(timeout=2)
        self._status_poller_stop.set()
        if self._status_poller_thread is not None:
            self._status_poller_thread.join(timeout=2)
        if self._preflight_stop is not None:
            self._preflight_stop.set()
        if self._preflight_thread is not None:
            self._preflight_thread.join(timeout=2)
            self._publish_preflight_health(
                running=self._preflight_thread.is_alive(), force=True
            )
        if self._metadata_tag_sync_stop is not None:
            self._metadata_tag_sync_stop.set()
        if self._metadata_tag_sync_thread is not None:
            self._metadata_tag_sync_thread.join(timeout=2)
        if self._ocr_executor is not None:
            self._ocr_executor.shutdown(wait=True, cancel_futures=True)
            self._ocr_executor = None

    def start_submission_dispatcher(self, *, poll_interval_seconds: float = 2.0) -> None:
        """Start the queue dispatcher without coupling it to NAS tree scans."""
        if self.processing_queue is None:
            return
        if self._submission_dispatcher_thread is not None and self._submission_dispatcher_thread.is_alive():
            return
        self._submission_dispatcher_stop.clear()
        self._submission_dispatcher_thread = threading.Thread(
            target=self._submission_dispatcher_loop,
            args=(max(0.5, float(poll_interval_seconds)),),
            name="workspace-hindsight-dispatch",
            daemon=True,
        )
        self._submission_dispatcher_thread.start()

    def wake_submission_dispatcher(self) -> None:
        self._submission_dispatcher_wake.set()

    def _submission_dispatcher_loop(self, interval_seconds: float) -> None:
        while not self._submission_dispatcher_stop.is_set():
            try:
                self._dispatch_ready_batch()
                self._submission_dispatcher_last_error = None
            except Exception as exc:
                self._submission_dispatcher_last_error = f"{type(exc).__name__}: {exc}"[:1200]
                LOGGER.exception("Hindsight batch dispatcher failed")
            self._publish_worker_health(
                "hindsight_dispatcher",
                enabled=True,
                running=True,
                healthy=self._submission_dispatcher_last_error is None,
                last_error=self._submission_dispatcher_last_error,
            )
            self._submission_dispatcher_wake.wait(interval_seconds)
            self._submission_dispatcher_wake.clear()

    def _dispatch_ready_batch(self) -> int:
        """Submit up to three already-preflighted documents without rescanning roots."""
        if self.processing_queue is None or not self._submission_dispatch_lock.acquire(blocking=False):
            return 0
        try:
            with self._submission_cache_lock:
                candidates = dict(self._submission_candidates)
            if not candidates:
                return 0
            candidates_by_document = {
                (candidate.workspace, candidate.document_id): (key, candidate)
                for key, candidate in candidates.items()
            }
            states = self._states()
            inflight = set(self._submission_inflight)
            active_count = sum(
                1 for key, row in states.items()
                if row.get("status") in ACTIVE_STATUSES or key in inflight
            )
            slots = self.max_active_hindsight_operations - active_count
            if slots <= 0:
                return 0
            snapshot = self.processing_queue.list_items(include_memorized=True)
            selected: list[tuple[str, ProducerCandidate, dict[str, Any], dict[str, Any] | None]] = []
            for queue_row in snapshot["items"]:
                workspace = str(queue_row.get("workspace") or "")
                document_id = str(queue_row.get("document_id") or "")
                candidate_entry = candidates_by_document.get((workspace, document_id))
                if candidate_entry is None or queue_row.get("preflight_status") != "ANALYZED":
                    continue
                candidate_key, candidate = candidate_entry
                if (
                    queue_row.get("source_sha256") != candidate.source_sha256
                    or queue_row.get("source_path") != candidate.relative_path
                ):
                    continue
                state = states.get(candidate.hindsight_document_id)
                if candidate.hindsight_document_id in inflight or (
                    state and state.get("status") in ACTIVE_STATUSES | {"VERIFY", "COMPLETED", "ARCHIVED"}
                ):
                    continue
                queue_status = str(queue_row.get("hindsight_status") or "")
                approved_replace = bool(
                    state
                    and state.get("status") == "SUBMIT_ERROR"
                    and state.get("last_error") == "Hindsight document already exists; OCR replacement requires operator review"
                    and not state.get("operation_id")
                    and queue_row.get("ocr_replace_approved")
                    and queue_row.get("request_action") == "replace_ocr"
                    and queue_row.get("ocr_status") == "READY"
                    and queue_row.get("ocr_preflight_source_sha256") == candidate.source_sha256
                    and str(queue_row.get("ocr_filename") or "").endswith(".md")
                    and queue_row.get("user_decision") != "DO_NOT_SEND"
                )
                if approved_replace:
                    queue_status = "OCR_READY"
                retry_unavailable = bool(
                    state and state.get("status") == "UNAVAILABLE" and queue_status == "UNAVAILABLE"
                )
                if queue_status not in {"QUEUED", "OCR_READY"} and not retry_unavailable:
                    continue
                if queue_row.get("user_decision") == "DO_NOT_SEND":
                    continue
                if queue_row.get("ocr_status") == "FAILED":
                    continue
                if queue_row.get("ocr_status") in {"QUEUED", "PROCESSING"}:
                    continue
                if queue_status == "OCR_READY" and (
                    queue_row.get("ocr_status") != "READY"
                    or queue_row.get("ocr_preflight_source_sha256") != candidate.source_sha256
                ):
                    continue
                if (
                    queue_row.get("ocr_status") == "READY"
                    and queue_row.get("ocr_filename")
                    and queue_row.get("ocr_preflight_source_sha256") != candidate.source_sha256
                ):
                    continue
                if self.processing_queue.is_item_paused(workspace, document_id, "hindsight"):
                    continue
                if state and state.get("status") == "COMPLETED" and state.get("fingerprint") == candidate.fingerprint:
                    continue
                if state and state.get("status") not in {
                    "QUEUED", "FAILED", "CANCELLED", "OCR_NEEDED", "SUBMIT_ERROR", "UNAVAILABLE"
                }:
                    continue
                if state and state.get("status") == "UNAVAILABLE":
                    try:
                        self._client_for(workspace).service_health()
                    except RuntimeError:
                        continue
                selected.append((candidate_key, candidate, dict(queue_row), state))
                if len(selected) >= slots:
                    break
            if not selected:
                return 0

            by_workspace: dict[str, list[tuple[str, ProducerCandidate, dict[str, Any], dict[str, Any] | None]]] = {}
            for item in selected:
                by_workspace.setdefault(item[1].workspace, []).append(item)
            submitted = 0
            for workspace, group in by_workspace.items():
                client = self._client_for(workspace)
                request_files: list[dict[str, Any]] = []
                request_items: list[tuple[str, ProducerCandidate, dict[str, Any], dict[str, Any] | None, list[str], bool]] = []
                total_size = 0
                for key, candidate, queue_row, state in group:
                    source = candidate.source_path
                    tags = list(candidate.tags)
                    metadata = dict(candidate.metadata)
                    context = candidate.context
                    ocr_submission = bool(
                        queue_row.get("hindsight_status") == "OCR_READY"
                        or (queue_row.get("ocr_status") == "READY" and queue_row.get("ocr_filename"))
                    )
                    expected_sha256 = candidate.source_sha256
                    if ocr_submission:
                        filename = str(queue_row.get("ocr_filename") or "")
                        cache_dir = self.ocr_processor.cache_dir if self.ocr_processor is not None else None
                        if cache_dir is None or Path(filename).name != filename or not filename.endswith(".md"):
                            continue
                        ocr_path = cache_dir / filename
                        if not ocr_path.is_file() or _sha256(candidate.source_path) != candidate.source_sha256:
                            continue
                        source = ocr_path
                        expected_sha256 = _sha256(ocr_path)
                        tags = sorted(set(tags) | {"ocr:complete"})
                        metadata.update({
                            "ocr_engine": str(queue_row.get("ocr_engine") or "unknown"),
                            "ocr_derived_from": candidate.relative_path,
                            "ocr_source_sha256": candidate.source_sha256,
                            "ocr_artifact_name": ocr_path.name,
                        })
                        context = (
                            f"{candidate.context}; Hindsight text representation=OCR derivative; "
                            f"content is an OCR derivative of the authoritative source file "
                            f"{candidate.relative_path}; OCR artifact filename={ocr_path.name}; "
                            f"raw source SHA-256={candidate.source_sha256}; do not OCR this source again "
                            "when this matching derivative is available"
                        )
                        try:
                            existing = client.get_document(candidate.hindsight_document_id)
                        except RuntimeError as exc:
                            if "Hindsight HTTP 404:" not in str(exc):
                                continue
                        else:
                            if (existing.get("id") == candidate.hindsight_document_id
                                    and not queue_row.get("ocr_replace_approved")):
                                continue
                    try:
                        authoritative_source = candidate.source_path.resolve(strict=True)
                        authoritative_source.relative_to(self.roots[workspace].resolve(strict=True))
                        source.resolve(strict=True)
                        size = source.stat().st_size
                        if not source.is_file() or source.is_symlink():
                            continue
                    except (OSError, RuntimeError, ValueError):
                        continue
                    if size > client.max_file_bytes or total_size + size > 100 * 1024 * 1024:
                        continue
                    total_size += size
                    request_files.append({
                        "source": source,
                        "document_id": candidate.hindsight_document_id,
                        "context": context,
                        "tags": tags,
                        "metadata": metadata,
                        "expected_source_sha256": expected_sha256,
                    })
                    request_items.append((key, candidate, queue_row, state, tags, ocr_submission))
                if not request_files:
                    continue
                # Build and checksum the complete request before writing SUBMITTING;
                # a missing or changed source therefore cannot create a false remote intent.
                prepared: list[dict[str, Any]] = []
                prepared_items = []
                for request_file, request_item in zip(request_files, request_items, strict=True):
                    try:
                        prepared.extend(client.prepare_retain_files_batch([request_file]))
                    except (OSError, RuntimeError, ValueError) as exc:
                        key, candidate, queue_row, _state, tags, ocr_submission = request_item
                        message = str(exc)[:1200]
                        source_unavailable = any(
                            marker in message.casefold()
                            for marker in (
                                "source unavailable before hindsight upload",
                                "source changed before hindsight upload",
                            )
                        )
                        self._save(
                            candidate, hindsight_document_id=key, document_id=candidate.document_id,
                            workspace=candidate.workspace, source_path=candidate.relative_path,
                            source_sha256=candidate.source_sha256, fingerprint=candidate.fingerprint,
                            operation_id=None, status="QUEUED" if source_unavailable else "SUBMIT_ERROR",
                            last_error=message, tags=tags,
                        )
                        self.processing_queue.set_status(
                            candidate.workspace, candidate.document_id,
                            preflight_status="STABILIZING" if source_unavailable else "ANALYZED",
                            hindsight_status="MODIFIED" if source_unavailable else "FAILED",
                            operation_id=None, clear_operation_id=True, error=message,
                        )
                        if ocr_submission:
                            self.processing_queue.set_ocr_status(
                                candidate.workspace, candidate.document_id,
                                status="READY",
                                queue_status="MODIFIED" if source_unavailable else "FAILED",
                            )
                        LOGGER.warning(
                            "Hindsight batch omitted one source (%s, %s): %s",
                            workspace, candidate.document_id, message[:500],
                        )
                        continue
                    prepared_items.append(request_item)
                request_items = prepared_items
                if not prepared:
                    continue
                latest_states = self._states()
                latest_queue = {
                    (str(item["workspace"]), str(item["document_id"])): item
                    for item in self.processing_queue.list_items(include_memorized=True)["items"]
                }
                if any(
                    self.processing_queue.is_item_paused(item[1].workspace, item[1].document_id, "hindsight")
                    or (
                        latest_states.get(item[0])
                        and latest_states[item[0]].get("status")
                        in ACTIVE_STATUSES | {"VERIFY", "COMPLETED", "ARCHIVED"}
                    )
                    or (
                        (current := latest_queue.get((item[1].workspace, item[1].document_id))) is None
                        or current.get("preflight_status") != "ANALYZED"
                        or current.get("user_decision") == "DO_NOT_SEND"
                        or current.get("source_sha256") != item[1].source_sha256
                        or current.get("source_path") != item[1].relative_path
                        or current.get("hindsight_status") != item[2].get("hindsight_status")
                        or current.get("ocr_status") != item[2].get("ocr_status")
                        or current.get("ocr_filename") != item[2].get("ocr_filename")
                        or current.get("ocr_preflight_source_sha256") != item[2].get("ocr_preflight_source_sha256")
                        or current.get("hindsight_status") not in {"QUEUED", "OCR_READY", "UNAVAILABLE", "VERIFY"}
                        or (item[5] and current.get("ocr_preflight_source_sha256") != item[1].source_sha256)
                    )
                    for item in request_items
                ):
                    continue
                now = _utc_now()
                for key, candidate, queue_row, state, tags, ocr_submission in request_items:
                    self._submission_inflight.add(key)
                    self._save(
                        candidate, hindsight_document_id=key, document_id=candidate.document_id,
                        workspace=candidate.workspace, source_path=candidate.relative_path,
                        source_sha256=candidate.source_sha256, fingerprint=candidate.fingerprint,
                        operation_id=None, status="SUBMITTING", tags=tags, updated_at=now,
                    )
                    self.processing_queue.set_status(
                        candidate.workspace, candidate.document_id,
                        preflight_status="ANALYZED", hindsight_status="MEMORIZING",
                        operation_id=None, clear_operation_id=True, clear_error=True,
                    )
                    if ocr_submission:
                        self.processing_queue.set_ocr_status(
                            candidate.workspace, candidate.document_id, status="SUBMITTED"
                        )
                    if queue_row.get("ocr_replace_approved"):
                        self.processing_queue.consume_ocr_replacement_approval(
                            candidate.workspace, candidate.document_id
                        )
                try:
                    operation_ids = client.submit_prepared_files(prepared)
                except (OSError, RuntimeError) as exc:
                    message = str(exc)[:1200]
                    unavailable = _hindsight_connection_unavailable(message)
                    uncertain = _submission_outcome_uncertain(message)
                    for key, candidate, queue_row, state, tags, ocr_submission in request_items:
                        status = "UNAVAILABLE" if unavailable else "SUBMITTING" if uncertain else "SUBMIT_ERROR"
                        self._save(
                            candidate, hindsight_document_id=key, document_id=candidate.document_id,
                            workspace=candidate.workspace, source_path=candidate.relative_path,
                            source_sha256=candidate.source_sha256, fingerprint=candidate.fingerprint,
                            operation_id=None, status=status, last_error=message, tags=tags,
                            updated_at=now if uncertain else None,
                        )
                        self.processing_queue.set_status(
                            candidate.workspace, candidate.document_id,
                            preflight_status="ANALYZED",
                            hindsight_status="UNAVAILABLE" if unavailable else "VERIFY" if uncertain else "FAILED",
                            error=message,
                        )
                        if ocr_submission:
                            self.processing_queue.set_ocr_status(
                                candidate.workspace, candidate.document_id, status="READY",
                                queue_status="UNAVAILABLE" if unavailable else "VERIFY" if uncertain else "FAILED",
                            )
                        self._submission_inflight.discard(key)
                    if unavailable or uncertain:
                        break
                    continue
                for (key, candidate, queue_row, state, tags, _ocr_submission), operation_id in zip(request_items, operation_ids, strict=True):
                    self._save(
                        candidate, hindsight_document_id=key, document_id=candidate.document_id,
                        workspace=candidate.workspace, source_path=candidate.relative_path,
                        source_sha256=candidate.source_sha256, fingerprint=candidate.fingerprint,
                        operation_id=operation_id, status="SUBMITTED", tags=tags,
                    )
                    self.processing_queue.set_status(
                        candidate.workspace, candidate.document_id,
                        preflight_status="ANALYZED", hindsight_status="MEMORIZING",
                        operation_id=operation_id,
                    )
                    self._submission_inflight.discard(key)
                    submitted += 1
            return submitted
        finally:
            self._submission_dispatch_lock.release()

    def start_status_poller(self, *, interval_seconds: float = 30.0) -> None:
        """Poll active Hindsight operations independently of filesystem scans."""
        if self.processing_queue is None:
            return
        interval = max(1.0, float(interval_seconds))
        self._status_poller_interval_seconds = interval
        if self._status_poller_thread is not None and self._status_poller_thread.is_alive():
            return
        self._status_poller_stop.clear()
        self._status_poller_thread = threading.Thread(
            target=self._status_poller_loop,
            name="workspace-hindsight-status",
            daemon=True,
        )
        self._status_poller_thread.start()

    def _status_poller_loop(self) -> None:
        while not self._status_poller_stop.is_set():
            try:
                self.client.service_health()
                self._hindsight_health_error = None
            except Exception as exc:
                self._hindsight_health_error = f"{type(exc).__name__}: {exc}"[:1200]
            self._publish_worker_health(
                "hindsight",
                enabled=bool(self.clients or self.client),
                running=bool(self._status_poller_thread and self._status_poller_thread.is_alive()),
                healthy=self._hindsight_health_error is None,
                last_error=self._hindsight_health_error,
            )
            try:
                states = self._states()
                for row in states.values():
                    if (
                        row.get("status") in ACTIVE_STATUSES
                        and row.get("operation_id")
                        and not self._status_poller_stop.is_set()
                    ):
                        try:
                            self._poll(row)
                            self._status_poller_last_error = None
                        except Exception as exc:
                            # A status-poll failure must not stop future checks or
                            # interfere with the independent filesystem coordinator.
                            self._status_poller_last_error = (
                                f"{type(exc).__name__}: {exc}"
                            )[:1200]
            except Exception as exc:
                self._status_poller_last_error = f"{type(exc).__name__}: {exc}"[:1200]
            self._status_poller_stop.wait(self._status_poller_interval_seconds)

    def _preflight_cache_key(self, source_sha256: str, workspace: str) -> str:
        source_kind = self._source_kind_for(workspace)
        metadata_profile = self.metadata_profiles.get(workspace)
        return hashlib.sha256(
            f"{PREFLIGHT_CACHE_VERSION}\0{source_kind}\0{metadata_profile or ''}\0{workspace}\0{source_sha256}".encode("utf-8")
        ).hexdigest()

    def _save_preflight_result(
        self, source: Path, *, source_sha256: str, workspace: str, result: PreflightResult
    ) -> None:
        cache_key = self._preflight_cache_key(source_sha256, workspace)
        try:
            source_path = source.relative_to(self.roots[workspace]).as_posix()
        except (KeyError, ValueError):
            source_path = None
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    f"""INSERT INTO {PREFLIGHT_TABLE}(cache_key, result_json, updated_at)
                        VALUES (?, ?, ?) ON CONFLICT(cache_key) DO UPDATE SET
                        result_json=excluded.result_json, updated_at=excluded.updated_at""",
                    (cache_key, json.dumps(result.as_dict(), ensure_ascii=False, separators=(",", ":")), _utc_now()),
                )
                if source_path is not None:
                    connection.execute(
                        f"""INSERT INTO {PREFLIGHT_SOURCE_TABLE}(
                            workspace, source_path, source_sha256, cache_key, updated_at
                        ) VALUES (?, ?, ?, ?, ?) ON CONFLICT(workspace, source_path) DO UPDATE SET
                            source_sha256=excluded.source_sha256, cache_key=excluded.cache_key,
                            updated_at=excluded.updated_at""",
                        (workspace, source_path, source_sha256, cache_key, _utc_now()),
                    )
        finally:
            connection.close()

    def _preflight_is_stable(self, request: Mapping[str, Any]) -> bool:
        if self.settle_observations <= 1:
            return True
        source_fingerprint = hashlib.sha256(
            f"{request['source_path']}\0{request['source_sha256']}".encode("utf-8")
        ).hexdigest()
        connection = self._connect()
        try:
            row = connection.execute(
                f"SELECT fingerprint, observations FROM {OBSERVATION_TABLE} WHERE hindsight_document_id=?",
                (f"{request['document_id']}:source",),
            ).fetchone()
        finally:
            connection.close()
        return bool(
            row
            and row["fingerprint"] == source_fingerprint
            and int(row["observations"]) >= self.settle_observations
        )

    def _defer_preflight_source(
        self, request: Mapping[str, Any], error: Exception
    ) -> None:
        assert self.processing_queue is not None
        workspace = str(request["workspace"])
        document_id = str(request["document_id"])
        source_sha256 = str(request["source_sha256"])
        current = self.processing_queue.get_item(workspace, document_id)
        if current and current.get("source_sha256") == source_sha256:
            self.processing_queue.set_status(
                workspace, document_id, preflight_status="STABILIZING",
                hindsight_status="MODIFIED", error=str(error)[:1200],
            )
            key = (workspace, document_id)
            previous = self._preflight_waiting_source.get(key)
            attempt = previous[2] + 1 if previous and previous[0] == source_sha256 else 1
            delay_seconds = min(300.0, 2.0 ** min(attempt, 8))
            self._preflight_waiting_source[key] = (
                source_sha256, time.monotonic() + delay_seconds, attempt
            )
            message = f"{type(error).__name__}: {error}; retry {attempt} in {delay_seconds:g}s"[:1200]
            with self._preflight_health_lock:
                self._preflight_last_error = message
                self._preflight_last_error_at = _utc_now()
            LOGGER.warning(
                "preflight source was unavailable or changed; retry scheduled "
                "(workspace=%s document=%s attempt=%s delay_seconds=%s): %s",
                workspace, document_id, attempt, delay_seconds, str(error)[:500],
            )
        self._notify_work_available()

    def _process_preflight_request(
        self, request: Mapping[str, Any], *, stability_checked: bool = False
    ) -> None:
        assert self.processing_queue is not None
        workspace = str(request["workspace"])
        document_id = str(request["document_id"])
        relative_path = str(request["source_path"])
        source_sha256 = str(request["source_sha256"])
        if not stability_checked and not self._preflight_is_stable(request):
            return
        if not self.processing_queue.claim_preflight(workspace, document_id, source_sha256):
            return
        source = self.roots[workspace] / relative_path
        try:
            if not source.exists():
                raise SourceChangedDuringPreflight("La source n’est plus présente au chemin indexé.")
            root_resolved = self.roots[workspace].resolve(strict=True)
            source_resolved = source.resolve(strict=True)
            source_resolved.relative_to(root_resolved)
            if source.is_symlink() or not source.is_file():
                raise OSError("La source n’est pas un fichier régulier.")
            if _sha256(source) != source_sha256:
                raise SourceChangedDuringPreflight("La source a changé avant le préflight.")
            stat_before = source.stat()
            ocr_status = str(request.get("ocr_status") or "").upper()
            ocr_filename = str(request.get("ocr_filename") or "")
            if ocr_status == "READY" and ocr_filename:
                cache_dir = self.ocr_processor.cache_dir if self.ocr_processor is not None else None
                if (
                    cache_dir is None
                    or Path(ocr_filename).name != ocr_filename
                    or not ocr_filename.endswith(".md")
                ):
                    raise RuntimeError("OCR Markdown artifact reference is invalid")
                ocr_path = cache_dir / ocr_filename
                if not ocr_path.is_file():
                    raise RuntimeError("OCR Markdown artifact is missing; OCR must be rerun")
                result = preflight_ocr_markdown(
                    ocr_path,
                    profile=self.metadata_profiles.get(workspace),
                    source_kind=self._source_kind_for(workspace),
                    workspace=workspace,
                    pdf_creation_date=_read_pdf_creation_date(source),
                )
            else:
                result = preflight_pdf_metadata(
                    source,
                    source_kind=self._source_kind_for(workspace),
                    workspace=workspace,
                    profile=self.metadata_profiles.get(workspace),
                )
            stat_after = source.stat()
            if (stat_before.st_dev, stat_before.st_ino, stat_before.st_size, stat_before.st_mtime_ns) != (
                stat_after.st_dev, stat_after.st_ino, stat_after.st_size, stat_after.st_mtime_ns
            ):
                # Network filesystems can refresh inode/mtime metadata without
                # changing the bytes. Treat the content digest as authoritative;
                # only defer when the source version actually changed.
                if _sha256(source) != source_sha256:
                    raise SourceChangedDuringPreflight("La source a changé pendant le préflight.")
            if source.suffix.casefold() == ".pdf":
                self._save_preflight_result(
                    source, source_sha256=source_sha256, workspace=workspace, result=result
                )
                if ocr_status == "READY" and ocr_filename:
                    self.processing_queue.mark_ocr_preflight_done(
                        workspace, document_id, source_sha256
                    )
        except SourceChangedDuringPreflight as exc:
            self._defer_preflight_source(request, exc)
            return
        except OSError as exc:
            self._defer_preflight_source(
                request,
                SourceChangedDuringPreflight(f"La source est temporairement indisponible : {exc}"),
            )
            return
        except Exception as exc:
            message = f"Analyse : {type(exc).__name__}: {exc}"[:1200]
            current = self.processing_queue.get_item(workspace, document_id)
            if current and current.get("source_sha256") == source_sha256 and current.get("preflight_status") == "ANALYZING":
                self.processing_queue.set_status(
                    workspace, document_id, preflight_status="FAILED",
                    hindsight_status=current.get("hindsight_status"), error=message,
                )
            with self._preflight_health_lock:
                self._preflight_last_error = message
                self._preflight_last_error_at = _utc_now()
            LOGGER.exception(
                "preflight failed (workspace=%s document=%s)", workspace, document_id
            )
            self._notify_work_available()
            return
        if (
            result.status == "no_native_text"
            and ocr_status == "NONE"
            and source.suffix.casefold() == ".pdf"
            and self.processing_queue.queue_ocr_after_empty_analysis(
                workspace, document_id, source_sha256
            )
        ):
            self._preflight_waiting_source.pop((workspace, document_id), None)
            with self._preflight_health_lock:
                self._preflight_last_success_at = _utc_now()
                self._preflight_last_error = None
                self._preflight_last_error_at = None
            self._notify_work_available()
            return
        current = self.processing_queue.get_item(workspace, document_id)
        if current and current.get("source_sha256") == source_sha256 and current.get("preflight_status") == "ANALYZING":
            self.processing_queue.complete_preflight(
                workspace, document_id, source_sha256
            )
            self._preflight_waiting_source.pop((workspace, document_id), None)
            with self._preflight_health_lock:
                self._preflight_last_success_at = _utc_now()
                self._preflight_last_error = None
                self._preflight_last_error_at = None
            self._notify_work_available()

    def _preflight_worker_loop(self) -> None:
        """Consume the shared preflight lane independently of Hindsight polling/upload."""
        assert self.processing_queue is not None and self._preflight_stop is not None
        reconciled_ocr_preflights = False
        while not self._preflight_stop.is_set():
            self._publish_preflight_health()
            try:
                if not reconciled_ocr_preflights:
                    self.processing_queue.queue_missing_ocr_preflights()
                    reconciled_ocr_preflights = True
                requests = self.processing_queue.preflight_requests(limit=4096)
                paused = {
                    workspace: self.processing_queue.is_paused(workspace)
                    for workspace in {str(item["workspace"]) for item in requests}
                }
                stable_observations: dict[str, tuple[str, int]] = {}
                if self.settle_observations > 1 and requests:
                    connection = self._connect()
                    try:
                        stable_observations = {
                            str(row["hindsight_document_id"]): (
                                str(row["fingerprint"]), int(row["observations"])
                            )
                            for row in connection.execute(
                                f"SELECT hindsight_document_id, fingerprint, observations FROM {OBSERVATION_TABLE}"
                            ).fetchall()
                        }
                    finally:
                        connection.close()
            except Exception as exc:
                message = f"{type(exc).__name__}: {exc}"[:1200]
                with self._preflight_health_lock:
                    self._preflight_last_error = message
                    self._preflight_last_error_at = _utc_now()
                self._publish_preflight_health(force=True)
                LOGGER.exception("preflight worker could not read its queue or stability state")
                self._preflight_stop.wait(2.0)
                continue
            handled = False
            for request in requests:
                if self._preflight_stop.is_set():
                    break
                workspace = str(request["workspace"])
                if paused.get(workspace, False) or self.processing_queue.is_item_paused(
                    workspace, str(request["document_id"]), "preflight"
                ):
                    continue
                stable = self.settle_observations <= 1
                if not stable:
                    expected_fingerprint = hashlib.sha256(
                        f"{request['source_path']}\0{request['source_sha256']}".encode("utf-8")
                    ).hexdigest()
                    observed = stable_observations.get(f"{request['document_id']}:source")
                    stable = bool(
                        observed
                        and observed[0] == expected_fingerprint
                        and observed[1] >= self.settle_observations
                    )
                if not stable:
                    continue
                blocked_key = (str(request["workspace"]), str(request["document_id"]))
                retry = self._preflight_waiting_source.get(blocked_key)
                if retry is not None:
                    if retry[0] == str(request["source_sha256"]):
                        if time.monotonic() < retry[1]:
                            continue
                    else:
                        self._preflight_waiting_source.pop(blocked_key, None)
                try:
                    with self._preflight_health_lock:
                        self._preflight_active_document = {
                            "workspace": workspace,
                            "document_id": str(request["document_id"]),
                            "source_path": str(request["source_path"]),
                        }
                    self._publish_preflight_health(force=True)
                    self._process_preflight_request(request, stability_checked=True)
                except Exception as exc:
                    message = f"Préflight worker: {type(exc).__name__}: {exc}"[:1200]
                    with self._preflight_health_lock:
                        self._preflight_last_error = message
                        self._preflight_last_error_at = _utc_now()
                    LOGGER.exception(
                        "unexpected preflight worker failure (workspace=%s document=%s)",
                        workspace, request["document_id"],
                    )
                    try:
                        current = self.processing_queue.get_item(
                            str(request["workspace"]), str(request["document_id"])
                        )
                        if current and current.get("source_sha256") == request["source_sha256"]:
                            self.processing_queue.set_status(
                                str(request["workspace"]), str(request["document_id"]),
                                preflight_status="FAILED", hindsight_status="FAILED",
                                error=message,
                            )
                        self._notify_work_available()
                    except Exception:
                        LOGGER.exception(
                            "could not persist preflight worker failure "
                            "(workspace=%s document=%s)",
                            workspace, request["document_id"],
                        )
                finally:
                    with self._preflight_health_lock:
                        self._preflight_active_document = None
                    self._publish_preflight_health(force=True)
                handled = True
                # Re-read priorities after each file: a user reorder made during
                # this analysis applies to the next claim, not after a whole batch.
                break
            self._preflight_stop.wait(0 if handled else 1.0)
        self._publish_preflight_health(running=False, force=True)

    def _notify_work_available(self) -> None:
        callback = self.on_work_available
        if callable(callback):
            callback()

    def _publish_preflight_health(
        self, *, running: bool | None = None, force: bool = False
    ) -> None:
        """Persist a credential-free heartbeat for the Cockpit sharing this queue."""
        if self.processing_queue is None:
            return
        now = time.monotonic()
        if not force and now - self._preflight_last_heartbeat < 15.0:
            return
        with self._preflight_health_lock:
            payload: dict[str, Any] = {
                "enabled": True,
                "running": bool(self._preflight_thread and self._preflight_thread.is_alive())
                if running is None else running,
                "healthy": True,
                "last_error": self._preflight_last_error,
                "last_error_at": self._preflight_last_error_at,
                "last_success_at": self._preflight_last_success_at,
                "retry_waiting": len(self._preflight_waiting_source),
            }
            if self._preflight_active_document:
                payload["active_document"] = dict(self._preflight_active_document)
        try:
            self.processing_queue.publish_worker_health("preflight", payload)
            ocr_enabled = self.ocr_processor is not None and self._ocr_executor is not None
            self.processing_queue.publish_worker_health(
                "ocr",
                {
                    "enabled": ocr_enabled,
                    "running": bool(ocr_enabled and self._preflight_thread and self._preflight_thread.is_alive()),
                    "healthy": True,
                    "last_error": None,
                },
            )
            self._preflight_last_heartbeat = now
        except Exception as exc:
            if now - self._preflight_health_warning_at >= 60.0:
                LOGGER.warning("could not publish preflight worker health: %s", exc)
                self._preflight_health_warning_at = now

    def _publish_worker_health(
        self,
        worker_name: str,
        *,
        enabled: bool,
        running: bool,
        healthy: bool,
        last_error: str | None,
    ) -> None:
        if self.processing_queue is None:
            return
        try:
            self.processing_queue.publish_worker_health(
                worker_name,
                {
                    "enabled": enabled,
                    "running": running,
                    "healthy": healthy,
                    "last_error": last_error,
                },
            )
        except (OSError, sqlite3.Error) as exc:
            LOGGER.warning("could not publish %s worker health: %s", worker_name, exc)

    def _advance_ocr(self, candidates: Mapping[str, ProducerCandidate]) -> bool:
        """Advance the explicit OCR lane; return true while one OCR job is active."""
        if self.processing_queue is None or self.ocr_processor is None or self._ocr_executor is None:
            return False
        for key, future in list(self._ocr_futures.items()):
            if not future.done():
                continue
            workspace, document_id = key
            current_item = self.processing_queue.get_item(workspace, document_id)
            try:
                result = future.result()
            except Exception as exc:
                if (
                    isinstance(exc, OSError)
                    and current_item
                    and current_item.get("ocr_status") == "PROCESSING"
                ):
                    source_sha256 = str(current_item.get("source_sha256") or "")
                    previous = self._ocr_waiting_source.get(key)
                    attempt = previous[2] + 1 if previous and previous[0] == source_sha256 else 1
                    delay_seconds = min(300.0, 2.0 ** min(attempt, 8))
                    self._ocr_waiting_source[key] = (
                        source_sha256, time.monotonic() + delay_seconds, attempt
                    )
                    self.processing_queue.set_ocr_status(
                        workspace, document_id, status="QUEUED",
                        error=f"Source temporairement indisponible pendant l’OCR : {exc}; reprise dans {delay_seconds:g}s",
                        queue_status="OCR_QUEUED",
                    )
                elif current_item and current_item.get("ocr_status") == "PROCESSING":
                    self.processing_queue.set_ocr_status(
                        workspace, document_id, status="FAILED", error=str(exc),
                        queue_status=(str(current_item.get("ocr_revision_origin_status") or "MODIFIED")
                                      if current_item.get("ocr_is_revision") else "FAILED"),
                    )
            else:
                if (
                    current_item
                    and current_item.get("ocr_status") == "PROCESSING"
                    and current_item.get("source_sha256") == result.source_sha256
                ):
                    self.processing_queue.set_ocr_status(
                        workspace, document_id, status="READY",
                        output_filename=result.markdown_path.name, engine=result.engine,
                        queue_status=("MODIFIED" if current_item.get("ocr_is_revision") else "OCR_READY"),
                    )
                    self.processing_queue.set_status(
                        workspace, document_id, preflight_status="TO_PROCESS",
                        clear_error=True,
                    )
                    self._ocr_waiting_source.pop(key, None)
            del self._ocr_futures[key]

        # Bound OCR independently. Shared inference concurrency and waiting are
        # handled by the model server, so Docling can run during a remote retain.
        if self._ocr_futures:
            return True
        for request in self.processing_queue.ocr_requests():
            workspace = str(request["workspace"])
            document_id = str(request["document_id"])
            candidate = next((value for value in candidates.values()
                              if value.workspace == workspace and value.document_id == document_id), None)
            if candidate is None:
                # A scan can miss a network-mounted source transiently. Keep the
                # persisted OCR request queued until a complete scan sees it again.
                continue
            if candidate.source_path.suffix.casefold() != ".pdf":
                self.processing_queue.set_ocr_status(
                    workspace, document_id, status="FAILED",
                    error="La source de la demande OCR n’est plus un PDF.",
                    queue_status="FAILED",
                )
                continue
            if candidate.source_sha256 != str(request["source_sha256"]):
                self.processing_queue.set_ocr_status(
                    workspace, document_id, status="FAILED",
                    error="Le PDF a changé depuis la demande OCR ; nouvelle analyse requise.",
                    queue_status="MODIFIED",
                )
                continue
            waiting = self._ocr_waiting_source.get((workspace, document_id))
            if waiting and waiting[0] == candidate.source_sha256 and time.monotonic() < waiting[1]:
                continue
            if self.processing_queue.is_item_paused(workspace, document_id, "ocr"):
                continue
            digest = hashlib.sha256(
                f"{workspace}\0{document_id}\0{candidate.source_sha256}".encode("utf-8")
            ).hexdigest()
            output_path = self.ocr_processor.cache_dir / f"{digest}.md"
            self.processing_queue.set_ocr_status(
                workspace, document_id, status="PROCESSING", queue_status="OCR_PROCESSING"
            )
            future = self._ocr_executor.submit(
                self.ocr_processor.process,
                candidate.source_path,
                expected_source_sha256=candidate.source_sha256,
                output_path=output_path,
            )
            self._ocr_futures[(workspace, document_id)] = future
            future.add_done_callback(lambda _future: self._notify_work_available())
            break
        return bool(self._ocr_futures)

    def _source_kind_for(self, workspace: str) -> str:
        return self.source_kinds.get(workspace, self.source_kind)

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
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {PREFLIGHT_TABLE} (
                    cache_key TEXT PRIMARY KEY,
                    result_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {PREFLIGHT_SOURCE_TABLE} (
                    workspace TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    source_sha256 TEXT NOT NULL,
                    cache_key TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(workspace, source_path)
                )
                """
            )
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {DOCUMENT_NOTES_TABLE} (
                    workspace TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    document_id TEXT,
                    source_sha256 TEXT,
                    note TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(workspace, source_path)
                )
                """
            )
            connection.execute(
                f"CREATE UNIQUE INDEX IF NOT EXISTS idx_{DOCUMENT_NOTES_TABLE}_identity "
                f"ON {DOCUMENT_NOTES_TABLE}(workspace, document_id) WHERE document_id IS NOT NULL"
            )
            connection.execute(
                f"""CREATE TABLE IF NOT EXISTS {DOCUMENT_METADATA_OVERRIDES_TABLE} (
                    workspace TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    document_id TEXT,
                    source_sha256 TEXT,
                    overrides_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(workspace, source_path)
                )"""
            )
            connection.execute(
                f"CREATE UNIQUE INDEX IF NOT EXISTS idx_{DOCUMENT_METADATA_OVERRIDES_TABLE}_identity "
                f"ON {DOCUMENT_METADATA_OVERRIDES_TABLE}(workspace, document_id) WHERE document_id IS NOT NULL"
            )
            connection.execute(
                f"""CREATE TABLE IF NOT EXISTS {PROJECT_OVERVIEW_TABLE} (
                    workspace TEXT NOT NULL,
                    scope_project TEXT NOT NULL,
                    scope_tag TEXT NOT NULL,
                    page_name TEXT NOT NULL,
                    source_query TEXT NOT NULL,
                    page_id TEXT,
                    operation_id TEXT,
                    status TEXT NOT NULL,
                    last_error TEXT,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(workspace, scope_project)
                )"""
            )
            # Full tree reconciliation still checks paths and stat metadata (needed
            # for NAS deletions and remote CIFS changes), but unchanged files do not
            # need to be read byte-for-byte on every pass just to recover their SHA.
            connection.execute(
                f"""CREATE TABLE IF NOT EXISTS {SOURCE_HASH_CACHE_TABLE} (
                    workspace TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    mtime_ns INTEGER NOT NULL,
                    ctime_ns INTEGER NOT NULL,
                    inode INTEGER NOT NULL,
                    source_sha256 TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(workspace, source_path)
                )"""
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

    @staticmethod
    def _source_stat_signature(source: Path) -> tuple[int, int, int, int]:
        stat = source.stat()
        return (
            int(stat.st_size),
            int(stat.st_mtime_ns),
            int(stat.st_ctime_ns),
            int(stat.st_ino),
        )

    def _source_sha256(self, workspace: str, relative_path: str, source: Path) -> str:
        """Reuse a digest only while the mounted file's stat signature is unchanged.

        A full directory walk remains the source of truth for additions/removals,
        including changes that CIFS does not report through inotify. This cache only
        avoids repeatedly reading the contents of files whose metadata is stable.
        """
        signature = self._source_stat_signature(source)
        cache_key = (workspace, relative_path)
        with self._source_hash_cache_lock:
            cached = self._source_hash_cache.get(cache_key)
        if cached is not None and cached[0] == signature:
            return cached[1]

        source_sha256 = _sha256(source)
        # Do not cache a digest against metadata from before a concurrent write.
        try:
            after_hash_signature = self._source_stat_signature(source)
        except OSError:
            after_hash_signature = None
        if after_hash_signature == signature:
            with self._source_hash_cache_lock:
                concurrent = self._source_hash_cache.get(cache_key)
                if concurrent is not None and concurrent[0] == signature:
                    return concurrent[1]
            connection = self._connect()
            try:
                connection.execute(
                    f"""INSERT INTO {SOURCE_HASH_CACHE_TABLE}
                        (workspace, source_path, size, mtime_ns, ctime_ns, inode,
                         source_sha256, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(workspace, source_path) DO UPDATE SET
                            size = excluded.size,
                            mtime_ns = excluded.mtime_ns,
                            ctime_ns = excluded.ctime_ns,
                            inode = excluded.inode,
                            source_sha256 = excluded.source_sha256,
                            updated_at = excluded.updated_at""",
                    (workspace, relative_path, *signature, source_sha256, _utc_now()),
                )
                connection.commit()
            finally:
                connection.close()
            with self._source_hash_cache_lock:
                self._source_hash_cache[cache_key] = (signature, source_sha256)
        return source_sha256

    def _load_source_hash_cache(self) -> None:
        connection = self._connect()
        try:
            rows = connection.execute(
                f"""SELECT workspace, source_path, size, mtime_ns, ctime_ns, inode,
                           source_sha256
                    FROM {SOURCE_HASH_CACHE_TABLE}"""
            ).fetchall()
        finally:
            connection.close()
        loaded = {
            (str(row["workspace"]), str(row["source_path"])): (
                tuple(int(row[key]) for key in ("size", "mtime_ns", "ctime_ns", "inode")),
                str(row["source_sha256"]),
            )
            for row in rows
        }
        with self._source_hash_cache_lock:
            self._source_hash_cache = loaded

    def _project_overview_state(self, workspace: str, project: str) -> dict[str, Any] | None:
        connection = self._connect()
        try:
            row = connection.execute(
                f"SELECT * FROM {PROJECT_OVERVIEW_TABLE} WHERE workspace = ? AND scope_project = ?",
                (workspace, project),
            ).fetchone()
            return dict(row) if row is not None else None
        finally:
            connection.close()

    def _save_project_overview(
        self, *, workspace: str, project: str, scope_tag: str, page_name: str,
        source_query: str, page_id: str | None, operation_id: str | None,
        status: str, last_error: str | None = None,
    ) -> None:
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    f"""INSERT INTO {PROJECT_OVERVIEW_TABLE}(
                        workspace, scope_project, scope_tag, page_name, source_query,
                        page_id, operation_id, status, last_error, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(workspace, scope_project) DO UPDATE SET
                        scope_tag=excluded.scope_tag,
                        page_name=excluded.page_name,
                        source_query=excluded.source_query,
                        page_id=COALESCE(excluded.page_id, {PROJECT_OVERVIEW_TABLE}.page_id),
                        operation_id=COALESCE(excluded.operation_id, {PROJECT_OVERVIEW_TABLE}.operation_id),
                        status=excluded.status,
                        last_error=excluded.last_error,
                        updated_at=excluded.updated_at""",
                    (workspace, project, scope_tag, page_name, source_query, page_id,
                     operation_id, status, last_error, _utc_now()),
                )
        finally:
            connection.close()

    def _ensure_project_overviews(
        self, candidates: Mapping[str, ProducerCandidate], states: Mapping[str, dict[str, Any]]
    ) -> None:
        """Create/track one scoped orientation page after project observations exist."""
        if not self.project_overview_prompts:
            return
        eligible: dict[tuple[str, str], ProducerCandidate] = {}
        for key, candidate in candidates.items():
            prompt_template = self.project_overview_prompts.get(candidate.workspace)
            state = states.get(key)
            project = candidate.metadata.get("scope_project")
            root_project = _path_project(candidate.relative_path)
            if (
                not prompt_template
                or not project
                or not root_project
                or not _same_project(project, root_project)
                or not state
                or state.get("status") != "COMPLETED"
                or state.get("fingerprint") != candidate.fingerprint
            ):
                continue
            eligible[(candidate.workspace, project)] = candidate

        # Keep each reconciliation bounded: one project's page lifecycle is advanced
        # per pass, independently of the one-file ingestion lane.
        pending_projects = []
        for project_key, candidate in eligible.items():
            prior = self._project_overview_state(*project_key)
            prompt_template = self.project_overview_prompts[project_key[0]]
            source_query = prompt_template.replace("{project}", project_key[1])
            if (
                prior
                and prior.get("status") in {"READY", "FAILED", "ADOPTED"}
                and prior.get("source_query") == source_query
            ) or (prior and prior.get("status") in {"DUPLICATE_REVIEW", "ADOPTED"}):
                continue
            pending_projects.append((project_key, candidate, prior))
        # One remote project-page lifecycle per producer tick prevents a large
        # backlog of project folders from delaying the document queue.
        for (workspace, project), candidate, state in pending_projects[:1]:
            prompt_template = self.project_overview_prompts[workspace]
            scope_tag = f"scope:project:{_project_scope_token(project)}"
            source_query = prompt_template.replace("{project}", project)
            page_name = f"Aperçu — {project[:96]} [{_project_scope_token(project)[-6:]}]"
            client = self._client_for(workspace)
            page_id = str(state["page_id"]) if state and state.get("page_id") else None
            operation_id = str(state["operation_id"]) if state and state.get("operation_id") else None
            operation_query = str(state.get("source_query") or source_query) if state else source_query

            if (
                page_id
                and state
                and state.get("source_query") != source_query
                and state.get("status") in {"READY", "FAILED"}
            ):
                try:
                    updated = client.update_knowledge_page_prompt(page_id, source_query)
                except RuntimeError as exc:
                    self._save_project_overview(
                        workspace=workspace, project=project, scope_tag=scope_tag,
                        page_name=page_name, source_query=source_query, page_id=page_id,
                        operation_id=None, status="FAILED", last_error=str(exc),
                    )
                    continue
                self._save_project_overview(
                    workspace=workspace, project=project, scope_tag=scope_tag,
                    page_name=page_name, source_query=source_query, page_id=page_id,
                    operation_id=updated.get("operation_id"),
                    status="BUILDING" if updated.get("operation_id") else "READY",
                )
                break

            if page_id and state and state.get("status") in {"BUILDING", "VERIFYING"}:
                if operation_id:
                    try:
                        operation = client.operation_status(operation_id)
                    except RuntimeError as exc:
                        self._save_project_overview(
                            workspace=workspace, project=project, scope_tag=scope_tag,
                            page_name=page_name, source_query=operation_query, page_id=page_id,
                            operation_id=operation_id, status="VERIFYING", last_error=str(exc),
                        )
                        continue
                    operation_status = str(operation.get("status") or "").casefold()
                    if operation_status in {"pending", "processing"}:
                        self._save_project_overview(
                            workspace=workspace, project=project, scope_tag=scope_tag,
                            page_name=page_name, source_query=operation_query, page_id=page_id,
                            operation_id=operation_id, status="BUILDING",
                        )
                        continue
                    if operation_status == "completed":
                        self._save_project_overview(
                            workspace=workspace, project=project, scope_tag=scope_tag,
                            page_name=page_name, source_query=operation_query, page_id=page_id,
                            operation_id=operation_id, status="READY",
                        )
                        continue
                    if operation_status in {"failed", "cancelled"}:
                        self._save_project_overview(
                            workspace=workspace, project=project, scope_tag=scope_tag,
                            page_name=page_name, source_query=operation_query, page_id=page_id,
                            operation_id=operation_id, status="FAILED",
                            last_error=str(operation.get("error_message") or operation_status),
                        )
                        continue
                else:
                    self._save_project_overview(
                        workspace=workspace, project=project, scope_tag=scope_tag,
                        page_name=page_name, source_query=source_query, page_id=page_id,
                        operation_id=None, status="READY",
                    )
                    continue

            try:
                pages = client.knowledge_base_tree(scope_tag)
            except RuntimeError as exc:
                self._save_project_overview(
                    workspace=workspace, project=project, scope_tag=scope_tag,
                    page_name=page_name, source_query=source_query, page_id=page_id,
                    operation_id=operation_id,
                    status=str(state.get("status") if state else "WAITING_OBSERVATIONS"),
                    last_error=str(exc),
                )
                continue
            if len(pages) > 1:
                self._save_project_overview(
                    workspace=workspace, project=project, scope_tag=scope_tag,
                    page_name=page_name, source_query=source_query, page_id=None,
                    operation_id=None, status="DUPLICATE_REVIEW",
                    last_error="Plusieurs pages portent le tag exact de ce projet.",
                )
                continue
            if pages:
                page_id = str(pages[0].get("id") or "")
                if not page_id.startswith("kp-"):
                    self._save_project_overview(
                        workspace=workspace, project=project, scope_tag=scope_tag,
                        page_name=page_name, source_query=source_query, page_id=None,
                        operation_id=None, status="DUPLICATE_REVIEW",
                        last_error="L’identifiant de page retourné est invalide.",
                    )
                    continue
                self._save_project_overview(
                    workspace=workspace, project=project, scope_tag=scope_tag,
                    page_name=str(pages[0].get("name") or page_name),
                    source_query=source_query,
                    page_id=page_id, operation_id=None,
                    status="ADOPTED",
                )
                continue
            try:
                has_observations = client.has_project_observations(scope_tag)
            except RuntimeError as exc:
                self._save_project_overview(
                    workspace=workspace, project=project, scope_tag=scope_tag,
                    page_name=page_name, source_query=source_query, page_id=None,
                    operation_id=None, status="WAITING_OBSERVATIONS", last_error=str(exc),
                )
                continue
            if not has_observations:
                self._save_project_overview(
                    workspace=workspace, project=project, scope_tag=scope_tag,
                    page_name=page_name, source_query=source_query, page_id=None,
                    operation_id=None, status="WAITING_OBSERVATIONS",
                )
                continue
            # Persist intent first. A timeout after server acceptance is recovered by
            # looking up the exact scope tag and by Hindsight's unique page-name rule.
            self._save_project_overview(
                workspace=workspace, project=project, scope_tag=scope_tag,
                page_name=page_name, source_query=source_query, page_id=None,
                operation_id=None, status="CREATING",
            )
            try:
                created = client.create_knowledge_page(
                    name=page_name, source_query=source_query, scope_tag=scope_tag,
                )
            except RuntimeError as exc:
                if "Hindsight HTTP 409:" in str(exc):
                    try:
                        pages = client.knowledge_base_tree(scope_tag)
                    except RuntimeError:
                        pages = []
                    if len(pages) == 1 and str(pages[0].get("id") or "").startswith("kp-"):
                        self._save_project_overview(
                            workspace=workspace, project=project, scope_tag=scope_tag,
                            page_name=str(pages[0].get("name") or page_name), source_query=source_query,
                            page_id=str(pages[0]["id"]), operation_id=None, status="READY",
                        )
                        continue
                self._save_project_overview(
                    workspace=workspace, project=project, scope_tag=scope_tag,
                    page_name=page_name, source_query=source_query, page_id=None,
                    operation_id=None, status="CREATING", last_error=str(exc),
                )
                continue
            self._save_project_overview(
                workspace=workspace, project=project, scope_tag=scope_tag,
                page_name=page_name, source_query=source_query,
                page_id=created["page_id"], operation_id=created.get("operation_id"),
                status="BUILDING" if created.get("operation_id") else "READY",
            )
            # Advance only one project in this reconciliation pass.
            break

    def _metadata_preflight(
        self,
        source: Path,
        *,
        source_sha256: str,
        workspace: str,
        allow_extract: bool = True,
    ):
        source_kind = self._source_kind_for(workspace)
        metadata_profile = self.metadata_profiles.get(workspace)
        if source.suffix.casefold() != ".pdf":
            if not allow_extract:
                return PreflightResult(
                    profile=metadata_profile or "affaires", status="not_run", fields={}
                )
            return preflight_pdf_metadata(
                source,
                source_kind=source_kind,
                workspace=workspace,
                profile=metadata_profile,
            )
        cache_key = self._preflight_cache_key(source_sha256, workspace)
        try:
            source_path = source.relative_to(self.roots[workspace]).as_posix()
        except (KeyError, ValueError):
            source_path = None
        connection = self._connect()
        try:
            row = connection.execute(
                f"SELECT result_json FROM {PREFLIGHT_TABLE} WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
        finally:
            connection.close()
        if row is not None:
            try:
                cached = json.loads(str(row["result_json"]))
                if isinstance(cached, dict):
                    result = PreflightResult.from_dict(cached)
                    if result.status != "extractor_unavailable":
                        if source_path is not None:
                            self._link_preflight_source(
                                workspace, source_path, source_sha256, cache_key
                            )
                        return result
            except (TypeError, ValueError, KeyError):
                pass

        if not allow_extract:
            return PreflightResult(
                profile=metadata_profile or "affaires", status="not_run", fields={}
            )

        result = preflight_pdf_metadata(
            source,
            source_kind=source_kind,
            workspace=workspace,
            profile=metadata_profile,
        )
        self._save_preflight_result(
            source, source_sha256=source_sha256, workspace=workspace, result=result
        )
        return result

    def _link_preflight_source(
        self, workspace: str, source_path: str, source_sha256: str, cache_key: str
    ) -> None:
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    f"""
                    INSERT INTO {PREFLIGHT_SOURCE_TABLE}(
                        workspace, source_path, source_sha256, cache_key, updated_at
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(workspace, source_path) DO UPDATE SET
                        source_sha256=excluded.source_sha256,
                        cache_key=excluded.cache_key,
                        updated_at=excluded.updated_at
                    """,
                    (workspace, source_path, source_sha256, cache_key, _utc_now()),
                )
        finally:
            connection.close()

    def _bind_document_note(
        self, workspace: str, source_path: str, source_sha256: str, document_id: str
    ) -> None:
        """Bind an existing manual note to the stable producer identity and current path."""
        connection = self._connect()
        try:
            with connection:
                by_identity = connection.execute(
                    f"SELECT * FROM {DOCUMENT_NOTES_TABLE} WHERE workspace = ? AND document_id = ?",
                    (workspace, document_id),
                ).fetchone()
                at_path = connection.execute(
                    f"SELECT * FROM {DOCUMENT_NOTES_TABLE} WHERE workspace = ? AND source_path = ?",
                    (workspace, source_path),
                ).fetchone()
                selected = by_identity or at_path
                if selected is None:
                    return
                note = str(selected["note"])
                created_at = str(selected["created_at"])
                updated_at = str(selected["updated_at"])
                if by_identity is not None and at_path is not None and by_identity["source_path"] != source_path:
                    # If a user left a note at the new path before identity
                    # reconciliation, keep the most recently edited one.
                    if str(at_path["updated_at"]) > updated_at:
                        note = str(at_path["note"])
                        created_at = str(at_path["created_at"])
                        updated_at = str(at_path["updated_at"])
                    connection.execute(
                        f"DELETE FROM {DOCUMENT_NOTES_TABLE} WHERE workspace = ? AND source_path = ?",
                        (workspace, source_path),
                    )
                connection.execute(
                    f"DELETE FROM {DOCUMENT_NOTES_TABLE} WHERE workspace = ? AND document_id = ?",
                    (workspace, document_id),
                )
                connection.execute(
                    f"""INSERT INTO {DOCUMENT_NOTES_TABLE}(
                        workspace, source_path, document_id, source_sha256, note, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (workspace, source_path, document_id, source_sha256, note, created_at, updated_at),
                )
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
        """Require identical source bytes and path across consecutive reconciles."""
        if self.settle_observations <= 1:
            return True
        source_fingerprint = hashlib.sha256(
            f"{candidate.relative_path}\0{candidate.source_sha256}".encode("utf-8")
        ).hexdigest()
        connection = self._connect()
        try:
            row = connection.execute(
                f"SELECT fingerprint, observations FROM {OBSERVATION_TABLE} "
                "WHERE hindsight_document_id = ?",
                (candidate.hindsight_document_id,),
            ).fetchone()
            observations = (
                int(row["observations"]) + 1
                if row is not None and row["fingerprint"] == source_fingerprint
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
                        source_fingerprint,
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
        updated_at: str | None = None,
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
                        updated_at or _utc_now(),
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
        run_preflight: bool = True,
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
        source_kind = self._source_kind_for(workspace)
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
            source_sha256 = self._source_sha256(workspace, relative_path, source)

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
        self._bind_document_note(workspace, relative_path, source_sha256, document_id)

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
        declared_document_family = _metadata_value(card.get("document_family"))
        if declared_document_family is not None:
            metadata["document_family"] = declared_document_family
        filename_revision_hint = _metadata_value(card.get("filename_revision_hint"))
        if filename_revision_hint is not None:
            metadata["filename_revision_hint"] = filename_revision_hint
        if source_kind:
            metadata["source_kind"] = source_kind
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

        preflight = self._metadata_preflight(
            source,
            source_sha256=source_sha256,
            workspace=workspace,
            allow_extract=run_preflight,
        )
        metadata["metadata_preflight_profile"] = preflight.profile
        metadata["metadata_preflight_status"] = preflight.status
        metadata["metadata_preflight_text_source"] = preflight.text_source
        classification = preflight.document_classification
        metadata["metadata_preflight_classification_status"] = (
            classification.status if classification is not None else "not_classified"
        )
        if classification is not None:
            metadata["metadata_preflight_classification"] = json.dumps(
                classification.__dict__,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            # Keep automated classification visibly provisional; it must not
            # overwrite canonical fields supplied by the source card or labels.
            metadata["metadata_preflight_document_family_candidate"] = classification.family
            metadata["metadata_preflight_document_type_candidate"] = classification.document_type
        if preflight.document_title_candidate is not None:
            title_candidate = preflight.document_title_candidate
            metadata["metadata_preflight_document_title_candidate"] = title_candidate.value
            metadata["metadata_preflight_document_title_evidence"] = json.dumps(
                {
                    "value": title_candidate.value,
                    "page": title_candidate.page,
                    "evidence": title_candidate.evidence,
                    "status": "candidate_unconfirmed",
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        if preflight.document_summary_candidate is not None:
            summary_candidate = preflight.document_summary_candidate
            metadata["metadata_preflight_summary_candidate"] = summary_candidate.value
            metadata["metadata_preflight_summary_evidence"] = json.dumps(
                {
                    "value": summary_candidate.value,
                    "page": summary_candidate.page,
                    "evidence": summary_candidate.evidence,
                    "source": summary_candidate.source,
                    "status": "extractive_preview",
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        for metadata_key, candidates in (
            ("metadata_preflight_corps_etat_candidates", preflight.corps_etat_candidates),
            ("metadata_preflight_sujets_techniques_candidates", preflight.sujet_technique_candidates),
        ):
            if candidates:
                metadata[metadata_key] = json.dumps(
                    [candidate.__dict__ for candidate in candidates],
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
        if preflight.issuer_candidates:
            # These are review cues only. Never promote them into the canonical
            # document_emetteur field without an explicit source label.
            metadata["metadata_preflight_issuer_candidates"] = json.dumps(
                [candidate.__dict__ for candidate in preflight.issuer_candidates],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        if preflight.fields:
            metadata["metadata_preflight_evidence"] = json.dumps(
                {key: value.__dict__ for key, value in preflight.fields.items()},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            for key, candidate in preflight.fields.items():
                # Keep source-read values in their agreed Hindsight fields;
                # cartouche values remain separate namespaced hints.
                target_key = {
                    "document_date": "document_date",
                    "pdf_creation_date": "document_creation_date",
                    "index": "document_indice",
                    "issuer": "document_emetteur",
                    "recipient": "document_destinataire",
                }[key]
                metadata.setdefault(target_key, candidate.value)
                if key == "pdf_creation_date":
                    metadata.setdefault("document_creation_date_source", "pdf_info_creation_date")
        if preflight.unresolved:
            metadata["metadata_preflight_unresolved"] = ",".join(preflight.unresolved)

        context_parts = [f"{workspace} professional source document"]
        if metadata.get("title"):
            context_parts.append(f"title={metadata['title']}")
        if preflight.document_title_candidate is not None:
            context_parts.append(
                "document title candidate="
                f"{preflight.document_title_candidate.value} "
                f"(page={preflight.document_title_candidate.page}; status=candidate_unconfirmed)"
            )
        if preflight.document_summary_candidate is not None:
            context_parts.append(
                "extractive document preview="
                f"{preflight.document_summary_candidate.value} "
                f"(page={preflight.document_summary_candidate.page}; not an AI summary)"
            )
        if metadata.get("document_type"):
            context_parts.append(f"type={metadata['document_type']}")
        if metadata.get("document_family"):
            context_parts.append(f"document family={metadata['document_family']}")
        if classification is not None:
            context_parts.append(
                "preflight classification candidate="
                f"{classification.document_type} (family={classification.family}; "
                f"status={classification.status})"
            )
            if classification.document_type in {"Plan", "Carnet de plans"}:
                plan_identity = ["document = plan"]
                for label, key in (
                    ("titre", "metadata_preflight_document_title_candidate"),
                    ("indice", "document_indice"),
                    ("date d’émission", "document_date"),
                    ("émetteur", "document_emetteur"),
                ):
                    if metadata.get(key):
                        plan_identity.append(f"{label}={metadata[key]}")
                context_parts.append("plan identity=" + "; ".join(plan_identity))
        if preflight.corps_etat_candidates:
            context_parts.append(
                "preflight construction trade candidates="
                + ", ".join(candidate.value for candidate in preflight.corps_etat_candidates)
            )
        if preflight.sujet_technique_candidates:
            context_parts.append(
                "preflight technical subject candidates="
                + ", ".join(candidate.value for candidate in preflight.sujet_technique_candidates)
            )
        if metadata.get("document_creation_date"):
            context_parts.append(
                "PDF creation metadata date="
                f"{metadata['document_creation_date']} (not the document issue date)"
            )
        if metadata.get("phase_hint"):
            context_parts.append(f"phase hint={metadata['phase_hint']}")
        if metadata.get("project_hint"):
            context_parts.append(f"project hint={metadata['project_hint']}")
        if metadata.get("folder_ancestry"):
            context_parts.append(f"folder ancestry={metadata['folder_ancestry']}")
        context = "; ".join(context_parts)

        tags = [f"workspace:{_tag_value(workspace)}"]
        if source_kind:
            tags.append(f"source:{source_kind}")
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
            preflight_loaded=preflight.status != "not_run",
        )

    def _poll(self, row: dict[str, Any]) -> dict[str, Any]:
        with self._operation_poll_lock:
            # Re-read after waiting for the lock so a stale poll cannot overwrite
            # a newer submission for the same document.
            operation_id = row.get("operation_id")
            if operation_id:
                current = self._states().get(str(row.get("hindsight_document_id") or ""))
                if current is not None:
                    if current.get("operation_id") != operation_id:
                        return current
                    if current.get("status") not in ACTIVE_STATUSES | {"VERIFY"}:
                        return current
                    row = current
            return self._poll_locked(row)

    def _poll_locked(self, row: dict[str, Any]) -> dict[str, Any]:
        operation_id = row.get("operation_id")
        if not operation_id:
            return row
        try:
            payload = self._client_for(str(row.get("workspace") or "")).operation_status(str(operation_id))
        except RuntimeError as exc:
            row["last_error"] = str(exc)
            row["_remote_check_succeeded"] = False
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
            if self.processing_queue is not None:
                self.processing_queue.set_status(
                    str(row["workspace"]), str(row["document_id"]),
                    preflight_status="ANALYZED", hindsight_status="VERIFY",
                    operation_id=str(operation_id), error=row["last_error"],
                )
            return row

        row["_remote_check_succeeded"] = True
        mapped = str(payload["status"]).upper()
        last_error = (
            str(payload.get("error_message"))
            if payload.get("error_message") is not None
            else None
        )
        if mapped == "COMPLETED":
            # File conversion can finish before Hindsight's asynchronous retain
            # makes the document readable. Treat operation completion as
            # provisional until the exact document is visible in this bank.
            document_id = str(row.get("hindsight_document_id") or "")
            try:
                retained = self._client_for(str(row.get("workspace") or "")).get_document(document_id)
            except RuntimeError as exc:
                last_error = f"Hindsight operation completed but document read-back failed: {exc}"
                # A 404 immediately after conversion is the known async retain
                # gap. Keep the operation attached and check again next pass;
                # other failures need an explicit human verification.
                mapped = "VERIFYING" if "Hindsight HTTP 404:" in str(exc) else "VERIFY"
            else:
                if not isinstance(retained, dict) or retained.get("id") != document_id:
                    mapped = "VERIFY"
                    last_error = "Hindsight operation completed but the exact document was not confirmed"
                else:
                    row["_document_readback"] = retained
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
        if self.processing_queue is not None:
            queue_status = (
                "MEMORIZED" if mapped == "COMPLETED"
                else "FAILED" if mapped in {"FAILED", "CANCELLED", "OCR_NEEDED"}
                else "VERIFYING" if mapped == "VERIFYING"
                else "MEMORIZING" if mapped in ACTIVE_STATUSES
                else "VERIFY" if mapped == "VERIFY"
                else "VERIFY" if mapped not in {"QUEUED", "STALE", "BLOCKED", "ARCHIVED"}
                else "QUEUED"
            )
            self.processing_queue.set_status(
                str(row["workspace"]), str(row["document_id"]),
                preflight_status="ANALYZED", hindsight_status=queue_status,
                operation_id=str(operation_id) if operation_id else None,
                error=last_error,
                clear_error=last_error is None,
            )
            if mapped == "COMPLETED":
                queue_item = self.processing_queue.get_item(str(row["workspace"]), str(row["document_id"]))
                if queue_item and queue_item.get("ocr_status") == "SUBMITTED":
                    self.processing_queue.set_ocr_status(
                        str(row["workspace"]), str(row["document_id"]), status="DONE"
                    )
        return row

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime | None:
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _recover_submission(self, row: dict[str, Any]) -> dict[str, Any]:
        """Recover the remote operation ID before an uncertain upload can be retried."""
        workspace = str(row.get("workspace") or "")
        try:
            operations = self._client_for(workspace).list_file_retain_operations(limit=100)
        except (AttributeError, OSError, RuntimeError) as exc:
            row["_remote_check_succeeded"] = False
            if self.processing_queue is not None:
                self.processing_queue.set_status(
                    workspace, str(row["document_id"]),
                    preflight_status="ANALYZED", hindsight_status="VERIFY",
                    operation_id=None,
                    error=f"Envoi antérieur à vérifier ; lecture des opérations Hindsight impossible : {exc}",
                )
            return row

        row["_remote_check_succeeded"] = True
        attempt_at = self._parse_timestamp(row.get("updated_at"))
        matches: list[dict[str, Any]] = []
        for operation in operations:
            operation_type = operation.get("operation_type") or operation.get("task_type")
            if (
                operation_type != "file_convert_retain"
                or operation.get("document_id") != row.get("hindsight_document_id")
            ):
                continue
            created_at = self._parse_timestamp(operation.get("created_at"))
            # Allow a small tolerance for timestamp serialization and clock skew.
            if attempt_at is not None and created_at is not None:
                if created_at.timestamp() < attempt_at.timestamp() - 5:
                    continue
            matches.append(operation)

        if len(matches) == 1 and isinstance(matches[0].get("id"), str) and matches[0]["id"]:
            operation_id = str(matches[0]["id"])
            try:
                tags = json.loads(str(row.get("tags_json") or "[]"))
            except json.JSONDecodeError:
                tags = []
            self._save(
                None,
                hindsight_document_id=str(row["hindsight_document_id"]),
                document_id=str(row["document_id"]),
                workspace=workspace,
                source_path=str(row["source_path"]),
                source_sha256=str(row["source_sha256"]),
                fingerprint=str(row["fingerprint"]),
                operation_id=operation_id,
                status="SUBMITTED",
                tags=tags,
            )
            row.update(status="SUBMITTED", operation_id=operation_id, last_error=None)
            if self.processing_queue is not None:
                self.processing_queue.set_status(
                    workspace, str(row["document_id"]),
                    preflight_status="ANALYZED", hindsight_status="MEMORIZING",
                    operation_id=operation_id, clear_error=True,
                )
            return row

        # A prior OCR replacement may have been accepted before a producer crash,
        # or the document may already contain that exact OCR artifact from an
        # earlier successful retain. In that case the operation can fall outside
        # Hindsight's recent-operation window. Confirm the exact stored bytes and
        # their source metadata before resolving the uncertain local intent; never
        # submit a second retain as a recovery action.
        queue_item = (
            self.processing_queue.get_item(workspace, str(row["document_id"]))
            if self.processing_queue is not None else None
        )
        if (
            queue_item is not None
            and queue_item.get("hindsight_status") == "VERIFY"
            and queue_item.get("request_action") == "replace_ocr"
            and bool(queue_item.get("ocr_replace_approved"))
            and str(queue_item.get("ocr_status") or "").upper() == "READY"
            and queue_item.get("source_sha256") == row.get("source_sha256")
            and queue_item.get("ocr_preflight_source_sha256") == row.get("source_sha256")
            and queue_item.get("source_path") == row.get("source_path")
            and queue_item.get("user_decision") != "DO_NOT_SEND"
            and self.ocr_processor is not None
        ):
            artifact_name = str(queue_item.get("ocr_filename") or "")
            cache_dir = Path(self.ocr_processor.cache_dir)
            if (
                artifact_name
                and Path(artifact_name).name == artifact_name
                and artifact_name.endswith(".md")
            ):
                artifact_path = cache_dir / artifact_name
                try:
                    artifact_hash = _sha256(artifact_path) if artifact_path.is_file() else None
                    existing = self._client_for(workspace).get_document(
                        str(row["hindsight_document_id"])
                    )
                except RuntimeError as exc:
                    if "Hindsight HTTP 404:" not in str(exc):
                        row["_remote_check_succeeded"] = False
                except OSError:
                    artifact_hash = None
                    existing = None
                else:
                    metadata = existing.get("document_metadata")
                    tags = existing.get("tags")
                    if (
                        isinstance(metadata, dict)
                        and existing.get("id") == row.get("hindsight_document_id")
                        and existing.get("content_hash") == artifact_hash
                        and metadata.get("source_sha256") == row.get("source_sha256")
                        and metadata.get("ocr_source_sha256") == row.get("source_sha256")
                        and metadata.get("ocr_artifact_name") == artifact_name
                        and metadata.get("ocr_derived_from") == row.get("source_path")
                        and isinstance(tags, list)
                        and "ocr:complete" in tags
                    ):
                        try:
                            stored_tags = json.loads(str(row.get("tags_json") or "[]"))
                        except json.JSONDecodeError:
                            stored_tags = []
                        self._save(
                            None,
                            hindsight_document_id=str(row["hindsight_document_id"]),
                            document_id=str(row["document_id"]),
                            workspace=workspace,
                            source_path=str(row["source_path"]),
                            source_sha256=str(row["source_sha256"]),
                            fingerprint=str(row["fingerprint"]),
                            operation_id=None,
                            status="COMPLETED",
                            tags=stored_tags if isinstance(stored_tags, list) else [],
                        )
                        row.update(status="COMPLETED", operation_id=None, last_error=None)
                        row["_document_readback"] = existing
                        if self.processing_queue is not None:
                            self.processing_queue.set_status(
                                workspace, str(row["document_id"]),
                                preflight_status="ANALYZED",
                                hindsight_status="MEMORIZED",
                                clear_operation_id=True,
                                clear_error=True,
                            )
                            self.processing_queue.set_ocr_status(
                                workspace, str(row["document_id"]), status="DONE"
                            )
                            self.processing_queue.consume_ocr_replacement_approval(
                                workspace, str(row["document_id"])
                            )
                        return row

        if len(matches) > 1:
            reason = "Plusieurs opérations Hindsight correspondent à cet envoi ; contrôle manuel requis."
        else:
            reason = "Aucune opération Hindsight retrouvée pour l’envoi en cours."
        updated_at = self._parse_timestamp(row.get("updated_at"))
        expired = (
            updated_at is not None
            and (datetime.now(timezone.utc) - updated_at).total_seconds()
            >= SUBMISSION_RECOVERY_GRACE_SECONDS
        )
        if len(matches) > 1:
            try:
                tags = json.loads(str(row.get("tags_json") or "[]"))
            except json.JSONDecodeError:
                tags = []
            self._save(
                None,
                hindsight_document_id=str(row["hindsight_document_id"]),
                document_id=str(row["document_id"]),
                workspace=workspace,
                source_path=str(row["source_path"]),
                source_sha256=str(row["source_sha256"]),
                fingerprint=str(row["fingerprint"]),
                operation_id=None,
                status="VERIFY",
                last_error=reason,
                tags=tags,
            )
            row.update(status="VERIFY", operation_id=None, last_error=reason)
        elif self.processing_queue is not None:
            self.processing_queue.set_status(
                workspace, str(row["document_id"]),
                preflight_status="ANALYZED", hindsight_status="VERIFY",
                operation_id=None,
                error=(
                    f"{reason} Recherche maintenue en arrière-plan après le délai de récupération."
                    if expired else reason
                ),
            )
        return row

    def reconcile(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        states = self._states()
        for key, row in list(states.items()):
            if row.get("status") == "SUBMITTING":
                if key in self._submission_inflight:
                    continue
                row = self._recover_submission(row)
                states[key] = row
            if row.get("status") in ACTIVE_STATUSES:
                if row.get("status") != "SUBMITTING":
                    states[key] = self._poll(row)

        candidates: dict[str, ProducerCandidate] = {}
        candidate_cards: dict[str, dict[str, Any]] = {}
        collided_candidate_ids: set[str] = set()
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
                        run_preflight=self.processing_queue is None,
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
                    previous = candidates.get(candidate.hindsight_document_id)
                    if previous is not None and previous.workspace != candidate.workspace:
                        collided_candidate_ids.add(candidate.hindsight_document_id)
                        candidates.pop(candidate.hindsight_document_id, None)
                        previous_card = candidate_cards.pop(candidate.hindsight_document_id, None)
                        for collision_card in (previous_card, card):
                            if collision_card is not None:
                                collision_card["hindsight_status"] = "VAULT_ID_COLLISION"
                                collision_card["hindsight_last_error"] = "document identity is shared across vaults"
                    elif candidate.hindsight_document_id not in collided_candidate_ids:
                        candidates[candidate.hindsight_document_id] = candidate
                        candidate_cards[candidate.hindsight_document_id] = card

        queue_order: dict[tuple[str, str], int] = {}
        queue_rows: dict[tuple[str, str], dict[str, Any]] = {}
        if self.processing_queue is not None:
            for key, candidate in candidates.items():
                row = states.get(key)
                sync_status = str(row.get("status") or "") if row else ""
                queue_status = (
                    "MEMORIZED" if sync_status == "COMPLETED"
                    else "VERIFYING" if sync_status == "VERIFYING"
                    else "UNAVAILABLE" if sync_status == "UNAVAILABLE"
                    else "VERIFY" if sync_status in {"SUBMITTING", "VERIFY"}
                    else "MEMORIZING" if sync_status in ACTIVE_STATUSES
                    else "FAILED" if sync_status in {"FAILED", "CANCELLED", "OCR_NEEDED", "SUBMIT_ERROR"}
                    else "QUEUED" if sync_status == "QUEUED"
                    else "NOT_SENT"
                )
                queue_row = self.processing_queue.upsert_candidate(
                    workspace=candidate.workspace,
                    document_id=candidate.document_id,
                    source_path=candidate.relative_path,
                    source_sha256=candidate.source_sha256,
                    preflight_status=(
                        "ANALYZED"
                        if sync_status in {"COMPLETED", *ACTIVE_STATUSES, "QUEUED", "VERIFY", "UNAVAILABLE"}
                        else "TO_PROCESS"
                    ),
                    hindsight_status=queue_status,
                )
                # The queue may predate the producer's durable sync state (for
                # example, a failed Hindsight submission while the Cockpit was
                # offline). Keep its visible status aligned without retrying or
                # resubmitting anything.
                queue_status_by_sync_status = {
                    "COMPLETED": "MEMORIZED",
                    "FAILED": "FAILED",
                    "CANCELLED": "FAILED",
                    "OCR_NEEDED": "FAILED",
                    "SUBMIT_ERROR": "FAILED",
                    "QUEUED": "QUEUED",
                    "SUBMITTING": "VERIFY",
                    "VERIFY": "VERIFY",
                    "VERIFYING": "VERIFYING",
                    "UNAVAILABLE": "UNAVAILABLE",
                }
                if sync_status == "UNAVAILABLE":
                    projected_status = "UNAVAILABLE"
                elif sync_status == "VERIFYING":
                    projected_status = "VERIFYING"
                elif sync_status in {"SUBMITTING", "VERIFY"}:
                    projected_status = "VERIFY"
                elif sync_status in ACTIVE_STATUSES:
                    projected_status = "MEMORIZING"
                else:
                    projected_status = queue_status_by_sync_status.get(sync_status)
                retry_pending = (
                    queue_row.get("hindsight_status") == "QUEUED"
                    and sync_status in {"FAILED", "CANCELLED", "OCR_NEEDED", "SUBMIT_ERROR"}
                )
                # An explicitly approved OCR replacement is also durable retry
                # intent. Preserve OCR_READY here: projecting the old SUBMIT_ERROR
                # back onto the queue would hide the approval, and the submission
                # loop would then skip the terminal sync row forever.
                approved_ocr_replacement = (
                    sync_status == "SUBMIT_ERROR"
                    and row is not None
                    and row.get("last_error")
                    == "Hindsight document already exists; OCR replacement requires operator review"
                    and not row.get("operation_id")
                    and queue_row.get("hindsight_status") in {"OCR_READY", "VERIFY", "FAILED"}
                    and bool(queue_row.get("ocr_replace_approved"))
                    and queue_row.get("request_action") == "replace_ocr"
                    and queue_row.get("ocr_status") == "READY"
                    and str(queue_row.get("ocr_filename") or "").endswith(".md")
                    and queue_row.get("ocr_preflight_source_sha256") == candidate.source_sha256
                    and queue_row.get("user_decision") != "DO_NOT_SEND"
                )
                if approved_ocr_replacement and queue_row.get("hindsight_status") != "OCR_READY":
                    # A previous reconcile may already have projected the stale
                    # SUBMIT_ERROR into VERIFY/FAILED. Restore the approved state
                    # before the submission loop, but only for this exact OCR/source.
                    self.processing_queue.set_status(
                        candidate.workspace,
                        candidate.document_id,
                        preflight_status="ANALYZED",
                        hindsight_status="OCR_READY",
                        clear_operation_id=True,
                        clear_error=True,
                    )
                    refreshed = self.processing_queue.get_item(
                        candidate.workspace, candidate.document_id
                    )
                    if refreshed is not None:
                        queue_row = refreshed
                        queue_rows[(candidate.workspace, candidate.document_id)] = refreshed
                retry_pending = retry_pending or approved_ocr_replacement
                if projected_status is not None and not retry_pending:
                    projected_error = str(row.get("last_error") or "")[:1200]
                    clear_operation = sync_status in {
                        "COMPLETED", "FAILED", "CANCELLED", "OCR_NEEDED", "SUBMIT_ERROR"
                    }
                    if (
                        queue_row.get("preflight_status") != "ANALYZED"
                        or queue_row.get("hindsight_status") != projected_status
                        or (queue_row.get("error") or "") != projected_error
                        or (clear_operation and queue_row.get("operation_id") is not None)
                    ):
                        self.processing_queue.set_status(
                            candidate.workspace,
                            candidate.document_id,
                            preflight_status="ANALYZED",
                            hindsight_status=projected_status,
                            operation_id=row.get("operation_id"),
                            error=projected_error,
                            clear_operation_id=clear_operation,
                            clear_error=not projected_error,
                        )
                        refreshed = self.processing_queue.get_item(
                            candidate.workspace, candidate.document_id
                        )
                        if refreshed is not None:
                            queue_row = refreshed
                            queue_rows[(candidate.workspace, candidate.document_id)] = refreshed
                # A newly observed source version must pass the settling checks before
                # the row becomes eligible for submission.
                # upsert_candidate invalidates preflight only when this source
                # version changes (or reappears). Repeated reconciliation must
                # preserve an in-progress or completed independent preflight.
                if queue_row["hindsight_status"] == "MODIFIED" and sync_status in {"SUBMITTING", "VERIFY"}:
                    self.processing_queue.set_status(
                        candidate.workspace, candidate.document_id,
                        hindsight_status="VERIFY",
                        error="Le fichier a changé alors que l’issue de l’envoi Hindsight reste incertaine.",
                    )
            # Explicit Cockpit requests perform only a remote status/operation lookup.
            # They never call retain_file; uncertain cases remain VERIFY until resolved.
            for request in self.processing_queue.verification_requests():
                workspace = str(request["workspace"])
                document_id = str(request["document_id"])
                key = next(
                    (
                        state_key for state_key, state in states.items()
                        if state.get("workspace") == workspace
                        and state.get("document_id") == document_id
                    ),
                    None,
                )
                if key is None:
                    continue
                row = states[key]
                if row.get("status") != "VERIFY":
                    continue
                if row.get("operation_id"):
                    checked = self._poll(row)
                else:
                    checked = self._recover_submission(row)
                    if checked.get("status") in ACTIVE_STATUSES and checked.get("operation_id"):
                        checked = self._poll(checked)
                states[key] = checked
                if checked.get("_remote_check_succeeded") is True:
                    self.processing_queue.clear_verification_request(
                        workspace, document_id, str(request["verification_requested_at"])
                    )
            queue_snapshot = self.processing_queue.list_items(include_memorized=True)
            queue_order = {
                (str(item["workspace"]), str(item["document_id"])): index
                for index, item in enumerate(queue_snapshot["items"])
            }
            queue_rows = {
                (str(item["workspace"]), str(item["document_id"])): item
                for item in queue_snapshot["items"]
            }
        self._advance_ocr(candidates)
        if self.processing_queue is not None:
            queue_snapshot = self.processing_queue.list_items(include_memorized=True)
            queue_rows = {
                (str(item["workspace"]), str(item["document_id"])): item
                for item in queue_snapshot["items"]
            }

        quality_states = self._quality_states()
        projected_tags = {key: candidate.tags for key, candidate in candidates.items()}
        ordered_candidates = sorted(
            candidates.items(),
            key=lambda pair: queue_order.get(
                (pair[1].workspace, pair[1].document_id), 2**31
            ),
        )
        for key, candidate in ordered_candidates:
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
                client = self._client_for(candidate.workspace)
                cached_readback = row.get("_document_readback") if row is not None else None
                retained = (
                    cached_readback
                    if isinstance(cached_readback, dict)
                    else client.get_document(key)
                )
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
                        client.update_document_tags(key, updated_tags)
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
        unavailable_retry_keys = {
            key for key, row in states.items()
            if row.get("status") == "UNAVAILABLE" and key in candidates
        }

        dispatcher_enabled = bool(
            self.processing_queue is not None
            and self._submission_dispatcher_thread is not None
            and self._submission_dispatcher_thread.is_alive()
        )
        if dispatcher_enabled:
            with self._submission_cache_lock:
                self._submission_candidates = dict(candidates)
            self.wake_submission_dispatcher()

        for key, candidate in ([] if dispatcher_enabled else ordered_candidates):
            # Keep the single Hindsight submission lane on the document that
            # observed the last connection refusal until that request succeeds.
            if unavailable_retry_keys and key not in unavailable_retry_keys:
                continue
            tags = projected_tags.get(key, candidate.tags)
            row = states.get(key)
            queue_row = queue_rows.get((candidate.workspace, candidate.document_id))
            ocr_submission = bool(
                queue_row is not None
                and (
                    queue_row.get("hindsight_status") == "OCR_READY"
                    or (queue_row.get("ocr_status") == "READY" and queue_row.get("ocr_filename"))
                )
            )
            if (
                ocr_submission
                and queue_row is not None
                and queue_row.get("ocr_preflight_source_sha256") != candidate.source_sha256
            ):
                # The OCR text must have its own metadata preflight persisted for
                # this exact source version before Hindsight can receive it.
                continue
            if queue_row is not None and queue_row.get("user_decision") == "DO_NOT_SEND":
                continue
            if queue_row is not None and queue_row.get("hindsight_status") in {"OCR_QUEUED", "OCR_PROCESSING"}:
                continue
            if (
                queue_row is not None
                and queue_row.get("hindsight_status") == "FAILED"
                and queue_row.get("ocr_status") == "FAILED"
            ):
                # OCR failure is terminal for the automatic chain. Never try to
                # memorize the unchanged, unreadable source behind that failure.
                continue
            if (
                self.processing_queue is not None
                and queue_row is not None
                and queue_row.get("hindsight_status") in {"QUEUED", "OCR_READY"}
                and row is not None
                and row.get("status") in {"FAILED", "CANCELLED", "OCR_NEEDED", "SUBMIT_ERROR"}
            ):
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
                row.update(status="QUEUED", operation_id=None, last_error=None)
                states[key] = row
            # Active rows were already polled exactly once at the start of this reconcile.
            # Never double-poll an operation in the same pass: a fast PENDING -> COMPLETED
            # transition must not also trigger a replacement submit before the next snapshot.
            if row and row.get("status") in ACTIVE_STATUSES:
                continue

            # An uncertain remote outcome blocks replacement content under the same
            # stable identity until an operator resolves it.
            if row and row.get("status") == "VERIFY":
                continue

            stable_content_move = bool(
                row
                and row.get("status") == "COMPLETED"
                and row.get("source_sha256") == candidate.source_sha256
                and row.get("source_path") != candidate.relative_path
            )
            if stable_content_move:
                try:
                    self._client_for(candidate.workspace).update_document_tags(key, tags)
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
                        self._client_for(candidate.workspace).update_document_tags(key, tags)
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
                if row.get("status") in {"FAILED", "CANCELLED", "OCR_NEEDED", "SUBMIT_ERROR", "VERIFY"}:
                    continue

            if not self._observe_stability(candidate):
                settling += 1
                if self.processing_queue is not None:
                    self.processing_queue.set_status(
                        candidate.workspace, candidate.document_id,
                        preflight_status="STABILIZING", hindsight_status="MODIFIED",
                    )
                continue

            if self.processing_queue is not None:
                queue_row = queue_rows.get((candidate.workspace, candidate.document_id)) or {}
                if queue_row.get("preflight_status") != "ANALYZED":
                    if self.processing_queue.is_item_paused(
                        candidate.workspace, candidate.document_id, "preflight"
                    ):
                        continue
                    # The preflight worker consumes this shared row independently;
                    # Hindsight waits only for this document's ANALYZED status.
                    continue

            if self.processing_queue is not None:
                waiting_status = (
                    "OCR_READY" if ocr_submission
                    else "MEMORIZING" if row and row.get("status") in ACTIVE_STATUSES
                    else "QUEUED"
                )
                self.processing_queue.set_status(
                    candidate.workspace, candidate.document_id,
                    preflight_status="ANALYZED", hindsight_status=waiting_status,
                )
                if queue_row is not None:
                    queue_row["hindsight_status"] = waiting_status

            # A single outstanding Hindsight operation gives both vaults one
            # deterministic submission lane. Polling continues above while paused.
            if (
                (self.processing_queue is not None and self.processing_queue.is_item_paused(
                    candidate.workspace, candidate.document_id, "hindsight"
                ))
                or any(state.get("status") in ACTIVE_STATUSES for state in states.values())
            ):
                continue

            if self.processing_queue is not None and not candidate.preflight_loaded:
                # Non-PDFs have no PDF metadata preflight cache; this is a cheap
                # no-op result. PDF extraction belongs exclusively to the worker.
                if candidate.source_path.suffix.casefold() == ".pdf":
                    continue
                card = candidate_cards.get(key)
                if card is None:
                    continue
                self.processing_queue.set_status(
                    candidate.workspace, candidate.document_id,
                    preflight_status="ANALYZING",
                )
                preflight_error: str | None = None
                try:
                    analyzed = self._candidate(
                        card,
                        current_paths=current_paths,
                        claimed_auto_ids=claimed_auto_ids,
                        run_preflight=True,
                    )
                except (OSError, ProjectReclassificationRequired) as exc:
                    analyzed = None
                    preflight_error = str(exc)
                if analyzed is None or analyzed.source_sha256 != candidate.source_sha256:
                    self.processing_queue.set_status(
                        candidate.workspace, candidate.document_id,
                        preflight_status="FAILED" if preflight_error else "STABILIZING",
                        hindsight_status="FAILED" if preflight_error else "MODIFIED",
                        error=preflight_error,
                    )
                    continue
                candidate = analyzed
                candidates[key] = candidate
                projected_tags[key] = candidate.tags
                tags = candidate.tags
                self.processing_queue.set_status(
                    candidate.workspace, candidate.document_id,
                    preflight_status="ANALYZED", clear_error=True,
                )

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
                if self.processing_queue is not None:
                    self.processing_queue.set_status(
                        candidate.workspace, candidate.document_id,
                        preflight_status="ANALYZED", hindsight_status="QUEUED",
                        operation_id=None,
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

            # Persist intent before the remote POST. If the process dies after
            # Hindsight accepts the file but before the operation ID is saved, the
            # next reconciliation recovers that ID from the exact document's
            # file-conversion operation list instead of submitting again.
            self._save(
                candidate,
                hindsight_document_id=key,
                document_id=candidate.document_id,
                workspace=candidate.workspace,
                source_path=candidate.relative_path,
                source_sha256=candidate.source_sha256,
                fingerprint=candidate.fingerprint,
                operation_id=None,
                status="SUBMITTING",
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
                "status": "SUBMITTING",
                "last_error": None,
                "tags_json": json.dumps(tags, ensure_ascii=False),
                "updated_at": _utc_now(),
            }
            if self.processing_queue is not None:
                self.processing_queue.set_status(
                    candidate.workspace, candidate.document_id,
                    preflight_status="ANALYZED", hindsight_status="MEMORIZING",
                    operation_id=None,
                    clear_error=True,
                )
                if ocr_submission:
                    # Persist derived-content intent before the network call so a
                    # crash after Hindsight accepts the file remains recoverable.
                    self.processing_queue.set_ocr_status(
                        candidate.workspace, candidate.document_id, status="SUBMITTED"
                    )

            try:
                retain_source = candidate.source_path
                retain_sha256 = candidate.source_sha256
                retain_metadata = dict(candidate.metadata)
                if queue_row is not None and queue_row.get("hindsight_status") == "OCR_READY":
                    output_filename = str(queue_row.get("ocr_filename") or "")
                    cache_dir = self.ocr_processor.cache_dir if self.ocr_processor is not None else None
                    if (cache_dir is None or not output_filename or Path(output_filename).name != output_filename
                            or not output_filename.endswith(".md")):
                        raise RuntimeError("OCR Markdown filename is invalid")
                    output_path = cache_dir / output_filename
                    if not output_path.is_file() or _sha256(candidate.source_path) != candidate.source_sha256:
                        raise RuntimeError("OCR result missing or source changed; rerun OCR")
                    retain_source = output_path
                    retain_sha256 = _sha256(output_path)
                    tags = sorted(set(tags) | {"ocr:complete"})
                    projected_tags[key] = tags
                    retain_metadata.update({
                        "ocr_engine": str(queue_row.get("ocr_engine") or "unknown"),
                        "ocr_derived_from": candidate.relative_path,
                        "ocr_source_sha256": candidate.source_sha256,
                        "ocr_artifact_name": output_path.name,
                    })
                    retain_context = (
                        f"{candidate.context}; Hindsight text representation=OCR derivative; "
                        f"content is an OCR derivative of the authoritative "
                        f"source file {candidate.relative_path}; OCR artifact filename={output_path.name}; "
                        f"raw source SHA-256={candidate.source_sha256}; do not OCR this source again "
                        "when this matching derivative is available"
                    )
                    # The stable document ID is protected by default. A one-shot
                    # operator approval explicitly enables Hindsight's replace upsert.
                    replacement_approved = bool(
                        queue_row is not None and queue_row.get("ocr_replace_approved")
                    )
                    try:
                        existing = self._client_for(candidate.workspace).get_document(candidate.hindsight_document_id)
                    except RuntimeError as exc:
                        if "Hindsight HTTP 404:" not in str(exc):
                            raise
                    else:
                        if (
                            isinstance(existing, dict)
                            and existing.get("id") == candidate.hindsight_document_id
                            and not replacement_approved
                        ):
                            raise RuntimeError("Hindsight document already exists; OCR replacement requires operator review")
                    if replacement_approved and self.processing_queue is not None:
                        self.processing_queue.consume_ocr_replacement_approval(
                            candidate.workspace, candidate.document_id
                        )
                operation_id = self._client_for(candidate.workspace).retain_file(
                    retain_source,
                    document_id=candidate.hindsight_document_id,
                    context=retain_context if queue_row is not None and queue_row.get("hindsight_status") == "OCR_READY" else candidate.context,
                    tags=tags,
                    metadata=retain_metadata,
                    expected_source_sha256=retain_sha256,
                )
            except (OSError, RuntimeError) as exc:
                last_error = str(exc)
                unavailable = _hindsight_connection_unavailable(last_error)
                uncertain = _submission_outcome_uncertain(last_error)
                replacement_review = (
                    last_error == "Hindsight document already exists; OCR replacement requires operator review"
                )
                source_unavailable = any(
                    marker in last_error.casefold()
                    for marker in (
                        "source unavailable before hindsight upload",
                        "source changed before hindsight upload",
                    )
                )
                persisted_status = (
                    "UNAVAILABLE" if unavailable
                    else "SUBMITTING" if uncertain
                    else "QUEUED" if source_unavailable
                    else "SUBMIT_ERROR"
                )
                self._save(
                    candidate,
                    hindsight_document_id=key,
                    document_id=candidate.document_id,
                    workspace=candidate.workspace,
                    source_path=candidate.relative_path,
                    source_sha256=candidate.source_sha256,
                    fingerprint=candidate.fingerprint,
                    operation_id=None,
                    status=persisted_status,
                    last_error=last_error,
                    tags=tags,
                    updated_at=(
                        str(states.get(key, {}).get("updated_at") or _utc_now())
                        if uncertain else None
                    ),
                )
                if self.processing_queue is not None:
                    self.processing_queue.set_status(
                        candidate.workspace, candidate.document_id,
                        preflight_status="STABILIZING" if source_unavailable else "ANALYZED",
                        hindsight_status=(
                            "VERIFY" if replacement_review
                            else "UNAVAILABLE" if unavailable
                            else "VERIFY" if uncertain
                            else "MODIFIED" if source_unavailable
                            else "FAILED"
                        ),
                        operation_id=None,
                        error=last_error,
                    )
                    if (unavailable or source_unavailable) and ocr_submission:
                        self.processing_queue.set_ocr_status(
                            candidate.workspace, candidate.document_id,
                            status="READY",
                            queue_status="UNAVAILABLE" if unavailable else "MODIFIED",
                        )
                    elif replacement_review and ocr_submission:
                        self.processing_queue.set_ocr_status(
                            candidate.workspace, candidate.document_id,
                            status="READY", queue_status="VERIFY",
                        )
                states[key] = {
                    "hindsight_document_id": key,
                    "document_id": candidate.document_id,
                    "workspace": candidate.workspace,
                    "source_path": candidate.relative_path,
                    "source_sha256": candidate.source_sha256,
                    "fingerprint": candidate.fingerprint,
                    "operation_id": None,
                    "status": persisted_status,
                    "last_error": last_error,
                    "tags_json": json.dumps(tags, ensure_ascii=False),
                }
                if unavailable:
                    # A refused connection is a Hindsight-wide outage, not a
                    # document failure. Keep this item retryable and stop the
                    # single submission lane before another document is attempted.
                    break
                if uncertain:
                    # Keep the durable SUBMITTING intent so the next reconcile
                    # searches for this exact operation before any later upload.
                    break
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
            if self.processing_queue is not None:
                self.processing_queue.set_status(
                    candidate.workspace, candidate.document_id,
                    preflight_status="ANALYZED", hindsight_status="MEMORIZING",
                    operation_id=operation_id,
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
            and workspace.get("complete", not workspace.get("errors")) is True
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
                    self._client_for(workspace).update_document_tags(
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
                quarantined_at = self._parse_timestamp(row.get("updated_at"))
                if (
                    quarantined_at is None
                    or (datetime.now(timezone.utc) - quarantined_at).total_seconds()
                    < self.missing_source_grace_seconds
                ):
                    continue
                try:
                    self._client_for(workspace).delete_document(key)
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
                if self.processing_queue is not None:
                    self.processing_queue.set_status(
                        workspace,
                        str(row["document_id"]),
                        preflight_status="ANALYZED",
                        hindsight_status="ARCHIVED",
                        clear_operation_id=True,
                        clear_error=True,
                    )

        if self.processing_queue is not None:
            # OCR/preflight requests that never reached Hindsight have no row in
            # hindsight_sync to drive missing-source cleanup. Retire them only
            # after a complete scan proves the path absent, so an OCR result for
            # a moved or deleted source cannot remain pending forever.
            refreshed_states = self._states()
            state_by_document = {
                (str(row.get("workspace") or ""), str(row.get("document_id") or "")): row
                for row in refreshed_states.values()
            }
            for item in self.processing_queue.list_items(include_memorized=True)["items"]:
                workspace = str(item.get("workspace") or "")
                document_id = str(item.get("document_id") or "")
                if (
                    workspace not in available_workspaces
                    or (workspace, str(item.get("source_path") or "")) in current_paths
                    or document_id in seen_document_ids
                    or item.get("user_decision") == "DO_NOT_SEND"
                    or item.get("hindsight_status") in {"MEMORIZED", "ARCHIVED", "FAILED", "UNAVAILABLE", "VERIFY", "VERIFYING"}
                ):
                    continue
                sync_row = state_by_document.get((workspace, document_id))
                if sync_row is not None and sync_row.get("status") != "ARCHIVED":
                    continue
                self.processing_queue.set_status(
                    workspace,
                    document_id,
                    preflight_status="ANALYZED",
                    hindsight_status="ARCHIVED",
                    clear_operation_id=True,
                    clear_error=True,
                )
                self.processing_queue.set_ocr_status(
                    workspace, document_id, status="NONE", queue_status="ARCHIVED"
                )

        states = self._states()
        quality_states = self._quality_states()
        try:
            self._ensure_project_overviews(candidates, states)
        except (OSError, RuntimeError, sqlite3.Error) as exc:
            # Page synthesis is a secondary, recoverable projection. It must not
            # turn a completed document retain into a failed producer pass.
            last_error = last_error or f"Project overview: {exc}"
        state_by_path = {
            (row.get("workspace"), row.get("source_path")): row
            for row in states.values()
        }
        queue_by_path: dict[tuple[str, str], dict[str, Any]] = {}
        if self.processing_queue is not None:
            queue_by_path = {
                (str(item["workspace"]), str(item["source_path"])): item
                for item in self.processing_queue.list_items(include_memorized=True)["items"]
            }
        for workspace in snapshot.get("workspaces") or []:
            for card in workspace.get("cards") or []:
                if card.get("kind") != "document":
                    continue
                if card.get("hindsight_status") == "VAULT_ID_COLLISION":
                    continue
                queue_row = queue_by_path.get((str(card.get("workspace") or ""), str(card.get("path") or "")))
                if queue_row is not None:
                    card["processing_queue_status"] = queue_row.get("hindsight_status")
                    card["processing_preflight_status"] = queue_row.get("preflight_status")
                    card["processing_queue_error"] = queue_row.get("error")
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
            "unavailable": 0,
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
            elif status == "UNAVAILABLE":
                counts["unavailable"] += 1
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
            "bank_ids": {
                name: item.bank_id for name, item in self.clients.items()
            } if self.clients else {name: self.client.bank_id for name in self.roots},
            "mode": "source-only",
            "delete_missing": "complete-scan-quarantine-then-grace",
            "missing_source_grace_seconds": self.missing_source_grace_seconds,
            "ocr_mode": "manual-per-file",
            **counts,
            "last_error": last_error,
            "last_reconcile_at": _utc_now(),
        }
        return dict(self._last_summary)

    def health(self) -> dict[str, Any]:
        preflight_health = None
        if self._preflight_thread is not None:
            with self._preflight_health_lock:
                preflight_health = {
                    "running": self._preflight_thread.is_alive(),
                    "last_error": self._preflight_last_error,
                    "last_error_at": self._preflight_last_error_at,
                    "last_success_at": self._preflight_last_success_at,
                    "retry_waiting": len(self._preflight_waiting_source),
                    "active_document": dict(self._preflight_active_document)
                    if self._preflight_active_document else None,
                }
        return {
            **self._last_summary,
            "preflight_worker": preflight_health,
            "status_poller": {
                "running": bool(self._status_poller_thread and self._status_poller_thread.is_alive()),
                "interval_seconds": self._status_poller_interval_seconds,
                "last_error": self._status_poller_last_error,
            },
        }
