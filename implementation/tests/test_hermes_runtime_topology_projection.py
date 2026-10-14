from __future__ import annotations

import pytest

from mvp_vertical.hermes_runtime_topology_projection import (
    HermesRuntimeTopologyProjectionError,
    HermesRuntimeTopologyProjector,
)


def test_projects_only_explicit_runtime_subagent_relationships() -> None:
    projector = HermesRuntimeTopologyProjector("run_12345678")
    event = {
        "event": "subagent.start",
        "run_id": "run_12345678",
        "timestamp": 10.5,
        "subagent_id": "sa-0-abcd1234",
        "child_session_id": "child-session-1",
        "delegation_id": "dg-1",
        "parent_id": "sa-parent-1",
        "depth": 1,
        "task_index": 0,
        "task_count": 2,
        "goal": "Review source coverage",
        "model": "review-model",
    }

    [projected] = projector.feed(event)

    assert projected["event"] == "runtime.subagent"
    assert projected["phase"] == "started"
    assert projected["runtime_node_id"] == "run_12345678:subagent:sa-0-abcd1234"
    assert projected["parent_id"] == "sa-parent-1"
    assert projected["delegation_id"] == "dg-1"
    assert projected["child_session_id"] == "child-session-1"
    assert projected["metrics"] == {"depth": 1, "task_index": 0, "task_count": 2}
    assert projected["relation_basis"] == "explicit_runtime_ids"
    assert projected["projection"] == "derived_transient"
    assert projected["persistence"] == "none"
    assert projected["authority_effect"] == "none"
    assert projected["governed_identity"] is False
    assert projected["private_reasoning_included"] is False


def test_completion_updates_same_node_without_exposing_output_tail() -> None:
    projector = HermesRuntimeTopologyProjector("run_12345678")
    projector.feed(
        {
            "event": "subagent.start",
            "run_id": "run_12345678",
            "subagent_id": "sa-0-abcd1234",
        }
    )
    [completed] = projector.feed(
        {
            "event": "subagent.complete",
            "run_id": "run_12345678",
            "timestamp": 20,
            "subagent_id": "sa-0-abcd1234",
            "status": "completed",
            "summary": "One unsupported claim remains.",
            "duration_seconds": 4.2,
            "input_tokens": 1200,
            "output_tokens": 230,
            "reasoning_tokens": 80,
            "api_calls": 2,
            "cost_usd": 0.12,
            "files_read": ["report.md"],
            "files_written": [],
            "output_tail": "must not be projected",
        }
    )

    assert completed["phase"] == "completed"
    assert completed["runtime_node_id"] == "run_12345678:subagent:sa-0-abcd1234"
    assert completed["summary"] == "One unsupported claim remains."
    assert completed["metrics"]["duration_seconds"] == 4.2
    assert completed["metrics"]["reasoning_tokens"] == 80
    assert completed["files"] == {"read": ["report.md"], "written": []}
    assert "output_tail" not in completed


def test_projects_a_figure_only_when_the_delegation_explicitly_declares_one() -> None:
    projector = HermesRuntimeTopologyProjector("run_12345678")
    [started] = projector.feed(
        {
            "event": "subagent.start",
            "run_id": "run_12345678",
            "subagent_id": "sa-0-abcd1234",
            "delegation_figure": "ariane",
        }
    )
    [completed] = projector.feed(
        {
            "event": "subagent.complete",
            "run_id": "run_12345678",
            "subagent_id": "sa-0-abcd1234",
        }
    )

    assert started["figure"] == {
        "name": "Ariane",
        "mission": "chronologie des échanges",
    }
    assert started["figure_basis"] == "explicit_delegation_metadata"
    assert completed["figure"] == started["figure"]


def test_rejects_unknown_or_changed_delegation_figure() -> None:
    projector = HermesRuntimeTopologyProjector("run_12345678")
    with pytest.raises(HermesRuntimeTopologyProjectionError, match="delegation_figure"):
        projector.feed(
            {
                "event": "subagent.start",
                "run_id": "run_12345678",
                "subagent_id": "sa-0-abcd1234",
                "delegation_figure": "Ulysse",
            }
        )

    projector.feed(
        {
            "event": "subagent.start",
            "run_id": "run_12345678",
            "subagent_id": "sa-0-abcd1234",
            "delegation_figure": "ariane",
        }
    )
    with pytest.raises(HermesRuntimeTopologyProjectionError, match="changed"):
        projector.feed(
            {
                "event": "subagent.complete",
                "run_id": "run_12345678",
                "subagent_id": "sa-0-abcd1234",
                "delegation_figure": "diomede",
            }
        )


def test_ignores_non_lifecycle_subagent_and_reasoning_events() -> None:
    projector = HermesRuntimeTopologyProjector("run_12345678")

    assert projector.feed({"event": "subagent.tool", "subagent_id": "sa-1"}) == []
    assert projector.feed({"event": "reasoning.available", "text": "private"}) == []
    assert projector.feed({"event": "tool.started", "tool": "delegate_task"}) == []


def test_fails_closed_on_missing_identity_or_cross_run_event() -> None:
    projector = HermesRuntimeTopologyProjector("run_12345678")

    with pytest.raises(HermesRuntimeTopologyProjectionError, match="subagent_id"):
        projector.feed({"event": "subagent.start", "run_id": "run_12345678"})

    with pytest.raises(HermesRuntimeTopologyProjectionError, match="crossed"):
        projector.feed(
            {
                "event": "subagent.complete",
                "run_id": "run_other999",
                "subagent_id": "sa-1",
            }
        )
