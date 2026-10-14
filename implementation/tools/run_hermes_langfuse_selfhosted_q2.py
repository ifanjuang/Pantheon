#!/usr/bin/env python3
"""Bounded real-ingestion probe for Hermes -> self-hosted Langfuse v4.

Synthetic data only. Q2 deliberately performs an A/B check:
A) the Langfuse SDK sends one structural control observation;
B) the bundled Hermes plugin sends one synthetic Hermes turn.
Readback uses the Langfuse v4 GA Observations API, not the deprecated legacy
traces endpoint.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import time
from pathlib import Path

import requests

BASE_URL = os.environ.get("HERMES_LANGFUSE_BASE_URL", "http://127.0.0.1:3000").rstrip("/")
PUBLIC_KEY = os.environ["HERMES_LANGFUSE_PUBLIC_KEY"]
SECRET_KEY = os.environ["HERMES_LANGFUSE_SECRET_KEY"]
HERMES_ROOT = Path(os.environ["HERMES_ROOT"]).resolve()

PROMPT_MARKER = "PANTHEON_Q2_PROMPT_MUST_NOT_BE_STORED"
TOOL_ARG_MARKER = "PANTHEON_Q2_TOOL_ARG_MUST_NOT_BE_STORED"
TOOL_RESULT_MARKER = "PANTHEON_Q2_TOOL_RESULT_MUST_NOT_BE_STORED"
FINAL_MARKER = "PANTHEON_Q2_FINAL_MUST_NOT_BE_STORED"
CONTROL_NAME = "Pantheon Q2 SDK control"

os.environ["HERMES_LANGFUSE_CAPTURE"] = "metadata"
os.environ["HERMES_LANGFUSE_ENV"] = "pantheon-q2"
os.environ["HERMES_LANGFUSE_RELEASE"] = "synthetic-q2"
os.environ["HERMES_LANGFUSE_SAMPLE_RATE"] = "1.0"

sys.path.insert(0, str(HERMES_ROOT))
mod_name = "plugins.observability.langfuse"
sys.modules.pop(mod_name, None)
plugin = importlib.import_module(mod_name)

client = plugin._get_langfuse()
assert client is not None, "Langfuse client did not initialize"
assert plugin._capture_mode() == "metadata"

auth = (PUBLIC_KEY, SECRET_KEY)


def read_observations() -> tuple[int, dict | None, str]:
    response = requests.get(f"{BASE_URL}/api/public/v2/observations?limit=100", auth=auth, timeout=10)
    payload = response.json() if response.status_code == 200 else None
    return response.status_code, payload, response.text[:1000]


def wait_for_observation_name(name: str, *, timeout_seconds: int = 90) -> dict:
    deadline = time.monotonic() + timeout_seconds
    last_status = None
    last_body = ""
    while time.monotonic() < deadline:
        status, payload, body = read_observations()
        last_status, last_body = status, body
        if status == 200 and isinstance(payload, dict):
            for observation in payload.get("data", []):
                if observation.get("name") == name:
                    return payload
        time.sleep(1)
    raise AssertionError(
        f"Observation {name!r} did not become visible; last_status={last_status} body={last_body}"
    )


# Authentication/readback gate on the GA Langfuse v4 surface.
preflight_status, preflight_payload, preflight_body = read_observations()
assert preflight_status == 200, (
    "Langfuse initialized project keys are not valid for v4 observations readback: "
    f"status={preflight_status} body={preflight_body}"
)
print(json.dumps({"phase": "v4_observations_api_preflight", "status": "passed"}))

# A — direct SDK transport control using exactly the same client instance that
# the Hermes plugin will use. No prompt/tool content is attached.
control_trace_id = client.create_trace_id(seed="pantheon-q2-sdk-control")
with client.start_as_current_observation(
    trace_context={"trace_id": control_trace_id, "session_id": "pantheon-q2-sdk-control-session"},
    name=CONTROL_NAME,
    as_type="chain",
    metadata={"source": "pantheon-q2-sdk-control", "capture_mode": "metadata"},
):
    pass
client.flush()
control_payload = wait_for_observation_name(CONTROL_NAME)
print(json.dumps({"phase": "sdk_transport_control", "status": "passed", "trace_id": control_trace_id}))

# B — drive the current Hermes request lifecycle. The first synthetic model
# response requests a tool, keeping the turn trace open.
common = {
    "task_id": "pantheon-langfuse-q2-task",
    "session_id": "pantheon-langfuse-q2-session",
    "turn_id": "pantheon-langfuse-q2-turn",
    "platform": "pantheon-q2",
    "provider": "synthetic",
    "model": "synthetic-model",
    "base_url": "synthetic://provider",
    "api_mode": "chat_completions",
}

plugin.on_pre_llm_request(
    **common,
    api_call_count=1,
    api_request_id="pantheon-q2-request-1",
    request_messages=[{"role": "user", "content": PROMPT_MARKER}],
    message_count=1,
    tool_count=1,
    approx_input_tokens=12,
    request_char_count=len(PROMPT_MARKER),
)
plugin.on_post_llm_call(
    **common,
    api_call_count=1,
    api_request_id="pantheon-q2-request-1",
    assistant_tool_call_count=1,
    assistant_content_chars=0,
    usage={"input_tokens": 12, "output_tokens": 3, "request_count": 1},
    finish_reason="tool_calls",
)

plugin.on_pre_tool_call(
    **common,
    tool_name="read_file",
    tool_call_id="pantheon-q2-tool-call",
    args={"path": "synthetic.md", "marker": TOOL_ARG_MARKER},
)
plugin.on_post_tool_call(
    **common,
    tool_name="read_file",
    tool_call_id="pantheon-q2-tool-call",
    args={"path": "synthetic.md", "marker": TOOL_ARG_MARKER},
    result=TOOL_RESULT_MARKER,
)

plugin.on_pre_llm_request(
    **common,
    api_call_count=2,
    api_request_id="pantheon-q2-request-2",
    request_messages=[
        {"role": "user", "content": PROMPT_MARKER},
        {"role": "tool", "name": "read_file", "tool_call_id": "pantheon-q2-tool-call", "content": TOOL_RESULT_MARKER},
    ],
    message_count=2,
    tool_count=1,
    approx_input_tokens=18,
    request_char_count=len(PROMPT_MARKER) + len(TOOL_RESULT_MARKER),
)
plugin.on_post_llm_call(
    **common,
    api_call_count=2,
    api_request_id="pantheon-q2-request-2",
    assistant_response=FINAL_MARKER,
    assistant_tool_call_count=0,
    usage={"input_tokens": 18, "output_tokens": 5, "request_count": 1},
    finish_reason="stop",
)

plugin._finalize_all_traces()
client.flush()
observations_payload = wait_for_observation_name("Hermes turn")
print(json.dumps({"phase": "hermes_plugin_ingestion", "status": "passed"}))

# Verify the current v4 server-side read surface does not expose any synthetic
# content marker when Hermes capture mode is metadata.
serialized = json.dumps(observations_payload, sort_keys=True)
for marker in (PROMPT_MARKER, TOOL_ARG_MARKER, TOOL_RESULT_MARKER, FINAL_MARKER):
    assert marker not in serialized, f"metadata mode leaked content marker: {marker}"

obs_data = observations_payload.get("data", [])
assert any(o.get("name") == "Hermes turn" for o in obs_data), "Hermes turn observation missing"
assert any(o.get("name") == "Tool: read_file" for o in obs_data), "Hermes tool observation missing"

result = {
    "kind": "hermes_langfuse_selfhosted_q2_acceptance",
    "status": "passed",
    "capture_mode": "metadata",
    "v4_observations_api_readback": True,
    "direct_sdk_transport": True,
    "real_hermes_plugin_ingestion": True,
    "observation_count_observed": len(obs_data),
    "content_markers_stored": False,
    "langfuse_is_authority": False,
    "evidence_admitted": False,
    "pantheon_state_mutated": False,
}
print(json.dumps(result, indent=2, sort_keys=True))
