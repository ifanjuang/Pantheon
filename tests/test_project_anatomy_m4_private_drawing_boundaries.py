from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = (
    ROOT
    / "schemas"
    / "examples"
    / "architecture-project-understanding"
    / "private_drawing_m4_observation_bundle.yaml"
)


def _bundle() -> dict:
    value = yaml.safe_load(BUNDLE.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_m4_provisional_annotations_never_become_claim_subjects_or_provenance() -> None:
    bundle = _bundle()
    provisional_ids = {
        "rep.m4.sheet-a.provisional-note",
        "rep.m4.sheet-a.ambiguous-note",
    }

    claim_subjects = {
        claim["subject_ref"]["entity_id"]
        for claim in bundle["attribute_claim_candidates"]
        if claim["subject_ref"]["entity_type"] == "source_representation"
    }
    claim_provenance = {
        ref
        for claim in bundle["attribute_claim_candidates"]
        for ref in claim.get("source_representation_refs", [])
    }

    assert claim_subjects.isdisjoint(provisional_ids)
    assert claim_provenance.isdisjoint(provisional_ids)
    assert bundle["relation_claim_candidates"] == []
