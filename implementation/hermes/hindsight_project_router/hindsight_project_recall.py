#!/usr/bin/env python3
"""Fail-closed scoped recall adapter for Hindsight (project or knowledge vault)."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen


TAG_SAFE_RE = re.compile(r"[^a-z0-9._-]+")
MAX_EVIDENCE_RESULTS = 8


class ProjectRecallError(RuntimeError):
    pass


def tag_value(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.strip().casefold())
    without_marks = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    normalized = TAG_SAFE_RE.sub("-", without_marks).strip("-")
    return normalized[:96]


def project_scope_token(value: str) -> str:
    canonical = unicodedata.normalize("NFKC", value.strip()).casefold()
    slug = tag_value(value) or "project"
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
    return f"{slug[:80]}-{digest}"


class ProjectRecallClient:
    """Expose recall only when one exact project scope can be enforced."""

    def __init__(
        self,
        base_url: str,
        bank_id: str,
        *,
        source_kind: str = "project-sync",
        authorization: str = "",
        timeout_seconds: float = 45.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.bank_id = bank_id.strip()
        self.source_kind = tag_value(source_kind)
        self.authorization = authorization.strip()
        self.timeout_seconds = max(1.0, float(timeout_seconds))
        parsed = urlparse(self.base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Hindsight URL must be an absolute HTTP(S) URL")
        if not self.bank_id:
            raise ValueError("Hindsight bank_id is required")
        if not self.source_kind:
            raise ValueError("Hindsight source_kind is required")

    def _post(self, body: dict[str, Any]) -> dict[str, Any]:
        path = f"/v1/default/banks/{quote(self.bank_id, safe='')}/memories/recall"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "pantheon-hindsight-project-router/1",
        }
        if self.authorization:
            headers["Authorization"] = self.authorization
        request = Request(
            f"{self.base_url}{path}",
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
        except HTTPError as exc:
            detail = exc.read(4096).decode("utf-8", errors="replace")
            raise ProjectRecallError(f"Hindsight HTTP {exc.code}: {detail}") from exc
        except (OSError, URLError) as exc:
            raise ProjectRecallError(f"Hindsight unavailable: {exc}") from exc
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ProjectRecallError("Hindsight returned invalid JSON") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
            raise ProjectRecallError("Hindsight returned an unexpected recall response")
        return payload

    @staticmethod
    def _recall_body(query: str, tags: list[str], max_tokens: int) -> dict[str, Any]:
        budget = max(256, min(int(max_tokens), 4096))
        return {
            "query": query,
            "types": ["world", "experience"],
            "budget": "mid",
            "max_tokens": budget,
            "trace": False,
            "prefer_observations": False,
            # Hindsight bounds facts with max_tokens but raw chunks separately
            # (8192 tokens by default): without this cap one recall can fill a
            # local model's context window on its own.
            "include": {"entities": None, "chunks": {"max_tokens": budget}, "source_facts": None},
            "tags": tags,
            "tags_match": "all_strict",
        }

    @staticmethod
    def _bounded_evidence(
        payload: dict[str, Any], required_tags: tuple[str, ...]
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        # Defense in depth: never pass through a result whose returned scope does
        # not prove that Hindsight applied every mandatory selector.
        for result in payload["results"]:
            result_tags = result.get("tags") if isinstance(result, dict) else None
            if not isinstance(result_tags, list):
                raise ProjectRecallError("Hindsight returned an unscoped result")
            if not all(tag in result_tags for tag in required_tags):
                raise ProjectRecallError("Hindsight returned a result outside the requested scope")

        evidence: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for result in payload["results"]:
            if not isinstance(result, dict):
                continue
            document_id = result.get("document_id")
            chunk_id = result.get("chunk_id")
            text = result.get("text")
            if not all(isinstance(value, str) and value for value in (document_id, chunk_id, text)):
                continue
            identity = (document_id, chunk_id, text)
            if identity in seen:
                continue
            seen.add(identity)
            evidence.append(result)
            if len(evidence) >= MAX_EVIDENCE_RESULTS:
                break

        chunk_ids = {result["chunk_id"] for result in evidence}
        raw_chunks = payload.get("chunks")
        chunks = (
            {
                chunk_id: value
                for chunk_id, value in raw_chunks.items()
                if chunk_id in chunk_ids
            }
            if isinstance(raw_chunks, dict)
            else {}
        )
        return evidence, chunks

    def _list_tags(self, pattern: str, limit: int) -> list[dict[str, Any]]:
        path = f"/v1/default/banks/{quote(self.bank_id, safe='')}/tags?" + urlencode({
            "q": pattern, "limit": max(1, min(int(limit), 250)),
        })
        headers = {"Accept": "application/json", "User-Agent": "pantheon-hindsight-project-router/1"}
        if self.authorization:
            headers["Authorization"] = self.authorization
        try:
            with urlopen(Request(f"{self.base_url}{path}", headers=headers), timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, OSError, URLError, UnicodeError, json.JSONDecodeError) as exc:
            raise ProjectRecallError(f"Hindsight tag list unavailable: {exc}") from exc
        items = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            raise ProjectRecallError("Hindsight returned an unexpected tag response")
        prefix = pattern.rstrip("*")
        return [
            {"tag": item["tag"], "memory_count": item["count"]}
            for item in items
            if isinstance(item, dict) and isinstance(item.get("tag"), str)
            and isinstance(item.get("count"), int) and item["tag"].startswith(prefix)
        ]

    def list_project_scopes(self, limit: int = 100) -> dict[str, Any]:
        """List bounded project-scope tags and their observed memory counts."""
        projects = [
            {"scope": row["tag"], "memory_count": row["memory_count"]}
            for row in self._list_tags("scope:project:*", limit)
        ]
        return {"status": "ok", "source_scope": f"source:{self.source_kind}", "projects": projects,
                "total": len(projects), "scope_is_indexed_not_identity": True}

    def list_knowledge_folders(self, limit: int = 100) -> dict[str, Any]:
        """List bounded knowledge-vault folder tags and their memory counts."""
        folders = [
            {"folder": row["tag"].removeprefix("folder:"), "memory_count": row["memory_count"]}
            for row in self._list_tags("folder:*", limit)
        ]
        return {"status": "ok", "source_scope": f"source:{self.source_kind}", "folders": folders,
                "total": len(folders), "folder_is_indexed_not_authority": True}

    def recall_project(
        self,
        project: str,
        query: str,
        *,
        folder: str = "",
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        project_slug = tag_value(project)
        if not project_slug or project_slug == "pending-identification":
            raise ProjectRecallError("A concrete project is required")
        project_scope = project_scope_token(project)
        query = query.strip()
        if not query or len(query) > 2000:
            raise ProjectRecallError("Query must contain between 1 and 2000 characters")

        source_tag = f"source:{self.source_kind}"
        scope_tag = f"scope:project:{project_scope}"
        tags = [source_tag, scope_tag]
        folder_slug = tag_value(folder) if folder else ""
        if folder_slug:
            tags.append(f"folder:{folder_slug}")

        payload = self._post(self._recall_body(query, tags, max_tokens))
        evidence, chunks = self._bounded_evidence(payload, (source_tag, scope_tag))

        return {
            "status": "ok",
            "bank_id": self.bank_id,
            "mode": "source-grounded-evidence",
            "project_scope": scope_tag,
            "source_scope": source_tag,
            "folder_scope": f"folder:{folder_slug}" if folder_slug else None,
            "tags_match": "all_strict",
            "max_results": MAX_EVIDENCE_RESULTS,
            "results": evidence,
            "chunks": chunks,
        }

    def recall_knowledge(
        self,
        query: str,
        *,
        folder: str = "",
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """Recall from the knowledge vault: one source, optional folder, no project."""
        query = query.strip()
        if not query or len(query) > 2000:
            raise ProjectRecallError("Query must contain between 1 and 2000 characters")
        source_tag = f"source:{self.source_kind}"
        tags = [source_tag]
        folder_slug = tag_value(folder) if folder else ""
        if folder_slug:
            tags.append(f"folder:{folder_slug}")
        payload = self._post(self._recall_body(query, tags, max_tokens))
        evidence, chunks = self._bounded_evidence(payload, tuple(tags))
        return {
            "status": "ok",
            "bank_id": self.bank_id,
            "mode": "source-grounded-evidence",
            "source_scope": source_tag,
            "folder_scope": f"folder:{folder_slug}" if folder_slug else None,
            "tags_match": "all_strict",
            "max_results": MAX_EVIDENCE_RESULTS,
            "results": evidence,
            "chunks": chunks,
        }
