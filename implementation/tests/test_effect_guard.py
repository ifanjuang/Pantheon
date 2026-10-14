"""Governance guard tests for public effect-preview responses."""

from __future__ import annotations

from mvp_vertical import effect_guard


def test_targetless_non_create_is_forced_to_unclassified_create() -> None:
    source = {
        "status": "proposal_only",
        "proposals": [
            {
                "proposal_id": "proposal-1",
                "effect": "UPDATE",
                "effect_source": "explicit_hint",
                "target": None,
                "candidate_object_type": "knowledge",
                "reasons": ["User hint."],
                "requires_human_confirmation": False,
                "apply_route": "/forbidden",
            }
        ],
    }

    guarded = effect_guard.enforce_preview(source)
    proposal = guarded["proposals"][0]

    assert proposal["effect"] == "CREATE"
    assert proposal["effect_source"] == "target_required:overrode_update"
    assert proposal["candidate_object_type"] == "unclassified"
    assert proposal["target"] is None
    assert proposal["requires_human_confirmation"] is True
    assert proposal["apply_route"] is None
    assert source["proposals"][0]["effect"] == "UPDATE"


def test_targeted_candidate_keeps_effect_but_never_exposes_apply_route() -> None:
    guarded = effect_guard.enforce_preview(
        {
            "proposals": [
                {
                    "effect": "CONFLICT",
                    "target": {"object_id": "knowledge.coverage"},
                    "requires_human_confirmation": False,
                    "apply_route": "/forbidden",
                }
            ]
        }
    )

    proposal = guarded["proposals"][0]
    assert proposal["effect"] == "CONFLICT"
    assert proposal["requires_human_confirmation"] is True
    assert proposal["apply_route"] is None
