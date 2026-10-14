from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MONOREPO = ROOT.parent
WORKFLOW = MONOREPO / ".github" / "workflows" / "implementation-hindsight-obsidian-o2-sync.yml"
SEQUENCE = ROOT / "tools" / "run_hindsight_obsidian_o2.sh"


def test_o2_uses_current_official_headless_sync_pin_registry() -> None:
    raw = WORKFLOW.read_text(encoding="utf-8")
    workflow = yaml.safe_load(raw)
    assert workflow["name"] == "Hindsight Obsidian O2 Sync"
    assert "pull_request" in workflow[True]
    assert "workflow_dispatch" in workflow[True]
    assert "export_external_qualification_pins.py" in raw
    assert "hindsight hindsight-obsidian-sync" in raw
    assert "HINDSIGHT_OBSIDIAN_REPOSITORY" in raw
    assert "HINDSIGHT_OBSIDIAN_REF" in raw
    assert "HINDSIGHT_OBSIDIAN_VERSION" in raw
    assert "hindsight-obsidian-sync" in raw
    assert "npm run lint" in raw
    assert "npm test" in raw
    assert "npm run build" in raw
    assert "pantheon-mvp" not in raw


def test_o2_live_lab_is_current_local_synthetic_and_no_llm_use() -> None:
    raw = WORKFLOW.read_text(encoding="utf-8")
    assert "HINDSIGHT_IMAGE" in raw
    assert "HINDSIGHT_VERSION" in raw
    assert "HINDSIGHT_API_RETAIN_EXTRACTION_MODE=chunks" in raw
    assert "HINDSIGHT_API_ENABLE_AUTO_CONSOLIDATION=false" in raw
    assert "HINDSIGHT_API_ENABLE_OBSERVATIONS=false" in raw
    assert "secrets." not in raw
    assert "pantheon-o2-synthetic" in raw
    assert "docker stop pantheon-o2-hindsight" in raw


def test_o2_exercises_real_reconcile_lifecycle_and_scope() -> None:
    raw = SEQUENCE.read_text(encoding="utf-8")
    assert raw.startswith("#!/usr/bin/env bash\nset -euo pipefail")
    assert 'VAULT_A="$LAB_ROOT/Vault-A"' in raw
    assert 'VAULT_B="$LAB_ROOT/Vault-B"' in raw
    assert '"$VAULT_A/Projects/Alpha"' in raw
    assert '"$VAULT_A/Projects/Beta"' in raw
    assert '"$VAULT_B/Projects/Alpha"' in raw
    assert raw.count('node "$CLI" reconcile') == 1
    assert "=2 unchanged" in raw
    assert "~1 updated" in raw
    assert "-1 deleted" in raw
    assert 'mv "$VAULT_A/Projects/Alpha/note.md"' in raw
    assert "tags_match': 'all_strict'" in raw
    assert "vault:Vault-A" in raw
    assert "vault:Vault-B" in raw
    assert "folder:Projects/Alpha" in raw
    assert "document_id" in raw
    assert "metadata" in raw and "path" in raw
    assert "pantheon_state_mutated':False" in raw
    assert "evidence_admitted':False" in raw
    assert "MVP_ROOT" not in raw


def test_o2_proves_realistic_strict_project_scope_without_new_scope_owner() -> None:
    raw = SEQUENCE.read_text(encoding="utf-8")
    assert "Projects/Project-A/CR/CR01.md" in raw
    assert "Projects/Project-A/CR/CR03.md" in raw
    assert "Projects/Project-A/CCTP/facade.md" in raw
    assert "Projects/Project-A/Mail/note.md" in raw
    assert "Projects/Project-B/CR/CR03.md" in raw
    assert "Projects/Project-B/CCTP/facade.md" in raw
    assert "folder:Projects/Project-A" in raw
    assert "folder:Projects/Project-B" in raw
    assert "PANTHEON_O2_PROJECT_A_CR03_TARGET" in raw
    assert "PANTHEON_O2_PROJECT_B_ONLY_FACT" in raw
    assert "no_silent_cross_project_widening_verified':True" in raw
    assert "explicit_project_widening_verified':True" in raw
    assert "strict_project_scope_verified':True" in raw
    assert "BANK =" not in raw


def test_o2_does_not_create_pantheon_memory_or_sync_authority() -> None:
    raw = SEQUENCE.read_text(encoding="utf-8") + WORKFLOW.read_text(encoding="utf-8")
    assert "Project Anatomy" not in raw
    assert "Registre Probatoire" not in raw
    assert "LangChain" not in raw
    assert "LangGraph" not in raw
    assert "bidirectional" not in raw.lower()
