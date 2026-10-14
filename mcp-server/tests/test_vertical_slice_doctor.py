"""Read-only tests for the vertical-slice doctor check.

They validate the shipped dossier and prove that a broken dossier is rejected:
a register candidate not scoped to a project, and an answer status that stops
referencing the dossier evidence pack, both fail the coherence invariants. The
tests copy the dossier + schemas into a temp root and mutate the copy; the repo
is never modified. They fetch nothing, execute nothing and write nothing to the repo.
"""
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from pantheon_mcp.doctor import check_vertical_slice, find_repo_root

SLICE = ("docs", "examples", "vertical_devis_reprise")


class TestVerticalSlice(unittest.TestCase):
    def _tmp_root(self) -> Path:
        src = find_repo_root()
        tmp = Path(tempfile.mkdtemp())
        shutil.copytree(src / "schemas", tmp / "schemas")
        shutil.copytree(src.joinpath(*SLICE), tmp.joinpath(*SLICE))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        return tmp

    def _mutate(self, root: Path, name: str, fn) -> None:
        f = root.joinpath(*SLICE, name)
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        fn(data)
        f.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")

    def test_shipped_dossier_is_coherent(self):
        report = check_vertical_slice(find_repo_root())
        if report.get("informational"):
            self.skipTest(report.get("note", "deps unavailable"))
        self.assertTrue(report["ok"], report.get("violations"))
        self.assertGreaterEqual(report["instances_checked"], 6)

    def test_missing_dossier_is_not_run_and_blocking(self):
        report = check_vertical_slice(Path(tempfile.mkdtemp()))
        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "not_run")
        self.assertEqual(report.get("instances_checked"), 0)

    def test_register_not_project_scoped_is_rejected(self):
        root = self._tmp_root()
        self._mutate(root, "register_candidate.devis-reprise.yaml",
                     lambda d: d["scope"].__setitem__("scope_type", "repository"))
        report = check_vertical_slice(root)
        if report.get("informational"):
            self.skipTest("deps unavailable")
        self.assertFalse(report["ok"])
        self.assertTrue(any("project" in v["message"] for v in report["violations"]), report["violations"])

    def test_answer_status_not_referencing_pack_is_rejected(self):
        root = self._tmp_root()
        self._mutate(root, "answer_status.devis-reprise.yaml",
                     lambda d: d.__setitem__("evidence_refs", []))
        report = check_vertical_slice(root)
        if report.get("informational"):
            self.skipTest("deps unavailable")
        self.assertFalse(report["ok"])
        self.assertTrue(any("evidence pack" in v["message"] for v in report["violations"]), report["violations"])


if __name__ == "__main__":
    unittest.main()
