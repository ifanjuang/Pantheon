from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SURFACE = ROOT / "docs" / "governance" / "HERMES_RUNTIME_SURFACE_REVIEW.md"


def _surface() -> str:
    return SURFACE.read_text(encoding="utf-8")


def test_hermes_0215_is_candidate_not_implicit_pin_move() -> None:
    surface = _surface()

    assert "live runtime qualification remains open" in surface
    assert "Current upstream stable requalification candidate: Hermes Agent 0.21.5" in surface
    assert "release_commit: f97608f178d1ffeca59860195ab7da295f7c8e5f" in surface
    assert "exact runtime qualification (Pantheon-Next#644 / H5.9b)" in surface
    assert "only then update the selected deployment pin" in surface


def test_requalification_preserves_runtime_governance_non_equivalences() -> None:
    surface = _surface()

    required = (
        "Hermes Profile A != Hermes Profile B",
        "parent session != delegated child session",
        "connector/webhook transcript input != Pantheon admitted input",
        "Hermes-visible tool != Pantheon admitted Capability / Binding",
        "Hermes runtime approval != Pantheon consequential-effect authorization",
        "Hermes/Hindsight memory or transcript != Evidence",
    )
    for invariant in required:
        assert invariant in surface


def test_affaires_source_admission_remains_outside_hermes() -> None:
    surface = _surface()

    assert "NAS / AFFAIRES source" in surface
    assert "Workspace observes/indexes" in surface
    assert "Pantheon explicitly admits bounded source/context" in surface
    assert "Hermes may consume only that admitted material" in surface
    assert "NAS mounted/readable != Hermes globally admitted browsing surface" in surface
    assert "Hindsight retained material != professional source != Evidence" in surface
