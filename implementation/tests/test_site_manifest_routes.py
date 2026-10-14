"""Cockpit route boundary for proposal-only site manifests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from mvp_vertical import site_manifest_preview
from mvp_vertical.cockpit_shell import create_cockpit_app


class _Connection:
    def close(self) -> None:
        pass


def test_site_manifest_preview_route_is_authenticated_and_proposal_only(monkeypatch) -> None:
    observed = {}

    def preview(_conn, **values):
        observed.update(values)
        return {
            "status": "proposal_only",
            "manifest_id": "manifest-preview-example",
            "manifest_digest": "sha256:example",
            "manifest": {
                "mode": "structure_only",
                "sites": values["sites"],
                "capture": {"body_text": False, "link_graph": True},
            },
            "execution": {"status": "not_created", "network_requests": 0},
            "indexing": {"status": "not_indexed"},
            "capability_slot": {
                "candidate_hermes_binding": None,
                "activation": "not_authorized",
            },
            "gates": [{"gate": "human_scope_approval", "status": "open"}],
            "warnings": [],
            "distinctions": ["manifest preview != crawl authorization"],
        }

    monkeypatch.setattr(site_manifest_preview, "preview_structure_manifest", preview)
    client = TestClient(create_cockpit_app(connect_fn=_Connection, api_key="read-key"))
    path = "/projects/project-a/knowledge/knowledge.rules/site-manifests/preview"
    body = {
        "mode": "structure_only",
        "sites": [
            {
                "url": "https://www.legifrance.gouv.fr/codes/",
                "path_prefixes": ["/codes/"],
                "max_depth": 2,
            }
        ],
    }

    assert client.post(path, json=body).status_code == 401
    response = client.post(
        path,
        json=body,
        headers={"Authorization": "Bearer read-key"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "proposal_only"
    assert payload["execution"]["network_requests"] == 0
    assert payload["capability_slot"]["activation"] == "not_authorized"
    assert observed == {
        "parent_project_id": "project-a",
        "knowledge_id": "knowledge.rules",
        "mode": "structure_only",
        "sites": body["sites"],
    }
    assert client.post(
        "/v1/projects/project-a/knowledge/knowledge.rules/site-manifests/preview",
        json=body,
        headers={"Authorization": "Bearer read-key"},
    ).status_code == 404
