"""Parity guard: the cockpit's verifyObservabilityVerdict (JS) must agree with
the observability.verify_observability classifier (Python, the source of truth).

The verdict rules live in two places by necessity — the read-only tool and the
thin cockpit mirror (observability-verify.js). This test replays a matrix of
cockpit input states through both implementations and asserts the same verdict,
so the mirror cannot drift silently. It is read-only: it evaluates the shipped JS
in a sandboxed node process with the DOM/helpers stubbed; it touches no system
and writes nothing. It skips gracefully when node is unavailable (best-effort
locally) and runs in CI where the ubuntu-latest runner ships node.
"""

import json
import shutil
import subprocess
import unittest
from itertools import product
from pathlib import Path

from pantheon_mcp import observability

ROOT = Path(__file__).resolve().parents[2]
COCKPIT = ROOT / "docs" / "assets" / "pantheon-control"

_SIGNALS = ["inconnu", "tous", "partiel", "aucun"]
_FRESH = ["inconnu", "oui", "non"]
_ERRORS = ["inconnu", "ok", "depasse"]

# verifyObservabilityVerdict is a function declaration, reachable within the same
# eval scope; chip()/toast() are only used by render helpers we never call here.
_NODE_DRIVER = r"""
const fs = require('fs');
global.chip = () => ''; global.toast = () => {};
const base = process.argv[1];
const src = fs.readFileSync(base + '/observability-verify.js', 'utf8')
          + '\nglobal.__verify = verifyObservabilityVerdict;';
eval(src);
let input = '';
process.stdin.on('data', d => input += d);
process.stdin.on('end', () => {
  const states = JSON.parse(input);
  process.stdout.write(JSON.stringify(states.map(s => global.__verify(s).verdict)));
});
"""


def _state_to_evidence(s: dict) -> dict:
    """Faithful mapping from the cockpit observability form to verify_observability
    evidence."""
    ev: dict = {"component": s.get("component", "x")}
    if s["signals"] == "tous":
        ev["signals"] = [{"name": "logs", "present": True}, {"name": "metrics", "present": True}]
        ev["expected_signals"] = ["logs", "metrics"]
    elif s["signals"] == "partiel":
        ev["signals"] = [{"name": "logs", "present": True}, {"name": "metrics", "present": False}]
        ev["expected_signals"] = ["logs", "metrics"]
    elif s["signals"] == "aucun":
        ev["signals"] = [{"name": "logs", "present": False}, {"name": "metrics", "present": False}]
        ev["expected_signals"] = ["logs", "metrics"]
    if s["fresh"] == "oui":
        ev["freshness"] = {"last_event_age_s": 10, "max_age_s": 60}
    elif s["fresh"] == "non":
        ev["freshness"] = {"last_event_age_s": 600, "max_age_s": 60}
    if s["errors"] == "ok":
        ev["errors"] = {"count": 0, "threshold": 5}
    elif s["errors"] == "depasse":
        ev["errors"] = {"count": 10, "threshold": 5}
    return ev


def _matrix() -> list[dict]:
    return [
        {"component": "x", "signals": sig, "fresh": fr, "errors": er}
        for sig, fr, er in product(_SIGNALS, _FRESH, _ERRORS)
    ]


class TestObservabilityParity(unittest.TestCase):
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
            py = observability.verify_observability(_state_to_evidence(state))["verdict"]
            if py != js:
                mismatches.append((state, py, js))
        self.assertFalse(
            mismatches,
            "cockpit JS diverged from observability.verify_observability:\n"
            + "\n".join(f"  {s} -> python={p} js={j}" for s, p, j in mismatches[:10]),
        )


if __name__ == "__main__":
    unittest.main()
