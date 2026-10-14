"""Load and validate Pantheon Next canonical contracts.

A monorepo checkout reads the repository-root ``schemas/`` tree directly. A
built distribution reads an exact generated copy staged inside the wheel at
build time. The generated copy is distribution material only: it is never a
second version-controlled authority.

Conformance remains distinct from authorization. A payload that validates is
structurally conformant; it is not approved, Evidence, admitted or canonized.
"""

from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import jsonschema
from referencing import Registry, Resource
import yaml

from .contract_manifest import CANONICAL_REPOSITORY, CONTRACT_PATHS

_PACKAGE_ROOT = Path(__file__).resolve().parent
_MONOREPO_ROOT = Path(__file__).resolve().parents[2]
_GENERATED_ROOT = _PACKAGE_ROOT / "_generated_contracts"
_MANIFEST = _GENERATED_ROOT / "manifest.json"


class ContractViolation(ValueError):
    """An emitted payload does not conform to the canonical contract."""


class ContractUnavailable(RuntimeError):
    """A declared canonical contract is missing, unreadable or invalid."""


def _source_root() -> tuple[Path, str]:
    if (_MONOREPO_ROOT / "schemas").is_dir():
        return _MONOREPO_ROOT, "canonical-repository"
    if (_GENERATED_ROOT / "schemas").is_dir():
        return _GENERATED_ROOT, "packaged-build-artifact"
    raise ContractUnavailable(
        "canonical Pantheon contracts unavailable: neither monorepo schemas/ "
        "nor packaged generated contracts are present"
    )


def _relative_path(name: str) -> str:
    try:
        return CONTRACT_PATHS[name]
    except KeyError as exc:
        raise ContractUnavailable(f"unknown Pantheon contract: {name}") from exc


@lru_cache(maxsize=1)
def _packaged_manifest() -> dict[str, Any]:
    if not _MANIFEST.is_file():
        raise ContractUnavailable("packaged Pantheon contract manifest is missing")
    try:
        value = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractUnavailable("packaged Pantheon contract manifest is invalid") from exc
    if not isinstance(value, dict):
        raise ContractUnavailable("packaged Pantheon contract manifest is not a mapping")
    if value.get("kind") != "pantheon_generated_contract_payload":
        raise ContractUnavailable("packaged Pantheon contract manifest has an unknown kind")
    files = value.get("files")
    if not isinstance(files, dict) or not files:
        raise ContractUnavailable("packaged Pantheon contract manifest has no file digests")
    return value


def _verify_packaged_path(path: Path) -> None:
    try:
        relative = path.relative_to(_GENERATED_ROOT).as_posix()
    except ValueError as exc:
        raise ContractUnavailable(f"packaged contract escaped generated root: {path}") from exc
    expected = _packaged_manifest()["files"].get(relative)
    if not isinstance(expected, str) or len(expected) != 64:
        raise ContractUnavailable(f"packaged contract has no recorded digest: {relative}")
    try:
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ContractUnavailable(f"cannot read packaged Pantheon contract: {relative}") from exc
    if actual != expected:
        raise ContractUnavailable(
            f"packaged Pantheon contract digest mismatch: {relative}"
        )


def schema_path(name: str) -> Path:
    root, source_kind = _source_root()
    path = root / _relative_path(name)
    if not path.is_file():
        raise ContractUnavailable(
            f"canonical Pantheon contract unavailable: {name} ({_relative_path(name)})"
        )
    if source_kind == "packaged-build-artifact":
        _verify_packaged_path(path)
    return path


