#!/usr/bin/env python3
"""Validate one Hermes fragment qualification candidate against one structure.

The validator checks transport integrity and governance boundaries only. It does
not verify professional truth, admit Evidence or write APU objects.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPRESENTATION_KINDS = {
    "site_plan", "floor_plan", "roof_plan", "reflected_ceiling_plan",
    "structural_plan", "network_plan", "section", "elevation", "detail",
    "diagram", "perspective", "axonometric", "sketch", "schedule",
    "report_section", "other",
}
PROJECT_STATES = {
    "existing", "to_demolish", "projected", "temporary", "as_built", "unknown",
}
CERTAINTIES = {"E0", "E1", "E2", "E3", "E4"}
STATUSES = {"generated_unreviewed", "needs_review"}
SEMANTIC_FIELDS = {
    "topic", "discipline", "representation_kind", "project_state",
    "variant_ref", "coverage_refs",
}
AUTHORITY = {
    "mutates_document_structure": False,
    "is_project_fact": False,
    "is_evidence": False,
    "is_apu_write": False,
    "is_professional_validation": False,
}


class ValidationError(ValueError):
    """Candidate or structure violates the bounded qualification contract."""


def _load(path: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot read JSON object {path!r}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{path!r} must contain a JSON object")
    return value


def _non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} must be a non-empty string")
    return value


def _string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise ValidationError(f"{field} must be an array of non-empty strings")
    if len(value) != len(set(value)):
        raise ValidationError(f"{field} must not contain duplicates")
    return value


def validate(structure: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    structure_id = _non_empty_string(structure.get("structure_id"), "structure.structure_id")
    document_ref = _non_empty_string(structure.get("document_ref"), "structure.document_ref")
    fragments = structure.get("fragments")
    if not isinstance(fragments, list) or not fragments:
        raise ValidationError("structure.fragments must be a non-empty array")
    fragment_ids = {
        _non_empty_string(fragment.get("fragment_id"), "structure.fragments[].fragment_id")
        for fragment in fragments
        if isinstance(fragment, dict)
    }
    if len(fragment_ids) != len(fragments):
        raise ValidationError("structure fragment identifiers must be unique objects")

    if candidate.get("structure_ref") != structure_id:
        raise ValidationError("candidate.structure_ref does not match structure.structure_id")
    if candidate.get("document_ref") != document_ref:
        raise ValidationError("candidate.document_ref does not match structure.document_ref")
    _non_empty_string(candidate.get("candidate_id"), "candidate.candidate_id")

    producer = candidate.get("producer")
    if not isinstance(producer, dict):
        raise ValidationError("candidate.producer must be an object")
    if producer.get("capability") != "architecture-project-understanding":
        raise ValidationError("producer.capability must be architecture-project-understanding")
    _non_empty_string(producer.get("implementation"), "producer.implementation")

    if candidate.get("status") not in STATUSES:
        raise ValidationError("candidate.status is not allowed")
    if candidate.get("authority") != AUTHORITY:
        raise ValidationError("candidate.authority must preserve every non-authoritative boundary")

    qualifications = candidate.get("qualifications")
    if not isinstance(qualifications, list) or not qualifications:
        raise ValidationError("candidate.qualifications must be a non-empty array")
    seen: set[str] = set()
    for index, qualification in enumerate(qualifications):
        field = f"candidate.qualifications[{index}]"
        if not isinstance(qualification, dict):
            raise ValidationError(f"{field} must be an object")
        fragment_ref = _non_empty_string(qualification.get("fragment_ref"), f"{field}.fragment_ref")
        if fragment_ref not in fragment_ids:
            raise ValidationError(f"{field}.fragment_ref is not present in the exact structure")
        if fragment_ref in seen:
            raise ValidationError(f"duplicate qualification for fragment {fragment_ref!r}")
        seen.add(fragment_ref)
        if not any(name in qualification for name in SEMANTIC_FIELDS):
            raise ValidationError(f"{field} must contain at least one semantic proposal")
        if qualification.get("certainty") not in CERTAINTIES:
            raise ValidationError(f"{field}.certainty is not allowed")
        _non_empty_string(qualification.get("rationale"), f"{field}.rationale")
        representation = qualification.get("representation_kind")
        if representation is not None and representation not in REPRESENTATION_KINDS:
            raise ValidationError(f"{field}.representation_kind is not allowed")
        project_state = qualification.get("project_state")
        if project_state is not None and project_state not in PROJECT_STATES:
            raise ValidationError(f"{field}.project_state is not allowed")
        for refs_field in (
            "coverage_refs", "supporting_fragment_refs", "opposing_fragment_refs"
        ):
            if refs_field in qualification:
                refs = _string_list(qualification[refs_field], f"{field}.{refs_field}")
                if refs_field != "coverage_refs":
                    unknown = set(refs) - fragment_ids
                    if unknown:
                        raise ValidationError(
                            f"{field}.{refs_field} contains unknown fragments: {sorted(unknown)}"
                        )
        if "question" in qualification:
            _non_empty_string(qualification["question"], f"{field}.question")

    for list_field in ("open_questions", "limitations"):
        if list_field in candidate:
            _string_list(candidate[list_field], f"candidate.{list_field}")
    _non_empty_string(candidate.get("created_at"), "candidate.created_at")
    return candidate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a fragment qualification candidate against one exact structure."
    )
    parser.add_argument("--structure", required=True)
    parser.add_argument("--candidate", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        validated = validate(_load(args.structure), _load(args.candidate))
    except ValidationError as exc:
        print(f"fragment-qualification: {exc}", file=sys.stderr)
        return 2
    json.dump(validated, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
