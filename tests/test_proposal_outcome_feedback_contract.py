"""Regression checks for proposal -> human decision -> actual outcome feedback."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PLATFORM = ROOT / "docs" / "governance" / "DATA_PLATFORM_ARCHITECTURE.md"
EVALUATION = ROOT / "hermes" / "profiles" / "_base" / "EVALUATION_AND_SIMULATION_CANDIDATE.md"


def test_feedback_reuses_existing_proposal_approval_execution_and_audit_owners() -> None:
    platform = DATA_PLATFORM.read_text(encoding="utf-8")

    for owner_signal in (
        "workflow_action_proposals",
        "workflow_action_executions",
        "approval_records",
        "audit_events",
        "The platform records what was proposed, what was accepted, what was executed and what can be reversed.",
    ):
        assert owner_signal in platform


def test_feedback_metrics_are_derived_review_signals_not_new_authority() -> None:
    evaluation = EVALUATION.read_text(encoding="utf-8")

    for invariant in (
        "proposal_outcome_feedback",
        "using the records already owned by the data platform / approval / audit responsibilities rather than creating a second feedback ledger",
        "candidate/proposal identity and version",
        "human disposition or decision reference",
        "actual resulting object/effect reference",
        "later correction/reversal reference",
        "acceptance",
        "material override",
        "abstention / held / unresolved",
        "reformulation or reclassification",
        "proposal-to-decision duration",
        "later correction or reversal",
        "Do not treat a manually stamped outcome label as stronger than the underlying records",
        "Report the evaluated class, time window and sample size",
        "Read material disagreements individually",
        "must not automatically rewrite prompts, skills, policies, doctrine, routing, model bindings or memory",
        "metric != truth",
        "override != model error",
        "acceptance != Evidence",
        "feedback observation != memory promotion",
        "correlation != authorization",
    ):
        assert invariant in evaluation

    assert "proposal_outcome_feedback_records" not in evaluation
    assert "feedback_ledger" not in evaluation
