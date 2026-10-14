from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"


def test_revision_review_adapter_is_loaded_after_candidate_decisions() -> None:
    bootstrap = (COCKPIT / "live_bootstrap.js").read_text(encoding="utf-8")
    decision = bootstrap.index('"actions/change_candidate_actions.js"')
    review = bootstrap.index('"actions/change_candidate_review.js"')
    assert review > decision
    editors = (COCKPIT / "styles" / "editors.css").read_text(encoding="utf-8")
    assert 'change_candidate_review.css' in editors


def test_loader_and_assembler_keep_review_history_without_creating_new_authority() -> None:
    loader = (COCKPIT / "data" / "cockpit_data_loader.js").read_text(encoding="utf-8")
    assembler = (COCKPIT / "projection" / "child_collection_assembler.js").read_text(encoding="utf-8")

    assert '/change-candidates?status=pending_review&limit=100' in loader
    assert '/change-candidates?status=revision_requested&limit=100' in loader
    assert '["pending_review", "revision_requested"]' in assembler
    assert "new_candidate" not in assembler
    assert "runs/start" not in assembler


def test_revision_review_uses_stable_human_route_and_structured_annotations() -> None:
    review = (COCKPIT / "actions" / "change_candidate_review.js").read_text(encoding="utf-8")

    assert '../agency/change-candidates/${encodeURIComponent(id)}' in review
    assert '/request-revision' in review
    assert 'X-Pantheon-Actor' in review
    for annotation_type in (
        "source_required",
        "question",
        "hypothesis",
        "contradiction",
        "needs_deeper_review",
    ):
        assert annotation_type in review
    assert "Demander une révision" in review
    assert "project_mutated" not in review
    assert "runs/start" not in review
    assert "execution-admissions" not in review
    assert "evidence_admitted" not in review


def test_revision_review_dialog_has_mobile_and_accessibility_guards() -> None:
    review = (COCKPIT / "actions" / "change_candidate_review.js").read_text(encoding="utf-8")
    css = (COCKPIT / "styles" / "change_candidate_review.css").read_text(encoding="utf-8")

    assert 'setAttribute("aria-labelledby", "change-candidate-review-title")' in review
    assert 'aria-live="polite"' in review
    assert 'returnFocus?.focus?.()' in review
    assert 'dialog.showModal()' in review
    assert '@media (max-width: 620px)' in css
    assert 'height: 100dvh' in css
    assert 'env(safe-area-inset-bottom)' in css
    assert '@media (prefers-reduced-motion: reduce)' in css


def test_revision_review_javascript_parses() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is unavailable")
    path = COCKPIT / "actions" / "change_candidate_review.js"
    subprocess.run([node, "--check", str(path)], check=True, capture_output=True, text=True)
