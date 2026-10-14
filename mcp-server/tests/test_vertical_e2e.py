"""ASSERT-style regression for the proven vertical (TARGET_ARCHITECTURE step 4).

Runs the Hermes-side conformance runner as a subprocess over the real MCP
stdio protocol on the Résidence Les Tilleuls fixture and asserts the run
ends at the gate with a conformant envelope. Skips cleanly when the MCP
SDK is not installed (the governance CI does not install it).
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[1]
RUNNER = MODULE_DIR / "examples" / "hermes_vertical_runner.py"


def _mcp_available() -> bool:
    try:
        import mcp  # noqa: F401
        import jsonschema  # noqa: F401
        return True
    except ImportError:
        return False


@unittest.skipUnless(_mcp_available(), "mcp SDK / jsonschema not installed")
class TestVerticalEndToEnd(unittest.TestCase):
    def test_tilleuls_vertical_passes_and_stops_at_gate(self):
        proc = subprocess.run(
            [sys.executable, str(RUNNER)],
            capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])
        out = proc.stdout
        for marker in (
            "[classify] K4/V4/C4",
            "Evidence Pack candidate validates against schemas/evidence_pack.schema.yaml",
            "Register candidate validates against schemas/register_candidate.schema.yaml",
            "[refusal] refused",
            "[external] blocked_by_default confirmed",
            "STOPPED at the User Decision Gate",
            "VERTICAL CONFORMANCE: PASS",
        ):
            self.assertIn(marker, out, f"missing marker: {marker}")
        # Structural check on the envelope: the run stopped at the gate and
        # the external effects are listed as forbidden, not performed.
        import json
        envelope = json.loads(out[out.index("{"): out.rindex("}") + 1])
        gate = envelope["USER_DECISION_GATE"]
        self.assertTrue(gate["stopped_here"])
        self.assertIn("letter sent to the purchaser", gate["forbidden"])
        self.assertIn("candidate", envelope["STATUS"])
        self.assertEqual(envelope["APPROVAL_NEEDED"], "C4")


if __name__ == "__main__":
    unittest.main()
