"""Boundary tests for explicit human submission of a prepared Hermes handoff."""

from __future__ import annotations

from fastapi.testclient import TestClient

from mvp_vertical import card_scope, hermes_handoff_store
from mvp_vertical.cockpit_shell import create_cockpit_app


class _Connection:
    def close(self) -> None:
        pass


def _preview_body() -> dict:
    return {
        "question": "Quels points structurels faut-il vérifier ?",
        "card_context_envelope": {
            "root_entity": {"entity_id": "project:verger", "entity_type": "project"},
            "descendants": [],
            "source_refs": [],
            "explicit_additions": [],
            "explicit_exclusions": [],
            "scope_widened_implicitly": False,
        },
        "selected_context": [
            {"entity_id": "person:bet", "entity_type": "person"},
        ],
        "include_declared_descendants": False,
    }


def _submitted_body(preview: dict) -> dict:
    return {
        **_preview_body(),
        "expected_preview_digest": preview["preview_digest"],
        "expected_task_contract_ref": preview["task_contract"]["task_contract_ref"],
        "expected_context_pack_ref": preview["context_pack"]["context_pack_ref"],
        "idempotency_key": "handoff-submit-0001",
    }


def _patch_scope_validation(monkeypatch) -> None:
    monkeypatch.setattr(
        card_scope,
        "validate_entity_ref",
        lambda _conn, *, entity_ref: {**entity_ref, "source_refs": []},
    )
    monkeypatch.setattr(
        card_scope,
        "resolve_explicit_context",
        lambda _conn, *, entity_refs: {
            "entities": list(entity_refs),
            "source_refs": [],
        },
    )


def test_exact_preview_can_create_work_issue_without_starting_hermes(monkeypatch) -> None:
    observed = {}
    _patch_scope_validation(monkeypatch)

    def submit_handoff(_conn, **values):
        observed.update(values)
        return {
            "handoff_id": "handoff-1",
            "case_ref": "verger",
            "task_contract_ref": values["preview"]["task_contract"]["task_contract_ref"],
            "context_pack_ref": values["preview"]["context_pack"]["context_pack_ref"],
            "preview_digest": values["preview"]["preview_digest"],
            "work_issue": {
                "issue_id": "work-1",
                "assigned_to": "hermes",
                "status": "open",
                "requested_effect": "read_only",
            },
            "execution_started": False,
            "hermes_run_created": False,
            "status": "submitted_work_issue",
        }

    monkeypatch.setattr(hermes_handoff_store, "submit_handoff", submit_handoff)
    client = TestClient(
        create_cockpit_app(
            connect_fn=_Connection,
            api_key="read-key",
            editor_api_key="editor-key",
        )
    )

    preview_response = client.post(
        "/cockpit/hermes-handoffs/preview",
        headers={"Authorization": "Bearer read-key"},
        json=_preview_body(),
    )
    assert preview_response.status_code == 200
    preview = preview_response.json()

    submitted = client.post(
        "/cockpit/hermes-handoffs/submit",
        headers={
            "Authorization": "Bearer editor-key",
            "X-Pantheon-Human-Actor": "ifan",
        },
        json=_submitted_body(preview),
    )
    assert submitted.status_code == 201
    payload = submitted.json()
    assert payload["status"] == "submitted_work_issue"
    assert payload["work_issue"]["assigned_to"] == "hermes"
    assert payload["execution_started"] is False
    assert payload["hermes_run_created"] is False
    assert observed["actor"] == "ifan"
    assert observed["preview"]["preview_digest"] == preview["preview_digest"]
    assert observed["selected_context"] == [
        {"entity_id": "person:bet", "entity_type": "person"}
    ]


