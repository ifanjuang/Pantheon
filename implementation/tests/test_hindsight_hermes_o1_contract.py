from __future__ import annotations

import ast
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MONOREPO = ROOT.parent
HARNESS = ROOT / "tools" / "run_hindsight_hermes_o1.py"
FIXTURE = ROOT / "tools" / "hindsight_hermes_o1_fixture.py"
SEQUENCE = ROOT / "tools" / "run_hindsight_hermes_o1.sh"
WORKFLOW = MONOREPO / ".github" / "workflows" / "implementation-hindsight-hermes-o1-lab.yml"
HISTORICAL_O3_WORKFLOW = MONOREPO / ".github" / "workflows" / "implementation-hindsight-obsidian-hermes-o3-lab.yml"
HISTORICAL_O3_SEQUENCE = ROOT / "tools" / "run_hindsight_obsidian_hermes_o3.sh"
HISTORICAL_O3_CONTRACT = ROOT / "tests" / "test_hindsight_obsidian_hermes_o3_contract.py"


def test_o1_harness_is_bounded_to_assistant_personal() -> None:
    raw = HARNESS.read_text(encoding="utf-8")
    ast.parse(raw)
    assert 'ASSISTANT_PROFILE = "assistant-personal"' in raw
    assert 'GOVERNED_PROFILE = "pantheon-governed"' in raw
    assert '"provider": "hindsight"' in raw
    assert '"memory_mode": "tools"' in raw
    assert '"auto_retain": False' in raw
    assert '"auto_recall": False' in raw
    assert '"pantheon_write_path": False' in raw
    assert '"evidence_admission": False' in raw


def test_model_fixture_requires_real_hindsight_tool_result() -> None:
    raw = FIXTURE.read_text(encoding="utf-8")
    ast.parse(raw)
    assert "hindsight_recall" in raw
    assert "PANTHEON_O1_SYNTHETIC_MEMORY_MARKER" in raw
    assert "O1_HINDSIGHT_RECALL_COMPLETED" in raw
    assert "Hindsight" in raw
    assert "retain" not in raw.lower().split("the fixture never impersonates hindsight", 1)[-1].split("from __future__", 1)[0]


def test_shared_hindsight_config_supports_strict_provider_scope() -> None:
    raw = HARNESS.read_text(encoding="utf-8")
    ast.parse(raw)
    assert 'cfg.add_argument("--recall-tag", action="append", default=[])' in raw
    assert 'cfg.add_argument("--recall-tags-match", default="all_strict")' in raw
    assert 'hindsight_config["recall_tags"] = recall_tags' in raw
    assert 'hindsight_config["recall_tags_match"] = recall_tags_match' in raw
    assert '"auto_retain": False' in raw
    assert '"auto_recall": False' in raw


def test_shared_fixture_can_exclude_stale_or_cross_scope_results() -> None:
    raw = FIXTURE.read_text(encoding="utf-8")
    ast.parse(raw)
    assert "DEFAULT_MARKER = \"PANTHEON_O1_SYNTHETIC_MEMORY_MARKER\"" in raw
    assert "DEFAULT_SUCCESS_TOKEN = \"O1_HINDSIGHT_RECALL_COMPLETED\"" in raw
    assert 'parser.add_argument("--forbid-marker", action="append", default=[])' in raw
    assert "forbidden_marker_seen_in_tool_result" in raw
    assert "hindsight_recall" in raw


def test_live_sequence_uses_registry_versioned_real_hindsight_endpoint_and_rolls_back() -> None:
    raw = SEQUENCE.read_text(encoding="utf-8")
    assert raw.startswith("#!/usr/bin/env bash\nset -euo pipefail")
    assert '"hindsight-client==${HINDSIGHT_VERSION}"' in raw
    assert "HERMES_RELEASE_COMMIT:?load hermes-agent qualification pin first" in raw
    assert "HINDSIGHT_VERSION:?load hindsight qualification pin first" in raw
    assert "hindsight_client import Hindsight" in raw
    assert "client.retain" in raw
    assert "client.recall" in raw
    assert "hermes -p assistant-personal chat -q" in raw
    assert "capture-memory-status --profile pantheon-governed" in raw
    assert "profile delete assistant-personal --yes" in raw
    assert "Project Anatomy" not in raw
    assert "Evidence" not in raw
    assert "LangChain" not in raw
    assert "LangGraph" not in raw


def test_active_workflow_resolves_current_registry_pins_and_runs_self_contained_lab() -> None:
    raw = WORKFLOW.read_text(encoding="utf-8")
    workflow = yaml.safe_load(raw)
    assert workflow["name"] == "Hindsight Hermes O1 Sandbox"
    assert "pull_request" in workflow[True]
    assert "workflow_dispatch" in workflow[True]
    assert "contract" in workflow["jobs"]
    assert "live-lab" in workflow["jobs"]
    assert workflow["jobs"]["live-lab"].get("if") is None
    assert "export_external_qualification_pins.py" in raw
    assert "hermes-agent hindsight" in raw
    assert "HERMES_REPOSITORY" in raw
    assert "HERMES_REF" in raw
    assert "HINDSIGHT_IMAGE" in raw
    assert "HINDSIGHT_VERSION" in raw
    assert "HINDSIGHT_API_RETAIN_EXTRACTION_MODE=chunks" in raw
    assert "HINDSIGHT_API_URL: http://127.0.0.1:8888" in raw
    assert "secrets." not in raw
    assert "docker stop pantheon-o1-hindsight" in raw
    assert "hindsight-image-repodigests.json" in raw
    assert "production" not in raw.lower()


def test_historical_o3_live_lane_stays_retired() -> None:
    assert not HISTORICAL_O3_WORKFLOW.exists()
    assert not HISTORICAL_O3_SEQUENCE.exists()
    assert not HISTORICAL_O3_CONTRACT.exists()
