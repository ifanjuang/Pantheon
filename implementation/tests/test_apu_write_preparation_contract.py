from pathlib import Path

from mvp_vertical import apu_write_preparation


ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "mvp_vertical" / "sql" / "012_apu_write_preparation.sql"
API = ROOT / "mvp_vertical" / "apu_write_api.py"


def test_write_preparation_vocabulary_is_bounded():
    assert apu_write_preparation.AUTHORIZATION_ACTIONS == {
        "authorize_application",
        "reject_application",
    }
    assert apu_write_preparation.COMMAND_AUTHORITY["is_apu_write"] is False
    assert apu_write_preparation.COMMAND_AUTHORITY["authorizes_external_effect"] is False


def test_migration_is_append_only_and_does_not_write_apu_objects():
    sql = SQL.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS apu_write_command_candidates" in sql
    assert "CREATE TABLE IF NOT EXISTS apu_write_authorization_events" in sql
    assert "BEFORE UPDATE OR DELETE" in sql
    assert "INSERT INTO stable_object" not in sql.lower()
    assert "INSERT INTO apu_object" not in sql.lower()


def test_api_separates_preparation_authorization_and_application():
    source = API.read_text(encoding="utf-8")
    assert "prepare-apu-write" in source
    assert '"/apu-write-commands/{command_id}/authorizations"' in source
    assert '"write_command_prepared": True' in source
    assert '"application_authorized": False' in source
    assert '"command_applied": False' in source
    assert '"apu_mutated": False' in source
    assert 'alias="X-Pantheon-Human-Actor"' in source
    assert 'alias="Idempotency-Key"' in source
