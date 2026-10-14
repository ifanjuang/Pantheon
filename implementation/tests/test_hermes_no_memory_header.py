from __future__ import annotations

import json

import httpx

from mvp_vertical.hermes_run_binding import HermesRunsHttpClient


def test_runs_client_never_sends_session_memory_header_or_provider_overrides() -> None:
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(202, json={"run_id": "run-1", "status": "started"})

    client = HermesRunsHttpClient(
        "http://hermes:8642/p/pantheon-governed",
        "api-key",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    response = client.submit(input_text="bounded", session_id="admission-1")

    assert response["run_id"] == "run-1"
    assert len(seen) == 1
    request = seen[0]
    body = json.loads(request.content)
    assert request.url.path == "/p/pantheon-governed/v1/runs"
    assert request.headers.get("authorization") == "Bearer api-key"
    assert request.headers.get("x-hermes-session-key") is None
    assert "model" not in body
    assert "provider" not in body
    assert "model_options" not in body
    assert "conversation_history" not in body
