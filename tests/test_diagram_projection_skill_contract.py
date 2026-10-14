from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "templates/hermes/skills/diagram-projection/SKILL.md"
REGISTRY = ROOT / "templates/TEMPLATE_REGISTRY.md"
REVIEW = ROOT / "docs/governance/reference_reviews/DIAGRAM_DESIGN.md"


def test_diagram_projection_is_bounded_presentation_only() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert "name: diagram-projection" in text
    assert "status: candidate_template_only" in text
    assert "governed_by: docs/governance/VISUAL_LANGUAGE.md" in text

    for invariant in (
        "diagram != source",
        "diagram != Evidence",
        "rendered relation != governed relation",
        "layout geometry != governed geometry",
        "projection != persistence",
        "renderer success != source verification",
        "renderer output != Project Anatomy mutation",
        "Rendering never upgrades authority.",
    ):
        assert invariant in text


def test_diagram_projection_keeps_apu_and_bim_upstream() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert "Architecture Project Understanding remains upstream" in text
    assert "Observation Bundle Candidate" in text
    assert "architecture-project-understanding" in text
    assert "Do not ask the renderer to become an IFC/Revit/PDF understanding authority." in text

    for invariant in (
        "not found in snapshot != deleted",
        "diagram coordinate != measured coordinate",
        "axonometric rendering != BIM geometry",
        "visual proximity != governed adjacency",
    ):
        assert invariant in text


def test_diagram_design_binding_is_pinned_but_not_installed() -> None:
    skill = SKILL.read_text(encoding="utf-8")
    review = REVIEW.read_text(encoding="utf-8")

    upstream_ref = "d1376371965f513d99cc9ec388835d255c5c88d5"
    assert "cathrynlavery/diagram-design" in skill
    assert upstream_ref in skill
    assert upstream_ref in review

    assert "current task admits this exact tool" in skill
    assert "When tool admission is absent" in skill

    for posture in (
        "install_status: not established",
        "activation_status: unavailable",
        "task_authorization_status: unauthorized",
        "auto_install: false",
        "auto_update: false",
    ):
        assert posture in review


def test_diagram_projection_is_registered_once() -> None:
    registry = REGISTRY.read_text(encoding="utf-8")
    path = "templates/hermes/skills/diagram-projection/SKILL.md"
    assert registry.count(path) == 1
