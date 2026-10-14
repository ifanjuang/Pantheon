"""Regression checks for bounded Hermes instruction/orientation context."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HERMES_TEMPLATE_ROOT = ROOT / "templates" / "hermes"
SKILLS = HERMES_TEMPLATE_ROOT / "SKILLS.md"
ORIENTATION_SURFACE = tuple(
    HERMES_TEMPLATE_ROOT / name
    for name in ("AGENTS.md", "CLAUDE.md", "DESIGN.md", "README.md", "SKILLS.md")
)

# Repository-side review ratchets only. They are not Hermes runtime/token limits.
ORIENTATION_REVIEW_CEILING_BYTES = 24 * 1024
PER_FILE_REVIEW_CEILING_BYTES = 12 * 1024


def test_hermes_template_orientation_surface_stays_bounded() -> None:
    sizes = {path.name: path.stat().st_size for path in ORIENTATION_SURFACE}

    assert sum(sizes.values()) <= ORIENTATION_REVIEW_CEILING_BYTES, sizes
    assert all(size <= PER_FILE_REVIEW_CEILING_BYTES for size in sizes.values()), sizes


def test_context_budget_contract_preserves_authority_and_complete_reads() -> None:
    text = SKILLS.read_text(encoding="utf-8")

    for invariant in (
        "Context read budget",
        "each durable convention has one owner",
        "per-file bytes",
        "Do not concatenate several mandatory files into one read",
        "complete-read check",
        "repository size check != deployed runtime observation",
        "file present != file read completely",
        "context loaded != instruction authorized",
        "smaller prompt != permission to drop governance",
        "rule duplicated != rule reinforced",
        "Verify the inventory of retained rules/references after the cut",
    ):
        assert invariant in text

    assert "the ceiling is a regression ratchet, not a Hermes token limit" in text
