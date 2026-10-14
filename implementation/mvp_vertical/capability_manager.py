"""Capability management slice (Phase D).

A bounded, governed lifecycle for one capability at a time — the executable seam
for `COCKPIT_CAPABILITY_MANAGEMENT.md`. The manager inventories a capability,
authors a candidate action, obtains the Pantheon preflight through the chokepoint
(`policy_gate`), and asks an injected native executor to perform exactly one
operation, returning a technical receipt and a fresh observation.

It never executes a capability itself, routes no provider, installs nothing and
approves nothing. The native operation is performed by `executor`, external to
this manager; a consequential action runs only behind an allow verdict plus a
valid human decision (fail-closed). Distinctions held as data:

    installed != approved
    enabled != activated for a scope
    update_available != update_authorized
    technical receipt != evidence
    healthy != safe
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Callable

from .policy_gate import PolicyClient, enforce_consequential

CAPABILITY_TYPES = frozenset(
    {"skill", "function", "workflow", "runtime_agent", "plugin", "mcp_binding", "connector"}
)


@dataclass(frozen=True)
class CapabilityRecord:
    capability_id: str
    capability_type: str
    installation_status: str = "absent"  # absent | proposed | installed | suspended
    enablement_status: str = "disabled"  # disabled | enabled
    activation_scope: str | None = None
    health_status: str = "unknown"
    update_status: str = "unknown"  # unknown | up_to_date | update_available
    source_ref: str | None = None


# Each action: whether it is consequential (must route through the chokepoint),
# a legality predicate over the current record, and the record transition.
@dataclass(frozen=True)
class _Action:
    consequential: bool
    legal: Callable[[CapabilityRecord], str | None]  # None = legal, else reason
    apply: Callable[[CapabilityRecord], CapabilityRecord]


def _requires(status_field: str, value: str):
    def check(record: CapabilityRecord) -> str | None:
        if getattr(record, status_field) != value:
            return f"{status_field} must be {value!r} (is {getattr(record, status_field)!r})"
        return None

    return check


ACTIONS: dict[str, _Action] = {
    # Authoring a candidate is not consequential: nothing is installed.
    "propose_install": _Action(
        consequential=False,
        legal=_requires("installation_status", "absent"),
        apply=lambda r: replace(r, installation_status="proposed"),
    ),
    "install": _Action(
        consequential=True,
        legal=_requires("installation_status", "proposed"),
        apply=lambda r: replace(r, installation_status="installed", health_status="unknown"),
    ),
    "enable": _Action(
        consequential=True,
        legal=lambda r: _requires("installation_status", "installed")(r)
        or _requires("enablement_status", "disabled")(r),
        apply=lambda r: replace(r, enablement_status="enabled"),
    ),
    "disable": _Action(
        consequential=True,
        legal=_requires("enablement_status", "enabled"),
        apply=lambda r: replace(r, enablement_status="disabled", activation_scope=None),
    ),
    "update": _Action(
        consequential=True,
        legal=lambda r: _requires("installation_status", "installed")(r)
        or _requires("update_status", "update_available")(r),
        apply=lambda r: replace(r, update_status="up_to_date"),
    ),
    "suspend": _Action(
        consequential=True,
        legal=_requires("installation_status", "installed"),
        apply=lambda r: replace(
            r, installation_status="suspended", enablement_status="disabled", activation_scope=None
        ),
    ),
    "retire": _Action(
        consequential=True,
        legal=lambda r: None if r.installation_status in {"installed", "suspended"} else "not installed",
        apply=lambda r: replace(
            r, installation_status="absent", enablement_status="disabled", activation_scope=None
        ),
    ),
}


def plan_action(record: CapabilityRecord, action: str) -> dict[str, Any]:
    """Author a bounded action request candidate. No effect, no execution."""
    if record.capability_type not in CAPABILITY_TYPES:
        return {"action": action, "legal": False, "reason": f"unknown capability_type {record.capability_type!r}"}
    spec = ACTIONS.get(action)
    if spec is None:
        return {"action": action, "legal": False, "reason": f"unknown action {action!r}"}
    reason = spec.legal(record)
    return {
        "action": action,
        "capability_id": record.capability_id,
        "from_installation_status": record.installation_status,
        "consequential": spec.consequential,
        "legal": reason is None,
        "reason": reason,
    }


def governed_execute(
    record: CapabilityRecord,
    action: str,
    *,
    policy_client: PolicyClient,
    executor: Callable[[str, CapabilityRecord], dict[str, Any]],
    decision_payload: dict[str, Any] | None = None,
    candidate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Perform one lifecycle action under governance.

    A consequential action routes through the chokepoint (preflight + valid human
    decision) and runs `executor` only behind an allow verdict; on a block the
    executor never runs and the record is unchanged. The executor performs the
    native operation externally and returns a technical receipt."""
    plan = plan_action(record, action)
    if not plan["legal"]:
        return {"status": "refused", "plan": plan, "observation": record, "receipt": None}

    if ACTIONS[action].consequential:
        if decision_payload is None:
            return {
                "status": "blocked",
                "plan": plan,
                "reasons": ["a consequential capability action requires a human decision"],
                "observation": record,
                "receipt": None,
            }
        verdict = enforce_consequential(
            policy_client,
            candidate=candidate or {"request": {"intent": f"capability:{action}"}},
            decision_payload=decision_payload,
        )
        if not verdict.allowed:
            return {
                "status": "blocked",
                "plan": plan,
                "disposition": verdict.disposition,
                "reasons": verdict.reasons,
                "observation": record,
                "receipt": None,
            }

    receipt = executor(action, record)  # native op, external to this manager
    observation = ACTIONS[action].apply(record)
    return {
        "status": "applied",
        "plan": plan,
        "receipt": receipt,  # technical receipt != evidence
        "observation": observation,
        "notes": [
            "installed != approved; enabled != activated for a scope.",
            "The technical receipt is not Evidence and grants no approval.",
        ],
    }


