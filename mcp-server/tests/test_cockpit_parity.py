"""Parity guard: the cockpit's verifyInstallVerdict (JS) must agree with the
install.verify_install classifier (Python, the source of truth) on the verdict.

The verdict rules live in two places by necessity — the read-only tool and the
thin cockpit mirror. This test replays a matrix of cockpit input states through
both implementations and asserts the same verdict, so the mirror cannot drift
silently. It is read-only: it evaluates the shipped JS in a sandboxed node
process with the DOM/helpers stubbed; it touches no system and writes nothing.

It skips gracefully when node is unavailable (best-effort locally), and runs in
CI where the ubuntu-latest runner ships node.
"""

import json
import shutil
import subprocess
import unittest
from itertools import product
from pathlib import Path

from pantheon_mcp import install

ROOT = Path(__file__).resolve().parents[2]
COCKPIT = ROOT / "docs" / "assets" / "pantheon-control"

_TRISTATE = ["oui", "non", "inconnu"]
_CHECKS = ["verts", "rouge", "inconnu"]
_CODES = ["", "200", "503"]

# Single node driver: load the shipped cockpit scripts with helpers stubbed,
# then map each cockpit state to its JS verdict. verifyInstallVerdict is a
# function declaration, so it is reachable within the same eval scope.
_NODE_DRIVER = r"""
const fs = require('fs');
global.chip = () => ''; global.kv = () => ''; global.toast = () => {}; global.panel = () => '';
const base = process.argv[1];
const src = fs.readFileSync(base + '/installations-data.js', 'utf8') + '\n'
          + fs.readFileSync(base + '/installations-ui.js', 'utf8')
          + '\nglobal.__verify = verifyInstallVerdict;';
eval(src);
let input = '';
process.stdin.on('data', d => input += d);
process.stdin.on('end', () => {
  const states = JSON.parse(input);
  process.stdout.write(JSON.stringify(states.map(s => global.__verify(s).verdict)));
});
"""


def _state_to_evidence(s: dict) -> dict:
    """Faithful mapping from a cockpit tri-state form to verify_install evidence."""
    ev: dict = {"component": s.get("component", "x")}
    if s["installed"] == "oui":
        ev["installed"] = True
    elif s["installed"] == "non":
        ev["installed"] = False
    if s["reachable"] in ("oui", "non"):
        health = {"reachable": s["reachable"] == "oui"}
        code = (s.get("status_code") or "").strip()
        if code:
            health["status_code"] = int(code)
        ev["health"] = health
    if s["checks"] == "verts":
        ev["checks"] = [{"name": "health", "status": "green"}]
        ev["expected_checks"] = ["health"]
    elif s["checks"] == "rouge":
        ev["checks"] = [{"name": "health", "status": "red"}]
    return ev


def _matrix() -> list[dict]:
    states = []
    for installed, reachable, code, checks in product(_TRISTATE, _TRISTATE, _CODES, _CHECKS):
        states.append(
            {
                "component": "x",
                "installed": installed,
                "reachable": reachable,
                "status_code": code,
                "checks": checks,
            }
        )
    return states


class TestCockpitParity(unittest.TestCase):
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
            py = install.verify_install(_state_to_evidence(state))["verdict"]
            if py != js:
                mismatches.append((state, py, js))
        self.assertFalse(
            mismatches,
            "cockpit JS diverged from install.verify_install:\n"
            + "\n".join(f"  {s} -> python={p} js={j}" for s, p, j in mismatches[:10]),
        )


if __name__ == "__main__":
    unittest.main()
