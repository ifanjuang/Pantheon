from __future__ import annotations

import hashlib
from dataclasses import dataclass
from importlib.metadata import version as package_version
from typing import Callable, Mapping, Sequence

from isnad.audit import (
    ChainNodeAudit,
    GradingStrategy,
    SourceDocument,
    WeakestLink,
    build_audit_record_from_nodes,
    hmac_signer,
    hmac_verifier,
    sign_detached,
)
from isnad.audit.canonical import canonical_hash, canonical_json
from isnad.core.chain import Chain, ChainLinkSpec, make_claim_id
from isnad.core.grading import grade_chain
from isnad.types import NarratorGrade, TransformType


AUTHORITY = {
    "qualification_lab_only": True,
    "advisory_grade_only": True,
    "owns_claim_status": False,
    "verifies_claim": False,
    "admits_evidence": False,
    "owns_review": False,
    "owns_persistence": False,
    "authorizes_effect": False,
    "pdp_authority": False,
    "governed_identity_authority": False,
}

_AUDIT_NARRATOR_TYPES = {
    "source": "dataset",
    "dataset": "dataset",
    "scraper": "scraper",
    "model": "model",
    "human": "human",
    "tool": "tool",
    "retriever": "retriever",
}

_GRADE_RANK = {
    NarratorGrade.REJECTED: 0,
    NarratorGrade.WEAK: 1,
    NarratorGrade.UNGRADED: 1,
    NarratorGrade.ACCEPTABLE: 2,
    NarratorGrade.RELIABLE: 3,
}


class IsnadQualificationError(ValueError):
    """Raised when qualification input would blur the bounded observer contract."""


@dataclass(frozen=True)
class ProvenanceLink:
    narrator_id: str
    step: int
    grade: str
    transform_type: str
    narrator_type: str
    version: str = "unknown"
    trace_id: str = ""
    domain: str = "general"
    invocation_timestamp: str | None = None
    input_snapshot: str | None = None
    output_snapshot: str | None = None

    def __post_init__(self) -> None:
        if not self.narrator_id.strip():
            raise IsnadQualificationError("narrator_id is required")
        if self.step < 0:
            raise IsnadQualificationError("step must be non-negative")
        try:
            NarratorGrade(self.grade)
        except ValueError as exc:
            raise IsnadQualificationError(f"unsupported narrator grade: {self.grade}") from exc
        try:
            TransformType(self.transform_type)
        except ValueError as exc:
            raise IsnadQualificationError(
                f"unsupported transform type: {self.transform_type}"
            ) from exc
        if self.narrator_type not in _AUDIT_NARRATOR_TYPES:
            raise IsnadQualificationError(
                f"unsupported narrator type: {self.narrator_type}"
            )


@dataclass(frozen=True)
class ProvenanceSource:
    uri: str
    content_hash: str | None = None
    retrieved_at: str | None = None
    licence: str | None = None


@dataclass(frozen=True)
class AdvisoryProvenanceObservation:
    provider: str
    provider_version: str
    claim_id: str
    chain_status: str
    advisory_chain_grade: str
    weakest_link_narrator_id: str
    audit_record: Mapping[str, object]
    audit_record_hash: str
    detached_signature: str | None
    advisory_only: bool = True
    evidence_admitted: bool = False
    claim_verified: bool = False
    authorized_effect: bool = False
    persisted: bool = False


def _snapshot_hash(value: str | None) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _audit_redactor(include_claim_text: bool) -> Callable[[str, object], object]:
    def redact(field_name: str, value: object) -> object:
        if field_name == "claim_text" and not include_claim_text:
            digest = hashlib.sha256(str(value).encode("utf-8")).hexdigest()
            return f"sha256:{digest}"
        return value

    return redact


def _weakest_link(
    links: Sequence[ProvenanceLink],
    grades: Sequence[NarratorGrade],
) -> WeakestLink:
    if not links or not grades:
        return WeakestLink(narrator_id="", grade="ungraded", why="empty chain")
    idx = min(range(len(grades)), key=lambda item: _GRADE_RANK[grades[item]])
    grade = grades[idx]
    return WeakestLink(
        narrator_id=links[idx].narrator_id,
        grade=grade.value,
        why="lowest advisory narrator grade in the supplied qualification chain",
    )


