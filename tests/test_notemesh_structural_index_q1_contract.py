"""Static contract for the qualification-only NoteMesh structural-index Q1."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "notemesh-structural-index-q1.yml"
REGISTRY = ROOT / "implementation" / "qualification" / "external-pins.json"
UPSTREAM = ROOT / "implementation" / "qualification" / "external-upstream-observations.json"
CORPUS = ROOT / "tests" / "fixtures" / "obsidian_graph_health_pilot.json"
OBSERVED = next((ROOT / "tests" / "fixtures").glob("notemesh_structural_index_observed_v*.json"))


def test_notemesh_is_current_qualification_input_without_duplicate_pin_literals() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    pin = registry["pins"]["notemesh"]

    assert pin["kind"] == "git"
    assert pin["env_prefix"] == "NOTEMESH"
    assert pin["repository"] == "ChangeNode/notemesh"
    assert pin["version"]
    assert len(pin["ref"]) == 40

    for claim in (
        "not deployment truth",
        "installation state",
        "authorization",
        "Evidence",
    ):
        assert claim in registry["description"]


def test_notemesh_pin_has_honest_separate_upstream_observation() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    pin = registry["pins"]["notemesh"]
    observations = json.loads(UPSTREAM.read_text(encoding="utf-8"))
    record = observations["observations"]["notemesh"]

    assert record["source"] == "not_observable"
    assert record["locator"] == pin["repository"]
    assert record["latest_seen"] == pin["ref"]
    assert record["delta"] == "none"
    assert "no supported release feed" in record["note"]
    assert "does not install, activate, authorize or adopt NoteMesh" in record["note"]


def test_q1_reuses_existing_bounded_corpus() -> None:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert corpus["workspace"]["authorized_scope"]["include_prefixes"] == ["projects/maison/"]
    assert corpus["workspace"]["authorized_scope"]["explicitly_out_of_scope_prefixes"] == ["projects/autre-projet/"]
    assert "valid_obsidian_link_false_positives" in corpus["measures"]
    assert "obsidian_graph_health_pilot.json" in workflow
    assert "projects/autre-projet/sentinel-hors-perimetre.md" in workflow
    assert "_raw/hypothese-non-verifiee.md" in workflow
    assert "sources/cctp-original.pdf" in workflow
    assert "evidence/admitted-cctp-record" in workflow


def test_q1_executes_real_upstream_indexer_not_a_reimplementation() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for invariant in (
        "pnpm --dir notemesh install --frozen-lockfile",
        'import { db } from "../src/server/db";',
        'import { indexer, parseNote } from "../src/server/vault/indexer";',
        "await indexer().rebuild();",
        'SELECT source_path, target, resolved_path FROM links',
        "parsed_valid_links",
        "unresolved_links",
    ):
        assert invariant in workflow


def test_q1_classifies_resolution_for_every_unique_normalized_valid_target() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for marker in (
        "expectedResolvedTargets",
        "expected_targets_all_present",
        "expected_targets_all_resolved",
        "normalized_cctp_parser_forms",
        "normalized_cctp_sql_rows",
        "escaped_alias_false_positive",
        "valid_obsidian_link_false_positives",
        "normalized_valid_targets_resolved",
        "normalized_cctp_forms_collapsed",
    ):
        assert marker in workflow

    for target in (
        "projects/maison/cctp.md",
        "projects/maison/chauffage.md",
        "plan.pdf",
        "perspective.png",
        "planning.base",
        "schema.canvas",
        "cctp.md",
    ):
        assert target in workflow

    assert 'expect(parsedValid.links).toHaveLength(10)' in workflow
    assert 'expect(validLinkResolution.normalized_cctp_sql_rows).toBe(1)' in workflow
    assert 'expect(resolvedByTarget.get("chauffage\\\\")).toBeNull()' in workflow
    assert 'result["measures"]["valid_obsidian_link_false_positives"] == 1' in workflow


def test_q1_keeps_sync_and_write_surfaces_disabled() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "indexer().start()" not in workflow
    assert "ensureIndexerStarted" not in workflow
    assert "notifyLocalChange" not in workflow
    assert "create_note" not in workflow
    assert "update_note" not in workflow
    assert "delete_note" not in workflow
    assert "vault:write" not in workflow
    assert "no sync backend activated" in workflow
    assert "no MCP write tool activated" in workflow


def test_q1_makes_scope_leakage_and_report_only_boundary_observable() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    for observation in (
        "sentinel_indexed",
        "raw_indexed",
        "bookkeeping_indexed",
        "source_indexed",
        "evidence_indexed",
        "escaped_alias_false_positive_observed",
        "true_missing_link_observed",
        "destructive_write_attempts",
        "authority_promotion_errors",
    ):
        assert observation in workflow

    assert "provider execution success is not authorization" in workflow
    assert "Evidence admission" in workflow
    assert "governed identity" in workflow
    assert "deployment adoption" in workflow


def test_q1_preserves_diagnostics_on_failed_provider_assertions() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    upload = workflow[workflow.index("- name: Upload qualification artifact") :]

    assert "if: always()" in upload
    assert "actions/upload-artifact@v4" in upload
    assert "if-no-files-found: error" in upload


def test_q1_verifies_no_workspace_mutation() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "before.json" in workflow
    assert "mutation_check" in workflow
    assert 'result["measures"]["destructive_write_attempts"] == 0' in workflow


def test_committed_observation_records_execution_without_adoption() -> None:
    observed = json.loads(OBSERVED.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    pin = registry["pins"]["notemesh"]

    assert observed["status"] == "observed_candidate_not_adopted"
    assert observed["candidate"] == {
        "repository": pin["repository"],
        "version": pin["version"],
        "ref": pin["ref"],
    }
    assert observed["execution"]["kind"] == "real_upstream_runtime"
    assert observed["qualification"]["class"] == "B"
    assert observed["qualification"]["decision"] == "qualify_further"
    assert observed["observations"]["true_missing_link_observed"] is True
    assert observed["observations"]["escaped_alias_false_positive_observed"] is True
    assert observed["observations"]["attachment_aware_resolution_observed"] is True
    assert observed["observations"]["unresolved_links_retained_in_projection"] is True

    link_resolution = observed["observations"]["valid_obsidian_link_resolution"]
    assert link_resolution["parser_valid_form_count"] == 10
    assert link_resolution["normalized_cctp_parser_forms"] == 2
    assert link_resolution["normalized_cctp_sql_rows"] == 1
    assert link_resolution["valid_obsidian_link_false_positives"] == 1
    assert link_resolution["known_false_unresolved_targets"] == ["chauffage\\"]
    assert len(link_resolution["resolved_unique_targets"]) == 8

    assert all(observed["observations"]["whole_vault_negative_control"].values())
    assert observed["observations"]["workspace_mutation"] == {
        "added": [],
        "changed": [],
        "removed": [],
    }
    assert observed["governance"] == {
        "retrieved_or_indexed_is_truth": False,
        "workspace_note_is_evidence": False,
        "provider_path_is_governed_identity": False,
        "provider_visibility_is_task_authorization": False,
        "projection_is_persistence": False,
        "successful_execution_is_adoption": False,
    }
