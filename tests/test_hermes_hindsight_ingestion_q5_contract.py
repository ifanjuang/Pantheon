from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "hermes-hindsight-ingestion-q5.yml"
HARNESS = ROOT / "implementation" / "tools" / "run_hermes_hindsight_ingestion_q5.sh"


def test_q5_resolves_current_hindsight_matrix_from_registry() -> None:
    raw = WORKFLOW.read_text(encoding="utf-8")
    assert "export_external_qualification_pins.py" in raw
    assert "hermes-agent hindsight hindsight-obsidian-sync" in raw
    assert "HERMES_REPOSITORY" in raw
    assert "HERMES_REF" in raw
    assert "HINDSIGHT_OBSIDIAN_REPOSITORY" in raw
    assert "HINDSIGHT_OBSIDIAN_REF" in raw
    assert "HINDSIGHT_OBSIDIAN_VERSION" in raw
    assert "HINDSIGHT_IMAGE" in raw
    assert "HERMES_OBSIDIAN_SKILL_BLOB" not in raw
    assert "latest" not in raw.lower()
    assert "edge" not in raw.lower()


def test_q5_proves_hermes_file_write_is_not_hindsight_write_path() -> None:
    raw = HARNESS.read_text(encoding="utf-8")
    assert raw.startswith("#!/usr/bin/env bash\nset -euo pipefail")
    assert "from tools.file_tools import patch_tool, read_file_tool, write_file_tool" in raw
    assert "write_file_tool(str(note),content)" in raw
    assert "read_file_tool(str(note))" in raw
    assert "patch_tool(" in raw
    assert "AFTER_HERMES_CREATE=$(retain_batch_count)" in raw
    assert 'test "$BEFORE_CREATE" = "$AFTER_HERMES_CREATE"' in raw
    assert "AFTER_HERMES_PATCH=$(retain_batch_count)" in raw
    assert 'test "$BEFORE_PATCH" = "$AFTER_HERMES_PATCH"' in raw
    assert "pre-sync-create-recall.json" in raw
    assert "pre-sync-patch-recall.json" in raw
    assert "os.environ['HINDSIGHT_VERSION']" in raw
    assert "os.environ['HINDSIGHT_OBSIDIAN_VERSION']" in raw


def test_q5_keeps_hindsight_obsidian_as_single_ingestion_producer() -> None:
    raw = HARNESS.read_text(encoding="utf-8")
    assert 'node "$CLI" reconcile' in raw
    assert "reconcile: +1 added" in raw
    assert "reconcile: +0 added, ~1 updated" in raw
    assert "'single_hindsight_producer_kind':'hindsight-obsidian-sync'" in raw
    assert "'hermes_direct_hindsight_write':False" in raw
    assert "'source_provenance_verified':True" in raw
    assert "'hindsight_writeback_to_vault':False" in raw
    assert "'pantheon_state_mutated':False" in raw
    assert "'evidence_admitted':False" in raw
    assert "sync_retain" not in raw
