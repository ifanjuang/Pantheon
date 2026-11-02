"""Read-only tests for the source kind check in the APU validator.

A declared source kind is governable, not true, admitted, Evidence or approved,
and it does not mean that a reader exists for it. Nothing here executes,
persists or canonizes.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("PANTHEON_REPO_PATH", str(ROOT))

from pantheon_mcp import apu  # noqa: E402


def _representation(kind: str, representation_id: str = "REP-1") -> dict:
    return {
        "representation_id": representation_id,
        "project_ref": "PRJ-1",
        "source_artifact_ref": "CCTP-lot-04.pdf",
        "source_kind": kind,
        "identifiers": [{"scheme": "document.fragment", "value": representation_id}],
        "observed_at": "2026-11-02T09:00:00Z",
        "binding_ref": "fixture.document",
        "adapter_version": "1.0",
        "freshness_token": "sha256:abc",
        "proof_status": "candidate",
    }


def _report(*kinds: str) -> dict:
    return apu.validate_apu_dossier(
        {"source_representation": [_representation(kind, f"REP-{i}") for i, kind in enumerate(kinds)]}
    )


class TestSourceKindVocabulary(unittest.TestCase):
    def setUp(self):
        patch = mock.patch.dict(os.environ)
        patch.start()
        self.addCleanup(patch.stop)
        os.environ.pop(apu.SOURCE_KIND_OVERLAY_ENV, None)

    def _agency_file(self, *entries: dict) -> str:
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        self.addCleanup(os.unlink, handle.name)
        json.dump(
            {"registry_kind": "vocabulary_overlay",
             "extends": "architecture_source_kind_profile", "entries": list(entries)},
            handle,
        )
        handle.close()
        return handle.name

    def test_declared_kinds_including_written_documents_are_accepted(self):
        report = _report("document", "email", "cad_drawing", "ifc", "other")
        self.assertEqual(report["result"], "ok", report)
        self.assertEqual(report["vocabulary_errors"], [])

    def test_undeclared_kind_is_rejected_and_blocks_emission(self):
        report = _report("document", "bordereau")
        self.assertEqual(report["result"], "error")
        self.assertEqual(
            report["vocabulary_errors"],
            ["source_representation[1].source_kind 'bordereau' is not declared in the source kind vocabulary"],
        )
        self.assertFalse(report["gate"]["canonical_emission_allowed"])

    def test_malformed_kind_is_a_schema_error(self):
        report = _report("Document")
        self.assertEqual(report["result"], "error")
        self.assertTrue(report["schema_errors"], report)

    def test_agency_kind_is_accepted_through_the_local_file(self):
        os.environ[apu.SOURCE_KIND_OVERLAY_ENV] = self._agency_file(
            {"id": "plan_recolement", "status": "active", "label": "Plan de récolement",
             "description": "Plan fourni par l'entreprise."}
        )
        report = _report("plan_recolement", "document")
        self.assertEqual(report["result"], "ok", report)

    def test_candidate_agency_kind_passes_with_a_review_note(self):
        os.environ[apu.SOURCE_KIND_OVERLAY_ENV] = self._agency_file(
            {"id": "plan_recolement", "status": "candidate", "label": "Plan de récolement",
             "description": "Plan fourni par l'entreprise."}
        )
        report = _report("plan_recolement")
        self.assertEqual(report["result"], "ok", report)
        self.assertTrue(
            any("'plan_recolement' is still a candidate kind" in item
                for item in report["gate"]["human_decisions_required"]),
            report["gate"],
        )

    def test_agency_file_cannot_redeclare_a_repository_kind(self):
        os.environ[apu.SOURCE_KIND_OVERLAY_ENV] = self._agency_file(
            {"id": "document", "status": "active", "label": "Document", "description": "Autre sens."}
        )
        report = _report("document")
        self.assertEqual(report["result"], "error")
        self.assertTrue(
            any("redeclares 'document'" in item and "add-only" in item
                for item in report["vocabulary_errors"]),
            report["vocabulary_errors"],
        )

    def test_unreadable_agency_file_fails_closed_instead_of_being_ignored(self):
        os.environ[apu.SOURCE_KIND_OVERLAY_ENV] = "/nonexistent/source-kinds.json"
        report = _report("document")
        self.assertEqual(report["result"], "error")
        self.assertTrue(
            any("source kind vocabulary unavailable" in item for item in report["vocabulary_errors"]),
            report["vocabulary_errors"],
        )

    def test_missing_registry_fails_closed(self):
        with mock.patch.object(apu, "SOURCE_KIND_PROFILE_PATH", "registries/missing.registry.json"):
            report = _report("document")
        self.assertEqual(report["result"], "error")
        self.assertTrue(
            any("source kind vocabulary unavailable" in item for item in report["vocabulary_errors"]),
            report["vocabulary_errors"],
        )

    def test_deprecated_kind_is_rejected_with_its_replacement(self):
        base = {"entries": [
            {"id": "document", "status": "active", "label": "x", "description": "x"},
            {"id": "ancien", "status": "deprecated", "label": "x", "description": "x", "replaced_by": "document"},
        ]}
        kinds = {entry["id"]: entry for entry in base["entries"]}
        errors, notes = apu.source_kind_findings(kinds, "ancien", label="source_representation[0]")
        self.assertEqual(errors, ["source_representation[0].source_kind 'ancien' is deprecated; use 'document'"])
        self.assertEqual(notes, [])


if __name__ == "__main__":
    unittest.main()
