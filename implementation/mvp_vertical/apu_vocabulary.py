"""Governed Project Anatomy vocabularies used at write time.

Today this is the ``source_kind`` vocabulary of a source representation. The
repository registry (``registries/architecture_source_kind_profile.registry.json``)
declares the base kinds. An agency may add kinds through a local file kept
outside the repository, named by ``PANTHEON_SOURCE_KIND_OVERLAY``.

The local file is add-only. It cannot redeclare, change or deprecate a kind of
the repository registry, and an unreadable or invalid file makes the vocabulary
unavailable instead of being ignored: a silently ignored file would let a typo
turn every agency kind into a refusal, or worse, hide a damaged file.

Declaring a kind makes the identifier governable. It does not make a source
representation true, admitted, Evidence or approved, and it does not mean that
a reader exists for that kind.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from typing import Any

from . import pantheon_contracts

REGISTRY = "apu_source_kind_profile"
OVERLAY_ENV = "PANTHEON_SOURCE_KIND_OVERLAY"
_AGENCY_STATUSES = {"active", "candidate"}


class VocabularyUnavailable(ValueError):
    """The vocabulary cannot be read or is invalid; writes fail closed."""


class VocabularyRefused(ValueError):
    """A value is not declared, or is deprecated."""


@dataclass(frozen=True)
class SourceKindVocabulary:
    kinds: dict[str, dict[str, Any]]
    agency_kinds: frozenset[str]


def merge_agency_file(base: dict[str, Any], overlay: Any) -> dict[str, dict[str, Any]]:
    """Return base entries plus the agency's additions, or raise.

    Pure function shared by the loader and the conformance tests.
    """
    rules = base.get("naming_rules") or {}
    pattern = re.compile(str(rules.get("id_pattern") or ""))
    limit = int(rules.get("max_agency_entries") or 0)
    kinds = {entry["id"]: dict(entry) for entry in base.get("entries", [])}
    if overlay is None:
        return kinds
    if not isinstance(overlay, dict):
        raise VocabularyUnavailable("the agency source kind file must be a JSON object")
    if overlay.get("registry_kind") != "vocabulary_overlay":
        raise VocabularyUnavailable("the agency source kind file must declare vocabulary_overlay")
    if overlay.get("extends") != base.get("registry_id"):
        raise VocabularyUnavailable(
            f"the agency source kind file must extend {base.get('registry_id')}"
        )
    entries = overlay.get("entries")
    if not isinstance(entries, list):
        raise VocabularyUnavailable("the agency source kind file has no entries list")
    if len(entries) > limit:
        raise VocabularyUnavailable(f"the agency source kind file has more than {limit} entries")
    added: set[str] = set()
    for index, entry in enumerate(entries):
        where = f"agency entry {index}"
        if not isinstance(entry, dict):
            raise VocabularyUnavailable(f"{where} must be an object")
        extra = set(entry) - {"id", "status", "label", "description"}
        if extra:
            raise VocabularyUnavailable(f"{where} has unknown fields: {', '.join(sorted(extra))}")
        kind = entry.get("id")
        if not isinstance(kind, str) or not pattern.fullmatch(kind):
            raise VocabularyUnavailable(f"{where} has an invalid id: {kind!r}")
        if kind in kinds:
            owner = "the agency file" if kind in added else "the repository registry"
            raise VocabularyUnavailable(
                f"{where} redeclares '{kind}', already declared by {owner}; the agency file is add-only"
            )
        if entry.get("status") not in _AGENCY_STATUSES:
            raise VocabularyUnavailable(f"{where} must be active or candidate")
        for field in ("label", "description"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                raise VocabularyUnavailable(f"{where} needs a non-empty {field}")
        kinds[kind] = {**entry, "origin": "agency"}
        added.add(kind)
    return kinds


_cache: dict[tuple[str, int, int] | tuple[None], SourceKindVocabulary] = {}


def _overlay_stamp(path: Path | None) -> tuple[str, int, int] | tuple[None]:
    if path is None:
        return (None,)
    try:
        stat = path.stat()
    except OSError as exc:
        raise VocabularyUnavailable(f"cannot read the agency source kind file: {exc}") from exc
    return (str(path), stat.st_mtime_ns, stat.st_size)


def source_kinds() -> SourceKindVocabulary:
    """Base registry plus the agency file, cached until the file changes."""
    configured = os.environ.get(OVERLAY_ENV, "").strip()
    path = Path(configured) if configured else None
    stamp = _overlay_stamp(path)
    cached = _cache.get(stamp)
    if cached is not None:
        return cached
    try:
        base = pantheon_contracts.load_registry(REGISTRY)
    except pantheon_contracts.ContractUnavailable as exc:
        raise VocabularyUnavailable(str(exc)) from exc
    overlay: Any = None
    if path is not None:
        try:
            overlay = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise VocabularyUnavailable(f"cannot read the agency source kind file: {exc}") from exc
    kinds = merge_agency_file(base, overlay)
    vocabulary = SourceKindVocabulary(
        kinds=kinds,
        agency_kinds=frozenset(kind for kind, entry in kinds.items() if entry.get("origin") == "agency"),
    )
    _cache.clear()
    _cache[stamp] = vocabulary
    return vocabulary


def require_source_kind(source_kind: Any) -> str:
    """Return the status of a declared kind; refuse an undeclared or deprecated one."""
    vocabulary = source_kinds()
    entry = vocabulary.kinds.get(source_kind) if isinstance(source_kind, str) else None
    if entry is None:
        raise VocabularyRefused(
            f"source_kind {source_kind!r} is not declared in the source kind vocabulary"
        )
    if entry.get("status") == "deprecated":
        replacement = entry.get("replaced_by")
        hint = f"; use '{replacement}'" if replacement else ""
        raise VocabularyRefused(f"source_kind '{source_kind}' is deprecated{hint}")
    return str(entry["status"])
