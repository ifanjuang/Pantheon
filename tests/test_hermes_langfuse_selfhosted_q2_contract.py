from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/hermes-langfuse-selfhosted-q2.yml"
PROBE = ROOT / "implementation/tools/run_hermes_langfuse_selfhosted_q2.py"


def test_q2_uses_exact_upstreams_and_official_v4_compose():
    text = WORKFLOW.read_text()
    assert "4c1f53be10d0fce1d25aee1975e5149b6c54f25a" in text
    assert "c2257f7d86b4407a2b27e8d3a95f719736ef4b01" in text
    assert "langfuse/langfuse" in text
    assert "docker-compose.yml up -d" in text
    assert "TELEMETRY_ENABLED: \"false\"" in text


def test_q2_is_metadata_only_and_synthetic():
    workflow = WORKFLOW.read_text()
    probe = PROBE.read_text()
    assert "HERMES_LANGFUSE_CAPTURE: metadata" in workflow
    assert 'os.environ["HERMES_LANGFUSE_CAPTURE"] = "metadata"' in probe
    assert "PANTHEON_Q2_PROMPT_MUST_NOT_BE_STORED" in probe
    assert "PANTHEON_Q2_TOOL_ARG_MUST_NOT_BE_STORED" in probe
    assert "PANTHEON_Q2_TOOL_RESULT_MUST_NOT_BE_STORED" in probe
    assert "marker not in serialized" in probe


def test_q2_preserves_pantheon_authority_boundaries():
    probe = PROBE.read_text()
    assert '"langfuse_is_authority": False' in probe
    assert '"evidence_admitted": False' in probe
    assert '"pantheon_state_mutated": False' in probe
    assert "Hindsight" not in probe
    assert "CouchDB" not in probe
