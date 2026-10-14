"""Contract tests for targeted APU mapping review events."""

from pathlib import Path

from mvp_vertical import apu_mapping_reviews


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "mvp_vertical" / "sql" / "011_apu_mapping_reviews.sql"
API = ROOT / "mvp_vertical" / "execution_result_api.py"
PERSISTENCE = ROOT / "mvp_vertical" / "apu_mapping_reviews.py"


def test_mapping_review_vocabulary_and_authority_are_bounded() -> None:
    assert apu_mapping_reviews.ACTIONS == {
        "select_existing_object",
        "mark_unmatched",
        "needs_clarification",
        "reject_mapping",
    }
    assert apu_mapping_reviews.AUTHORITY == {
        "confirms_stable_identity": False,
        "writes_apu": False,
        "adopts_project_truth": False,
        "admits_evidence": False,
        "promotes_memory": False,
    }


def test_mapping_review_migration_is_append_only_and_not_apu_storage() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS apu_mapping_review_events" in sql
    assert "BEFORE UPDATE OR DELETE" in sql
    assert "selected_stable_object_ref" in sql
    assert "clarification_question" in sql
    assert "CREATE TABLE IF NOT EXISTS stable_object" not in sql
    assert "INSERT INTO" not in sql


def test_mapping_review_routes_require_editor_and_human_actor() -> None:
    source = API.read_text(encoding="utf-8")
    assert "/mappings/{mapping_ref}/reviews" in source
    assert "Depends(require_editor_key)" in source
    assert 'alias="X-Pantheon-Human-Actor"' in source
    assert '"stable_identity_confirmed": False' in source
    assert '"apu_mutated": False' in source
    assert '"evidence_admitted": False' in source
    assert '"memory_promoted": False' in source


def test_mapping_review_persistence_has_no_apu_write_path() -> None:
    source = PERSISTENCE.read_text(encoding="utf-8")
    assert "INSERT INTO apu_mapping_review_events" in source
    assert "selected stable object is not a mapping candidate" in source
    assert "INSERT INTO stable" not in source
    assert "UPDATE " not in source
    assert "DELETE " not in source