class HermesCapabilityExecutor:
    """Generic HTTP transport for one externally implemented capability operation.

    This class does **not** model the public Hermes Agent Runs API. It is retained
    only as a transport seam for a separately verified native capability-operation
    binding. The historical default ``/v1/capabilities:operate`` was a candidate
    assumption and is not part of the verified Hermes Agent v0.19 stable API
    surface, so callers must now provide an explicit reviewed ``operations_path``.

    It does not execute the capability itself. `governed_execute` calls it only
    behind an allow verdict. A returned receipt is a technical acknowledgement,
    not Evidence or approval.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        operations_path: str | None = None,
        timeout: float = 10.0,
        client: Any | None = None,
    ):
        base_url = base_url.strip().rstrip("/")
        if not base_url:
            raise ValueError("base_url is required")
        if not api_key:
            raise ValueError("api_key is required")
        if not operations_path or not operations_path.strip().startswith("/"):
            raise ValueError(
                "operations_path must be an explicitly verified native capability endpoint; "
                "Hermes Agent v0.19 public Runs API is not a capability lifecycle endpoint"
            )
        self._base_url = base_url
        self._api_key = api_key
        self._operations_path = operations_path.strip()
        self._timeout = timeout
        self._client = client

    def __call__(self, action: str, record: CapabilityRecord) -> dict[str, Any]:
        body = {
            "action": action,
            "capability_id": record.capability_id,
            "capability_type": record.capability_type,
            "from_installation_status": record.installation_status,
        }
        client = self._client
        owns = client is None
        if owns:
            import httpx  # lazy: not a core dependency

            client = httpx.Client(timeout=self._timeout)
        try:
            response = client.post(
                self._base_url + self._operations_path,
                json=body,
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
        finally:
            if owns:
                client.close()
        return {
            "receipt_id": payload.get("receipt_id"),
            "runtime": "hermes",
            "action": action,
            "response": payload,
        }
