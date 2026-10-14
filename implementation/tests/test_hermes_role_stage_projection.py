from __future__ import annotations

import pytest

from mvp_vertical.hermes_role_stage_projection import (
    MAX_LINE_CHARS,
    HermesRoleStageProjectionError,
    HermesRoleStageProjector,
)


def _event(kind: str, **fields):
    return {"event": kind, "run_id": "run-role-1", "timestamp": 10.0, **fields}


def test_split_public_header_starts_one_canonical_role_stage() -> None:
    projector = HermesRoleStageProjector("run-role-1")

    assert projector.feed(_event("message.delta", delta="🦉 Ath")) == []
    stages = projector.feed(
        _event("message.delta", delta="ena · Plan / structuration\n")
    )

    assert len(stages) == 1
    assert stages[0]["event"] == "role.stage"
    assert stages[0]["phase"] == "started"
    assert stages[0]["visible_role"] == "Athena"
    assert stages[0]["role_family"] == "analysis"
    assert stages[0]["private_reasoning_included"] is False
    assert stages[0]["authority_effect"] == "none"


def test_public_summary_updates_then_next_header_completes_in_order() -> None:
    projector = HermesRoleStageProjector("run-role-1")
    projector.feed(_event("message.delta", delta="🦉 Athena · Plan\n"))

    updated = projector.feed(
        _event("message.delta", delta="Action: comparer les deux options\n")
    )
    transition = projector.feed(
        _event("message.delta", delta="⚡ Zeus · Statut\n")
    )

    assert updated[0]["phase"] == "updated"
    assert updated[0]["summary"] == "comparer les deux options"
    assert updated[0]["details"] == {"action": "comparer les deux options"}
    assert [stage["phase"] for stage in transition] == ["completed", "started"]
    assert transition[0]["visible_role"] == "Athena"
    assert transition[1]["visible_role"] == "Zeus"
    assert transition[1]["sequence"] == 2


def test_reasoning_event_is_deliberately_ignored() -> None:
    projector = HermesRoleStageProjector("run-role-1")

    assert projector.feed(
        _event("reasoning.available", text="private scratchpad")
    ) == []


def test_tool_lifecycle_is_projected_as_observed_hermes_execution() -> None:
    projector = HermesRoleStageProjector("run-role-1")

    started = projector.feed(_event("tool.started", tool="document_inventory"))
    completed = projector.feed(
        _event("tool.completed", tool="document_inventory", duration=0.75, error=False)
    )

    assert started[0]["visible_role"] == "Hermes"
    assert started[0]["phase"] == "started"
    assert started[0]["source_event"] == "tool.started"
    assert completed[0]["stage_id"] == started[0]["stage_id"]
    assert completed[0]["phase"] == "completed"
    assert completed[0]["error"] is False


def test_governed_attention_is_visible_without_implying_rite_activation() -> None:
    projector = HermesRoleStageProjector("run-role-1")

    started = projector.feed(
        _event("message.delta", delta="⚙ Hermes · Attention gouvernée\n")
    )
    question = projector.feed(
        _event(
            "message.delta",
            delta="What would passing these tests still not establish?\n",
        )
    )
    limit = projector.feed(
        _event(
            "message.delta",
            delta="Limite: attention_only — question ≠ symptôme confirmé ≠ Rite activé\n",
        )
    )

    assert started[0]["visible_role"] == "Hermes"
    assert started[0]["role_family"] == "runtime"
    assert started[0]["semantic_function"] == "Attention gouvernée"
    assert started[0]["authority_effect"] == "none"
    assert question[0]["summary"] == "What would passing these tests still not establish?"
    assert limit[0]["summary"] == question[0]["summary"]
    assert limit[0]["details"]["limite"] == (
        "attention_only — question ≠ symptôme confirmé ≠ Rite activé"
    )


def test_terminal_event_flushes_the_last_public_stage() -> None:
    projector = HermesRoleStageProjector("run-role-1")
    projector.feed(_event("message.delta", delta="⚡ Zeus · Statut\nRésultat: prêt"))

    stages = projector.feed(_event("run.completed"))

    assert [stage["phase"] for stage in stages] == ["updated", "completed"]
    assert stages[-1]["visible_role"] == "Zeus"
    assert stages[-1]["summary"] == "prêt"


def test_unknown_labels_and_unrelated_events_create_no_role() -> None:
    projector = HermesRoleStageProjector("run-role-1")

    assert projector.feed(_event("message.delta", delta="Socrate · Réflexion\n")) == []
    assert projector.feed(_event("subagent.start", goal="candidate")) == []


def test_unbounded_unterminated_public_line_fails_closed() -> None:
    projector = HermesRoleStageProjector("run-role-1")

    with pytest.raises(HermesRoleStageProjectionError, match="unterminated"):
        projector.feed(_event("message.delta", delta="x" * (MAX_LINE_CHARS + 1)))
