"""Review and apply the claim candidates of one Observation Bundle as one batch.

The per-candidate chain stays the only writer: review -> write command ->
separate human authorization -> application, each recorded per candidate as
before. This module only removes the repetition. A human looks at one preview,
whose digest covers every candidate and the decision taken on it, and approves
that digest once. The batch then replays the chain candidate by candidate, in
one transaction: if any step fails, nothing of the batch is kept.

Commands bind the owner revision, so candidates are prepared and applied one
after the other, never prepared all at once. Identity candidates
(``identity.*``) are not claim writes and are not part of a batch.

```text
batch approval != claim validation   (applied claims stay candidate)
one gesture    != fewer records      (every candidate keeps its own trail)
```
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from . import apu_mapping_reviews, apu_write_preparation, execution_results

ACCEPT = "accept"
REJECT = "reject"


class ApuBatchError(execution_results.ExecutionResultError):
    pass


def _digest(value: Any) -> str:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _candidates(execution: dict[str, Any], result_ref: str) -> list[dict[str, Any]]:
    result = next(
        (item for item in execution.get("results", []) if item.get("result_id") == result_ref),
        None,
    )
    if result is None or result.get("result_kind") != "observation_bundle":
        raise ApuBatchError("batch review needs one Observation Bundle result")
    payload = result.get("payload") or {}
    refs = [item.get("attribute_claim_id") for item in payload.get("attribute_claim_candidates") or []]
    refs += [item.get("relation_claim_id") for item in payload.get("relation_claim_candidates") or []]
    found = []
    for ref in refs:
        # Same lookup as the per-candidate review; it skips identity relations.
        candidate = apu_mapping_reviews.claim_candidate(execution, result_ref, str(ref or ""))
        if candidate is not None:
            found.append({"ref": ref, "candidate": candidate})
    if not found:
        raise ApuBatchError("the Observation Bundle has no claim candidate to review")
    return found


def preview_batch(
    conn, *, execution_result_id: str, result_ref: str, reject: list[str] | None = None
) -> dict[str, Any]:
    """Candidates with the decision taken on each, and the digest a human approves. Writes nothing."""
    execution = execution_results.get_execution_result(conn, execution_result_id)
    candidates = _candidates(execution, result_ref)
    refused = set(reject or [])
    unknown = refused - {item["ref"] for item in candidates}
    if unknown:
        raise ApuBatchError("rejected refs are not candidates of this bundle: " + ", ".join(sorted(unknown)))
    items = [
        {
            "ref": item["ref"],
            "decision": REJECT if item["ref"] in refused else ACCEPT,
            "candidate_digest": _digest(item["candidate"]),
            "candidate": item["candidate"],
        }
        for item in candidates
    ]
    digest = _digest(
        {
            "execution_result_id": execution_result_id,
            "result_ref": result_ref,
            "items": [(item["ref"], item["decision"], item["candidate_digest"]) for item in items],
        }
    )
    return {"execution_result_id": execution_result_id, "result_ref": result_ref, "batch_digest": digest, "items": items}


def apply_batch(
    conn,
    *,
    execution_result_id: str,
    result_ref: str,
    batch_digest: str,
    reviewer: str,
    authorized_by: str,
    applied_by: str,
    reject: list[str] | None = None,
    note: str = "",
) -> dict[str, Any]:
    """Replay the per-candidate chain for the exact batch a human approved, all or nothing."""
    preview = preview_batch(conn, execution_result_id=execution_result_id, result_ref=result_ref, reject=reject)
    if preview["batch_digest"] != batch_digest:
        raise ApuBatchError("the batch changed since it was approved: preview it again")
    batch_note = f"batch:{batch_digest}" + (f" · {note}" if note else "")
    applied, rejected = [], []
    with conn.transaction():
        for item in preview["items"]:
            ref = item["ref"]
            key = f"batch:{batch_digest}:{ref}"
            action = "accept_claim_candidate" if item["decision"] == ACCEPT else "reject_mapping"
            apu_mapping_reviews.append_mapping_review(
                conn,
                execution_result_id=execution_result_id,
                result_ref=result_ref,
                mapping_ref=ref,
                action=action,
                selected_stable_object_ref=None,
                clarification_question=None,
                note=batch_note,
                reviewer=reviewer,
                idempotency_key=f"{key}:review",
                # A replacement candidate is accepted only with the claim it declares it replaces.
                superseded_claim_ref=(
                    item["candidate"]["claim_candidate"].get("supersedes_claim_ref")
                    if item["decision"] == ACCEPT
                    else None
                ),
            )
            if item["decision"] == REJECT:
                rejected.append(ref)
                continue
            command = apu_write_preparation.prepare_write_command(
                conn,
                execution_result_id=execution_result_id,
                result_ref=result_ref,
                mapping_ref=ref,
                prepared_by=applied_by,
                idempotency_key=f"{key}:prepare",
            )
            apu_write_preparation.append_authorization(
                conn,
                command_id=command["command_id"],
                action="authorize_application",
                note=batch_note,
                authorized_by=authorized_by,
                idempotency_key=f"{key}:authorize",
            )
            apu_write_preparation.apply_authorized_write_command(
                conn,
                command_id=command["command_id"],
                applied_by=applied_by,
                idempotency_key=f"{key}:apply",
            )
            applied.append(ref)
    return {"batch_digest": batch_digest, "applied": applied, "rejected": rejected}
