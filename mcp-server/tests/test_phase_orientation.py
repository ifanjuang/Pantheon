"""Read-only tests for the phase orientation tool.

The answer orients a reader on the main subjects of a phase. It computes no
status, checks no completeness and requires nothing.
"""

import json
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("PANTHEON_REPO_PATH", str(ROOT))

from pantheon_mcp import phase_orientation, server  # noqa: E402


class TestPhaseOrientation(unittest.TestCase):
    def test_a_covered_phase_returns_its_block_and_gate_risk(self):
        result = phase_orientation.phase_orientation("act", ROOT)
        self.assertTrue(result["found"])
        self.assertEqual(result["phase"], "ACT")
        self.assertEqual(result["block"], "DCE_ACT")
        self.assertEqual(result["block_phases"], ["DCE", "ACT"])
        self.assertEqual(result["gate_risk"], "devis ou marché utilisé avant signature ou attribution")
        self.assertTrue(result["advisory"])

    def test_a_phase_without_a_block_is_not_an_error(self):
        result = phase_orientation.phase_orientation("AGENCY_LIBRARY", ROOT)
        self.assertFalse(result["found"])
        self.assertNotIn("deliverables", result)

    def test_the_tool_answers_without_any_effect(self):
        result = json.loads(server.get_phase_orientation("PRO"))
        self.assertEqual(result["operation"], "architecture.phase_orientation")
        self.assertEqual(result["authority_effect"], "none")
        self.assertFalse(result["write_effect"])
        self.assertFalse(result["execution_effect"])
        self.assertIn("CCTP", result["deliverables"])


if __name__ == "__main__":
    unittest.main()
