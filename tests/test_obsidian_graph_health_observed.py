"""Regression checks for the executed Obsidian graph/health qualification result."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREPARED = ROOT / "tests" / "fixtures" / "obsidian_graph_health_pilot.json"
OBSERVED = ROOT / "tests" / "fixtures" / "obsidian_graph_health_observed_v2026.08.6.json"
PIN_REGISTRY = ROOT / "implementation" / "qualification" / "external-pins.json"


def _observed() -> dict:
    return json.loads(OBSERVED.read_text(encoding="utf-8"))


def _provider_pin() -> dict:
    registry = json.loads(PIN_REGISTRY.read_text(encoding="utf-8"))
    return registry["pins"]["obsidian-wiki"]


def _numeric_version(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.removeprefix("v").split("."))


def test_observed_graph_health_result_stays_separate_from_prepared_expectations() -> None:
    prepared = json.loads(PREPARED.read_text(encoding="utf-8"))
    observed = _observed()

    assert prepared["execution_status"] == "prepared_not_executed"
    assert "observed_results" not in prepared
    assert observed["execution_status"] == "executed_real_upstream_not_accepted"
    assert observed["provider_acceptance"] == "not_accepted"
    assert observed["pilot_id"] == prepared["pilot_id"]


def test_observed_result_is_pinned_to_exact_real_upstream_execution() -> None:
    observed = _observed()
    provider = observed["provider"]
    record = observed["execution_record"]
    pin = _provider_pin()

    assert pin["repository"] == provider["repository"]
    assert _numeric_version(provider["stable_release"]) == _numeric_version(pin["version"])
    assert provider["stable_release_sha"] == pin["ref"]
    assert provider["current_main_observed_sha"] == "37596cffeef43faecd9b61246b0b119b11a87bc4"
    assert provider["source_blobs"] == {
        "graph_analysis.py": "9e2ff9be961f4149aa09d490e10089fb1d700c69",
        "lint.py": "09a2b8207e02296455fd4d9a9401e6aa1fbdd66d",
    }
    assert provider["current_main_uses_same_deterministic_blobs"] is True
    assert record["workflow_run_id"] == 33331529533
    assert record["artifact_id"] == 9737779875
    assert record["artifact_sha256"] == "1dabfa025b443970a97743bba53a954206afeddfb50ea641ef1def04c8253f97"
    assert record["harness_status"] == "success"
    assert "real obsidian_wiki graph-analyse CLI" in observed["execution_scope"]["included"]


def test_real_upstream_result_keeps_graph_failures_visible() -> None:
    observed = _observed()
    cases = observed["case_results"]
    raw = observed["raw_observations"]

    assert cases["bookkeeping_not_hub"]["status"] == "pass"
    assert cases["raw_staging_excluded"]["status"] == "pass"
    assert cases["bounded_shortest_path"]["status"] == "fail"
    assert raw["shortest_programme_cctp"] is None
    assert cases["isolated_question"]["status"] == "fail"
    assert raw["scoped_graph"]["pages"] == 7
    assert raw["scoped_graph"]["edges"] == 2
    assert set(raw["scoped_graph"]["isolated"]) == {
        "chauffage-notes",
        "chauffage",
        "decisions",
        "programme",
        "question-ouverte",
    }


def test_real_upstream_lint_result_keeps_false_positives_and_schema_noise_visible() -> None:
    observed = _observed()
    cases = observed["case_results"]
    lint = observed["raw_observations"]["scoped_lint"]

    assert lint["exit_code"] == 1
    assert lint["status"] == "fail"
    assert lint["broken_link_count"] == 15
    assert lint["orphan_count"] == 5
    assert lint["confidence_missing_fields_count"] == 7
    assert lint["confidence_ledger_error_count"] == 1
    assert lint["provider_schema_noise"]["required_trust_fields"] == ["base_confidence", "lifecycle"]
    assert lint["provider_schema_noise"]["ledger_missing"] is True

    assert cases["broken_menuiseries_link"]["status"] == "partial"
    valid_links = cases["valid_obsidian_links_not_broken"]
    assert valid_links["status"] == "fail"
    assert set(valid_links["false_positive_targets"]) == {
        "cctp.md",
        "chauffage.md",
        "plan.pdf",
        "perspective.png",
        "planning.base",
        "schema.canvas",
        "chauffage\\",
    }


def test_scope_is_caller_enforced_not_provider_owned() -> None:
    observed = _observed()
    scope = observed["case_results"]["bounded_scope"]
    negative = observed["raw_observations"]["whole_vault_negative_control"]

    assert scope["status"] == "conditional_pass"
    assert scope["native_scope_parameter"] is False
    assert scope["sentinel_in_scoped_graph"] is False
    assert scope["sentinel_in_full_vault_graph"] is True
    assert negative["sentinel_present"] is True
    assert "caller-supplied root" in scope["reason"]


def test_semantic_capabilities_remain_not_demonstrated() -> None:
    cases = _observed()["case_results"]

    assert cases["heating_duplicate_candidate"]["status"] == "not_demonstrated"
    assert cases["heating_contradiction_candidate"]["status"] == "not_demonstrated"


def test_observed_result_preserves_read_only_and_governance_boundaries() -> None:
    observed = _observed()

    assert observed["case_results"]["protected_material_no_mutation"]["status"] == "pass"
    assert observed["raw_observations"]["write_check"] == {
        "tracked_file_count": 16,
        "changed": False,
        "added_removed_or_modified": [],
    }
    assert "provider-wide adoption" in observed["qualification_decision"]["not_accepted_now"]
    assert observed["qualification_decision"]["next_action"].startswith("Keep obsidian-wiki unbound")

    for invariant in (
        "observed result != provider-wide truth",
        "partial capability pass != provider adoption",
        "read-only success != authorization",
        "graph relation != Evidence",
        "health finding != defect confirmed",
        "provider output != governed Knowledge",
        "caller-supplied scope != provider-owned authorization",
    ):
        assert invariant in observed["invariants"]
