"""Read-only tool handlers for the Pantheon context bridge Hermes plugin.

The Hermes host supplies ``task_id`` outside the model-authored arguments. The
joined Run Binding uses ``session_id = admission_id`` when creating the run, so
this plugin treats that host context as the only admissible Pantheon admission
identity. Live equality of Hermes v0.19 task_id/session_id remains an activation
check; any mismatch fails closed here.
"""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ACTOR = "hermes-plugin:pantheon-context-bridge"
TIMEOUT_SECONDS = 10.0
MAX_RESPONSE_BYTES = 1_000_000


def _error(message: str) -> str:
    return json.dumps({"error": message}, ensure_ascii=False)


def _admission_from_host_context(kwargs: dict) -> str:
    task_id = str(kwargs.get("task_id") or "").strip()
    if not task_id:
        raise ValueError("Hermes host task_id is required")
    if not task_id.startswith("admission-") or len(task_id) > 300:
        raise ValueError("Hermes host task_id is not a Pantheon admission identity")
    return task_id


def _configuration() -> tuple[str, str]:
    base = os.environ.get("PANTHEON_HERMES_API_BASE", "").strip().rstrip("/")
    key = os.environ.get("PANTHEON_HERMES_API_KEY", "").strip()
    if not base or not key:
        raise ValueError("Pantheon context bridge environment is incomplete")
    if not (base.startswith("http://") or base.startswith("https://")):
        raise ValueError("PANTHEON_HERMES_API_BASE must be an http(s) URL")
    return base, key


def _get_json(path: str) -> dict:
    base, key = _configuration()
    request = Request(
        base + path,
        method="GET",
        headers={
            "Authorization": f"Bearer {key}",
            "X-Pantheon-Hermes-Actor": ACTOR,
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # nosec B310: reviewed configured base only
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        raise ValueError(f"Pantheon context request refused with HTTP {exc.code}") from exc
    except URLError as exc:
        raise ValueError("Pantheon context API is unreachable") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("Pantheon context response exceeds plugin limit")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise ValueError("Pantheon context response is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("Pantheon context response must be an object")
    return payload


def pantheon_context_manifest(args: dict, **kwargs) -> str:
    del args
    try:
        admission_id = _admission_from_host_context(kwargs)
        payload = _get_json(
            f"/hermes/execution-admissions/{quote(admission_id, safe='')}/active-context"
        )
        return json.dumps(payload, ensure_ascii=False)
    except Exception as exc:
        return _error(str(exc))


def pantheon_context_entity(args: dict, **kwargs) -> str:
    try:
        admission_id = _admission_from_host_context(kwargs)
        entity_type = str(args.get("entity_type") or "").strip()
        entity_id = str(args.get("entity_id") or "").strip()
        if not entity_type or not entity_id:
            raise ValueError("entity_type and entity_id are required")
        if len(entity_type) > 100 or len(entity_id) > 500:
            raise ValueError("entity identity exceeds plugin limits")
        payload = _get_json(
            "/hermes/execution-admissions/"
            f"{quote(admission_id, safe='')}/active-context/entities/"
            f"{quote(entity_type, safe='')}/{quote(entity_id, safe='')}"
        )
        return json.dumps(payload, ensure_ascii=False)
    except Exception as exc:
        return _error(str(exc))