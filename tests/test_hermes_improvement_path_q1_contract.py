from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "hermes_improvement_path_q1.json"
DOC = ROOT / "docs" / "architecture" / "HERMES_IMPROVEMENT_PATH.md"


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_improvement_path_is_method_first_not_tool_first() -> None:
    fixture = _fixture()
    direction = fixture["direction"]

    assert fixture["schema_id"] == "pantheon.hermes_improvement_path_q1"
    assert fixture["revision"] == 2
    assert fixture["status"] == "candidate"
    assert fixture["live_executed"] is False

    assert direction["durable_owner"] == "hermes_evaluation_improvement_loop"
    assert direction["method"] == [
        "observe",
        "measure",
        "classify_failure_layer",
        "change_one_layer",
        "compare_on_held_out_cases",
        "human_review",
    ]
    assert direction["self_evolution_role"] == "optional_future_automation_candidate"
    assert direction["self_evolution_activation"] == "blocked_unresolved"


def test_weight_tuning_is_downstream_of_existing_failure_layers() -> None:
    fixture = _fixture()
    direction = fixture["direction"]

    assert direction["weight_tuning_gate"] == "residual_model_limitation_proven"
    assert direction["failure_layers_before_weight_tuning"] == [
        "skill",
        "prompt",
        "tool_contract",
        "context_admission_or_budget",
        "retrieval_or_provenance",
        "provider_binding_or_routing",
    ]

    text = _doc()
    assert "A model must not be trained to compensate for a defect owned elsewhere." in text


def test_llamafactory_is_one_training_facade_and_unsloth_is_optional_acceleration() -> None:
    fixture = _fixture()
    direction = fixture["direction"]
    upstream = fixture["observed_upstream"]
    text = _doc()

    assert direction["training_facade"] == "llamafactory"
    assert direction["unsloth_role"] == "optional_llama_lora_accelerator"
    assert upstream["llamafactory_unsloth_integration"] == "use_unsloth"
    assert "use_unsloth: true" in text
    assert "Unsloth independent training facade = not selected" in text
    assert "Unsloth permanent serving role = not selected" in text


def test_existing_serving_path_remains_the_only_selected_direction() -> None:
    fixture = _fixture()
    direction = fixture["direction"]
    text = _doc()

    assert direction["serving_path"] == [
        "hermes",
        "pair",
        "ollama_or_lm_studio",
        "gpu_node",
    ]
    assert "No second agent runtime, scheduler, provider router, evaluation service or model-serving path is added." in text
    assert "PAIR routes one request to an eligible node" in text


def test_evaluation_reuses_existing_contracts_instead_of_adding_a_runtime() -> None:
    fixture = _fixture()
    posture = fixture["evaluation_posture"]
    categories = set(posture["candidate_case_categories"])

    assert posture["new_evaluation_runtime"] is False
    assert posture["reuse_existing_tests_and_qualification_labs"] is True
    assert {
        "structured_tool_calling",
        "scope_isolation",
        "refusal_and_approval_boundaries",
        "context_admission_untrusted_content",
        "pdf_document_understanding",
        "provenance",
        "retrieval",
        "memory_evidence_boundaries",
        "provider_fallback",
    }.issubset(categories)
    assert posture["evaluation_set_is_evidence"] is False
    assert posture["benchmark_corpus_is_training_data"] is False


def test_pair_hardware_observation_precedes_training_work() -> None:
    fixture = _fixture()
    priority = fixture["priority"]
    text = _doc()

    assert priority[0] == "execute_existing_pair_q1a_q1b_q1c"
    assert priority[-1] == "qualify_llamafactory_only_if_model_gap_remains"
    assert "Q1A -> Linux RTX 4080 isolated PAIR + Ollama observation" in text
    assert "Q1B -> Linux RTX 4080 + Windows RTX 4090 routing / failover / rejoin" in text
    assert "Q1C -> current Hermes container -> local PAIR ingress compatibility" in text


def test_training_data_and_authority_boundaries_remain_closed() -> None:
    fixture = _fixture()

    assert fixture["training_posture"] == {
        "project_client_data_training_default": False,
        "synthetic_or_explicitly_authorized_data_default": True,
        "llamafactory_required_dependency": False,
        "unsloth_required_dependency": False,
        "self_evolution_required_dependency": False,
    }

    assert fixture["authority"] == {
        "deployment_selected": False,
        "installed": False,
        "runtime_activated": False,
        "training_authorized": False,
        "task_authorized": False,
        "evidence_admitted": False,
        "new_scheduler_authority": False,
        "new_router_authority": False,
        "new_runtime_owner": False,
        "new_dataset_authority": False,
    }


def test_non_equivalences_cover_evaluation_training_serving_and_evidence() -> None:
    rules = set(_fixture()["non_equivalences"])

    assert "optimizer score gain != reviewed skill improvement" in rules
    assert "evaluation score != professional correctness" in rules
    assert "benchmark corpus != training dataset" in rules
    assert "training completed != model qualified" in rules
    assert "model qualified != model activated" in rules
    assert "model activated != task authorized" in rules
    assert "dataset != Evidence" in rules
    assert "runtime trace != Evidence" in rules
    assert "project data available != training authorized" in rules
    assert "Unsloth acceleration enabled != trained model qualified" in rules
    assert "PAIR routing != Pantheon authorization" in rules
