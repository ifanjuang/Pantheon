"""Validate a Hermes distribution composition without installing or activating it."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import jsonschema
import yaml


REQUIRED_COMPONENT_KINDS = {"run_binding", "context_bridge", "runtime_observer"}
REQUIRED_CHECK_KINDS = {
    "static_structure",
    "artifact_integrity",
    "route_contract",
    "end_to_end",
    "no_authority",
}
IGNORED_TREE_DIRECTORIES = {".git", "__pycache__"}
IGNORED_TREE_FILENAMES = {".DS_Store"}
IGNORED_TREE_SUFFIXES = {".pyc", ".pyo"}


class DistributionLockError(ValueError):
    pass


def load_mapping(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise DistributionLockError(f"cannot read {label}: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise DistributionLockError(f"{label} must be an object")
    return value


def file_content_digest(path: Path) -> str:
    if path.is_symlink():
        raise DistributionLockError(f"symbolic links are forbidden in component digests: {path}")
    if not path.is_file():
        raise DistributionLockError(f"file digest target is not a regular file: {path}")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _ignored_tree_path(relative: Path) -> bool:
    return (
        any(part in IGNORED_TREE_DIRECTORIES for part in relative.parts)
        or relative.name in IGNORED_TREE_FILENAMES
        or relative.suffix in IGNORED_TREE_SUFFIXES
    )


def tree_content_digest(path: Path) -> str:
    if path.is_symlink():
        raise DistributionLockError(f"symbolic links are forbidden in component digests: {path}")
    if not path.is_dir():
        raise DistributionLockError(f"tree digest target is not a directory: {path}")

    files: list[Path] = []
    for candidate in path.rglob("*"):
        if candidate.is_symlink():
            raise DistributionLockError(
                f"symbolic links are forbidden in component digests: {candidate}"
            )
        relative = candidate.relative_to(path)
        if _ignored_tree_path(relative):
            continue
        if candidate.is_file():
            files.append(candidate)

    digest = hashlib.sha256()
    for candidate in sorted(files, key=lambda item: item.relative_to(path).as_posix()):
        relative = candidate.relative_to(path).as_posix()
        file_hex = hashlib.sha256(candidate.read_bytes()).hexdigest()
        digest.update(f"{relative}\0{file_hex}\n".encode("utf-8"))
    return "sha256:" + digest.hexdigest()


def component_content_digest(path: Path, mode: str) -> str:
    if mode == "file":
        return file_content_digest(path)
    if mode == "tree":
        return tree_content_digest(path)
    raise DistributionLockError(f"unknown digest mode: {mode}")


def _component_target(component: dict[str, Any], monorepo_root: Path) -> Path:
    component_id = str(component.get("component_id") or "")
    relative = str(component.get("path") or "")
    root = monorepo_root.resolve()
    target = (root / relative).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise DistributionLockError(
            f"component {component_id} escapes Pantheon monorepo root"
        ) from exc
    return target


def evaluate(
    manifest: dict[str, Any],
    *,
    monorepo_root: Path,
) -> list[str]:
    errors: list[str] = []
    if manifest.get("revision") != 3:
        errors.append("active distribution validator supports revision 3 only")

    root = monorepo_root.resolve()
    if not root.is_dir():
        errors.append(f"Pantheon monorepo root does not exist: {root}")
        return errors

    components = manifest.get("components") or []
    component_ids: set[str] = set()
    observed_kinds: set[str] = set()

    for index, component in enumerate(components):
        if not isinstance(component, dict):
            errors.append(f"components[{index}] must be an object")
            continue
        component_id = str(component.get("component_id") or "")
        if component_id in component_ids:
            errors.append(f"duplicate component_id: {component_id}")
        component_ids.add(component_id)
        observed_kinds.add(str(component.get("kind") or ""))

        try:
            target = _component_target(component, root)
        except DistributionLockError as exc:
            errors.append(str(exc))
            continue
        relative = str(component.get("path") or "")
        if not target.exists():
            errors.append(f"component path does not exist: {relative}")
            continue
        if component.get("enabled_by_default") is not False:
            errors.append(f"component must remain default-off: {component_id}")

        mode = str(component.get("digest_mode") or "")
        expected = str(component.get("content_digest") or "")
        try:
            actual = component_content_digest(target, mode)
        except DistributionLockError as exc:
            errors.append(f"component {component_id} digest failed: {exc}")
        else:
            if actual != expected:
                errors.append(
                    f"component {component_id} digest mismatch: expected {expected}, actual {actual}"
                )

    missing_kinds = sorted(REQUIRED_COMPONENT_KINDS - observed_kinds)
    if missing_kinds:
        errors.append("missing required component kinds: " + ", ".join(missing_kinds))

    checks = manifest.get("required_checks") or []
    check_kinds = {
        str(item.get("kind") or "")
        for item in checks
        if isinstance(item, dict) and item.get("required") is True
    }
    missing_checks = sorted(REQUIRED_CHECK_KINDS - check_kinds)
    if missing_checks:
        errors.append("missing required check kinds: " + ", ".join(missing_checks))

    state = manifest.get("state") or {}
    if state.get("activation_state") != "not_activated":
        errors.append("distribution lock must not activate a binding")
    if state.get("task_authorization_state") != "not_authorized":
        errors.append("distribution lock must not authorize a task")

    authority = manifest.get("authority") or {}
    enabled_authority = sorted(key for key, value in authority.items() if value is not False)
    if enabled_authority:
        errors.append("distribution lock claims authority: " + ", ".join(enabled_authority))

    return errors


def route_contract(manifest: dict[str, Any], monorepo_root: Path) -> list[str]:
    errors: list[str] = []
    root = monorepo_root.resolve()
    by_kind: dict[str, Path] = {}
    for item in manifest.get("components") or []:
        if not isinstance(item, dict) or item.get("kind") not in {"run_binding", "context_bridge"}:
            continue
        try:
            by_kind[str(item["kind"])] = _component_target(item, root)
        except DistributionLockError:
            continue

    run_binding = by_kind.get("run_binding")
    if run_binding and run_binding.is_file():
        source = run_binding.read_text(encoding="utf-8")
        required = {
            "/hermes/execution-admissions/{admission_id}/launch-reservations",
            "/hermes/execution-admissions/{admission_id}/runs/start",
            "/hermes/execution-admissions/{admission_id}/runs/{run_id}/return",
            '"/v1/runs"',
        }
        for marker in required:
            if marker not in source:
                errors.append(f"run binding is missing route marker: {marker}")
        if "/v1/hermes/" in source:
            errors.append("run binding reintroduces retired internal /v1/hermes routes")
    else:
        errors.append("run binding source is missing")

    bridge = by_kind.get("context_bridge")
    bridge_tools = bridge / "tools.py" if bridge and bridge.is_dir() else None
    if bridge_tools and bridge_tools.is_file():
        source = bridge_tools.read_text(encoding="utf-8")
        if "/active-context" not in source or "/active-context/entities/" not in source:
            errors.append("context bridge is missing bounded active-context routes")
        if "/v1/hermes/" in source:
            errors.append("context bridge reintroduces retired internal /v1/hermes routes")
    else:
        errors.append("context bridge tools.py is missing")

    return errors


def _verified_component_receipt(component: dict[str, Any]) -> dict[str, Any]:
    """Project only the already-verified immutable composition fields."""

    return {
        "component_id": component["component_id"],
        "kind": component["kind"],
        "path": component["path"],
        "digest_mode": component["digest_mode"],
        "content_digest": component["content_digest"],
        "required": component["required"],
        "enabled_by_default": component["enabled_by_default"],
    }


def validate(
    *,
    manifest_path: Path,
    schema_path: Path,
    monorepo_root: Path,
) -> dict[str, Any]:
    manifest = load_mapping(manifest_path, label="distribution lock")
    schema = load_mapping(schema_path, label="distribution lock schema")
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(manifest)
    except jsonschema.SchemaError as exc:
        raise DistributionLockError(f"invalid distribution schema: {exc.message}") from exc
    except jsonschema.ValidationError as exc:
        path = ".".join(str(part) for part in exc.path) or "<root>"
        raise DistributionLockError(
            f"distribution lock validation failed at {path}: {exc.message}"
        ) from exc

    errors = evaluate(manifest, monorepo_root=monorepo_root)
    errors.extend(route_contract(manifest, monorepo_root))
    if errors:
        raise DistributionLockError("; ".join(errors))

    runtime = manifest["source_pins"]["hermes_runtime"]
    return {
        "schema_id": manifest["schema_id"],
        "revision": manifest["revision"],
        "distribution_id": manifest["distribution_id"],
        "status": manifest["status"],
        "components": [
            _verified_component_receipt(component)
            for component in manifest["components"]
        ],
        "component_count": len(manifest["components"]),
        "verified_component_digest_count": len(manifest["components"]),
        "required_check_count": len(manifest["required_checks"]),
        "hermes_version_target": runtime["version"],
        "hermes_artifact_observed": runtime["artifact_digest"] is not None,
        "installation_state": manifest["state"]["installation_state"],
        "activation_state": manifest["state"]["activation_state"],
        "task_authorization_state": manifest["state"]["task_authorization_state"],
        "authority_effect": "none",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--monorepo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        result = validate(
            manifest_path=args.manifest,
            schema_path=args.schema,
            monorepo_root=args.monorepo_root.resolve(),
        )
    except DistributionLockError as exc:
        print(f"Hermes distribution lock failed: {exc}")
        return 1

    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0
