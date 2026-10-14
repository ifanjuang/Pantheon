#!/usr/bin/env python3
"""Read-only referential-integrity check for the Project Anatomy dossier.

The fixture and checker exercise only the sole active Project Anatomy baseline.
They never execute adapters, route providers, admit Evidence or promote memory.
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import jsonschema
import yaml
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[2]
DOSSIER = ROOT / "docs/examples/architecture_project_understanding_dossier"
SCHEMA_DIR = ROOT / "schemas/architecture-project-understanding"

FILE_SCHEMA = {
    "program.yaml": "program.schema.yaml",
    "requirement_area.yaml": "requirement.schema.yaml",
    "requirement_count.yaml": "requirement.schema.yaml",
    "calibration.yaml": "calibration.schema.yaml",
    "derivation_area.yaml": "derivation.schema.yaml",
    "attribute_claim_area.yaml": "attribute_claim.schema.yaml",
    "stable_object_chambre.yaml": "stable_object.schema.yaml",
    "stable_object_sdb.yaml": "stable_object.schema.yaml",
    "stable_object_door.yaml": "stable_object.schema.yaml",
    "source_representation_door.yaml": "source_representation.schema.yaml",
    "relation_claim_door_identity.yaml": "relation_claim.schema.yaml",
    "relation_claim_opens.yaml": "relation_claim.schema.yaml",
}

ID_FIELDS = {
    "program.schema.yaml": "program_id",
    "requirement.schema.yaml": "requirement_id",
    "calibration.schema.yaml": "calibration_id",
    "derivation.schema.yaml": "derivation_id",
    "attribute_claim.schema.yaml": "attribute_claim_id",
    "stable_object.schema.yaml": "stable_object_id",
    "source_representation.schema.yaml": "representation_id",
    "relation_claim.schema.yaml": "relation_claim_id",
}

EXTERNAL_PREFIXES = (
    "SRC-",
    "DET-",
    "EQ-",
    "SYS-",
    "OP-CAND-",
    "REV-",
    "MAIL-",
    "DOC-",
    "IDS-",
)


def load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return value


def is_external(value: str) -> bool:
    return any(value.startswith(prefix) for prefix in EXTERNAL_PREFIXES)


def build_id_index(
    docs: dict[str, dict[str, Any]],
) -> tuple[dict[str, str], list[str]]:
    """Build one declaration namespace and fail closed on duplicate ids."""
    id_index: dict[str, str] = {}
    errors: list[str] = []
    for filename, instance in docs.items():
        schema_name = FILE_SCHEMA.get(filename)
        if schema_name is None:
            continue
        id_field = ID_FIELDS.get(schema_name)
        if not id_field or id_field not in instance:
            continue
        value = str(instance[id_field])
        previous = id_index.get(value)
        if previous is not None:
            errors.append(
                f"duplicate id '{value}': first declared by {previous}, repeated by {filename}"
            )
        else:
            id_index[value] = filename
    return id_index, errors


def main() -> int:
    errors: list[str] = []
    docs: dict[str, dict[str, Any]] = {}

    if not DOSSIER.exists():
        print(f"FAIL: dossier missing: {DOSSIER.relative_to(ROOT)}", file=sys.stderr)
        return 1

    validator_cls = jsonschema.Draft202012Validator
    format_checker = jsonschema.FormatChecker()
    shared = Resource.from_contents(
        load(SCHEMA_DIR / "shared.schema.yaml"),
        default_specification=DRAFT202012,
    )
    registry = Registry().with_resource(uri="shared.schema.yaml", resource=shared)

    actual_files = {
        path.name
        for path in DOSSIER.glob("*.yaml")
        if path.name != "README.md"
    }
    undeclared = sorted(actual_files - set(FILE_SCHEMA))
    missing = sorted(set(FILE_SCHEMA) - actual_files)
    errors.extend(f"undeclared dossier file: {name}" for name in undeclared)
    errors.extend(f"missing dossier file: {name}" for name in missing)

    for filename, schema_name in FILE_SCHEMA.items():
        file_path = DOSSIER / filename
        schema_path = SCHEMA_DIR / schema_name
        if not file_path.is_file() or not schema_path.is_file():
            continue
        instance = load(file_path)
        docs[filename] = instance
        schema = load(schema_path)
        validator_cls.check_schema(schema)
        for error in sorted(
            validator_cls(
                schema,
                format_checker=format_checker,
                registry=registry,
            ).iter_errors(instance),
            key=lambda item: list(item.path),
        ):
            path = ".".join(str(part) for part in error.path) or "<root>"
            errors.append(f"{filename}: schema: {path}: {error.message}")

    id_index, duplicate_errors = build_id_index(docs)
    errors.extend(duplicate_errors)

    def must_resolve(value: Any, where: str) -> None:
        if value in (None, ""):
            return
        text = str(value)
        if text in id_index or is_external(text):
            return
        errors.append(f"{where}: unresolved reference '{text}'")

    def entity_ref(value: Any, where: str) -> None:
        if isinstance(value, dict):
            must_resolve(value.get("entity_id"), f"{where}.entity_id")

    for filename, instance in docs.items():
        schema_name = FILE_SCHEMA[filename]
        if schema_name == "requirement.schema.yaml":
            source = instance.get("source") or {}
            if source.get("source_type") == "program":
                must_resolve(source.get("source_ref"), f"{filename}.source.source_ref")
            target = instance.get("target") or {}
            entity_ref(target.get("entity_ref"), f"{filename}.target.entity_ref")
            related = (instance.get("constraint") or {}).get("related_target") or {}
            entity_ref(
                related.get("entity_ref"),
                f"{filename}.constraint.related_target.entity_ref",
            )
        elif schema_name == "derivation.schema.yaml":
            for produced in instance.get("produces") or []:
                if isinstance(produced, dict):
                    must_resolve(
                        produced.get("claim_id"),
                        f"{filename}.produces.claim_id",
                    )
            for value in instance.get("inputs") or []:
                must_resolve(value, f"{filename}.inputs")
        elif schema_name == "attribute_claim.schema.yaml":
            entity_ref(instance.get("subject_ref"), f"{filename}.subject_ref")
            for value in instance.get("source_representation_refs") or []:
                must_resolve(value, f"{filename}.source_representation_refs")
            for value in instance.get("derivation_refs") or []:
                must_resolve(value, f"{filename}.derivation_refs")
        elif schema_name == "source_representation.schema.yaml":
            must_resolve(instance.get("calibration_ref"), f"{filename}.calibration_ref")
        elif schema_name == "relation_claim.schema.yaml":
            entity_ref(instance.get("subject_ref"), f"{filename}.subject_ref")
            entity_ref(instance.get("object_ref"), f"{filename}.object_ref")
            for value in instance.get("source_representation_refs") or []:
                must_resolve(value, f"{filename}.source_representation_refs")
            for value in instance.get("derivation_refs") or []:
                must_resolve(value, f"{filename}.derivation_refs")

    if errors:
        print(
            "Architecture Project Understanding referential-integrity check failed:",
            file=sys.stderr,
        )
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"OK: {len(docs)} Project Anatomy dossier instance(s) valid; "
        "ids are unique and references resolve against the sole active baseline."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
