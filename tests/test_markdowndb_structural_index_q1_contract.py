"""Contract for the completed MarkdownDB structural-index qualification record."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "implementation" / "qualification" / "external-pins.json"
UPSTREAM = ROOT / "implementation" / "qualification" / "external-upstream-observations.json"
WORKFLOW = ROOT / ".github" / "workflows" / "markdowndb-structural-index-q1.yml"
CORPUS = ROOT / "tests" / "fixtures" / "obsidian_graph_health_pilot.json"
OBSERVED = ROOT / "tests" / "fixtures" / "markdowndb_structural_index_observed_v0.9.5.json"
INSPECTOR = ROOT / "docs" / "architecture" / "WORKSPACE_MANIFEST_INSPECTOR_CANDIDATE.md"


def test_completed_markdowndb_qualification_is_not_a_current_input() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    observations = json.loads(UPSTREAM.read_text(encoding="utf-8"))
    description = registry["description"]

    assert "markdowndb" not in registry["pins"]
    assert "markdowndb" not in observations["observations"]
    assert not WORKFLOW.exists()
    assert description.startswith("Canonical inputs for current external-component qualification.")
    assert "This registry is not" in description
    assert "record of historical qualification runs" in description


def test_observed_result_preserves_exact_executed_provenance_and_rejection() -> None:
    observed = json.loads(OBSERVED.read_text(encoding="utf-8"))

    assert observed["execution_status"] == "executed_real_upstream_not_accepted_for_direct_index"
    assert observed["provider_acceptance"] == "not_accepted_for_direct_index"
    assert observed["decision_class"] == "C"
    assert observed["execution_record"]["harness_status"] == "success"

    raw = observed["raw_observations"]
    assert raw["scope"]["sentinel_path_in_scoped_db"] is False
    assert raw["scope"]["sentinel_path_in_whole_vault_db"] is True
    assert raw["obsidian_link_parser"]["missing_details_menuiseries_preserved_by_parser"] is True
    assert raw["sqlite_link_projection"]["missing_details_menuiseries_retained"] is False
    assert raw["sqlite_link_projection"]["existing_pdf_embed_link_retained"] is False
    assert raw["sqlite_link_projection"]["existing_png_embed_link_retained"] is False
    assert raw["sqlite_link_projection"]["existing_base_link_retained"] is False
    assert raw["sqlite_link_projection"]["existing_canvas_link_retained"] is False
    assert raw["sqlite_link_projection"]["existing_heading_anchor_link_retained"] is False
    assert raw["identity_and_digest"]["rename_changes_provider_id"] is True
    assert raw["identity_and_digest"]["same_path_byte_change_preserves_provider_id"] is True
    assert raw["reconstruction"]["delete_index_then_rebuild_same_structural_projection"] is True
    assert raw["write_check"]["changed"] is False

    decision = observed["qualification_decision"]
    assert decision["classification"] == "C"
    assert "bounded deterministic filesystem scan" in decision["accepted_patterns"]
    assert "MarkdownDB as the direct Pantheon workspace structural index implementation" in decision["not_accepted"]
    assert "runtime dependency adoption" in decision["not_accepted"]


def test_provider_neutral_pattern_remains_owned_by_existing_workspace_candidate() -> None:
    inspector = INSPECTOR.read_text(encoding="utf-8")
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))

    assert corpus["workspace"]["authorized_scope"]["include_prefixes"] == ["projects/maison/"]
    for invariant in (
        "one AFFAIRES indexer/sync daemon",
        "initial scan",
        "reconstructible technical index",
        "The index is technical cache/state only.",
        "Deleting it must cause a rebuild, not loss of professional knowledge.",
        "watcher   = responsiveness",
        "reconcile = convergence guarantee",
    ):
        assert invariant in inspector


def test_historical_result_preserves_non_equivalences_without_provider_authority() -> None:
    observed = json.loads(OBSERVED.read_text(encoding="utf-8"))

    for invariant in (
        "provider file id != governed identity",
        "raw tag != Tag Registry tag",
        "wikilink != governed relation",
        "Markdown task != WorkIssue",
        "caller-supplied scope != provider-owned authorization",
        "Q1 success != dependency adopted",
    ):
        assert invariant in observed["invariants"]

    assert "Do not build a Pantheon compatibility adapter solely to compensate" in observed["qualification_decision"]["next_action"]
