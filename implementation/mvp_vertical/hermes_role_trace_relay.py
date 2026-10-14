"""Bounded in-memory fan-out for one already-admitted Hermes public run stream.

One upstream consumer owns each run. Any number of bounded local readers may
observe the same derived Role-stage and explicit runtime-topology events without
competing for Hermes' source queue. The relay cannot create, stop, approve or
retry a run and persists nothing.
"""

from __future__ import annotations

import asyncio
import json
import re
from collections import deque
from collections.abc import AsyncIterable, AsyncIterator, Callable
from dataclasses import dataclass, field
from typing import Any

from .hermes_role_stage_projection import HermesRoleStageProjector
from .hermes_runtime_topology_projection import HermesRuntimeTopologyProjector


MAX_TRACES = 32
MAX_REPLAY_EVENTS = 500
MAX_UPSTREAM_EVENTS = 1_000
_RUN_ID = re.compile(r"^run_[A-Za-z0-9]{8,128}$")
_TERMINAL = {"run.completed", "run.failed", "run.cancelled", "run.interrupted"}
_PROJECTED_EVENT_NAMES = {"role.stage", "runtime.subagent"}


class HermesRoleTraceRelayError(RuntimeError):
    pass


class HermesRoleTraceNotFound(HermesRoleTraceRelayError):
    pass


class HermesRoleTraceReplayGap(HermesRoleTraceRelayError):
    pass


