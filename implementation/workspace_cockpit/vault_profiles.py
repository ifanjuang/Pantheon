"""Credential-free configuration loader for multi-vault producers."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
METADATA_PROFILES = {"affaires", "bibliotheque"}


def _valid_vault_name(value: str) -> bool:
    return 1 <= len(value) <= 48 and value[0].isalpha() and all(
        character.isalnum() or character in "_-" for character in value
    )


@dataclass(frozen=True)
class VaultProfile:
    name: str
    root: Path
    mount_root: Path
    bank_id: str
    source_kind: str
    metadata_profile: str
    max_depth: int = 8
    parser: str = "markitdown"
    max_file_mb: int = 100
    project_overview_prompt: str | None = None


@dataclass(frozen=True)
class VaultConfiguration:
    vaults: tuple[VaultProfile, ...]
    max_depth: int = 8
    reconcile_seconds: float = 60.0
    watch_debounce_ms: int = 500
    settle_observations: int = 2
    excluded_folders: tuple[str, ...] = ()
    missing_source_grace_seconds: float = 86400.0


def load_vault_configuration(path: Path | str) -> VaultConfiguration:
    source = Path(path)
    if not source.is_absolute():
        raise ValueError("vault configuration path must be absolute")
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("vault configuration is unreadable or invalid JSON") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("vault configuration schema_version must be 1")
    raw_vaults = payload.get("vaults")
    if not isinstance(raw_vaults, list) or not raw_vaults:
        raise ValueError("vault configuration requires a non-empty vaults array")
    max_depth = payload.get("max_depth", 8)
    if not isinstance(max_depth, int) or isinstance(max_depth, bool) or not 1 <= max_depth <= 16:
        raise ValueError("max_depth must be from 1 to 16")
    vaults: list[VaultProfile] = []
    names: set[str] = set()
    banks: set[str] = set()
    roots: set[Path] = set()
    for index, raw in enumerate(raw_vaults):
        if not isinstance(raw, dict):
            raise ValueError(f"vaults[{index}] must be an object")
        name = raw.get("name")
        root_value = raw.get("root")
        mount_root_value = raw.get("mount_root")
        bank_id = raw.get("bank_id")
        source_kind = raw.get("source_kind")
        metadata_profile = raw.get("metadata_profile")
        if not isinstance(name, str) or not _valid_vault_name(name):
            raise ValueError(f"vaults[{index}].name is invalid")
        if name.casefold() in {item.casefold() for item in names}:
            raise ValueError(f"duplicate vault name: {name}")
        if not isinstance(root_value, str) or not Path(root_value).is_absolute():
            raise ValueError(f"vaults[{index}].root must be absolute")
        root = Path(root_value).resolve(strict=False)
        if not isinstance(mount_root_value, str) or not Path(mount_root_value).is_absolute():
            raise ValueError(f"vaults[{index}].mount_root must be an absolute mounted source path")
        mount_root = Path(mount_root_value).resolve(strict=False)
        if root != mount_root and mount_root not in root.parents:
            raise ValueError(f"vaults[{index}].root must be inside mount_root")
        if any(root == old or root in old.parents or old in root.parents for old in roots):
            raise ValueError(f"duplicate vault root: {root}")
        if not isinstance(bank_id, str) or not bank_id.strip() or bank_id.casefold() in {item.casefold() for item in banks}:
            raise ValueError(f"vaults[{index}].bank_id must be non-empty and unique")
        if not isinstance(source_kind, str) or not source_kind.strip():
            raise ValueError(f"vaults[{index}].source_kind is required")
        if metadata_profile not in METADATA_PROFILES:
            raise ValueError(f"vaults[{index}].metadata_profile must be affaires or bibliotheque")
        parser = raw.get("parser", "markitdown")
        max_file_mb = raw.get("max_file_mb", 100)
        project_overview_prompt = raw.get("project_overview_prompt")
        vault_max_depth = raw.get("max_depth", max_depth)
        if not isinstance(vault_max_depth, int) or isinstance(vault_max_depth, bool) or not 1 <= vault_max_depth <= 16:
            raise ValueError(f"vaults[{index}].max_depth must be from 1 to 16")
        if not isinstance(parser, str) or not parser.strip():
            raise ValueError(f"vaults[{index}].parser must be a non-empty string")
        if not isinstance(max_file_mb, int) or isinstance(max_file_mb, bool) or not 1 <= max_file_mb <= 2048:
            raise ValueError(f"vaults[{index}].max_file_mb must be from 1 to 2048")
        if project_overview_prompt is not None and (
            not isinstance(project_overview_prompt, str)
            or not project_overview_prompt.strip()
            or len(project_overview_prompt) > 8000
            or "{project}" not in project_overview_prompt
        ):
            raise ValueError(
                f"vaults[{index}].project_overview_prompt must be non-empty, at most 8000 chars, "
                "and include {project}"
            )
        if project_overview_prompt is not None and metadata_profile != "affaires":
            raise ValueError(
                f"vaults[{index}].project_overview_prompt is only supported for the affaires profile"
            )
        names.add(name)
        roots.add(root)
        banks.add(bank_id)
        vaults.append(VaultProfile(
            name=name,
            root=root,
            mount_root=mount_root,
            bank_id=bank_id,
            source_kind=source_kind.strip(),
            metadata_profile=str(metadata_profile),
            max_depth=vault_max_depth,
            parser=parser.strip(),
            max_file_mb=max_file_mb,
            project_overview_prompt=project_overview_prompt.strip() if project_overview_prompt else None,
        ))
    reconcile_seconds = payload.get("reconcile_seconds", 60.0)
    watch_debounce_ms = payload.get("watch_debounce_ms", 500)
    settle_observations = payload.get("settle_observations", 2)
    missing_source_grace_seconds = payload.get("missing_source_grace_seconds", 86400.0)
    excluded = payload.get("excluded_folders", [])
    if not isinstance(reconcile_seconds, (int, float)) or isinstance(reconcile_seconds, bool) or reconcile_seconds < 0.1:
        raise ValueError("reconcile_seconds must be at least 0.1")
    if not isinstance(watch_debounce_ms, int) or isinstance(watch_debounce_ms, bool) or watch_debounce_ms < 0:
        raise ValueError("watch_debounce_ms must be a non-negative integer")
    if not isinstance(settle_observations, int) or isinstance(settle_observations, bool) or not 1 <= settle_observations <= 10:
        raise ValueError("settle_observations must be from 1 to 10")
    if (
        not isinstance(missing_source_grace_seconds, (int, float))
        or isinstance(missing_source_grace_seconds, bool)
        or not 0 <= missing_source_grace_seconds <= 90 * 86400
    ):
        raise ValueError("missing_source_grace_seconds must be from 0 to 7776000")
    if not isinstance(excluded, list) or any(not isinstance(value, str) or not value.strip() for value in excluded):
        raise ValueError("excluded_folders must be a list of non-empty names")
    return VaultConfiguration(
        vaults=tuple(vaults),
        max_depth=max_depth,
        reconcile_seconds=float(reconcile_seconds),
        watch_debounce_ms=watch_debounce_ms,
        settle_observations=settle_observations,
        excluded_folders=tuple(dict.fromkeys(value.strip() for value in excluded)),
        missing_source_grace_seconds=float(missing_source_grace_seconds),
    )
