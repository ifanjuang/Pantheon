from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "hermes/profiles/_base/LANGGRAPH_RUNTIME_CANDIDATE.md"


def _text() -> str:
    return DOC.read_text(encoding="utf-8")


def test_langgraph_candidate_has_no_openwebui_binding() -> None:
    text = _text()
    assert "OpenWebUI" not in text
    assert "OPENWEBUI_INTEGRATION.md" not in text


def test_langgraph_candidate_keeps_current_surface_owners() -> None:
    text = _text()
    assert "Hermes clients handle runtime interaction" in text
    assert "Hermes Agent executes externally under Task Contract" in text
    assert "Pantheon Cockpit" in text
    assert "client selected != governance authority" in text
    assert "projection != persistence" in text


def test_langgraph_candidate_remains_optional_and_bounded() -> None:
    text = _text()
    assert "Status: Hermes runtime candidate template — not installed, not implemented" in text
    assert "Prefer the simpler existing Hermes execution path" in text
    assert "A graph edge cannot grant tool authority by itself" in text
    assert "LangGraph state is runtime state" in text
    assert "run trace as Evidence Pack" in text
    assert "LangGraph remains replaceable" in text
