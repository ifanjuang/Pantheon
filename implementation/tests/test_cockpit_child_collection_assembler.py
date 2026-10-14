from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
ASSEMBLER = COCKPIT / "projection" / "child_collection_assembler.js"
PROJECTION = COCKPIT / "projection" / "cockpit_projection.js"
DECISION_PROJECTION = COCKPIT / "projection" / "decision_request_projection.js"
REGISTRY = COCKPIT / "registries" / "navigation_registry.json"


def test_registry_sources_have_bounded_assembler_resolvers() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assembler = ASSEMBLER.read_text(encoding="utf-8")

    declared = {
        source
        for item in registry["root_collection"]["items"]
        for source in item["sources"]
    }

    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is unavailable; assembler source contract check skipped")
    result = subprocess.run(
        [
            node,
            "--input-type=module",
            "-e",
            (
                "globalThis.window = {}; "
                f"await import({json.dumps(ASSEMBLER.as_uri())}); "
                "console.log(JSON.stringify(window.PantheonChildCollectionAssembler.supportedSources));"
            ),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert set(json.loads(result.stdout)) == declared

    assert "PantheonGlobalDecisionRequests" in assembler
    assert "PantheonProjectDecisionRequests" in assembler
    assert "decisionProjection().normalize" in assembler
    assert "decision-request:${requestId}" in DECISION_PROJECTION.read_text(encoding="utf-8")

    forbidden = (
        "fetch(",
        "/v1/",
        "Authorization",
        "Evidence",
        "task_authorized",
        "approved =",
    )
    for token in forbidden:
        assert token not in assembler


def test_projection_delegates_child_graph_assembly() -> None:
    projection = PROJECTION.read_text(encoding="utf-8")
    assembler = ASSEMBLER.read_text(encoding="utf-8")

    assert "childAssembler.assemble({" in projection
    assert "navigationProjection.rootItemIds" in projection
    assert "navigationProjection.sourcesFor" in projection
    assert 'setChildren("space:pantheon"' not in projection
    assert 'setChildren("space:affaires"' not in projection
    assert 'setChildren("space:connaissances"' not in projection
    assert 'setChildren("space:outils"' not in projection
    assert 'setChildren("space:decisions"' not in projection
    assert "assembleRootCollections(context)" in assembler
    assert "assembleSelectedProject(context)" in assembler


@pytest.mark.parametrize("path", [ASSEMBLER, PROJECTION, DECISION_PROJECTION])
def test_child_collection_javascript_parses(path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is unavailable; JavaScript syntax check skipped")
    result = subprocess.run([node, "--check", str(path)], check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
