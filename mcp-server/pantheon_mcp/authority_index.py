"""Pure, read-only authority-index discovery and resolution.

The master index remains the only registration point. Registered sub-indexes
extend placement coverage but cannot change the authority vocabulary. This
module has no MCP or network dependency so the MCP source map and governance CI
can share exactly the same path, group and glob semantics.
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path

INDEX_REL = "docs/governance/AUTHORITY_INDEX.md"
SUBINDEX_DIR = "docs/governance/authority"
PATH_RE = re.compile(r"`((?:docs|schemas|templates|ai_logs|hermes)/[^`]+)`")
ROW_RE = re.compile(
    r"^\s*\|\s*`(?P<path>[^`]+)`\s*\|\s*(?P<authority>[^|]+)"
    r"\|\s*(?P<repo_state>[^|]+)\|"
)


def _table_lines(path: Path) -> list[tuple[int, str]]:
    return [
        (number, line)
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if line.lstrip().startswith("|")
    ]


def _registered_subindex_paths(root: Path, master_lines: list[tuple[int, str]]) -> list[str]:
    cited = {
        match.group(1).strip()
        for _, line in master_lines
        for match in PATH_RE.finditer(line)
    }
    prefix = SUBINDEX_DIR + "/"
    return sorted(
        rel
        for rel in cited
        if rel.startswith(prefix) and rel.endswith(".md") and (root / rel).is_file()
    )


def load_authority_catalog(root: Path) -> dict:
    """Load the master plus registered sub-index rows from ``root``.

    Classification records come only from rows whose first cell is a backticked
    path. Coverage paths retain the checker's broader historic behavior: every
    repository path cited in a deliberate table row counts for coverage.
    """
    master = root / INDEX_REL
    if not master.is_file():
        return {
            "status": "not_run",
            "records": [],
            "coverage_paths": set(),
            "registered_subindexes": [],
            "unregistered_subindexes": [],
            "diagnostics": [f"master authority index missing: {INDEX_REL}"],
        }

    master_lines = _table_lines(master)
    registered = _registered_subindex_paths(root, master_lines)
    authority_dir = root / SUBINDEX_DIR
    available = (
        sorted(path.relative_to(root).as_posix() for path in authority_dir.glob("*.md"))
        if authority_dir.is_dir()
        else []
    )
    unregistered = sorted(set(available) - set(registered))
    diagnostics = [f"unregistered sub-index ignored: {rel}" for rel in unregistered]

    records: list[dict] = []
    coverage_paths: set[str] = set()
    for order, rel in enumerate([INDEX_REL, *registered]):
        for line_number, line in _table_lines(root / rel):
            coverage_paths.update(match.group(1).strip() for match in PATH_RE.finditer(line))
            match = ROW_RE.match(line)
            if not match:
                continue
            records.append(
                {
                    "path": match.group("path").strip(),
                    "authority": match.group("authority").strip(),
                    "repo_state": match.group("repo_state").strip(),
                    "source_index": rel,
                    "source_line": line_number,
                    "entry": line.strip(),
                    "index_order": order,
                }
            )

    return {
        "status": "loaded",
        "records": records,
        "coverage_paths": coverage_paths,
        "registered_subindexes": registered,
        "unregistered_subindexes": unregistered,
        "diagnostics": diagnostics,
    }


def _match_specificity(pattern: str, target: str) -> tuple[int, int] | None:
    if pattern == target:
        return (2, len(pattern))
    if pattern.endswith("/") and target.startswith(pattern):
        return (1, len(pattern))
    if "*" in pattern and fnmatch.fnmatch(target, pattern):
        return (1, len(pattern.replace("*", "")))
    return None


def resolve_authority(target: str, catalog: dict) -> dict:
    """Resolve one repository path without silently choosing a conflict."""
    if catalog.get("status") != "loaded":
        return {
            "resolution": "not_indexed",
            "authority": "not indexed",
            "repo_state": "not indexed",
            "source_index": None,
            "source_line": None,
            "entry": None,
            "matches": [],
            "diagnostics": list(catalog.get("diagnostics", [])),
        }

    matches: list[dict] = []
    for record in catalog["records"]:
        specificity = _match_specificity(record["path"], target)
        if specificity is not None:
            matches.append({**record, "specificity": specificity})

    if not matches:
        return {
            "resolution": "not_indexed",
            "authority": "not indexed",
            "repo_state": "not indexed",
            "source_index": None,
            "source_line": None,
            "entry": None,
            "matches": [],
            "diagnostics": [
                *catalog.get("diagnostics", []),
                f"no registered authority row covers: {target}",
            ],
        }

    best_specificity = max(match["specificity"] for match in matches)
    best = [match for match in matches if match["specificity"] == best_specificity]
    classifications = {(match["authority"], match["repo_state"]) for match in best}
    ordered = sorted(best, key=lambda item: (item["index_order"], item["source_line"], item["path"]))

    if len(classifications) > 1:
        return {
            "resolution": "conflict",
            "authority": "conflict",
            "repo_state": "conflict",
            "source_index": None,
            "source_line": None,
            "entry": None,
            "matches": ordered,
            "diagnostics": [
                *catalog.get("diagnostics", []),
                f"incompatible authority rows cover: {target}",
            ],
        }

    selected = ordered[0]
    return {
        "resolution": "resolved",
        "authority": selected["authority"],
        "repo_state": selected["repo_state"],
        "source_index": selected["source_index"],
        "source_line": selected["source_line"],
        "entry": selected["entry"],
        "matched_path": selected["path"],
        "match_type": "exact" if selected["path"] == target else "grouped",
        "matches": ordered,
        "diagnostics": list(catalog.get("diagnostics", [])),
    }


def grouped_covers(groups: set[str], rel: str) -> bool:
    """Return whether a registered directory or glob row covers ``rel``."""
    return any(_match_specificity(group, rel) is not None for group in groups)
