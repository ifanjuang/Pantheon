"""Read-only validation for the sole Project Anatomy contract.

The active baseline accepts only the reviewed Project Anatomy V0.2 primitives
and supporting contracts. It contains no legacy projection, compatibility
carrier or authority transfer.

Nothing here executes, persists, canonizes, admits Evidence or approves a claim.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import jsonschema
import yaml
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from .repo import find_repo_root, read_repo_text

SCHEMA_DIR = "schemas/architecture-project-understanding"

TYPE_SCHEMA = {
    "program": "program.schema.yaml",
    "requirement": "requirement.schema.yaml",
    "classification_scheme": "classification_scheme.schema.yaml",
    "stable_object": "stable_object.schema.yaml",
    "source_representation": "source_representation.schema.yaml",
    "attribute_claim": "attribute_claim.schema.yaml",
    "relation_claim": "relation_claim.schema.yaml",
    "calibration": "calibration.schema.yaml",
    "derivation": "derivation.schema.yaml",
    "contradiction": "contradiction.schema.yaml",
}

_ID_FIELD = {
    "program": "program_id",
    "requirement": "requirement_id",
    "classification_scheme": "scheme_id",
    "stable_object": "stable_object_id",
    "source_representation": "representation_id",
    "attribute_claim": "attribute_claim_id",
    "relation_claim": "relation_claim_id",
    "calibration": "calibration_id",
    "derivation": "derivation_id",
    "contradiction": "contradiction_id",
}

_EXTERNAL_PREFIXES = (
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


def _load_schema(name: str, root: Path) -> dict[str, Any]:
    return yaml.safe_load(read_repo_text(f"{SCHEMA_DIR}/{name}", root))


def _registry(root: Path) -> Registry:
    shared = _load_schema("shared.schema.yaml", root)
    resource = Resource.from_contents(shared, default_specification=DRAFT202012)
    return Registry().with_resource(uri="shared.schema.yaml", resource=resource)


def _iter_objects(dossier: dict[str, Any]):
    for object_type, payload in dossier.items():
        if object_type not in TYPE_SCHEMA:
            yield object_type, None, payload, f"unknown object type: {object_type}"
            continue
        items = payload if isinstance(payload, list) else [payload]
        for index, item in enumerate(items):
            yield object_type, index, item, None


def _error_report(problem: str) -> dict[str, Any]:
    return {
        "result": "error",
        "validated": 0,
        "schema_errors": [problem],
        "reference_errors": [],
        "gate": {
            "posture": "candidate-only",
            "canonical_effect": False,
            "canonical_emission_allowed": False,
            "regulatory_claims_without_approval": [],
            "human_decisions_required": [],
        },
    }


def validate_apu_dossier(dossier: dict[str, Any]) -> dict[str, Any]:
    """Validate one candidate dossier against the sole active baseline."""
    if not isinstance(dossier, dict):
        return _error_report("dossier must be a mapping of object_type -> object(s)")

    root = find_repo_root()
    registry = _registry(root)
    format_checker = jsonschema.FormatChecker()
    validator_cls = jsonschema.Draft202012Validator

    schema_errors: list[str] = []
    reference_errors: list[str] = []
    human_decisions_required: list[str] = []
    id_index: dict[str, str] = {}
    objects: list[tuple[str, int, dict[str, Any]]] = []
    schema_cache: dict[str, dict[str, Any]] = {}
    validated = 0

    for object_type, index, item, error in _iter_objects(dossier):
        if error:
            schema_errors.append(error)
            continue
        if not isinstance(item, dict):
            schema_errors.append(f"{object_type}[{index}]: not a mapping")
            continue

        objects.append((object_type, index, item))
        schema = schema_cache.get(object_type)
        if schema is None:
            schema = _load_schema(TYPE_SCHEMA[object_type], root)
            schema_cache[object_type] = schema
        for validation_error in sorted(
            validator_cls(
                schema,
                format_checker=format_checker,
                registry=registry,
            ).iter_errors(item),
            key=lambda value: list(value.path),
        ):
            path = ".".join(str(part) for part in validation_error.path) or "<root>"
            schema_errors.append(
                f"{object_type}[{index}].{path}: {validation_error.message}"
            )
        validated += 1

        id_field = _ID_FIELD.get(object_type)
        if id_field and id_field in item:
            value = str(item[id_field])
            previous = id_index.get(value)
            if previous is not None:
                schema_errors.append(
                    f"duplicate APU id '{value}': {previous} and {object_type}[{index}]"
                )
            else:
                id_index[value] = f"{object_type}[{index}]"

    def resolves(value: Any) -> bool:
        if value is None:
            return True
        text = str(value)
        return text in id_index or any(
            text.startswith(prefix) for prefix in _EXTERNAL_PREFIXES
        )

    def ref(value: Any, label: str) -> None:
        if value in (None, ""):
            return
        if not resolves(value):
            reference_errors.append(f"{label} '{value}' unresolved")

    def refs(values: Any, label: str) -> None:
        for value in values or []:
            ref(value, label)

    def entity_ref(value: Any, label: str) -> None:
        if isinstance(value, dict):
            ref(value.get("entity_id"), f"{label}.entity_id")

    for object_type, index, item in objects:
        tag = f"{object_type}[{index}]"
        if object_type == "attribute_claim":
            entity_ref(item.get("subject_ref"), f"{tag}.subject_ref")
            refs(
                item.get("source_representation_refs"),
                f"{tag}.source_representation_refs",
            )
            refs(item.get("derivation_refs"), f"{tag}.derivation_refs")
            ref(item.get("supersedes_claim_ref"), f"{tag}.supersedes_claim_ref")
        elif object_type == "relation_claim":
            entity_ref(item.get("subject_ref"), f"{tag}.subject_ref")
            entity_ref(item.get("object_ref"), f"{tag}.object_ref")
            refs(
                item.get("source_representation_refs"),
                f"{tag}.source_representation_refs",
            )
            refs(item.get("derivation_refs"), f"{tag}.derivation_refs")
            ref(item.get("supersedes_claim_ref"), f"{tag}.supersedes_claim_ref")
            if item.get("relation_type") == "identity.represents" and item.get(
                "proof_status"
            ) in {"candidate", "requires_more_evidence", "contradictory_evidence"}:
                human_decisions_required.append(
                    f"{tag}: identity relation remains candidate/review material"
                )
        elif object_type == "requirement":
            source = item.get("source") or {}
            if source.get("source_type") == "program":
                ref(source.get("source_ref"), f"{tag}.source.source_ref")
            target = item.get("target") or {}
            entity_ref(target.get("entity_ref"), f"{tag}.target.entity_ref")
            related = (item.get("constraint") or {}).get("related_target") or {}
            entity_ref(
                related.get("entity_ref"),
                f"{tag}.constraint.related_target.entity_ref",
            )
        elif object_type == "source_representation":
            ref(item.get("calibration_ref"), f"{tag}.calibration_ref")
        elif object_type == "derivation":
            for produced in item.get("produces") or []:
                if isinstance(produced, dict):
                    ref(produced.get("claim_id"), f"{tag}.produces.claim_id")
            refs(item.get("inputs"), f"{tag}.inputs")
        elif object_type == "contradiction":
            entity_ref(item.get("subject_ref"), f"{tag}.subject_ref")
            refs(item.get("claim_refs"), f"{tag}.claim_refs")
            ref(item.get("resolved_claim_ref"), f"{tag}.resolved_claim_ref")

    result = "ok" if not (schema_errors or reference_errors) else "error"
    return {
        "result": result,
        "validated": validated,
        "schema_errors": schema_errors,
        "reference_errors": reference_errors,
        "gate": {
            "posture": "candidate-only",
            "canonical_effect": False,
            "canonical_emission_allowed": result == "ok",
            "regulatory_claims_without_approval": [],
            "human_decisions_required": human_decisions_required,
        },
    }
