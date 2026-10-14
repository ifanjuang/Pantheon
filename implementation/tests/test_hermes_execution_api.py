"""API boundary tests for execution admission and external Hermes callbacks."""

from __future__ import annotations

from fastapi.testclient import TestClient

from mvp_vertical import hermes_execution
from mvp_vertical.cockpit_shell import create_cockpit_app


class _Connection:
    def close(self) -> None: pass


def _client() -> TestClient:
    return TestClient(create_cockpit_app(
        connect_fn=_Connection, api_key="read-key", editor_api_key="editor-key", hermes_api_key="hermes-key"
    ))


def test_human_can_admit_exact_handoff_with_explicit_ttl(monkeypatch) -> None:
    observed = {}
    def admit_handoff(_conn, **values):
        observed.update(values)
        return {
            "admission_id":"admission-1", "handoff_id":values["handoff_id"], "decision":"allow",
            "requested_effect":"read_only", "admission_state":"admitted", "ready_for_external_runtime":True,
            "runtime_started":False, "consumed_by_run_id":None, "ttl_seconds":values["ttl_seconds"],
        }
    monkeypatch.setattr(hermes_execution, "admit_handoff", admit_handoff)
    response = _client().post(
        "/cockpit/hermes-handoffs/handoff-1/admissions",
        headers={"Authorization":"Bearer editor-key","X-Pantheon-Human-Actor":"ifan"},
        json={"ttl_seconds":900,"idempotency_key":"execution-admit-001"},
    )
    assert response.status_code == 201
    assert response.json()["ttl_seconds"] == 900
    assert observed == {"handoff_id":"handoff-1","actor":"ifan","idempotency_key":"execution-admit-001","ttl_seconds":900}


def test_admission_requires_explicit_bounded_ttl() -> None:
    client = _client()
    headers={"Authorization":"Bearer editor-key","X-Pantheon-Human-Actor":"ifan"}
    assert client.post(
        "/cockpit/hermes-handoffs/handoff-1/admissions", headers=headers,
        json={"idempotency_key":"execution-admit-001"},
    ).status_code == 422
    assert client.post(
        "/cockpit/hermes-handoffs/handoff-1/admissions", headers=headers,
        json={"ttl_seconds":86401,"idempotency_key":"execution-admit-001"},
    ).status_code == 422


def test_human_can_read_and_revoke_admission_but_not_after_runtime_semantics(monkeypatch) -> None:
    monkeypatch.setattr(hermes_execution, "get_admission", lambda _conn, admission_id: {
        "admission_id":admission_id,"admission_state":"admitted","ready_for_external_runtime":True
    })
    observed = {}
    def revoke(_conn, **values):
        observed.update(values)
        return {"admission_id":values["admission_id"],"admission_state":"revoked","ready_for_external_runtime":False,"revocation_reason":values["reason"]}
    monkeypatch.setattr(hermes_execution, "revoke_admission", revoke)
    client = _client()
    headers={"Authorization":"Bearer editor-key","X-Pantheon-Human-Actor":"ifan"}
    read = client.get("/cockpit/hermes-execution-admissions/admission-1", headers={"Authorization":"Bearer editor-key"})
    assert read.status_code == 200
    assert read.json()["admission_state"] == "admitted"
    revoked = client.post(
        "/cockpit/hermes-execution-admissions/admission-1/revocations", headers=headers,
        json={"reason":"Contexte devenu obsolète","idempotency_key":"admission-revoke-001"},
    )
    assert revoked.status_code == 201
    assert revoked.json()["admission_state"] == "revoked"
    assert observed["actor"] == "ifan"


def test_execution_envelope_is_hermes_only_and_lookup_requires_admission_id(monkeypatch) -> None:
    monkeypatch.setattr(hermes_execution, "get_execution_envelope", lambda _conn, admission_id: {
        "kind":"hermes_execution_envelope","admission":{"admission_id":admission_id},"dispatch_requested":False
    })
    client = _client()
    assert client.get("/hermes/execution-admissions/admission-1", headers={"Authorization":"Bearer editor-key"}).status_code == 401
    accepted = client.get("/hermes/execution-admissions/admission-1", headers={"Authorization":"Bearer hermes-key"})
    assert accepted.status_code == 200
    assert accepted.json()["dispatch_requested"] is False
    assert client.get("/hermes/execution-admissions", headers={"Authorization":"Bearer hermes-key"}).status_code == 404


def test_only_external_hermes_can_report_runtime_start(monkeypatch) -> None:
    observed = {}
    def record(_conn, **values):
        observed.update(values)
        return {"admission_id":values["admission_id"],"run_id":values["run_id"],"runtime_start_recorded":True,"replayed":False,"work_issue":{"status":"in_progress"}}
    monkeypatch.setattr(hermes_execution, "record_external_runtime_start", record)
    client = _client()
    body={"run_id":"hermes-runtime-123","expected_issue_version":1,"idempotency_key":"runtime-start-123"}
    assert client.post(
        "/hermes/execution-admissions/admission-1/runs/start",
        headers={"Authorization":"Bearer editor-key","X-Pantheon-Hermes-Actor":"hermes-adapter"}, json=body,
    ).status_code == 401
    assert client.post(
        "/hermes/execution-admissions/admission-1/runs/start",
        headers={"Authorization":"Bearer hermes-key"}, json=body,
    ).status_code == 422
    started = client.post(
        "/hermes/execution-admissions/admission-1/runs/start",
        headers={"Authorization":"Bearer hermes-key","X-Pantheon-Hermes-Actor":"hermes-adapter"}, json=body,
    )
    assert started.status_code == 201
    assert observed["run_id"] == "hermes-runtime-123"
    assert observed["actor"] == "hermes-adapter"


def test_recorded_runtime_start_notifies_optional_display_observer(monkeypatch) -> None:
    monkeypatch.setattr(hermes_execution, "record_external_runtime_start", lambda _conn, **values: {
        "admission_id": values["admission_id"], "run_id": values["run_id"],
        "runtime_start_recorded": True, "replayed": False, "work_issue": {"status": "in_progress"},
    })
    client = _client()
    observed = []

    async def observer(run_id):
        observed.append(run_id)

    client.app.state.hermes_runtime_start_observer = observer
    response = client.post(
        "/hermes/execution-admissions/admission-1/runs/start",
        headers={"Authorization": "Bearer hermes-key", "X-Pantheon-Hermes-Actor": "hermes-adapter"},
        json={"run_id": "run_12345678", "expected_issue_version": 1, "idempotency_key": "runtime-start-123"},
    )
    assert response.status_code == 201
    assert observed == ["run_12345678"]
