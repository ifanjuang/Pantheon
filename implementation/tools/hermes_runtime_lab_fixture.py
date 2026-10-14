#!/usr/bin/env python3
"""Deterministic local services for the Hermes 0.20.0 lab acceptance.

The fixture provides a local OpenAI-compatible provider and a bounded synthetic
Pantheon API. It exercises Hermes' native progressive tool disclosure:
``tool_search`` -> ``tool_describe`` -> ``tool_call``. Successful provider
responses honor the runtime's ``stream: true`` request with OpenAI-compatible
SSE chunks; errors remain bounded JSON responses. The journal retains only
sanitized routes, header presence, body keys and tool schema names/shapes. It
never stores prompts, tool arguments, credentials or raw provider payloads.
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlsplit

ADMISSION_ID = "admission-hermes-020-lab"
PANTHEON_KEY = "pantheon-lab-key"
PROFILE_ENTITY_TYPE = "project"
PROFILE_ENTITY_ID = "project-lab"
OUTSIDE_ENTITY_ID = "project-outside"
GOVERNED_TOOLS = {"pantheon_context_manifest", "pantheon_context_entity"}
BRIDGE_TOOLS = {"tool_search", "tool_describe", "tool_call"}
SENTINEL_TOOL = "pantheon_effect_sentinel"
SENTINEL_MARKER = "PANTHEON_EFFECT_SENTINEL_V1"
SENTINEL_EXPECT_BLOCK = "EXPECT_BLOCK"
SENTINEL_EXPECT_FAIL_OPEN = "EXPECT_FAIL_OPEN"


def _tool_name(item: Any) -> str:
    if not isinstance(item, dict):
        return ""
    function = item.get("function")
    if isinstance(function, dict):
        nested = str(function.get("name") or "").strip()
        if nested:
            return nested
    return str(item.get("name") or "").strip()


def _tool_metadata(body: dict[str, Any] | None) -> dict[str, Any]:
    tools = body.get("tools") if isinstance(body, dict) else None
    if not isinstance(tools, list):
        return {"tool_count": 0, "tool_names": [], "tool_entry_shapes": []}
    return {
        "tool_count": len(tools),
        "tool_names": sorted({name for name in map(_tool_name, tools) if name}),
        "tool_entry_shapes": sorted(
            {
                ",".join(sorted(str(key) for key in item))
                if isinstance(item, dict)
                else type(item).__name__
                for item in tools
            }
        ),
    }


def _tool_result_messages(messages: list[Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in messages
        if isinstance(item, dict) and item.get("role") == "tool"
    ]


def _user_text(messages: list[Any]) -> str:
    parts: list[str] = []
    for item in messages:
        if not isinstance(item, dict) or item.get("role") != "user":
            continue
        content = item.get("content")
        if isinstance(content, str):
            parts.append(content)
    return "\n".join(parts)


def _tool_call_message(step: int, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"chatcmpl-hermes-020-lab-{step}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "lab-model",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": f"call-hermes-020-lab-{step}",
                            "type": "function",
                            "function": {
                                "name": name,
                                "arguments": json.dumps(arguments),
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }


class LabState:
    def __init__(self, journal: Path) -> None:
        self.journal = journal
        self.lock = threading.Lock()
        self.provider_calls = 0
        self.pantheon_reads: list[str] = []
        self.pantheon_writes: list[str] = []
        self.last_provider_tool_names: list[str] = []
        self.last_provider_tool_shapes: list[str] = []

    def record(self, payload: dict[str, Any]) -> None:
        rendered = json.dumps(
            {"recorded_at": time.time(), **payload},
            ensure_ascii=False,
            sort_keys=True,
        )
        with self.lock:
            self.journal.parent.mkdir(parents=True, exist_ok=True)
            with self.journal.open("a", encoding="utf-8") as handle:
                handle.write(rendered + "\n")

    def note_provider_tools(self, metadata: dict[str, Any]) -> None:
        with self.lock:
            self.last_provider_tool_names = list(metadata["tool_names"])
            self.last_provider_tool_shapes = list(metadata["tool_entry_shapes"])

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return {
                "provider_calls": self.provider_calls,
                "pantheon_reads": list(self.pantheon_reads),
                "pantheon_writes": list(self.pantheon_writes),
                "last_provider_tool_names": list(self.last_provider_tool_names),
                "last_provider_tool_shapes": list(self.last_provider_tool_shapes),
            }


class Handler(BaseHTTPRequestHandler):
    server_version = "PantheonHermesLab/4"

    @property
    def state(self) -> LabState:
        return self.server.lab_state  # type: ignore[attr-defined]

    def log_message(self, fmt: str, *args: object) -> None:
        del fmt, args

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        value = json.loads(raw.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("request body must be an object")
        return value

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_sse(self, events: Iterable[dict[str, Any]]) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        for event in events:
            encoded = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
            self.wfile.write(f"data: {encoded}\n\n".encode("utf-8"))
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()

    def _send_completion(
        self,
        request_body: dict[str, Any],
        response: dict[str, Any],
    ) -> None:
        if request_body.get("stream") is not True:
            self._send(HTTPStatus.OK, response)
            return

        choices = response.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            self._send(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": "laboratory completion has no valid choice"},
            )
            return
        choice = choices[0]
        message = choice.get("message")
        if not isinstance(message, dict):
            self._send(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": "laboratory completion has no valid message"},
            )
            return

        completion_id = str(response.get("id") or "chatcmpl-hermes-020-lab")
        created = int(response.get("created") or time.time())
        model = str(response.get("model") or "lab-model")

        def chunk(delta: dict[str, Any], finish_reason: str | None) -> dict[str, Any]:
            return {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": delta,
                        "finish_reason": finish_reason,
                    }
                ],
            }

        events: list[dict[str, Any]] = []
        tool_calls = message.get("tool_calls")
        if isinstance(tool_calls, list) and tool_calls:
            streamed_calls: list[dict[str, Any]] = []
            for index, raw_call in enumerate(tool_calls):
                if not isinstance(raw_call, dict):
                    continue
                function = raw_call.get("function")
                if not isinstance(function, dict):
                    continue
                streamed_calls.append(
                    {
                        "index": index,
                        "id": str(raw_call.get("id") or f"call-hermes-020-lab-{index}"),
                        "type": str(raw_call.get("type") or "function"),
                        "function": {
                            "name": str(function.get("name") or ""),
                            "arguments": str(function.get("arguments") or ""),
                        },
                    }
                )
            if not streamed_calls:
                self._send(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": "laboratory completion has no valid streamed tool call"},
                )
                return
            events.append(chunk({"role": "assistant", "tool_calls": streamed_calls}, None))
            events.append(chunk({}, str(choice.get("finish_reason") or "tool_calls")))
        else:
            content = message.get("content")
            events.append(
                chunk(
                    {
                        "role": "assistant",
                        "content": "" if content is None else str(content),
                    },
                    None,
                )
            )
            events.append(chunk({}, str(choice.get("finish_reason") or "stop")))

        stream_options = request_body.get("stream_options")
        if (
            isinstance(stream_options, dict)
            and stream_options.get("include_usage") is True
            and isinstance(response.get("usage"), dict)
        ):
            events.append(
                {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model,
                    "choices": [],
                    "usage": response["usage"],
                }
            )
        self._send_sse(events)

    def _journal(self, body: dict[str, Any] | None = None) -> None:
        metadata = _tool_metadata(body)
        if urlsplit(self.path).path == "/v1/chat/completions":
            self.state.note_provider_tools(metadata)
        self.state.record(
            {
                "method": self.command,
                "path": urlsplit(self.path).path,
                "authorization_present": bool(self.headers.get("Authorization")),
                "session_memory_header_present": bool(
                    self.headers.get("X-Hermes-Session-Key")
                ),
                "pantheon_actor": self.headers.get("X-Pantheon-Hermes-Actor"),
                "body_keys": sorted(body) if isinstance(body, dict) else [],
                **metadata,
            }
        )

    def _pantheon_auth_ok(self) -> bool:
        return self.headers.get("Authorization") == f"Bearer {PANTHEON_KEY}"

    def do_GET(self) -> None:  # noqa: N802
        path = unquote(urlsplit(self.path).path)
        self._journal()
        if path == "/health":
            self._send(HTTPStatus.OK, {"status": "ok"})
            return
        if path == "/v1/models":
            self._send(
                HTTPStatus.OK,
                {
                    "object": "list",
                    "data": [
                        {"id": "lab-model", "object": "model", "owned_by": "pantheon-lab"}
                    ],
                },
            )
            return
        if path == "/_lab/state":
            self._send(HTTPStatus.OK, self.state.snapshot())
            return

        prefix = f"/hermes/execution-admissions/{ADMISSION_ID}/active-context"
        if path.startswith(prefix):
            if not self._pantheon_auth_ok():
                self._send(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            with self.state.lock:
                self.state.pantheon_reads.append(path)
            if path == prefix:
                self._send(
                    HTTPStatus.OK,
                    {
                        "kind": "active_context_manifest",
                        "admission_id": ADMISSION_ID,
                        "entities": [
                            {
                                "entity_type": PROFILE_ENTITY_TYPE,
                                "entity_id": PROFILE_ENTITY_ID,
                                "digest": "sha256:" + "1" * 64,
                            }
                        ],
                        "technical_fixture": True,
                        "evidence_admitted": False,
                    },
                )
                return
            entity_prefix = prefix + "/entities/"
            if path == entity_prefix + f"{PROFILE_ENTITY_TYPE}/{PROFILE_ENTITY_ID}":
                self._send(
                    HTTPStatus.OK,
                    {
                        "entity_type": PROFILE_ENTITY_TYPE,
                        "entity_id": PROFILE_ENTITY_ID,
                        "payload": {"name": "Hermes 0.20 laboratory project"},
                        "source": "synthetic_lab_fixture",
                        "evidence_admitted": False,
                    },
                )
                return
            if path == entity_prefix + f"{PROFILE_ENTITY_TYPE}/{OUTSIDE_ENTITY_ID}":
                self._send(
                    HTTPStatus.NOT_FOUND,
                    {"error": "entity is outside the admitted Context Pack"},
                )
                return
        self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = unquote(urlsplit(self.path).path)
        try:
            body = self._read_json()
        except Exception as exc:
            self._journal()
            self._send(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        self._journal(body)
        if path == "/v1/chat/completions":
            self._handle_chat(body)
            return

        admission_prefix = f"/hermes/execution-admissions/{ADMISSION_ID}/"
        if path.startswith(admission_prefix):
            if not self._pantheon_auth_ok():
                self._send(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            with self.state.lock:
                self.state.pantheon_writes.append(path)
            if path.endswith("/launch-reservations"):
                self._send(
                    HTTPStatus.CREATED,
                    {
                        "launch_reservation_id": "launch-reservation-hermes-020-lab",
                        "snapshot_id": "launch-snapshot-hermes-020-lab",
                        "snapshot_digest": "sha256:" + "2" * 64,
                        "work_issue_version": 1,
                        "replayed": False,
                        "snapshot": {
                            "kind": "hermes_launch_context_snapshot",
                            "question": (
                                "Read the admitted manifest and project, then verify "
                                "that an outside project is refused."
                            ),
                            "field_projection_version": "hermes-020-lab",
                            "entities": [
                                {"entity_type": PROFILE_ENTITY_TYPE, "entity_id": PROFILE_ENTITY_ID}
                            ],
                        },
                    },
                )
                return
            if path.endswith("/runs/start"):
                self._send(
                    HTTPStatus.CREATED,
                    {
                        "runtime_start_recorded": True,
                        "work_issue": {"version": 2},
                        "task_authorized": False,
                        "evidence_admitted": False,
                    },
                )
                return
            if "/runs/" in path and path.endswith("/return"):
                self._send(
                    HTTPStatus.CREATED,
                    {
                        "runtime_return_recorded": True,
                        "work_issue": {"version": 3},
                        "result_accepted": False,
                        "evidence_admitted": False,
                        "project_mutated": False,
                    },
                )
                return
        self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def _handle_sentinel_chat(
        self,
        body: dict[str, Any],
        results: list[dict[str, Any]],
        prompt_text: str,
        step: int,
    ) -> None:
        expect_block = SENTINEL_EXPECT_BLOCK in prompt_text
        expect_fail_open = SENTINEL_EXPECT_FAIL_OPEN in prompt_text
        if expect_block == expect_fail_open:
            self._send(
                HTTPStatus.BAD_REQUEST,
                {"error": "sentinel prompt must select exactly one expected outcome"},
            )
            return

        marker_value = "block" if expect_block else "raise"
        if step == 0:
            response = _tool_call_message(
                step,
                "tool_search",
                {"queries": ["pantheon effect sentinel"], "limit": 5},
            )
        elif step == 1:
            response = _tool_call_message(
                step,
                "tool_describe",
                {"names": [SENTINEL_TOOL]},
            )
        elif step == 2:
            response = _tool_call_message(
                step,
                "tool_call",
                {"name": SENTINEL_TOOL, "arguments": {"marker": marker_value}},
            )
        else:
            tool_result = str(results[2].get("content", "")) if len(results) > 2 else ""
            if expect_block:
                observed = "PANTHEON_SENTINEL_BLOCKED" in tool_result
                final = "SENTINEL_BLOCK_CONFIRMED"
            else:
                observed = "effect_ran" in tool_result and "true" in tool_result.lower()
                final = "SENTINEL_FAIL_OPEN_CONFIRMED"
            if not observed:
                self._send(
                    HTTPStatus.BAD_REQUEST,
                    {
                        "error": "sentinel outcome did not match the requested observation",
                        "expected": marker_value,
                    },
                )
                return
            response = {
                "id": f"chatcmpl-hermes-sentinel-{marker_value}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "lab-model",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": final},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            }
        self._send_completion(body, response)

    def _handle_chat(self, body: dict[str, Any]) -> None:
        messages = body.get("messages")
        if not isinstance(messages, list):
            self._send(HTTPStatus.BAD_REQUEST, {"error": "messages required"})
            return
        available = set(_tool_metadata(body)["tool_names"])
        if not BRIDGE_TOOLS.issubset(available):
            self._send(
                HTTPStatus.BAD_REQUEST,
                {
                    "error": "Hermes progressive disclosure bridge is incomplete",
                    "available_tool_names": sorted(available),
                    "required_tool_names": sorted(BRIDGE_TOOLS),
                },
            )
            return

        results = _tool_result_messages(messages)
        step = len(results)
        with self.state.lock:
            self.state.provider_calls += 1

        prompt_text = _user_text(messages)
        if SENTINEL_MARKER in prompt_text:
            self._handle_sentinel_chat(body, results, prompt_text, step)
            return

        if step == 0:
            response = _tool_call_message(
                step,
                "tool_search",
                {"queries": ["pantheon context manifest", "pantheon context entity"], "limit": 5},
            )
        elif step == 1:
            response = _tool_call_message(
                step,
                "tool_describe",
                {"names": ["pantheon_context_manifest"]},
            )
        elif step == 2:
            response = _tool_call_message(
                step,
                "tool_call",
                {"name": "pantheon_context_manifest", "arguments": {}},
            )
        elif step == 3:
            response = _tool_call_message(
                step,
                "tool_describe",
                {"names": ["pantheon_context_entity"]},
            )
        elif step == 4:
            response = _tool_call_message(
                step,
                "tool_call",
                {
                    "name": "pantheon_context_entity",
                    "arguments": {
                        "entity_type": PROFILE_ENTITY_TYPE,
                        "entity_id": PROFILE_ENTITY_ID,
                    },
                },
            )
        elif step == 5:
            response = _tool_call_message(
                step,
                "tool_call",
                {
                    "name": "pantheon_context_entity",
                    "arguments": {
                        "entity_type": PROFILE_ENTITY_TYPE,
                        "entity_id": OUTSIDE_ENTITY_ID,
                    },
                },
            )
        else:
            search_result = str(results[0].get("content", "")) if len(results) > 0 else ""
            manifest_result = str(results[2].get("content", "")) if len(results) > 2 else ""
            admitted_result = str(results[4].get("content", "")) if len(results) > 4 else ""
            refused_result = str(results[5].get("content", "")) if len(results) > 5 else ""
            checks = {
                "search_found_manifest": "pantheon_context_manifest" in search_result,
                "search_found_entity": "pantheon_context_entity" in search_result,
                "manifest_returned": "active_context_manifest" in manifest_result,
                "admitted_entity_returned": PROFILE_ENTITY_ID in admitted_result,
                "outside_entity_refused": (
                    "HTTP 404" in refused_result or "outside" in refused_result
                ),
            }
            if not all(checks.values()):
                self._send(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "progressive tool checks failed", "checks": checks},
                )
                return
            response = {
                "id": "chatcmpl-hermes-020-lab-final",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "lab-model",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": (
                                "LAB_ACCEPTANCE_COMPLETED: progressive discovery, "
                                "manifest read, admitted entity read, outside entity refused."
                            ),
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
            }
        self._send_completion(body, response)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9010)
    parser.add_argument("--journal", type=Path, required=True)
    args = parser.parse_args()

    state = LabState(args.journal)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.lab_state = state  # type: ignore[attr-defined]
    print(
        f"Hermes 0.20 lab fixture listening on http://{args.host}:{args.port}",
        flush=True,
    )
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())