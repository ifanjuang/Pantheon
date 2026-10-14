"""API checks for bounded Hermes runtime returns and separate rich candidates."""

from __future__ import annotations

from fastapi.testclient import TestClient

from mvp_vertical import hermes_runtime_return
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


def _body() -> dict:
    return {
        "normalized_return": {
            "outcome": "result_candidate",
            "summary": "Résultat à relire",
            "trace_refs": ["hermes://trace/123"],
            "result_refs": [],
            "evidence_candidate_refs": [],
        },
        "result_candidate": {
            "result_type": "project_analysis",
            "candidate_payload": {"finding_count": 2},
            "confidence_note": "À vérifier",
            "known_limits": ["source incomplète"],
            "open_questions": ["validation BET ?"],
            "source_refs": ["nas://project/source.pdf"],
            "missing_evidence": ["note de calcul"],
        },
        "expected_issue_version": 2,
        "idempotency_key": "runtime-return-123",
    }


def test_only_hermes_can_report_normalized_return_and_rich_candidate(monkeypatch) -> None:
    observed = {}

    def record(_conn, **values):
        observed.update(values)
        return {
            "admission_id": values["admission_id"],
            "run_id": values["run_id"],
            "runtime_return_recorded": True,
            "runtime_status": "returned",
            "work_issue": {"status": "review"},
            "result_status": "candidate",
            "result_candidate": {"result_candidate_id": "result-candidate-1"},
            "evidence_admitted": False,
            "issue_closed": False,
        }

    monkeypatch.setattr(hermes_runtime_return, "record_external_runtime_return", record)
    client = _client()
    body = _body()

    denied = client.post(
        "/hermes/execution-admissions/admission-1/runs/run-1/return",
        headers={
            "Authorization": "Bearer editor-key",
            "X-Pantheon-Hermes-Actor": "hermes-adapter",
        },
        json=body,
    )
    assert denied.status_code == 401

    accepted = client.post(
        "/hermes/execution-admissions/admission-1/runs/run-1/return",
        headers={
            "Authorization": "Bearer hermes-key",
            "X-Pantheon-Hermes-Actor": "hermes-adapter",
        },
        json=body,
    )
    assert accepted.status_code == 200
    payload = accepted.json()
    assert payload["result_status"] == "candidate"
    assert payload["evidence_admitted"] is False
    assert payload["issue_closed"] is False
    assert observed["admission_id"] == "admission-1"
    assert observed["run_id"] == "run-1"
    assert observed["normalized_return"] == body["normalized_return"]
    assert observed["result_candidate"] == body["result_candidate"]


def test_return_shape_requires_summary_and_trace_refs() -> None:
    client = _client()
    response = client.post(
        "/hermes/execution-admissions/admission-1/runs/run-1/return",
        headers={
            "Authorization": "Bearer hermes-key",
            "X-Pantheon-Hermes-Actor": "hermes-adapter",
        },
        json={
            "normalized_return": {"outcome": "result_candidate"},
            "result_candidate": {"result_type": "analysis"},
            "expected_issue_version": 2,
            "idempotency_key": "runtime-return-invalid",
        },
    )
    assert response.status_code == 422


def test_bounded_return_still_rejects_rich_fields_inline() -> None:
    client = _client()
    body = _body()
    body["normalized_return"]["source_refs"] = ["nas://project/source.pdf"]
    response = client.post(
        "/hermes/execution-admissions/admission-1/runs/run-1/return",
        headers={
            "Authorization": "Bearer hermes-key",
            "X-Pantheon-Hermes-Actor": "hermes-adapter",
        },
        json=body,
    )
    assert response.status_code == 422


def test_rich_candidate_rejects_undeclared_fields() -> None:
    client = _client()
    body = _body()
    body["result_candidate"]["approval"] = True
    response = client.post(
        "/hermes/execution-admissions/admission-1/runs/run-1/return",
        headers={
            "Authorization": "Bearer hermes-key",
            "X-Pantheon-Hermes-Actor": "hermes-adapter",
        },
        json=body,
    )
    assert response.status_code == 422