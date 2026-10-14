from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
BOOTSTRAP = COCKPIT / "live_bootstrap.js"
FAILURE = COCKPIT / "shell" / "boot_failure.js"


def test_live_bootstrap_delegates_visible_failure_projection() -> None:
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")

    assert 'import("./shell/boot_failure.js")' in bootstrap
    assert "projectBootFailure(error)" in bootstrap
    assert "Le Cockpit n’a pas pu être chargé" not in bootstrap
    assert "stage.replaceChildren" not in bootstrap


def test_boot_failure_projection_is_visible_but_non_authoritative() -> None:
    source = FAILURE.read_text(encoding="utf-8")

    assert "export function projectBootFailure" in source
    assert 'dataset.cockpitLoad = "failed"' in source
    assert "Le Cockpit n’a pas pu être chargé" in source

    for forbidden in ("fetch(", "Hermes", "hermes", "Evidence", "ChangeCandidate", "authorization", "admission", "dispatch"):
        assert forbidden not in source


def test_bootstrap_and_failure_projection_parse_in_node() -> None:
    for path in (BOOTSTRAP, FAILURE):
        subprocess.run(["node", "--check", str(path)], check=True, capture_output=True, text=True)
