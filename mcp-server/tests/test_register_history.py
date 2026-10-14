"""Adversarial tests for Register Candidate history coherence."""

from __future__ import annotations

import unittest

from pantheon_mcp.register_history import check_register_history, evaluate_register_history


def _candidate(
    candidate_id: str,
    *,
    claim: str = "The courtyard facade finish is zinc.",
    created_at: str = "2026-06-01T09:00:00Z",
    status: str = "candidate",
    scope_id: str = "project-alpha",
    supersedes: str | None = None,
) -> dict:
    candidate = {
        "candidate_id": candidate_id,
        "created_at": created_at,
        "claim": claim,
        "status": status,
        "scope": {"scope_type": "project", "scope_id": scope_id},
    }
    if supersedes is not None:
        candidate["supersedes_candidate_id"] = supersedes
    return candidate


class RegisterHistoryTests(unittest.TestCase):
    def test_repository_example_history_is_coherent(self) -> None:
        result = check_register_history()
        self.assertTrue(result["ok"], result)
        self.assertGreaterEqual(result["candidates_checked"], 6)

    def test_silent_reappearance_of_rejected_claim_is_refused(self) -> None:
        candidates = [
            _candidate("r1", status="rejected"),
            _candidate("r2", created_at="2026-06-02T09:00:00Z"),
        ]
        violations = evaluate_register_history(candidates)
        self.assertTrue(any("silently resurrects rejected candidate r1" in v for v in violations))

    def test_explicit_reconsideration_of_rejected_claim_is_allowed(self) -> None:
        candidates = [
            _candidate("r1", status="rejected"),
            _candidate(
                "r2",
                created_at="2026-06-02T09:00:00Z",
                status="under_review",
                supersedes="r1",
            ),
        ]
        self.assertEqual(evaluate_register_history(candidates), [])

    def test_approved_supersession_chain_is_coherent(self) -> None:
        candidates = [
            _candidate(
                "s1",
                claim="The roof finish is natural slate.",
                status="superseded",
            ),
            _candidate(
                "s2",
                claim="The roof finish is pre-weathered zinc.",
                created_at="2026-06-03T09:00:00Z",
                status="approved",
                supersedes="s1",
            ),
        ]
        self.assertEqual(evaluate_register_history(candidates), [])

    def test_unknown_supersession_reference_is_refused(self) -> None:
        violations = evaluate_register_history([
            _candidate("s2", status="under_review", supersedes="missing")
        ])
        self.assertTrue(any("unknown candidate 'missing'" in v for v in violations))

    def test_self_supersession_is_refused(self) -> None:
        violations = evaluate_register_history([
            _candidate("s1", supersedes="s1")
        ])
        self.assertTrue(any("cannot supersede itself" in v for v in violations))

    def test_supersession_must_move_forward_in_time(self) -> None:
        candidates = [
            _candidate("s1", created_at="2026-06-03T09:00:00Z"),
            _candidate(
                "s2",
                created_at="2026-06-02T09:00:00Z",
                supersedes="s1",
            ),
        ]
        violations = evaluate_register_history(candidates)
        self.assertTrue(any("must be created after" in v for v in violations))

    def test_supersession_cannot_cross_scope(self) -> None:
        candidates = [
            _candidate("s1", scope_id="project-alpha"),
            _candidate(
                "s2",
                created_at="2026-06-02T09:00:00Z",
                scope_id="project-beta",
                supersedes="s1",
            ),
        ]
        violations = evaluate_register_history(candidates)
        self.assertTrue(any("across different scopes" in v for v in violations))

    def test_approved_successor_cannot_leave_active_predecessor(self) -> None:
        candidates = [
            _candidate("s1", status="approved"),
            _candidate(
                "s2",
                created_at="2026-06-02T09:00:00Z",
                status="approved",
                supersedes="s1",
            ),
        ]
        violations = evaluate_register_history(candidates)
        self.assertTrue(any("cannot leave predecessor s1 in active status 'approved'" in v for v in violations))

    def test_superseded_candidate_requires_approved_successor(self) -> None:
        candidates = [
            _candidate("s1", status="superseded"),
            _candidate(
                "s2",
                created_at="2026-06-02T09:00:00Z",
                status="under_review",
                supersedes="s1",
            ),
        ]
        violations = evaluate_register_history(candidates)
        self.assertTrue(any("has no approved successor" in v for v in violations))

    def test_supersession_cycle_is_refused(self) -> None:
        candidates = [
            _candidate("s1", supersedes="s2"),
            _candidate("s2", created_at="2026-06-02T09:00:00Z", supersedes="s1"),
        ]
        violations = evaluate_register_history(candidates)
        self.assertTrue(any("supersession cycle detected" in v for v in violations))


if __name__ == "__main__":
    unittest.main()
