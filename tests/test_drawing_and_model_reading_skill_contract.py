"""Contract of the drawing-reading and model-reading Hermes skills.

Both are loaded by a local model on demand: they stay short, name their
references, keep the confidence scale and never present a deduced value as read.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "templates" / "hermes" / "skills"
BUDGET = 6000  # bytes of the main SKILL.md a local model reads whole


@pytest.mark.parametrize("name", ["drawing-reading", "model-reading"])
def test_skill_is_short_declared_and_references_exist(name: str) -> None:
    text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\nname: " + name + "\n")
    assert "status: candidate_template_only" in text
    assert len(text.encode("utf-8")) <= BUDGET
    for reference in ("agency.md",):
        assert (SKILLS / name / "references" / reference).is_file()
    for linked in __import__("re").findall(r"\]\((references/[^)]+)\)", text):
        assert (SKILLS / name / linked).is_file(), linked


def test_drawing_reading_keeps_written_dimensions_above_measurements() -> None:
    text = (SKILLS / "drawing-reading" / "SKILL.md").read_text(encoding="utf-8")
    assert "Never measure when a\n  written dimension exists" in text
    assert "déduit (mesuré à l'échelle)" in text
    assert "get_project" in text and "Grid lines" in text


def test_model_reading_answers_from_published_readings_with_confidence() -> None:
    text = (SKILLS / "model-reading" / "SKILL.md").read_text(encoding="utf-8")
    assert "it does not open the IFC file" in text
    for word in ("validé", "lu", "déduit", "estimé"):
        assert f"**{word}**" in text
    assert "retry **once**" in text and "never choose" in text