def test_submit_uses_revalidated_context_not_untrusted_request_copy(monkeypatch) -> None:
    observed = {}
    monkeypatch.setattr(
        card_scope,
        "validate_entity_ref",
        lambda _conn, *, entity_ref: {**entity_ref, "source_refs": []},
    )
    monkeypatch.setattr(
        card_scope,
        "resolve_explicit_context",
        lambda _conn, *, entity_refs: {
            "entities": [
                {"entity_id": "person:canonical", "entity_type": "person"}
            ] if entity_refs else [],
            "source_refs": [],
        },
    )

    def submit_handoff(_conn, **values):
        observed.update(values)
        return {
            "handoff_id": "handoff-1",
            "case_ref": "verger",
            "task_contract_ref": values["preview"]["task_contract"]["task_contract_ref"],
            "context_pack_ref": values["preview"]["context_pack"]["context_pack_ref"],
            "preview_digest": values["preview"]["preview_digest"],
            "work_issue": {"issue_id": "work-1", "assigned_to": "hermes"},
            "execution_started": False,
            "hermes_run_created": False,
            "status": "submitted_work_issue",
        }

    monkeypatch.setattr(hermes_handoff_store, "submit_handoff", submit_handoff)
    client = TestClient(
        create_cockpit_app(
            connect_fn=_Connection,
            api_key="read-key",
            editor_api_key="editor-key",
        )
    )
    preview = client.post(
        "/cockpit/hermes-handoffs/preview",
        headers={"Authorization": "Bearer read-key"},
        json=_preview_body(),
    ).json()
    response = client.post(
        "/cockpit/hermes-handoffs/submit",
        headers={
            "Authorization": "Bearer editor-key",
            "X-Pantheon-Human-Actor": "ifan",
        },
        json=_submitted_body(preview),
    )
    assert response.status_code == 201
    assert observed["selected_context"] == [
        {"entity_id": "person:canonical", "entity_type": "person"}
    ]


def test_stale_preview_is_refused_before_work_issue_creation(monkeypatch) -> None:
    called = False
    _patch_scope_validation(monkeypatch)

    def submit_handoff(_conn, **_values):
        nonlocal called
        called = True
        raise AssertionError("stale preview must not reach persistence")

    monkeypatch.setattr(hermes_handoff_store, "submit_handoff", submit_handoff)
    client = TestClient(
        create_cockpit_app(
            connect_fn=_Connection,
            api_key="read-key",
            editor_api_key="editor-key",
        )
    )
    preview = client.post(
        "/cockpit/hermes-handoffs/preview",
        headers={"Authorization": "Bearer read-key"},
        json=_preview_body(),
    ).json()
    body = _submitted_body(preview)
    body["expected_preview_digest"] = "0" * 64

    response = client.post(
        "/cockpit/hermes-handoffs/submit",
        headers={
            "Authorization": "Bearer editor-key",
            "X-Pantheon-Human-Actor": "ifan",
        },
        json=body,
    )
    assert response.status_code == 409
    assert "preview is stale" in response.json()["detail"]
    assert called is False


def test_handoff_submission_requires_editor_key_and_human_actor(monkeypatch) -> None:
    _patch_scope_validation(monkeypatch)
    client = TestClient(
        create_cockpit_app(
            connect_fn=_Connection,
            api_key="read-key",
            editor_api_key="editor-key",
        )
    )
    preview = client.post(
        "/cockpit/hermes-handoffs/preview",
        headers={"Authorization": "Bearer read-key"},
        json=_preview_body(),
    ).json()
    body = _submitted_body(preview)

    no_actor = client.post(
        "/cockpit/hermes-handoffs/submit",
        headers={"Authorization": "Bearer editor-key"},
        json=body,
    )
    assert no_actor.status_code == 422

    read_only_key = client.post(
        "/cockpit/hermes-handoffs/submit",
        headers={
            "Authorization": "Bearer read-key",
            "X-Pantheon-Human-Actor": "ifan",
        },
        json=body,
    )
    assert read_only_key.status_code == 401


def test_handoff_store_has_no_runtime_start_call() -> None:
    source = (
        __import__("pathlib").Path(hermes_handoff_store.__file__).read_text(encoding="utf-8")
    )
    assert "work_issues.create_issue" in source
    assert "start_hermes_run" not in source
    assert '"execution_started": False' in source
    assert '"hermes_run_created": False' in source
