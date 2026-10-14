from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "implementation" / "hermes" / "skills" / "vault-search" / "SKILL.md"


def test_latest_document_resolution_uses_source_chronology_not_ingest_metadata() -> None:
    text = SKILL.read_text(encoding="utf-8")
    normalized = " ".join(text.split())

    assert "Latest document / revision resolution" in text
    assert "admitted vault reader or Docling" in text
    assert "source_revision" in text
    assert "source_document_date" in text
    assert "source_revision_history[]" in text
    assert "source_supersedes[]" in text
    assert "filesystem mtime" in normalized
    assert "cartouche date/index" in text
    assert "structurally resolved explicit Workspace supersedes relation" in text
    assert "explicit supersedes/replaces statement in the source" in text
    assert "explicit coherent revision history/table in the source" in text
    assert "heuristic ordering by comparable source revision/index" in text
    assert "source document date as heuristic tie-breaker/fallback" in text


def test_revision_date_conflicts_do_not_hide_human_errors() -> None:
    text = SKILL.read_text(encoding="utf-8")
    normalized = " ".join(text.split())

    assert "revision_date_conflict" in text
    assert "duplicate_revision" in text
    assert "incomparable_revision" in text
    assert "keep it first only as the index-ranked candidate" in text
    assert "keep the other candidate visible" in text
    assert "do not silently collapse them" in text
    assert "currentness is unresolved" in text
    assert "declared routing lineage, not source truth" in normalized
    assert "branching_lineage" in text
    assert "invalid_lineage" in text
    assert "declared_source_conflict" in text
    assert "declared routing" in text
    assert "source chronology does not contradict it" in text
