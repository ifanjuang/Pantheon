"""Static contract checks for the cross-source competency corpus.

These checks verify that the documented evaluation scenarios retain their
essential contrast cases. They do NOT validate Hermes reasoning, APU ingestion,
or the longitudinal H5.8 runtime.
"""

from pathlib import Path
import re

CORPUS = (
    Path(__file__).resolve().parents[1]
    / "docs/domain-packs/architecture/CROSS_SOURCE_COMPETENCY_CORPUS.md"
)


def _read() -> str:
    return CORPUS.read_text(encoding="utf-8")


def test_ten_cross_source_scenarios_are_distinct() -> None:
    text = _read()
    ids = re.findall(r"^### (C\d{2}) — ", text, flags=re.MULTILINE)
    assert ids == [f"C{i:02d}" for i in range(1, 11)]


def test_context_contrasts_are_present_without_new_phase_engine() -> None:
    text = _read()
    variants = re.findall(r"^\| (C\d{2}-[A-Z]) \|", text, flags=re.MULTILINE)
    assert variants == [
        "C01-A", "C01-B", "C01-C", "C01-D",
        "C03-A", "C03-B", "C03-C",
        "C08-A", "C08-B", "C08-C",
    ]
    assert "phase engine" in text.lower()
    assert "mixed-phase" in text


def test_epistemic_and_authorization_boundaries_are_explicit() -> None:
    text = _read()
    for phrase in (
        "never infer approval",
        "actual execution",
        "identity from a matching label",
        "without automatic write",
        "an explicitly asked question",
        "not executed acceptance",
    ):
        assert phrase.lower() in text.lower()
