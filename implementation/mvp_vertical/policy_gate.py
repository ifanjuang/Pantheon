"""Policy chokepoint seam (Phase C): a consequential effect routes through the
Pantheon policy check before it happens.

This repository does not embed the Pantheon policy service. It defines the seam
the runtime uses to consult a Policy Decision Point (Pantheon `mcp-server`) and
to enforce the verdict — the Policy Enforcement Point role.

Rules:

- fail closed on transport, malformed payload or non-eligible preflight;
- bind human-decision validation to PEP-derived effect facts when supplied;
- require independently authenticated issuers for the closed direct-human effect class;
- never let a validated Decision override explicit PDP effect-denial flags;
- consume one-shot Decisions at the operational PEP when the PDP explicitly
  requires replay protection for a bounded external-effect qualification;
- neutralize runtime/model smart approvals.

`eligible_for_candidate_work` is not an external-effect authorization. External
permission is honored only when the PDP explicitly emits it. The synthetic Pantheon-Next#664
qualification additionally requires a validated gate signal and a local one-shot
consumer before any effect-producing caller may receive an allow verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from .policy_request import (
    PolicyRequestError,
    bind_decision_payload,
    build_preflight_payload,
    requires_authenticated_human_decision,
)

_ELIGIBLE_DISPOSITIONS = frozenset(
    {
        "eligible_for_candidate_work",
        "eligible_with_gate_signals_unverified",
        "eligible_with_gate_validated",
    }
)

OBJECT_IDENTITY_KEY = "object_identity"


class PolicyClient(Protocol):
    def preflight(self, candidate: dict[str, Any]) -> dict[str, Any]:
        ...

    def validate_decision(self, payload: dict[str, Any]) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class GateVerdict:
    allowed: bool
    disposition: str
    reasons: list[str] = field(default_factory=list)
    replay_guard_required: bool = False
    decision_id: str | None = None


def enforce_consequential(
    client: PolicyClient,
    *,
    candidate: dict[str, Any],
    decision_payload: dict[str, Any],
    consume_decision: Callable[[str], bool] | None = None,
) -> GateVerdict:
    """Consult the PDP and decide whether the local executor may run."""
    try:
        bound_decision = bind_decision_payload(candidate, decision_payload)
        preflight_payload = build_preflight_payload(candidate, bound_decision)
    except PolicyRequestError as exc:
        return GateVerdict(False, "blocked_invalid_decision_envelope", [str(exc)])
    except Exception as exc:
        return GateVerdict(False, "policy_unavailable", [f"policy request binding failed: {exc}"])

    try:
        preflight = client.preflight(preflight_payload)
    except Exception as exc:
        return GateVerdict(False, "policy_unavailable", [f"preflight call failed: {exc}"])

    disposition = str(preflight.get("policy_disposition", "unknown"))
    if disposition not in _ELIGIBLE_DISPOSITIONS:
        reasons = [f"preflight disposition: {disposition}"]
        reasons += list(preflight.get("missing_requirements", []))
        return GateVerdict(False, disposition, reasons)

    request = preflight_payload["request"]
    requests_external_effect = bool(
        request.get("external_effect") or request.get("transmission_requested")
    )
    if requests_external_effect and preflight.get("external_effect_allowed") is not True:
        return GateVerdict(
            False,
            "blocked_external_effect_not_authorized",
            [
                "Pantheon preflight did not authorize an external effect",
                f"policy disposition: {disposition}",
            ],
        )

    replay_guard_required = bool(preflight.get("replay_guard_required", False))
    if replay_guard_required and preflight.get("gate_signal_validation_performed") is not True:
        return GateVerdict(
            False,
            "blocked_unvalidated_gate_signal",
            [
                "Pantheon requested one-shot replay protection without reporting "
                "that gate-signal validation was performed"
            ],
        )

    if request.get("memory_promotion_requested") and preflight.get(
        "canonical_effect_allowed"
    ) is not True:
        return GateVerdict(
            False,
            "blocked_canonical_effect_not_authorized",
            [
                "Pantheon preflight did not authorize a canonical/memory effect",
                f"policy disposition: {disposition}",
            ],
        )

    try:
        validation = client.validate_decision(bound_decision)
    except Exception as exc:
        return GateVerdict(False, "policy_unavailable", [f"decision validation failed: {exc}"])

    if validation.get("verdict") != "valid":
        reasons = [f"decision verdict: {validation.get('verdict', 'unknown')}"]
        reasons += list(validation.get("findings", []))
        return GateVerdict(False, disposition, reasons)

    if (
        requires_authenticated_human_decision(candidate)
        and validation.get("issuer_authenticated") is not True
    ):
        reasons = [
            "direct human consequential effect requires an independently authenticated issuer"
        ]
        reasons += list(validation.get("findings", []))
        return GateVerdict(False, "blocked_unauthenticated_human_decision", reasons)

    decision = bound_decision.get("decision") or {}
    decision_id = str(decision.get("decision_id") or "").strip() or None
    if replay_guard_required and decision_id is None:
        return GateVerdict(
            False,
            "blocked_missing_decision_identity",
            ["one-shot replay protection requires an immutable decision_id"],
        )

    if replay_guard_required:
        if consume_decision is None:
            return GateVerdict(
                False,
                "blocked_replay_guard_unavailable",
                ["PDP requires one-shot decision consumption before an allow verdict"],
                replay_guard_required=True,
                decision_id=decision_id,
            )
        try:
            consumed = consume_decision(decision_id or "")
        except Exception as exc:
            return GateVerdict(
                False,
                "blocked_replay_guard_unavailable",
                [f"decision consumption failed closed: {exc}"],
                replay_guard_required=True,
                decision_id=decision_id,
            )
        if consumed is not True:
            return GateVerdict(
                False,
                "blocked_replayed_decision",
                [f"decision {decision_id!r} has already been consumed"],
                replay_guard_required=True,
                decision_id=decision_id,
            )

    return GateVerdict(
        True,
        disposition,
        [],
        replay_guard_required=replay_guard_required,
        decision_id=decision_id,
    )


def governed_effect(
    client: PolicyClient,
    *,
    candidate: dict[str, Any],
    decision_payload: dict[str, Any],
    effect: Callable[[], Any],
    consume_decision: Callable[[str], bool] | None = None,
) -> dict[str, Any]:
    verdict = enforce_consequential(
        client,
        candidate=candidate,
        decision_payload=decision_payload,
        consume_decision=consume_decision,
    )
    if not verdict.allowed:
        return {
            "status": "blocked",
            "disposition": verdict.disposition,
            "reasons": verdict.reasons,
            "effect_ran": False,
        }

    qualification_trace: dict[str, Any] | None = None
    if verdict.replay_guard_required:
        qualification_trace = {
            "decision_consumed_once": True,
            "decision_id": verdict.decision_id,
            "runtime_success_is_evidence": False,
            "effect_execution_is_approval": False,
        }

    result = {
        "status": "applied",
        "disposition": verdict.disposition,
        "effect_ran": True,
        "result": effect(),
    }
    if qualification_trace is not None:
        result["qualification_trace"] = qualification_trace
    return result


class StandInPolicyClient:
    """Deterministic offline PDP stand-in for tests; not Pantheon authority."""

    _SYSTEM_PREFIXES = ("system", "service", "runtime", "hermes", "bot", "agent")

    def __init__(
        self,
        *,
        disposition: str = "eligible_for_candidate_work",
        external_effect_allowed: bool = True,
        canonical_effect_allowed: bool = False,
        gate_signal_validation_performed: bool = False,
        replay_guard_required: bool = False,
        issuer_authenticated: bool = True,
    ):
        self._disposition = disposition
        self._external_effect_allowed = external_effect_allowed
        self._canonical_effect_allowed = canonical_effect_allowed
        self._gate_signal_validation_performed = gate_signal_validation_performed
        self._replay_guard_required = replay_guard_required
        self._issuer_authenticated = issuer_authenticated
        self.last_preflight: dict[str, Any] | None = None
        self.last_decision: dict[str, Any] | None = None

    def preflight(self, candidate: dict[str, Any]) -> dict[str, Any]:
        self.last_preflight = candidate
        return {
            "policy_disposition": self._disposition,
            "missing_requirements": [],
            "external_effect_allowed": self._external_effect_allowed,
            "canonical_effect_allowed": self._canonical_effect_allowed,
            "gate_signal_validation_performed": self._gate_signal_validation_performed,
            "replay_guard_required": self._replay_guard_required,
        }

    def validate_decision(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.last_decision = payload
        decision = payload.get("decision") or {}
        expectation = payload.get("expectation") or {}
        findings: list[str] = []
        signer = str(decision.get("decided_by", "")).strip().lower()
        if not signer or signer.split(":", 1)[0].split("-", 1)[0] in self._SYSTEM_PREFIXES:
            findings.append("decided_by is empty or a non-human identity")
        req_scope = expectation.get("required_scope")
        if req_scope is not None and decision.get("scope") != req_scope:
            findings.append("decision scope does not match required scope")
        required_ceiling = expectation.get("required_ceiling")
        if required_ceiling is not None and decision.get("approval_level") != required_ceiling:
            findings.append("decision approval_level does not match required ceiling")
        object_identity = expectation.get("object_identity")
        if object_identity is not None and decision.get("object_identity") != object_identity:
            findings.append("decision object_identity does not match effect object")
        expected_digest = expectation.get("expected_digest")
        if expected_digest is not None and decision.get("content_digest") != expected_digest:
            findings.append("decision content_digest does not match effect digest")
        verdict = "valid" if not findings else "invalid"
        return {
            "verdict": verdict,
            "findings": findings,
            "issuer_authenticated": self._issuer_authenticated if verdict == "valid" else False,
        }


class HttpPolicyClient:
    """Real ``PolicyClient`` for the Pantheon internal HTTP PDP."""

    _PREFLIGHT = "/policy/preflights:evaluate"
    _VALIDATE = "/policy/decisions:validate"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout: float = 5.0,
        client: Any | None = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        self._client = client

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        client = self._client
        owns = client is None
        if owns:
            import httpx

            client = httpx.Client(timeout=self._timeout)
        try:
            response = client.post(
                self._base_url + path,
                json=body,
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=self._timeout,
            )
            response.raise_for_status()
            return response.json()
        finally:
            if owns:
                client.close()

    def preflight(self, candidate: dict[str, Any]) -> dict[str, Any]:
        return self._post(self._PREFLIGHT, candidate)

    def validate_decision(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post(self._VALIDATE, payload)
