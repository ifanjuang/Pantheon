#!/usr/bin/env python3
"""Bounded operator harness for the current qualified Hermes runtime acceptance.

The harness writes only an isolated HERMES_HOME, waits for local HTTP surfaces,
and validates technical receipts. It never configures a production host,
activates future tasks, admits Evidence, or updates the distribution state.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml

PROFILE = "pantheon-governed"
ADMISSION_ID = "admission-hermes-020-lab"
PROFILE_KEY = "hermes-profile-lab-key"
DEFAULT_KEY = "hermes-default-lab-key"
PANTHEON_KEY = "pantheon-lab-key"
EXPECTED_TOOLS = {"pantheon_context_manifest", "pantheon_context_entity"}
EXPECTED_COMPONENTS = {"run-binding", "context-bridge", "runtime-observer"}
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class LabAcceptanceError(RuntimeError):
    pass


def _write_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _write_env(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(f"{key}={value}\n" for key, value in values.items()),
        encoding="utf-8",
    )
    path.chmod(0o600)


def configure(hermes_home: Path, fixture_url: str) -> dict[str, Any]:
    """Create one listener and one non-port-binding governed profile."""

    hermes_home = hermes_home.resolve()
    profile_home = hermes_home / "profiles" / PROFILE
    if not profile_home.is_dir():
        raise LabAcceptanceError(
            f"profile directory does not exist; create it first: {profile_home}"
        )

    memory_off = {
        "provider": "",
        "memory_enabled": False,
        "user_profile_enabled": False,
    }
    _write_yaml(
        hermes_home / "config.yaml",
        {
            "gateway": {"multiplex_profiles": True},
            "memory": dict(memory_off),
            "platform_toolsets": {"api_server": [], "cli": []},
            "plugins": {"enabled": [], "disabled": []},
        },
    )
    _write_env(hermes_home / ".env", {"API_SERVER_KEY": DEFAULT_KEY})

    # Hermes profiles are separate home directories with their own plugins and
    # tool policy. The governed route therefore owns the bridge plugin copy;
    # the default home owns only the multiplexing listener. The profile CLI
    # surface stays empty so memory/tool state cannot leak through that path.
    _write_yaml(
        profile_home / "config.yaml",
        {
            "model": {
                "provider": "custom",
                "default": "lab-model",
                "base_url": fixture_url.rstrip("/") + "/v1",
                "api_mode": "chat_completions",
            },
            "memory": dict(memory_off),
            "platform_toolsets": {
                "api_server": ["pantheon_context"],
                "cli": [],
            },
            # The named profile keeps its own route key but must never own the
            # shared listener. The explicit marker is stricter than env-only
            # API_SERVER_ENABLED=false and keeps the test fail-closed.
            "platforms": {
                "api_server": {
                    "enabled": False,
                },
            },
        },
    )
    _write_env(
        profile_home / ".env",
        {
            "API_SERVER_KEY": PROFILE_KEY,
            "PANTHEON_HERMES_API_BASE": fixture_url.rstrip("/"),
            "PANTHEON_HERMES_API_KEY": PANTHEON_KEY,
            "OPENAI_API_KEY": "local-lab-provider-key",
        },
    )

    return {
        "kind": "hermes_runtime_lab_configuration",
        "hermes_home": str(hermes_home),
        "profile": PROFILE,
        "multiplex_profiles": True,
        "profile_api_prefix": f"/p/{PROFILE}",
        "profile_api_key_present": True,
        "profile_port_binding_enabled": False,
        "gateway_plugin_scope": "profile_home",
        "profile_plugin_copy": True,
        "platform_toolsets_expected": {
            "api_server": ["pantheon_context"],
            "cli": [],
        },
        "memory_axes_expected": {
            "external_provider": "off",
            "built_in_memory_injection": "off",
            "built_in_user_profile_injection": "off",
            "memory_tool": "off",
            "session_memory_key": "absent",
        },
        "expected_tools": sorted(EXPECTED_TOOLS),
        "production_activation": False,
        "future_task_authorization": False,
    }


def _request_json(url: str, *, bearer: str | None = None) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    request = Request(url, headers=headers)
    with urlopen(request, timeout=5) as response:  # nosec B310: loopback lab only
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise LabAcceptanceError(f"{url} did not return an object")
    return payload


def wait_http(url: str, bearer: str | None, timeout: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last_error = "not attempted"
    while time.monotonic() < deadline:
        try:
            return _request_json(url, bearer=bearer)
        except (HTTPError, URLError, OSError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            time.sleep(0.5)
    raise LabAcceptanceError(f"HTTP surface did not become ready: {url}: {last_error}")


def wait_run(base_url: str, api_key: str, run_id: str, timeout: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last: dict[str, Any] = {}
    while time.monotonic() < deadline:
        last = _request_json(
            base_url.rstrip("/") + f"/v1/runs/{run_id}",
            bearer=api_key,
        )
        if str(last.get("status") or "").lower() in {
            "completed",
            "failed",
            "cancelled",
        }:
            return last
        time.sleep(0.5)
    raise LabAcceptanceError(f"Hermes run did not reach a terminal state: {last}")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LabAcceptanceError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise LabAcceptanceError(f"{path} must contain an object")
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise LabAcceptanceError(message)


def _require_false(value: dict[str, Any], key: str, message: str) -> None:
    _require(value.get(key) is False, message)


def validate(artifacts: Path) -> dict[str, Any]:
    artifacts = artifacts.resolve()
    expected_version = os.environ.get("HERMES_VERSION", "").strip()
    _require(bool(expected_version), "HERMES_VERSION was not supplied by the qualification registry")
    version = (artifacts / "hermes-version.txt").read_text(encoding="utf-8").strip()
    source_digest = (
        artifacts / "hermes-source-artifact.sha256"
    ).read_text(encoding="utf-8").strip()
    distribution = _load_json(artifacts / "distribution-verification.json")
    memory = _load_json(artifacts / "memory-status-launch.json")
    observation = _load_json(artifacts / "runtime-observation.json")
    launch = _load_json(artifacts / "launch-receipt.json")
    terminal = _load_json(artifacts / "run-terminal.json")
    reconciliation = _load_json(artifacts / "return-receipt.json")
    fixture_state = _load_json(artifacts / "fixture-state.json")
    rollback = _load_json(artifacts / "rollback.json")
    sentinel_required = os.environ.get("PANTHEON_RUN_PRETOOL_SENTINEL", "0").strip() == "1"
    sentinel = (
        _load_json(artifacts / "sentinel-observation.json")
        if sentinel_required
        else None
    )

    _require(expected_version in version, f"unexpected Hermes version: {version}")
    _require(SHA256_RE.fullmatch(source_digest) is not None, "invalid source digest")

    components = distribution.get("components") or []
    component_ids = {
        str(item.get("component_id"))
        for item in components
        if isinstance(item, dict)
    }
    _require(distribution.get("status") == "candidate", "lock is not candidate")
    _require(component_ids == EXPECTED_COMPONENTS, "distribution components differ")
    _require(
        distribution.get("verified_component_digest_count") == 3,
        "component digests were not all verified",
    )
    _require(distribution.get("authority_effect") == "none", "lock claims authority")

    _require(memory.get("status") == "qualified", "launch memory is not qualified")
    for axis in (
        "external_provider",
        "built_in_memory_injection",
        "built_in_user_profile_injection",
        "memory_tool",
    ):
        _require(memory.get(axis) == "off", f"memory axis active or unknown: {axis}")
    _require_false(memory, "raw_output_retained", "raw memory output was retained")

    _require(observation.get("runs_api_status") == "compatible", "Runs API incompatible")
    _require(observation.get("safety_status") == "qualified", "runtime not qualified")
    _require(
        observation.get("profile_surface", {}).get("observed_profile") == PROFILE,
        "wrong profile route",
    )
    _require(
        observation.get("toolsets_contract", {}).get("object") == "list",
        "official toolset envelope was not observed",
    )
    _require(
        observation.get("toolsets_contract", {}).get("platform") == "api_server",
        "wrong toolset platform",
    )
    tool_surface = observation.get("tool_surface") or {}
    _require(set(tool_surface.get("active_tools") or []) == EXPECTED_TOOLS, "wrong tools")
    _require(
        observation.get("memory_posture", {}).get("status") == "qualified",
        "memory posture not qualified",
    )
    _require_false(observation, "session_memory_header_sent", "observer sent memory header")

    _require(launch.get("runtime_submission_performed") is True, "run not submitted")
    _require(launch.get("runtime_start_recorded") is True, "start not recorded")
    _require(launch.get("session_id") == ADMISSION_ID, "session/admission mismatch")
    _require_false(launch, "session_memory_header_sent", "launch sent memory header")
    _require_false(launch, "automatic_retry_performed", "launch retried")
    _require_false(launch, "provider_routing_performed", "binding routed provider")
    _require_false(launch, "model_override_performed", "binding overrode model")

    _require(terminal.get("status") == "completed", f"run not completed: {terminal}")
    _require(
        "LAB_ACCEPTANCE_COMPLETED" in str(terminal.get("output") or ""),
        "context checks did not complete",
    )

    _require(
        reconciliation.get("pantheon_return_recorded") is True,
        "return not recorded",
    )
    _require_false(
        reconciliation,
        "technical_receipt_is_evidence",
        "technical receipt classified as Evidence",
    )
    _require_false(reconciliation, "scheduler_effect", "scheduler effect detected")
    _require_false(reconciliation, "retry_effect", "retry effect detected")
    recorded = reconciliation.get("recorded") or {}
    _require_false(recorded, "result_accepted", "result was accepted")
    _require_false(recorded, "evidence_admitted", "Evidence was admitted")
    _require_false(recorded, "project_mutated", "Project was mutated")

    reads = fixture_state.get("pantheon_reads") or []
    _require(any(path.endswith("/active-context") for path in reads), "manifest not read")
    _require(any(path.endswith("/project/project-lab") for path in reads), "entity not read")
    _require(
        any(path.endswith("/project/project-outside") for path in reads),
        "outside entity refusal not exercised",
    )
    _require(int(fixture_state.get("provider_calls") or 0) >= 4, "tool loop incomplete")

    journal = [
        json.loads(line)
        for line in (artifacts / "fixture-journal.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    _require(journal, "fixture journal is empty")
    _require(
        not any(item.get("session_memory_header_present") for item in journal),
        "X-Hermes-Session-Key reached a fixture",
    )

    _require(rollback.get("plugin_disabled") is True, "plugin rollback failed")
    _require(rollback.get("gateway_stopped") is True, "gateway rollback failed")
    _require(
        rollback.get("profile_route_unreachable") is True,
        "profile route remained reachable",
    )

    if sentinel_required:
        _require(sentinel is not None, "sentinel receipt is required")
        _require(
            sentinel.get("pre_tool_call_block_observed") is True,
            "pre_tool_call block was not observed through the real Runs route",
        )
        _require(
            sentinel.get("blocked_effect_sink_untouched") is True,
            "blocked sentinel effect touched its sink",
        )
        _require(
            sentinel.get("callback_exception_fail_open_observed") is True,
            "ordinary pre_tool_call callback exception did not reproduce pinned fail-open semantics",
        )
        _require(
            sentinel.get("exception_effect_sink_touched") is True,
            "exception-path sentinel effect did not reach its synthetic sink",
        )
        _require_false(
            sentinel,
            "pantheon_pep_qualified_by_this_test",
            "runtime sentinel was incorrectly promoted to Pantheon PEP qualification",
        )
        _require_false(
            sentinel,
            "technical_receipt_is_evidence",
            "sentinel technical observation classified as Evidence",
        )
        _require_false(
            sentinel,
            "production_authorization",
            "sentinel technical observation claimed production authorization",
        )
        _require(
            rollback.get("sentinel_exercised") is True,
            "sentinel run was not recorded as exercised",
        )
        _require(
            rollback.get("sentinel_plugin_disabled") is True,
            "sentinel plugin rollback failed",
        )
        _require(
            rollback.get("sentinel_tool_policy_restored") is True,
            "sentinel tool policy rollback failed",
        )
    else:
        _require(
            rollback.get("sentinel_exercised") is False,
            "non-sentinel lab incorrectly claims the sentinel was exercised",
        )

    limits = [
        "This qualifies an ephemeral GitHub-hosted laboratory installation only.",
        "The NAS installation, OpenWebUI path and production rollback remain unobserved.",
        "The inference provider and Pantheon API were deterministic local fixtures.",
    ]
    if sentinel_required:
        limits.append(
            "The effect sentinel is synthetic and characterizes Hermes hook behavior only; "
            "it does not qualify Pantheon's PEP."
        )

    summary = {
        "kind": "hermes_runtime_ephemeral_lab_acceptance",
        "status": "passed",
        "hermes_version": expected_version,
        "source_artifact_digest": source_digest,
        "profile": PROFILE,
        "profile_route": f"/p/{PROFILE}",
        "distribution_components": sorted(EXPECTED_COMPONENTS),
        "tool_surface": sorted(EXPECTED_TOOLS),
        "memory_posture": "qualified_off",
        "synthetic_run_completed": True,
        "context_manifest_read": True,
        "admitted_entity_read": True,
        "outside_entity_refused": True,
        "rollback_verified": True,
        "pre_tool_call_sentinel_exercised": sentinel_required,
        "pre_tool_call_block_observed": bool(
            sentinel_required and sentinel and sentinel.get("pre_tool_call_block_observed") is True
        ),
        "pre_tool_call_exception_fail_open_observed": bool(
            sentinel_required
            and sentinel
            and sentinel.get("callback_exception_fail_open_observed") is True
        ),
        "pre_tool_call_is_pantheon_pep": False,
        "pre_tool_call_sentinel_claim_scope": (
            "ephemeral_pinned_release_lab_only" if sentinel_required else None
        ),
        "deployed_route_guard_qualified": False,
        "repeat_sentinel_on_claimed_deployed_route": sentinel_required,
        "target_installation_observed": False,
        "production_activated": False,
        "future_tasks_authorized": False,
        "result_accepted": False,
        "evidence_admitted": False,
        "limits": limits,
    }
    (artifacts / "acceptance-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    configure_parser = sub.add_parser("configure")
    configure_parser.add_argument("--hermes-home", type=Path, required=True)
    configure_parser.add_argument("--fixture-url", required=True)
    configure_parser.add_argument("--output", type=Path)

    wait_parser = sub.add_parser("wait-http")
    wait_parser.add_argument("--url", required=True)
    wait_parser.add_argument("--bearer")
    wait_parser.add_argument("--timeout", type=float, default=60.0)
    wait_parser.add_argument("--output", type=Path)

    run_parser = sub.add_parser("wait-run")
    run_parser.add_argument("--base-url", required=True)
    run_parser.add_argument("--api-key", required=True)
    run_parser.add_argument("--run-id", required=True)
    run_parser.add_argument("--timeout", type=float, default=120.0)
    run_parser.add_argument("--output", type=Path, required=True)

    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("--artifacts", type=Path, required=True)
    return parser


def _emit(payload: dict[str, Any], output: Path | None) -> None:
    rendered = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if output is None:
        print(rendered, end="")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "configure":
        _emit(configure(args.hermes_home, args.fixture_url), args.output)
    elif args.command == "wait-http":
        _emit(wait_http(args.url, args.bearer, args.timeout), args.output)
    elif args.command == "wait-run":
        _emit(wait_run(args.base_url, args.api_key, args.run_id, args.timeout), args.output)
    elif args.command == "validate":
        _emit(validate(args.artifacts), None)
    else:  # pragma: no cover
        raise LabAcceptanceError(f"unsupported command: {args.command}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LabAcceptanceError as exc:
        print(f"Hermes runtime lab acceptance refused: {exc}")
        raise SystemExit(1) from exc
