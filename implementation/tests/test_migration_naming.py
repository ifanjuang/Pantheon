"""The migration filenames must stay unambiguous, and every one must be owned.

`mvp_vertical/sql/` accumulated four duplicate numeric prefixes — `003`, `004`,
`005` and `010` — because two independent sequences were numbering into one
directory: the Agency/Cockpit lineage and the Hermes lineage, the latter a
contiguous `003`–`007` block. Nothing was misordered by it (every cross-file
dependency held either way), but `sql/003_*` no longer named one file, so the
prefix stopped answering the only question it exists to answer.

The two lineages now live in two directories. These tests keep it that way, and
catch the two mistakes a rename makes easy: a constant left pointing at the old
path, and a `.sql` file no module claims.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "mvp_vertical" / "sql"
MODULES = sorted((ROOT / "mvp_vertical").glob("*.py"))

# `Path(...) / "sql" / "hermes" / "004_execution_admissions.sql"` and the
# one-segment form both reduce to the trailing quoted segments.
_MIGRATION_PATH = re.compile(r'"sql"((?:\s*/\s*"[^"]+")+)')
_SEGMENT = re.compile(r'"([^"]+)"')


def _declared_migrations() -> dict[Path, Path]:
    """Every migration file a module names, mapped to the module naming it."""
    declared: dict[Path, Path] = {}
    for module in MODULES:
        text = module.read_text(encoding="utf-8")
        for match in _MIGRATION_PATH.finditer(text):
            declared[SQL.joinpath(*_SEGMENT.findall(match.group(1)))] = module
    return declared


def _lineages() -> dict[Path, list[Path]]:
    return {SQL: sorted(SQL.glob("*.sql")), SQL / "hermes": sorted((SQL / "hermes").glob("*.sql"))}


@pytest.mark.parametrize("lineage", sorted(_lineages()), ids=lambda path: path.name)
def test_numeric_prefixes_are_unique_within_a_lineage(lineage: Path) -> None:
    prefixes: dict[str, list[str]] = {}
    for migration in _lineages()[lineage]:
        prefix = migration.name.split("_", 1)[0]
        assert prefix.isdigit(), f"{migration.name} has no numeric prefix"
        prefixes.setdefault(prefix, []).append(migration.name)
    duplicated = {prefix: names for prefix, names in prefixes.items() if len(names) > 1}
    assert not duplicated, (
        f"duplicate migration prefixes in {lineage.name}/: "
        + "; ".join(f"{prefix} -> {', '.join(names)}" for prefix, names in sorted(duplicated.items()))
    )


def test_every_declared_migration_path_exists() -> None:
    """A rename that misses a constant fails here, not at the next boot."""
    missing = sorted(
        f"{module.name} -> {path.relative_to(SQL)}"
        for path, module in _declared_migrations().items()
        if not path.is_file()
    )
    assert not missing, "module(s) naming a migration that does not exist: " + "; ".join(missing)


def test_every_migration_file_is_claimed_by_a_module() -> None:
    """A migration no module replays is applied by nothing and read by no one."""
    declared = set(_declared_migrations())
    orphans = sorted(
        str(migration.relative_to(SQL))
        for lineage in _lineages().values()
        for migration in lineage
        if migration not in declared
    )
    assert not orphans, "migration file(s) no module names: " + ", ".join(orphans)
