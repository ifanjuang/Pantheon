"""Cards-first cockpit static composition boundaries."""

from __future__ import annotations

from fastapi.testclient import TestClient

from mvp_vertical import effect_preview, resource_profiles, work_issue_read
from mvp_vertical.cockpit_shell import create_cockpit_app


class _Connection:
    def close(self) -> None:
        pass


def test_cards_first_cockpit_shell_is_available() -> None:
    client = TestClient(create_cockpit_app(connect_fn=_Connection, api_key="read-key"))

    response = client.get("/cockpit/")
    assert response.status_code == 200
    assert "Pantheon Cockpit" in response.text
    assert 'id="v2-stage"' in response.text
    assert 'src="cockpit_bootstrap.js"' in response.text

    for script in (
        "cockpit_bootstrap.js",
        "live_bootstrap.js",
        "live_collection_adapter.js",
        "shell_controls.js",
    ):
        assert client.get(f"/cockpit/{script}").status_code == 200
    for retired in (
        "v3_bootstrap.js",
        "v2_bootstrap.js",
        "v3_swiper.js",
        "v2_shell_controls.js",
    ):
        assert client.get(f"/cockpit/{retired}").status_code == 404
    assert client.get("/cockpit/collection/collection_controller.js").status_code == 200
    assert client.get("/cockpit/v3/collection/collection_controller.js").status_code == 404
    for stylesheet in ("cockpit.css", "cards.css", "families.css", "editors.css"):
        assert client.get(f"/cockpit/styles/{stylesheet}").status_code == 200
    assert client.get("/cockpit/styles/index.css").status_code == 404
    assert client.get("/editor/").status_code == 200


def test_composed_shell_keeps_existing_api_boundary() -> None:
    client = TestClient(create_cockpit_app(connect_fn=_Connection, api_key="read-key"))

    assert client.get("/health").status_code == 200
    assert client.get("/projects/project-a/documents").status_code == 401
    assert client.get("/work/issues", params={"case_ref": "project-a"}).status_code == 401
    assert client.get("/projects/project-a/resource-profiles").status_code == 401
    assert client.post(
        "/projects/project-a/effects/preview",
        json={"information": "Préciser le choix de couverture."},
    ).status_code == 401

    assert client.get("/v1/projects/project-a/documents").status_code == 404
    assert client.get("/v1/projects/project-a/resource-profiles").status_code == 404
    assert client.post(
        "/v1/projects/project-a/effects/preview",
        json={"information": "Préciser le choix de couverture."},
    ).status_code == 404


def test_health_reports_effective_service_posture() -> None:
    read_client = TestClient(create_cockpit_app(connect_fn=_Connection, api_key="read-key"))
    read_health = read_client.get("/health").json()
    assert read_health["mode"] == "read_only"
    assert read_health["preview_effect"] == "none"
    assert read_health["write_surface"] == "disabled"
    assert read_health["signed_knowledge_update_gate"] == "not_configured"

    editor_client = TestClient(create_cockpit_app(connect_fn=_Connection, editor_api_key="editor-key"))
    editor_health = editor_client.get("/health").json()
    assert editor_health["mode"] == "bounded_read_write"
    assert editor_health["preview_effect"] == "none"
    assert editor_health["write_surface"] == "bounded_document_knowledge_writes"
    assert editor_health["signed_knowledge_update_gate"] == "not_configured"


def test_preview_effect_contract_is_proposal_only(monkeypatch) -> None:
    payload = {
        "parent_project_id": "project-a",
        "proposals": [{"proposal_id": "proposal-1", "effect": "UPDATE", "target": {"object_id": "object-a"}, "reasons": []}],
    }
    monkeypatch.setattr(effect_preview, "preview_project_effects", lambda *_, **__: payload)
    client = TestClient(create_cockpit_app(connect_fn=_Connection, editor_api_key="editor-key"))
    response = client.post(
        "/projects/project-a/effects/preview",
        headers={"Authorization": "Bearer editor-key"},
        json={"information": "Préciser le choix de couverture."},
    )
    assert response.status_code == 200
    proposal = response.json()["proposals"][0]
    assert proposal["effect"] == "UPDATE"
    assert proposal["requires_human_confirmation"] is True
    assert proposal["apply_route"] is None


def test_resource_profile_contract(monkeypatch) -> None:
    payload = {"parent_project_id": "project-a", "resource_profiles": []}
    monkeypatch.setattr(resource_profiles, "list_project_resource_profiles", lambda *_: payload)
    client = TestClient(create_cockpit_app(connect_fn=_Connection, api_key="read-key"))
    response = client.get("/projects/project-a/resource-profiles", headers={"Authorization": "Bearer read-key"})
    assert response.status_code == 200
    assert response.json() == payload


def test_work_issue_read_contract_preserves_hermes_cognitive_summary(monkeypatch) -> None:
    projections = [
        {
            "work_issue": {
                "issue_id": "issue-athena-live",
                "case_ref": "project-athena-live",
            },
            "comments": [],
            "hermes_runs": [
                {
                    "run_id": "run-athena-live",
                    "status": "returned",
                    "normalized_return": {
                        "outcome": "result_candidate",
                        "summary": "Bounded situated reasoning candidate.",
                        "result_refs": [],
                        "evidence_candidate_refs": [],
                        "trace_refs": ["hermes://runs/run-athena-live"],
                    },
                }
            ],
            "events": [],
            "governance_refs": [],
        }
    ]
    monkeypatch.setattr(
        work_issue_read,
        "list_issue_projections",
        lambda *_, **__: projections,
    )
    client = TestClient(create_cockpit_app(connect_fn=_Connection, api_key="read-key"))

    response = client.get(
        "/work/issues",
        params={"case_ref": "project-athena-live"},
        headers={"Authorization": "Bearer read-key"},
    )

    assert response.status_code == 200
    returned = response.json()["work_issues"][0]["hermes_runs"][0]
    assert returned["run_id"] == "run-athena-live"
    assert returned["normalized_return"]["summary"] == "Bounded situated reasoning candidate."


def test_work_issue_read_contract(monkeypatch) -> None:
    monkeypatch.setattr(work_issue_read, "list_issue_projections", lambda *_, **__: [])
    client = TestClient(create_cockpit_app(connect_fn=_Connection, api_key="read-key"))
    response = client.get("/work/issues", params={"case_ref": "project-a"}, headers={"Authorization": "Bearer read-key"})
    assert response.status_code == 200
    assert response.json() == {"case_ref": "project-a", "scope_match": "exact_case_ref", "work_issues": []}
