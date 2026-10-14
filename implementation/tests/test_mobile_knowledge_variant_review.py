from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
EDITOR = ROOT / "mvp_vertical" / "mobile_editor"


def test_variant_review_adapter_loads_after_existing_editor() -> None:
    html = (EDITOR / "index.html").read_text(encoding="utf-8")

    assert 'id="variant-ab"' in html
    assert 'id="edit-reviews"' in html
    assert 'aria-live="polite"' in html
    assert html.index('src="app.js"') < html.index('src="variant_review.js"')
    assert "la sélection d’une variante ne modifient pas la Knowledge" in html
    assert "Un retour d’exécution" in html


def test_mobile_variant_queue_preserves_scope_and_separates_selection_from_apply() -> None:
    javascript = (EDITOR / "variant_review.js").read_text(encoding="utf-8")

    assert '"pantheon-knowledge:variant-queue"' in javascript
    assert "base_version: state.current.version" in javascript
    assert "selection_start: start" in javascript
    assert "selection_end: end" in javascript
    assert "selected_text: textarea.value.slice(start, end)" in javascript
    assert "requested_variant_count: requestedVariantCount" in javascript
    assert "/variant-edit-requests" in javascript
    assert "/select-variant" in javascript
    assert "/apply-selected" in javascript
    assert "Variante sélectionnée. Aucun Markdown n’a encore été modifié." in javascript
    assert "project-knowledge-edit-variant" not in javascript
    assert "review_status:" not in javascript
    assert "runs/start" not in javascript
    assert "execution-admissions" not in javascript


def test_mobile_variant_review_is_explicit_and_not_a_polling_loop() -> None:
    javascript = (EDITOR / "variant_review.js").read_text(encoding="utf-8")

    assert 'id="refresh-reviews"' in (EDITOR / "index.html").read_text(encoding="utf-8")
    assert '$("refresh-reviews").onclick = loadReviews' in javascript
    assert "setInterval" not in javascript
    assert "setTimeout(() => void syncVariantQueue(), 0)" in javascript
    assert "window.addEventListener(\"online\"" in javascript
    assert '$("variant-ab").disabled = !active' in javascript


def test_variant_comparison_is_mobile_accessible() -> None:
    css = (EDITOR / "styles.css").read_text(encoding="utf-8")

    assert ".proposal-variants" in css
    assert ".proposal-variant.selected" in css
    assert "grid-template-columns:repeat(2" in css
    assert "@media (max-width:760px)" in css
    assert ".connect,.workspace,.proposal-variants { grid-template-columns:1fr; }" in css
    assert ":focus-visible" in css
    assert "@media (prefers-reduced-motion:reduce)" in css


def test_service_worker_caches_variant_shell_but_not_authenticated_api() -> None:
    service_worker = (EDITOR / "sw.js").read_text(encoding="utf-8")

    assert 'pantheon-knowledge-shell-r4' in service_worker
    assert '"variant_review.js"' in service_worker
    assert '"/knowledge/"' in service_worker
    assert '"/edit-requests"' in service_worker
    assert '"/execution-results/"' in service_worker
    assert "if (API_PREFIXES.some" in service_worker


def test_variant_review_javascript_parses() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is unavailable")
    result = subprocess.run(
        [node, "--check", str(EDITOR / "variant_review.js")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
