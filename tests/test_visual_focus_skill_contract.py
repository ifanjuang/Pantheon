from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "templates/hermes/skills/visual-focus/SKILL.md"
REGISTRY = ROOT / "templates/TEMPLATE_REGISTRY.md"


def test_visual_focus_skill_reuses_native_hermes_region_surface():
    assert SKILL.is_file()

    text = SKILL.read_text(encoding="utf-8")
    assert "name: visual-focus" in text
    assert "status: candidate_template_only" in text
    assert "governed_by: templates/hermes/SKILLS.md" in text

    for native_surface in (
        "Hermes Agent 0.20.6 / v2026.8.27",
        "vision_analyze.region",
        "region=[x1, y1, x2, y2]",
        "original-image pixel coordinates",
        "reviewed upstream surface != installed runtime",
        "runtime capability available != task-authorized",
    ):
        assert native_surface in text

    assert "`human_focus`" in text
    assert "`context_compare`" in text
    assert "`grounded_focus` — optional capability gap only" in text
    assert "no grounding model is needed" in text
    assert "A model-derived region requires traceable tool/model identity and localization method" in text
    assert "missing provenance is a gap" in text

    for invariant in (
        "human selection != professional conclusion",
        "crop != source",
        "region != stable object identity",
        "bbox or mask != governed geometry",
        "visible != complete",
        "not visible != absent",
        "apparent defect != contractual non-conformity",
        "model inference != Evidence",
        "grounding confidence != verification",
        "runtime success != Evidence",
        "tool available != task-authorized",
        "A partial or unknown visual field must not support absence inference",
        "Hermes already owns the region zoom when available.",
        "Pantheon still decides what may become governed truth.",
    ):
        assert invariant in text

    lowered = text.lower()
    for provider_name in ("llmog", "sam3", "samapi", "x-anylabeling", "cvat"):
        assert provider_name not in lowered

    registry = REGISTRY.read_text(encoding="utf-8")
    skill_path = "templates/hermes/skills/visual-focus/SKILL.md"
    assert registry.count(skill_path) == 1
