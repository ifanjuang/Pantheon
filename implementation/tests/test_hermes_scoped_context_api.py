"""HTTP boundary tests for exact running-run Hermes context access."""

from __future__ import annotations

from fastapi.testclient import TestClient

from mvp_vertical import hermes_scoped_context
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


def test_manifest_requires_hermes_key_and_actor(monkeypatch) -> None:
    observed = {}

    def manifest(_conn, **values):
        observed.update(values)
        return {
            "kind": "hermes_scoped_context_manifest",
            "admission_id": values["admission_id"],
            "run_id": values["run_id"],
            "entities": [],
            "global_search_available": False,
            "global_listing_available": False,
            "source_dereference_available": False,
            "write_effect": False,
        }

    monkeypatch.setattr(hermes_scoped_context, "get_context_manifest", manifest)
    client = _client()
    path = "/hermes/execution-admissions/admission-1/runs/run-1/context"

    wrong_key = client.get(
        path,
        headers={
            "Authorization": "Bearer editor-key",
            "X-Pantheon-Hermes-Actor": "hermes-runtime",
        },
    )
    assert wrong_key.status_code == 401

    missing_actor = client.get(
        path,
        headers={"Authorization": "Bearer hermes-key"},
    )
    assert missing_actor.status_code == 422

    accepted = client.get(
        path,
        headers={
            "Authorization": "Bearer hermes-key",
            "X-Pantheon-Hermes-Actor": "hermes-runtime",
        },
    )
    assert accepted.status_code == 200
    assert accepted.json()["global_search_available"] is False
    assert observed == {
        "admission_id": "admission-1",
        "run_id": "run-1",
        "actor": "hermes-runtime",
    }


def test_exact_entity_route_passes_only_requested_admitted_identity(monkeypatch) -> None:
    observed = {}

    def entity(_conn, **values):
        observed.update(values)
        return {
            "kind": "hermes_scoped_context_entity",
            "entity_ref": {
                "entity_type": values["entity_type"],
                "entity_id": values["entity_id"],
            },
            "record": {"project_id": "project-verger"},
            "write_effect": False,
        }

    monkeypatch.setattr(hermes_scoped_context, "get_context_entity", entity)
    client = _client()
    response = client.get(
        "/hermes/execution-admissions/admission-1/runs/run-1/context/entities/project/project:project-verger",
        headers={
            "Authorization": "Bearer hermes-key",
            "X-Pantheon-Hermes-Actor": "hermes-runtime",
        },
    )
    assert response.status_code == 200
    assert observed == {
        "admission_id": "admission-1",
        "run_id": "run-1",
        "entity_type": "project",
        "entity_id": "project:project-verger",
        "actor": "hermes-runtime",
    }


def test_scope_conflict_and_oversized_representation_fail_closed(monkeypatch) -> None:
    client = _client()
    headers = {
        "Authorization": "Bearer hermes-key",
        "X-Pantheon-Hermes-Actor": "hermes-runtime",
    }
    path = (
        "/hermes/execution-admissions/admission-1/runs/run-1/"
        "context/entities/person/person:outside"
    )

    monkeypatch.setattr(
        hermes_scoped_context,
        "get_context_entity",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            hermes_scoped_context.ScopedContextConflict("outside exact Context Pack")
        ),
    )
    outside = client.get(path, headers=headers)
    assert outside.status_code == 409

    monkeypatch.setattr(
        hermes_scoped_context,
        "get_context_entity",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            hermes_scoped_context.ScopedContextContentTooLarge("representation too large")
        ),
    )
    oversized = client.get(path, headers=headers)
    assert oversized.status_code == 413


def test_no_generic_scoped_search_or_source_dereference_route_exists() -> None:
    client = _client()
    headers = {
        "Authorization": "Bearer hermes-key",
        "X-Pantheon-Hermes-Actor": "hermes-runtime",
    }
    assert client.get(
        "/hermes/execution-admissions/admission-1/runs/run-1/context/search",
        headers=headers,
    ).status_code == 404
    assert client.get(
        "/hermes/execution-admissions/admission-1/runs/run-1/context/sources/source-1",
        headers=headers,
    ).status_code == 404