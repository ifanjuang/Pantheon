from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
RUNTIME_TOPOLOGY = COCKPIT / "handoff" / "runtime_topology.js"
D3_LOADER = COCKPIT / "visualization" / "d3_loader.js"
ROLE_DIALOGUE = COCKPIT / "handoff" / "role_dialogue.js"
BOOTSTRAP = COCKPIT / "live_bootstrap.js"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _node() -> str:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is unavailable; JavaScript syntax check skipped")
    return node


def test_runtime_topology_javascript_parses() -> None:
    result = subprocess.run(
        [_node(), "--check", str(RUNTIME_TOPOLOGY)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    module_result = subprocess.run(
        [_node(), "--input-type=module", "--check"],
        input=_read(D3_LOADER),
        check=False,
        capture_output=True,
        text=True,
    )
    assert module_result.returncode == 0, module_result.stderr


def test_runtime_topology_is_a_separate_read_only_surface() -> None:
    html = _read(COCKPIT / "index.html")
    bootstrap = _read(BOOTSTRAP)
    dialogue = _read(ROLE_DIALOGUE)
    runtime = _read(RUNTIME_TOPOLOGY)

    assert 'id="v2-runtime-topology"' in html
    assert 'id="v2-runtime-topology-tree"' in html
    assert 'id="v2-runtime-topology-detail"' in html
    assert "worker ≠ rôle Pantheon" in html

    assert '"handoff/runtime_topology.js"' in bootstrap
    assert bootstrap.index('"handoff/runtime_topology.js"') < bootstrap.index('"handoff/role_dialogue.js"')
    assert 'import("./visualization/d3_loader.js")' in bootstrap
    assert "window.PantheonD3Loader" in bootstrap
    assert "await ensureD3()" not in bootstrap

    assert 'kind === "runtime.subagent"' in dialogue
    assert "PantheonRuntimeTopology?.consume" in dialogue
    assert dialogue.count("role-traces/${encodeURIComponent(runId)}/events") == 1
    assert "reasoning.available" not in dialogue

    assert "event.governed_identity !== false" in runtime
    assert "event.parent_id" in runtime
    assert "synthetic_root: true" in runtime
    assert "cycleDetected" in runtime
    assert "d3.hierarchy" in runtime
    assert "d3.tree()" in runtime
    assert "forceSimulation" not in runtime
    assert "output_tail" not in runtime
    assert "reasoning" not in runtime.lower()
    assert "fetch(" not in runtime


def test_d3_is_pinned_integrity_checked_and_lazy() -> None:
    loader = _read(D3_LOADER)

    assert 'const D3_VERSION = "7.9.0";' in loader
    assert "sha512-vc58qvvBdrDR4etbxMdlTt4GBQk1qjvyORR2nrsPsFPyrs+/u5c3+1Ct6upOgdZoIl7eq6k3a1UPDSNAQi/32A==" in loader
    assert "script.integrity = D3_SCRIPT_SRI" in loader
    assert 'script.crossOrigin = "anonymous"' in loader
    assert 'script.referrerPolicy = "no-referrer"' in loader
    assert "cdn.jsdelivr.net/npm/d3@" in loader
    assert "cdnjs.cloudflare.com/ajax/libs/d3/" in loader
    assert "export async function ensureD3()" in loader


def test_runtime_topology_styles_do_not_add_a_fifth_local_stylesheet() -> None:
    html = _read(COCKPIT / "index.html")
    runtime = _read(RUNTIME_TOPOLOGY)
    local_styles = [
        line for line in html.splitlines()
        if '<link rel="stylesheet" href="styles/' in line
    ]

    assert len(local_styles) == 4
    assert "pantheon-runtime-topology-styles" in runtime
    assert ".v2-runtime-topology-link--run" in runtime
    assert '.v2-runtime-topology-node circle[data-selected="true"]' in runtime
