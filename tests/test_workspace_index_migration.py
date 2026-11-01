from __future__ import annotations

import importlib.util
from pathlib import Path
import sqlite3

import pytest


MODULE_PATH = Path(__file__).parents[1] / "deployment/ubuntu/migrate-workspace-indexes.py"
SPEC = importlib.util.spec_from_file_location("workspace_index_migration", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
migration = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(migration)


def _database(path: Path, workspace: str, entry_key: str, meta: dict[str, str], *, column_order: bool = False) -> None:
    path.unlink(missing_ok=True)
    db = sqlite3.connect(path)
    if column_order:
        db.execute("CREATE TABLE workspace_entries(entry_key TEXT PRIMARY KEY, workspace TEXT, kind TEXT, path TEXT, status TEXT, payload_json TEXT, observed_at TEXT, parent_path TEXT DEFAULT '')")
    else:
        db.execute("CREATE TABLE workspace_entries(entry_key TEXT PRIMARY KEY, workspace TEXT, kind TEXT, path TEXT, parent_path TEXT DEFAULT '', status TEXT, payload_json TEXT, observed_at TEXT)")
    db.execute("CREATE TABLE workspace_meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    db.execute(
        "INSERT INTO workspace_entries(entry_key, workspace, kind, path, parent_path, status, payload_json, observed_at) "
        "VALUES (?, ?, 'document', 'file.pdf', '', 'COMPLETE', '{\"parent_path\":\"folder\"}', 'now')",
        (entry_key, workspace),
    )
    db.executemany("INSERT INTO workspace_meta VALUES (?, ?)", list(meta.items()))
    db.commit()
    db.close()


def test_merge_imports_rows_preserves_affaires_meta_and_never_overwrites_sources(tmp_path: Path) -> None:
    affaires = tmp_path / "affaires.sqlite3"
    library = tmp_path / "library.sqlite3"
    output = tmp_path / "merged.sqlite3"
    _database(affaires, "Affaires", "a", {"projection": "affaires", "only_affaires": "yes"})
    _database(library, "Bibliotheque", "b", {"projection": "library", "only_library": "yes"}, column_order=True)

    report = migration.create_merged(affaires, library, output)
    db = sqlite3.connect(output)
    assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert db.execute("SELECT workspace FROM workspace_entries ORDER BY workspace").fetchall() == [("Affaires",), ("Bibliotheque",)]
    assert db.execute("SELECT parent_path FROM workspace_entries WHERE entry_key='b'").fetchone()[0] == "folder"
    assert db.execute("SELECT value FROM workspace_meta WHERE key='projection'").fetchone()[0] == "affaires"
    assert db.execute("SELECT value FROM workspace_meta WHERE key='only_library'").fetchone()[0] == "yes"
    db.close()
    assert report["integrity_check"] == "ok"
    assert not output.with_suffix(".sqlite3-wal").exists()
    assert sqlite3.connect(affaires).execute("SELECT COUNT(*) FROM workspace_entries").fetchone()[0] == 1
    assert sqlite3.connect(library).execute("SELECT COUNT(*) FROM workspace_entries").fetchone()[0] == 1


def test_merge_refuses_conflicting_identity_and_existing_output(tmp_path: Path) -> None:
    affaires = tmp_path / "affaires.sqlite3"
    library = tmp_path / "library.sqlite3"
    output = tmp_path / "merged.sqlite3"
    _database(affaires, "Affaires", "same", {"projection": "affaires"})
    _database(library, "Bibliotheque", "same", {"projection": "library"})
    with pytest.raises(ValueError, match="conflicting primary-key collision"):
        migration.create_merged(affaires, library, output)
    assert not output.exists()

    _database(library, "Bibliotheque", "b", {"projection": "library"})
    migration.create_merged(affaires, library, output)
    with pytest.raises(FileExistsError, match="already exists"):
        migration.create_merged(affaires, library, output)
