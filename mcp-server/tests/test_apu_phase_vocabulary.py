"""Read-only tests for the phase check in the APU validator.

A declared phase code is governable, not true, admitted, Evidence or approved,
and it does not mean that a project goes through that phase. Nothing here
executes, persists or canonizes.
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


def _requirement(phase: str, requirement_id: str = "REQ-1") -> dict:
    return {
        "requirement_id": requirement_id,
        "human_ref": "Hauteur sous plafond minimale",
        "source": {"source_type": "document", "source_ref": "DOC-programme"},
        "requirement_kind": "attribute",
        "target": {"selector": {"object_family": "spatial"}},
        "constraint": {
            "operator": "min",
            "expected_value": {"value_type": "number", "value": 2.5, "unit": "m"},
        },
        "scope_type": "project",
        "scope_id": "PRJ-1",
        "source_authority": "approved_client_decision",
        "proof_status": "candidate",
        "validity": {"project_phase": phase},
    }


def _report(*phases: str) -> dict:
    return apu.validate_apu_dossier(
        {"requirement": [_requirement(phase, f"REQ-{i}") for i, phase in enumerate(phases)]}
    )


class TestPhaseVocabulary(unittest.TestCase):
    def setUp(self):
        patch = mock.patch.dict(os.environ)
        patch.start()
        self.addCleanup(patch.stop)
        os.environ.pop(apu.PHASE_OVERLAY_ENV, None)

    def _agency_file(self, *entries: dict) -> str:
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        self.addCleanup(os.unlink, handle.name)
        json.dump(
            {"registry_kind": "vocabulary_overlay",
             "extends": "architecture_phase_profile", "entries": list(entries)},
            handle,
        )
        handle.close()
        return handle.name

    def test_declared_phases_including_esq_are_accepted(self):
        report = _report("ESQ", "APS", "DCE", "AOR")
        self.assertEqual(report["vocabulary_errors"], [], report)
        self.assertEqual(report["schema_errors"], [], report)

    def test_undeclared_phase_is_rejected_and_blocks_emission(self):
        report = _report("ESQ", "ESQUISSE")
        self.assertEqual(report["result"], "error")
        self.assertEqual(
            report["vocabulary_errors"],
            ["requirement[1].validity.project_phase 'ESQUISSE' is not declared in the phase vocabulary"],
        )
        self.assertFalse(report["gate"]["canonical_emission_allowed"])

    def test_malformed_phase_is_a_schema_error(self):
        report = _report("esq")
        self.assertEqual(report["result"], "error")
        self.assertTrue(report["schema_errors"], report)

    def test_agency_phase_is_accepted_and_a_candidate_one_needs_review(self):
        os.environ[apu.PHASE_OVERLAY_ENV] = self._agency_file(
            {"id": "FAISA", "status": "candidate", "category": "mission_element",
             "label": "Faisabilité", "description": "Étude de faisabilité."}
        )
        report = _report("FAISA")
        self.assertEqual(report["vocabulary_errors"], [], report)
        self.assertIn(
            "requirement[0].validity.project_phase 'FAISA' is still a candidate phase code",
            report["gate"]["human_decisions_required"],
        )

    def test_broken_agency_file_makes_the_vocabulary_unavailable(self):
        os.environ[apu.PHASE_OVERLAY_ENV] = self._agency_file(
            {"id": "ESQ", "status": "active", "category": "mission_element",
             "label": "Esquisse", "description": "Redéclaration."}
        )
        report = _report("ESQ")
        self.assertEqual(report["result"], "error")
        self.assertTrue(
            any(error.startswith("phase vocabulary unavailable") for error in report["vocabulary_errors"]),
            report,
        )


if __name__ == "__main__":
    unittest.main()
