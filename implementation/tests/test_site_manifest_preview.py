"""Proposal-only structure manifest preview contracts."""

from __future__ import annotations

import pytest

from mvp_vertical import knowledge, site_manifest_preview


class _Connection:
    pass


MARKDOWN = """
# Sources web

- https://www.legifrance.gouv.fr/codes/article_lc/ABC
- https://sitesecurite.fr/erp
"""


def _patch_knowledge(monkeypatch, *, project: str = "project-a", markdown: str = MARKDOWN):
    monkeypatch.setattr(
        knowledge,
        "get_knowledge_card",
        lambda _conn, knowledge_id: {
            "knowledge_id": knowledge_id,
            "parent_project_id": project,
            "title": "Références réglementaires",
        },
    )
    monkeypatch.setattr(
        knowledge,
        "get_knowledge_markdown",
        lambda _conn, _knowledge_id: markdown,
    )


def test_structure_manifest_preview_is_deterministic_and_never_executes(monkeypatch) -> None:
    _patch_knowledge(monkeypatch)
    sites = [
        {
            "url": "https://sitesecurite.fr/erp",
            "path_prefixes": ["/erp"],
            "max_depth": 2,
        },
        {
            "url": "https://www.legifrance.gouv.fr/codes/article_lc/ABC",
            "path_prefixes": ["/codes/"],
            "max_depth": 1,
        },
    ]

    first = site_manifest_preview.preview_structure_manifest(
        _Connection(),
        parent_project_id="project-a",
        knowledge_id="knowledge.regulations",
        mode="structure_only",
        sites=sites,
    )
    second = site_manifest_preview.preview_structure_manifest(
        _Connection(),
        parent_project_id="project-a",
        knowledge_id="knowledge.regulations",
        mode="structure_only",
        sites=list(reversed(sites)),
    )

    assert first["status"] == "proposal_only"
    assert first["manifest_digest"] == second["manifest_digest"]
    assert first["execution"] == {
        "status": "not_created",
        "network_requests": 0,
        "persisted": False,
        "scheduled": False,
    }
    assert first["indexing"]["structure_indexed"] is False
    assert first["manifest"]["capture"]["body_text"] is False
    assert first["manifest"]["capture"]["link_graph"] is True
    assert first["capability_slot"]["candidate_hermes_binding"] is None
    assert first["capability_slot"]["activation"] == "not_authorized"
    assert all(gate["status"] == "open" for gate in first["gates"])
    assert "structure indexed != content adopted" in first["distinctions"]


def test_preview_refuses_unlinked_scope_private_targets_and_wrong_project(monkeypatch) -> None:
    _patch_knowledge(monkeypatch)
    common = dict(
        conn=_Connection(),
        parent_project_id="project-a",
        knowledge_id="knowledge.regulations",
        mode="structure_only",
    )

    with pytest.raises(site_manifest_preview.SiteManifestPreviewError, match="not already present"):
        site_manifest_preview.preview_structure_manifest(
            **common,
            sites=[{"url": "https://example.com/", "path_prefixes": ["/"]}],
        )

    _patch_knowledge(monkeypatch, markdown="https://127.0.0.1/admin")
    with pytest.raises(site_manifest_preview.SiteManifestPreviewError, match="private"):
        site_manifest_preview.preview_structure_manifest(
            **common,
            sites=[{"url": "https://127.0.0.1/admin", "path_prefixes": ["/"]}],
        )

    _patch_knowledge(monkeypatch, project="project-other")
    with pytest.raises(site_manifest_preview.SiteManifestPreviewError, match="exact opened project"):
        site_manifest_preview.preview_structure_manifest(
            **common,
            sites=[{"url": "https://sitesecurite.fr/erp", "path_prefixes": ["/erp"]}],
        )


def test_preview_refuses_bracketed_ipv6_loopback_after_canonicalization(monkeypatch) -> None:
    _patch_knowledge(monkeypatch, markdown="https://[::1]/admin")

    with pytest.raises(site_manifest_preview.SiteManifestPreviewError, match="private"):
        site_manifest_preview.preview_structure_manifest(
            _Connection(),
            parent_project_id="project-a",
            knowledge_id="knowledge.regulations",
            mode="structure_only",
            sites=[{"url": "https://[::1]/admin", "path_prefixes": ["/"]}],
        )


def test_preview_refuses_credentials_before_url_canonicalization(monkeypatch) -> None:
    _patch_knowledge(monkeypatch, markdown="https://user:secret@sitesecurite.fr/erp")
    with pytest.raises(site_manifest_preview.SiteManifestPreviewError, match="credential-bearing"):
        site_manifest_preview.preview_structure_manifest(
            _Connection(),
            parent_project_id="project-a",
            knowledge_id="knowledge.regulations",
            mode="structure_only",
            sites=[
                {
                    "url": "https://user:secret@sitesecurite.fr/erp",
                    "path_prefixes": ["/erp"],
                    "max_depth": 1,
                }
            ],
        )


def test_preview_makes_scope_expansion_and_transport_risks_visible(monkeypatch) -> None:
    _patch_knowledge(monkeypatch, markdown="http://sitesecurite.fr/erp/articles/42")
    preview = site_manifest_preview.preview_structure_manifest(
        _Connection(),
        parent_project_id="project-a",
        knowledge_id="knowledge.regulations",
        mode="structure_only",
        sites=[
            {
                "url": "http://sitesecurite.fr/erp/articles/42",
                "path_prefixes": ["/erp/"],
                "max_depth": 4,
            }
        ],
    )

    site = preview["manifest"]["sites"][0]
    assert site["scope_expansion_from_seed"] is True
    assert site["same_host_only"] is True
    assert site["follow_subdomains"] is False
    assert any("insecure HTTP" in warning for warning in preview["warnings"])
    assert any("broader than" in warning for warning in preview["warnings"])
    assert any("heightened review" in warning for warning in preview["warnings"])
