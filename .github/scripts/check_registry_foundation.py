#!/usr/bin/env python3
"""Validate Pantheon registry projections without granting semantic authority."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[2]
REGISTRIES = ROOT / "registries"
INDEX = REGISTRIES / "registry_index.json"
SCHEMA_PATH = ROOT / "schemas" / "registry.schema.yaml"


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read valid JSON from {path.relative_to(ROOT)}: {exc}") from exc


def main() -> int:
    failures: list[str] = []

    if not SCHEMA_PATH.is_file():
        failures.append("missing schemas/registry.schema.yaml")
    if not INDEX.is_file():
        failures.append("missing registries/registry_index.json")
    if failures:
        return report(failures)

    schema = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)

    index = load_json(INDEX)
    failures.extend(validation_errors(validator, index, INDEX))

    if index.get("registry_kind") != "registry_index":
        failures.append("registry_index.json must declare registry_kind=registry_index")

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    indexed_paths: set[str] = set()

    for position, descriptor in enumerate(index.get("entries", [])):
        prefix = f"registry_index.json entries[{position}]"
        registry_id = descriptor.get("id")
        path_value = descriptor.get("path")
        schema_value = descriptor.get("schema", "schemas/registry.schema.yaml")

        if not isinstance(path_value, str) or not path_value:
            failures.append(f"{prefix}: missing non-empty path")
            continue
        if registry_id in seen_ids:
            failures.append(f"{prefix}: duplicate registry id {registry_id!r}")
        if path_value in seen_paths:
            failures.append(f"{prefix}: duplicate registry path {path_value!r}")
        seen_ids.add(registry_id)
        seen_paths.add(path_value)
        indexed_paths.add(path_value)

        registry_path = ROOT / path_value
        registry_schema_path = ROOT / schema_value
        if not registry_path.is_file():
            failures.append(f"{prefix}: missing registry file {path_value}")
            continue
        if not registry_schema_path.is_file():
            failures.append(f"{prefix}: missing schema file {schema_value}")
            continue

        registry = load_json(registry_path)
        registry_schema = yaml.safe_load(registry_schema_path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(registry_schema)
        registry_validator = jsonschema.Draft202012Validator(registry_schema)
        failures.extend(validation_errors(registry_validator, registry, registry_path))

        if registry.get("registry_id") != registry_id:
            failures.append(
                f"{prefix}: descriptor id {registry_id!r} does not match "
                f"registry_id {registry.get('registry_id')!r}"
            )
        authority = registry.get("authority_document")
        if not isinstance(authority, str) or not (ROOT / authority).is_file():
            failures.append(f"{path_value}: authority_document does not resolve: {authority!r}")
        entry_ids = [entry.get("id") for entry in registry.get("entries", [])]
        duplicates = sorted({item for item in entry_ids if entry_ids.count(item) > 1})
        if duplicates:
            failures.append(f"{path_value}: duplicate entry ids: {', '.join(duplicates)}")

    discovered = {
        path.relative_to(ROOT).as_posix()
        for path in REGISTRIES.rglob("*.registry.json")
    }
    unindexed = sorted(discovered - indexed_paths)
    if unindexed:
        failures.append("unindexed registry files: " + ", ".join(unindexed))

    if failures:
        return report(failures)

    print(
        "OK: registry foundation valid; "
        f"{len(index.get('entries', []))} business registry projection(s) indexed."
    )
    return 0


def validation_errors(
    validator: jsonschema.Draft202012Validator,
    value: dict,
    path: Path,
) -> list[str]:
    errors: list[str] = []
    for error in sorted(validator.iter_errors(value), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path) or "<root>"
        errors.append(f"{path.relative_to(ROOT)} {location}: {error.message}")
    return errors


def report(failures: list[str]) -> int:
    print("Registry foundation check failed:", file=sys.stderr)
    for failure in failures:
        print(f"- {failure}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
