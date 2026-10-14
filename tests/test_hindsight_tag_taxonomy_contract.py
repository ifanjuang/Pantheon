from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TAXONOMY = ROOT / "docs" / "governance" / "HINDSIGHT_TAG_TAXONOMY.md"


def test_native_project_page_is_scoped_incremental_and_non_recursive() -> None:
    text = TAXONOMY.read_text(encoding="utf-8")

    assert "Hindsight's native knowledge page" in text
    assert '"mode": "delta"' in text
    assert '"fact_types": ["world", "experience", "observation"]' in text
    assert '"exclude_mental_models": true' in text
    assert '"refresh_after_consolidation": true' in text
    assert '"tags_match": "all_strict"' in text
    assert "does not write a second summary file" in text
    assert "staleness check detects newer in-scope memories but not deletion" in text
