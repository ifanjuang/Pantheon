"""Proposal-only site navigation profile contracts."""

from __future__ import annotations

import pytest

from mvp_vertical import knowledge, site_navigation_profile


class _Connection:
    pass


MARKDOWN = """
# Sources

- https://www.legifrance.gouv.fr/codes/article_lc/ABC
- https://sitesecurite.fr/erp
- https://www.geoportail.gouv.fr/
"""


def _patch(monkeypatch, *, project="project-a", markdown=MARKDOWN):
    monkeypatch.setattr(
        knowledge,
        "get_knowledge_card",
        lambda _conn, knowledge_id: {
            "knowledge_id": knowledge_id,
            "parent_project_id": project,
            "title": "Sources réglementaires",
        },
    )
    monkeypatch.setattr(
        knowledge,
        "get_knowledge_markdown",
        lambda _conn, _knowledge_id: markdown,
    )


def test_profiles_are_task_specific_deterministic_and_never_execute(monkeypatch) -> None:
    _patch(monkeypatch)
    first = site_navigation_profile.preview_site_navigation_profiles(
        _Connection(),
        parent_project_id="project-a",
        knowledge_id="knowledge.sources",
        task="Trouver la version en vigueur d'un article ERP",
        selected_urls=[
            "https://sitesecurite.fr/erp",
            "https://www.legifrance.gouv.fr/codes/article_lc/ABC",
        ],
    )
    second = site_navigation_profile.preview_site_navigation_profiles(
        _Connection(),
        parent_project_id="project-a",
        knowledge_id="knowledge.sources",
        task="Trouver la version en vigueur d'un article ERP",
        selected_urls=[
            "https://www.legifrance.gouv.fr/codes/article_lc/ABC",
            "https://sitesecurite.fr/erp",
        ],
    )

    assert first["status"] == "proposal_only"
    assert first["profile_digest"] == second["profile_digest"]
    assert first["execution"] == {
        "status": "not_created",
        "network_requests": 0,
        "catalog_queries": 0,
        "skills_installed": 0,
        "persisted": False,
    }
    archetypes = {profile["archetype"]["id"] for profile in first["profiles"]}
    assert archetypes == {"legal_database", "hierarchical_safety_reference"}
    assert all(profile["navigation_plan"]["read_only"] for profile in first["profiles"])
    assert all(profile["navigation_plan"]["login_allowed"] is False for profile in first["profiles"])
    assert all(
        binding["approved"] is False
        for profile in first["profiles"]
        for binding in profile["candidate_bindings"]
    )
    assert first["capability_slot"]["activation"] == "not_authorized"
    assert all(gate["status"] == "open" for gate in first["gates"])


def test_geodata_profile_prefers_catalog_or_api_before_browser(monkeypatch) -> None:
    _patch(monkeypatch)
    preview = site_navigation_profile.preview_site_navigation_profiles(
        _Connection(),
        parent_project_id="project-a",
        knowledge_id="knowledge.sources",
        task="Identifier la couche cadastrale disponible",
        selected_urls=["https://www.geoportail.gouv.fr/"],
    )

    profile = preview["profiles"][0]
    assert profile["archetype"]["id"] == "interactive_geospatial_portal"
    assert profile["archetype"]["preferred_strategy"] == "api_or_catalog_first_then_browser_map"
    assert "dataset_or_layer_id" in profile["archetype"]["verification_fields"]


def test_preview_refuses_unlinked_site_wrong_project_and_empty_task(monkeypatch) -> None:
    _patch(monkeypatch)
    with pytest.raises(site_navigation_profile.SiteNavigationProfileError, match="not already present"):
        site_navigation_profile.preview_site_navigation_profiles(
            _Connection(),
            parent_project_id="project-a",
            knowledge_id="knowledge.sources",
            task="Trouver une règle",
            selected_urls=["https://example.com/"],
        )

    _patch(monkeypatch, project="project-other")
    with pytest.raises(site_navigation_profile.SiteNavigationProfileError, match="exact opened project"):
        site_navigation_profile.preview_site_navigation_profiles(
            _Connection(),
            parent_project_id="project-a",
            knowledge_id="knowledge.sources",
            task="Trouver une règle",
        )

    _patch(monkeypatch)
    with pytest.raises(site_navigation_profile.SiteNavigationProfileError, match="between 3 and 500"):
        site_navigation_profile.preview_site_navigation_profiles(
            _Connection(),
            parent_project_id="project-a",
            knowledge_id="knowledge.sources",
            task=" ",
        )
