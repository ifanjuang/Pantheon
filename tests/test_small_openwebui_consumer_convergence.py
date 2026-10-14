from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_distillation_registry_is_client_agnostic():
    text = _read("docs/governance/DISTILLATION_REGISTRY.md")
    assert "OPENWEBUI_INTEGRATION.md" not in text
    assert "openwebui_exposure_candidate" not in text
    assert "OpenWebUI User Decision Surface Pattern" not in text
    assert "governed_projection_candidate" in text
    assert "client selected != governance authority" in text


def test_evaluation_simulation_candidate_keeps_governance_boundary():
    text = _read("hermes/profiles/_base/EVALUATION_AND_SIMULATION_CANDIDATE.md")
    assert "OPENWEBUI_INTEGRATION.md" not in text
    assert "OpenWebUI" not in text
    assert "Hermes Agent executes externally" in text
    assert "Pantheon Cockpit" in text
    assert "Task Contract" in text
    assert "Evidence Pack Candidate" in text
    assert "memory promotion authority" in text
    assert "approval authority" in text
    assert "simulation pass as approval" in text
