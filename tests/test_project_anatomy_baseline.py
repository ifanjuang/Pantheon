"""Guards for the V0.2-only Project Anatomy repository baseline."""

from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas" / "architecture-project-understanding"
EXAMPLES = ROOT / "schemas" / "examples" / "architecture-project-understanding"

ACTIVE_SCHEMAS = {
    "adapter_result.schema.yaml",
    "attribute_claim.schema.yaml",
    "calibration.schema.yaml",
    "classification_scheme.schema.yaml",
    "contradiction.schema.yaml",
    "derivation.schema.yaml",
    "mapping_review.schema.yaml",
    "observation_bundle.schema.yaml",
    "program.schema.yaml",
    "relation_claim.schema.yaml",
    "requirement.schema.yaml",
    "shared.schema.yaml",
    "source_representation.schema.yaml",
    "stable_object.schema.yaml",
    "write_authorization_event.schema.yaml",
    "write_command_candidate.schema.yaml",
}

DISCARDED_CARRIERS = {
    "analysis_context_candidate",
    "canonization",
    "classification",
    "deviation",
    "doubt",
    "evidence",
    "human_override",
    "instance_override",
    "object_group",
    "object_identity",
    "object_note",
    "object_relation",
    "phase_state",
    "program_change",
    "property_set",
    "space_group",
    "spatial_node",
}


def test_schema_family_contains_only_the_active_baseline() -> None:
    assert {path.name for path in SCHEMAS.glob("*.yaml")} == ACTIVE_SCHEMAS


def test_discarded_carriers_have_no_schema_or_example() -> None:
    for name in DISCARDED_CARRIERS:
        assert not (SCHEMAS / f"{name}.schema.yaml").exists()
        assert not (EXAMPLES / f"{name}.example.yaml").exists()


def test_shared_vocabulary_has_no_legacy_compatibility_definitions() -> None:
    shared = yaml.safe_load((SCHEMAS / "shared.schema.yaml").read_text(encoding="utf-8"))
    definitions = set(shared["$defs"])
    assert {
        "object_kind",
        "match_status",
        "claim_modality",
        "value_type",
        "property_status",
        "attribute_ref",
    }.isdisjoint(definitions)


def test_write_command_has_one_exact_effect_shape() -> None:
    schema = yaml.safe_load(
        (SCHEMAS / "write_command_candidate.schema.yaml").read_text(encoding="utf-8")
    )
    assert "target_model_version" not in schema["properties"]
    assert {"source_representation", "identity_relation_claim"} <= set(schema["required"])
