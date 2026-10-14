"""MCP stdio projection of the transport-neutral Pantheon policy service.

Every primitive is read-only and side-effect-free. The server returns policy,
validation and candidate data; it never executes, sends, writes, approves,
installs, schedules, routes providers or promotes memory.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Callable

import yaml
from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from . import source_map
from .repo import find_repo_root
from .service import PantheonPolicyService

mcp = MCPServer(
    "pantheon-policy-server",
    instructions=(
        "Pantheon Next read-only policy plane. Consult doctrine, classify requests, "
        "prepare candidates and validate caller-provided structures or evidence. "
        "Decisions are data: Hermes enforces and executes outside Pantheon; the "
        "human decides consequential effects."
    ),
)


_READ_ONLY_ANNOTATIONS = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=False,
)
"""Protocol-level declaration of the property this package already guarantees.

Every primitive here consults governed data and returns a verdict. None of them
executes, sends, writes, approves, installs, schedules, routes a provider or
promotes memory, so the read-only, non-destructive, idempotent and closed-world
hints are true for the whole surface. A client reading the tool list can verify
that boundary without trusting this package's prose.

An annotation is a declaration, not an enforcement: it does not itself prevent an
effect. ``tests/test_tool_annotations.py`` fails closed when a tool is registered
without it, so the declaration cannot silently drift from the surface it describes.
"""


def _read_only_tool():
    """Register one read-only, side-effect-free Pantheon policy tool."""
    return mcp.tool(annotations=_READ_ONLY_ANNOTATIONS)


def _dump(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _load_yaml_document(raw: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        return None, _dump({"result": "error", "problems": [f"invalid YAML: {exc}"]})
    if not isinstance(data, dict):
        data = {"intent": str(data or "")}
    return data, None


@lru_cache(maxsize=1)
def _service() -> PantheonPolicyService:
    """Return one lazy read-only service for the stdio server process."""
    return PantheonPolicyService()


def _call(method_name: str, *args: Any) -> str:
    """Project one explicit service method as JSON."""
    method = getattr(_service(), method_name)
    return _dump(method(*args))


def _call_yaml(raw: str, method_name: str) -> str:
    """Parse one YAML mapping and invoke an explicit service method."""
    data, error = _load_yaml_document(raw)
    if error is not None:
        return error
    assert data is not None
    return _call(method_name, data)


def _make_resource_reader(key: str) -> Callable[[], str]:
    def read_resource() -> str:
        return _call("read_doctrine", key)

    read_resource.__name__ = f"read_{key.replace('-', '_')}"
    return read_resource


def _register_resources() -> None:
    for key, (relative_path, title) in source_map.SOURCES.items():
        mcp.resource(
            f"pantheon://{key}",
            name=key,
            description=(
                f"{title} — {relative_path} (labeled with authority and status)"
            ),
            mime_type="application/json",
        )(_make_resource_reader(key))


_register_resources()


@_read_only_tool()
def list_sources() -> str:
    """List governed sources with the historical JSON-array response shape."""
    return _dump(source_map.list_sources())


@_read_only_tool()
def find_relevant_sources(request_yaml: str) -> str:
    """Shortlist up to eight governance sources from conditions and search terms."""
    return _call_yaml(request_yaml, "find_relevant_sources")


@_read_only_tool()
def read_doctrine(key: str = "", input_key: str = "") -> str:
    """Read one allowlisted governed source; arbitrary paths are not accepted."""
    # Hermes deferred-tool envelopes have used both names across supported
    # runtime versions. Accepting the compatibility alias keeps a valid call
    # single-shot without broadening the allowlisted source-key boundary.
    selected_key = (key or input_key).strip()
    return _call("read_doctrine", selected_key)


@_read_only_tool()
def explain_governance_structure(source_key: str = "") -> str:
    """Explain repository placement without creating parallel doctrine."""
    return _call("explain_governance_structure", source_key)


@_read_only_tool()
def get_consultation_catalog() -> str:
    """Return the honest availability map for policy consultation surfaces."""
    return _call("consultation_catalog")


@_read_only_tool()
def explain_architecture(topic: str) -> str:
    """Explain one allowlisted architecture topic from governed sources."""
    return _call("explain_architecture", topic)


@_read_only_tool()
def get_capability_status(status_yaml: str) -> str:
    """Qualify a caller-provided capability observation; perform no live probe."""
    return _call_yaml(status_yaml, "qualify_capability_status")


@_read_only_tool()
def validate_passport(passport_yaml: str) -> str:
    """Validate a capability passport candidate; validation is not authorization."""
    return _call_yaml(passport_yaml, "validate_passport")


@_read_only_tool()
def classify_request(request_yaml: str) -> str:
    """Classify a request on the governed consequence, verification and approval axes."""
    return _call_yaml(request_yaml, "classify_request")


@_read_only_tool()
def route_governed_request(request_yaml: str = "", request_text: str = "") -> str:
    """Route YAML or plain request text; Hermes should not ask the user to build YAML."""
    raw = (request_yaml or request_text).strip()
    if not raw:
        return _dump(
            {
                "result": "error",
                "problems": ["request_yaml or request_text is required"],
            }
        )
    return _call_yaml(raw, "route_governed_request")


@_read_only_tool()
def evaluate_preflight(preflight_yaml: str) -> str:
    """Return candidate-work eligibility and missing gates without authorizing effects."""
    return _call_yaml(preflight_yaml, "evaluate_preflight")


@_read_only_tool()
def validate_decision(decision_yaml: str) -> str:
    """Validate a caller-provided human decision reference (scope, ceiling, expiry,
    object identity, digest, human signer). A valid verdict is not an approval."""
    return _call_yaml(decision_yaml, "validate_decision")


@_read_only_tool()
def prepare_task_contract_skeleton(request_yaml: str) -> str:
    """Prepare a non-executable Task Contract candidate skeleton."""
    return _call_yaml(request_yaml, "prepare_task_contract")


@_read_only_tool()
def prepare_evidence_pack_skeleton(request_yaml: str) -> str:
    """Prepare an Evidence Pack candidate skeleton; do not validate truth."""
    return _call_yaml(request_yaml, "prepare_evidence_pack")


@_read_only_tool()
def check_external_action(description: str) -> str:
    """Return the blocked-by-default legitimacy path for an external action."""
    return _call("check_external_action", description)


@_read_only_tool()
def run_doctor_checks() -> str:
    """Run fail-closed, read-only repository governance checks."""
    return _call("run_doctor")


@_read_only_tool()
def validate_apu_dossier(dossier_yaml: str) -> str:
    """Validate a candidate APU dossier; canonize and approve nothing."""
    return _call_yaml(dossier_yaml, "validate_apu_dossier")


@_read_only_tool()
def verify_install(evidence_yaml: str) -> str:
    """Classify installation posture from caller-provided evidence only."""
    return _call_yaml(evidence_yaml, "verify_install")


@_read_only_tool()
def verify_observability(evidence_yaml: str) -> str:
    """Classify observability posture from caller-provided evidence only."""
    return _call_yaml(evidence_yaml, "verify_observability")


@_read_only_tool()
def verify_backup(evidence_yaml: str) -> str:
    """Classify recoverability posture from caller-provided evidence only."""
    return _call_yaml(evidence_yaml, "verify_backup")


@_read_only_tool()
def verify_exposure(evidence_yaml: str) -> str:
    """Classify exposure posture from caller-provided evidence only."""
    return _call_yaml(evidence_yaml, "verify_exposure")


@_read_only_tool()
def verify_update(evidence_yaml: str) -> str:
    """Classify update availability from caller-provided version evidence only."""
    return _call_yaml(evidence_yaml, "verify_update")


@_read_only_tool()
def load_verification_preset(preset_yaml: str) -> str:
    """Validate and project a verification preset into a data-gathering plan."""
    return _call_yaml(preset_yaml, "load_verification_preset")


@_read_only_tool()
def plan_context_pack(request_yaml: str) -> str:
    """Prepare boundaries for a caller-assembled scoped Context Pack candidate."""
    return _call_yaml(request_yaml, "plan_context_pack")


@_read_only_tool()
def validate_context_pack(context_pack_yaml: str) -> str:
    """Validate one caller-provided Context Pack against the governed schema."""
    return _call_yaml(context_pack_yaml, "validate_context_pack")


def main() -> None:
    find_repo_root()
    mcp.run()


if __name__ == "__main__":
    main()
