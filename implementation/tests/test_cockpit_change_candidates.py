from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
PROJECTION = COCKPIT / "projection" / "cockpit_projection.js"
ASSEMBLER = COCKPIT / "projection" / "child_collection_assembler.js"
DATA_LOADER = COCKPIT / "data" / "cockpit_data_loader.js"


def test_project_back_uses_authoritative_server_schema() -> None:
    renderer = PROJECTION.read_text(encoding="utf-8")
    data_loader = DATA_LOADER.read_text(encoding="utf-8")

    assert '../agency/schema/project' in data_loader
    assert '../v1/agency/' not in data_loader
    assert "dataLoader.loadProjectSchema(token)" in renderer
    assert "state.projectSchema" in renderer
    assert "projectSchemaRows" in renderer
    assert 'field.storage === "attributes"' in renderer
    assert 'field.title || field.label || field.key' in renderer
    assert "const labels = {" not in renderer


def test_reviewable_change_candidates_stay_distinct_from_decision_requests() -> None:
    renderer = PROJECTION.read_text(encoding="utf-8")
    assembler = ASSEMBLER.read_text(encoding="utf-8")
    data_loader = DATA_LOADER.read_text(encoding="utf-8")

    assert '/change-candidates?status=pending_review&limit=100' in data_loader
    assert '/change-candidates?status=revision_requested&limit=100' in data_loader
    assert "dataLoader.loadProjectBundle(project, token)" in renderer
    assert 'entity_type: "project_change_candidate"' in renderer
    assert 'entity_id: `decision:change:${item.candidate_id}`' in renderer
    assert 'category: "Décision · Modification"' in renderer
    assert 'entity_type: "work_decision"' not in renderer
    assert "normalizeWorkDecision" not in renderer
    assert "pending_change_candidates(context)" in assembler
    assert '["pending_review", "revision_requested"]' in assembler
    assert "decision_requests(_context)" in assembler
    assert "work_decisions(context)" not in assembler
    assert "current_runs(context)" in assembler
    assert "modelsForSources(sources, context)" in assembler
    assert 'setChildren("space:pantheon"' not in renderer
    assert 'setChildren("space:decisions"' not in renderer
    assert "state.changeCandidates" in renderer


def test_change_candidate_buttons_use_human_apply_reject_routes() -> None:
    bootstrap = (COCKPIT / "live_bootstrap.js").read_text(encoding="utf-8")
    actions = (COCKPIT / "actions" / "change_candidate_actions.js").read_text(encoding="utf-8")

    assert '"actions/change_candidate_actions.js"' in bootstrap
    assert 'decision:change:' in actions
    assert '/agency/change-candidates/${encodeURIComponent(candidate.candidateId)}/apply' in actions
    assert '/agency/change-candidates/${encodeURIComponent(candidate.candidateId)}/reject' in actions
    assert '/v1/agency/' not in actions
    assert 'X-Pantheon-Actor' in actions
    assert "runs/start" not in actions
    assert "execution-admissions" not in actions


def test_change_candidate_javascript_parses() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is unavailable")
    path = COCKPIT / "actions" / "change_candidate_actions.js"
    subprocess.run([node, "--check", str(path)], check=True, capture_output=True, text=True)
