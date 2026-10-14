#!/usr/bin/env python3
"""Optional Hindsight/NAS explorer over one AFFAIRES producer projection."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
from datetime import date, datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import re
import select
import sqlite3
import struct
import sys
import threading
import time
import unicodedata
from typing import Any, Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, unquote, urlparse
from urllib.request import Request, urlopen

import yaml

# server.py is intentionally executable as a standalone script rather than a package.
# Add only its own directory so the colocated producer module is importable in both
# systemd/Docker execution and importlib-based contract tests.
_MODULE_ROOT = Path(__file__).resolve().parent
if str(_MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(_MODULE_ROOT))
from hindsight_producer import HindsightHTTPClient, HindsightProducer
from memory_reconciliation import (
    HermesReconciliationClient,
    MemoryReconciliationService,
    ReconciliationError,
    ReconciliationResidencyError,
)
from worker_observability import logs as producer_logs, status as producer_status


APP_ROOT = _MODULE_ROOT
STATIC_ROOT = APP_ROOT / "static"
PROJECTION_ID = "affaires_hindsight_project_scope_v5"
CARTOUCHE_SCHEMA = "pantheon/cartouche/v1"
FOLDER_CONTEXT_SCHEMA = "pantheon/folder-context/v1"
MARKDOWN_EXTENSIONS = {".md", ".markdown"}
LEGACY_MANIFEST_NAMES = {"document.yaml", "document.yml", "manifest.yaml", "manifest.yml"}
HINDSIGHT_ELIGIBLE_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".md", ".markdown", ".html", ".htm"}
SCANNED_SOURCE_EXTENSIONS = HINDSIGHT_ELIGIBLE_EXTENSIONS | {".eml"}
HEAVY_VISIBLE_EXTENSIONS = {".rvt", ".rfa", ".rte", ".psd", ".psb"}
TEMP_SUFFIXES = {".bak", ".lock", ".lck", ".swp", ".tmp", ".temp", ".autosave"}
ARCHIVE_STEM_MARKERS = {"archive", "bak", "backup", "old"}
MAX_CARTOUCHE_BYTES = 512 * 1024
MAX_ITEMS = 100_000
DEFAULT_EXCLUDED_FOLDERS = ("archive", "archives")
PROJECT_CATALOGUE_MAX_ITEMS = 10_000
PROJECT_ROOT_POLICIES = {
    "affaires": {
        "root_kind": "AFFAIRES",
        "state": "active",
        "write_requires_confirmation": False,
    },
    "project-platform": {
        "root_kind": "AFFAIRES",
        "state": "active",
        "write_requires_confirmation": False,
    },
    "archivesprojet": {
        "root_kind": "ARCHIVES_PROJET",
        "state": "archived",
        "write_requires_confirmation": True,
    },
    "archivesprojet": {
        "root_kind": "ARCHIVES_PROJET",
        "state": "archived",
        "write_requires_confirmation": True,
    },
}
STATUS_NAMES = (
    "COMPLETE",
    "FOLDER_SCOPED",
    "PENDING_SCOPE",
    "SOURCE_ONLY",
    "CHECK",
    "CARTOUCHE_MISSING",
    "SOURCE_MISSING",
    "FOLDER",
)
REVISION_MODES = {"supersedes", "supplements"}
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
FILENAME_REVISION_RE = re.compile(
    r"^(?P<base>.+?)[\s_.-]+(?:ind(?:ice)?|rev(?:ision)?|v(?:ersion)?)"
    r"[\s_.-]*(?P<token>[a-z0-9]+)$",
    re.IGNORECASE,
)

# The Cockpit is a local navigation surface, not a reverse proxy. Links are
# deliberately opt-in: an absent or malformed URL is not rendered.
NAVIGATION_LINKS = (
    ("WORKSPACE_COCKPIT_HERMES_URL", "Hermes", "Assistant gouverné"),
    ("WORKSPACE_COCKPIT_HINDSIGHT_URL", "Hindsight", "Mémoire et documents indexés"),
    ("WORKSPACE_COCKPIT_MNEMOSYNE_URL", "Mnemosyne", "Mémoire locale"),
)


def _visible(path: Path) -> bool:
    return not path.name.startswith(".") and not path.is_symlink()


def configured_navigation() -> list[dict[str, str]]:
    """Return explicitly configured, credential-free HTTP(S) navigation links."""
    links: list[dict[str, str]] = []
    for variable, label, description in NAVIGATION_LINKS:
        raw_url = os.getenv(variable, "").strip()
        parsed = urlparse(raw_url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            continue
        links.append({"label": label, "description": description, "url": raw_url})
    return links


def _direct_files(path: Path) -> list[Path]:
    """Return direct regular files, including dot-prefixed cartouches.

    Source admission still filters ordinary hidden files separately.
    """
    try:
        return sorted(
            (item for item in path.iterdir() if item.is_file() and not item.is_symlink()),
            key=lambda item: item.name.casefold(),
        )
    except OSError:
        return []


def _cartouche_name_for_source(source_name: str) -> str:
    return f".{source_name}.md"


def _is_document_cartouche(path: Path) -> bool:
    name = path.name
    return (
        name.startswith(".")
        and name.casefold().endswith(".md")
        and len(name) > len("..md")
        and not _is_temp_or_backup(path)
    )


def _is_temp_or_backup(path: Path) -> bool:
    name = path.name.casefold()
    if name.startswith("~$") or name.startswith(".~lock."):
        return True
    if path.suffix.casefold() in TEMP_SUFFIXES:
        return True
    stem_tokens = [
        token
        for token in re.split(r"[\s._-]+", path.stem.casefold().strip(" ._-"))
        if token
    ]
    if stem_tokens and stem_tokens[-1] in ARCHIVE_STEM_MARKERS:
        return True
    # Revit numbered backup copies: Model.0001.rvt, Model.0002.rvt, ...
    if re.search(r"\.\d{4}\.r(?:vt|fa|te)$", name):
        return True
    return False


def _is_source_file(path: Path) -> bool:
    if not _visible(path) or _is_temp_or_backup(path):
        return False
    if path.name.casefold() == "_folder.md":
        return False
    if _is_document_cartouche(path):
        return False
    if path.name.casefold() in LEGACY_MANIFEST_NAMES:
        return False
    return path.suffix.casefold() in SCANNED_SOURCE_EXTENSIONS


def _read_cartouche(path: Path) -> tuple[dict[str, Any], str, str | None]:
    """Read one bounded Markdown cartouche without touching its source bytes."""
    try:
        if path.stat().st_size > MAX_CARTOUCHE_BYTES:
            return {}, "", "Cartouche Markdown trop volumineux"
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return {}, "", "Cartouche Markdown illisible"

    metadata: dict[str, Any] = {}
    body = text
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        closing = next((idx for idx, line in enumerate(lines[1:], start=1) if line.strip() == "---"), None)
        if closing is None:
            return {}, text, "Frontmatter YAML non terminé"
        raw_frontmatter = "\n".join(lines[1:closing])
        try:
            parsed = yaml.safe_load(raw_frontmatter) if raw_frontmatter.strip() else {}
        except yaml.YAMLError:
            return {}, "\n".join(lines[closing + 1 :]), "Frontmatter YAML illisible"
        if parsed is None:
            parsed = {}
        if not isinstance(parsed, dict):
            return {}, "\n".join(lines[closing + 1 :]), "Le frontmatter doit contenir un objet YAML"
        metadata = parsed
        body = "\n".join(lines[closing + 1 :])

    return metadata, body, None


def _meta_string(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return None


def _schema_warning(metadata: dict[str, Any], expected: str) -> str | None:
    schema = _meta_string(metadata, "schema")
    if schema == expected:
        return None
    if schema is None:
        return f"schema absent (attendu: {expected})"
    return f"schema incompatible: {schema} (attendu: {expected})"


def _meta_tags(metadata: dict[str, Any]) -> list[str]:
    value = metadata.get("tags")
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if isinstance(item, (str, int, float)) and str(item).strip()]
    return []


def _revision_relation(
    metadata: dict[str, Any],
    document_id: str | None,
) -> tuple[dict[str, Any], list[str]]:
    """Parse only explicit revision semantics; index/date/name never imply lineage."""
    warnings: list[str] = []
    mode_present = "revision_mode" in metadata
    target_present = "revision_of" in metadata
    mode = _meta_string(metadata, "revision_mode")
    target = _meta_string(metadata, "revision_of")

    if not mode_present and not target_present:
        return {
            "revision_mode": None,
            "revision_of": None,
            "revision_target_present": None,
            "revision_target_status": "NONE",
        }, warnings

    if not mode or not target:
        warnings.append("revision_mode et revision_of doivent être renseignés ensemble")
        return {
            "revision_mode": mode,
            "revision_of": target,
            "revision_target_present": None,
            "revision_target_status": "INVALID",
        }, warnings

    normalized_mode = mode.casefold()
    invalid = False
    if normalized_mode not in REVISION_MODES:
        invalid = True
        warnings.append(
            "revision_mode invalide (attendu: supersedes ou supplements)"
        )
    if document_id and target == document_id:
        invalid = True
        warnings.append("revision_of ne peut pas référencer le document lui-même")

    return {
        "revision_mode": normalized_mode,
        "revision_of": target,
        "revision_target_present": None,
        "revision_target_status": "INVALID" if invalid else "UNRESOLVED",
    }, warnings


def _first_heading(body: str) -> str | None:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") and len(stripped) > 2:
            return stripped[2:].strip()
    return None


def _summary_excerpt(body: str, limit: int = 800) -> str:
    lines = body.splitlines()
    start: int | None = None
    for idx, line in enumerate(lines):
        heading = line.strip().casefold()
        if heading in {"## résumé", "## resume"}:
            start = idx + 1
            break

    chunks: list[str] = []
    if start is not None:
        for line in lines[start:]:
            stripped = line.strip()
            if stripped.startswith("## "):
                break
            if stripped:
                chunks.append(stripped)
    else:
        paragraph: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                if paragraph:
                    break
                continue
            if stripped.startswith("#"):
                continue
            paragraph.append(stripped)
        chunks = paragraph

    text = " ".join(chunks).strip()
    if len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def _mtime_iso(path: Path) -> str | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    except OSError:
        return None


def _file_size(path: Path) -> int | None:
    try:
        return path.stat().st_size
    except OSError:
        return None


def _file_sha256(path: Path) -> tuple[str | None, str | None]:
    """Hash source bytes only when a cartouche explicitly requests integrity verification."""
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest(), None
    except OSError:
        return None, "Source illisible pendant la vérification SHA-256"


def _declared_source_size(metadata: dict[str, Any]) -> tuple[int | None, str | None]:
    value = metadata.get("source_size_bytes")
    if value is None:
        return None, None
    if isinstance(value, bool):
        return None, "source_size_bytes invalide"
    if isinstance(value, int) and value >= 0:
        return value, None
    if isinstance(value, str):
        normalized = value.strip()
        if normalized.isdigit() and len(normalized) <= 20:
            try:
                return int(normalized), None
            except ValueError:
                pass
    return None, "source_size_bytes invalide"


def _source_integrity(
    metadata: dict[str, Any],
    source: Path,
    *,
    require_digest: bool = False,
    require_size: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    """Verify an explicitly declared source checksum without hashing every AFFAIRES source."""
    warnings: list[str] = []
    declared_key_present = "source_sha256" in metadata
    declared = _meta_string(metadata, "source_sha256")
    declared_size, size_error = _declared_source_size(metadata)
    actual_size = _file_size(source)

    if size_error:
        warnings.append(size_error)
    elif require_size and declared_size is None:
        warnings.append("source_size_bytes absent du cartouche")
    elif declared_size is not None and actual_size is not None and declared_size != actual_size:
        warnings.append(
            f"source_size_bytes différent de la source : déclaré {declared_size}, observé {actual_size}"
        )

    if declared is None:
        if declared_key_present:
            warnings.append("source_sha256 invalide : chaîne hexadécimale attendue")
            return {
                "source_sha256": None,
                "source_sha256_verified": False,
                "source_integrity": "INVALID",
                "declared_source_size": declared_size,
            }, warnings
        if require_digest:
            warnings.append("source_sha256 absent du cartouche")
        return {
            "source_sha256": None,
            "source_sha256_verified": None,
            "source_integrity": "UNDECLARED",
            "declared_source_size": declared_size,
        }, warnings

    if not SHA256_RE.fullmatch(declared):
        warnings.append("source_sha256 invalide : 64 caractères hexadécimaux attendus")
        return {
            "source_sha256": declared,
            "source_sha256_verified": False,
            "source_integrity": "INVALID",
            "declared_source_size": declared_size,
        }, warnings

    normalized = declared.casefold()
    observed, hash_error = _file_sha256(source)
    if hash_error or observed is None:
        warnings.append(hash_error or "Vérification SHA-256 impossible")
        return {
            "source_sha256": normalized,
            "source_sha256_verified": False,
            "source_integrity": "UNREADABLE",
            "declared_source_size": declared_size,
        }, warnings

    verified = observed == normalized
    if not verified:
        warnings.append("source_sha256 ne correspond pas aux octets exacts de la source")
    return {
        "source_sha256": normalized,
        "source_sha256_verified": verified,
        "source_integrity": "VERIFIED" if verified else "MISMATCH",
        "declared_source_size": declared_size,
    }, warnings


def _safe_source_ref(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, None
    if "/" in value or "\\" in value or value in {".", ".."}:
        return None, "La source déclarée doit rester dans le même dossier"
    if Path(value).is_absolute() or Path(value).name != value:
        return None, "La source déclarée doit rester dans le même dossier"
    return value, None


def _subtitle(metadata: dict[str, Any]) -> str:
    parts = [
        _meta_string(metadata, "type"),
        _meta_string(metadata, "phase"),
        _meta_string(metadata, "index"),
        _meta_string(metadata, "document_date"),
    ]
    return " · ".join(part for part in parts if part) or "Cartouche Markdown"


def _filename_family_hint(
    workspace: str,
    relative_source: str,
    source: Path,
) -> tuple[str | None, str | None]:
    """Return a non-authoritative family/revision hint only for explicit filename markers."""
    match = FILENAME_REVISION_RE.fullmatch(source.stem)
    if match is None:
        return None, None
    base = match.group("base").strip(" ._-")
    token = match.group("token").strip()
    if not base or not token:
        return None, None
    parent = Path(relative_source).parent.as_posix()
    family_key = "\0".join((workspace, parent, base.casefold(), source.suffix.casefold()))
    family_id = "family-" + hashlib.sha256(family_key.encode("utf-8")).hexdigest()[:24]
    return family_id, token


def _document_card(workspace: str, root: Path, source: Path, cartouche: Path | None) -> dict[str, Any]:
    relative_source = source.relative_to(root).as_posix()
    source_parts = Path(relative_source).parts
    folder_ancestry = list(source_parts[:-1])
    inherited_project = folder_ancestry[0] if folder_ancestry else None
    document_family_hint, filename_revision_hint = _filename_family_hint(
        workspace, relative_source, source
    )
    extension = source.suffix.casefold()
    size = _file_size(source)

    if cartouche is None:
        source_format_supported = extension in HINDSIGHT_ELIGIBLE_EXTENSIONS
        folder_scoped = inherited_project is not None
        return {
            "workspace": workspace,
            "kind": "document",
            "path": relative_source,
            "parent_path": source.parent.relative_to(root).as_posix() if source.parent != root else "",
            "name": source.name,
            "title": source.name,
            "subtitle": (
                "Contexte hérité des dossiers"
                if folder_scoped
                else "Projet à identifier"
            ),
            "summary": "",
            "status": "FOLDER_SCOPED" if folder_scoped else "PENDING_SCOPE",
            "document_id": None,
            "document_identity_source": "technical",
            "document_family_hint": document_family_hint,
            "filename_revision_hint": filename_revision_hint,
            "source": source.name,
            "source_present": True,
            "cartouche": None,
            "cartouche_present": False,
            "cartouche_enrichment_admitted": False,
            "can_generate_cartouche": False,
            "project": inherited_project,
            "scope_project": inherited_project,
            "project_declared": None,
            "project_scope_conflict": False,
            "scope_move_confirmed": False,
            "project_scope_source": (
                "top_level_folder" if folder_scoped else "pending_identification"
            ),
            "folder_ancestry": folder_ancestry,
            "phase": None,
            "document_type": None,
            "index": None,
            "document_date": None,
            "issuer": None,
            "revision_mode": None,
            "revision_of": None,
            "revision_target_present": None,
            "revision_target_status": "NONE",
            "tags": [],
            "extension": extension.removeprefix(".").upper() or "FILE",
            "source_size": size,
            "source_sha256": None,
            "source_sha256_verified": None,
            "source_integrity": "UNDECLARED",
            "declared_source_size": None,
            "hindsight_format_supported": source_format_supported,
            "hindsight_eligible": source_format_supported,
            "hindsight_representation_candidate": (
                "source" if source_format_supported else None
            ),
            "heavy_binary": extension in HEAVY_VISIBLE_EXTENSIONS,
            "modified_at": _mtime_iso(source),
            "warnings": [],
        }

    metadata, body, cartouche_error = _read_cartouche(cartouche)
    warnings: list[str] = []
    if cartouche_error:
        warnings.append(cartouche_error)
    else:
        schema_warning = _schema_warning(metadata, CARTOUCHE_SCHEMA)
        if schema_warning:
            warnings.append(schema_warning)

    declared, source_ref_error = _safe_source_ref(_meta_string(metadata, "source"))
    if source_ref_error:
        warnings.append(source_ref_error)
    elif declared is None:
        warnings.append("Source non déclarée dans le cartouche")
    elif declared != source.name:
        warnings.append(f"Source déclarée différente du fichier apparié : {declared}")

    document_id = _meta_string(metadata, "document_id")
    if not document_id:
        warnings.append("document_id absent du cartouche")

    revision, revision_warnings = _revision_relation(metadata, document_id)
    warnings.extend(revision_warnings)

    integrity, integrity_warnings = _source_integrity(
        metadata,
        source,
        require_digest=extension == ".eml",
        require_size=extension == ".eml",
    )
    warnings.extend(integrity_warnings)

    cartouche_valid = not warnings
    derived_document_id = (
        "path-"
        + hashlib.sha256(
            f"{workspace}\0{relative_source}".encode("utf-8")
        ).hexdigest()[:32]
    )
    effective_document_id = document_id if cartouche_valid else derived_document_id
    title = (
        _meta_string(metadata, "title") or _first_heading(body) or source.stem
        if cartouche_valid
        else source.name
    )
    status = "CHECK" if warnings else "COMPLETE"
    source_format_supported = extension in HINDSIGHT_ELIGIBLE_EXTENSIONS
    email_cartouche_candidate = (
        extension == ".eml"
        and status == "COMPLETE"
        and integrity.get("source_sha256_verified") is True
    )
    producer_eligible = source_format_supported or email_cartouche_candidate
    declared_project = _meta_string(metadata, "project")
    scope_project = inherited_project or (declared_project if cartouche_valid else None)
    project_scope_conflict = bool(
        inherited_project
        and declared_project
        and inherited_project.casefold() != declared_project.casefold()
    )
    return {
        "workspace": workspace,
        "kind": "document",
        "path": relative_source,
        "parent_path": source.parent.relative_to(root).as_posix() if source.parent != root else "",
        "name": source.name,
        "title": title,
        "subtitle": _subtitle(metadata),
        "summary": _summary_excerpt(body),
        "status": status,
        "document_id": effective_document_id,
        "document_identity_source": (
            "cartouche" if cartouche_valid else "workspace_path_fallback"
        ),
        "document_family_hint": document_family_hint,
        "filename_revision_hint": filename_revision_hint,
        "source": source.name,
        "source_present": True,
        "cartouche": cartouche.name,
        "cartouche_present": True,
        "cartouche_enrichment_admitted": cartouche_valid,
        "can_generate_cartouche": False,
        "project": (
            declared_project or inherited_project
            if cartouche_valid
            else inherited_project
        ),
        "scope_project": scope_project,
        "project_declared": declared_project,
        "project_scope_conflict": project_scope_conflict,
        "scope_move_confirmed": (
            metadata.get("scope_move_confirmed") is True if cartouche_valid else False
        ),
        "project_scope_source": (
            "top_level_folder"
            if inherited_project
            else "cartouche"
            if declared_project and cartouche_valid
            else "pending_identification"
        ),
        "folder_ancestry": folder_ancestry,
        "phase": _meta_string(metadata, "phase") if cartouche_valid else None,
        "document_type": _meta_string(metadata, "type") if cartouche_valid else None,
        "index": _meta_string(metadata, "index"),
        "document_date": _meta_string(metadata, "document_date"),
        "issuer": _meta_string(metadata, "issuer") if cartouche_valid else None,
        **revision,
        "tags": _meta_tags(metadata) if cartouche_valid else [],
        "extension": extension.removeprefix(".").upper() or "FILE",
        "source_size": size,
        **integrity,
        "hindsight_format_supported": source_format_supported,
        "hindsight_eligible": producer_eligible,
        "hindsight_representation_candidate": (
            "cartouche" if email_cartouche_candidate
            else "source" if source_format_supported
            else None
        ),
        "heavy_binary": extension in HEAVY_VISIBLE_EXTENSIONS,
        "modified_at": max(
            (value for value in (_mtime_iso(source), _mtime_iso(cartouche)) if value),
            default=None,
        ),
        "warnings": warnings,
    }


def _orphan_cartouche_card(workspace: str, root: Path, cartouche: Path) -> dict[str, Any]:
    metadata, body, cartouche_error = _read_cartouche(cartouche)
    warnings: list[str] = []
    if cartouche_error:
        warnings.append(cartouche_error)
    else:
        schema_warning = _schema_warning(metadata, CARTOUCHE_SCHEMA)
        if schema_warning:
            warnings.append(schema_warning)

    declared, source_ref_error = _safe_source_ref(_meta_string(metadata, "source"))
    if source_ref_error:
        warnings.append(source_ref_error)

    source_path: Path | None = None
    source_present = False
    if declared:
        candidate = cartouche.parent / declared
        try:
            source_present = candidate.is_file() and not candidate.is_symlink() and _is_source_file(candidate)
        except OSError:
            source_present = False
        if source_present:
            source_path = candidate
            warnings.append("La source existe mais son basename ne correspond pas au cartouche")
    else:
        warnings.append("Source non déclarée dans le cartouche")

    document_id = _meta_string(metadata, "document_id")
    if not document_id:
        warnings.append("document_id absent du cartouche")

    revision, revision_warnings = _revision_relation(metadata, document_id)
    warnings.extend(revision_warnings)

    integrity = {
        "source_sha256": _meta_string(metadata, "source_sha256"),
        "source_sha256_verified": None,
        "source_integrity": "SOURCE_MISSING" if not source_present else "UNVERIFIED",
        "declared_source_size": _declared_source_size(metadata)[0],
    }
    if source_present and source_path is not None:
        integrity, integrity_warnings = _source_integrity(
            metadata,
            source_path,
            require_digest=source_path.suffix.casefold() == ".eml",
            require_size=source_path.suffix.casefold() == ".eml",
        )
        warnings.extend(integrity_warnings)

    fallback_title = cartouche.name[1:-3] if _is_document_cartouche(cartouche) else cartouche.stem
    title = _meta_string(metadata, "title") or _first_heading(body) or fallback_title
    status = "CHECK" if source_present else "SOURCE_MISSING"
    return {
        "workspace": workspace,
        "kind": "document",
        "path": (source_path or cartouche).relative_to(root).as_posix(),
        "parent_path": cartouche.parent.relative_to(root).as_posix() if cartouche.parent != root else "",
        "name": source_path.name if source_path else cartouche.name,
        "title": title,
        "subtitle": _subtitle(metadata) if source_present else "Source manquante",
        "summary": _summary_excerpt(body),
        "status": status,
        "document_id": document_id,
        "source": declared,
        "source_present": source_present,
        "cartouche": cartouche.name,
        "cartouche_present": True,
        "can_generate_cartouche": False,
        "project": _meta_string(metadata, "project"),
        "phase": _meta_string(metadata, "phase"),
        "document_type": _meta_string(metadata, "type"),
        "index": _meta_string(metadata, "index"),
        "document_date": _meta_string(metadata, "document_date"),
        "issuer": _meta_string(metadata, "issuer"),
        **revision,
        "tags": _meta_tags(metadata),
        "extension": source_path.suffix.removeprefix(".").upper() if source_path else None,
        "source_size": _file_size(source_path) if source_path else None,
        **integrity,
        "hindsight_format_supported": bool(
            source_path and source_path.suffix.casefold() in HINDSIGHT_ELIGIBLE_EXTENSIONS
        ),
        "hindsight_eligible": False,
        "hindsight_representation_candidate": None,
        "heavy_binary": bool(source_path and source_path.suffix.casefold() in HEAVY_VISIBLE_EXTENSIONS),
        "modified_at": max(
            (value for value in (_mtime_iso(cartouche), _mtime_iso(source_path) if source_path else None) if value),
            default=None,
        ),
        "warnings": warnings,
    }


def _folder_card(workspace: str, root: Path, folder: Path) -> dict[str, Any]:
    folder_context = next(
        (item for item in _direct_files(folder) if item.name.casefold() == "_folder.md"),
        None,
    )
    metadata: dict[str, Any] = {}
    body = ""
    warnings: list[str] = []
    if folder_context:
        metadata, body, error = _read_cartouche(folder_context)
        if error:
            warnings.append(error)
        else:
            schema_warning = _schema_warning(metadata, FOLDER_CONTEXT_SCHEMA)
            if schema_warning:
                warnings.append(schema_warning)

    relative_path = folder.relative_to(root).as_posix()
    return {
        "workspace": workspace,
        "kind": "folder",
        "path": relative_path,
        "parent_path": folder.parent.relative_to(root).as_posix() if folder.parent != root else "",
        "name": folder.name,
        "title": _meta_string(metadata, "title") or _first_heading(body) or folder.name,
        "subtitle": _meta_string(metadata, "phase") or "Dossier",
        "summary": _summary_excerpt(body),
        "status": "CHECK" if warnings else "FOLDER",
        "folder_context": folder_context.name if folder_context else None,
        "folder_context_present": folder_context is not None,
        "can_generate_folder_context": folder_context is None,
        "project": _meta_string(metadata, "project"),
        "phase": _meta_string(metadata, "phase"),
        "tags": _meta_tags(metadata),
        "modified_at": max(
            (value for value in (_mtime_iso(folder), _mtime_iso(folder_context) if folder_context else None) if value),
            default=None,
        ),
        "warnings": warnings,
    }


def _directory_document_cards(
    workspace: str,
    root: Path,
    folder: Path,
    direct_files: list[Path] | None = None,
) -> list[dict[str, Any]]:
    direct = _direct_files(folder) if direct_files is None else direct_files
    sources = [item for item in direct if _is_source_file(item)]
    cartouches = [item for item in direct if _is_document_cartouche(item)]
    # Pairing is exact and case-sensitive because Linux filenames are exact identifiers.
    cartouche_by_name = {item.name: item for item in cartouches}

    cards: list[dict[str, Any]] = []
    paired_cartouches: set[Path] = set()
    source_cards: list[dict[str, Any]] = []
    for source in sources:
        expected_name = _cartouche_name_for_source(source.name)
        cartouche = cartouche_by_name.get(expected_name)
        if cartouche:
            paired_cartouches.add(cartouche)
        card = _document_card(workspace, root, source, cartouche)
        cards.append(card)
        source_cards.append(card)

    # Portable storage can be case-insensitive and normalize Unicode even when Linux does not.
    portable_groups: dict[str, list[dict[str, Any]]] = {}
    for card in source_cards:
        key = unicodedata.normalize("NFC", card["name"]).casefold()
        portable_groups.setdefault(key, []).append(card)
    for group in portable_groups.values():
        exact_names = {card["name"] for card in group}
        if len(group) > 1 and len(exact_names) > 1:
            for card in group:
                card["status"] = "CHECK"
                card["name_conflict"] = "CASE_OR_UNICODE_COLLISION"
                card["hindsight_eligible"] = False
                card["hindsight_representation_candidate"] = None
                card["warnings"].append("Collision potentielle de nom sur stockage case-insensitive/normalisé")

    for cartouche in cartouches:
        if cartouche in paired_cartouches:
            continue
        metadata, _body, read_error = _read_cartouche(cartouche)
        # Ignore unrelated hidden Markdown unless it declares itself as a Pantheon cartouche
        # or otherwise carries cartouche-shaped metadata.
        if (
            read_error is None
            and _meta_string(metadata, "schema") != CARTOUCHE_SCHEMA
            and not any(key in metadata for key in ("source", "document_id"))
        ):
            continue
        declared_source = _meta_string(metadata, "source")
        if (
            declared_source
            and Path(declared_source).suffix.casefold() not in SCANNED_SOURCE_EXTENSIONS
        ):
            continue
        cards.append(_orphan_cartouche_card(workspace, root, cartouche))

    return cards


def _folder_match_key(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold().strip(" ._-")


def _folder_is_excluded(value: str, excluded_folder_names: set[str]) -> bool:
    key = _folder_match_key(value)
    if key in excluded_folder_names:
        return True
    if not {"archive", "archives"}.intersection(excluded_folder_names):
        return False
    decomposed = unicodedata.normalize("NFKD", key)
    ascii_key = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    tokens = {token for token in re.split(r"[^a-z0-9]+", ascii_key) if token}
    return bool({"archive", "archives"}.intersection(tokens))


def _walk_directories(
    root: Path,
    max_depth: int,
    excluded_folder_names: set[str] | None = None,
    excluded_paths: list[str] | None = None,
) -> Iterable[Path]:
    excluded_folder_names = excluded_folder_names or set()

    def visit(parent: Path, depth: int) -> Iterable[Path]:
        if depth > max_depth:
            return
        try:
            children = sorted(
                (item for item in parent.iterdir() if item.is_dir() and _visible(item)),
                key=lambda item: item.name.casefold(),
            )
        except OSError:
            return
        for child in children:
            if _folder_is_excluded(child.name, excluded_folder_names):
                if excluded_paths is not None:
                    excluded_paths.append(child.relative_to(root).as_posix())
                continue
            yield child
            if depth < max_depth:
                yield from visit(child, depth + 1)

    yield from visit(root, 1)


def _walk_workspace_entries(
    root: Path,
    max_depth: int,
    excluded_folder_names: set[str],
    excluded_paths: list[str],
) -> Iterable[tuple[Path, int, list[Path]]]:
    """Walk once per SMB directory and return its direct regular files.

    The earlier scan separately listed subdirectories and files, doubling remote
    directory enumeration. ``os.scandir`` lets the traversal reuse one listing.
    """

    def visit(folder: Path, depth: int) -> Iterable[tuple[Path, int, list[Path]]]:
        directories: list[Path] = []
        files: list[Path] = []
        try:
            with os.scandir(folder) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            if not _visible(path):
                                continue
                            if _folder_is_excluded(entry.name, excluded_folder_names):
                                excluded_paths.append(path.relative_to(root).as_posix())
                                continue
                            directories.append(path)
                        elif entry.is_file(follow_symlinks=False):
                            files.append(path)
                    except OSError:
                        continue
        except OSError:
            return

        files.sort(key=lambda item: item.name.casefold())
        yield folder, depth, files
        if depth >= max_depth:
            return
        directories.sort(key=lambda item: item.name.casefold())
        for directory in directories:
            yield from visit(directory, depth + 1)

    yield from visit(root, 0)


def _project_root_policy(label: str) -> dict[str, Any] | None:
    return PROJECT_ROOT_POLICIES.get(_folder_match_key(label))


def _empty_project_catalogue(
    roots: list[tuple[str, Path]],
    *,
    error: str | None = None,
) -> dict[str, Any]:
    root_states: list[dict[str, Any]] = []
    for label, root in roots:
        policy = _project_root_policy(label)
        if policy is None:
            continue
        root_states.append(
            {
                "workspace": label,
                "root_kind": policy["root_kind"],
                "state": policy["state"],
                "available": root.is_dir() and os.access(root, os.R_OK | os.X_OK),
                "error": error,
            }
        )
    return {
        "read_only": True,
        "bounded": True,
        "limit": PROJECT_CATALOGUE_MAX_ITEMS,
        "truncated": False,
        "project_count": 0,
        "conflict_count": 0,
        "projects": [],
        "conflicts": [],
        "roots": root_states,
    }


def _project_catalogue(
    roots: list[tuple[str, Path]],
    excluded_folder_names: set[str],
) -> dict[str, Any]:
    catalogue = _empty_project_catalogue(roots)
    projects: list[dict[str, Any]] = []
    truncated = False

    for label, root in roots:
        policy = _project_root_policy(label)
        if policy is None:
            continue
        available = root.is_dir() and os.access(root, os.R_OK | os.X_OK)
        if not available:
            continue
        try:
            with os.scandir(root) as entries:
                directories = []
                for entry in entries:
                    try:
                        if (
                            entry.is_symlink()
                            or not entry.is_dir(follow_symlinks=False)
                            or not _visible(Path(entry.path))
                            or _folder_is_excluded(entry.name, excluded_folder_names)
                        ):
                            continue
                    except OSError:
                        continue
                    directories.append(entry.name)
        except OSError:
            continue

        for name in sorted(directories, key=str.casefold):
            if len(projects) >= PROJECT_CATALOGUE_MAX_ITEMS:
                truncated = True
                break
            projects.append(
                {
                    "name": name,
                    "workspace": label,
                    "state": policy["state"],
                    "root_kind": policy["root_kind"],
                    "relative_root": name,
                    "available": True,
                    "write_requires_confirmation": bool(
                        policy["write_requires_confirmation"]
                    ),
                    "routing_status": "valid",
                    "automatic_routing_allowed": policy["state"] == "active",
                }
            )
        if truncated:
            break

    by_name: dict[str, list[dict[str, Any]]] = {}
    for project in projects:
        key = unicodedata.normalize("NFKC", project["name"]).casefold()
        by_name.setdefault(key, []).append(project)

    conflicts: list[dict[str, Any]] = []
    for candidates in by_name.values():
        if len(candidates) < 2:
            continue
        for project in candidates:
            project["routing_status"] = "conflict"
            project["automatic_routing_allowed"] = False
        conflicts.append(
            {
                "name": candidates[0]["name"],
                "candidates": [
                    {
                        "name": project["name"],
                        "state": project["state"],
                        "root_kind": project["root_kind"],
                        "relative_root": project["relative_root"],
                    }
                    for project in candidates
                ],
            }
        )

    projects.sort(
        key=lambda project: (
            unicodedata.normalize("NFKC", project["name"]).casefold(),
            0 if project["state"] == "active" else 1,
            project["root_kind"],
        )
    )
    conflicts.sort(
        key=lambda conflict: unicodedata.normalize(
            "NFKC", conflict["name"]
        ).casefold()
    )
    catalogue.update(
        {
            "truncated": truncated,
            "project_count": len(projects),
            "conflict_count": len(conflicts),
            "projects": projects,
            "conflicts": conflicts,
        }
    )
    return catalogue


def scan_workspaces(
    roots: list[tuple[str, Path]],
    max_depth: int = 2,
    excluded_folder_names: Iterable[str] = DEFAULT_EXCLUDED_FOLDERS,
) -> dict[str, Any]:
    workspaces: list[dict[str, Any]] = []
    excluded_names = {
        key
        for value in excluded_folder_names
        if (key := _folder_match_key(value))
    }

    for label, root in roots:
        cards: list[dict[str, Any]] = []
        errors: list[str] = []
        excluded_paths: list[str] = []
        root_available = root.is_dir() and os.access(root, os.R_OK | os.X_OK)
        if not root_available:
            errors.append("Source AFFAIRES indisponible")
        else:
            candidates: list[dict[str, Any]] = []
            for folder, depth, direct_files in _walk_workspace_entries(
                root,
                max_depth,
                excluded_names,
                excluded_paths,
            ):
                if depth > 0:
                    candidates.append(_folder_card(label, root, folder))
                candidates.extend(
                    _directory_document_cards(label, root, folder, direct_files)
                )
                if len(candidates) >= MAX_ITEMS:
                    errors.append(f"Inventaire limité aux {MAX_ITEMS} premiers éléments")
                    break

            cards.extend(candidates[:MAX_ITEMS])

        workspaces.append({
            "name": label,
            "available": root_available,
            "cards": cards,
            "errors": errors,
            "excluded_folders": excluded_paths,
        })

    # A copied bundle must not silently become the same Hindsight document in two places.
    document_ids: dict[str, list[dict[str, Any]]] = {}
    for workspace in workspaces:
        for card in workspace["cards"]:
            if card.get("kind") == "document" and card.get("document_id"):
                document_ids.setdefault(card["document_id"], []).append(card)
    for document_id, duplicates in document_ids.items():
        if len(duplicates) < 2:
            continue
        for card in duplicates:
            # Preserve a more specific broken-pair state such as SOURCE_MISSING.
            if card.get("status") == "COMPLETE":
                card["status"] = "CHECK"
            card["hindsight_eligible"] = False
            card["hindsight_representation_candidate"] = None
            card["identity_conflict"] = "DUPLICATE_DOCUMENT_ID"
            card["warnings"].append(f"document_id dupliqué dans AFFAIRES: {document_id}")

    for workspace in workspaces:
        for card in workspace["cards"]:
            target = card.get("revision_of")
            if not target or card.get("revision_target_status") == "INVALID":
                continue
            matches = document_ids.get(target, [])
            if len(matches) == 1:
                card["revision_target_present"] = True
                card["revision_target_status"] = "RESOLVED"
            elif len(matches) > 1:
                card["revision_target_present"] = True
                card["revision_target_status"] = "AMBIGUOUS"
            else:
                # Missing history is observable but does not make index/date authoritative
                # and does not block an otherwise valid current bundle.
                card["revision_target_present"] = False
                card["revision_target_status"] = "MISSING"

    totals = {status: 0 for status in STATUS_NAMES}
    total_items = 0
    document_count = 0
    folder_count = 0
    for workspace in workspaces:
        for card in workspace["cards"]:
            totals[card["status"]] = totals.get(card["status"], 0) + 1
            total_items += 1
            if card["kind"] == "folder":
                folder_count += 1
            else:
                document_count += 1

    generated_at = datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")
    project_catalogue = _project_catalogue(roots, excluded_names)
    project_catalogue["generated_at"] = generated_at
    return {
        "generated_at": generated_at,
        "projection": PROJECTION_ID,
        "read_only": True,
        "totals": totals,
        "workspace_count": len(workspaces),
        "item_count": total_items,
        "package_count": total_items,
        "document_count": document_count,
        "folder_count": folder_count,
        "workspaces": workspaces,
        "project_catalogue": project_catalogue,
    }


class _InotifyWatcher:
    """Best-effort Linux event accelerator; periodic reconcile remains authoritative."""

    _EVENT = struct.Struct("iIII")
    _IN_ATTRIB = 0x00000004
    _IN_CLOSE_WRITE = 0x00000008
    _IN_MOVED_FROM = 0x00000040
    _IN_MOVED_TO = 0x00000080
    _IN_CREATE = 0x00000100
    _IN_DELETE = 0x00000200
    _IN_DELETE_SELF = 0x00000400
    _IN_MOVE_SELF = 0x00000800
    _IN_Q_OVERFLOW = 0x00004000
    _IN_IGNORED = 0x00008000
    _IN_ISDIR = 0x40000000
    _WATCH_MASK = (
        _IN_ATTRIB
        | _IN_CLOSE_WRITE
        | _IN_MOVED_FROM
        | _IN_MOVED_TO
        | _IN_CREATE
        | _IN_DELETE
        | _IN_DELETE_SELF
        | _IN_MOVE_SELF
    )

    def __init__(
        self,
        roots: list[tuple[str, Path]],
        max_depth: int,
        on_event: Callable[[], None],
        excluded_folder_names: Iterable[str] = DEFAULT_EXCLUDED_FOLDERS,
    ) -> None:
        self._roots = [root for _, root in roots]
        self._max_depth = max_depth
        self._excluded_folder_names = {
            key
            for value in excluded_folder_names
            if (key := _folder_match_key(value))
        }
        self._on_event = on_event
        self._fd = -1
        self._libc: Any = None
        self._watches: dict[int, Path] = {}
        self._watch_lock = threading.RLock()
        self._stop = threading.Event()
        self._rebuild = threading.Event()
        self._thread: threading.Thread | None = None
        self.mode = "reconcile-only"

    def _within_depth(self, path: Path) -> bool:
        for root in self._roots:
            try:
                depth = len(path.relative_to(root).parts)
            except ValueError:
                continue
            if depth <= self._max_depth:
                return True
        return False

    def _add_watch(self, path: Path) -> None:
        if self._fd < 0 or not self._within_depth(path):
            return
        try:
            if not path.is_dir() or path.is_symlink() or not _visible(path):
                return
        except OSError:
            return
        wd = self._libc.inotify_add_watch(self._fd, os.fsencode(path), self._WATCH_MASK)
        if wd >= 0:
            with self._watch_lock:
                self._watches[int(wd)] = path

    def _reset_watches(self) -> None:
        if self._fd < 0:
            return
        with self._watch_lock:
            old = list(self._watches)
            self._watches.clear()
        for wd in old:
            try:
                self._libc.inotify_rm_watch(self._fd, wd)
            except Exception:
                pass
        for root in self._roots:
            try:
                if not root.is_dir():
                    continue
            except OSError:
                continue
            self._add_watch(root)
            for folder in _walk_directories(
                root,
                self._max_depth,
                self._excluded_folder_names,
            ):
                self._add_watch(folder)

    def start(self) -> bool:
        if not sys.platform.startswith("linux"):
            return False
        try:
            libc = ctypes.CDLL(None, use_errno=True)
            libc.inotify_init1.argtypes = [ctypes.c_int]
            libc.inotify_init1.restype = ctypes.c_int
            libc.inotify_add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
            libc.inotify_add_watch.restype = ctypes.c_int
            libc.inotify_rm_watch.argtypes = [ctypes.c_int, ctypes.c_int]
            libc.inotify_rm_watch.restype = ctypes.c_int
            fd = libc.inotify_init1(os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0))
        except (AttributeError, OSError):
            return False
        if fd < 0:
            return False

        self._libc = libc
        self._fd = int(fd)
        self._reset_watches()
        self.mode = "inotify"
        self._thread = threading.Thread(target=self._run, name="workspace-inotify", daemon=True)
        self._thread.start()
        return True

    def request_rebuild(self) -> None:
        if self._fd >= 0:
            self._rebuild.set()

    def _run(self) -> None:
        while not self._stop.is_set():
            if self._rebuild.is_set():
                self._rebuild.clear()
                self._reset_watches()
            try:
                readable, _, _ = select.select([self._fd], [], [], 0.5)
            except (OSError, ValueError):
                if self._stop.is_set():
                    break
                continue
            if not readable:
                continue
            try:
                payload = os.read(self._fd, 64 * 1024)
            except BlockingIOError:
                continue
            except OSError:
                if self._stop.is_set():
                    break
                continue

            offset = 0
            changed = False
            rebuild = False
            while offset + self._EVENT.size <= len(payload):
                wd, mask, _cookie, name_len = self._EVENT.unpack_from(payload, offset)
                offset += self._EVENT.size
                raw_name = payload[offset : offset + name_len]
                offset += name_len
                name = raw_name.rstrip(b"\0").decode(errors="surrogateescape") if raw_name else ""

                if mask & self._IN_Q_OVERFLOW:
                    changed = True
                    rebuild = True
                    continue

                with self._watch_lock:
                    base = self._watches.get(wd)
                if mask & self._IN_IGNORED:
                    with self._watch_lock:
                        self._watches.pop(wd, None)
                    continue

                if base and name and mask & self._IN_ISDIR and mask & (self._IN_CREATE | self._IN_MOVED_TO):
                    self._add_watch(base / name)
                    rebuild = True
                if mask & self._IN_ISDIR and mask & (
                    self._IN_DELETE_SELF | self._IN_MOVE_SELF | self._IN_MOVED_FROM | self._IN_DELETE
                ):
                    rebuild = True
                if mask & self._WATCH_MASK:
                    changed = True

            if rebuild:
                self._rebuild.set()
            if changed:
                self._on_event()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
        if self._fd >= 0:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = -1
        self.mode = "stopped"


class WorkspaceIndex:
    """Reconstructible technical index for fast Cockpit reads and later sync ownership."""

    SCHEMA_VERSION = "1"

    def __init__(
        self,
        roots: list[tuple[str, Path]],
        max_depth: int,
        state_db: Path,
        *,
        reconcile_seconds: float = 60.0,
        debounce_seconds: float = 0.5,
        enable_watcher: bool = True,
        producer: HindsightProducer | None = None,
        excluded_folder_names: Iterable[str] = DEFAULT_EXCLUDED_FOLDERS,
    ) -> None:
        self.roots = roots
        self.max_depth = max_depth
        self.state_db = state_db
        self.reconcile_seconds = max(0.1, float(reconcile_seconds))
        self.debounce_seconds = max(0.0, float(debounce_seconds))
        self.enable_watcher = enable_watcher
        self.producer = producer
        self.excluded_folder_names = tuple(excluded_folder_names)
        self._snapshot: dict[str, Any] = {
            "generated_at": None,
            "projection": PROJECTION_ID,
            "read_only": True,
            "totals": {status: 0 for status in STATUS_NAMES},
            "workspace_count": len(roots),
            "item_count": 0,
            "package_count": 0,
            "document_count": 0,
            "folder_count": 0,
            "workspaces": [{"name": label, "available": False, "cards": [], "errors": ["Index non initialisé"]} for label, _ in roots],
            "project_catalogue": _empty_project_catalogue(roots, error="Index non initialisé"),
            "index_state": {"mode": "initializing", "watcher": "reconcile-only"},
            "hindsight_producer": {"enabled": producer is not None},
        }
        self._snapshot_lock = threading.RLock()
        self._reconcile_lock = threading.Lock()
        self._dirty = threading.Event()
        self._stop = threading.Event()
        self._coordinator: threading.Thread | None = None
        self._watcher = _InotifyWatcher(
            roots,
            max_depth,
            self.mark_dirty,
            self.excluded_folder_names,
        )
        self._watcher_mode = "reconcile-only"
        self._last_error: str | None = None

    def _persist(self, snapshot: dict[str, Any], reason: str) -> str | None:
        try:
            self.state_db.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self.state_db, timeout=5)
            try:
                connection.execute("PRAGMA journal_mode=DELETE")
                connection.execute("PRAGMA synchronous=NORMAL")
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS workspace_entries (
                        entry_key TEXT PRIMARY KEY,
                        workspace TEXT NOT NULL,
                        kind TEXT NOT NULL,
                        path TEXT NOT NULL,
                        parent_path TEXT NOT NULL DEFAULT '',
                        status TEXT NOT NULL,
                        payload_json TEXT NOT NULL,
                        observed_at TEXT NOT NULL
                    )
                    """
                )
                entry_columns = {
                    str(row[1]) for row in connection.execute("PRAGMA table_info(workspace_entries)").fetchall()
                }
                if "parent_path" not in entry_columns:
                    connection.execute("ALTER TABLE workspace_entries ADD COLUMN parent_path TEXT NOT NULL DEFAULT ''")
                    connection.execute(
                        "UPDATE workspace_entries SET parent_path=COALESCE(json_extract(payload_json, '$.parent_path'), '')"
                    )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS workspace_meta (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS idx_workspace_entries_parent "
                    "ON workspace_entries(workspace, parent_path, path)"
                )
                observed_at = snapshot["generated_at"] or ""
                with connection:
                    connection.execute("DELETE FROM workspace_entries")
                    for workspace in snapshot["workspaces"]:
                        workspace_name = workspace["name"]
                        for card in workspace["cards"]:
                            entry_key = json.dumps(
                                [workspace_name, card.get("kind"), card.get("path"), card.get("cartouche")],
                                ensure_ascii=False,
                                separators=(",", ":"),
                            )
                            connection.execute(
                                """
                                INSERT INTO workspace_entries(
                                    entry_key, workspace, kind, path, parent_path, status, payload_json, observed_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    entry_key,
                                    workspace_name,
                                    card.get("kind") or "",
                                    card.get("path") or "",
                                    card.get("parent_path") or "",
                                    card.get("status") or "",
                                    json.dumps(card, ensure_ascii=False, separators=(",", ":")),
                                    observed_at,
                                ),
                            )
                    meta = {
                        "schema_version": self.SCHEMA_VERSION,
                        "projection": PROJECTION_ID,
                        "last_reconcile_at": observed_at,
                        "last_reconcile_reason": reason,
                        "project_catalogue": json.dumps(
                            snapshot.get("project_catalogue") or _empty_project_catalogue(self.roots),
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ),
                    }
                    connection.executemany(
                        "INSERT OR REPLACE INTO workspace_meta(key, value) VALUES (?, ?)",
                        list(meta.items()),
                    )
            finally:
                connection.close()
        except (OSError, sqlite3.Error) as exc:
            return f"{type(exc).__name__}: {exc}"
        return None

    def reconcile(self, reason: str = "manual") -> dict[str, Any]:
        with self._reconcile_lock:
            snapshot = scan_workspaces(
                self.roots,
                self.max_depth,
                self.excluded_folder_names,
            )
            if self.producer is None:
                snapshot["hindsight_producer"] = {"enabled": False}
            else:
                try:
                    snapshot["hindsight_producer"] = self.producer.reconcile(snapshot)
                except Exception as exc:  # producer failure must not take Cockpit navigation down
                    snapshot["hindsight_producer"] = {
                        **self.producer.health(),
                        "last_error": f"{type(exc).__name__}: {exc}",
                    }
            index_state = {
                "mode": "indexed",
                "watcher": self._watcher_mode,
                "last_reconcile_at": snapshot["generated_at"],
                "last_reconcile_reason": reason,
                "reconcile_seconds": self.reconcile_seconds,
            }
            snapshot["index_state"] = index_state
            persistence_error = self._persist(snapshot, reason)
            if persistence_error:
                index_state["state_error"] = persistence_error
                self._last_error = persistence_error
            else:
                self._last_error = None
            with self._snapshot_lock:
                self._snapshot = snapshot
            if self._watcher_mode == "inotify":
                self._watcher.request_rebuild()
            return snapshot

    def snapshot(self) -> dict[str, Any]:
        with self._snapshot_lock:
            return self._snapshot

    def project_catalogue(self) -> dict[str, Any]:
        with self._snapshot_lock:
            catalogue = self._snapshot.get("project_catalogue")
            if isinstance(catalogue, dict):
                return catalogue
        return _empty_project_catalogue(self.roots, error="Catalogue non initialisé")

    def health(self) -> dict[str, Any]:
        with self._snapshot_lock:
            state = dict(self._snapshot.get("index_state") or {})
        state["state_error"] = self._last_error
        state["hindsight_producer"] = (
            self.producer.health() if self.producer is not None else {"enabled": False}
        )
        return state

    def mark_dirty(self) -> None:
        self._dirty.set()

    def _coordinator_loop(self) -> None:
        try:
            self.reconcile("startup")
        except Exception as exc:  # HTTP health remains available while a remote root is slow
            self._last_error = f"{type(exc).__name__}: {exc}"
            print(f"workspace-cockpit: initial reconcile failed: {self._last_error}", file=sys.stderr)
        next_periodic = time.monotonic() + self.reconcile_seconds
        while not self._stop.is_set():
            timeout = max(0.0, next_periodic - time.monotonic())
            dirty = self._dirty.wait(timeout)
            if self._stop.is_set():
                break
            if dirty:
                if self._stop.wait(self.debounce_seconds):
                    break
                self._dirty.clear()
                reason = "watch"
            else:
                reason = "periodic"
            try:
                self.reconcile(reason)
            except Exception as exc:  # defensive: an index failure must not kill the HTTP service
                self._last_error = f"{type(exc).__name__}: {exc}"
                print(f"workspace-cockpit: reconcile failed: {self._last_error}", file=sys.stderr)
            next_periodic = time.monotonic() + self.reconcile_seconds

    def start(self) -> None:
        if self.enable_watcher and self._watcher.start():
            self._watcher_mode = "inotify"
        self._coordinator = threading.Thread(
            target=self._coordinator_loop,
            name="workspace-reconcile",
            daemon=True,
        )
        self._coordinator.start()

    def stop(self) -> None:
        self._stop.set()
        self._dirty.set()
        if self._coordinator:
            self._coordinator.join(timeout=2)
        self._watcher.stop()


class PersistedWorkspaceProjection:
    """Read-only Cockpit view over the producer-owned SQLite projection."""

    def __init__(self, roots: list[tuple[str, Path]], state_db: Path) -> None:
        self.roots = roots
        self.state_db = state_db
        self._last_error: str | None = None

    def start(self) -> None:
        return

    def stop(self) -> None:
        return

    def _empty(self, error: str | None = None) -> dict[str, Any]:
        workspaces = [
            {
                "name": label,
                "available": root.is_dir() and os.access(root, os.R_OK | os.X_OK),
                "cards": [],
                "errors": [error or "Projection producer non disponible"],
            }
            for label, root in self.roots
        ]
        return {
            "generated_at": None,
            "projection": PROJECTION_ID,
            "read_only": True,
            "totals": {status: 0 for status in STATUS_NAMES},
            "workspace_count": len(workspaces),
            "item_count": 0,
            "package_count": 0,
            "document_count": 0,
            "folder_count": 0,
            "workspaces": workspaces,
            "project_catalogue": _empty_project_catalogue(self.roots, error=error),
            "index_state": {
                "mode": "persisted-projection",
                "watcher": "external-producer",
                "last_reconcile_at": None,
                "last_reconcile_reason": None,
                "state_error": error,
            },
            "hindsight_producer": {"enabled": True, "mode": "external-producer"},
        }

    def project_catalogue(self) -> dict[str, Any]:
        if not self.state_db.is_file():
            return _empty_project_catalogue(self.roots, error="producer index absent")
        try:
            connection = sqlite3.connect(self.state_db, timeout=2)
            try:
                connection.execute("PRAGMA query_only=ON")
                row = connection.execute(
                    "SELECT value FROM workspace_meta WHERE key='project_catalogue'"
                ).fetchone()
            finally:
                connection.close()
        except (OSError, sqlite3.Error):
            return _empty_project_catalogue(
                self.roots, error="workspace index unavailable"
            )
        if row is None:
            return _empty_project_catalogue(
                self.roots, error="project catalogue absent"
            )
        try:
            catalogue = json.loads(str(row[0]))
        except json.JSONDecodeError:
            return _empty_project_catalogue(
                self.roots, error="project catalogue invalid"
            )
        return (
            catalogue
            if isinstance(catalogue, dict)
            else _empty_project_catalogue(
                self.roots, error="project catalogue invalid"
            )
        )

    def overview(self) -> dict[str, Any]:
        """Return bounded workspace totals without transferring every indexed card."""
        if not self.state_db.is_file():
            return self._empty("producer index absent")
        try:
            connection = sqlite3.connect(self.state_db, timeout=2)
            connection.row_factory = sqlite3.Row
            try:
                connection.execute("PRAGMA query_only=ON")
                counts = connection.execute(
                    "SELECT workspace, kind, status, COUNT(*) AS count "
                    "FROM workspace_entries GROUP BY workspace, kind, status"
                ).fetchall()
                meta_rows = connection.execute(
                    "SELECT key, value FROM workspace_meta"
                ).fetchall()
            finally:
                connection.close()
        except (OSError, sqlite3.Error) as exc:
            return self._empty(f"{type(exc).__name__}: workspace index unavailable")

        by_workspace: dict[str, dict[str, int]] = {}
        totals = {status: 0 for status in STATUS_NAMES}
        folder_count = document_count = 0
        for row in counts:
            workspace = str(row["workspace"])
            values = by_workspace.setdefault(workspace, {"folder_count": 0, "document_count": 0})
            count = int(row["count"])
            if row["kind"] == "folder":
                values["folder_count"] += count
                folder_count += count
            else:
                values["document_count"] += count
                document_count += count
            status = str(row["status"] or "")
            totals[status] = totals.get(status, 0) + count

        workspaces = []
        for label, root in self.roots:
            values = by_workspace.get(label, {"folder_count": 0, "document_count": 0})
            workspaces.append({
                "name": label,
                "available": root.is_dir() and os.access(root, os.R_OK | os.X_OK),
                **values,
                "errors": [],
            })
        for label, values in sorted(by_workspace.items()):
            if label not in {name for name, _ in self.roots}:
                workspaces.append({"name": label, "available": False, **values, "errors": ["Workspace non configuré"]})
        metadata = {str(row["key"]): str(row["value"]) for row in meta_rows}
        item_count = folder_count + document_count
        self._last_error = None
        return {
            "generated_at": metadata.get("last_reconcile_at"),
            "projection": metadata.get("projection", PROJECTION_ID),
            "read_only": True,
            "totals": totals,
            "workspace_count": len(workspaces),
            "item_count": item_count,
            "package_count": len(workspaces),
            "document_count": document_count,
            "folder_count": folder_count,
            "workspaces": workspaces,
            "index_state": {
                "mode": "persisted-projection",
                "watcher": "external-producer",
                "last_reconcile_at": metadata.get("last_reconcile_at"),
                "last_reconcile_reason": metadata.get("last_reconcile_reason"),
                "state_error": None,
            },
            "hindsight_producer": {"enabled": True, "mode": "external-producer"},
        }

    def children(self, workspace_name: str, relative_folder: str, *, offset: int = 0, limit: int = 100, query: str = "") -> dict[str, Any]:
        """Read one indexed directory level; never recurse or scan the NAS here."""
        if not self.state_db.is_file():
            raise RuntimeError("workspace_index_unavailable")
        if offset < 0 or limit < 1 or limit > 200:
            raise ValueError("invalid_pagination")
        if relative_folder.startswith("/") or ".." in Path(relative_folder).parts or "\\" in relative_folder:
            raise ValueError("invalid_folder_path")
        try:
            connection = sqlite3.connect(self.state_db, timeout=2)
            connection.row_factory = sqlite3.Row
            try:
                connection.execute("PRAGMA query_only=ON")
                folder_card = None
                if relative_folder:
                    row = connection.execute(
                        "SELECT payload_json FROM workspace_entries WHERE workspace=? AND kind='folder' AND path=? LIMIT 1",
                        (workspace_name, relative_folder),
                    ).fetchone()
                    if row is None:
                        raise ValueError("folder_not_indexed")
                    folder_card = json.loads(str(row["payload_json"]))
                elif connection.execute(
                    "SELECT 1 FROM workspace_entries WHERE workspace=? LIMIT 1",
                    (workspace_name,),
                ).fetchone() is None:
                    raise ValueError("workspace_not_indexed")
                clauses = "workspace=? AND parent_path=?"
                parameters: list[Any] = [workspace_name, relative_folder]
                search_pattern = "%"
                if query:
                    clauses += " AND lower(payload_json) LIKE lower(?) ESCAPE '\\'"
                    escaped_query = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                    search_pattern = f"%{escaped_query}%"
                    parameters.append(search_pattern)
                total = int(connection.execute(
                    f"SELECT COUNT(*) FROM workspace_entries WHERE {clauses}",
                    parameters,
                ).fetchone()[0])
                rows = connection.execute(
                    """SELECT e.payload_json,
                              EXISTS(
                                SELECT 1 FROM workspace_entries child
                                WHERE child.workspace=e.workspace
                                  AND child.parent_path=e.path
                              ) AS has_children
                       FROM workspace_entries e
                       WHERE e.workspace=? AND e.parent_path=?
                         AND (?='' OR lower(e.payload_json) LIKE lower(?) ESCAPE '\\')
                       ORDER BY e.path COLLATE NOCASE LIMIT ? OFFSET ?""",
                    (workspace_name, relative_folder, query, search_pattern, limit, offset),
                ).fetchall()
            finally:
                connection.close()
        except ValueError:
            raise
        except (OSError, sqlite3.Error, json.JSONDecodeError) as exc:
            raise RuntimeError("workspace_index_unavailable") from exc
        cards = []
        for row in rows:
            try:
                card = json.loads(str(row["payload_json"]))
            except json.JSONDecodeError:
                continue
            if isinstance(card, dict):
                if card.get("kind") == "folder":
                    card["has_children"] = bool(row["has_children"])
                cards.append(card)
        return {
            "workspace": workspace_name,
            "path": relative_folder,
            "folder": folder_card,
            "cards": cards,
            "total": total,
            "offset": offset,
            "limit": limit,
            "query": query,
        }

    def snapshot(self) -> dict[str, Any]:
        if not self.state_db.is_file():
            self._last_error = "producer index absent"
            return self._empty(self._last_error)
        try:
            connection = sqlite3.connect(self.state_db, timeout=2)
            connection.row_factory = sqlite3.Row
            try:
                connection.execute("PRAGMA query_only=ON")
                rows = connection.execute(
                    "SELECT workspace, payload_json FROM workspace_entries ORDER BY workspace, path"
                ).fetchall()
                meta_rows = connection.execute(
                    "SELECT key, value FROM workspace_meta"
                ).fetchall()
            finally:
                connection.close()
        except (OSError, sqlite3.Error) as exc:
            self._last_error = f"{type(exc).__name__}: {exc}"
            return self._empty(self._last_error)

        metadata = {str(row["key"]): str(row["value"]) for row in meta_rows}
        project_catalogue = _empty_project_catalogue(
            self.roots, error="project catalogue absent"
        )
        raw_project_catalogue = metadata.get("project_catalogue")
        if raw_project_catalogue:
            try:
                parsed_project_catalogue = json.loads(raw_project_catalogue)
            except json.JSONDecodeError:
                parsed_project_catalogue = None
            if isinstance(parsed_project_catalogue, dict):
                project_catalogue = parsed_project_catalogue
        cards_by_workspace: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            try:
                payload = json.loads(str(row["payload_json"]))
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                cards_by_workspace.setdefault(str(row["workspace"]), []).append(payload)

        workspaces: list[dict[str, Any]] = []
        known = {label for label, _ in self.roots}
        for label, root in self.roots:
            workspaces.append(
                {
                    "name": label,
                    "available": root.is_dir() and os.access(root, os.R_OK | os.X_OK),
                    "cards": cards_by_workspace.pop(label, []),
                    "errors": [],
                }
            )
        for label, cards in sorted(cards_by_workspace.items()):
            if label not in known:
                workspaces.append(
                    {"name": label, "available": False, "cards": cards, "errors": ["Workspace non configuré"]}
                )

        totals = {status: 0 for status in STATUS_NAMES}
        document_count = 0
        folder_count = 0
        for workspace in workspaces:
            for card in workspace["cards"]:
                status = str(card.get("status") or "")
                totals[status] = totals.get(status, 0) + 1
                if card.get("kind") == "folder":
                    folder_count += 1
                else:
                    document_count += 1
        item_count = document_count + folder_count
        generated_at = metadata.get("last_reconcile_at")
        self._last_error = None
        return {
            "generated_at": generated_at,
            "projection": metadata.get("projection", PROJECTION_ID),
            "read_only": True,
            "totals": totals,
            "workspace_count": len(workspaces),
            "item_count": item_count,
            "package_count": item_count,
            "document_count": document_count,
            "folder_count": folder_count,
            "workspaces": workspaces,
            "project_catalogue": project_catalogue,
            "index_state": {
                "mode": "persisted-projection",
                "watcher": "external-producer",
                "last_reconcile_at": generated_at,
                "last_reconcile_reason": metadata.get("last_reconcile_reason"),
                "state_error": None,
            },
            "hindsight_producer": {"enabled": True, "mode": "external-producer"},
        }

    def health(self) -> dict[str, Any]:
        snapshot = self.snapshot()
        state = dict(snapshot.get("index_state") or {})
        state["state_error"] = self._last_error
        return state


class WorkspaceProjectionRouter:
    """Present independently produced workspace indexes as one read-only Cockpit view."""

    def __init__(self, projections: list[tuple[list[str], PersistedWorkspaceProjection]]) -> None:
        self.projections = projections
        self.by_workspace = {name: projection for names, projection in projections for name in names}

    def start(self) -> None:
        for _, projection in self.projections:
            projection.start()

    def stop(self) -> None:
        for _, projection in self.projections:
            projection.stop()

    def children(self, workspace_name: str, relative_folder: str, **kwargs: Any) -> dict[str, Any]:
        projection = self.by_workspace.get(workspace_name)
        if projection is None:
            raise ValueError("workspace_not_found")
        return projection.children(workspace_name, relative_folder, **kwargs)

    def project_catalogue(self) -> dict[str, Any]:
        # The catalogue is owned by the projection whose roots carry a project-root policy.
        for _, projection in self.projections:
            if any(_project_root_policy(label) is not None for label, _ in projection.roots):
                return projection.project_catalogue()
        return self.projections[0][1].project_catalogue()

    def _combine(self, method: str) -> dict[str, Any]:
        results = [getattr(projection, method)() for _, projection in self.projections]
        combined = dict(results[0])
        combined["workspaces"] = [workspace for result in results for workspace in result["workspaces"]]
        combined["workspace_count"] = len(combined["workspaces"])
        combined["totals"] = {
            status: sum(int(result.get("totals", {}).get(status, 0)) for result in results)
            for status in set().union(*(result.get("totals", {}) for result in results))
        }
        for key in ("item_count", "package_count", "document_count", "folder_count"):
            combined[key] = sum(int(result.get(key, 0)) for result in results)
        combined["index_state"] = {
            "mode": "multiple-persisted-projections",
            "workspaces": {
                name: result.get("index_state", {})
                for (names, _), result in zip(self.projections, results)
                for name in names
            },
        }
        return combined

    def overview(self) -> dict[str, Any]:
        return self._combine("overview")

    def snapshot(self) -> dict[str, Any]:
        return self._combine("snapshot")

    def health(self) -> dict[str, Any]:
        return {
            "mode": "multiple-persisted-projections",
            "workspaces": {name: projection.health() for names, projection in self.projections for name in names},
        }


def _path_is_within(candidate: Path, root: Path) -> bool:
    try:
        candidate.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except (OSError, RuntimeError, ValueError):
        return False


class CockpitHandler(BaseHTTPRequestHandler):
    roots: list[tuple[str, Path]] = []
    max_depth = 2
    excluded_folder_names: tuple[str, ...] = DEFAULT_EXCLUDED_FOLDERS
    workspace_index: WorkspaceIndex | PersistedWorkspaceProjection | WorkspaceProjectionRouter | None = None
    role_trace_url = ""
    role_trace_key = ""
    memory_reconciliation: MemoryReconciliationService | None = None
    navigation: list[dict[str, str]] = []
    expected_worker_root = ""
    expected_worker_source = ""
    scope_request_path = Path("/var/lib/pantheon-workspace-cockpit/apply-affaires-scope.request")

    def _headers(self, status: HTTPStatus, content_type: str, *, csp: str | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            csp or (
                "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
                "connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
            ),
        )
        self.end_headers()

    def _json(self, value: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self._headers(status, "application/json; charset=utf-8")
        self.wfile.write(body)

    def _proxy_role_trace(self, upstream_path: str, *, stream: bool = False) -> None:
        if not self.role_trace_url or not self.role_trace_key:
            self._json({"error": "role_trace_not_configured"}, HTTPStatus.NOT_FOUND)
            return
        headers = {"Authorization": f"Bearer {self.role_trace_key}"}
        last_event_id = self.headers.get("Last-Event-ID", "").strip()
        if last_event_id:
            headers["Last-Event-ID"] = last_event_id
        request = Request(f"{self.role_trace_url}{upstream_path}", headers=headers)
        try:
            response = urlopen(request, timeout=190 if stream else 5)
        except HTTPError as exc:
            body = exc.read(16_384)
            self._headers(HTTPStatus(exc.code), exc.headers.get_content_type() or "application/json")
            self.wfile.write(body)
            return
        except (OSError, URLError):
            self._json({"error": "role_trace_unavailable"}, HTTPStatus.BAD_GATEWAY)
            return
        with response:
            content_type = response.headers.get("Content-Type", "application/json")
            self._headers(HTTPStatus.OK, content_type)
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                self.wfile.write(chunk)
                if stream:
                    self.wfile.flush()

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        path = urlparse(self.path).path
        if path == "/workspace":
            path = "/"
        elif path.startswith("/workspace/"):
            path = path[len("/workspace"):]
        if path == "/api/producers/configure-affaires":
            origin = self.headers.get("Origin", "")
            if origin and urlparse(origin).netloc != self.headers.get("Host", ""):
                self._json({"error": "same_origin_required"}, HTTPStatus.FORBIDDEN)
                return
            if self.headers.get("X-Pantheon-Intent", "") != "configure-affaires-scope":
                self._json({"error": "explicit_intent_required"}, HTTPStatus.FORBIDDEN)
                return
            try:
                if int(self.headers.get("Content-Length", "0")) != 0:
                    raise ValueError("body_not_allowed")
                self.scope_request_path.parent.mkdir(parents=True, exist_ok=True)
                fd = os.open(self.scope_request_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                with os.fdopen(fd, "w", encoding="utf-8") as request_file:
                    request_file.write(datetime.now(timezone.utc).isoformat() + "\n")
            except FileExistsError:
                pass
            except (OSError, ValueError):
                self._json({"error": "scope_request_unavailable"}, HTTPStatus.SERVICE_UNAVAILABLE)
                return
            self._json({"status": "queued"}, HTTPStatus.ACCEPTED)
            return
        match = re.fullmatch(r"/api/documents/([^/]+)/reconcile-memory", path)
        if not match:
            self._json({"error": "not_found"}, HTTPStatus.NOT_FOUND)
            return
        if self.memory_reconciliation is None:
            self._json({"error": "memory_reconciliation_not_configured"}, HTTPStatus.NOT_FOUND)
            return
        if self.headers.get("X-Pantheon-Intent", "").strip() != "memory-reconcile":
            self._json({"error": "explicit_intent_required"}, HTTPStatus.FORBIDDEN)
            return
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().casefold()
        if content_type != "application/json":
            self._json({"error": "application_json_required"}, HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._json({"error": "invalid_content_length"}, HTTPStatus.BAD_REQUEST)
            return
        if content_length < 0 or content_length > 8192:
            self._json({"error": "request_too_large"}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            return
        try:
            raw = self.rfile.read(content_length)
            body = json.loads(raw.decode("utf-8") or "{}")
        except (UnicodeError, json.JSONDecodeError):
            self._json({"error": "invalid_json"}, HTTPStatus.BAD_REQUEST)
            return
        if not isinstance(body, dict):
            self._json({"error": "json_object_required"}, HTTPStatus.BAD_REQUEST)
            return
        focus = body.get("focus", "")
        if not isinstance(focus, str):
            self._json({"error": "focus_must_be_string"}, HTTPStatus.BAD_REQUEST)
            return
        document_id = unquote(match.group(1))
        snapshot = (
            self.workspace_index.snapshot()
            if self.workspace_index is not None
            else scan_workspaces(self.roots, self.max_depth, self.excluded_folder_names)
        )
        try:
            result = self.memory_reconciliation.reconcile(
                snapshot,
                document_id,
                focus=focus,
            )
        except ReconciliationResidencyError as exc:
            self._json(
                {"error": "memory_reconciliation_residency_failure", "detail": str(exc)},
                HTTPStatus.BAD_GATEWAY,
            )
            return
        except ReconciliationError as exc:
            self._json(
                {"error": "memory_reconciliation_failed", "detail": str(exc)},
                HTTPStatus.CONFLICT,
            )
            return
        self._json(result, HTTPStatus.OK)

    def _resolve_indexed_source(self, workspace_name: str, relative_path: str) -> Path | None:
        snapshot = (
            self.workspace_index.snapshot()
            if self.workspace_index is not None
            else scan_workspaces(self.roots, self.max_depth)
        )
        matched = any(
            card.get("kind") == "document"
            and card.get("source_present") is True
            and card.get("path") == relative_path
            for workspace in snapshot.get("workspaces") or []
            if workspace.get("name") == workspace_name
            for card in workspace.get("cards") or []
        )
        if not matched:
            return None
        root = dict(self.roots).get(workspace_name)
        if root is None:
            return None
        try:
            root_resolved = root.resolve(strict=True)
            candidate = (root / relative_path).resolve(strict=True)
            candidate.relative_to(root_resolved)
            if not candidate.is_file() or candidate.is_symlink():
                return None
        except (OSError, RuntimeError, ValueError):
            return None
        return candidate

    def _serve_indexed_source(self, workspace_name: str, relative_path: str) -> None:
        source = self._resolve_indexed_source(workspace_name, relative_path)
        if source is None:
            self._json({"error": "source_not_available"}, HTTPStatus.NOT_FOUND)
            return
        try:
            size = source.stat().st_size
            handle = source.open("rb")
        except OSError:
            self._json({"error": "source_unavailable"}, HTTPStatus.NOT_FOUND)
            return
        filename = source.name.replace('"', "_").replace("\r", "_").replace("\n", "_")
        content_type = mimetypes.guess_type(source.name)[0] or "application/octet-stream"
        status = HTTPStatus.OK
        start = 0
        end = size - 1
        range_header = self.headers.get("Range", "").strip()
        if range_header:
            match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header)
            if (
                not match
                or size == 0
                or len(match.group(1)) > 20
                or len(match.group(2)) > 20
            ):
                handle.close()
                self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            first, last = match.groups()
            if first:
                start = int(first)
                end = min(int(last), size - 1) if last else size - 1
            else:
                suffix_length = int(last or "0")
                if suffix_length <= 0:
                    handle.close()
                    self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                start = max(size - suffix_length, 0)
            if start >= size or end < start:
                handle.close()
                self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            status = HTTPStatus.PARTIAL_CONTENT
        length = max(end - start + 1, 0)
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        if status is HTTPStatus.PARTIAL_CONTENT:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Disposition", f'inline; filename="{filename}"')
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        handle.seek(start)
        with handle:
            remaining = length
            while remaining:
                chunk = handle.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/workspace":
            path = "/"
        elif path.startswith("/workspace/"):
            path = path[len("/workspace"):]
        if path == "/api/producers/status":
            self._json(producer_status(self.expected_worker_root, self.expected_worker_source))
            return
        if path == "/api/producers/logs":
            query = parse_qs(parsed.query)
            name = (query.get("producer") or [""])[0]
            try:
                lines = int((query.get("lines") or ["80"])[0])
                self._json(producer_logs(name, lines))
            except ValueError:
                self._json({"error": "invalid_producer_or_limit"}, HTTPStatus.BAD_REQUEST)
            return
        if path == "/api/source":
            query = parse_qs(parsed.query, keep_blank_values=False)
            workspace_name = (query.get("workspace") or [""])[0]
            relative_path = (query.get("path") or [""])[0]
            if not workspace_name or not relative_path:
                self._json({"error": "workspace_and_path_required"}, HTTPStatus.BAD_REQUEST)
                return
            self._serve_indexed_source(workspace_name, relative_path)
            return
        if path == "/api/health":
            index_state = self.workspace_index.health() if self.workspace_index else {"mode": "direct-scan"}
            self._json(
                {
                    "status": "ok",
                    "projection": PROJECTION_ID,
                    "read_only": True,
                    "role_trace": bool(self.role_trace_url),
                    "memory_reconciliation": self.memory_reconciliation is not None,
                    "index": index_state,
                }
            )
            return
        if path == "/api/navigation":
            self._json({"links": self.navigation})
            return
        if path == "/api/project-catalogue":
            if not self.workspace_index:
                self._json(
                    {"error": "workspace_index_unavailable"},
                    HTTPStatus.SERVICE_UNAVAILABLE,
                )
                return
            self._json(self.workspace_index.project_catalogue())
            return
        if path == "/api/workspaces":
            if self.workspace_index:
                self._json(self.workspace_index.snapshot())
            else:
                self._json(scan_workspaces(
                    self.roots,
                    self.max_depth,
                    self.excluded_folder_names,
                ))
            return
        if path == "/api/workspace-overview":
            if not self.workspace_index:
                self._json({"error": "workspace_index_unavailable"}, HTTPStatus.SERVICE_UNAVAILABLE)
                return
            self._json(self.workspace_index.overview())
            return
        if path == "/api/workspace-children":
            query = parse_qs(parsed.query, keep_blank_values=True)
            workspace_name = (query.get("workspace") or [""])[0]
            relative_folder = (query.get("path") or [""])[0]
            try:
                offset = max(0, int((query.get("offset") or ["0"])[0]))
                limit = min(200, max(1, int((query.get("limit") or ["100"])[0])))
            except ValueError:
                self._json({"error": "invalid_pagination"}, HTTPStatus.BAD_REQUEST)
                return
            if not workspace_name or workspace_name not in dict(self.roots):
                self._json({"error": "workspace_not_found"}, HTTPStatus.NOT_FOUND)
                return
            try:
                search_query = (query.get("q") or [""])[0][:128]
                if not self.workspace_index:
                    raise RuntimeError("workspace_index_unavailable")
                result = self.workspace_index.children(workspace_name, relative_folder, offset=offset, limit=limit, query=search_query)
            except ValueError as exc:
                status = HTTPStatus.BAD_REQUEST if str(exc) in {"invalid_pagination", "invalid_folder_path"} else HTTPStatus.NOT_FOUND
                self._json({"error": str(exc)}, status)
                return
            except (RuntimeError, StopIteration):
                self._json({"error": "workspace_index_unavailable"}, HTTPStatus.SERVICE_UNAVAILABLE)
                return
            self._json(result)
            return
        if path == "/api/role-traces/latest":
            self._proxy_role_trace("/internal/role-traces/latest")
            return
        role_match = re.fullmatch(r"/api/role-traces/(run_[A-Za-z0-9]{8,128})(/events)?", path)
        if role_match:
            run_id, suffix = role_match.groups()
            self._proxy_role_trace(
                f"/internal/role-traces/{run_id}{suffix or ''}",
                stream=suffix == "/events",
            )
            return
        if path.startswith("/vendor/pdfjs/"):
            relative_asset = unquote(path.removeprefix("/vendor/pdfjs/"))
            asset_root = (STATIC_ROOT / "vendor" / "pdfjs").resolve()
            try:
                target = (asset_root / relative_asset).resolve(strict=True)
                target.relative_to(asset_root)
                if not target.is_file():
                    raise ValueError("asset is not a file")
                body = target.read_bytes()
            except (OSError, RuntimeError, ValueError):
                self._json({"error": "not_found"}, HTTPStatus.NOT_FOUND)
                return
            content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            if target.suffix == ".mjs":
                content_type = "text/javascript; charset=utf-8"
            elif target.suffix == ".ftl":
                content_type = "text/plain; charset=utf-8"
            elif content_type.startswith("text/"):
                content_type += "; charset=utf-8"
            pdfjs_csp = (
                "default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; worker-src 'self' blob:; "
                "style-src 'self'; img-src 'self' blob: data:; media-src blob:; font-src 'self' data:; "
                "connect-src 'self' blob: data:; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
            )
            self._headers(HTTPStatus.OK, content_type, csp=pdfjs_csp if target.name == "viewer.html" else None)
            self.wfile.write(body)
            return
        asset = {
            "/": "index.html",
            "/app.js": "app.js",
            "/styles.css": "styles.css",
            "/role_trace_graph.css": "role_trace_graph.css",
            "/vendor/swiper-14.3.0-bundle.min.js": "vendor/swiper-14.3.0-bundle.min.js",
            "/vendor/swiper-14.3.0-bundle.min.css": "vendor/swiper-14.3.0-bundle.min.css",
        }.get(path)
        if not asset:
            self._json({"error": "not_found"}, HTTPStatus.NOT_FOUND)
            return
        target = STATIC_ROOT / asset
        try:
            body = target.read_bytes()
        except OSError:
            self._json({"error": "asset_unavailable"}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type == "application/javascript":
            content_type += "; charset=utf-8"
        self._headers(HTTPStatus.OK, content_type)
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"workspace-cockpit: {self.address_string()} {format % args}", file=sys.stderr)


def _root(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("expected NAME=/absolute/path")
    name, raw_path = value.split("=", 1)
    path = Path(raw_path)
    if not name.strip() or not path.is_absolute():
        raise argparse.ArgumentTypeError("expected NAME=/absolute/path")
    return name.strip(), path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8189)
    parser.add_argument("--root", action="append", type=_root, required=True)
    parser.add_argument("--max-depth", type=int, default=2, choices=range(1, 17))
    parser.add_argument(
        "--exclude-folder",
        action="append",
        default=[],
        help="exact directory name to skip recursively; repeatable (directory names containing the word Archive/Archives are always skipped)",
    )
    parser.add_argument(
        "--state-db",
        default=os.getenv("WORKSPACE_INDEX_DB", "/tmp/pantheon-workspace-cockpit/index.sqlite3"),
        help="absolute path to reconstructible SQLite index state",
    )
    parser.add_argument(
        "--reconcile-seconds",
        type=float,
        default=float(os.getenv("WORKSPACE_RECONCILE_SECONDS", "60")),
        help="periodic full reconcile interval (default 60s)",
    )
    parser.add_argument(
        "--watch-debounce-ms",
        type=int,
        default=int(os.getenv("WORKSPACE_WATCH_DEBOUNCE_MS", "500")),
        help="coalesce filesystem event bursts before reconcile",
    )
    parser.add_argument("--no-watch", action="store_true", help="disable inotify acceleration; periodic reconcile remains")
    parser.add_argument(
        "--projection-only",
        action="store_true",
        help="serve the producer-owned persisted projection without scanning or producing",
    )
    parser.add_argument(
        "--workspace-db",
        action="append",
        type=_root,
        default=[],
        metavar="NAME=PATH",
        help="with --projection-only, read this root from its own producer index instead of --state-db",
    )
    parser.add_argument(
        "--hindsight-url",
        default=os.getenv("WORKSPACE_HINDSIGHT_URL", ""),
        help="Hindsight base URL; producer stays disabled when omitted",
    )
    parser.add_argument(
        "--hindsight-bank-id",
        default=os.getenv("WORKSPACE_HINDSIGHT_BANK_ID", ""),
        help="target Hindsight bank id; required with --hindsight-url",
    )
    parser.add_argument(
        "--hindsight-parser",
        default=os.getenv("WORKSPACE_HINDSIGHT_PARSER", "markitdown"),
        help="file parser requested from Hindsight (default markitdown)",
    )
    parser.add_argument(
        "--hindsight-max-submits-per-reconcile",
        type=int,
        default=int(os.getenv("WORKSPACE_HINDSIGHT_MAX_SUBMITS_PER_RECONCILE", "4")),
        help="bound new Hindsight file submissions per reconcile",
    )
    parser.add_argument(
        "--hindsight-max-file-mb",
        type=int,
        default=int(os.getenv("WORKSPACE_HINDSIGHT_MAX_FILE_MB", "100")),
        help="reject a source before buffering it when larger than this many MiB",
    )
    parser.add_argument(
        "--hindsight-settle-observations",
        type=int,
        default=int(os.getenv("WORKSPACE_HINDSIGHT_SETTLE_OBSERVATIONS", "1")),
        help="require identical source fingerprints across this many reconciles before retain",
    )
    parser.add_argument(
        "--hindsight-source-kind",
        default=os.getenv("WORKSPACE_HINDSIGHT_SOURCE_KIND", ""),
        help="optional provenance tag such as project-sync",
    )
    parser.add_argument(
        "--reconcile-hermes-url",
        default=os.getenv("WORKSPACE_RECONCILE_HERMES_URL", ""),
        help="dedicated no-tool Hermes profile base URL for on-demand memory reconciliation",
    )
    parser.add_argument(
        "--reconcile-max-context-chars",
        type=int,
        default=int(os.getenv("WORKSPACE_RECONCILE_MAX_CONTEXT_CHARS", "48000")),
        help="maximum serialized Hindsight/cartouche context sent to Hermes",
    )
    parser.add_argument("--check", action="store_true", help="scan once, print summary, and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configured_exclusions = [
        value.strip()
        for value in os.getenv("WORKSPACE_EXCLUDED_FOLDERS", "").split(",")
        if value.strip()
    ]
    excluded_folder_names = tuple(dict.fromkeys(
        (*DEFAULT_EXCLUDED_FOLDERS, *configured_exclusions, *args.exclude_folder)
    ))
    if args.check:
        result = scan_workspaces(args.root, args.max_depth, excluded_folder_names)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if all(workspace["available"] for workspace in result["workspaces"]) else 1
    state_db = Path(args.state_db)
    if not state_db.is_absolute():
        raise SystemExit("--state-db must be an absolute path")
    if args.reconcile_seconds < 0.1:
        raise SystemExit("--reconcile-seconds must be >= 0.1")
    if args.watch_debounce_ms < 0:
        raise SystemExit("--watch-debounce-ms must be >= 0")
    if args.hindsight_max_submits_per_reconcile < 1:
        raise SystemExit("--hindsight-max-submits-per-reconcile must be >= 1")
    if args.hindsight_max_file_mb < 1:
        raise SystemExit("--hindsight-max-file-mb must be >= 1")
    if args.hindsight_settle_observations < 1:
        raise SystemExit("--hindsight-settle-observations must be >= 1")
    if args.reconcile_max_context_chars < 8000:
        raise SystemExit("--reconcile-max-context-chars must be >= 8000")
    if bool(args.hindsight_url.strip()) != bool(args.hindsight_bank_id.strip()):
        raise SystemExit("--hindsight-url and --hindsight-bank-id must be configured together")
    if any(_path_is_within(state_db, root) for _, root in args.root):
        raise SystemExit("--state-db must remain outside every watched workspace root")
    workspace_dbs = dict(args.workspace_db)
    if len(workspace_dbs) != len(args.workspace_db) or any(name not in dict(args.root) for name in workspace_dbs):
        raise SystemExit("--workspace-db names must be unique configured roots")
    if workspace_dbs and not args.projection_only:
        raise SystemExit("--workspace-db requires --projection-only")
    if any(not db.is_absolute() or any(_path_is_within(db, root) for _, root in args.root) for db in workspace_dbs.values()):
        raise SystemExit("--workspace-db paths must be absolute and outside every watched workspace root")

    producer: HindsightProducer | None = None
    hindsight_client: HindsightHTTPClient | None = None
    if args.hindsight_url.strip():
        hindsight_client = HindsightHTTPClient(
            args.hindsight_url.strip(),
            args.hindsight_bank_id.strip(),
            authorization=os.getenv("WORKSPACE_HINDSIGHT_AUTHORIZATION", "").strip(),
            timeout_seconds=float(os.getenv("WORKSPACE_HINDSIGHT_TIMEOUT_SECONDS", "30")),
            parser=args.hindsight_parser,
            max_file_bytes=args.hindsight_max_file_mb * 1024 * 1024,
        )
        if not args.projection_only:
            producer = HindsightProducer(
                roots=args.root,
                state_db=state_db,
                client=hindsight_client,
                max_submits_per_reconcile=args.hindsight_max_submits_per_reconcile,
                settle_observations=args.hindsight_settle_observations,
                source_kind=args.hindsight_source_kind,
            )

    reconcile_hermes_url = args.reconcile_hermes_url.strip().rstrip("/")
    reconcile_hermes_key = os.getenv("WORKSPACE_RECONCILE_HERMES_KEY", "").strip()
    if bool(reconcile_hermes_url) != bool(reconcile_hermes_key):
        raise SystemExit(
            "WORKSPACE_RECONCILE_HERMES_URL and WORKSPACE_RECONCILE_HERMES_KEY must be configured together"
        )
    if reconcile_hermes_url and hindsight_client is None:
        raise SystemExit("memory reconciliation requires the configured Hindsight producer/client")
    if reconcile_hermes_url and not reconcile_hermes_url.startswith(("http://", "https://")):
        raise SystemExit("WORKSPACE_RECONCILE_HERMES_URL must be HTTP(S)")

    CockpitHandler.roots = args.root
    CockpitHandler.expected_worker_root = os.getenv("WORKSPACE_EXPECTED_AFFAIRES_ROOT", "")
    CockpitHandler.expected_worker_source = os.getenv("WORKSPACE_EXPECTED_AFFAIRES_SOURCE", "")
    CockpitHandler.scope_request_path = Path(os.getenv(
        "WORKSPACE_SCOPE_REQUEST_PATH",
        "/var/lib/pantheon-workspace-cockpit/apply-affaires-scope.request",
    ))
    CockpitHandler.max_depth = args.max_depth
    CockpitHandler.excluded_folder_names = excluded_folder_names
    CockpitHandler.memory_reconciliation = None
    if reconcile_hermes_url and hindsight_client is not None:
        CockpitHandler.memory_reconciliation = MemoryReconciliationService(
            hindsight_client=hindsight_client,
            hermes_client=HermesReconciliationClient(
                reconcile_hermes_url,
                reconcile_hermes_key,
                timeout_seconds=float(os.getenv("WORKSPACE_RECONCILE_HERMES_TIMEOUT_SECONDS", "120")),
            ),
            max_context_chars=args.reconcile_max_context_chars,
        )

    if args.projection_only:
        primary_roots = [(name, root) for name, root in args.root if name not in workspace_dbs]
        projections: list[tuple[list[str], PersistedWorkspaceProjection]] = []
        if primary_roots:
            projections.append(([name for name, _ in primary_roots], PersistedWorkspaceProjection(primary_roots, state_db)))
        projections.extend(
            ([name], PersistedWorkspaceProjection([(name, root)], workspace_dbs[name]))
            for name, root in args.root
            if name in workspace_dbs
        )
        workspace_index: WorkspaceIndex | PersistedWorkspaceProjection | WorkspaceProjectionRouter = (
            WorkspaceProjectionRouter(projections) if len(projections) > 1 else projections[0][1]
        )
    else:
        workspace_index = WorkspaceIndex(
            args.root,
            args.max_depth,
            state_db,
            reconcile_seconds=args.reconcile_seconds,
            debounce_seconds=args.watch_debounce_ms / 1000.0,
            enable_watcher=not args.no_watch,
            producer=producer,
            excluded_folder_names=excluded_folder_names,
        )
    workspace_index.start()
    CockpitHandler.workspace_index = workspace_index

    role_trace_url = os.getenv("WORKSPACE_ROLE_TRACE_URL", "").strip().rstrip("/")
    role_trace_key = os.getenv("WORKSPACE_ROLE_TRACE_KEY", "").strip()
    if bool(role_trace_url) != bool(role_trace_key):
        raise SystemExit("WORKSPACE_ROLE_TRACE_URL and WORKSPACE_ROLE_TRACE_KEY must be configured together")
    if role_trace_url and not role_trace_url.startswith(("http://", "https://")):
        raise SystemExit("WORKSPACE_ROLE_TRACE_URL must be HTTP(S)")
    CockpitHandler.role_trace_url = role_trace_url
    CockpitHandler.role_trace_key = role_trace_key
    CockpitHandler.navigation = configured_navigation()
    server = ThreadingHTTPServer((args.host, args.port), CockpitHandler)
    print(f"workspace-cockpit listening on http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        workspace_index.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
