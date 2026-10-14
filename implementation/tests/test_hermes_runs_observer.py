"""Tests for read-only Hermes Runs API contract observation."""

from __future__ import annotations

import httpx
import pytest

from mvp_vertical.hermes_runs_observer import (
    HermesRunsApiObserver,
    HermesRunsObservationError,
    parse_memory_status,
)

PROFILE = "pantheon-governed"
BASE = f"http://hermes:8642/p/{PROFILE}"
MEMORY_OUTPUT = """
Memory status
────────────────────────────────────────
  Built-in (MEMORY.md / USER.md):
    Memory injection:   disabled ✗
    User profile:       disabled ✗
    Memory tool:        disabled ✗
  Provider:  (none — built-in only)
"""


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def _memory_receipt(output: str = MEMORY_OUTPUT, profile: str = PROFILE):
    return parse_memory_status(output, profile=profile)


def _capabilities(**feature_overrides):
    features = {
        "chat_completions": True,
        "responses_api": True,
        "run_submission": True,
        "run_status": True,
        "run_events_sse": True,
        "run_stop": True,
        "run_approval": True,
    }
    features.update(feature_overrides)
    return {
        "object": "hermes.api_server.capabilities",
        "platform": "hermes-agent",
        "model": "pantheon-governed",
        "auth": {"type": "bearer", "required": True},
        "features": features,
        "endpoints": {
            "run_submit": "/v1/runs",
            "run_status": "/v1/runs/{run_id}",
            "toolsets": "/v1/toolsets",
        },
    }


def _toolset_rows(*tools: str, name: str = "pantheon_context"):
    return [{
        "name": name,
        "enabled": True,
        "configured": True,
        "tools": list(tools),
    }]


def _toolset_envelope(rows):
    return {
        "object": "list",
        "platform": "api_server",
        "data": rows,
    }


def _qualified_observer(handler, **overrides):
    values = {
        "expected_profile": PROFILE,
        "memory_observation": _memory_receipt(),
        "allowed_tools": {"pantheon_context_manifest", "pantheon_context_entity"},
        "required_tools": {"pantheon_context_manifest", "pantheon_context_entity"},
        "client": _client(handler),
    }
    values.update(overrides)
    return HermesRunsApiObserver(BASE, "api-key", **values)


def test_observer_reads_official_020_toolset_envelope_and_performs_no_effect() -> None:
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((
            request.method,
            request.url.path,
            request.headers.get("authorization"),
            request.headers.get("x-hermes-session-key"),
        ))
        if request.url.path.endswith("/v1/capabilities"):
            return httpx.Response(200, json=_capabilities())
        if request.url.path.endswith("/v1/toolsets"):
            return httpx.Response(
                200,
                json=_toolset_envelope(_toolset_rows(
                    "pantheon_context_manifest",
                    "pantheon_context_entity",
                )),
            )
        raise AssertionError(f"unexpected request {request.method} {request.url.path}")

    observed = _qualified_observer(handler).observe()

    assert observed["runs_api_status"] == "compatible"
    assert observed["safety_status"] == "qualified"
    assert observed["toolsets_contract"] == {
        "object": "list",
        "platform": "api_server",
        "data_field": True,
        "compatibility_surface": False,
    }
    assert observed["profile_surface"] == {
        "status": "qualified",
        "expected_profile": PROFILE,
        "observed_profile": PROFILE,
        "route_observed": True,
        "reason": None,
    }
    assert observed["memory_posture"]["status"] == "qualified"
    assert observed["memory_posture"]["external_provider"] == "off"
    assert observed["memory_posture"]["built_in_memory_injection"] == "off"
    assert observed["memory_posture"]["built_in_user_profile_injection"] == "off"
    assert observed["memory_posture"]["memory_tool"] == "off"
    assert observed["memory_posture"]["session_memory_key"] == "absent"
    assert observed["session_memory_header_sent"] is False
    assert observed["tool_surface"]["active_toolsets"] == ["pantheon_context"]
    assert observed["run_submission_performed"] is False
    assert observed["run_stop_performed"] is False
    assert observed["approval_effect_performed"] is False
    assert observed["write_effect"] is False
    assert observed["authority_effect"] == "none"
    assert seen == [
        ("GET", f"/p/{PROFILE}/v1/capabilities", "Bearer api-key", None),
        ("GET", f"/p/{PROFILE}/v1/toolsets", "Bearer api-key", None),
    ]


def test_legacy_bare_toolset_list_is_explicitly_labelled() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/v1/capabilities"):
            return httpx.Response(200, json=_capabilities())
        return httpx.Response(200, json=_toolset_rows(
            "pantheon_context_manifest",
            "pantheon_context_entity",
        ))

    observed = _qualified_observer(handler).observe()
    assert observed["safety_status"] == "qualified"
    assert observed["toolsets_contract"] == {
        "object": "legacy_bare_list",
        "platform": None,
        "data_field": False,
        "compatibility_surface": True,
    }


