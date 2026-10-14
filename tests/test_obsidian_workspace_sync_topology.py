from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "docs" / "governance" / "OBSIDIAN_HINDSIGHT_WORKSPACE_MODEL.md"


def _model() -> str:
    return MODEL.read_text(encoding="utf-8")


def test_active_workspace_model_uses_headless_daemon_mirror_topology() -> None:
    raw = _model()
    assert "one long-running Self-hosted LiveSync CLI daemon" in raw
    assert "dedicated local LiveSync DB" in raw
    assert "dedicated filesystem vault mirror" in raw
    assert "repeated one-shot `sync` + `mirror` composition was explicitly rejected" in raw


def test_obsidian_web_is_optional_ui_not_sync_infrastructure() -> None:
    raw = _model()
    assert "Obsidian Web/Docker is not part of the synchronization or ingestion chain" in raw
    assert "Obsidian Web remains optional UI only" in raw
    assert "optional Obsidian Web/Docker client\n           for browser / always-available access" not in raw
    assert "native Obsidian + future Self-hosted LiveSync" not in raw


def test_sync_model_preserves_authority_boundaries() -> None:
    raw = _model()
    assert "external_runtime_memory.preferred_binding = unbound" in raw
    assert "synchronization qualified != Hindsight ingestion authorized" in raw
    assert "filesystem materialized != Evidence" in raw
    assert "vault path != governed identity" in raw
