"""Small ASGI middleware for the bounded Pantheon policy HTTP adapter."""

from __future__ import annotations

from uuid import uuid4

from fastapi.responses import JSONResponse

from .service import POLICY_CONTRACT

_MUTATING_METHODS = {"POST", "PUT", "PATCH"}
_REQUEST_ID_HEADER = b"x-request-id"
_RESPONSE_REQUEST_ID_HEADER = b"x-pantheon-request-id"


def _headers(scope: dict) -> dict[bytes, bytes]:
    return {key.lower(): value for key, value in scope.get("headers", [])}


async def _send_json(scope: dict, receive, send, status_code: int, content: dict) -> None:
    response = JSONResponse(status_code=status_code, content=content)
    await response(scope, receive, send)


class RequestIdMiddleware:
    """Attach a bounded correlation identifier without treating it as evidence."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope: dict, receive, send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        supplied = _headers(scope).get(_REQUEST_ID_HEADER, b"").decode(
            "utf-8", errors="ignore"
        )
        request_id = supplied.strip()[:128] or uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id

        async def send_with_request_id(message: dict) -> None:
            if message.get("type") == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((_RESPONSE_REQUEST_ID_HEADER, request_id.encode("utf-8")))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_request_id)


class BodySizeLimitMiddleware:
    """Buffer and replay bounded request bodies without mutating Starlette internals."""

    def __init__(self, app, *, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: dict, receive, send) -> None:
        if scope.get("type") != "http" or scope.get("method") not in _MUTATING_METHODS:
            await self.app(scope, receive, send)
            return

        declared = _headers(scope).get(b"content-length")
        if declared:
            try:
                declared_size = int(declared)
            except ValueError:
                await _send_json(
                    scope,
                    receive,
                    send,
                    400,
                    {"contract": POLICY_CONTRACT, "result": "invalid_content_length"},
                )
                return
            if declared_size > self.max_bytes:
                await _send_json(
                    scope,
                    receive,
                    send,
                    413,
                    {
                        "contract": POLICY_CONTRACT,
                        "result": "request_too_large",
                        "max_body_bytes": self.max_bytes,
                    },
                )
                return

        chunks: list[bytes] = []
        total = 0
        while True:
            message = await receive()
            if message.get("type") == "http.disconnect":
                return
            body = message.get("body", b"")
            total += len(body)
            if total > self.max_bytes:
                await _send_json(
                    scope,
                    receive,
                    send,
                    413,
                    {
                        "contract": POLICY_CONTRACT,
                        "result": "request_too_large",
                        "max_body_bytes": self.max_bytes,
                    },
                )
                return
            chunks.append(body)
            if not message.get("more_body", False):
                break

        replayed = False
        buffered = b"".join(chunks)

        async def replay_receive() -> dict:
            nonlocal replayed
            if replayed:
                return {"type": "http.request", "body": b"", "more_body": False}
            replayed = True
            return {"type": "http.request", "body": buffered, "more_body": False}

        await self.app(scope, replay_receive, send)
