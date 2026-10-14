import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "tests/fixtures/hermes_request_intake_evaluation_pilot.json"
CORPUS = ROOT / "tests/fixtures/hermes_request_intake_cases.yaml"
SKILL = ROOT / "templates/hermes/skills/pantheon-request-intake/SKILL.md"
RUNTIME_REVIEW = ROOT / "docs/governance/HERMES_RUNTIME_SURFACE_REVIEW.md"
EXTERNAL_PINS = ROOT / "implementation/qualification/external-pins.json"


def _pilot() -> dict:
    return json.loads(PILOT.read_text(encoding="utf-8"))


def _hermes_pin() -> dict:
    registry = json.loads(EXTERNAL_PINS.read_text(encoding="utf-8"))
    return registry["pins"]["hermes-agent"]


def test_runtime_pilot_reuses_exact_merged_skill_and_existing_corpus() -> None:
    pilot = _pilot()
    hermes_pin = _hermes_pin()

    assert pilot["pilot_id"] == "hermes-request-intake-runtime-eval-001"
    assert pilot["capability"] == "pantheon_request_intake"
    assert pilot["execution_status"] == "blocked_missing_observed_runtime"

    target = pilot["runtime_target"]
    assert target["runtime_id"] == "nousresearch-hermes-agent"
    assert target["version"] == hermes_pin["version"]
    assert target["release_commit"] == hermes_pin["ref"]
    assert target["required_profile"] == "pantheon-governed"
    assert target["must_observe_exact_installed_artifact"] is True

    snapshot = pilot["instruction_variant"]
    assert snapshot["commit"] == "5ee6b614b910da5ac6b323b01102a4c5e76df390"
    assert snapshot["path"] == "templates/hermes/skills/pantheon-request-intake/SKILL.md"
    assert snapshot["blob_sha"] == "d5d21b5afca5dfb4197652b50e7d121fcec8fee9"
    assert SKILL.is_file()

    corpus_ref = pilot["case_corpus"]
    assert corpus_ref["path"] == "tests/fixtures/hermes_request_intake_cases.yaml"
    corpus = yaml.safe_load(CORPUS.read_text(encoding="utf-8"))["cases"]
    assert len(corpus) >= corpus_ref["minimum_cases"]
    assert len({case["id"] for case in corpus}) == len(corpus)

    runtime_review = RUNTIME_REVIEW.read_text(encoding="utf-8")
    assert f"Current reviewed target: Hermes Agent {hermes_pin['version']}" in runtime_review
    assert "real_instance_observation_required: true" in runtime_review


def test_runtime_pilot_measures_over_and_under_governance_separately() -> None:
    pilot = _pilot()
    measures = set(pilot["measures"])

    assert {
        "condition_true_positives",
        "condition_false_positives",
        "condition_false_negatives",
        "condition_precision",
        "condition_recall",
        "harmless_escalation_errors",
        "missed_external_effect_conditions",
        "missed_memory_promotion_conditions",
        "unsupported_risk_escalations",
        "out_of_vocabulary_conditions",
        "kvc_or_disposition_leakage_from_hermes",
    } <= measures

    acceptance = pilot["acceptance_logic"]
    assert acceptance["human_review_required"] is True
    assert acceptance["automatic_acceptance"] is False
    hard_failures = "\n".join(acceptance["hard_failures"])
    assert "missed requested external transmission/effect condition" in hard_failures
    assert "missed requested memory promotion condition" in hard_failures
    assert "Hermes emits K/V/C as its own authority" in hard_failures


def test_runtime_pilot_does_not_fake_live_qualification() -> None:
    pilot = _pilot()
    hermes_pin = _hermes_pin()
    blocker = pilot["execution_blocker"]

    assert f"exact observed Hermes {hermes_pin['version']} runtime/profile" in blocker["missing_prerequisite"]
    assert "cannot establish whether a live language model infers" in blocker["why_repo_tests_are_insufficient"]
    assert "green CI" in blocker["forbidden_shortcut"]
    assert "deterministic fake provider" in blocker["forbidden_shortcut"]

    observation = pilot["required_runtime_observation"]
    assert observation["record_exact_runtime_version"] is True
    assert observation["record_runtime_artifact_digest"] is True
    assert observation["record_model_identity"] is True
    assert observation["record_skill_snapshot"] is True
    assert observation["preserve_case_isolation"] is True
    assert observation["forbid_prior_session_reuse"] is True

    assert "observed_results" not in pilot
    assert "qualified" not in pilot
    assert "quality_score" not in pilot
