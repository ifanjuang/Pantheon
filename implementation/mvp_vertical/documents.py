"""Bounded document conversion for the external Hermes-side runtime.

Text sources stay dependency-free. Binary office documents are sent only to a
caller-selected, self-hosted Docling Serve instance. This module never scans a
folder, follows an undeclared URL or chooses a source outside the Task Contract.
"""

from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


TEXT_EXTENSIONS = frozenset({".md", ".markdown", ".txt"})


class DocumentConversionError(RuntimeError):
    """The declared document could not be converted without widening scope."""


@dataclass(frozen=True)
class ConvertedDocument:
    markdown: str
    document_json: dict[str, Any]
    converter: str
    converter_version: str
    config_digest: str
    status: str = "ready"
    processing_time: float | None = None
    quality_flags: tuple[str, ...] = ()


class DocumentConverter(Protocol):
    converter: str
    converter_version: str
    config_digest: str
    observation_kind: str

    def convert(self, path: Path) -> ConvertedDocument: ...


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _digest_config(value: dict[str, Any]) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class DirectTextConverter:
    converter = "direct_text"
    converter_version = "1"
    config_digest = _digest_config({"encoding": "utf-8", "errors": "strict"})
    observation_kind = "direct_text"

    def convert(self, path: Path) -> ConvertedDocument:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise DocumentConversionError(f"cannot read text source {path.name}: {exc}") from exc
        if not text.strip():
            raise DocumentConversionError(f"text source is empty: {path.name}")
        return ConvertedDocument(
            markdown=text,
            document_json={"schema_name": "direct_text"},
            converter=self.converter,
            converter_version=self.converter_version,
            config_digest=self.config_digest,
        )


class DoclingServeClient:
    """Small standard-library client for Docling Serve's stable v1 API.

    Base64 JSON is intentional for the first bounded slice: it avoids an extra
    HTTP dependency and sends exactly one already-contained file. Large-batch
    processing belongs to a separately reviewed async adapter.
    """

    converter = "docling_serve"
    observation_kind = "live_parser"

    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        version: str = "v1.21.0",
        timeout: float = 180.0,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("Docling Serve URL must use http:// or https://")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.converter_version = version
        self.timeout = timeout
        self._opener = opener
        self.options: dict[str, Any] = {
            "to_formats": ["md", "json"],
            "do_ocr": True,
            "image_export_mode": "placeholder",
            "table_mode": "accurate",
        }
        self.config_digest = _digest_config(self.options)

    @classmethod
    def from_env(cls) -> "DoclingServeClient":
        return cls(
            os.environ.get("DOCLING_SERVE_URL", "http://127.0.0.1:5001"),
            api_key=os.environ.get("DOCLING_SERVE_API_KEY"),
            version=os.environ.get("DOCLING_SERVE_VERSION", "v1.21.0"),
        )

    def convert(self, path: Path) -> ConvertedDocument:
        try:
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        except OSError as exc:
            raise DocumentConversionError(
                f"cannot read declared source {path.name}: {exc}"
            ) from exc

        payload = {
            "file_sources": [{"base64_string": encoded, "filename": path.name}],
            "options": self.options,
        }
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        request = Request(
            f"{self.base_url}/v1/convert/source",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with self._opener(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise DocumentConversionError(f"Docling Serve returned HTTP {exc.code}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise DocumentConversionError(f"Docling Serve is unreachable: {exc}") from exc
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise DocumentConversionError("Docling Serve returned invalid JSON") from exc

        status = result.get("status")
        if status not in {"success", "partial_success"}:
            errors = result.get("errors") or []
            raise DocumentConversionError(f"Docling conversion failed ({status}): {errors}")
        document = result.get("document") or {}
        markdown = document.get("md_content") or ""
        document_json = document.get("json_content") or {}
        if not isinstance(markdown, str) or not markdown.strip():
            raise DocumentConversionError("Docling conversion returned no Markdown content")
        if not isinstance(document_json, dict):
            raise DocumentConversionError("Docling conversion returned invalid structured JSON")
        flags = ("docling_partial_success",) if status == "partial_success" else ()
        return ConvertedDocument(
            markdown=markdown,
            document_json=document_json,
            converter=self.converter,
            converter_version=self.converter_version,
            config_digest=self.config_digest,
            status="needs_review" if flags else "ready",
            processing_time=result.get("processing_time"),
            quality_flags=flags,
        )


def converter_for(path: Path, docling: DocumentConverter | None) -> DocumentConverter:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return DirectTextConverter()
    if docling is None:
        media_type = mimetypes.guess_type(path.name)[0] or "binary document"
        raise DocumentConversionError(
            f"{media_type} source {path.name} requires the bounded Docling Serve adapter"
        )
    return docling
