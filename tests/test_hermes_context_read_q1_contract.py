from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "implementation-hermes-context-read-q1.yml"
TOOL = ROOT / "implementation" / "tools" / "run_hermes_context_read_q1.py"
PINS = ROOT / "implementation" / "qualification" / "external-pins.json"
SKILLS = ROOT / "templates" / "hermes" / "SKILLS.md"


def test_q1_reuses_canonical_hermes_pin() -> None:
    pins = json.loads(PINS.read_text(encoding="utf-8"))
    hermes = pins["pins"]["hermes-agent"]
    assert {"repository", "version", "ref", "env_prefix"} <= hermes.keys()
    assert all(hermes[field] for field in ("repository", "version", "ref", "env_prefix"))

    raw = WORKFLOW.read_text(encoding="utf-8")
    assert "export_external_qualification_pins.py" in raw
    assert "repository: ${{ env.HERMES_REPOSITORY }}" in raw
    assert "ref: ${{ env.HERMES_REF }}" in raw
    assert 'git -C "$GITHUB_WORKSPACE/hermes-upstream" rev-parse HEAD' in raw
    assert '"$HERMES_RELEASE_COMMIT"' in raw


def test_q1_executes_offline_prompt_and_real_prompt_builder() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    tool = TOOL.read_text(encoding="utf-8")

    assert "hermes\" prompt-size --platform cli --json" in workflow
    assert "agent.prompt_builder" in tool
    assert "build_context_files_prompt" in tool
    assert "CONTEXT_FILE_MAX_CHARS" in tool
    assert "_get_context_file_max_chars" in tool

    for marker in (
        "Q1_PRIORITY_HERMES",
        "Q1_AGENTS_ROOT",
        "Q1_AGENTS_NESTED",
        "Q1_CLAUDE_CWD",
        "Q1_UNRECOGNIZED_README",
        "Q1_COMPLETE_EOF",
        "Q1_TRUNCATION_HEAD",
        "Q1_TRUNCATION_MIDDLE",
        "Q1_TRUNCATION_TAIL",
    ):
        assert marker in tool


def test_q1_keeps_repository_ratchet_distinct_from_runtime_observation() -> None:
    skills = SKILLS.read_text(encoding="utf-8")
    tool = TOOL.read_text(encoding="utf-8")

    assert "the ceiling is a regression ratchet, not a Hermes token limit" in skills
    assert "must qualify the real set separately" in skills
    assert "repository size check != deployed runtime observation" in skills

    assert '"repository_orientation_surface_is_runtime_manifest": False' in tool
    assert '"over_cap_context_is_complete_read": False' in tool
    assert '"below_cap_eof_sentinel_proves_only_this_synthetic_read": True' in tool


def test_q1_has_no_authority_side_effects() -> None:
    tool = TOOL.read_text(encoding="utf-8")
    for boundary in (
        '"target_installation_observed": False',
        '"production_activated": False',
        '"future_tasks_authorized": False',
        '"evidence_admitted": False',
        '"pantheon_state_mutated": False',
        '"authority_effect": "none"',
    ):
        assert boundary in tool

    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "permissions:\n  contents: read" in workflow
    assert "workflow_dispatch:" in workflow
    assert "upload-artifact@v4" in workflow
