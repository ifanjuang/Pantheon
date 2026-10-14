"""Parity guard: the cockpit's verifyExposureVerdict (JS) must agree with the
exposure.verify_exposure classifier (Python, the source of truth).

The verdict rules live in two places by necessity — the read-only tool and the
thin cockpit mirror (exposure-verify.js). This test replays a matrix of cockpit
input states through both implementations and asserts the same verdict, so the
mirror cannot drift silently. It is read-only: it evaluates the shipped JS in a
sandboxed node process with the DOM/helpers stubbed; it touches no system and
writes nothing. It skips gracefully when node is unavailable (best-effort
locally) and runs in CI where the ubuntu-latest runner ships node.
"""

import json
import shutil
import subprocess
import unittest
from itertools import product
from pathlib import Path

from pantheon_mcp import exposure

ROOT = Path(__file__).resolve().parents[2]
COCKPIT = ROOT / "docs" / "assets" / "pantheon-control"

_REACH = ["inconnu", "local", "vpn", "public"]
_TRISTATE = ["inconnu", "oui", "non"]

# verifyExposureVerdict is a function declaration, reachable within the same eval
# scope; chip()/kv()/toast() are only used by render helpers we never call here.
_NODE_DRIVER = r"""
const fs = require('fs');
global.chip = () => ''; global.kv = () => ''; global.toast = () => {};
const base = process.argv[1];
const src = fs.readFileSync(base + '/exposure-verify.js', 'utf8')
          + '\nglobal.__verify = verifyExposureVerdict;';
eval(src);
let input = '';
process.stdin.on('data', d => input += d);
process.stdin.on('end', () => {
  const states = JSON.parse(input);
  process.stdout.write(JSON.stringify(states.map(s => global.__verify(s).verdict)));
});
"""


def _state_to_evidence(s: dict) -> dict:
    """Faithful mapping from the cockpit exposure form to verify_exposure evidence."""
    ev: dict = {"component": s.get("component", "x")}
    if s["reach"] in ("local", "vpn", "public"):
        ev["reach"] = s["reach"]
    if s["auth"] == "oui":
        ev["auth"] = {"enforced": True}
    elif s["auth"] == "non":
        ev["auth"] = {"enforced": False}
    if s["scope"] == "oui":
        ev["scope"] = {"limited": True}
    elif s["scope"] == "non":
        ev["scope"] = {"limited": False}
    return ev


def _matrix() -> list[dict]:
    return [
        {"component": "x", "reach": rc, "auth": a, "scope": sc}
        for rc, a, sc in product(_REACH, _TRISTATE, _TRISTATE)
    ]


class TestExposureParity(unittest.TestCase):
    def test_js_mirror_matches_python_classifier(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node not available; parity is enforced in CI (ubuntu-latest ships node)")

        states = _matrix()
        proc = subprocess.run(
            [node, "-e", _NODE_DRIVER, str(COCKPIT)],
            input=json.dumps(states),
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        js_verdicts = json.loads(proc.stdout)
        self.assertEqual(len(js_verdicts), len(states))

        mismatches = []
        for state, js in zip(states, js_verdicts):
            py = exposure.verify_exposure(_state_to_evidence(state))["verdict"]
            if py != js:
                mismatches.append((state, py, js))
        self.assertFalse(
            mismatches,
            "cockpit JS diverged from exposure.verify_exposure:\n"
            + "\n".join(f"  {s} -> python={p} js={j}" for s, p, j in mismatches[:10]),
        )


if __name__ == "__main__":
    unittest.main()
