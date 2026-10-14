from __future__ import annotations

import asyncio

from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

from mvp_vertical.hermes_role_trace_relay import HermesRoleTraceRelay, install_role_trace_routes


async def _source(events):
    for event in events:
        await asyncio.sleep(0)
        yield event


def test_role_trace_relay_multiplexes_explicit_subagent_topology_on_one_source() -> None:
    async def scenario():
        relay = HermesRoleTraceRelay()
        run_id = "run_12345678"
        await relay.register(run_id)
        await relay.consume(
            run_id,
            _source(
                [
                    {
                        "event": "subagent.start",
                        "run_id": run_id,
                        "timestamp": 1,
                        "subagent_id": "sa-0-abcd1234",
                        "delegation_id": "dg-1",
                        "parent_id": None,
                        "depth": 0,
                        "goal": "Independent review",
                    },
                    {
                        "event": "subagent.complete",
                        "run_id": run_id,
                        "timestamp": 2,
                        "subagent_id": "sa-0-abcd1234",
                        "delegation_id": "dg-1",
                        "parent_id": None,
                        "depth": 0,
                        "status": "completed",
                        "summary": "Review complete.",
                        "duration_seconds": 1.1,
                    },
                    {"event": "run.completed", "run_id": run_id, "timestamp": 3},
                ]
            ),
        )
        events = [event async for event in relay.subscribe(run_id)]
        return relay.snapshot(run_id), events

    snapshot, events = asyncio.run(scenario())

    runtime = [event for event in events if event["event"] == "runtime.subagent"]
    assert len(runtime) == 2
    assert runtime[0]["phase"] == "started"
    assert runtime[1]["phase"] == "completed"
    assert runtime[0]["runtime_node_id"] == runtime[1]["runtime_node_id"]
    assert runtime[0]["relation_basis"] == "explicit_runtime_ids"
    assert runtime[0]["governed_identity"] is False
    assert snapshot["projected_event_kinds"] == ["role.stage", "runtime.subagent"]
    assert snapshot["runtime_relations"] == "explicit_ids_only"
    assert snapshot["persistence"] == "none"


def test_sse_preserves_distinct_role_and_runtime_event_names() -> None:
    relay = HermesRoleTraceRelay()

    async def prepare():
        run_id = "run_12345678"
        await relay.register(run_id)
        await relay.consume(
            run_id,
            _source(
                [
                    {
                        "event": "message.delta",
                        "run_id": run_id,
                        "delta": "🦉 Athena · Plan\nAction: cadrer\n",
                        "timestamp": 1,
                    },
                    {
                        "event": "subagent.start",
                        "run_id": run_id,
                        "subagent_id": "sa-0-abcd1234",
                        "goal": "Independent review",
                        "timestamp": 2,
                    },
                    {
                        "event": "subagent.complete",
                        "run_id": run_id,
                        "subagent_id": "sa-0-abcd1234",
                        "status": "completed",
                        "timestamp": 3,
                    },
                    {"event": "run.completed", "run_id": run_id, "timestamp": 4},
                ]
            ),
        )

    asyncio.run(prepare())
    app = FastAPI()

    def require_read_key(authorization: str | None = Header(default=None)) -> None:
        if authorization != "Bearer read-key":
            raise HTTPException(status_code=401, detail="invalid read API key")

    install_role_trace_routes(app, relay=relay, require_read_key=require_read_key)
    client = TestClient(app)
    with client.stream(
        "GET",
        "/cockpit/role-traces/run_12345678/events",
        headers={"Authorization": "Bearer read-key"},
    ) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert "event: role.stage\n" in body
    assert body.count("event: runtime.subagent\n") == 2
    assert "private_reasoning_included\":false" in body
    assert "governed_identity\":false" in body