def _read_schema_path(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ContractUnavailable(f"cannot read Pantheon schema: {path}") from exc
    except yaml.YAMLError as exc:
        raise ContractUnavailable(f"Pantheon schema is not valid YAML: {path}") from exc
    if not isinstance(value, dict):
        raise ContractUnavailable(f"Pantheon schema is not a mapping: {path}")
    return value


@lru_cache(maxsize=None)
def load_schema(name: str) -> dict[str, Any]:
    return _read_schema_path(schema_path(name))


def _schema_with_file_id(name: str) -> dict[str, Any]:
    schema = dict(load_schema(name))
    schema.setdefault("$id", schema_path(name).resolve().as_uri())
    return schema


@lru_cache(maxsize=1)
def _all_schema_paths() -> tuple[Path, ...]:
    root, source_kind = _source_root()
    paths = tuple(sorted((root / "schemas").rglob("*.schema.yaml")))
    if not paths:
        raise ContractUnavailable("Pantheon schemas/ contains no *.schema.yaml contracts")
    if source_kind == "packaged-build-artifact":
        for path in paths:
            _verify_packaged_path(path)
    return paths


@lru_cache(maxsize=1)
def _registry() -> Registry:
    registry = Registry()
    for path in _all_schema_paths():
        schema = dict(_read_schema_path(path))
        schema.setdefault("$id", path.resolve().as_uri())
        try:
            resource = Resource.from_contents(schema)
        except Exception as exc:  # pragma: no cover - guarded by schema CI
            raise ContractUnavailable(f"cannot register Pantheon schema: {path}") from exc
        file_uri = path.resolve().as_uri()
        registry = registry.with_resource(file_uri, resource)
        resource_id = resource.id()
        if resource_id and resource_id != file_uri:
            registry = registry.with_resource(resource_id, resource)
    return registry


@lru_cache(maxsize=None)
def _validator(name: str) -> jsonschema.Draft202012Validator:
    schema = _schema_with_file_id(name)
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
    except jsonschema.SchemaError as exc:
        raise ContractUnavailable(f"Pantheon contract is not a valid schema: {name}") from exc
    return jsonschema.Draft202012Validator(schema, registry=_registry())


def problems(name: str, payload: Any) -> list[str]:
    """Deterministic conformance findings. Empty means structurally conformant."""
    try:
        errors = sorted(
            _validator(name).iter_errors(payload),
            key=lambda error: (
                tuple(str(part) for part in error.absolute_path),
                error.message,
            ),
        )
    except ContractUnavailable:
        raise
    except Exception as exc:
        raise ContractUnavailable(f"cannot resolve Pantheon contract graph: {name}") from exc
    return [
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in errors
    ]


def declared_properties(name: str) -> frozenset[str]:
    return frozenset(load_schema(name).get("properties", {}))


def validate(name: str, payload: Any) -> Any:
    found = problems(name, payload)
    if found:
        raise ContractViolation(
            f"payload does not conform to the canonical {name} contract: "
            + "; ".join(found)
        )
    return payload


def definition_enum(name: str, definition: str) -> tuple[Any, ...]:
    """Read one closed enum directly from a canonical schema definition."""
    value = load_schema(name).get("$defs", {}).get(definition, {}).get("enum")
    if not isinstance(value, list) or not value:
        raise ContractUnavailable(
            f"Pantheon contract {name} has no non-empty $defs.{definition}.enum"
        )
    return tuple(value)


def _git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(
        f"blob {len(raw)}\0".encode("ascii") + raw,
        usedforsecurity=False,
    ).hexdigest()


def _git_run(*args: str) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["git", "-C", str(_MONOREPO_ROOT), *args],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _repository_revision() -> str | None:
    result = _git_run("rev-parse", "HEAD")
    if result is None or result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value if len(value) == 40 else None


def _repository_file_matches_head(relative: str) -> bool | None:
    result = _git_run("diff", "--quiet", "HEAD", "--", relative)
    if result is None:
        return None
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def provenance(name: str) -> dict[str, Any]:
    """Provenance of the exact schema bytes currently used for validation."""
    path = schema_path(name)
    raw = path.read_bytes()
    _, source_kind = _source_root()

    if source_kind == "packaged-build-artifact":
        manifest = _packaged_manifest()
        source_commit = manifest.get("source_revision")
        repository_revision = manifest.get("repository_revision")
        working_tree_dirty = manifest.get("source_tree_dirty")
    else:
        repository_revision = _repository_revision()
        matches_head = _repository_file_matches_head(_relative_path(name))
        source_commit = repository_revision if matches_head is True else None
        working_tree_dirty = None if matches_head is None else not matches_head

    return {
        "source_repository": CANONICAL_REPOSITORY,
        "source_path": _relative_path(name),
        "source_commit": source_commit,
        "repository_revision": repository_revision,
        "working_tree_dirty": working_tree_dirty,
        "source_blob_sha": _git_blob_sha(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "posture": source_kind,
        "authority_transfer": False,
    }
