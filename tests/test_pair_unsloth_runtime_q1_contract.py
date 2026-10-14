from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "pair_unsloth_runtime_q1.json"
PINS = ROOT / "implementation" / "qualification" / "external-pins.json"
RUNBOOK = ROOT / "docs" / "governance" / "PAIR_UNSLOTH_RUNTIME_Q1_RUNBOOK.md"


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _pins() -> dict:
    return json.loads(PINS.read_text(encoding="utf-8"))["pins"]


def _runbook() -> str:
    return RUNBOOK.read_text(encoding="utf-8")


def test_q1_targets_existing_external_pin_authority() -> None:
    fixture = _fixture()
    pins = _pins()

    assert fixture["schema_id"] == "pantheon.pair_unsloth_runtime_qualification_q1"
    assert fixture["revision"] == 2
    assert fixture["status"] == "candidate"
    assert fixture["live_executed"] is False

    assert fixture["target_pins"] == {
        "pair": "personal-ai-router",
        "unsloth": "unsloth",
        "hermes": "hermes-agent",
    }
    for pin_id in fixture["target_pins"].values():
        assert pin_id in pins


def test_q1_is_a_staged_lab_not_a_runtime_claim() -> None:
    fixture = _fixture()
    stages = fixture["stages"]

    assert [stage["stage_id"] for stage in stages] == [
        "q1a_pair_linux_isolated",
        "q1b_pair_linux_windows_cluster",
        "q1c_hermes_container_to_pair",
        "q1d_unsloth_as_existing_hermes_custom_provider",
        "q1e_classification",
    ]
    assert all(stage["result"] == "not_run" for stage in stages)

    assert fixture["authority"] == {
        "deployment_selected": False,
        "installed": False,
        "runtime_qualified": False,
        "runtime_activated": False,
        "task_authorized": False,
        "evidence_admitted": False,
        "new_scheduler_authority": False,
        "new_router_authority": False,
        "new_runtime_owner": False,
    }


def test_q1_runbook_is_bound_to_the_fixture_and_existing_pin_exporter() -> None:
    fixture = _fixture()
    text = _runbook()

    assert fixture["runbook"]["path"] == RUNBOOK.relative_to(ROOT).as_posix()
    assert RUNBOOK.is_file()
    assert "export_external_qualification_pins.py" in text
    assert "personal-ai-router unsloth hermes-agent" in text
    assert fixture["runbook"]["secrets_persisted_in_artifacts"] is False
    assert fixture["runbook"]["production_compose_mutation_allowed"] is False


def test_q1_runbook_matches_the_bounded_lab_topology() -> None:
    fixture = _fixture()
    text = _runbook()
    inputs = fixture["lab_inputs"]

    assert fixture["runbook"]["linux_pair_surface"] == "nvpair_tui_isolated_home"
    assert fixture["runbook"]["windows_pair_surface"] == "desktop_jobs_observation"
    assert "nvpair-tui" in text
    assert "Ran on" in text

    assert inputs["pair_model"] in text
    assert inputs["unsloth_model"] in text
    assert str(inputs["unsloth_context_tokens"]) in text
    assert str(inputs["unsloth_api_port"]) in text
    assert inputs["hermes_temporary_profile"] in text
    assert inputs["unsloth_bind_scope"] == "docker_bridge_gateway_scoped"


def test_pair_lab_preserves_physical_routing_ceiling_and_rollback() -> None:
    fixture = _fixture()
    by_id = {stage["stage_id"]: stage for stage in fixture["stages"]}

    linux_checks = set(by_id["q1a_pair_linux_isolated"]["required_checks"])
    assert "pair_uninstall_keeps_model_weights" in linux_checks
    assert "pantheon_ollama_store_unchanged_after_rollback" in linux_checks

    cluster_checks = set(by_id["q1b_pair_linux_windows_cluster"]["required_checks"])
    assert "discovery_vs_direct_ip_pairing_distinguished" in cluster_checks
    assert "no_cross_machine_vram_pooling_claim" in cluster_checks
    assert "served_node_is_observable" in cluster_checks

    classification_checks = set(by_id["q1e_classification"]["required_checks"])
    assert "no_runtime_activation" in classification_checks
    assert "no_task_authorization" in classification_checks
    assert "no_evidence_admission" in classification_checks


def test_container_loopback_question_must_be_observed_not_assumed() -> None:
    fixture = _fixture()
    stage = next(
        item for item in fixture["stages"] if item["stage_id"] == "q1c_hermes_container_to_pair"
    )
    checks = set(stage["required_checks"])
    text = _runbook()

    assert "current_compose_path_used_without_network_workaround" in checks
    assert "http_status_and_pair_error_recorded" in checks
    assert "no_403_assumed_before_execution" in checks
    assert "no_relay_or_host_network_change_in_q1" in checks
    assert "compose_hash_unchanged" in checks
    assert "host.docker.internal:11434" in text
    assert "Do not add `network_mode: host`" in text
    assert "Do not pre-record `403`" in text


def test_unsloth_is_isolated_and_uses_a_fresh_temporary_hermes_profile() -> None:
    fixture = _fixture()
    stage = next(
        item
        for item in fixture["stages"]
        if item["stage_id"] == "q1d_unsloth_as_existing_hermes_custom_provider"
    )
    checks = set(stage["required_checks"])
    text = _runbook()

    assert "unsloth_runtime_and_cache_isolated" in checks
    assert "runtime_dependency_closure_captured" in checks
    assert "docker_bridge_scoped_bind" in checks
    assert "existing_hermes_custom_provider_configuration" in checks
    assert "fresh_temporary_hermes_profile" in checks
    assert "no_unsloth_start_hermes_path" in checks
    assert "structured_tool_call" in checks
    assert "tool_call_round_trip" in checks
    assert "no_silent_provider_fallback" in checks
    assert "pantheon_governed_profile_not_mutated" in checks
    assert "temporary_profile_and_server_rollback" in checks

    assert "UNSLOTH_STUDIO_HOME" in text
    assert "HF_HOME" in text
    assert "docker network inspect bridge" in text
    assert "hermes profile create pantheon-q1-unsloth --no-skills" in text
    assert "Do not clone `pantheon-governed`" in text
    assert "Do not use Hermes `--yolo`" in text
    assert "runtime dependency closure" in text
    assert "importlib.metadata" in text
    assert "torch.version.cuda" in text
    assert "llama-server" in text
    assert "bridge-scoped" in text


def test_q1_observation_rows_are_structured_before_classification() -> None:
    fixture = _fixture()

    assert fixture["observation_record_fields"] == [
        "check_id",
        "stage_id",
        "host",
        "command_or_action",
        "expected_observation",
        "actual_observation",
        "status",
        "artifact_ref",
        "started_at",
        "ended_at",
        "notes",
    ]

    classification = next(
        item for item in fixture["stages"] if item["stage_id"] == "q1e_classification"
    )
    assert "all_required_checks_have_observation_rows" in classification["required_checks"]


def test_q1_keeps_governance_non_equivalences_explicit() -> None:
    fixture = _fixture()
    rules = set(fixture["non_equivalences"])

    assert "runtime_success != task_authorization" in rules
    assert "runtime_success != Evidence" in rules
    assert "PAIR routing != Pantheon authorization" in rules
    assert "PAIR model availability != model approval" in rules
    assert "Unsloth provider configured != provider authorized" in rules
    assert "container connectivity != runtime qualification" in rules
