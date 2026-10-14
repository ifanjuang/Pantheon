"""Intake vocabularies raise consequence; they never lower it.

`classify_request` accepts the same signal from three places: a legacy
top-level field, a `conditions` entry, and an `observations` dict. Two of them
composed upward only. `observations` did not: `_semantic_bool` returned
`observations[name] is True` whenever the key was present, so an `observations`
entry of `False` overruled a `True` the request already carried.

That is not a cosmetic asymmetry. A request declaring `external_effect: True`
classified K4 with `blocked_until_gate: True`; adding
`observations: {"external_effect": False}` dropped it to K3 and removed the User
Decision Gate entirely. The same held for `transmission_requested`,
`memory_promotion_requested`, `professional_position`,
`financial_or_contractual_effect` and `writes_state`.

Hermes describes material conditions; it does not decide their consequence. A
described request must not be able to talk its way under the gate.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pantheon_mcp.policy import classify_request  # noqa: E402


# Every signal that reaches `classify_request` through both a legacy top-level
# field and an `observations` entry.
RAISING_SIGNALS = (
    "external_effect",
    "transmission_requested",
    "external_transmission",
    "memory_promotion_requested",
    "professional_position",
    "financial_or_contractual_effect",
    "writes_state",
)


class TestIntakeSignalComposition(unittest.TestCase):
    def test_an_observation_of_false_never_lowers_a_declared_signal(self):
        for name in RAISING_SIGNALS:
            declared = classify_request({"intent": "handle the request", name: True})
            with_denial = classify_request(
                {
                    "intent": "handle the request",
                    name: True,
                    "observations": {name: False},
                }
            )
            with self.subTest(signal=name):
                self.assertEqual(
                    declared["consequence_level"],
                    with_denial["consequence_level"],
                    f"observations[{name}]=False lowered the consequence level",
                )
                self.assertEqual(
                    declared["required_approval_ceiling"],
                    with_denial["required_approval_ceiling"],
                )
                self.assertEqual(
                    declared["blocked_until_gate"],
                    with_denial["blocked_until_gate"],
                    f"observations[{name}]=False removed the gate",
                )

    def test_an_observation_alone_still_raises(self):
        """Dropping the override must not cost `observations` its own voice."""
        for name in RAISING_SIGNALS:
            with self.subTest(signal=name):
                observed = classify_request(
                    {"intent": "handle the request", "observations": {name: True}}
                )
                declared = classify_request({"intent": "handle the request", name: True})
                self.assertEqual(
                    observed["consequence_level"], declared["consequence_level"]
                )

    def test_external_effect_unknown_remains_an_escalation_from_either_source(self):
        """`external_effect` is tri-state and "unknown" is itself K4."""
        for request in (
            {"intent": "handle the request", "external_effect": "unknown"},
            {
                "intent": "handle the request",
                "observations": {"external_effect": "unknown"},
            },
            {
                "intent": "handle the request",
                "external_effect": "unknown",
                "observations": {"external_effect": False},
            },
        ):
            with self.subTest(request=request):
                report = classify_request(request)
                self.assertEqual(report["consequence_level"], "K4")
                self.assertTrue(report["blocked_until_gate"])

    def test_declaring_nothing_is_unaffected(self):
        """The composition change must not inflate an ordinary request."""
        report = classify_request({"intent": "explain the phasing note"})
        self.assertEqual(report["consequence_level"], "K2")
        self.assertFalse(report["blocked_until_gate"])
        self.assertFalse(report["evidence_required"])

    def test_a_harmless_transformation_stays_k0(self):
        report = classify_request(
            {"intent": "tidy this paragraph", "requested_transformation": "rewrite"}
        )
        self.assertEqual(report["consequence_level"], "K0")
        self.assertFalse(report["blocked_until_gate"])


if __name__ == "__main__":
    unittest.main()
