#!/usr/bin/env python3
"""Read-only check of the Project Anatomy relation profile (architecture@1).

It verifies that the governed relation vocabulary is internally coherent, that
every relation type named by PROJECT_ANATOMY_MODEL.md section 6 is declared and
active, and that the governed fixtures use only declared, non-deprecated
relation types. Relation-use checks reuse the bounded read-only validator in
mcp-server/pantheon_mcp/apu.py instead of duplicating it (CLAUDE.md).

Declaring a relation type makes the identifier governable. It never makes a
relation claim true, admitted, Evidence or approved. The script reads files
and reports; it executes, persists and promotes nothing.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any, Iterator

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "mcp-server"))

from pantheon_mcp import apu  # noqa: E402

PROFILE = ROOT / apu.RELATION_PROFILE_PATH
PROFILE_SCHEMA = (
    ROOT / "schemas/architecture-project-understanding/relation_profile.schema.yaml"
)
MODEL = ROOT / "docs/domain-packs/architecture/PROJECT_ANATOMY_MODEL.md"
EXAMPLE_DOSSIER = ROOT / "docs/examples/architecture_project_understanding_dossier"
COCKPIT_DEMO = ROOT / "implementation/mvp_vertical/cockpit/demo-data.json"


ACTIVE_LIST_LABEL = "Active relation types (architecture@1):"


def doctrine_relation_types(model_text: str) -> list[str]:
    """Relation types listed under the active-list label of section 6."""
    section = re.search(
        r"^## 6\. Relation claims\n(.*?)^## 7\.", model_text, re.MULTILINE | re.DOTALL
    )
    if not section:
        raise ValueError("PROJECT_ANATOMY_MODEL.md has no '## 6. Relation claims' section")
    block = re.search(
        re.escape(ACTIVE_LIST_LABEL) + r"\s*```text\n(.*?)```", section.group(1), re.DOTALL
    )
    if not block:
        raise ValueError(
            f"section 6 of PROJECT_ANATOMY_MODEL.md has no text block under {ACTIVE_LIST_LABEL!r}"
        )
    return [line.strip() for line in block.group(1).splitlines() if line.strip()]


def coherence_failures(profile: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    rules = profile.get("naming_rules") or {}
    pattern = re.compile(rules.get("id_pattern") or r"^$")
    forbidden = tuple(rules.get("forbidden_name_prefixes") or [])
    families = {family.get("id") for family in profile.get("families", [])}
    vocabularies = {
        vocab.get("key"): vocab for vocab in profile.get("qualifier_vocabularies", [])
    }
    ids = [entry.get("id") for entry in profile.get("entries", [])]
    for duplicate in sorted({str(item) for item in ids if ids.count(item) > 1}):
        failures.append(f"{duplicate}: declared more than once; the vocabulary is ambiguous")
    keys = [vocab.get("key") for vocab in profile.get("qualifier_vocabularies", [])]
    for duplicate in sorted({str(item) for item in keys if keys.count(item) > 1}):
        failures.append(f"qualifier {duplicate}: declared more than once")
    entries = {entry.get("id"): entry for entry in profile.get("entries", [])}

    for key, vocab in vocabularies.items():
        for family in vocab.get("allowed_families") or []:
            if family not in families:
                failures.append(f"qualifier {key}: unknown allowed family {family!r}")

    for relation_id, entry in entries.items():
        if not isinstance(relation_id, str) or not pattern.match(relation_id):
            failures.append(f"{relation_id!r}: does not match the profile id pattern")
            continue
        namespace, name = relation_id.split(".", 1)
        if namespace != entry.get("family"):
            failures.append(
                f"{relation_id}: namespace {namespace!r} differs from family "
                f"{entry.get('family')!r}"
            )
        if entry.get("family") not in families:
            failures.append(f"{relation_id}: family {entry.get('family')!r} is not declared")
        if name.startswith(forbidden):
            failures.append(
                f"{relation_id}: name encodes time or negation; use validity, "
                "qualifier.ouvrage_state or a positive named relation"
            )

        inverse = entry.get("inverse")
        if entry.get("symmetric"):
            if inverse is not None:
                failures.append(f"{relation_id}: a symmetric relation declares no inverse")
            if entry.get("subject_entity_types") != entry.get("object_entity_types") or (
                entry.get("subject_object_families") != entry.get("object_object_families")
            ):
                failures.append(f"{relation_id}: a symmetric relation needs identical endpoints")
        if inverse is not None:
            other = entries.get(inverse)
            if other is None:
                failures.append(f"{relation_id}: inverse {inverse!r} is not declared")
            elif other.get("inverse") != relation_id:
                failures.append(f"{relation_id}: inverse {inverse!r} does not point back")
            elif (
                entry.get("subject_entity_types") != other.get("object_entity_types")
                or entry.get("object_entity_types") != other.get("subject_entity_types")
                or entry.get("subject_object_families") != other.get("object_object_families")
                or entry.get("object_object_families") != other.get("subject_object_families")
            ):
                failures.append(f"{relation_id}: inverse {inverse!r} does not swap the endpoints")

        if entry.get("status") == "deprecated":
            replacement = entry.get("replaced_by")
            if replacement not in entries or entries[replacement].get("status") == "deprecated":
                failures.append(
                    f"{relation_id}: deprecated without a declared, non-deprecated replaced_by"
                )
        elif entry.get("replaced_by"):
            failures.append(f"{relation_id}: replaced_by is reserved for deprecated entries")

        for key in entry.get("allowed_qualifiers") or []:
            if key not in vocabularies:
                failures.append(f"{relation_id}: allowed qualifier {key!r} has no vocabulary")
    return failures


def doctrine_failures(profile: dict[str, Any], model_text: str) -> list[str]:
    entries = {entry.get("id"): entry for entry in profile.get("entries", [])}
    failures: list[str] = []
    named = doctrine_relation_types(model_text)
    for relation_id in named:
        entry = entries.get(relation_id)
        if entry is None:
            failures.append(f"PROJECT_ANATOMY_MODEL.md section 6 names undeclared {relation_id!r}")
        elif entry.get("status") != "active":
            failures.append(
                f"{relation_id}: named by section 6 but status is {entry.get('status')!r}"
            )
    for relation_id, entry in entries.items():
        if entry.get("status") == "active" and relation_id not in named:
            failures.append(
                f"{relation_id}: active in the profile but not named by section 6; "
                "activation is a doctrine change"
            )
    return failures


def example_dossier() -> dict[str, list[dict[str, Any]]]:
    """Assemble the reviewed example dossier as object_type -> objects."""
    type_by_id_field = {field: object_type for object_type, field in apu._ID_FIELD.items()}
    dossier: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(EXAMPLE_DOSSIER.glob("*.yaml")):
        item = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(item, dict):
            continue
        object_type = next(
            (type_by_id_field[field] for field in type_by_id_field if field in item), None
        )
        if object_type:
            dossier.setdefault(object_type, []).append(item)
    return dossier


def _relation_claims(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        if value.get("claim_type") == "relation_claim" and "relation_type" in value:
            yield value
        for child in value.values():
            yield from _relation_claims(child)
    elif isinstance(value, list):
        for child in value:
            yield from _relation_claims(child)


def _object_families(value: Any) -> Iterator[tuple[str, str]]:
    """(object_id, object_family) pairs from projected Cockpit objects."""
    if isinstance(value, dict):
        object_id, family = value.get("object_id"), value.get("object_family")
        if isinstance(object_id, str) and isinstance(family, str):
            yield object_id, family
        for child in value.values():
            yield from _object_families(child)
    elif isinstance(value, list):
        for child in value:
            yield from _object_families(child)


def usage_failures(profile: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if EXAMPLE_DOSSIER.is_dir():
        report = apu.validate_apu_dossier(example_dossier())
        failures.extend(
            f"{EXAMPLE_DOSSIER.relative_to(ROOT)}: {item}"
            for item in report.get("vocabulary_errors", [])
        )
    if COCKPIT_DEMO.is_file():
        demo = json.loads(COCKPIT_DEMO.read_text(encoding="utf-8"))
        demo_families = dict(_object_families(demo))
        for claim in _relation_claims(demo):
            found, _notes = apu.relation_profile_findings(
                profile,
                relation_type=claim.get("relation_type"),
                subject_ref=claim.get("subject_ref"),
                object_ref=claim.get("object_ref"),
                qualifier=claim.get("qualifier"),
                object_families=demo_families,
                label=f"{COCKPIT_DEMO.relative_to(ROOT)} {claim.get('claim_id')}",
            )
            failures.extend(found)
    return sorted(set(failures))


def main() -> int:
    failures: list[str] = []
    for required in (PROFILE, PROFILE_SCHEMA, MODEL):
        if not required.is_file():
            failures.append(f"missing {required.relative_to(ROOT)}")
    if failures:
        return report(failures)

    schema = yaml.safe_load(PROFILE_SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    for error in jsonschema.Draft202012Validator(schema).iter_errors(profile):
        location = ".".join(str(part) for part in error.path) or "<root>"
        failures.append(f"{PROFILE.relative_to(ROOT)} {location}: {error.message}")
    if failures:
        return report(failures)

    failures.extend(coherence_failures(profile))
    failures.extend(doctrine_failures(profile, MODEL.read_text(encoding="utf-8")))
    failures.extend(usage_failures(profile))
    if failures:
        return report(failures)

    entries = profile.get("entries", [])
    active = sum(1 for entry in entries if entry.get("status") == "active")
    print(
        f"OK: relation profile {profile['profile']['id']} coherent; "
        f"{len(entries)} relation type(s), {active} active, "
        f"{len(entries) - active} candidate or deprecated; governed fixtures conform."
    )
    return 0


def report(failures: list[str]) -> int:
    print("Relation profile check failed:", file=sys.stderr)
    for failure in failures:
        print(f"- {failure}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
