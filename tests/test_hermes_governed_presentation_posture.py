from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE_CONSTITUTION = ROOT / "hermes/profiles/PROFILE_CONSTITUTION.md"
RUNBOOK = ROOT / "docs/install/HERMES_EXECUTION_BRIDGE_RUNBOOK.md"


def test_governed_profile_forbids_private_reasoning_projection() -> None:
    text = PROFILE_CONSTITUTION.read_text(encoding="utf-8")

    assert "private_reasoning_projection: forbidden" in text
    assert "reasoning_stream_to_user_surface: forbidden" in text
    assert "commentary_projection: preferred_when_supported" in text
    assert "interim_progress_projection: preferred_when_supported" in text
    assert "private reasoning != user-visible activity" in text


def test_presentation_qualification_depends_on_observed_behavior_not_nominal_config() -> None:
    constitution = PROFILE_CONSTITUTION.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")

    assert "show_reasoning false != private reasoning proven hidden" in constitution
    assert "observed reasoning disclosure -> not_qualified regardless of nominal config" in constitution
    assert "configured reasoning hidden != observed reasoning hidden" in runbook
    assert "The current observer does not inspect Hermes display configuration" in runbook
    assert "runtime safety_status qualified != presentation posture observed" in runbook


def test_runbook_recommends_hidden_reasoning_without_making_commentary_a_safety_gate() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    assert "config set display.show_reasoning false" in text
    assert "config set plugins.stream_reasoning_deltas false" in text
    assert "config set display.show_commentary true" in text
    assert "config set display.interim_assistant_messages true" in text
    assert "commentary unavailable -> presentation degraded, not automatically unsafe" in text
    assert "interim messages unavailable -> presentation degraded, not automatically unsafe" in text


def test_runbook_requires_surface_behavior_check_and_minimal_incident_retention() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    assert "no private scratchpad shown" in text
    assert "no chain-of-thought / reasoning block shown" in text
    assert "no reasoning delta streamed to the user-visible surface" in text
    assert 'no "💭 Reasoning" block or equivalent private-reasoning projection' in text
    assert "Do not retain private reasoning content merely to prove that it leaked" in text
    assert "private reasoning absent from each admitted governed user-visible surface" in text
    assert "reasoning deltas not projected to each admitted governed user-visible surface" in text


def test_reasoning_posture_does_not_create_new_authority_or_task_authorization() -> None:
    constitution = PROFILE_CONSTITUTION.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")

    assert "presentation observation != task authorization" in runbook
    assert "Private reasoning stays private; safe observable commentary may be projected." in constitution
    assert "None creates authority." in constitution
