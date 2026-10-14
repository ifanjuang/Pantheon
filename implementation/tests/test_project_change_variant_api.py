"""API boundary tests for human Project variant selection."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from mvp_vertical import project_change_variants
from mvp_vertical.project_change_variant_api import install_project_change_variant_routes


def _app(monkeypatch, *, transition=None):
    app = FastAPI()

    def require_editor_key():
        return None

    def with_connection(operation):
        return operation(object())

    if transition is not None:
        monkeypatch.setattr(
            project_change_variants,
            "select_variant_for_change_candidate",
            lambda *args, **kwargs: transition,
        )
    install_project_change_variant_routes(
        app,
        with_connection=with_connection,
        require_editor_key=require_editor_key,
    )
    return TestClient(app)


def test_selection_requires_explicit_human_actor(monkeypatch) -> None:
    response = _app(monkeypatch).post(
        "/execution-results/execution-1/results/result-1/project-change-candidate",
        headers={"Idempotency-Key": "variant-selection-key"},
    )
    assert response.status_code == 422
    assert "X-Pantheon-Human-Actor" in response.json()["detail"]


def test_selection_returns_candidate_without_project_application(monkeypatch) -> None:
    transition = {
        "selection": {"disposition_id": "disposition-1"},
        "change_candidate": {
            "candidate_id": "change-1",
            "status": "pending_review",
        },
    }
    response = _app(monkeypatch, transition=transition).post(
        "/execution-results/execution-1/results/result-1/project-change-candidate",
        headers={
            "X-Pantheon-Human-Actor": "human:architect",
            "Idempotency-Key": "variant-selection-key",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["selection"] == transition["selection"]
    assert body["change_candidate"] == transition["change_candidate"]
    assert body["variant_selected"] is True
    assert body["project_mutated"] is False
    assert body["human_decision_recorded"] is False
    assert body["evidence_admitted"] is False
    assert body["external_effect_authorized"] is False


def test_selection_conflict_maps_to_http_409(monkeypatch) -> None:
    app = FastAPI()

    def require_editor_key():
        return None

    def with_connection(operation):
        return operation(object())

    def conflict(*args, **kwargs):
        raise project_change_variants.ProjectChangeVariantConflict(
            "a sibling variant is already selected"
        )

    monkeypatch.setattr(
        project_change_variants,
        "select_variant_for_change_candidate",
        conflict,
    )
    install_project_change_variant_routes(
        app,
        with_connection=with_connection,
        require_editor_key=require_editor_key,
    )
    response = TestClient(app).post(
        "/execution-results/execution-1/results/result-2/project-change-candidate",
        headers={
            "X-Pantheon-Human-Actor": "human:architect",
            "Idempotency-Key": "variant-selection-key",
        },
    )
    assert response.status_code == 409
