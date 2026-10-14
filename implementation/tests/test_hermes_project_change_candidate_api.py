"""API boundary tests for admission-bound Hermes Project ChangeCandidates."""

from __future__ import annotations

from fastapi.testclient import TestClient

from mvp_vertical import (
    agency_change_candidates,
    hermes_active_context,
    hermes_scoped_context,
)
from mvp_vertical.cockpit_shell import create_cockpit_app


class _Connection:
    def close(self) -> None:
        pass


def _client() -> TestClient:
    return TestClient(
        create_cockpit_app(
            connect_fn=_Connection,
            api_key="read-key",
            editor_api_key="editor-key",
            hermes_api_key="hermes-key",
        )
    )


def _headers(key: str = "hermes-key") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {key}",
        "X-Pantheon-Hermes-Actor": "hermes-runtime",
    }


def _route(project_id: str = "p1") -> str:
    return (
        "/hermes/execution-admissions/admission-1/projects/"
        f"{project_id}/change-candidates"
    )


def test_admitted_hermes_can_create_candidate_without_project_mutation(monkeypatch) -> None:
    monkeypatch.setattr(
        hermes_active_context,
        "get_active_context_entity",
        lambda _conn, **values: {
            "entity_ref": {
                "entity_type": values["entity_type"],
                "entity_id": values["entity_id"],
            },
            "current_revision": 4,
            "record": {"project_id": "p1", "revision": 4},
            "write_effect": False,
        },
    )
    monkeypatch.setattr(
        hermes_active_context,
        "get_active_context_manifest",
        lambda _conn, **_values: {
            "source_refs": ["paperless://doc/42"],
            "write_effect": False,
        },
    )
    observed: dict = {}

    def create_candidate(_conn, **values):
        observed.update(values)
        return {
            "candidate_id": "change-1",
            "entity_type": "project",
            "entity_id": values["project_id"],
            "base_revision": values["base_revision"],
            "proposer": values["proposer"],
            "proposer_kind": values["proposer_kind"],
            "status": "pending_review",
            "changes": [
                {"field": "budget", "before": 350000, "proposed": 375000}
            ],
        }

    monkeypatch.setattr(
        agency_change_candidates,
        "create_project_candidate",
        create_candidate,
    )

    response = _client().post(
        _route(),
        headers=_headers(),
        json={
            "expected_project_revision": 4,
            "proposed_attributes": {"budget": 375000},
            "reason": "Budget extrait du document admis",
            "source_refs": ["paperless://doc/42"],
            "idempotency_key": "hermes-candidate-001",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["project_mutated"] is False
    assert payload["execution_authorized"] is False
    assert payload["human_apply_required"] is True
    assert payload["evidence_admitted"] is False
    assert payload["change_candidate"]["status"] == "pending_review"
    assert observed["project_id"] == "p1"
    assert observed["base_revision"] == 4
    assert observed["proposer"] == "hermes-runtime"
    assert observed["proposer_kind"] == "hermes"


def test_hermes_candidate_requires_exact_current_project_revision(monkeypatch) -> None:
    monkeypatch.setattr(
        hermes_active_context,
        "get_active_context_entity",
        lambda _conn, **_values: {"current_revision": 5},
    )
    response = _client().post(
        _route(),
        headers=_headers(),
        json={
            "expected_project_revision": 4,
            "proposed_attributes": {"budget": 375000},
            "source_refs": [],
            "idempotency_key": "hermes-candidate-002",
        },
    )
    assert response.status_code == 409
    assert "stale Project revision" in response.json()["detail"]


def test_hermes_candidate_refuses_sources_outside_admitted_context(monkeypatch) -> None:
    monkeypatch.setattr(
        hermes_active_context,
        "get_active_context_entity",
        lambda _conn, **_values: {"current_revision": 4},
    )
    monkeypatch.setattr(
        hermes_active_context,
        "get_active_context_manifest",
        lambda _conn, **_values: {"source_refs": ["paperless://doc/42"]},
    )
    response = _client().post(
        _route(),
        headers=_headers(),
        json={
            "expected_project_revision": 4,
            "proposed_attributes": {"budget": 375000},
            "source_refs": ["paperless://doc/outside"],
            "idempotency_key": "hermes-candidate-003",
        },
    )
    assert response.status_code == 422
    assert "outside the admitted Context Pack" in response.json()["detail"]


def test_hermes_candidate_refuses_project_outside_exact_admission(monkeypatch) -> None:
    def outside(_conn, **_values):
        raise hermes_scoped_context.ScopedContextConflict(
            "requested entity is outside the exact admitted Context Pack"
        )

    monkeypatch.setattr(
        hermes_active_context,
        "get_active_context_entity",
        outside,
    )
    response = _client().post(
        _route("other"),
        headers=_headers(),
        json={
            "expected_project_revision": 1,
            "proposed_attributes": {"budget": 375000},
            "source_refs": [],
            "idempotency_key": "hermes-candidate-004",
        },
    )
    assert response.status_code == 409
    assert "outside the exact admitted Context Pack" in response.json()["detail"]


def test_hermes_key_cannot_use_human_apply_gate() -> None:
    response = _client().post(
        "/agency/change-candidates/change-1/apply",
        headers={
            "Authorization": "Bearer hermes-key",
            "X-Pantheon-Actor": "hermes-runtime",
        },
        json={"idempotency_key": "apply-forbidden-001"},
    )
    assert response.status_code == 403
    assert "Hermes direct Agency Data writes are disabled" in response.json()["detail"]


def test_editor_key_cannot_impersonate_hermes_candidate_route() -> None:
    response = _client().post(
        _route(),
        headers=_headers("editor-key"),
        json={
            "expected_project_revision": 1,
            "proposed_attributes": {"budget": 375000},
            "source_refs": [],
            "idempotency_key": "hermes-candidate-005",
        },
    )
    assert response.status_code == 401


def test_legacy_versioned_route_is_absent() -> None:
    response = _client().post(
        "/v1/hermes/execution-admissions/admission-1/projects/p1/change-candidates",
        headers=_headers(),
        json={
            "expected_project_revision": 1,
            "proposed_attributes": {"budget": 375000},
            "source_refs": [],
            "idempotency_key": "hermes-candidate-006",
        },
    )
    assert response.status_code == 404