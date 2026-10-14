from __future__ import annotations

from fastapi.testclient import TestClient

from mvp_vertical import knowledge_edit_variants
from mvp_vertical.cockpit_composed import create_composed_cockpit_app


class _Connection:
    def close(self) -> None:
        pass


def _review(status: str = "proposed") -> dict:
    return {
        "edit_request": {
            "request_id": "edit-1",
            "knowledge_id": "knowledge.techniques.cctp",
            "status": status,
            "base_version": 1,
            "requested_variant_count": 2,
            "selected_variant_id": None,
        },
        "variants": [],
        "review_events": [],
        "knowledge": {"knowledge_id": "knowledge.techniques.cctp", "version": 1},
        "execution_result_stored_is_variant_projected": False,
        "variant_selected_is_edit_applied": False,
        "proposal_is_evidence": False,
    }


def _client() -> TestClient:
    # This module exercises route wiring and actor extraction with the
    # underlying knowledge_edit_variants functions monkeypatched out, not the
    # chokepoint apply_selected_variant now routes through — that gate is
    # covered directly against the real functions in
    # test_knowledge_edit_and_publish_gate.py. Disabled here so a test with
    # no policy client configured is not a statement about the gate.
    return TestClient(
        create_composed_cockpit_app(
            connect_fn=_Connection,
            initialize_fn=None,
            api_key="read-key",
            editor_api_key="editor-key",
            hermes_api_key="hermes-key",
            policy_enforcement="disabled",
        )
    )


def test_variant_request_and_review_reads_require_editor_key(monkeypatch) -> None:
    observed = {}

    def create(_conn, **values):
        observed.update(values)
        return _review("queued_for_hermes")

    monkeypatch.setattr(knowledge_edit_variants, "create_variant_request", create)
    monkeypatch.setattr(
        knowledge_edit_variants,
        "list_variant_reviews",
        lambda _conn, **_values: [_review()],
    )
    client = _client()
    body = {
        "request_id": "edit-1",
        "instruction_kind": "rewrite",
        "instruction": "Produire deux variantes.",
        "base_version": 1,
        "selection_start": 10,
        "selection_end": 20,
        "selected_text": "sélection",
        "requested_by": "architecte",
        "requested_variant_count": 2,
        "idempotency_key": "variant-request-1",
    }

    assert client.post(
        "/knowledge/knowledge.techniques.cctp/variant-edit-requests",
        json=body,
        headers={"Authorization": "Bearer read-key"},
    ).status_code == 401
    created = client.post(
        "/knowledge/knowledge.techniques.cctp/variant-edit-requests",
        json=body,
        headers={"Authorization": "Bearer editor-key"},
    )
    assert created.status_code == 202
    assert created.json()["knowledge_mutated"] is False
    assert created.json()["execution_authorized"] is False
    assert observed["requested_variant_count"] == 2

    assert client.get(
        "/knowledge/knowledge.techniques.cctp/edit-reviews",
        headers={"Authorization": "Bearer read-key"},
    ).status_code == 401
    listed = client.get(
        "/knowledge/knowledge.techniques.cctp/edit-reviews",
        headers={"Authorization": "Bearer editor-key"},
    )
    assert listed.status_code == 200
    assert listed.json()["variant_selected_is_edit_applied"] is False


def test_execution_result_projection_is_editor_controlled_and_not_selection(monkeypatch) -> None:
    observed = {}

    def project(_conn, **values):
        observed.update(values)
        return _review()

    monkeypatch.setattr(
        knowledge_edit_variants,
        "project_execution_result_variant",
        project,
    )
    client = _client()
    route = "/execution-results/execution-1/results/result-a/project-knowledge-edit-variant"

    assert client.post(
        route,
        headers={
            "Authorization": "Bearer hermes-key",
            "Idempotency-Key": "project-variant-a",
        },
    ).status_code == 401
    projected = client.post(
        route,
        headers={
            "Authorization": "Bearer editor-key",
            "Idempotency-Key": "project-variant-a",
        },
    )
    assert projected.status_code == 200
    assert projected.json()["execution_result_mutated"] is False
    assert projected.json()["knowledge_mutated"] is False
    assert projected.json()["variant_selected"] is False
    assert projected.json()["edit_applied"] is False
    assert observed == {
        "execution_result_id": "execution-1",
        "result_ref": "result-a",
        "idempotency_key": "project-variant-a",
    }

    # The retired direct-Hermes submission route is deliberately absent.
    assert client.put(
        "/edit-requests/edit-1/variants/A",
        json={"replacement_markdown": "A"},
        headers={"Authorization": "Bearer hermes-key"},
    ).status_code in {404, 405}


def test_human_selects_rejects_and_applies_separately(monkeypatch) -> None:
    observed = {}

    def select(_conn, **values):
        observed["select"] = values
        return _review()

    monkeypatch.setattr(knowledge_edit_variants, "select_variant", select)
    monkeypatch.setattr(
        knowledge_edit_variants,
        "reject_request",
        lambda _conn, **values: observed.setdefault("reject", values) or _review("rejected"),
    )
    monkeypatch.setattr(
        knowledge_edit_variants,
        "apply_selected_variant",
        lambda _conn, **values: {
            "knowledge": {"knowledge_id": "knowledge.techniques.cctp", "version": 2},
            "edit_request": {"request_id": "edit-1", "status": "applied"},
            "review": _review("applied"),
            "observed": observed.setdefault("apply", values),
        },
    )
    client = _client()
    selection_body = {
        "variant_id": "edit-variant-a",
        "idempotency_key": "variant-selection-a",
    }

    assert client.post(
        "/edit-requests/edit-1/select-variant",
        json=selection_body,
        headers={"Authorization": "Bearer editor-key"},
    ).status_code == 422
    assert client.post(
        "/edit-requests/edit-1/select-variant",
        json=selection_body,
        headers={
            "Authorization": "Bearer hermes-key",
            "X-Pantheon-Human-Actor": "architecte",
        },
    ).status_code == 401
    selected = client.post(
        "/edit-requests/edit-1/select-variant",
        json=selection_body,
        headers={
            "Authorization": "Bearer editor-key",
            "X-Pantheon-Human-Actor": "architecte",
        },
    )
    assert selected.status_code == 200
    assert selected.json()["edit_applied"] is False
    assert selected.json()["knowledge_mutated"] is False
    assert observed["select"]["actor"] == "architecte"

    rejected = client.post(
        "/edit-requests/edit-1/reject",
        json={"reason": "Non retenue", "idempotency_key": "reject-variant-1"},
        headers={
            "Authorization": "Bearer editor-key",
            "X-Pantheon-Human-Actor": "architecte",
        },
    )
    assert rejected.status_code == 200
    assert rejected.json()["knowledge_mutated"] is False
    assert rejected.json()["evidence_admitted"] is False

    applied = client.post(
        "/edit-requests/edit-1/apply-selected",
        json={"idempotency_key": "apply-variant-1"},
        headers={
            "Authorization": "Bearer editor-key",
            "X-Pantheon-Human-Actor": "architecte",
        },
    )
    assert applied.status_code == 200
    assert applied.json()["edit_applied"] is True
    assert applied.json()["review_status_promoted"] is False
    assert applied.json()["evidence_admitted"] is False
