"""Lab-only synthetic effect sentinel for Hermes hook qualification.

This fixture is intentionally outside the Pantheon Hermes distribution. Its tool
writes only one operator-selected marker file inside the ephemeral lab. The
pre_tool_call hook can either block the tool or raise deliberately so the exact
pinned Hermes failure semantics can be observed through the real Runs route.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

TOOL_NAME = "pantheon_effect_sentinel"
BLOCK_MESSAGE = "PANTHEON_SENTINEL_BLOCKED"
MODE_ENV = "PANTHEON_SENTINEL_MODE_FILE"
SINK_ENV = "PANTHEON_SENTINEL_SINK"

TOOL_SCHEMA: dict[str, Any] = {
    "name": TOOL_NAME,
    "description": (
        "LAB ONLY. Touch the isolated synthetic sentinel sink so runtime guard "
        "behavior can be observed. This is not a real external effect."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "marker": {"type": "string", "minLength": 1, "maxLength": 100},
        },
        "required": ["marker"],
        "additionalProperties": False,
    },
}


def _required_path(env_name: str) -> Path:
    value = str(os.environ.get(env_name) or "").strip()
    if not value:
        raise RuntimeError(f"{env_name} is required for the lab sentinel")
    return Path(value)


def _mode() -> str:
    path = _required_path(MODE_ENV)
    return path.read_text(encoding="utf-8").strip().lower()


def _effect(args: dict[str, Any], **kwargs: Any) -> str:
    sink = _required_path(SINK_ENV)
    sink.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "effect_ran": True,
        "marker": str(args.get("marker") or ""),
        "task_id": str(kwargs.get("task_id") or ""),
        "session_id": str(kwargs.get("session_id") or ""),
        "synthetic": True,
        "evidence": False,
        "authorization": False,
    }
    sink.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _pre_tool_call(tool_name: str, **kwargs: Any):
    del kwargs
    if tool_name != TOOL_NAME:
        return None
    mode = _mode()
    if mode == "block":
        return {"action": "block", "message": BLOCK_MESSAGE}
    if mode == "raise":
        raise RuntimeError("PANTHEON_SENTINEL_HOOK_EXCEPTION")
    if mode == "allow":
        return None
    return {
        "action": "block",
        "message": f"PANTHEON_SENTINEL_UNKNOWN_MODE:{mode or 'empty'}",
    }


def register(ctx) -> None:
    ctx.register_tool(
        name=TOOL_NAME,
        toolset="pantheon_effect_sentinel",
        schema=TOOL_SCHEMA,
        handler=_effect,
        description=TOOL_SCHEMA["description"],
    )
    ctx.register_hook("pre_tool_call", _pre_tool_call)
