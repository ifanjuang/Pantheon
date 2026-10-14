"""The relation review migration must survive a database that already has rows.

Relations shipped without a review state: a relation was canonical the moment it
was written. Adding `proposed -> canonical -> retired` means adding a column to a
populated table and backfilling it, and the backfill is the dangerous half.

The first version of that migration died on every installation that already had a
relation, and no existing test could see it: the scope trigger installed by the
previous version accepts exactly one UPDATE shape — active to retired, advancing
the revision — and a backfill is neither. Every local database was empty, so the
UPDATE touched no rows and raised nothing.

This applies the previously shipped migration to a throwaway database, writes one
active and one retired relation through it, and only then applies the migration
under test. The shipped schema is an immutable fixture copied from commit
fa27ae9fd71d39e06c27271e2d3936c36284afb7, the parent of the relation-review
change introduced in Pantheon-Next#254.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import psycopg
import pytest

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "mvp_vertical" / "sql" / "015_entity_relations.sql"
SHIPPED_MIGRATION = ROOT / "tests" / "fixtures" / "015_entity_relations_pre_review.sql"


@pytest.fixture
def migrated_from_shipped():
    from mvp_vertical import (
        agency_data,
        information_projection,
        source_intake,
        store,
        work_issues,
    )

    try:
        admin = psycopg.connect(store.dsn_from_env(), autocommit=True)
    except Exception as exc:  # pragma: no cover - unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")

    scratch = f"mvp_relationprobe_{uuid.uuid4().hex[:12]}"
    with admin:
        admin.execute(f'CREATE DATABASE "{scratch}"')
    probe_dsn = store.dsn_from_env().rsplit("/", 1)[0] + "/" + scratch
    conn = psycopg.connect(probe_dsn)
    try:
        conn.execute(store.DDL)
        for migration in (
            work_issues.MIGRATION,
            agency_data.MIGRATION,
            source_intake.MIGRATION,
            information_projection.MIGRATION,
        ):
            conn.execute(migration.read_text(encoding="utf-8"))
        conn.execute(SHIPPED_MIGRATION.read_text(encoding="utf-8"))
        conn.commit()

        conn.execute(
            "INSERT INTO agency_projects (project_id, code, display_name, created_by, updated_by) "
            "VALUES ('p1', 'P1', 'P1', 'h', 'h')"
        )
        for index in (1, 2):
            conn.execute(
                "INSERT INTO agency_information_cards (information_id, series_id, project_id, "
                "title, category, source_type, source_note, index_label, status) "
                "VALUES (%s, %s, 'p1', %s, 'note', 'human', 'n', 'A', 'draft')",
                (f"i{index}", f"s{index}", f"T{index}"),
            )
        conn.execute(
            "INSERT INTO agency_entity_relations (relation_id, project_id, from_entity_type, "
            "from_entity_id, to_entity_type, to_entity_id, relation_type, created_by) "
            "VALUES ('r-active', 'p1', 'information', 'i1', 'information', 'i2', 'responds_to', 'h')"
        )
        conn.execute(
            "INSERT INTO agency_entity_relations (relation_id, project_id, from_entity_type, "
            "from_entity_id, to_entity_type, to_entity_id, relation_type, created_by, "
            "retired_at, retired_by, revision) "
            "VALUES ('r-retired', 'p1', 'information', 'i2', 'information', 'i1', 'relies_on', "
            "'h', clock_timestamp(), 'h', 2)"
        )
        conn.commit()

        conn.execute(MIGRATION.read_text(encoding="utf-8"))
        conn.commit()
        yield conn
    finally:
        conn.close()
        admin = psycopg.connect(store.dsn_from_env(), autocommit=True)
        with admin:
            admin.execute(f'DROP DATABASE IF EXISTS "{scratch}" WITH (FORCE)')


def test_existing_rows_keep_their_meaning(migrated_from_shipped) -> None:
    """Nothing becomes a proposal retroactively.

    Under the old rules an unretired relation was canonical — that is what its
    author asserted. Backfilling it to `proposed` would claim a human review that
    never happened, which is the one mapping that would be a lie.
    """
    rows = migrated_from_shipped.execute(
        "SELECT relation_id, status FROM agency_entity_relations ORDER BY relation_id"
    ).fetchall()
    assert rows == [("r-active", "canonical"), ("r-retired", "retired")]


def test_the_scope_guard_is_restored(migrated_from_shipped) -> None:
    """The backfill drops the stale guard; the migration must put the new one back."""
    assert migrated_from_shipped.execute(
        "SELECT 1 FROM pg_trigger WHERE tgname = 'agency_entity_relations_scope_guard'"
    ).fetchone() is not None


def test_every_guarded_change_reaches_its_target(migrated_from_shipped) -> None:
    """A guard that skips is only correct if the schema is already correct."""
    index = migrated_from_shipped.execute(
        "SELECT indexdef FROM pg_indexes "
        "WHERE indexname = 'agency_entity_relations_active_edge_unique'"
    ).fetchone()
    assert index is not None and "status" in index[0], index

    expected = {
        "agency_entity_relations_from_entity_type_check": "apu_object",
        "agency_entity_relations_to_entity_type_check": "apu_object",
        "agency_entity_relations_revision_check": "revision >= 1",
        "agency_entity_relations_open_or_closed_check": "rejected",
        "agency_entity_relation_events_event_type_check": "relation_proposed",
        "agency_entity_relation_events_hermes_proposes_only": "relation_proposed",
    }
    for name, marker in expected.items():
        row = migrated_from_shipped.execute(
            "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = %s",
            (name,),
        ).fetchone()
        assert row is not None, f"{name} was never created"
        assert marker in row[0], f"{name} did not reach its target: {row[0]}"


def test_replaying_the_migration_changes_nothing(migrated_from_shipped) -> None:
    """It is replayed on every boot, so the second run must be a catalog read."""
    before = migrated_from_shipped.execute(
        "SELECT relation_id, status, revision FROM agency_entity_relations ORDER BY relation_id"
    ).fetchall()
    migrated_from_shipped.execute(MIGRATION.read_text(encoding="utf-8"))
    migrated_from_shipped.commit()
    after = migrated_from_shipped.execute(
        "SELECT relation_id, status, revision FROM agency_entity_relations ORDER BY relation_id"
    ).fetchall()
    assert before == after


def test_hermes_cannot_write_a_decision_event_even_directly(migrated_from_shipped) -> None:
    """The gate is in the schema, not only in the module.

    A caller that bypasses entity_relations.py — a script, a future route, a
    migration — still cannot record Hermes canonizing anything.
    """
    with pytest.raises(psycopg.errors.CheckViolation):
        migrated_from_shipped.execute(
            "INSERT INTO agency_entity_relation_events (event_id, relation_id, event_type, "
            "actor, actor_kind, idempotency_key, payload_digest, result_snapshot) "
            "VALUES ('e1', 'r-active', 'relation_canonized', 'hermes', 'hermes', 'k1', 'd', '{}')"
        )