class HermesRunsRoleEventSource:
    """Read exactly one existing Hermes Runs SSE stream without control effects."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout: float = 180.0,
        client: Any | None = None,
    ) -> None:
        self._base_url = str(base_url or "").strip().rstrip("/")
        self._api_key = str(api_key or "").strip()
        self._timeout = timeout
        self._client = client
        if not self._base_url.startswith(("http://", "https://")):
            raise HermesRoleTraceRelayError("Hermes Runs base URL must be HTTP(S)")
        if not self._api_key:
            raise HermesRoleTraceRelayError("Hermes Runs API key is required")
        if timeout <= 0:
            raise HermesRoleTraceRelayError("Hermes Runs timeout must be positive")

    async def events(self, run_id: str) -> AsyncIterator[dict[str, Any]]:
        run_id = HermesRoleTraceRelay._run_id(run_id)
        client = self._client
        owns_client = client is None
        if owns_client:
            import httpx

            client = httpx.AsyncClient(timeout=self._timeout)
        count = 0
        terminal = False
        try:
            async with client.stream(
                "GET",
                f"{self._base_url}/v1/runs/{run_id}/events",
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=self._timeout,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or line.startswith(":") or not line.startswith("data:"):
                        continue
                    try:
                        event = json.loads(line.removeprefix("data:").strip())
                    except json.JSONDecodeError as exc:
                        raise HermesRoleTraceRelayError(
                            "Hermes Role source returned invalid SSE JSON"
                        ) from exc
                    if not isinstance(event, dict):
                        raise HermesRoleTraceRelayError(
                            "Hermes Role source event must be an object"
                        )
                    if str(event.get("run_id") or run_id) != run_id:
                        raise HermesRoleTraceRelayError(
                            "Hermes Role source crossed the requested run boundary"
                        )
                    count += 1
                    if count > MAX_UPSTREAM_EVENTS:
                        raise HermesRoleTraceRelayError(
                            f"Hermes Role source exceeds {MAX_UPSTREAM_EVENTS} events"
                        )
                    yield event
                    if str(event.get("event") or "") in _TERMINAL:
                        terminal = True
                        return
            if not terminal:
                raise HermesRoleTraceRelayError(
                    "Hermes Role source ended before a terminal event"
                )
        finally:
            if owns_client:
                await client.aclose()


@dataclass
class _Trace:
    run_id: str
    projector: HermesRoleStageProjector
    runtime_projector: HermesRuntimeTopologyProjector
    condition: asyncio.Condition = field(default_factory=asyncio.Condition)
    events: deque[dict[str, Any]] = field(
        default_factory=lambda: deque(maxlen=MAX_REPLAY_EVENTS)
    )
    next_cursor: int = 1
    source_attached: bool = False
    terminal: bool = False
    diagnostic: str | None = None


class HermesRoleTraceRelay:
    """One-source, bounded-replay, multi-reader observable Hermes trace relay."""

    def __init__(self, *, max_traces: int = MAX_TRACES) -> None:
        if max_traces < 1 or max_traces > MAX_TRACES:
            raise HermesRoleTraceRelayError(
                f"max_traces must be between 1 and {MAX_TRACES}"
            )
        self._max_traces = max_traces
        self._traces: dict[str, _Trace] = {}
        self._registry_lock = asyncio.Lock()
        self._source_tasks: set[asyncio.Task[None]] = set()

    def _finish_source_task(self, task: asyncio.Task[None]) -> None:
        self._source_tasks.discard(task)
        if not task.cancelled():
            task.exception()

    @staticmethod
    def _run_id(value: str) -> str:
        run_id = str(value or "").strip()
        if not _RUN_ID.fullmatch(run_id):
            raise HermesRoleTraceRelayError("invalid Hermes run_id")
        return run_id

    async def register(self, run_id: str) -> dict[str, Any]:
        """Register a run already created through the governed binding."""

        run_id = self._run_id(run_id)
        async with self._registry_lock:
            existing = self._traces.get(run_id)
            if existing is not None:
                return self.snapshot(run_id)
            if len(self._traces) >= self._max_traces:
                terminal = next(
                    (key for key, value in self._traces.items() if value.terminal), None
                )
                if terminal is None:
                    raise HermesRoleTraceRelayError("active Role trace capacity reached")
                self._traces.pop(terminal)
            self._traces[run_id] = _Trace(
                run_id=run_id,
                projector=HermesRoleStageProjector(run_id),
                runtime_projector=HermesRuntimeTopologyProjector(run_id),
            )
        return self.snapshot(run_id)

    def _trace(self, run_id: str) -> _Trace:
        normalized = self._run_id(run_id)
        try:
            return self._traces[normalized]
        except KeyError as exc:
            raise HermesRoleTraceNotFound(f"Role trace not found: {normalized}") from exc

    def snapshot(self, run_id: str) -> dict[str, Any]:
        trace = self._trace(run_id)
        first_cursor = trace.events[0]["cursor"] if trace.events else None
        last_cursor = trace.events[-1]["cursor"] if trace.events else None
        return {
            "run_id": trace.run_id,
            "source_attached": trace.source_attached,
            "terminal": trace.terminal,
            "diagnostic": trace.diagnostic,
            "retained_events": len(trace.events),
            "first_cursor": first_cursor,
            "last_cursor": last_cursor,
            "projected_event_kinds": sorted(_PROJECTED_EVENT_NAMES),
            "runtime_relations": "explicit_ids_only",
            "persistence": "none",
            "authority_effect": "none",
        }

    async def _publish(self, trace: _Trace, projected: list[dict[str, Any]]) -> None:
        if not projected:
            return
        async with trace.condition:
            for event in projected:
                event_name = str(event.get("event") or "")
                if event_name not in _PROJECTED_EVENT_NAMES:
                    raise HermesRoleTraceRelayError(
                        f"unsupported projected Hermes trace event: {event_name or '<empty>'}"
                    )
                trace.events.append({"cursor": trace.next_cursor, **event})
                trace.next_cursor += 1
            trace.condition.notify_all()

    async def consume(
        self,
        run_id: str,
        source: AsyncIterable[dict[str, Any]],
    ) -> None:
        """Consume the sole upstream event iterator for one registered run."""

        trace = self._trace(run_id)
        async with trace.condition:
            if trace.source_attached:
                raise HermesRoleTraceRelayError(
                    f"an upstream source is already attached for {trace.run_id}"
                )
            trace.source_attached = True
            trace.condition.notify_all()
        await self._consume_attached(trace, source)

    async def _consume_attached(
        self,
        trace: _Trace,
        source: AsyncIterable[dict[str, Any]],
    ) -> None:
        """Consume a source whose unique attachment has already been claimed."""

        try:
            async for raw_event in source:
                projected = trace.projector.feed(raw_event)
                projected.extend(trace.runtime_projector.feed(raw_event))
                await self._publish(trace, projected)
                if str(raw_event.get("event") or "") in _TERMINAL:
                    trace.terminal = True
                    break
        except Exception as exc:
            trace.diagnostic = f"upstream Role trace incomplete: {type(exc).__name__}"
            raise
        finally:
            if not trace.terminal and trace.diagnostic is None:
                trace.diagnostic = "upstream Role trace ended before a terminal event"
            trace.terminal = True
            async with trace.condition:
                trace.condition.notify_all()

    async def start_hermes_source(
        self,
        run_id: str,
        source: HermesRunsRoleEventSource,
    ) -> bool:
        """Attach one source in the background after governed start registration."""

        await self.register(run_id)
        trace = self._trace(run_id)
        async with trace.condition:
            if trace.source_attached:
                return False
            trace.source_attached = True
            trace.condition.notify_all()
        task = asyncio.create_task(
            self._consume_attached(trace, source.events(trace.run_id)),
            name=f"pantheon-role-trace-{trace.run_id}",
        )
        self._source_tasks.add(task)
        task.add_done_callback(self._finish_source_task)
        return True

    async def attach_hermes_source(
        self,
        run_id: str,
        source: HermesRunsRoleEventSource,
    ) -> None:
        """Register and consume one existing run through the fixed source."""

        await self.register(run_id)
        await self.consume(run_id, source.events(run_id))

    async def subscribe(
        self,
        run_id: str,
        *,
        after_cursor: int = 0,
    ) -> AsyncIterator[dict[str, Any]]:
        """Replay retained projections then follow the trace until terminal."""

        if after_cursor < 0:
            raise HermesRoleTraceRelayError("after_cursor cannot be negative")
        trace = self._trace(run_id)
        cursor = after_cursor
        while True:
            async with trace.condition:
                if trace.events and cursor < trace.events[0]["cursor"] - 1:
                    raise HermesRoleTraceReplayGap(
                        f"requested cursor {cursor} is outside the retained replay window"
                    )
                available = [event for event in trace.events if event["cursor"] > cursor]
                if not available and not trace.terminal:
                    await trace.condition.wait()
                    continue
                terminal = trace.terminal
            for event in available:
                cursor = int(event["cursor"])
                yield dict(event)
            if terminal:
                return


def install_role_trace_routes(
    app: Any,
    *,
    relay: HermesRoleTraceRelay,
    require_read_key: Callable[..., None],
    route_prefix: str = "/cockpit",
) -> None:
    """Install read-only Cockpit SSE routes over an injected relay."""

    from fastapi import Depends, Header, HTTPException
    from fastapi.responses import StreamingResponse

    prefix = route_prefix.rstrip("/")
    if not prefix.startswith("/") or "{" in prefix or "}" in prefix:
        raise HermesRoleTraceRelayError("invalid Role trace route prefix")

    @app.get(f"{prefix}/role-traces/{{run_id}}")
    async def role_trace_status(
        run_id: str,
        _authorized: None = Depends(require_read_key),
    ) -> dict[str, Any]:
        try:
            return relay.snapshot(run_id)
        except HermesRoleTraceNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except HermesRoleTraceRelayError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get(f"{prefix}/role-traces/{{run_id}}/events")
    async def role_trace_events(
        run_id: str,
        last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
        _authorized: None = Depends(require_read_key),
    ) -> StreamingResponse:
        try:
            after = int(last_event_id or 0)
            relay.snapshot(run_id)
        except HermesRoleTraceNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (ValueError, HermesRoleTraceRelayError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        async def stream() -> AsyncIterator[str]:
            try:
                async for event in relay.subscribe(run_id, after_cursor=after):
                    payload = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
                    event_name = str(event.get("event") or "")
                    yield f"id: {event['cursor']}\nevent: {event_name}\ndata: {payload}\n\n"
            except HermesRoleTraceReplayGap as exc:
                payload = json.dumps(
                    {"event": "role.trace.error", "detail": str(exc)},
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                yield f"event: role.trace.error\ndata: {payload}\n\n"

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
        )
