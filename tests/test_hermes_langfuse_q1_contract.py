from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "hermes-langfuse-q1.yml"
PROBE = ROOT / "implementation" / "tools" / "run_hermes_langfuse_q1.py"


def test_langfuse_q1_workflow_is_pinned_and_bounded():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "4c1f53be10d0fce1d25aee1975e5149b6c54f25a" in text
    assert "4454fd5788969def17516a21cd8f9242216a95f9" in text
    assert "tests/plugins/test_langfuse_plugin.py" in text
    assert "implementation/tools/run_hermes_langfuse_q1.py" in text


def test_langfuse_q1_defaults_to_metadata_and_preserves_authority_boundary():
    text = PROBE.read_text(encoding="utf-8")
    assert 'HERMES_LANGFUSE_CAPTURE"] = "metadata"' in text
    assert '"content_exported": False' in text
    assert '"langfuse_is_authority": False' in text
    assert '"evidence_admitted": False' in text
    assert '"pantheon_state_mutated": False' in text
    assert "sync_retain" not in text
    assert "CouchDB" not in text
