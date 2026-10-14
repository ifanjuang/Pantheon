"""Site navigation profile API boundary contracts."""

from __future__ import annotations

from fastapi.testclient import TestClient

from mvp_vertical import site_navigation_profile
from mvp_vertical.cockpit_shell import create_cockpit_app


class _Connection:
    def close(self) -> None:
        pass


def test_navigation_profile_route_is_authenticated_exact_and_proposal_only(monkeypatch) -> None:
    observed = {}

    def preview(_conn, **values):
        observed.update(values)
        return {
            "status": "proposal_only",
            "schema": "pantheon.site_navigation_profile_candidate.v1",
            "parent_project_id": values["parent_project_id"],
            "knowledge_id": values["knowledge_id"],
            "task": values["task"],
            "profile_digest": "sha256:test",
            "profiles": [],
            "capability_slot": {"activation": "not_authorized"},
            "gates": [],
            "execution": {
                "status": "not_created",
                "network_requests": 0,
                "catalog_queries": 0,
                "skills_installed": 0,
                "persisted": False,
            },
            "distinctions": [],
        }

    monkeypatch.setattr(
        site_navigation_profile,
        "preview_site_navigation_profiles",
        preview,
    )
    client = TestClient(create_cockpit_app(connect_fn=_Connection, api_key="read-key"))
    path = "/projects/project-a/knowledge/knowledge.sources/navigation-profiles/preview"

    assert client.post(path, json={"task": "Trouver une règle"}).status_code == 401

    response = client.post(
        path,
        headers={"Authorization": "Bearer read-key"},
        json={
            "task": "Trouver la version en vigueur",
            "selected_urls": ["https://www.legifrance.gouv.fr/"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "proposal_only"
    assert payload["execution"]["network_requests"] == 0
    assert payload["execution"]["skills_installed"] == 0
    assert payload["capability_slot"]["activation"] == "not_authorized"
    assert observed == {
        "parent_project_id": "project-a",
        "knowledge_id": "knowledge.sources",
        "task": "Trouver la version en vigueur",
        "selected_urls": ["https://www.legifrance.gouv.fr/"],
    }
    assert client.post(
        "/v1/projects/project-a/knowledge/knowledge.sources/navigation-profiles/preview",
        headers={"Authorization": "Bearer read-key"},
        json={"task": "Trouver une règle"},
    ).status_code == 404
