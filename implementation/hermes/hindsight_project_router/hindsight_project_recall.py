#!/usr/bin/env python3
"""Fail-closed scoped recall adapter for Hindsight (project or knowledge vault)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
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
# Indexing bookkeeping repeated on every row: it restates the enforced scope or
# derives from source_path, so it costs a local model context without adding
# provenance. Descriptive document metadata (title, revision, phase...) is kept.
REDUNDANT_METADATA = frozenset({
    "workspace", "parent_path", "source_kind", "source_space", "scope_project",
    "project_hint", "folder_ancestry", "identity_origin", "pantheon_document_id",
    "project_scope_source", "document_identity_source",
})
EVIDENCE_FIELDS = ("text", "type", "document_id", "chunk_id", "occurred_start", "occurred_end", "mentioned_at")
# Raw chunks are requested generously from Hindsight but never forwarded: each
# row carries only the verbatim passage of its own chunk that supports it.
CHUNK_TOKENS = 8192
QUOTE_MAX_CHARS = 420
_WORD_RE = re.compile(r"\w+", re.UNICODE)
# A numbered heading on its own line ("8.6.1 Section de ventilation", "Annexe B").
_GLYPH_RE = re.compile(r"\(cid:\d+\)")
# Sentence-like units: up to a sentence end, a semicolon or a list bullet.
_UNIT_RE = re.compile(r"(?:[^.;•]|\.(?=\d))+?(?:[.;](?!\d)|(?=•)|$)")
# Print footers, links and watermark contacts are not part of the source text:
# they are replaced by an elision mark instead of being quoted.
_NOISE_RE = re.compile(
    r"https?://\S+|\b[\w.+-]+@[\w-]+\.[\w.]+\b|\bPage \d+ of \d+\b|(?:\+33|\b0)[1-9](?:[ .]?\d{2}){4}\b"
)
_HEADING_RE = re.compile(r"^\s*((?:\d+(?:\.\d+)+|[A-Z](?:\.\d+)+|Annexe\s+[A-Z]))\.?\s+(\S.{0,80}?)\s*$")


# Document-level labels carried as tags (producer or promotion after extraction). They are exposed
# apart from the passage and never used to filter or to exclude: they describe, they do not decide.
LABEL_KEYS = frozenset({
    "indice", "indice_fiche", "revision_hint", "date_document", "emetteur", "destinataire",
    "version", "revision", "portee", "lot", "type", "phase",
})
# A text-layer passage is quoted whole; a fact is quoted by its supporting sentences.
TEXT_QUOTE_MAX_CHARS = 1000
GENERAL_CONDITIONS_NOTICE = (
    "Reprise de conditions générales d'entreprise, pas une règle ni une obligation propre à cette affaire."
)
OLDER_MEMBER_NOTICE = (
    "Version antérieure d'un même ensemble de pièces, présentée après la plus récente ; "
    "consultable sur demande (older_versions)."
)
SUPERSEDED_NOTICE = (
    "Édition remplacée par {successor} : présentée après les éditions en vigueur, "
    "consultable sur demande (older_versions)."
)
_DATE_RE = re.compile(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$")


class ProjectRecallError(RuntimeError):
    pass


def _significant_tokens(text: str) -> set[str]:
    return {token for token in _WORD_RE.findall(text.lower()) if len(token) >= 4 or any(c.isdigit() for c in token)}


def _numbers(text: str) -> set[str]:
    return {token for token in _WORD_RE.findall(text) if token.isdigit()}


def _is_spaced_out(unit: str) -> bool:
    """Margin text printed vertically ("e r u t i o t") extracts as single letters."""
    tokens = unit.split()
    return len(tokens) >= 6 and sum(len(token) == 1 for token in tokens) > 0.5 * len(tokens)


def _weight(tokens: set[str]) -> int:
    return sum(2 if token.isdigit() else 1 for token in tokens)


def locate_quote(summary: str, chunk_text: str) -> tuple[str | None, str | None]:
    """Find the verbatim chunk passage that supports a Hindsight summary.

    Returns (quote, section). The quote is copied from the chunk with only
    whitespace and PDF glyph artifacts normalized; the section is the last
    numbered heading above it in the same chunk. Either is None when the chunk
    does not establish it (for example a summary of a table), so a caller never
    receives a reconstructed quotation or locator.
    """
    wanted = _significant_tokens(summary)
    if not wanted or not chunk_text.strip():
        return None, None
    text = _GLYPH_RE.sub(lambda m: " " * len(m.group()), chunk_text)
    text = _NOISE_RE.sub(lambda m: "[…]".ljust(len(m.group())), text)
    headings, offset = [], 0
    for line in text.splitlines(keepends=True):
        match = _HEADING_RE.match(line)
        if match:
            headings.append((offset, " ".join(f"{match.group(1)} {match.group(2)}".split())))
        offset += len(line)
    # PDF extraction breaks lines mid-sentence: join them (same length, so the
    # heading offsets stay valid), then cut at sentence or list-item ends.
    flow = text.replace("\n", " ")
    units = [(m.start(), m.group()) for m in _UNIT_RE.finditer(flow) if m.group().strip() and not _is_spaced_out(m.group())]
    candidates: list[tuple[float, int, int, int]] = []  # ratio, length, first, last
    for first in range(len(units)):
        for last in range(first, len(units)):
            passage = " ".join(unit for _, unit in units[first:last + 1])
            if len(" ".join(passage.split())) > QUOTE_MAX_CHARS and last > first:
                break
            ratio = _weight(wanted & _significant_tokens(passage)) / _weight(wanted)
            candidates.append((ratio, len(passage), first, last))
    if not candidates:
        return None, None
    top = max(candidate[0] for candidate in candidates)
    # Near-equal support: the shortest passage is the most precise quotation.
    ratio, _, first, last = min((c for c in candidates if c[0] >= top - 0.1), key=lambda c: (c[1], -c[0]))
    quote = " ".join(" ".join(unit for _, unit in units[first:last + 1]).split())
    if ratio < 0.6 or not _numbers(summary) <= _numbers(quote):
        return None, None  # the passage does not carry the summary or one of its figures
    if len(quote) > QUOTE_MAX_CHARS:
        quote = quote[:QUOTE_MAX_CHARS].rsplit(" ", 1)[0] + " …"
    # A heading opening the quoted passage is its own section.
    opening = units[first][0] + len(units[first][1])
    section = next((title for position, title in reversed(headings) if position < opening), None)
    return quote, section


def _compact_evidence(result: dict[str, Any], chunk_text: str = "") -> dict[str, Any]:
    """Keep the summary and its provenance, add the verbatim supporting passage;
    drop scope tags (already enforced), scores, context strings and empty fields."""
    row = {key: result[key] for key in EVIDENCE_FIELDS if result.get(key) not in (None, "", [], {})}
    metadata = result.get("metadata")
    if isinstance(metadata, dict):
        kept = {
            key: value for key, value in metadata.items()
            if key not in REDUNDANT_METADATA and value not in (None, "", [], {})
        }
        if kept:
            row["metadata"] = kept
    quote, section = locate_quote(row["text"], chunk_text) if chunk_text else (None, None)
    if quote:
        row["quote"] = quote
    if section:
        row["section"] = section
    title = (row.get("metadata") or {}).get("title")
    if title:
        row["citation"] = f"{title}, {section}" if section else title
    return row


def _normalized_passage(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).split())


def _tag_labels(tags: list[str]) -> dict[str, list[str]]:
    """Group the descriptive label tags by key ("indice:B" -> {"indice": ["B"]})."""
    labels: dict[str, list[str]] = {}
    for tag in tags:
        key, separator, value = tag.partition(":")
        if separator and value and key in LABEL_KEYS and value not in labels.get(key, []):
            labels.setdefault(key, []).append(value)
    return labels


def _date_key(value: str) -> tuple[int, int, int] | None:
    """A read document date as a comparable key; a missing month or day sorts first."""
    match = _DATE_RE.match(value.strip())
    return tuple(int(part or 0) for part in match.groups()) if match else None


def _latest_date(labels: dict[str, list[str]]) -> tuple[int, int, int] | None:
    keys = [key for key in map(_date_key, labels.get("date_document", [])) if key]
    return max(keys) if keys else None


@dataclass(eq=False)
class _Hit:
    """One distinct passage in relevance order, with what ordering may use (never to drop it)."""

    row: dict[str, Any]
    tags: list[str]
    document_id: str
    chunk_id: str
    title: str | None
    key: tuple[str, str]
    labels: dict[str, list[str]]
    family: str | None
    date: tuple[int, int, int] | None
    pos: int = 0
    notices: list[str] = field(default_factory=list)


def _apply_family_recency(hits: list[_Hit], older_versions: bool) -> list[_Hit]:
    """Present the most recent member of a document family first.

    Recency is the document date read in the content; an index never orders (a higher index
    is not newer). Members without a read date are not ranked. Older members are moved
    behind the rest, never dropped; on request they keep their relevance rank.
    """
    families: dict[str, list[_Hit]] = defaultdict(list)
    for hit in hits:
        if hit.family and hit.date:
            families[hit.family].append(hit)
    promoted: dict[int, int] = {}
    demoted: list[_Hit] = []
    for members in families.values():
        if len(members) < 2:
            continue
        # Equal dates fall back to relevance, never to the index.
        newest = min(members, key=lambda hit: (tuple(-part for part in hit.date), hit.pos))
        newest.row["earlier_in_family"] = len(members) - 1
        if older_versions:
            continue
        promoted[id(newest)] = min(member.pos for member in members)
        for member in members:
            if member is not newest:
                member.notices.append(OLDER_MEMBER_NOTICE)
                demoted.append(member)
    if older_versions or not demoted:
        return hits
    behind = {id(hit) for hit in demoted}
    kept = sorted(
        (hit for hit in hits if id(hit) not in behind),
        key=lambda hit: (promoted.get(id(hit), hit.pos), hit.pos),
    )
    return kept + sorted(demoted, key=lambda hit: (tuple(-part for part in hit.date), hit.pos))


def _apply_superseded(hits: list[_Hit], older_versions: bool) -> list[_Hit]:
    """Knowledge vault: demote, never drop, an edition declared superseded."""
    behind: list[_Hit] = []
    for hit in hits:
        successor = next(
            (value.split(":", 1)[1] for value in hit.labels.get("revision", []) if value.startswith("superseded-by:")),
            None,
        )
        if successor and not older_versions:
            hit.notices.append(SUPERSEDED_NOTICE.format(successor=successor))
            behind.append(hit)
    if not behind:
        return hits
    ids = {id(hit) for hit in behind}
    return [hit for hit in hits if id(hit) not in ids] + behind


def _apply_general_conditions(hits: list[_Hit]) -> list[_Hit]:
    """A company's boilerplate comes after what is specific to the matter, with a notice."""
    general = [hit for hit in hits if "conditions_generales" in hit.labels.get("portee", [])]
    if not general:
        return hits
    for hit in general:
        hit.notices.append(GENERAL_CONDITIONS_NOTICE)
    ids = {id(hit) for hit in general}
    return [hit for hit in hits if id(hit) not in ids] + general


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
            # Chunks feed the per-row verbatim quote and are not forwarded, so
            # their budget no longer reaches the model's context window.
            "include": {"entities": None, "chunks": {"max_tokens": CHUNK_TOKENS}, "source_facts": None},
            "tags": tags,
            "tags_match": "all_strict",
        }

    @staticmethod
    def _bounded_evidence(
        payload: dict[str, Any],
        required_tags: tuple[str, ...],
        *,
        older_versions: bool = False,
        mode: str = "project",
    ) -> list[dict[str, Any]]:
        # Defense in depth: never pass through a result whose returned scope does
        # not prove that Hindsight applied every mandatory selector. This covers the
        # text layer as well: a passage outside the scope fails the whole recall.
        for result in payload["results"]:
            result_tags = result.get("tags") if isinstance(result, dict) else None
            if not isinstance(result_tags, list):
                raise ProjectRecallError("Hindsight returned an unscoped result")
            if not all(tag in result_tags for tag in required_tags):
                raise ProjectRecallError("Hindsight returned a result outside the requested scope")

        raw_chunks = payload.get("chunks")
        chunks = {
            chunk_id: value["text"]
            for chunk_id, value in (raw_chunks.items() if isinstance(raw_chunks, dict) else ())
            if isinstance(value, dict) and isinstance(value.get("text"), str)
        }
        hits: list[_Hit] = []
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
            tags = [tag for tag in result["tags"] if isinstance(tag, str)]
            is_text_layer = "representation:text" in tags or document_id.endswith(":text")
            row = _compact_evidence(result, "" if is_text_layer else chunks.get(chunk_id, ""))
            if is_text_layer:
                # A raw passage is its own quotation: no summary is claimed over it.
                passage = _normalized_passage(text)
                if len(passage) > TEXT_QUOTE_MAX_CHARS:
                    passage = passage[:TEXT_QUOTE_MAX_CHARS].rsplit(" ", 1)[0] + " …"
                row.pop("text", None)
                row["representation"] = "text"
                row["quote"] = passage
            labels = _tag_labels(tags)
            if labels:
                row["labels"] = labels
            metadata = result.get("metadata")
            hits.append(_Hit(
                row=row, tags=tags, document_id=document_id, chunk_id=chunk_id,
                title=metadata.get("title") if isinstance(metadata, dict) else None,
                key=("text" if is_text_layer else "fact", _normalized_passage(text)),
                labels=labels,
                family=next((tag.split(":", 1)[1] for tag in tags if tag.startswith("family:")), None),
                date=_latest_date(labels),
            ))

        # The same passage repeated across documents (letterheads, general conditions,
        # title blocks) is one result that lists where else it appears: nothing is lost.
        groups: dict[tuple[str, str], list[_Hit]] = {}
        for hit in hits:
            groups.setdefault(hit.key, []).append(hit)
        grouped: list[_Hit] = []
        for members in groups.values():
            lead = members[0]
            if lead.family and len(members) > 1 and all(m.family == lead.family and m.date for m in members):
                lead = min(members, key=lambda m: (tuple(-part for part in m.date), m.pos))
            others = [member for member in members if member is not lead]
            if others:
                lead.row["present_in_documents"] = len({member.document_id for member in members})
                lead.row["also_in"] = [
                    {"document_id": other.document_id, "chunk_id": other.chunk_id,
                     **({"title": other.title} if other.title else {})}
                    for other in others
                ]
            lead.pos = len(grouped)
            grouped.append(lead)

        if mode == "project":
            ordered = _apply_family_recency(grouped, older_versions)
        else:
            ordered = _apply_superseded(grouped, older_versions)
        ordered = _apply_general_conditions(ordered)

        evidence: list[dict[str, Any]] = []
        quoted: set[str] = set()
        for hit in ordered[:MAX_EVIDENCE_RESULTS]:
            row = hit.row
            if hit.notices:
                row["notice"] = " ".join(hit.notices)
            # Facts drawn from one passage would repeat it: quote it once; later
            # rows keep their summary, section and citation. A raw text passage is
            # never stripped: it is the only content of its row.
            if row.get("representation") != "text":
                if row.get("quote") in quoted:
                    del row["quote"]
                elif "quote" in row:
                    quoted.add(row["quote"])
            evidence.append(row)
        return evidence

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
        older_versions: bool = False,
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
        evidence = self._bounded_evidence(
            payload, (source_tag, scope_tag), older_versions=older_versions, mode="project"
        )

        return {
            "status": "ok",
            "bank_id": self.bank_id,
            "mode": "source-grounded-evidence",
            "project_scope": scope_tag,
            "source_scope": source_tag,
            "folder_scope": f"folder:{folder_slug}" if folder_slug else None,
            "tags_match": "all_strict",
            "max_results": MAX_EVIDENCE_RESULTS,
            "older_versions": older_versions,
            "results": evidence,
        }

    def recall_knowledge(
        self,
        query: str,
        *,
        folder: str = "",
        max_tokens: int = 2048,
        older_versions: bool = False,
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
        evidence = self._bounded_evidence(
            payload, tuple(tags), older_versions=older_versions, mode="knowledge"
        )
        return {
            "status": "ok",
            "bank_id": self.bank_id,
            "mode": "source-grounded-evidence",
            "source_scope": source_tag,
            "folder_scope": f"folder:{folder_slug}" if folder_slug else None,
            "tags_match": "all_strict",
            "max_results": MAX_EVIDENCE_RESULTS,
            "older_versions": older_versions,
            "results": evidence,
        }
