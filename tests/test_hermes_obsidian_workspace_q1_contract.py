from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "hermes-obsidian-workspace-q1.yml"
REGISTRY = ROOT / "implementation" / "qualification" / "external-pins.json"


def test_q1_uses_canonical_hermes_pin_and_derives_skill_blob() -> None:
    raw = WORKFLOW.read_text(encoding="utf-8")
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    hermes = registry["pins"]["hermes-agent"]

    assert "export_external_qualification_pins.py" in raw
    assert "hermes-agent" in raw
    assert "${{ env.HERMES_REPOSITORY }}" in raw
    assert "${{ env.HERMES_REF }}" in raw
    assert hermes["ref"] not in raw
    assert hermes["version"] not in raw
    assert "git -C hermes-agent hash-object skills/note-taking/obsidian/SKILL.md" in raw
    assert "HERMES_OBSIDIAN_SKILL_BLOB=$SKILL_BLOB" in raw
    assert "skills/note-taking/obsidian/SKILL.md" in raw
    assert "latest" not in raw.lower()


def test_q1_exercises_actual_hermes_file_tools_on_synthetic_workspace() -> None:
    raw = WORKFLOW.read_text(encoding="utf-8")
    assert "write_file_tool" in raw
    assert "read_file_tool" in raw
    assert "patch_tool" in raw
    assert "PANTHEON_HERMES_OBSIDIAN_CREATE" in raw
    assert "PANTHEON_HERMES_OBSIDIAN_PATCH" in raw
    assert 'workspace / "Affaires" / "Alpha" / "note.md"' in raw
    assert "outside.md" in raw
    assert '"raw_tool_root_enforcement": False' in raw


def test_q1_preserves_authority_and_destructive_operation_boundaries() -> None:
    raw = WORKFLOW.read_text(encoding="utf-8")
    assert '"couchdb_direct_write": False' in raw
    assert '"hindsight_direct_write": False' in raw
    assert '"pantheon_state_mutated": False' in raw
    assert '"evidence_admitted": False' in raw
    assert '"delete_qualified": False' in raw
    assert '"move_rename_qualified": False' in raw
    assert "whole_file_overwrite_without_pantheon_revision_gate" in raw
