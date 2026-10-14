"""Regression checks for the bounded Lotus renderer qualification."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "lotus_renderer_pilot.json"


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_lotus_renderer_profile_is_source_reviewed_not_runtime_accepted() -> None:
    fixture = _fixture()

    assert fixture["pilot_id"] == "lotus-renderer-001"
    assert fixture["capability"] == "optional_interactive_visualization"
    assert fixture["execution_status"] == "source_reviewed_runtime_smoke_pending"

    reference = fixture["reference_candidate"]
    assert reference["repository"] == "TzadikimBIU/lotus"
    assert reference["reviewed_release"] == "1.2.3"
    assert reference["reviewed_main_sha"] == "b3b4dec3095d6cfe32d1443ad8a4a87ea50dd3e4"
    assert reference["upstream_open_prs_observed"] == 0
    assert reference["upstream_open_issues_observed"] == 0
    assert reference["upstream_smoke_run"] == {
        "run_id": 32519680456,
        "head_sha": "b3b4dec3095d6cfe32d1443ad8a4a87ea50dd3e4",
        "conclusion": "success",
    }

    assert reference["reviewed_source_blobs"] == {
        "src/engine/managedOutput.ts": "8d2ea48eee202ee6faae7f1d24e553982af23aff",
        "src/plugin/main.ts": "57e0a52c6b0f688c970e084daae6840c25f4fa43",
        "src/plugin/visualization/javascriptGraphs.ts": "1e2358b21cfb0c2b5c19d505efc4316f8c2d36c1",
        "src/engine/defaultSettings.ts": "342c3892c0661f86547d493710f939210316f99a",
        "src/engine/buildProfile.ts": "372ddd5a11310da170eb9fe8c385e7c420bc4941",
        "src/engine/languagePackages.ts": "499d572ebe5bee43f55476546a79c7a47708cb5e",
        "scripts/managed-output.test.mjs": "77a1320eb386ece7ed59db74c275c016c92b2a0d",
    }

    assert "provider_accepted" not in fixture
    assert "capability_binding" not in fixture
    assert "installation_status" not in fixture


def test_lotus_renderer_profile_keeps_execution_and_persistence_out() -> None:
    fixture = _fixture()
    observations = fixture["source_observations"]
    profile = fixture["candidate_profile"]

    assert observations["managed_display_path"]["status"] == "observed_in_source"
    assert observations["default_settings"] == {
        "status": "observed_in_source",
        "enableLocalExecution": False,
        "writeOutputToNote": False,
        "autoRunOnFileOpen": False,
        "apiEnabled": False,
        "loggingEnabled": False,
    }

    assert profile["name"] == "renderer_only_d3"
    assert profile["allowed_mime_types"] == ["application/vnd.lotus.d3+json"]
    assert profile["required_runtime_settings"] == {
        "enableLocalExecution": False,
        "writeOutputToNote": False,
        "autoRunOnFileOpen": False,
        "apiEnabled": False,
        "loggingEnabled": False,
    }
    assert set(profile["payload_contract"]["allowed_kinds"]) == {"bar", "line", "scatter"}
    assert profile["payload_contract"]["data"] == "JSON records only"
    assert profile["payload_contract"]["custom_color"] == "omit in the first profile; use renderer default"
    assert profile["payload_contract"]["external_urls"] == "forbidden"
    assert profile["payload_contract"]["script_or_function_fields"] == "forbidden"
    assert profile["payload_contract"]["html"] == "forbidden"
    assert "separate workspace persistence action" in profile["workspace_write_boundary"]
    assert "Rendering an existing fence is read-only" in profile["workspace_write_boundary"]


def test_lotus_renderer_profile_defers_wider_renderer_and_execution_surfaces() -> None:
    fixture = _fixture()
    observations = fixture["source_observations"]

    assert observations["d3_renderer"]["status"] == "candidate_for_runtime_smoke"
    assert observations["d3_renderer"]["mime_type"] == "application/vnd.lotus.d3+json"
    assert set(observations["d3_renderer"]["observed_shape"]["kind"]) == {"bar", "line", "scatter"}
    assert "no JavaScript from the display payload is evaluated" in observations["d3_renderer"]["observed_shape"]["behavior"]

    cytoscape = observations["cytoscape_renderer"]
    assert cytoscape["status"] == "deferred_restricted_candidate"
    assert "CytoscapeOptions" in cytoscape["reason"]
    assert "allowlisted projection" in cytoscape["reason"]

    excluded = set(observations["excluded_surfaces"])
    for surface in (
        "local fenced-code execution",
        "obsidian-js execution",
        "custom languages",
        "external language packs",
        "container execution groups",
        "Graphviz process execution",
        "text/html display",
        "Plotly display",
        "JSXGraph display",
        "Cytoscape display until a restricted payload contract is demonstrated",
        "automatic write-back",
        "API server",
        "logging sinks",
        "signing and reproducibility mutation commands",
    ):
        assert surface in excluded


def test_lotus_renderer_profile_keeps_projection_subordinate() -> None:
    fixture = _fixture()
    boundaries = set(fixture["candidate_profile"]["projection_boundary"])
    assert {
        "display record != Evidence",
        "rendered node or edge != governed relation",
        "view model != canonical model",
        "visualization success != professional validation",
        "renderer available != renderer authorized",
        "projection != persistence",
    } <= boundaries

    cases = {case["id"]: case for case in fixture["cases"]}
    assert set(cases) == {
        "managed_display_without_code_runner",
        "execution_disabled_profile",
        "d3_fixed_declarative_payload",
        "invalid_or_unapproved_mime_rejected_by_profile",
        "render_does_not_mutate_note",
        "visualization_is_not_authority",
    }
    assert cases["managed_display_without_code_runner"]["runtime_smoke_required"] is True
    assert cases["execution_disabled_profile"]["runtime_smoke_required"] is True
    assert cases["d3_fixed_declarative_payload"]["runtime_smoke_required"] is True
    assert cases["render_does_not_mutate_note"]["runtime_smoke_required"] is True
    assert cases["invalid_or_unapproved_mime_rejected_by_profile"]["runtime_smoke_required"] is False
    assert cases["visualization_is_not_authority"]["runtime_smoke_required"] is False

    gate = fixture["execution_gate"]
    assert "isolated Obsidian test vault" in gate["required_before_register_placement"]
    assert "before/after note hashes" in gate["required_before_register_placement"]
    assert "Do not treat source review" in gate["forbidden_shortcut"]
