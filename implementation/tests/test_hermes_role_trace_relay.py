from __future__ import annotations

import asyncio

import pytest
from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

from mvp_vertical.hermes_role_trace_relay import (
    HermesRoleTraceRelay,
    HermesRoleTraceRelayError,
    HermesRunsRoleEventSource,
    install_role_trace_routes,
)


async def _source(events):
    for event in events:
        await asyncio.sleep(0)
        yield event


class _UpstreamResponse:
    def __init__(self, lines):
        self._lines = lines

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    def raise_for_status(self):
        return None

    async def aiter_lines(self):
        for line in self._lines:
            yield line


class _UpstreamClient:
    def __init__(self, lines):
        self._lines = lines

    def stream(self, *_args, **_kwargs):
        return _UpstreamResponse(self._lines)


class _RoleSource:
    def __init__(self, events):
        self._events = events
        self.calls = []

    def events(self, run_id):
        self.calls.append(run_id)
        return _source(self._events)


def test_two_subscribers_receive_the_same_ordered_role_stages() -> None:
    async def scenario():
        relay = HermesRoleTraceRelay()
        run_id = "run_12345678"
        await relay.register(run_id)
        events = [
            {
                "event": "message.delta",
                "delta": "🦉 Athena · Plan\nAction: cadrer\n",
                "timestamp": 1,
            },
            {"event": "tool.started", "tool": "inventory", "timestamp": 2},
            {
                "event": "tool.completed",
                "tool": "inventory",
                "error": False,
                "timestamp": 3,
            },
            {"event": "run.completed", "timestamp": 4},
        ]
        consumer = asyncio.create_task(relay.consume(run_id, _source(events)))

        async def read_all():
            return [event async for event in relay.subscribe(run_id)]

        first, second = await asyncio.gather(read_all(), read_all())
        await consumer
        return relay, first, second

    relay, first, second = asyncio.run(scenario())
    assert first == second
    assert [event["cursor"] for event in first] == list(range(1, len(first) + 1))
    assert [event["visible_role"] for event in first] == [
        "Athena",
        "Athena",
        "Hermes",
        "Hermes",
        "Athena",
    ]
    assert relay.snapshot("run_12345678")["terminal"] is True
    assert relay.snapshot("run_12345678")["persistence"] == "none"


def test_relay_refuses_a_second_upstream_consumer() -> None:
    async def scenario():
        relay = HermesRoleTraceRelay()
        run_id = "run_abcdefgh"
        await relay.register(run_id)
        trace = relay._trace(run_id)
        trace.source_attached = True
        with pytest.raises(HermesRoleTraceRelayError, match="already attached"):
            await relay.consume(run_id, _source([]))

    asyncio.run(scenario())


def test_governed_start_callback_attaches_exactly_one_background_source() -> None:
    async def scenario():
        relay = HermesRoleTraceRelay()
        source = _RoleSource(
            [
                {
                    "event": "message.delta",
                    "delta": "⚖ Themis · Limite\nLimite: approbation requise\n",
                    "timestamp": 1,
                },
                {"event": "run.completed", "timestamp": 2},
            ]
        )
        first = await relay.start_hermes_source("run_12345678", source)
        second = await relay.start_hermes_source("run_12345678", source)
        events = [event async for event in relay.subscribe("run_12345678")]
        return first, second, source.calls, events

    first, second, calls, events = asyncio.run(scenario())
    assert first is True
    assert second is False
    assert calls == ["run_12345678"]
    assert events[-1]["visible_role"] == "Themis"
    assert events[-1]["phase"] == "completed"


def test_register_is_idempotent_and_run_ids_fail_closed() -> None:
    async def scenario():
        relay = HermesRoleTraceRelay()
        first = await relay.register("run_12345678")
        second = await relay.register("run_12345678")
        assert first == second
        with pytest.raises(HermesRoleTraceRelayError, match="invalid Hermes run_id"):
            await relay.register("../../state.db")

    asyncio.run(scenario())


def test_authenticated_http_surface_replays_a_finite_sse_trace() -> None:
    relay = HermesRoleTraceRelay()

    async def prepare():
        await relay.register("run_12345678")
        await relay.consume(
            "run_12345678",
            _source(
                [
                    {
                        "event": "message.delta",
                        "delta": "🦉 Athena · Plan\nAction: cadrer\n",
                        "timestamp": 1,
                    },
                    {"event": "run.completed", "timestamp": 2},
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

    assert client.get("/cockpit/role-traces/run_12345678").status_code == 401
    status = client.get(
        "/cockpit/role-traces/run_12345678",
        headers={"Authorization": "Bearer read-key"},
    )
    assert status.status_code == 200
    assert status.json()["terminal"] is True

    with client.stream(
        "GET",
        "/cockpit/role-traces/run_12345678/events",
        headers={"Authorization": "Bearer read-key"},
    ) as response:
        body = "".join(response.iter_text())
    assert response.status_code == 200
    assert body.count("event: role.stage\n") == 3
    assert "private scratchpad" not in body


def test_fixed_hermes_source_reads_one_terminal_run_stream() -> None:
    async def scenario():
        run_id = "run_12345678"
        lines = [
            ": keepalive",
            'data: {"event":"tool.started","run_id":"run_12345678","tool":"inventory"}',
            'data: {"event":"run.completed","run_id":"run_12345678"}',
        ]
        source = HermesRunsRoleEventSource(
            "http://hermes.invalid",
            "api-key",
            client=_UpstreamClient(lines),
        )
        return [event async for event in source.events(run_id)]

    events = asyncio.run(scenario())
    assert [event["event"] for event in events] == ["tool.started", "run.completed"]


def test_fixed_hermes_source_refuses_cross_run_events() -> None:
    async def scenario():
        source = HermesRunsRoleEventSource(
            "http://hermes.invalid",
            "api-key",
            client=_UpstreamClient(
                ['data: {"event":"run.completed","run_id":"run_other999"}']
            ),
        )
        with pytest.raises(HermesRoleTraceRelayError, match="crossed"):
            _ = [event async for event in source.events("run_12345678")]

    asyncio.run(scenario())
