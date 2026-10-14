from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "governance" / "CAPABILITY_REGISTRY.md"
PASSPORT_SCHEMA = ROOT / "schemas" / "capability_passport.schema.yaml"
WORKFLOW_SCHEMA = ROOT / "schemas" / "workflow_manifest.schema.yaml"
SKILL_SCHEMA = ROOT / "schemas" / "skill_manifest.schema.yaml"


def test_capability_slot_is_not_collapsed_into_capability() -> None:
    registry = REGISTRY.read_text(encoding="utf-8")

    assert "Capability Slot != Capability" in registry
    assert "Capability Slot" in registry
    assert "replaceable function / binding target" in registry


def test_capability_passport_allows_skill_as_a_capability_primitive() -> None:
    schema = yaml.safe_load(PASSPORT_SCHEMA.read_text(encoding="utf-8"))
    primitives = schema["properties"]["capability"]["properties"]["primitive"]["enum"]

    assert "skill" in primitives


def test_skill_reference_does_not_collapse_admission_or_task_authorization() -> None:
    registry = REGISTRY.read_text(encoding="utf-8")
    workflow = WORKFLOW_SCHEMA.read_text(encoding="utf-8")
    skill = SKILL_SCHEMA.read_text(encoding="utf-8")

    assert "skill_manifest_ref:" in workflow
    assert "Optional join to the admitted skill backing this step" in workflow
    assert "skill_id:" in skill
    assert "Skill validated != Capability admitted" in registry
    assert "Capability admitted != task-authorized" in registry


def test_passport_and_runtime_binding_remain_distinct() -> None:
    registry = REGISTRY.read_text(encoding="utf-8")

    assert "Capability Passport != runtime binding" in registry
    assert "installed != approved" in registry
    assert "activated != task-authorized" in registry
