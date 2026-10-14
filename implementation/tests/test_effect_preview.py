"""Deterministic effect-preview tests without persistence or model calls."""

from __future__ import annotations

import pytest

from mvp_vertical import effect_preview


def _object(
    *,
    object_type: effect_preview.ObjectKind = "knowledge",
    object_id: str = "knowledge.coverage",
    title: str = "Choix de la couverture zinc",
    status: str = "needs_review",
    searchable_text: str | None = None,
) -> effect_preview.ProjectObject:
    return effect_preview.ProjectObject(
        object_type=object_type,
        object_id=object_id,
        card_id=f"card-{object_id}",
        title=title,
        status=status,
        searchable_text=searchable_text or f"{title} toiture zinc naturel couverture",
        explicit_refs=(object_id, f"card-{object_id}"),
    )


def test_matching_existing_object_defaults_to_update() -> None:
    preview = effect_preview.preview_from_objects(
        parent_project_id="project-verger",
        information="Le client confirme le choix de la couverture en zinc naturel.",
        objects=[_object()],
    )

    proposal = preview["proposals"][0]
    assert preview["status"] == "proposal_only"
    assert proposal["effect"] == "UPDATE"
    assert proposal["target"]["object_id"] == "knowledge.coverage"
    assert proposal["requires_human_confirmation"] is True
    assert proposal["apply_route"] is None


def test_conflict_and_supersede_are_only_candidate_effects() -> None:
    conflict = effect_preview.preview_from_objects(
        parent_project_id="project-verger",
        information="Cette nouvelle note contredit le choix de la couverture zinc.",
        objects=[_object()],
    )["proposals"][0]
    supersede = effect_preview.preview_from_objects(
        parent_project_id="project-verger",
        information="Le client supprime finalement la couverture zinc du programme.",
        objects=[_object()],
    )["proposals"][0]

    assert conflict["effect"] == "CONFLICT"
    assert supersede["effect"] == "SUPERSEDE"
    assert conflict["effect_source"].startswith("deterministic_cue:")
    assert supersede["effect_source"].startswith("deterministic_cue:")


def test_no_match_proposes_unclassified_create() -> None:
    preview = effect_preview.preview_from_objects(
        parent_project_id="project-verger",
        information="Ajouter une étude acoustique indépendante pour le studio musical.",
        objects=[_object()],
    )

    proposal = preview["proposals"][0]
    assert proposal["effect"] == "CREATE"
    assert proposal["target"] is None
    assert proposal["candidate_object_type"] == "unclassified"
    assert "type du nouvel objet" in proposal["reasons"][1]


def test_explicit_reference_wins_without_broadening_scope() -> None:
    first = _object(object_id="knowledge.coverage", title="Couverture")
    second = _object(
        object_type="work_issue",
        object_id="issue-scaffold",
        title="Échafaudage à répartir",
        status="waiting",
    )
    preview = effect_preview.preview_from_objects(
        parent_project_id="project-verger",
        information="Préciser que la location reste à répartir.",
        objects=[first, second],
        explicit_object_refs=["issue-scaffold"],
    )

    proposal = preview["proposals"][0]
    assert proposal["target"]["object_id"] == "issue-scaffold"
    assert proposal["score"] == 1.0
    assert proposal["confidence"] == "high"


def test_effect_hint_is_visible_but_still_not_applied() -> None:
    proposal = effect_preview.preview_from_objects(
        parent_project_id="project-verger",
        information="Le choix de couverture doit être revu.",
        objects=[_object()],
        effect_hint="CONFLICT",
    )["proposals"][0]

    assert proposal["effect"] == "CONFLICT"
    assert proposal["effect_source"] == "explicit_hint"
    assert proposal["apply_route"] is None


def test_preview_refuses_unbounded_inputs() -> None:
    with pytest.raises(effect_preview.EffectPreviewError, match="information length"):
        effect_preview.preview_from_objects(
            parent_project_id="project-verger",
            information="x",
            objects=[],
        )
    with pytest.raises(effect_preview.EffectPreviewError, match="max_proposals"):
        effect_preview.preview_from_objects(
            parent_project_id="project-verger",
            information="une information bornée",
            objects=[],
            max_proposals=11,
        )
