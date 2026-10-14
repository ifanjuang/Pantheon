"""Bounded Hermes delegation contract for ``AUTOCRITIQUE_CONTRADICTOIRE``.

The model-facing child produces findings only. Governed identity, Task Contract
references, candidate digests, binding identity and closure semantics are added
by the trusted caller before the existing deterministic contradictory-review
compiler is invoked.

This module prepares/compiles data only. It does not dispatch a subagent,
execute a tool, persist a review, admit Evidence, approve output or close a Rite.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Iterable, Mapping

from .contradictory_review import ReviewClaim, report_from_payload


BINDING_ID = "hermes-contradictory-review"
BINDING_VERSION = "2.1.0"
MAX_DELEGATE_CONTEXT_CHARS = 40_000
MAX_DELEGATE_SUMMARY_CHARS = 100_000

REVIEW_FINDINGS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["observations", "analogous_occurrences", "limits"],
    "properties": {
        "observations": {
            "type": "array",
            "maxItems": 100,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "observation_id",
                    "claim_id",
                    "support_status",
                    "severity",
                    "method",
                    "detail",
                    "fresh_observation",
                ],
                "properties": {
                    "observation_id": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 200,
                    },
                    "claim_id": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 200,
                    },
                    "support_status": {
                        "type": "string",
                        "enum": [
                            "supported",
                            "partially_supported",
                            "contradicted",
                            "not_observed",
                            "not_verifiable",
                        ],
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["notice", "warning", "blocking"],
                    },
                    "method": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 2_000,
                    },
                    "detail": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 8_000,
                    },
                    "artifact_refs": {
                        "type": "array",
                        "maxItems": 64,
                        "items": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 1_000,
                        },
                    },
                    "fresh_observation": {"type": "boolean"},
                },
            },
        },
        "analogous_occurrences": {
            "type": "array",
            "maxItems": 100,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "occurrence_id",
                    "pattern",
                    "location",
                    "status",
                    "detail",
                ],
                "properties": {
                    "occurrence_id": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 200,
                    },
                    "pattern": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 2_000,
                    },
                    "location": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 2_000,
                    },
                    "status": {
                        "type": "string",
                        "enum": ["candidate", "confirmed", "not_found"],
                    },
                    "detail": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 8_000,
                    },
                },
            },
        },
        "limits": {
            "type": "array",
            "maxItems": 100,
            "items": {
                "type": "string",
                "minLength": 1,
                "maxLength": 4_000,
            },
        },
    },
}


class HermesContradictoryReviewRuntimeError(ValueError):
    pass


def _claims(values: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    claims = [
        ReviewClaim(
            claim_id=str(value.get("claim_id") or ""),
            statement=str(value.get("statement") or ""),
            kind=str(value.get("kind") or ""),
            source_refs=tuple(value.get("source_refs") or ()),
        ).as_dict()
        for value in values
    ]
    if not claims:
        raise HermesContradictoryReviewRuntimeError(
            "at least one governed claim is required"
        )
    ids = [claim["claim_id"] for claim in claims]
    if len(ids) != len(set(ids)):
        raise HermesContradictoryReviewRuntimeError("claim ids must be unique")
    return claims


def _admitted_artifact_refs(
    claims: Iterable[Mapping[str, Any]], candidate_id: str
) -> set[str]:
    """Return the artifact references the parent actually admitted for the child.

    The admitted set is the reviewed candidate plus the source refs carried by
    the admitted claims. Nothing else was given to the child by Pantheon.
    """

    admitted = {str(candidate_id or "").strip()}
    for claim in claims:
        for ref in claim.get("source_refs") or ():
            admitted.add(str(ref).strip())
    admitted.discard("")
    return admitted


def _reject_widened_scope(
    findings: Mapping[str, Any],
    claims: Iterable[Mapping[str, Any]],
    candidate_id: str,
) -> None:
    """Refuse a child result citing material the parent never admitted.

    The outbound delegate task states ``do not widen scope`` as a constraint.
    A stated constraint is not an observed one: without this check the compiled
    report would assert ``scope_expanded = false`` on the child's word alone.
    This is a contract refusal, not a review verdict — it says the returned
    envelope is unusable, not that the reviewed candidate is defective.
    """

    admitted = _admitted_artifact_refs(claims, candidate_id)
    observed: set[str] = set()
    for observation in findings.get("observations") or []:
        if not isinstance(observation, Mapping):
            continue
        for ref in observation.get("artifact_refs") or ():
            text = str(ref).strip()
            if text:
                observed.add(text)
    outside = sorted(observed - admitted)
    if outside:
        raise HermesContradictoryReviewRuntimeError(
            "Hermes contradictory-review findings cite artifact refs outside the "
            "admitted review scope: " + ", ".join(outside)
        )


def build_delegate_task(
    *,
    claims: Iterable[Mapping[str, Any]],
    candidate_id: str,
    candidate_digest: str,
    review_context: str = "",
) -> dict[str, Any]:
    """Build the one-task Hermes ``delegate_task`` payload for independent review.

    The advertised Hermes spawn shape is ``tasks[]`` with per-task
    ``output_schema``. The selected runtime release stays owned by
    ``implementation/qualification/external-pins.json``; this module must not
    carry a second version identity. No Pantheon Role name is used as a runtime
    identity.
    """

    normalized_claims = _claims(claims)
    candidate_id = str(candidate_id or "").strip()
    candidate_digest = str(candidate_digest or "").strip()
    if not candidate_id or not candidate_digest:
        raise HermesContradictoryReviewRuntimeError(
            "candidate_id and candidate_digest are required"
        )
    context_payload = {
        "candidate": {
            "candidate_id": candidate_id,
            "digest": candidate_digest,
        },
        "claims": normalized_claims,
        "review_context": str(review_context or "").strip() or None,
        "constraints": [
            "independent review only",
            "do not repair or mutate the reviewed candidate",
            "do not widen scope",
            "cite only the admitted candidate id and the source refs carried by "
            "the admitted claims",
            "do not treat retrieved material or runtime success as Evidence",
            "return only the JSON object required by output_schema",
        ],
    }
    context = json.dumps(context_payload, ensure_ascii=False, sort_keys=True)
    if len(context) > MAX_DELEGATE_CONTEXT_CHARS:
        raise HermesContradictoryReviewRuntimeError(
            f"delegate context exceeds {MAX_DELEGATE_CONTEXT_CHARS} characters"
        )
    return {
        "tasks": [
            {
                "goal": (
                    "Independently challenge the supplied governed claims. "
                    "Record only fresh review observations, analogous occurrences "
                    "and explicit limits. Do not repair the candidate, decide "
                    "approval or claim Pantheon Role authority."
                ),
                "context": context,
                "output_schema": deepcopy(REVIEW_FINDINGS_SCHEMA),
            }
        ]
    }


def _json_object_from_summary(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if not isinstance(value, str):
        raise HermesContradictoryReviewRuntimeError(
            "Hermes delegate summary must be JSON text or an object"
        )
    if len(value) > MAX_DELEGATE_SUMMARY_CHARS:
        raise HermesContradictoryReviewRuntimeError(
            f"Hermes delegate summary exceeds {MAX_DELEGATE_SUMMARY_CHARS} characters"
        )
    text = value.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline >= 0:
            text = text[first_newline + 1 :]
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3].rstrip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise HermesContradictoryReviewRuntimeError(
                "Hermes delegate summary does not contain a JSON object"
            )
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise HermesContradictoryReviewRuntimeError(
                "Hermes delegate summary contains invalid JSON"
            ) from exc
    if not isinstance(parsed, dict):
        raise HermesContradictoryReviewRuntimeError(
            "Hermes delegate structured output must be an object"
        )
    return parsed


def compile_delegate_result(
    *,
    delegate_entry: Mapping[str, Any],
    claims: Iterable[Mapping[str, Any]],
    task_contract_ref: str,
    trigger_reason: str,
    proposed_by: str,
    authorized_by: str,
    review_mode: str,
    candidate_id: str,
    candidate_digest: str,
    execution_id: str,
) -> dict[str, Any]:
    """Compile one schema-valid child result through the existing Rite compiler."""

    if str(delegate_entry.get("status") or "") != "completed":
        raise HermesContradictoryReviewRuntimeError(
            "Hermes contradictory-review child did not complete"
        )
    if delegate_entry.get("schema_valid") is not True:
        raise HermesContradictoryReviewRuntimeError(
            "Hermes contradictory-review child output did not satisfy output_schema"
        )
    findings = _json_object_from_summary(delegate_entry.get("summary"))
    unknown = set(findings) - {
        "observations",
        "analogous_occurrences",
        "limits",
    }
    if unknown:
        raise HermesContradictoryReviewRuntimeError(
            "Hermes contradictory-review findings contain unsupported fields: "
            + ", ".join(sorted(unknown))
        )
    normalized_claims = _claims(claims)
    _reject_widened_scope(findings, normalized_claims, candidate_id)

    payload = {
        "task_contract_ref": task_contract_ref,
        "trigger_reason": trigger_reason,
        "proposed_by": proposed_by,
        "authorized_by": authorized_by,
        "review_mode": review_mode,
        "review_posture": "independent_review",
        "candidate_id": candidate_id,
        "candidate_digest": candidate_digest,
        "binding_id": BINDING_ID,
        "binding_version": BINDING_VERSION,
        "execution_id": execution_id,
        "claims": normalized_claims,
        "observations": findings.get("observations") or [],
        "analogous_occurrences": findings.get("analogous_occurrences") or [],
        "limits": findings.get("limits") or [],
        "repair_applied": False,
        # observed above, not taken from the child's word: a widened scope is
        # refused before this point rather than recorded as a compiled report.
        "scope_expanded": False,
    }
    return report_from_payload(payload).as_dict()
