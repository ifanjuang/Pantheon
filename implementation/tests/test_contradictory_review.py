"""Contradictory review implementation contract tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from mvp_vertical.contradictory_review import (
    AnalogousOccurrence,
    ContradictoryReviewReport,
    ReviewClaim,
    ReviewObservation,
    report_from_payload,
)

ROOT = Path(__file__).resolve().parents[1]
COMPILER = ROOT / "scripts" / "compile_contradictory_review.py"


def _claim(claim_id: str = "claim-1") -> ReviewClaim:
    return ReviewClaim(
        claim_id=claim_id,
        statement="The implementation matches the declared contract.",
        kind="fact",
        source_refs=("contract.md",),
    )


def _observation(
    *,
    claim_id: str = "claim-1",
    support_status: str = "supported",
    severity: str = "notice",
    fresh_observation: bool = True,
) -> ReviewObservation:
    return ReviewObservation(
        observation_id=f"obs-{claim_id}-{support_status}",
        claim_id=claim_id,
        support_status=support_status,
        severity=severity,
        method="rerun declared check",
        detail="The observed output was compared with the declared claim.",
        artifact_refs=("test-output.txt",),
        fresh_observation=fresh_observation,
    )


def _report(**overrides) -> ContradictoryReviewReport:
    values = {
        "task_contract_ref": "task-contract-42",
        "trigger_reason": "candidate output is consequential",
        "proposed_by": "THEMIS",
        "authorized_by": "ZEUS:rite_allowed",
        "review_mode": "mode_full",
        "review_posture": "independent_review",
        "candidate_id": "candidate-7",
        "candidate_digest": "sha256:candidate",
        "binding_id": "hermes-contradictory-review",
        "binding_version": "0.1.0",
        "execution_id": "run-19",
        "claims": (_claim(),),
        "observations": (_observation(),),
    }
    values.update(overrides)
    return ContradictoryReviewReport(**values)


def test_complete_independent_review_produces_trace_and_review_card_candidate():
    payload = _report().as_dict()

    assert payload["status"] == "review_completed"
    assert payload["trace"]["trace_type"] == "contradictory_review_observation"
    assert payload["trace"]["write_effect"] is False
    assert payload["rite_review_card"]["ZEUS_status_candidate"] == "rite_completed_as_draft"
    assert payload["rite_review_card"]["next_allowed_action"] == "request_zeus_closure"
    assert payload["authority"] == {
        "is_evidence": False,
        "is_approval": False,
        "is_zeus_closure": False,
        "is_task_authorization": False,
        "requires_zeus_closure": True,
    }


def test_contradiction_and_blocking_observation_do_not_approve_or_repair():
    report = _report(
        observations=(
            _observation(support_status="contradicted", severity="blocking"),
        ),
        analogous_occurrences=(
            AnalogousOccurrence(
                occurrence_id="occ-1",
                pattern="same stale route",
                location="module/other.py",
                status="candidate",
                detail="Candidate analogous occurrence inside the authorized repository scope.",
            ),
        ),
    ).as_dict()

    assert report["status"] == "review_blocked"
    assert report["rite_review_card"]["blocked_claims"] == ["claim-1"]
    assert report["rite_review_card"]["User_Decision_Gate"] is True
    assert report["rite_review_card"]["next_allowed_action"] == "zeus_or_human_review"
    assert report["authority"]["is_approval"] is False
    assert report["analogous_occurrences"][0]["status"] == "candidate"


def test_missing_or_non_fresh_observations_remain_visible_as_limits():
    no_observation = _report(observations=()).as_dict()
    stale_observation = _report(
        observations=(_observation(fresh_observation=False),),
    ).as_dict()

    assert no_observation["status"] == "review_inconclusive"
    assert stale_observation["status"] == "review_completed_with_reserve"
    assert stale_observation["rite_review_card"]["ZEUS_status_candidate"] == "rite_completed_with_reserve"


def test_report_identity_is_deterministic_and_context_bound():
    baseline = _report()
    same = _report()
    changed_candidate = _report(candidate_digest="sha256:other")
    changed_observation = _report(
        observations=(_observation(support_status="partially_supported", severity="warning"),),
    )

    assert baseline.review_id == same.review_id
    assert baseline.review_id != changed_candidate.review_id
    assert baseline.review_id != changed_observation.review_id


def test_independent_review_rejects_repair_scope_expansion_and_unknown_claims():
    with pytest.raises(ValueError, match="cannot repair"):
        _report(repair_applied=True)
    with pytest.raises(ValueError, match="cannot expand task scope"):
        _report(scope_expanded=True)
    with pytest.raises(ValueError, match="unknown claims"):
        _report(observations=(_observation(claim_id="missing"),))


def test_payload_rejects_another_rite_and_keeps_authorization_assertion_non_authoritative():
    payload = {
        "rite_id": "RITE_DIVERGENCE_CONTROLEE",
        "task_contract_ref": "task-1",
    }
    with pytest.raises(ValueError, match="unsupported rite_id"):
        report_from_payload(payload)


def test_compiler_accepts_bounded_json_and_rejects_independent_repair(tmp_path: Path):
    base = {
        "rite_id": "AUTOCRITIQUE_CONTRADICTOIRE",
        "task_contract_ref": "task-contract-42",
        "trigger_reason": "delivery review",
        "proposed_by": "THEMIS",
        "authorized_by": "ZEUS:rite_allowed",
        "review_mode": "mode_standard",
        "review_posture": "independent_review",
        "candidate_id": "candidate-7",
        "candidate_digest": "sha256:candidate",
        "binding_id": "hermes-contradictory-review",
        "binding_version": "0.1.0",
        "execution_id": "run-19",
        "claims": [
            {
                "claim_id": "claim-1",
                "statement": "The check passes.",
                "kind": "fact",
                "source_refs": ["report.md"],
            }
        ],
        "observations": [
            {
                "observation_id": "obs-1",
                "claim_id": "claim-1",
                "support_status": "supported",
                "severity": "notice",
                "method": "rerun",
                "detail": "Observed pass.",
                "artifact_refs": ["output.txt"],
                "fresh_observation": True,
            }
        ],
    }
    input_path = tmp_path / "review.json"
    input_path.write_text(json.dumps(base), encoding="utf-8")

    accepted = subprocess.run(
        [sys.executable, str(COMPILER), str(input_path)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert accepted.returncode == 0, accepted.stderr
    compiled = json.loads(accepted.stdout)
    assert compiled["status"] == "review_completed"
    assert compiled["authority"]["is_zeus_closure"] is False

    base["repair_applied"] = True
    input_path.write_text(json.dumps(base), encoding="utf-8")
    rejected = subprocess.run(
        [sys.executable, str(COMPILER), str(input_path)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert rejected.returncode == 2
    assert "cannot repair" in rejected.stderr
