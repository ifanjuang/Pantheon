"""Read-only validation for the sole Project Anatomy contract.

The active baseline accepts only the reviewed Project Anatomy V0.2 primitives
and supporting contracts. It contains no legacy projection, compatibility
carrier or authority transfer.

Nothing here executes, persists, canonizes, admits Evidence or approves a claim.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from .repo import find_repo_root, read_repo_text

SCHEMA_DIR = "schemas/architecture-project-understanding"

# The governed relation profile (architecture@1). Declaring a relation type
# makes the identifier governable; it never makes a relation claim true,
# admitted, Evidence or approved.
RELATION_PROFILE_PATH = "registries/architecture_relation_profile.registry.json"

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


def load_relation_profile(root: Path | None = None) -> dict[str, Any]:
    """Read the governed relation profile. Read-only; raises on a broken file."""
    value = json.loads(read_repo_text(RELATION_PROFILE_PATH, root))
    if not isinstance(value, dict) or not isinstance(value.get("entries"), list):
        raise ValueError(f"{RELATION_PROFILE_PATH} is not a relation profile")
    return value


def relation_profile_findings(
    profile: dict[str, Any],
    *,
    relation_type: Any,
    subject_ref: Any = None,
    object_ref: Any = None,
    qualifier: Any = None,
    object_families: dict[str, str] | None = None,
    label: str = "relation_claim",
) -> tuple[list[str], list[str]]:
    """Check one relation use against the profile.

    Returns (errors, review_notes). Errors: undeclared or deprecated type,
    inadmissible endpoint entity type or object family, controlled qualifier
    key not admitted for the relation, controlled qualifier value outside its
    vocabulary. Review notes: use of a relation type still `candidate` in the
    profile. Qualifier keys that the profile does not control stay free.
    Families are checked only for stable objects present in the same dossier.
    """
    profile_id = (profile.get("profile") or {}).get("id", "relation profile")
    entries = {entry.get("id"): entry for entry in profile.get("entries", [])}
    errors: list[str] = []
    notes: list[str] = []

    entry = entries.get(relation_type)
    if entry is None:
        errors.append(
            f"{label}.relation_type '{relation_type}' is not declared in {profile_id}"
        )
        return errors, notes
    status = entry.get("status")
    if status == "deprecated":
        replacement = entry.get("replaced_by")
        hint = f"; use '{replacement}'" if replacement else ""
        errors.append(
            f"{label}.relation_type '{relation_type}' is deprecated in {profile_id}{hint}"
        )
    elif status == "candidate":
        notes.append(
            f"{label}: relation type '{relation_type}' is still candidate in {profile_id}"
        )

    families = object_families or {}
    for side, ref, allowed_types, allowed_families in (
        (
            "subject_ref",
            subject_ref,
            entry.get("subject_entity_types") or [],
            entry.get("subject_object_families") or [],
        ),
        (
            "object_ref",
            object_ref,
            entry.get("object_entity_types") or [],
            entry.get("object_object_families") or [],
        ),
    ):
        if not isinstance(ref, dict):
            continue
        entity_type = ref.get("entity_type")
        if entity_type and allowed_types and entity_type not in allowed_types:
            errors.append(
                f"{label}.{side}.entity_type '{entity_type}' is not admitted for "
                f"'{relation_type}' (expected {', '.join(allowed_types)})"
            )
            continue
        family = families.get(str(ref.get("entity_id")))
        if (
            entity_type == "stable_object"
            and family
            and allowed_families
            and family not in allowed_families
        ):
            errors.append(
                f"{label}.{side} object_family '{family}' is not admitted for "
                f"'{relation_type}' (expected {', '.join(allowed_families)})"
            )

    if isinstance(qualifier, dict):
        vocabularies = {
            vocab.get("key"): vocab for vocab in profile.get("qualifier_vocabularies", [])
        }
        entry_qualifiers = set(entry.get("allowed_qualifiers") or [])
        for key, value in qualifier.items():
            vocab = vocabularies.get(key)
            if vocab is None:
                continue
            admitted = key in entry_qualifiers or entry.get("family") in (
                vocab.get("allowed_families") or []
            )
            if not admitted:
                errors.append(
                    f"{label}.qualifier.{key} is not admitted for '{relation_type}'"
                )
                continue
            if value not in (vocab.get("values") or []):
                errors.append(
                    f"{label}.qualifier.{key} '{value}' is outside the {profile_id} "
                    f"vocabulary ({', '.join(vocab.get('values') or [])})"
                )
    return errors, notes


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
        "vocabulary_errors": [],
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

    vocabulary_errors: list[str] = []
    try:
        relation_profile: dict[str, Any] | None = load_relation_profile(root)
    except (OSError, ValueError) as exc:
        relation_profile = None
        vocabulary_errors.append(f"relation profile unavailable: {exc}")
    object_families = {
        str(item.get("stable_object_id")): str(item.get("object_family"))
        for object_type, _index, item in objects
        if object_type == "stable_object" and item.get("object_family")
    }

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
            if relation_profile is not None:
                found, review_notes = relation_profile_findings(
                    relation_profile,
                    relation_type=item.get("relation_type"),
                    subject_ref=item.get("subject_ref"),
                    object_ref=item.get("object_ref"),
                    qualifier=item.get("qualifier"),
                    object_families=object_families,
                    label=tag,
                )
                vocabulary_errors.extend(found)
                human_decisions_required.extend(review_notes)
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
            constraint = item.get("constraint") or {}
            related = constraint.get("related_target") or {}
            entity_ref(
                related.get("entity_ref"),
                f"{tag}.constraint.related_target.entity_ref",
            )
            if relation_profile is not None and constraint.get("relation_type"):
                found, review_notes = relation_profile_findings(
                    relation_profile,
                    relation_type=constraint.get("relation_type"),
                    label=f"{tag}.constraint",
                )
                vocabulary_errors.extend(found)
                human_decisions_required.extend(review_notes)
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

    result = (
        "ok" if not (schema_errors or reference_errors or vocabulary_errors) else "error"
    )
    return {
        "result": result,
        "validated": validated,
        "schema_errors": schema_errors,
        "reference_errors": reference_errors,
        "vocabulary_errors": vocabulary_errors,
        "gate": {
            "posture": "candidate-only",
            "canonical_effect": False,
            "canonical_emission_allowed": result == "ok",
            "regulatory_claims_without_approval": [],
            "human_decisions_required": human_decisions_required,
        },
    }
