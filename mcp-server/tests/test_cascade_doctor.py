"""Read-only tests for the cascade-rule doctor check.

The check flags; it never edits, fixes or decides. These tests validate the
declarative rule and the example instance only.
"""

from __future__ import annotations

from pantheon_mcp.doctor import (
    check_cascade_rule,
    check_register_instances,
    evaluate_impact_review,
    run_all,
)


def test_example_impact_review_passes() -> None:
    result = check_cascade_rule()
    assert result["ok"], result
    assert result.get("instances_checked", 0) >= 1


def test_critical_must_route_to_arbitration() -> None:
    bad = {
        "impact_review_id": "x",
        "trigger_id": "P-1",
        "trigger_change": "validated",
        "status": "open",
        "impacted": [
            {"target_id": "P-2", "severity": "critical", "impact_status": "supersede", "decision": "pending"}
        ],
    }
    violations = evaluate_impact_review(bad)
    assert any("critical" in v for v in violations), violations


def test_resolved_requires_recorded_decisions() -> None:
    bad = {
        "status": "resolved",
        "impacted": [
            {"target_id": "P-2", "severity": "high", "impact_status": "revalidate", "decision": "pending"}
        ],
    }
    violations = evaluate_impact_review(bad)
    assert any("resolved" in v for v in violations), violations


def test_well_formed_review_has_no_violation() -> None:
    good = {
        "status": "open",
        "impacted": [
            {"target_id": "P-2", "severity": "critical", "impact_status": "critical_arbitration", "decision": "pending"}
        ],
    }
    assert evaluate_impact_review(good) == []


def test_run_all_includes_cascade_rule() -> None:
    result = run_all()
    assert any(c["check"] == "cascade_rule" for c in result["checks"])


def test_register_instances_dossier_is_coherent() -> None:
    result = check_register_instances()
    assert result["ok"], result
    # the cascade_register dossier carries candidates, links and a review
    assert result.get("instances_checked", 0) >= 5


def test_run_all_includes_register_instances() -> None:
    result = run_all()
    assert any(c["check"] == "register_instances" for c in result["checks"])


def test_missing_register_schemas_is_not_run_and_blocking(tmp_path) -> None:
    instances = tmp_path / "docs" / "examples" / "cascade_register"
    instances.mkdir(parents=True)
    (instances / "candidate.yaml").write_text(
        "candidate_id: P-1\nlink_ids:\n  - L-does-not-exist\n", encoding="utf-8"
    )
    result = check_register_instances(tmp_path)
    assert not result["ok"]
    assert result["status"] == "not_run"
    assert result["missing_schemas"]
