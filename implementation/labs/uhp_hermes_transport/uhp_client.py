from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import httpx


DEFAULT_PROTOCOL_VERSION = "2026-09-28"


class UhpTransportError(RuntimeError):
    pass


class UhpClient:
    """Small external qualification client.

    This is deliberately not a Pantheon runtime component. It knows UHP HTTP
    only and carries no Pantheon authorization semantics.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        protocol_version: str = DEFAULT_PROTOCOL_VERSION,
        client: httpx.Client | None = None,
    ) -> None:
        if not base_url.strip():
            raise ValueError("base_url is required")
        if not api_key.strip():
            raise ValueError("api_key is required")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.protocol_version = protocol_version
        self.client = client or httpx.Client(timeout=120.0)

    def _headers(
        self,
        *,
        idempotency_key: str | None = None,
    ) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "UHP-Version": self.protocol_version,
            "Accept": "application/json",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    @staticmethod
    def _json(
        response: httpx.Response,
        operation: str,
    ) -> dict[str, Any]:
        try:
            body = response.json()
        except ValueError as exc:
            raise UhpTransportError(
                f"{operation} returned non-JSON HTTP "
                f"{response.status_code}"
            ) from exc
        if response.is_error:
            raise UhpTransportError(
                f"{operation} failed HTTP {response.status_code}: "
                f"{json.dumps(body, ensure_ascii=False)[:1000]}"
            )
        if not isinstance(body, dict):
            raise UhpTransportError(
                f"{operation} returned a non-object JSON body"
            )
        return body

    def discovery(self) -> dict[str, Any]:
        response = self.client.get(
            self._url("/v1/uhp"),
            headers=self._headers(),
        )
        return self._json(response, "UHP discovery")

    def list_harnesses(self) -> dict[str, Any]:
        response = self.client.get(
            self._url("/v1/harnesses"),
            headers=self._headers(),
        )
        return self._json(response, "list harnesses")

    def submit_task(
        self,
        *,
        input_value: str | list[dict[str, Any]],
        harness_id: str,
        idempotency_key: str,
        stream: bool = False,
        background: bool = False,
        timeout_seconds: int | None = None,
        max_step: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        meta = dict(metadata or {})
        meta["harness_id"] = harness_id
        payload: dict[str, Any] = {
            "input": input_value,
            "metadata": meta,
            "stream": stream,
            "background": background,
        }
        if timeout_seconds is not None:
            payload["timeout_seconds"] = timeout_seconds
        if max_step is not None:
            payload["max_step"] = max_step
        response = self.client.post(
            self._url("/v1/responses"),
            headers=self._headers(
                idempotency_key=idempotency_key
            ),
            json=payload,
        )
        return self._json(response, "submit task")

    def stream_task(
        self,
        *,
        input_value: str | list[dict[str, Any]],
        harness_id: str,
        idempotency_key: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        meta = dict(metadata or {})
        meta["harness_id"] = harness_id
        payload = {
            "input": input_value,
            "metadata": meta,
            "stream": True,
        }
        events: list[dict[str, Any]] = []
        with self.client.stream(
            "POST",
            self._url("/v1/responses"),
            headers={
                **self._headers(
                    idempotency_key=idempotency_key
                ),
                "Accept": "text/event-stream",
            },
            json=payload,
        ) as response:
            if response.is_error:
                raw = response.read().decode(
                    "utf-8",
                    errors="replace",
                )
                raise UhpTransportError(
                    f"stream task failed HTTP "
                    f"{response.status_code}: {raw[:1000]}"
                )
            for line in response.iter_lines():
                if not line or line.startswith(":"):
                    continue
                if not line.startswith("data:"):
                    continue
                raw = line[5:].strip()
                if not raw:
                    continue
                event = json.loads(raw)
                if not isinstance(event, dict):
                    raise UhpTransportError(
                        "stream event must be a JSON object"
                    )
                events.append(event)
        return events

    @staticmethod
    def stream_sequence_valid(
        events: Iterable[dict[str, Any]],
    ) -> bool:
        events = list(events)
        if not events:
            return False
        numbers = [
            event.get("sequence_number")
            for event in events
        ]
        if numbers != list(range(len(events))):
            return False
        if events[0].get("type") != "response.created":
            return False
        terminals = [
            event
            for event in events
            if event.get("type")
            in {
                "response.completed",
                "response.incomplete",
                "response.failed",
            }
        ]
        return (
            len(terminals) == 1
            and terminals[0] is events[-1]
        )

    def get_response(
        self,
        response_id: str,
    ) -> dict[str, Any]:
        response = self.client.get(
            self._url(f"/v1/responses/{response_id}"),
            headers=self._headers(),
        )
        return self._json(response, "get response")

    def cancel_response(
        self,
        response_id: str,
    ) -> dict[str, Any]:
        response = self.client.post(
            self._url(
                f"/v1/responses/{response_id}/cancel"
            ),
            headers=self._headers(),
        )
        return self._json(response, "cancel response")

    def upload_file(
        self,
        path: Path,
        *,
        media_type: str = "application/octet-stream",
    ) -> dict[str, Any]:
        with path.open("rb") as handle:
            response = self.client.post(
                self._url("/v1/files"),
                headers=self._headers(),
                data={"purpose": "user_data"},
                files={
                    "file": (
                        path.name,
                        handle,
                        media_type,
                    )
                },
            )
        return self._json(response, "upload file")

    def list_session_files(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        response = self.client.get(
            self._url(
                f"/v1/sessions/{session_id}/files"
            ),
            headers=self._headers(),
        )
        return self._json(response, "list session files")

    def download_file(
        self,
        container_id: str,
        file_id: str,
    ) -> bytes:
        response = self.client.get(
            self._url(
                f"/v1/containers/{container_id}"
                f"/files/{file_id}/content"
            ),
            headers=self._headers(),
        )
        if response.is_error:
            raise UhpTransportError(
                f"download file failed HTTP "
                f"{response.status_code}: "
                f"{response.text[:1000]}"
            )
        return response.content