@pytest.mark.parametrize(
    "payload,match",
    [
        ({"object": "unexpected", "platform": "api_server", "data": []}, "unexpected contract object"),
        ({"object": "list", "platform": "cli", "data": []}, "unexpected platform scope"),
        ({"object": "list", "platform": "api_server", "data": {}}, "non-list data field"),
        ("not-an-object", "object list envelope"),
    ],
)
def test_malformed_toolset_envelope_fails_closed(payload, match) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/v1/capabilities"):
            return httpx.Response(200, json=_capabilities())
        return httpx.Response(200, json=payload)

    with pytest.raises(HermesRunsObservationError, match=match):
        _qualified_observer(handler).observe()


def test_full_or_extra_runtime_tool_surface_is_not_qualified() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/v1/capabilities"):
            return httpx.Response(200, json=_capabilities())
        return httpx.Response(200, json=[{
            "name": "hermes-api-server",
            "enabled": True,
            "configured": True,
            "tools": ["pantheon_context_manifest", "pantheon_context_entity", "terminal", "write_file"],
        }])

    observed = _qualified_observer(
        handler,
        required_tools={"pantheon_context_manifest"},
    ).observe()
    assert observed["runtime_reachable"] is True
    assert observed["runs_api_status"] == "compatible"
    assert observed["safety_status"] == "not_qualified"
    assert observed["tool_surface"]["unexpected_tools"] == ["terminal", "write_file"]


def test_without_reviewed_allowlist_safety_remains_not_evaluated() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/v1/capabilities"):
            return httpx.Response(200, json=_capabilities())
        return httpx.Response(200, json=[{
            "name": "hermes-api-server",
            "enabled": True,
            "configured": True,
            "tools": ["terminal", "write_file"],
        }])

    observed = HermesRunsApiObserver(
        BASE,
        "api-key",
        expected_profile=PROFILE,
        memory_observation=_memory_receipt(),
        client=_client(handler),
    ).observe()
    assert observed["runs_api_status"] == "compatible"
    assert observed["safety_status"] == "not_evaluated"
    assert "terminal" in observed["tool_surface"]["active_tools"]


def test_missing_runs_feature_marks_contract_incomplete_without_side_effect() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/v1/capabilities"):
            return httpx.Response(200, json=_capabilities(run_events_sse=False))
        return httpx.Response(200, json=[])

    observed = HermesRunsApiObserver(BASE, "api-key", client=_client(handler)).observe()
    assert observed["runs_api_status"] == "incomplete"
    assert observed["missing_run_features"] == ["run_events_sse"]
    assert observed["safety_status"] == "not_evaluated"
    assert observed["run_submission_performed"] is False


def test_toolset_disabled_or_unconfigured_does_not_count_as_active() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/v1/capabilities"):
            return httpx.Response(200, json=_capabilities())
        return httpx.Response(200, json=[
            {"name": "mcp-pantheon", "enabled": True, "configured": True, "tools": ["pantheon_context_manifest"]},
            {"name": "terminal", "enabled": False, "configured": True, "tools": ["terminal"]},
            {"name": "file", "enabled": True, "configured": False, "tools": ["write_file"]},
        ])

    observed = _qualified_observer(
        handler,
        allowed_tools={"pantheon_context_manifest"},
        required_tools={"pantheon_context_manifest"},
    ).observe()
    assert observed["safety_status"] == "qualified"
    assert observed["tool_surface"]["active_tools"] == ["pantheon_context_manifest"]


def test_profile_route_or_memory_posture_mismatch_fails_closed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/v1/capabilities"):
            return httpx.Response(200, json=_capabilities())
        return httpx.Response(200, json=[{
            "name": "mcp-pantheon",
            "enabled": True,
            "configured": True,
            "tools": ["pantheon_context_manifest", "pantheon_context_entity"],
        }])

    wrong_route = HermesRunsApiObserver(
        "http://hermes:8642",
        "api-key",
        expected_profile=PROFILE,
        memory_observation=_memory_receipt(),
        allowed_tools={"pantheon_context_manifest", "pantheon_context_entity"},
        required_tools={"pantheon_context_manifest", "pantheon_context_entity"},
        client=_client(handler),
    ).observe()
    assert wrong_route["profile_surface"]["status"] == "not_qualified"
    assert wrong_route["safety_status"] == "not_qualified"

    active_memory = MEMORY_OUTPUT.replace("Memory tool:        disabled", "Memory tool:        enabled")
    memory_on = _qualified_observer(
        handler,
        memory_observation=_memory_receipt(active_memory),
    ).observe()
    assert memory_on["memory_posture"]["status"] == "not_qualified"
    assert memory_on["memory_posture"]["active_axes"] == ["memory_tool"]
    assert memory_on["safety_status"] == "not_qualified"


def test_required_tools_must_be_within_reviewed_allowlist() -> None:
    with pytest.raises(HermesRunsObservationError, match="subset of allowed_tools"):
        HermesRunsApiObserver(
            BASE,
            "api-key",
            allowed_tools={"pantheon_context_manifest"},
            required_tools={"pantheon_context_entity"},
        )


def test_bad_capability_contract_fails_closed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/v1/capabilities"):
            return httpx.Response(200, json={"object": "unexpected"})
        return httpx.Response(200, json=[])

    with pytest.raises(HermesRunsObservationError, match="unexpected contract object"):
        HermesRunsApiObserver(BASE, "api-key", client=_client(handler)).observe()