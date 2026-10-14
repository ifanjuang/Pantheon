from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from mvp_vertical.hermes_role_trace_relay import HermesRoleTraceRelay
from workspace_cockpit.role_server import create_app


class _Source:
    def events(self, run_id):
        async def stream():
            await asyncio.sleep(0)
            yield {
                "event": "message.delta",
                "run_id": run_id,
                "delta": "🦉 Athena · Plan\nAction: cadrer\n",
                "timestamp": 1,
            }
            yield {"event": "run.completed", "run_id": run_id, "timestamp": 2}

        return stream()


def test_sidecar_separates_attach_and_read_credentials() -> None:
    app = create_app(
        source=_Source(), relay=HermesRoleTraceRelay(),
        attach_key="attach-key", read_key="read-key",
    )
    client = TestClient(app)
    path = "/internal/role-traces/run_12345678/attach"
    assert client.post(path, headers={"Authorization": "Bearer read-key"}).status_code == 401
    attached = client.post(path, headers={"Authorization": "Bearer attach-key"})
    assert attached.status_code == 202
    assert attached.json()["attached"] is True

    latest = client.get(
        "/internal/role-traces/latest",
        headers={"Authorization": "Bearer read-key"},
    )
    assert latest.status_code == 200
    assert latest.json()["run_id"] == "run_12345678"

    with client.stream(
        "GET", "/internal/role-traces/run_12345678/events",
        headers={"Authorization": "Bearer read-key"},
    ) as response:
        body = "".join(response.iter_text())
    assert response.status_code == 200
    assert "event: role.stage" in body
    assert "reasoning.available" not in body