def observe_transmission(
    *,
    claim_text: str,
    links: Sequence[ProvenanceLink],
    sources: Sequence[ProvenanceSource] = (),
    hmac_secret: str | None = None,
    include_claim_text_in_audit: bool = False,
) -> AdvisoryProvenanceObservation:
    """Grade and seal a transmission chain without making a Pantheon decision."""
    if not claim_text.strip():
        raise IsnadQualificationError("claim_text is required")
    if not links:
        raise IsnadQualificationError("at least one provenance link is required")
    if hmac_secret is not None and not hmac_secret:
        raise IsnadQualificationError("hmac_secret must be non-empty when supplied")

    ordered = tuple(sorted(links, key=lambda link: link.step))
    chain = Chain(
        [
            ChainLinkSpec(
                link.narrator_id,
                link.step,
                version=link.version,
                transform_type=TransformType(link.transform_type),
                trace_id=link.trace_id,
                domain=link.domain,
                input_snapshot=link.input_snapshot,
                output_snapshot=link.output_snapshot,
                timestamp=link.invocation_timestamp,
            )
            for link in ordered
        ]
    )
    grades = [NarratorGrade(link.grade) for link in ordered]
    transforms = [TransformType(link.transform_type) for link in ordered]
    chain_grade = grade_chain(grades, transforms, is_complete=chain.is_complete)

    audit_nodes = []
    for index, link in enumerate(ordered):
        previous = ordered[index - 1] if index > 0 else None
        upstream_ids = (
            [previous.narrator_id]
            if previous is not None and link.step == previous.step + 1
            else []
        )
        audit_nodes.append(
            ChainNodeAudit(
                narrator_id=link.narrator_id,
                narrator_type=_AUDIT_NARRATOR_TYPES[link.narrator_type],
                grade=link.grade,
                grade_rationale=(
                    "caller-supplied qualification grade; advisory provenance signal only"
                ),
                model_identifier=link.narrator_id,
                model_version=link.version,
                invocation_timestamp=link.invocation_timestamp,
                input_hash=_snapshot_hash(link.input_snapshot),
                output_hash=_snapshot_hash(link.output_snapshot),
                upstream_ids=upstream_ids,
            )
        )

    record = build_audit_record_from_nodes(
        claim_id=make_claim_id(claim_text),
        claim_text=claim_text,
        final_grade=chain_grade.value,
        grading_strategy=GradingStrategy(
            name="RefinedWeakestLink",
            version="1",
            parameters={
                "input_grade_basis": "caller_supplied_qualification_input",
                "pantheon_authority": "none",
            },
        ),
        nodes=audit_nodes,
        weakest_link=_weakest_link(ordered, grades),
        source_documents=[
            SourceDocument(
                uri=source.uri,
                retrieved_at=source.retrieved_at,
                content_hash=source.content_hash,
                licence=source.licence,
            )
            for source in sources
        ],
        human_oversight=[],
        redact_fn=_audit_redactor(include_claim_text_in_audit),
    )
    if hmac_secret is not None:
        sign_detached(record, hmac_signer(hmac_secret))

    serialized = record.to_dict()
    return AdvisoryProvenanceObservation(
        provider="isnad",
        provider_version=package_version("isnad"),
        claim_id=record.claim_id,
        chain_status=chain.chain_status.value,
        advisory_chain_grade=chain_grade.value,
        weakest_link_narrator_id=record.weakest_link.narrator_id,
        audit_record=serialized,
        audit_record_hash=record.integrity.record_hash,
        detached_signature=record.integrity.detached_signature,
    )


def verify_serialized_audit_record(
    audit_record: Mapping[str, object],
    *,
    hmac_secret: str | None = None,
) -> bool:
    """Verify the self-hash and, when requested, the detached HMAC signature."""
    integrity = audit_record.get("integrity")
    if not isinstance(integrity, Mapping):
        return False
    record_hash = integrity.get("record_hash")
    if not isinstance(record_hash, str) or not record_hash:
        return False

    payload = {key: value for key, value in audit_record.items() if key != "integrity"}
    if canonical_hash(payload) != record_hash:
        return False

    if hmac_secret is None:
        return True
    signature = integrity.get("detached_signature")
    if not isinstance(signature, str) or not signature:
        return False
    return hmac_verifier(hmac_secret)(canonical_json(payload), signature)
