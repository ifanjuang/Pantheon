"""Every startup migration must be lock-light, not just the Information one.

`initialize_composed_schema()` replays all of these on each service start. An
unguarded `ALTER TABLE` takes an ACCESS EXCLUSIVE lock even when it has nothing
to change, and a plain `ADD CONSTRAINT ... CHECK` re-scans the whole table every
time, so a boot can block behind — or block — live traffic.

`test_projection_startup_migration_remains_lock_light` already asserted this for
`information_projection` alone. Scoping the rule to one module let the next
migration reintroduce eight unguarded statements. This asserts it for the whole
startup set, discovered from the initializer rather than listed.

Guarded schema evolution stays allowed: an `ALTER TABLE` inside a `DO $$ ... $$`
block that first checks the catalog performs catalog reads only once applied.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMPOSED = ROOT / "mvp_vertical" / "cockpit_composed.py"


def _startup_migration_modules() -> list[str]:
    """Modules whose MIGRATION the composed initializer replays on every boot."""
    tree = ast.parse(COMPOSED.read_text(encoding="utf-8"))
    initializer = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "initialize_composed_schema"
    )
    modules = [
        node.value.id
        for node in ast.walk(initializer)
        if isinstance(node, ast.Attribute)
        and node.attr == "MIGRATION"
        and isinstance(node.value, ast.Name)
    ]
    assert modules, "no startup migrations discovered in initialize_composed_schema"
    return modules


def _migration_path(module_name: str) -> Path:
    module = __import__(f"mvp_vertical.{module_name}", fromlist=["MIGRATION"])
    return Path(module.MIGRATION)


def _strip_guarded_blocks(sql: str) -> str:
    """Remove DO $$ ... $$ blocks: their ALTERs run only when the catalog says so."""
    return re.sub(r"DO\s*\$\$.*?\$\$\s*;", "", sql, flags=re.DOTALL | re.IGNORECASE)


@pytest.mark.parametrize("module_name", _startup_migration_modules())
def test_startup_migration_has_no_unguarded_alter_table(module_name: str) -> None:
    sql = _migration_path(module_name).read_text(encoding="utf-8")
    unguarded = _strip_guarded_blocks(sql)

    offenders = [
        line.strip()
        for line in unguarded.splitlines()
        if line.strip().upper().startswith("ALTER TABLE")
    ]
    assert not offenders, (
        f"{module_name}: unguarded ALTER TABLE in a migration replayed on every "
        f"start. Wrap it in a DO $$ block that checks the catalog first:\n  "
        + "\n  ".join(offenders)
    )


@pytest.mark.parametrize("module_name", _startup_migration_modules())
def test_startup_migration_adds_no_validating_check_constraint(module_name: str) -> None:
    """A validating CHECK re-scans the table; guarded or NOT VALID, never bare."""
    sql = _strip_guarded_blocks(_migration_path(module_name).read_text(encoding="utf-8"))
    bare = re.findall(
        r"ADD\s+CONSTRAINT\s+\S+\s+CHECK\s*\((?:[^()]|\([^()]*\))*\)\s*;",
        sql,
        flags=re.IGNORECASE,
    )
    assert not bare, f"{module_name}: unguarded validating CHECK constraint: {bare}"


def test_the_guard_recognizes_a_guarded_alter() -> None:
    """The rule must accept the guarded form, or it just bans schema evolution."""
    guarded = """
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'x') THEN
            ALTER TABLE t ADD CONSTRAINT x CHECK (c IN (1, 2));
        END IF;
    END;
    $$;
    """
    assert "ALTER TABLE" not in _strip_guarded_blocks(guarded).upper()

    bare = "ALTER TABLE t ADD COLUMN c TEXT;"
    assert "ALTER TABLE" in _strip_guarded_blocks(bare).upper()


def test_guarded_migrations_reach_their_target_schema_on_a_fresh_database() -> None:
    """A guard that skips is only correct if the schema is already correct.

    Guarding schema evolution on the catalog introduces a failure mode the
    unguarded form did not have: a marker that also matches the *old* definition
    makes the guard conclude "already applied" and skip. The suite could not see
    it, because every local database had already been migrated by the earlier,
    unguarded statements — only a fresh database exercises the guard's decision.

    This applies the startup set to a throwaway database and asserts the
    constraints reached their target vocabulary.
    """
    import uuid

    import psycopg
    import pytest as _pytest

    from mvp_vertical import store

    try:
        admin = psycopg.connect(store.dsn_from_env(), autocommit=True)
    except Exception as exc:  # pragma: no cover - unit-only environment
        _pytest.skip(f"PostgreSQL unreachable: {exc}")

    scratch = f"mvp_migrationprobe_{uuid.uuid4().hex[:12]}"
    with admin:
        admin.execute(f'CREATE DATABASE "{scratch}"')
    try:
        dsn = store.dsn_from_env()
        probe_dsn = dsn.rsplit("/", 1)[0] + "/" + scratch
        conn = psycopg.connect(probe_dsn)
        try:
            # store.DDL creates the base tables the startup migrations evolve.
            conn.execute(store.DDL)
            conn.commit()
            for module_name in _startup_migration_modules():
                conn.execute(_migration_path(module_name).read_text(encoding="utf-8"))
            conn.commit()

            expected = {
                "agency_change_candidates_status_check": "revision_requested",
                "agency_change_candidate_events_event_type_check": "revision_requested",
                "execution_result_items_result_kind_check": "knowledge_edit_variant",
            }
            for name, value in expected.items():
                row = conn.execute(
                    "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = %s",
                    (name,),
                ).fetchone()
                assert row is not None, f"{name} was never created"
                assert value in row[0], (
                    f"{name} does not accept {value!r} on a fresh database: {row[0]}. "
                    "A catalog guard whose marker also matches the previous "
                    "definition skips the evolution it was meant to perform."
                )

            # Same failure mode, other half of the schema: a guarded ALTER COLUMN
            # ... SET DEFAULT can skip just as silently as a guarded constraint.
            # Discovered from the catalog rather than listed, so a table added
            # later is covered without anyone remembering to add it here.
            transaction_timed = conn.execute(
                """
                SELECT table_name, column_default
                  FROM information_schema.columns
                 WHERE table_schema = 'public'
                   AND column_name = 'occurred_at'
                   AND column_default NOT LIKE '%clock_timestamp%'
                 ORDER BY table_name
                """
            ).fetchall()
            assert not transaction_timed, (
                "append-only log(s) whose occurred_at is the transaction start time, "
                "so events written together cannot be ordered by it: "
                + "; ".join(f"{table} -> {default}" for table, default in transaction_timed)
            )
        finally:
            conn.close()
    finally:
        admin = psycopg.connect(store.dsn_from_env(), autocommit=True)
        with admin:
            admin.execute(f'DROP DATABASE IF EXISTS "{scratch}" WITH (FORCE)')
