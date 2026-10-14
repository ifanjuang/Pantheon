from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MONOREPO = ROOT.parent
WORKFLOW = MONOREPO / ".github" / "workflows" / "implementation-hindsight-obsidian-o2-sync.yml"
ROUTING = ROOT / "tools" / "run_hindsight_obsidian_workspace_routing_o2.sh"


def test_workspace_routing_reuses_current_registry_backed_o2_runtime_matrix() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "export_external_qualification_pins.py" in workflow
    assert "hindsight hindsight-obsidian-sync" in workflow
    assert "HINDSIGHT_VERSION" in workflow
    assert "HINDSIGHT_OBSIDIAN_REF" in workflow
    assert "run_hindsight_obsidian_workspace_routing_o2.sh" in workflow


def test_one_human_workspace_routes_affaires_and_documentaires_to_separate_banks() -> None:
    raw = ROUTING.read_text(encoding="utf-8")
    assert 'VAULT="$LAB_ROOT/Workspace"' in raw
    assert 'AFFAIRES_BANK="workspace-projects"' in raw
    assert 'DOCUMENTAIRES_BANK="workspace-reference"' in raw
    assert '--include "$include"' in raw
    assert "Affaires/Verger/CR/CR03.md" in raw
    assert "Documentaires/Technique/bardage.md" in raw
    assert "folder:Affaires" in raw
    assert "folder:Documentaires" in raw
    assert "separate_indexes_verified':True" in raw
    assert "cross_bank_leakage_not_observed':True" in raw
    assert "independent_prune_verified':True" in raw


def test_workspace_routing_remains_neutral_and_does_not_mutate_authority_or_live_data() -> None:
    raw = ROUTING.read_text(encoding="utf-8")
    assert "agency" not in raw
    assert "agency-" not in raw.lower()
    assert "synthetic_neutral_bank_ids_used':True" in raw
    assert "real_vaults_changed':False" in raw
    assert "pantheon_state_mutated':False" in raw
    assert "evidence_admitted':False" in raw
    assert "sync_retain" not in raw
    assert "Project Anatomy" not in raw
