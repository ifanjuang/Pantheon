#!/usr/bin/env python3
"""Merge the Affaires and Bibliotheque producer indexes into a new SQLite file.

The default mode is read-only and reports the merge plan. ``--apply`` creates a
new destination; it never edits either input or overwrites an existing file.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from typing import Any


def _open_readonly(path: Path) -> sqlite3.Connection:
    if not path.is_absolute() or not path.is_file() or path.is_symlink():
        raise ValueError(f"input must be an absolute regular file: {path}")
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    integrity = connection.execute("PRAGMA quick_check").fetchone()[0]
    if integrity != "ok":
        connection.close()
        raise ValueError(f"SQLite integrity check failed for {path}: {integrity}")
    return connection


def _tables(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    names = [row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )]
    for name in names:
        info = connection.execute(f'PRAGMA table_info("{name}")').fetchall()
        result[name] = {
            "columns": [str(row[1]) for row in info],
            "primary_key": [str(row[1]) for row in sorted(info, key=lambda row: int(row[5]) or 9999) if int(row[5])],
        }
    return result


def _count(connection: sqlite3.Connection, table: str) -> int:
    return int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])


def _row_key(row: sqlite3.Row, primary_key: list[str]) -> tuple[Any, ...]:
    if not primary_key:
        raise ValueError("cannot safely merge a table without a primary key")
    return tuple(row[column] for column in primary_key)


def _rows_equal(left: sqlite3.Row, right: sqlite3.Row, columns: list[str]) -> bool:
    return all(left[column] == right[column] for column in columns)


def inspect_merge(affaires: sqlite3.Connection, library: sqlite3.Connection) -> dict[str, Any]:
    target_schema = _tables(affaires)
    source_schema = _tables(library)
    if set(target_schema) != set(source_schema):
        raise ValueError("input table sets differ; refusing an implicit schema migration")

    report: dict[str, Any] = {"tables": {}, "workspace_meta_conflicts_preserved_from_affaires": []}
    for table in sorted(target_schema):
        target = target_schema[table]
        source = source_schema[table]
        if set(target["columns"]) != set(source["columns"]):
            raise ValueError(f"column sets differ in {table}; refusing to discard data")
        if target["primary_key"] != source["primary_key"]:
            raise ValueError(f"primary keys differ in {table}")
        if not target["primary_key"]:
            raise ValueError(f"table {table} has no primary key")

        left_rows = affaires.execute(f'SELECT * FROM "{table}"').fetchall()
        right_rows = library.execute(f'SELECT * FROM "{table}"').fetchall()
        left_by_key = {_row_key(row, target["primary_key"]): row for row in left_rows}
        collisions: list[tuple[Any, ...]] = []
        identical = 0
        for row in right_rows:
            key = _row_key(row, target["primary_key"])
            existing = left_by_key.get(key)
            if existing is None:
                continue
            collisions.append(key)
            if _rows_equal(existing, row, target["columns"]):
                identical += 1
            elif table != "workspace_meta":
                raise ValueError(f"conflicting primary-key collision in {table}: {key!r}")

        imported = len(right_rows) - len(collisions)
        report["tables"][table] = {
            "affaires_rows": len(left_rows),
            "bibliotheque_rows": len(right_rows),
            "imported_rows": imported,
            "identical_collisions_skipped": identical,
            "conflicting_meta_keys_preserved_from_affaires": (
                [str(key[0]) for key, row in ((key, left_by_key[key]) for key in collisions)
                 if not _rows_equal(row, next(r for r in right_rows if _row_key(r, target["primary_key"]) == key), target["columns"])]
                if table == "workspace_meta" else []
            ),
        }
        if table == "workspace_meta":
            report["workspace_meta_conflicts_preserved_from_affaires"].extend(
                report["tables"][table]["conflicting_meta_keys_preserved_from_affaires"]
            )
    return report


def create_merged(affaires_path: Path, library_path: Path, output_path: Path) -> dict[str, Any]:
    if not output_path.is_absolute():
        raise ValueError("destination must be absolute")
    if output_path.exists() or output_path.is_symlink():
        raise FileExistsError(f"destination already exists: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    affaires = _open_readonly(affaires_path)
    library = _open_readonly(library_path)
    temporary_path: Path | None = None
    try:
        report = inspect_merge(affaires, library)
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{output_path.name}.", suffix=".building", dir=output_path.parent)
        os.close(descriptor)
        temporary_path = Path(temporary_name)
        destination = sqlite3.connect(temporary_path)
        destination.row_factory = sqlite3.Row
        try:
            affaires.backup(destination)
            destination.execute("PRAGMA journal_mode=DELETE")
            destination.execute("BEGIN IMMEDIATE")
            for table in sorted(_tables(affaires)):
                columns = _tables(affaires)[table]["columns"]
                source_rows = library.execute(f'SELECT * FROM "{table}"').fetchall()
                target_rows = destination.execute(f'SELECT * FROM "{table}"').fetchall()
                primary_key = _tables(affaires)[table]["primary_key"]
                existing = {_row_key(row, primary_key): row for row in target_rows}
                placeholders = ",".join("?" for _ in columns)
                quoted_columns = ",".join(f'"{column}"' for column in columns)
                for row in source_rows:
                    key = _row_key(row, primary_key)
                    if key in existing:
                        # workspace_meta is a per-index singleton map. Keep the
                        # Affaires value for duplicate keys; import only keys
                        # present exclusively in the Bibliotheque index.
                        continue
                    values = {column: row[column] for column in columns}
                    if table == "workspace_entries" and not values.get("parent_path"):
                        try:
                            payload = json.loads(str(values.get("payload_json") or "{}"))
                        except json.JSONDecodeError:
                            payload = {}
                        if isinstance(payload, dict):
                            values["parent_path"] = str(payload.get("parent_path") or "")
                    destination.execute(
                        f'INSERT INTO "{table}" ({quoted_columns}) VALUES ({placeholders})',
                        [values[column] for column in columns],
                    )
            destination.commit()
            integrity = destination.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise ValueError(f"merged SQLite integrity check failed: {integrity}")
            for table in sorted(_tables(affaires)):
                report["tables"][table]["merged_rows"] = _count(destination, table)
        except Exception:
            destination.rollback()
            raise
        finally:
            destination.close()
        os.chmod(temporary_path, 0o600)
        # Hard-link publication refuses to overwrite a file created concurrently.
        os.link(temporary_path, output_path)
        temporary_path.unlink()
        temporary_path = None
        report["destination"] = str(output_path)
        report["integrity_check"] = "ok"
        return report
    finally:
        affaires.close()
        library.close()
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--affaires", type=Path, required=True)
    parser.add_argument("--bibliotheque", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="create a new merged output; inputs remain read-only")
    args = parser.parse_args()
    affaires = _open_readonly(args.affaires)
    library = _open_readonly(args.bibliotheque)
    try:
        report = inspect_merge(affaires, library)
    finally:
        affaires.close()
        library.close()
    if args.apply:
        report = create_merged(args.affaires, args.bibliotheque, args.output)
    else:
        report["mode"] = "dry-run"
        report["destination"] = str(args.output)
        report["destination_exists"] = args.output.exists()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
