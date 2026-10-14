"""Regression checks for the report-only Obsidian operational-health pilot."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "obsidian_operational_health_pilot.json"
OBSIDIAN = ROOT / "docs" / "governance" / "OBSIDIAN_HINDSIGHT_WORKSPACE_MODEL.md"
INSPECTOR = ROOT / "docs" / "architecture" / "WORKSPACE_MANIFEST_INSPECTOR_CANDIDATE.md"
PIN_REGISTRY = ROOT / "implementation" / "qualification" / "external-pins.json"


def test_operational_health_pilot_reuses_existing_workspace_owners() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    obsidian = OBSIDIAN.read_text(encoding="utf-8")
    inspector = INSPECTOR.read_text(encoding="utf-8")

    assert fixture["owners"] == [
        "docs/governance/OBSIDIAN_HINDSIGHT_WORKSPACE_MODEL.md",
        "docs/architecture/WORKSPACE_MANIFEST_INSPECTOR_CANDIDATE.md",
    ]
    assert "report-only workspace audit" in obsidian
    assert "It must not auto-fix, rename, merge, archive, relink or rewrite professional material." in obsidian
    assert "### Workspace-health projection" in inspector
    assert "workspace health != professional currentness" in inspector
    assert "must not auto-fix, rename, merge, archive, relink or rewrite professional material" in inspector


def test_prior_art_is_not_promoted_to_dependency_or_qualification_pin() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    pins = json.loads(PIN_REGISTRY.read_text(encoding="utf-8"))["pins"]
    prior_art = fixture["prior_art"]

    assert prior_art["repository"] == "dtiger1889-ops/obsidian-agent-integration"
    assert prior_art["reviewed_main_sha"] == "6f1d58ceb49e3fbb69e52b502e1f9d794fb173b3"
    assert prior_art["classification"] == "operational prior art only; not a Pantheon dependency or authority"
    assert "obsidian-agent-integration" not in pins


def test_operational_health_cases_remain_prepared_report_only_and_bounded() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    assert fixture["execution_status"] == "prepared_not_executed"
    assert fixture["post_mutation_posture"]["mode"] == "report_only"
    assert fixture["post_mutation_posture"]["automatic_repairs"] is False
    assert "observed_results" not in fixture

    assert set(fixture["invariants"]) == {
        "workspace health observation != professional currentness",
        "health finding != defect confirmed",
        "filesystem mutation success != sync convergence",
        "config snapshot != active per-device state",
        "metadata field != source-authored observation",
        "conflict copy != stale by definition",
        "bulk mutation != authorization to auto-fix",
        "audit clean != Evidence",
        "workspace path != governed identity",
    }

    cases = {case["id"]: case for case in fixture["cases"]}
    assert set(cases) == {
        "archive_move_link_impact",
        "link_frontmatter_shape",
        "timestamp_writer_ambiguity",
        "device_local_setting_divergence",
        "sync_conflict_live_copy_ambiguity",
        "scripted_write_convergence",
        "external_leaf_pointer_rename",
    }

    assert "auto-relink every inbound reference" in cases["archive_move_link_impact"]["forbidden_effects"]
    assert "treat the metadata timestamp as proof of a human-authored edit" in cases["timestamp_writer_ambiguity"]["forbidden_effects"]
    assert "assume synced configuration proves effective device state" in cases["device_local_setting_divergence"]["forbidden_effects"]
    assert "assume the live filename is the correct version" in cases["sync_conflict_live_copy_ambiguity"]["forbidden_effects"]
    assert "claim sync success from local filesystem success" in cases["scripted_write_convergence"]["forbidden_effects"]
    assert "rewrite files outside the authorized scope automatically" in cases["external_leaf_pointer_rename"]["forbidden_effects"]

    assert fixture["authorized_scope"]["include_prefixes"] == ["projects/maison/"]
    assert fixture["authorized_scope"]["explicitly_out_of_scope_prefixes"] == ["projects/autre-projet/"]
    assert "Do not convert the prepared expectations" in fixture["execution_gate"]["forbidden_shortcut"]
