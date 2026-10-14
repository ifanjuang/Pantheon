from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = ROOT / "templates/langfuse-hermes"
README = SUPPORT / "README.md"
RUNBOOK = ROOT / "operations/langfuse-hermes-first-test-runbook.md"


def test_pantheon_does_not_own_langfuse_server_compose_or_env():
    assert not (SUPPORT / "docker-compose.langfuse.example.yml").exists()
    assert not (SUPPORT / "langfuse.env.example").exists()


def test_bundled_hermes_plugin_is_the_selected_instrumentation_path():
    text = README.read_text()
    assert "observability/langfuse" in text
    assert "HERMES_LANGFUSE_CAPTURE=metadata" in text
    assert "Pantheon does not maintain a Langfuse server stack" in text
    assert "official upstream Docker Compose" in text


def test_runbook_uses_v4_observations_and_rejects_legacy_trace_readback():
    text = RUNBOOK.read_text()
    assert "/api/public/v2/observations" in text
    assert "legacy `/api/public/traces`" in text
    assert "Do not copy a Pantheon-owned Langfuse compose" in text


def test_observability_remains_non_authoritative():
    text = README.read_text() + "\n" + RUNBOOK.read_text()
    assert "A Langfuse trace is not an Evidence Pack" in text
    assert "Langfuse observes." in text
    assert "Pantheon governs." in text
