from __future__ import annotations

from fastapi.testclient import TestClient

from mvp_vertical import cockpit_composed, execution_result_api


class DummyConnection:
    def close(self) -> None:
        pass


def test_read_key_cannot_record_project_claim_candidate_disposition(monkeypatch) -> None:
    monkeypatch.setattr(
        execution_result_api.execution_results,
        "get_execution_result",
        lambda _conn, _execution_id: {"results": [{"result_id": "result.claim"}]},
    )
    monkeypatch.setattr(
        execution_result_api.execution_results,
        "append_review_disposition",
        lambda *_args, **_kwargs: {"review_dispositions": []},
    )

    app = cockpit_composed.create_composed_cockpit_app(
        connect_fn=DummyConnection,
        initialize_fn=None,
        api_key="read-secret",
        editor_api_key="editor-secret",
        hermes_api_key="hermes-secret",
    )

    with TestClient(app) as client:
        response = client.post(
            "/execution-results/execution.claim/results/result.claim/dispositions",
            headers={
                "Authorization": "Bearer read-secret",
                "X-Pantheon-Human-Actor": "human:test",
                "Idempotency-Key": "review-claim-candidate-001",
            },
            json={"disposition": "accepted_for_claim"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid editor API key"
