"""Tests for the shared, fail-closed authority-index resolver."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = MODULE_DIR.parent
sys.path.insert(0, str(MODULE_DIR))

from pantheon_mcp.authority_index import (  # noqa: E402
    load_authority_catalog,
    resolve_authority,
)


class TestAuthorityResolver(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "docs/governance/authority").mkdir(parents=True)
        (self.root / "docs/governance/AUTHORITY_INDEX.md").write_text(
            """| Path | Authority | State | Notes |
|---|---|---|---|
| `docs/governance/exact.md` | canonical doctrine | implemented | exact |
| `docs/governance/group/` | active support doctrine | documented | group |
| `docs/governance/GLOB_*.md` | candidate / to verify | to verify | glob |
| `docs/governance/authority/REGISTERED.md` | candidate support map | documented | registered |
""",
            encoding="utf-8",
        )
        (self.root / "docs/governance/authority/REGISTERED.md").write_text(
            """| Path | Authority | State | Notes |
|---|---|---|---|
| `docs/governance/from-subindex.md` | active support doctrine | documented | sub |
| `docs/governance/group/specific.md` | canonical doctrine | implemented | exact wins |
""",
            encoding="utf-8",
        )
        (self.root / "docs/governance/authority/UNREGISTERED.md").write_text(
            """| Path | Authority | State | Notes |
|---|---|---|---|
| `docs/governance/ignored.md` | canonical doctrine | implemented | ignored |
""",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def test_exact_master_row_is_traced(self):
        result = resolve_authority(
            "docs/governance/exact.md", load_authority_catalog(self.root)
        )
        self.assertEqual(result["resolution"], "resolved")
        self.assertEqual(result["authority"], "canonical doctrine")
        self.assertEqual(
            result["source_index"], "docs/governance/AUTHORITY_INDEX.md"
        )
        self.assertEqual(result["match_type"], "exact")
        self.assertIsInstance(result["source_line"], int)

    def test_registered_subindex_row_resolves(self):
        result = resolve_authority(
            "docs/governance/from-subindex.md",
            load_authority_catalog(self.root),
        )
        self.assertEqual(result["resolution"], "resolved")
        self.assertEqual(
            result["source_index"],
            "docs/governance/authority/REGISTERED.md",
        )

    def test_exact_row_wins_over_group(self):
        result = resolve_authority(
            "docs/governance/group/specific.md",
            load_authority_catalog(self.root),
        )
        self.assertEqual(result["authority"], "canonical doctrine")
        self.assertEqual(result["match_type"], "exact")

    def test_directory_and_glob_rows_resolve(self):
        catalog = load_authority_catalog(self.root)
        directory = resolve_authority("docs/governance/group/member.md", catalog)
        glob = resolve_authority("docs/governance/GLOB_ONE.md", catalog)
        self.assertEqual(directory["resolution"], "resolved")
        self.assertEqual(directory["match_type"], "grouped")
        self.assertEqual(glob["resolution"], "resolved")
        self.assertEqual(glob["authority"], "candidate / to verify")

    def test_missing_and_unregistered_rows_are_explicit(self):
        catalog = load_authority_catalog(self.root)
        missing = resolve_authority("docs/governance/missing.md", catalog)
        ignored = resolve_authority("docs/governance/ignored.md", catalog)
        self.assertEqual(missing["resolution"], "not_indexed")
        self.assertEqual(ignored["resolution"], "not_indexed")
        self.assertTrue(
            any("UNREGISTERED.md" in item for item in ignored["diagnostics"])
        )

    def test_incompatible_equally_specific_rows_fail_closed(self):
        with (self.root / "docs/governance/authority/REGISTERED.md").open(
            "a", encoding="utf-8"
        ) as handle:
            handle.write(
                "| `docs/governance/exact.md` | candidate / to verify | "
                "to verify | conflict |\n"
            )
        result = resolve_authority(
            "docs/governance/exact.md", load_authority_catalog(self.root)
        )
        self.assertEqual(result["resolution"], "conflict")
        self.assertEqual(result["authority"], "conflict")
        self.assertEqual(len(result["matches"]), 2)


class TestAuthorityIntegration(unittest.TestCase):
    def test_coverage_checker_uses_the_same_current_catalog(self):
        script_path = REPO_ROOT / ".github/scripts/check_index_coverage.py"
        spec = importlib.util.spec_from_file_location("check_index_coverage", script_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)

        catalog = load_authority_catalog(REPO_ROOT)
        self.assertEqual(
            checker.registered_subindexes(None), catalog["registered_subindexes"]
        )
        self.assertEqual(checker.indexed_paths(None), catalog["coverage_paths"])


if __name__ == "__main__":
    unittest.main()
