"""Parity guard: the cockpit's verifyUpdateVerdict (JS) must agree with the
update.verify_update classifier (Python, the source of truth), including the
version parse/compare.

The verdict rules live in two places by necessity — the read-only tool and the
thin cockpit mirror (update-verify.js). This test replays a matrix of version
pairs through both implementations and asserts the same verdict, so the mirror
cannot drift silently. It is read-only: it evaluates the shipped JS in a sandboxed
node process with the DOM/helpers stubbed; it touches no system and writes
nothing. It skips gracefully when node is unavailable (best-effort locally) and
runs in CI where the ubuntu-latest runner ships node.
"""

import json
import shutil
import subprocess
import unittest
from itertools import product
from pathlib import Path

from pantheon_mcp import update

ROOT = Path(__file__).resolve().parents[2]
COCKPIT = ROOT / "docs" / "assets" / "pantheon-control"

# Version strings exercising equal, behind, ahead, v-prefix, pre-release, padding,
# empty and unparseable cases.
_VERSIONS = ["", "1.5.0", "1.5", "1.4.2", "2.0.0", "v1.5.0", "1.5.0-beta", "rolling"]

# verifyUpdateVerdict is a function declaration, reachable within the same eval
# scope; chip()/kv()/toast() are only used by render helpers we never call here.
_NODE_DRIVER = r"""
const fs = require('fs');
global.chip = () => ''; global.kv = () => ''; global.toast = () => {};
const base = process.argv[1];
const src = fs.readFileSync(base + '/update-verify.js', 'utf8')
          + '\nglobal.__verify = verifyUpdateVerdict;';
eval(src);
let input = '';
process.stdin.on('data', d => input += d);
process.stdin.on('end', () => {
  const states = JSON.parse(input);
  process.stdout.write(JSON.stringify(states.map(s => global.__verify(s).verdict)));
});
"""


def _state_to_evidence(s: dict) -> dict:
    ev = {"component": s.get("component", "x")}
    if s.get("current_version"):
        ev["current_version"] = s["current_version"]
    if s.get("available_version"):
        ev["available_version"] = s["available_version"]
    return ev


def _matrix() -> list[dict]:
    return [
        {"component": "x", "current_version": cur, "available_version": av}
        for cur, av in product(_VERSIONS, _VERSIONS)
    ]


class TestUpdateParity(unittest.TestCase):
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
            py = update.verify_update(_state_to_evidence(state))["verdict"]
            if py != js:
                mismatches.append((state, py, js))
        self.assertFalse(
            mismatches,
            "cockpit JS diverged from update.verify_update:\n"
            + "\n".join(f"  {s} -> python={p} js={j}" for s, p, j in mismatches[:10]),
        )


if __name__ == "__main__":
    unittest.main()
