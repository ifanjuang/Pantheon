from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
BOOTSTRAP = COCKPIT / "live_bootstrap.js"
FAILURE = COCKPIT / "shell" / "boot_failure.js"


def test_live_bootstrap_delegates_visible_failure_projection() -> None:
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
    failure = FAILURE.read_text(encoding="utf-8")

    assert 'import("./shell/boot_failure.js")' in bootstrap
    assert "projectBootFailure(error)" in bootstrap
    assert 'message.textContent = "Le Cockpit n’a pas pu être chargé. Rechargez la page."' not in bootstrap
    assert 'document.documentElement.dataset.cockpitLoad = "failed"' in failure
    assert 'network.textContent = "chargement impossible"' in failure
    assert 'message.textContent = "Le Cockpit n’a pas pu être chargé. Rechargez la page."' in failure


def test_boot_failure_projection_has_no_domain_or_runtime_authority() -> None:
    failure = FAILURE.read_text(encoding="utf-8")

    for forbidden in (
        "fetch(",
        "XMLHttpRequest",
        "runs/start",
        "execution-admissions",
        "change-candidates",
        "Evidence",
    ):
        assert forbidden not in failure


@pytest.mark.parametrize("path", [BOOTSTRAP, FAILURE])
def test_boot_modules_parse(path: Path) -> None:
    node = shutil.which("node")
    if node is None:  # pragma: no cover
        pytest.skip("Node.js is unavailable")
    result = subprocess.run([node, "--check", str(path)], check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
