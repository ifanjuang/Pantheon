"""Deterministic implementation contract for contradictory review.

The contract compiles bounded Hermes-side review observations into a Trace
projection and a Rite Review Card candidate. It does not execute tools, repair
artifacts, close the rite, admit Evidence, authorize a task or approve output.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

RITE_ID = "AUTOCRITIQUE_CONTRADICTOIRE"
REVIEW_MODES = {"mode_light", "mode_standard", "mode_full"}
REVIEW_POSTURES = {"self_review", "independent_review"}
CLAIM_KINDS = {"fact", "interpretation", "recommendation"}
SUPPORT_STATUSES = {
    "supported",
    "partially_supported",
    "contradicted",
    "not_observed",
    "not_verifiable",
}
SEVERITIES = {"notice", "warning", "blocking"}
REPORT_STATUSES = {
    "review_completed",
    "review_completed_with_reserve",
    "review_blocked",
    "review_inconclusive",
}
OCCURRENCE_STATUSES = {"candidate", "confirmed", "not_found"}


def _text(name: str, value: object) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{name} is required")
    return normalized


def _unique_texts(name: str, values: object) -> tuple[str, ...]:
    if values in (None, ""):
        return ()
    if not isinstance(values, (list, tuple)):
        raise ValueError(f"{name} must be a list")
    return tuple(dict.fromkeys(_text(name, value) for value in values))


def _digest(payload: Any) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ReviewClaim:
    claim_id: str
    statement: str
    kind: str
    source_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "claim_id", _text("claim_id", self.claim_id))
        object.__setattr__(self, "statement", _text("statement", self.statement))
        if self.kind not in CLAIM_KINDS:
            raise ValueError(f"unsupported claim kind: {self.kind}")
        object.__setattr__(self, "source_refs", _unique_texts("source_refs", self.source_refs))

    def as_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "statement": self.statement,
            "kind": self.kind,
            "source_refs": list(self.source_refs),
        }


@dataclass(frozen=True)
class ReviewObservation:
    observation_id: str
    claim_id: str
    support_status: str
    severity: str
    method: str
    detail: str
    artifact_refs: tuple[str, ...] = ()
    fresh_observation: bool = True

    def __post_init__(self) -> None:
        for field in ("observation_id", "claim_id", "method", "detail"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        if self.support_status not in SUPPORT_STATUSES:
            raise ValueError(f"unsupported support status: {self.support_status}")
        if self.severity not in SEVERITIES:
            raise ValueError(f"unsupported observation severity: {self.severity}")
        if not isinstance(self.fresh_observation, bool):
            raise ValueError("fresh_observation must be boolean")
        object.__setattr__(self, "artifact_refs", _unique_texts("artifact_refs", self.artifact_refs))

    def as_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "claim_id": self.claim_id,
            "support_status": self.support_status,
            "severity": self.severity,
            "method": self.method,
            "detail": self.detail,
            "artifact_refs": list(self.artifact_refs),
            "fresh_observation": self.fresh_observation,
        }


@dataclass(frozen=True)
class AnalogousOccurrence:
    occurrence_id: str
    pattern: str
    location: str
    status: str
    detail: str

    def __post_init__(self) -> None:
        for field in ("occurrence_id", "pattern", "location", "detail"):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        if self.status not in OCCURRENCE_STATUSES:
            raise ValueError(f"unsupported analogous occurrence status: {self.status}")

    def as_dict(self) -> dict[str, str]:
        return {
            "occurrence_id": self.occurrence_id,
            "pattern": self.pattern,
            "location": self.location,
            "status": self.status,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class ContradictoryReviewReport:
    task_contract_ref: str
    trigger_reason: str
    proposed_by: str
    authorized_by: str
    review_mode: str
    review_posture: str
    candidate_id: str
    candidate_digest: str
    binding_id: str
    binding_version: str
    execution_id: str
    claims: tuple[ReviewClaim, ...]
    observations: tuple[ReviewObservation, ...] = ()
    analogous_occurrences: tuple[AnalogousOccurrence, ...] = ()
    limits: tuple[str, ...] = ()
    repair_applied: bool = False
    scope_expanded: bool = False

    def __post_init__(self) -> None:
        for field in (
            "task_contract_ref",
            "trigger_reason",
            "proposed_by",
            "authorized_by",
            "candidate_id",
            "candidate_digest",
            "binding_id",
            "binding_version",
            "execution_id",
        ):
            object.__setattr__(self, field, _text(field, getattr(self, field)))
        if self.review_mode not in REVIEW_MODES:
            raise ValueError(f"unsupported review mode: {self.review_mode}")
        if self.review_posture not in REVIEW_POSTURES:
            raise ValueError(f"unsupported review posture: {self.review_posture}")
        if not isinstance(self.repair_applied, bool) or not isinstance(self.scope_expanded, bool):
            raise ValueError("repair_applied and scope_expanded must be boolean")
        if self.review_posture == "independent_review" and self.repair_applied:
            raise ValueError("independent review cannot repair the reviewed candidate")
        if self.scope_expanded:
            raise ValueError("review cannot expand task scope")

        claims = tuple(self.claims)
        observations = tuple(self.observations)
        occurrences = tuple(self.analogous_occurrences)
        if not claims or any(not isinstance(item, ReviewClaim) for item in claims):
            raise ValueError("claims must contain at least one ReviewClaim")
        if any(not isinstance(item, ReviewObservation) for item in observations):
            raise ValueError("observations must contain ReviewObservation values")
        if any(not isinstance(item, AnalogousOccurrence) for item in occurrences):
            raise ValueError("analogous_occurrences must contain AnalogousOccurrence values")

        claim_ids = [item.claim_id for item in claims]
        observation_ids = [item.observation_id for item in observations]
        occurrence_ids = [item.occurrence_id for item in occurrences]
        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError("claim ids must be unique")
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("observation ids must be unique")
        if len(occurrence_ids) != len(set(occurrence_ids)):
            raise ValueError("analogous occurrence ids must be unique")
        unknown_claims = sorted({item.claim_id for item in observations} - set(claim_ids))
        if unknown_claims:
            raise ValueError(f"observations reference unknown claims: {', '.join(unknown_claims)}")

        object.__setattr__(self, "claims", claims)
        object.__setattr__(self, "observations", observations)
        object.__setattr__(self, "analogous_occurrences", occurrences)
        object.__setattr__(self, "limits", _unique_texts("limits", self.limits))

    @property
    def status(self) -> str:
        if not self.observations:
            return "review_inconclusive"
        if any(item.severity == "blocking" for item in self.observations):
            return "review_blocked"
        if self.limits or any(
            item.support_status != "supported" or not item.fresh_observation
            for item in self.observations
        ):
            return "review_completed_with_reserve"
        return "review_completed"

    @property
    def zeus_status_candidate(self) -> str:
        return {
            "review_completed": "rite_completed_as_draft",
            "review_completed_with_reserve": "rite_completed_with_reserve",
            "review_blocked": "rite_blocked",
            "review_inconclusive": "rite_completed_with_reserve",
        }[self.status]

    @property
    def review_id(self) -> str:
        return f"crr-{_digest(self._identity())[:24]}"

    def _identity(self) -> dict[str, Any]:
        return {
            "task_contract_ref": self.task_contract_ref,
            "rite_id": RITE_ID,
            "trigger_reason": self.trigger_reason,
            "proposed_by": self.proposed_by,
            "authorized_by": self.authorized_by,
            "review_mode": self.review_mode,
            "review_posture": self.review_posture,
            "candidate_id": self.candidate_id,
            "candidate_digest": self.candidate_digest,
            "binding_id": self.binding_id,
            "binding_version": self.binding_version,
            "execution_id": self.execution_id,
            "claims": [item.as_dict() for item in self.claims],
            "observations": [item.as_dict() for item in self.observations],
            "analogous_occurrences": [item.as_dict() for item in self.analogous_occurrences],
            "limits": list(self.limits),
            "repair_applied": self.repair_applied,
            "scope_expanded": self.scope_expanded,
        }

    def as_dict(self) -> dict[str, Any]:
        status = self.status
        if status not in REPORT_STATUSES:
            raise AssertionError(f"invalid contradictory review status: {status}")
        blocked_claims = sorted(
            {
                item.claim_id
                for item in self.observations
                if item.severity == "blocking" or item.support_status == "contradicted"
            }
        )
        tensions = [
            {
                "claim_id": item.claim_id,
                "support_status": item.support_status,
                "severity": item.severity,
                "detail": item.detail,
            }
            for item in self.observations
            if item.support_status != "supported" or item.severity != "notice"
        ]
        return {
            "review_id": self.review_id,
            "status": status,
            "task_contract_ref": self.task_contract_ref,
            "rite_id": RITE_ID,
            "review_mode": self.review_mode,
            "review_posture": self.review_posture,
            "candidate": {"candidate_id": self.candidate_id, "digest": self.candidate_digest},
            "produced_by": {
                "binding_id": self.binding_id,
                "binding_version": self.binding_version,
                "execution_id": self.execution_id,
            },
            "claim_reconciliation": [
                {
                    **claim.as_dict(),
                    "observations": [
                        item.as_dict() for item in self.observations if item.claim_id == claim.claim_id
                    ],
                }
                for claim in self.claims
            ],
            "analogous_occurrences": [item.as_dict() for item in self.analogous_occurrences],
            "limits": list(self.limits),
            "trace": {
                "trace_type": "contradictory_review_observation",
                "review_id": self.review_id,
                "observed_claim_ids": sorted({item.claim_id for item in self.observations}),
                "write_effect": self.repair_applied,
                "scope_expanded": False,
                "authorization_effect": "none",
            },
            "rite_review_card": {
                "rite_id": RITE_ID,
                "trigger_reason": self.trigger_reason,
                "proposed_by": self.proposed_by,
                "authorized_by": self.authorized_by,
                "inputs_considered": [self.candidate_id, *sorted({ref for claim in self.claims for ref in claim.source_refs})],
                "outputs_retained": ["claim_reconciliation", "contradiction_findings", "review_limits"],
                "tensions_exposed": tensions,
                "blocked_claims": blocked_claims,
                "ZEUS_status_candidate": self.zeus_status_candidate,
                "User_Decision_Gate": status == "review_blocked",
                "Evidence_Pack_impact": "candidate_observations_only",
                "memory_impact": "none",
                "next_allowed_action": (
                    "zeus_or_human_review"
                    if status == "review_blocked"
                    else "resolve_limits_then_request_zeus_closure"
                    if status in {"review_completed_with_reserve", "review_inconclusive"}
                    else "request_zeus_closure"
                ),
            },
            "authority": {
                "is_evidence": False,
                "is_approval": False,
                "is_zeus_closure": False,
                "is_task_authorization": False,
                "requires_zeus_closure": True,
            },
        }


def report_from_payload(payload: Mapping[str, Any]) -> ContradictoryReviewReport:
    """Build a validated report from a JSON-compatible Hermes handoff payload."""
    if payload.get("rite_id", RITE_ID) != RITE_ID:
        raise ValueError(f"unsupported rite_id: {payload.get('rite_id')}")
    return ContradictoryReviewReport(
        task_contract_ref=payload.get("task_contract_ref", ""),
        trigger_reason=payload.get("trigger_reason", ""),
        proposed_by=payload.get("proposed_by", ""),
        authorized_by=payload.get("authorized_by", ""),
        review_mode=payload.get("review_mode", ""),
        review_posture=payload.get("review_posture", ""),
        candidate_id=payload.get("candidate_id", ""),
        candidate_digest=payload.get("candidate_digest", ""),
        binding_id=payload.get("binding_id", ""),
        binding_version=payload.get("binding_version", ""),
        execution_id=payload.get("execution_id", ""),
        claims=tuple(ReviewClaim(**item) for item in payload.get("claims", [])),
        observations=tuple(ReviewObservation(**item) for item in payload.get("observations", [])),
        analogous_occurrences=tuple(
            AnalogousOccurrence(**item) for item in payload.get("analogous_occurrences", [])
        ),
        limits=tuple(payload.get("limits", [])),
        repair_applied=payload.get("repair_applied", False),
        scope_expanded=payload.get("scope_expanded", False),
    )
