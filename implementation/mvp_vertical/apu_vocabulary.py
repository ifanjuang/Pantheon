"""Governed Project Anatomy vocabularies.

Three vocabularies are governed this way:

- ``source_kind`` of a source representation
  (``registries/architecture_source_kind_profile.registry.json``), extended by
  the local file named by ``PANTHEON_SOURCE_KIND_OVERLAY``;
- phase codes (``registries/architecture_phase_profile.registry.json``),
  extended by the local file named by ``PANTHEON_PHASE_OVERLAY``;
- property keys of attribute claims
  (``registries/architecture_property_profile.registry.json``), extended by the
  local file named by ``PANTHEON_PROPERTY_OVERLAY``. This one is advisory: an
  undeclared key is reported (``undeclared_properties``), never refused, so a
  reading or a human can record what the vocabulary does not name yet.

The repository registry declares the base entries. An agency may add entries
through a local file kept outside the repository. That file is add-only. It
cannot redeclare, change or deprecate an entry of the repository registry, and
an unreadable or invalid file makes the vocabulary unavailable instead of being
ignored: a silently ignored file would let a typo turn every agency entry into
a refusal, or worse, hide a damaged file.

Declaring an entry makes the identifier governable. It does not make a source
representation or a claim true, admitted, Evidence or approved, it does not
mean that a reader exists for a source kind, and it does not mean that a
project goes through a phase.
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
PHASE_REGISTRY = "apu_phase_profile"
PHASE_OVERLAY_ENV = "PANTHEON_PHASE_OVERLAY"
PROPERTY_REGISTRY = "apu_property_profile"
PROPERTY_OVERLAY_ENV = "PANTHEON_PROPERTY_OVERLAY"
# Same lists as shared.schema.yaml claim_value_type and object_family (kept equal by a test).
VALUE_TYPES = frozenset({"number", "boolean", "text", "range", "reference", "controlled_label", "structured"})
OBJECT_FAMILIES = frozenset({"spatial", "element", "assembly", "material", "system", "datum", "group", "type_definition"})
_AGENCY_STATUSES = {"active", "candidate"}
_BASE_FIELDS = {"id", "status", "label", "description"}

# Agency-file rules that differ between vocabularies, keyed by registry_id.
_AGENCY_RULES: dict[str, dict[str, Any]] = {
    "architecture_source_kind_profile": {"noun": "source kind", "categories": None, "aliases": False},
    "architecture_phase_profile": {
        "noun": "phase",
        "categories": {"mission_element", "project_stage"},
        "aliases": True,
    },
    "architecture_property_profile": {
        "noun": "property",
        "categories": None,
        "aliases": False,
        # Extra fields an agency property carries; facets come from the registry itself.
        "fields": {"facet", "value_type", "unit", "applies_to"},
    },
}

# Phase categories a project may declare as one of its phases.
PROJECT_PHASE_CATEGORIES = frozenset({"mission_element", "project_stage"})


class VocabularyUnavailable(ValueError):
    """The vocabulary cannot be read or is invalid; writes fail closed."""


class VocabularyRefused(ValueError):
    """A value is not declared, or is deprecated."""


@dataclass(frozen=True)
class Vocabulary:
    entries: dict[str, dict[str, Any]]
    agency_entries: frozenset[str]

    # Former name, kept for the source kind callers.
    @property
    def kinds(self) -> dict[str, dict[str, Any]]:
        return self.entries

    @property
    def agency_kinds(self) -> frozenset[str]:
        return self.agency_entries

    @property
    def aliases(self) -> dict[str, str]:
        """Each accepted alias with the code it names."""
        return alias_map(self.entries)

    def resolve(self, value: Any) -> Any:
        """The declared code an alias names; any other value unchanged."""
        if isinstance(value, str) and value not in self.entries:
            return self.aliases.get(value, value)
        return value


SourceKindVocabulary = Vocabulary


def alias_map(entries: dict[str, dict[str, Any]]) -> dict[str, str]:
    return {alias: code for code, entry in entries.items() for alias in entry.get("aliases") or []}


def _check_base_aliases(entries_by_id: dict[str, dict[str, Any]], noun: str) -> None:
    seen: set[str] = set()
    for code, entry in entries_by_id.items():
        for alias in entry.get("aliases") or []:
            if alias in entries_by_id or alias in seen:
                raise VocabularyUnavailable(f"{noun} alias '{alias}' of '{code}' is already declared")
            seen.add(alias)


def _merge_agency_aliases(
    entries_by_id: dict[str, dict[str, Any]], aliases: Any, *, pattern: re.Pattern[str], limit: int, noun: str
) -> None:
    if not isinstance(aliases, dict):
        raise VocabularyUnavailable(f"the agency {noun} file aliases must be an object")
    if len(aliases) > limit:
        raise VocabularyUnavailable(f"the agency {noun} file has more than {limit} aliases")
    base_aliases = alias_map(entries_by_id)
    for alias, code in aliases.items():
        where = f"agency alias {alias!r}"
        if not pattern.fullmatch(alias):
            raise VocabularyUnavailable(f"{where} is invalid")
        if alias in entries_by_id:
            owner = "the agency file" if entries_by_id[alias].get("origin") == "agency" else "the repository registry"
            raise VocabularyUnavailable(
                f"{where} redeclares '{alias}', already declared by {owner}; the agency file is add-only"
            )
        if alias in base_aliases:
            raise VocabularyUnavailable(f"{where} redefines an alias of the repository registry")
        target = entries_by_id.get(code) if isinstance(code, str) else None
        if target is None:
            raise VocabularyUnavailable(f"{where} names {code!r}, which is not declared")
        if target.get("status") == "deprecated":
            raise VocabularyUnavailable(f"{where} names '{code}', which is deprecated")
        target["aliases"] = [*(target.get("aliases") or []), alias]
        target["agency_aliases"] = [*(target.get("agency_aliases") or []), alias]


def merge_agency_file(base: dict[str, Any], overlay: Any) -> dict[str, dict[str, Any]]:
    """Return base entries plus the agency's additions, or raise.

    Pure function shared by the loader and the conformance tests.
    """
    rules = base.get("naming_rules") or {}
    pattern = re.compile(str(rules.get("id_pattern") or ""))
    limit = int(rules.get("max_agency_entries") or 0)
    agency_rules = _AGENCY_RULES.get(
        str(base.get("registry_id")), {"noun": "vocabulary", "categories": None, "aliases": False}
    )
    noun = agency_rules["noun"]
    categories: set[str] | None = agency_rules["categories"]
    extra_fields: set[str] = agency_rules.get("fields") or set()
    allowed = _BASE_FIELDS | ({"category"} if categories else set()) | extra_fields
    facets = {facet.get("id") for facet in base.get("facets") or [] if isinstance(facet, dict)}
    entries_by_id = {entry["id"]: dict(entry) for entry in base.get("entries", [])}
    _check_base_aliases(entries_by_id, noun)
    if overlay is None:
        return entries_by_id
    if not isinstance(overlay, dict):
        raise VocabularyUnavailable(f"the agency {noun} file must be a JSON object")
    if overlay.get("registry_kind") != "vocabulary_overlay":
        raise VocabularyUnavailable(f"the agency {noun} file must declare vocabulary_overlay")
    if overlay.get("extends") != base.get("registry_id"):
        raise VocabularyUnavailable(
            f"the agency {noun} file must extend {base.get('registry_id')}"
        )
    entries = overlay.get("entries")
    if not isinstance(entries, list):
        raise VocabularyUnavailable(f"the agency {noun} file has no entries list")
    if len(entries) > limit:
        raise VocabularyUnavailable(f"the agency {noun} file has more than {limit} entries")
    base_aliases = alias_map(entries_by_id)
    added: set[str] = set()
    for index, entry in enumerate(entries):
        where = f"agency entry {index}"
        if not isinstance(entry, dict):
            raise VocabularyUnavailable(f"{where} must be an object")
        extra = set(entry) - allowed
        if extra:
            raise VocabularyUnavailable(f"{where} has unknown fields: {', '.join(sorted(extra))}")
        value = entry.get("id")
        if not isinstance(value, str) or not pattern.fullmatch(value):
            raise VocabularyUnavailable(f"{where} has an invalid id: {value!r}")
        if value in entries_by_id or value in base_aliases:
            owner = "the agency file" if value in added else "the repository registry"
            raise VocabularyUnavailable(
                f"{where} redeclares '{value}', already declared by {owner}; the agency file is add-only"
            )
        if entry.get("status") not in _AGENCY_STATUSES:
            raise VocabularyUnavailable(f"{where} must be active or candidate")
        if categories is not None and entry.get("category") not in categories:
            raise VocabularyUnavailable(
                f"{where} must have category {' or '.join(sorted(categories))}"
            )
        for field in ("label", "description"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                raise VocabularyUnavailable(f"{where} needs a non-empty {field}")
        if extra_fields:
            _check_property_fields(entry, where=where, facets=facets)
        entries_by_id[value] = {**entry, "origin": "agency"}
        added.add(value)
    if "aliases" in overlay:
        if not agency_rules.get("aliases"):
            raise VocabularyUnavailable(f"the agency {noun} file cannot declare aliases")
        _merge_agency_aliases(entries_by_id, overlay["aliases"], pattern=pattern, limit=limit, noun=noun)
    return entries_by_id


def _check_property_fields(entry: dict[str, Any], *, where: str, facets: set[Any]) -> None:
    if entry.get("facet") not in facets:
        raise VocabularyUnavailable(f"{where} must have a facet declared by the profile")
    if entry.get("value_type") not in VALUE_TYPES:
        raise VocabularyUnavailable(f"{where} must have a value_type of the claim schema")
    unit = entry.get("unit")
    if unit is not None and (not isinstance(unit, str) or not 0 < len(unit) <= 20):
        raise VocabularyUnavailable(f"{where} has an invalid unit")
    families = entry.get("applies_to")
    if families is not None and (
        not isinstance(families, list) or not families or not set(families) <= OBJECT_FAMILIES
        or len(families) != len(set(families))
    ):
        raise VocabularyUnavailable(f"{where} applies_to must list object families")


_cache: dict[tuple[str, tuple[str, int, int] | tuple[None]], Vocabulary] = {}


def _overlay_stamp(path: Path | None, noun: str) -> tuple[str, int, int] | tuple[None]:
    if path is None:
        return (None,)
    try:
        stat = path.stat()
    except OSError as exc:
        raise VocabularyUnavailable(f"cannot read the agency {noun} file: {exc}") from exc
    return (str(path), stat.st_mtime_ns, stat.st_size)


def _load(registry: str, overlay_env: str, noun: str) -> Vocabulary:
    configured = os.environ.get(overlay_env, "").strip()
    path = Path(configured) if configured else None
    key = (registry, _overlay_stamp(path, noun))
    cached = _cache.get(key)
    if cached is not None:
        return cached
    try:
        base = pantheon_contracts.load_registry(registry)
    except pantheon_contracts.ContractUnavailable as exc:
        raise VocabularyUnavailable(str(exc)) from exc
    overlay: Any = None
    if path is not None:
        try:
            overlay = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise VocabularyUnavailable(f"cannot read the agency {noun} file: {exc}") from exc
    entries = merge_agency_file(base, overlay)
    vocabulary = Vocabulary(
        entries=entries,
        agency_entries=frozenset(
            value for value, entry in entries.items() if entry.get("origin") == "agency"
        ),
    )
    for stale in [cached_key for cached_key in _cache if cached_key[0] == registry]:
        del _cache[stale]
    _cache[key] = vocabulary
    return vocabulary


def source_kinds() -> Vocabulary:
    """Base source kind registry plus the agency file, cached until the file changes."""
    return _load(REGISTRY, OVERLAY_ENV, "source kind")


def phases() -> Vocabulary:
    """Base phase registry plus the agency file, cached until the file changes."""
    return _load(PHASE_REGISTRY, PHASE_OVERLAY_ENV, "phase")


def properties() -> Vocabulary:
    """Base property registry plus the agency file, cached until the file changes."""
    return _load(PROPERTY_REGISTRY, PROPERTY_OVERLAY_ENV, "property")


def describe_property(key: Any) -> dict[str, Any] | None:
    """The declared property (label, facet, value type, unit), or None when the key is not declared."""
    entry = properties().entries.get(key) if isinstance(key, str) else None
    return dict(entry) if entry is not None else None


def undeclared_properties(keys: Any) -> list[str]:
    """Keys the property profile does not name, sorted; reported, never refused."""
    declared = properties().entries
    return sorted({key for key in keys if isinstance(key, str) and key not in declared})


def _require(vocabulary: Vocabulary, value: Any, *, field: str, noun: str) -> dict[str, Any]:
    entry = vocabulary.entries.get(value) if isinstance(value, str) else None
    if entry is None:
        raise VocabularyRefused(f"{field} {value!r} is not declared in the {noun} vocabulary")
    if entry.get("status") == "deprecated":
        replacement = entry.get("replaced_by")
        hint = f"; use '{replacement}'" if replacement else ""
        raise VocabularyRefused(f"{field} '{value}' is deprecated{hint}")
    return entry


def require_source_kind(source_kind: Any) -> str:
    """Return the status of a declared kind; refuse an undeclared or deprecated one."""
    entry = _require(source_kinds(), source_kind, field="source_kind", noun="source kind")
    return str(entry["status"])


def resolve_phase(phase_code: Any) -> Any:
    """The declared phase code an alias names (``PC`` gives ``DPC``); any other value unchanged."""
    return phases().resolve(phase_code)


def require_phase(phase_code: Any, *, field: str = "phase", project_phase: bool = False) -> str:
    """Return the status of a declared phase code; refuse an undeclared or deprecated one.

    An alias declared by the registry or the agency file is accepted as the code
    it names. With ``project_phase`` the code must also be one a project can go
    through, which excludes non-project scope markers such as ``AGENCY_LIBRARY``.
    """
    vocabulary = phases()
    entry = _require(vocabulary, vocabulary.resolve(phase_code), field=field, noun="phase")
    if project_phase and entry.get("category") not in PROJECT_PHASE_CATEGORIES:
        raise VocabularyRefused(
            f"{field} '{phase_code}' is a non-project scope marker, not a project phase"
        )
    return str(entry["status"])
