"""Read-only Cockpit projection for Project Anatomy.

This module derives presentation lenses from the executable APU owner. It creates
no project fact, performs no write, admits no Evidence and infers no authorization.
Where the current owner does not persist enough information (notably Observation
Bundle coverage and registered hierarchy semantics), the projection reports that
limitation instead of inventing an answer.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from . import apu_owner


ATTENTION_PROOF_STATUSES = {
    "source_missing",
    "source_incomplete",
    "contradictory_evidence",
    "authority_too_low",
    "requires_more_evidence",
}
MAPPED_IDENTITY_PROOF_STATUSES = {"accepted_as_support"}


def _entity_id(ref: Any, entity_type: str) -> str | None:
    if not isinstance(ref, dict) or ref.get("entity_type") != entity_type:
        return None
    entity_id = str(ref.get("entity_id") or "").strip()
    return entity_id or None


def _claim_phase_refs(claim: dict[str, Any]) -> set[str]:
    validity = claim.get("validity")
    if not isinstance(validity, dict):
        return set()
    phase = str(validity.get("established_at_phase") or "").strip()
    return {phase} if phase else set()


def _claim_summary(claim: dict[str, Any], *, claim_type: str) -> dict[str, Any]:
    summary = {
        "claim_type": claim_type,
        "claim_id": claim.get(
            "attribute_claim_id" if claim_type == "attribute_claim" else "relation_claim_id"
        ),
        "subject_ref": claim.get("subject_ref"),
        "proof_status": claim.get("proof_status"),
        "certainty": claim.get("certainty"),
        "assertion_mode": claim.get("assertion_mode"),
        "source_authority": claim.get("source_authority"),
        "source_representation_refs": list(claim.get("source_representation_refs") or []),
        "phase_refs": sorted(_claim_phase_refs(claim)),
    }
    if claim_type == "attribute_claim":
        summary["attribute_key"] = claim.get("attribute_key")
        summary["value"] = claim.get("value")
    else:
        summary["relation_type"] = claim.get("relation_type")
        summary["object_ref"] = claim.get("object_ref")
    return summary


def build_project_anatomy_projection(
    anatomy: dict[str, Any],
    *,
    model_doctrine_ref: str | None,
) -> dict[str, Any]:
    """Calculate bounded lenses from the canonical owner projection."""
    stable_entries = list(anatomy.get("stable_objects") or [])
    representations = list(anatomy.get("source_representations") or [])
    attribute_claims = list(anatomy.get("attribute_claims") or [])
    relation_claims = list(anatomy.get("relation_claims") or [])

    representations_by_id = {
        str(item.get("representation_id")): item
        for item in representations
        if str(item.get("representation_id") or "").strip()
    }
    mapped_objects_by_representation: dict[str, set[str]] = defaultdict(set)
    mapped_representations_by_object: dict[str, set[str]] = defaultdict(set)

    for claim in relation_claims:
        if claim.get("relation_type") != "identity.represents":
            continue
        representation_id = _entity_id(claim.get("subject_ref"), "source_representation")
        object_id = _entity_id(claim.get("object_ref"), "stable_object")
        if not representation_id or not object_id:
            continue
        if claim.get("proof_status") not in MAPPED_IDENTITY_PROOF_STATUSES:
            continue
        mapped_objects_by_representation[representation_id].add(object_id)
        mapped_representations_by_object[object_id].add(representation_id)

    attributes_by_object: dict[str, list[dict[str, Any]]] = defaultdict(list)
    attributes_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    identity_claims_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    relations_by_object: dict[str, list[dict[str, Any]]] = defaultdict(list)
    phases_by_object: dict[str, set[str]] = defaultdict(set)
    source_refs_by_object: dict[str, set[str]] = defaultdict(set)
    attention_by_object: dict[str, list[str]] = defaultdict(list)

    for claim in attribute_claims:
        summarized = _claim_summary(claim, claim_type="attribute_claim")
        object_id = _entity_id(claim.get("subject_ref"), "stable_object")
        source_id = _entity_id(claim.get("subject_ref"), "source_representation")
        if source_id:
            attributes_by_source[source_id].append(summarized)
        if not object_id:
            continue
        attributes_by_object[object_id].append(summarized)
        phases_by_object[object_id].update(_claim_phase_refs(claim))
        source_refs_by_object[object_id].update(claim.get("source_representation_refs") or [])
        if claim.get("proof_status") in ATTENTION_PROOF_STATUSES:
            attention_by_object[object_id].append(str(claim.get("attribute_claim_id")))

    for claim in relation_claims:
        subject_object_id = _entity_id(claim.get("subject_ref"), "stable_object")
        target_object_id = _entity_id(claim.get("object_ref"), "stable_object")
        summarized = _claim_summary(claim, claim_type="relation_claim")
        if claim.get("relation_type") == "identity.represents":
            source_id = _entity_id(claim.get("subject_ref"), "source_representation")
            if source_id:
                identity_claims_by_source[source_id].append(summarized)
        for object_id in {subject_object_id, target_object_id} - {None}:
            relations_by_object[object_id].append(summarized)
            phases_by_object[object_id].update(_claim_phase_refs(claim))
            source_refs_by_object[object_id].update(claim.get("source_representation_refs") or [])
            if claim.get("proof_status") in ATTENTION_PROOF_STATUSES:
                attention_by_object[object_id].append(str(claim.get("relation_claim_id")))

    objects: list[dict[str, Any]] = []
    for entry in stable_entries:
        stable = dict(entry.get("stable_object") or {})
        object_id = str(stable.get("stable_object_id") or entry.get("object_id") or "").strip()
        nomenclature = stable.get("nomenclature") if isinstance(stable.get("nomenclature"), dict) else {}
        source_refs = set(source_refs_by_object.get(object_id, set()))
        source_refs.update(mapped_representations_by_object.get(object_id, set()))
        objects.append(
            {
                "object_id": object_id,
                "object_family": stable.get("object_family"),
                "display_name": nomenclature.get("display_name") or nomenclature.get("internal_code") or object_id,
                "internal_code": nomenclature.get("internal_code"),
                "aliases": list(nomenclature.get("aliases") or []),
                "revision": entry.get("revision"),
                "attribute_claims": attributes_by_object.get(object_id, []),
                "relations": relations_by_object.get(object_id, []),
                "source_representation_refs": sorted(
                    ref for ref in source_refs if ref in representations_by_id
                ),
                "phase_refs": sorted(phases_by_object.get(object_id, set())),
                "attention_claim_refs": sorted(set(attention_by_object.get(object_id, []))),
            }
        )

    source_lens: list[dict[str, Any]] = []
    unmapped: list[dict[str, Any]] = []
    limited_source_count = 0
    for representation in representations:
        representation_id = str(representation.get("representation_id") or "").strip()
        limitations = list(representation.get("limitations") or [])
        if limitations:
            limited_source_count += 1
        item = {
            "representation_id": representation_id,
            "source_artifact_ref": representation.get("source_artifact_ref"),
            "source_version_ref": representation.get("source_version_ref"),
            "source_kind": representation.get("source_kind"),
            "observed_at": representation.get("observed_at"),
            "proof_status": representation.get("proof_status"),
            "binding_ref": representation.get("binding_ref"),
            "adapter_version": representation.get("adapter_version"),
            "identifiers": list(representation.get("identifiers") or []),
            "locators": list(representation.get("locators") or []),
            "limitations": limitations,
            "context": representation.get("context") or {},
            "attribute_claims": attributes_by_source.get(representation_id, []),
            "identity_claims": identity_claims_by_source.get(representation_id, []),
            "mapped_object_refs": sorted(mapped_objects_by_representation.get(representation_id, set())),
        }
        source_lens.append(item)
        if not item["mapped_object_refs"]:
            unmapped.append(item)

    attention_claims = [
        _claim_summary(claim, claim_type="attribute_claim")
        for claim in attribute_claims
        if claim.get("proof_status") in ATTENTION_PROOF_STATUSES
    ] + [
        _claim_summary(claim, claim_type="relation_claim")
        for claim in relation_claims
        if claim.get("proof_status") in ATTENTION_PROOF_STATUSES
    ]

    relation_edges = [
        _claim_summary(claim, claim_type="relation_claim")
        for claim in relation_claims
        if _entity_id(claim.get("subject_ref"), "stable_object")
        and _entity_id(claim.get("object_ref"), "stable_object")
    ]

    authority = dict(anatomy.get("authority") or {})
    authority.update(
        {
            "cockpit_projection_only": True,
            "authorization_inferred": False,
            "absence_inferred": False,
            "hierarchy_inferred_without_registered_semantics": False,
        }
    )

    return {
        "project_ref": anatomy.get("project_ref"),
        "model_version": anatomy.get("model_version"),
        "model_authority_ref": anatomy.get("model_authority_ref"),
        "model_doctrine_ref": model_doctrine_ref,
        "owner_revision": anatomy.get("owner_revision"),
        "summary": {
            "stable_object_count": len(objects),
            "source_representation_count": len(source_lens),
            "attribute_claim_count": len(attribute_claims),
            "relation_claim_count": len(relation_claims),
            "unmapped_source_representation_count": len(unmapped),
            "attention_claim_count": len(attention_claims),
            "limited_source_count": limited_source_count,
        },
        "structure": {
            "objects": objects,
            "object_family_counts": {
                family: sum(1 for item in objects if item.get("object_family") == family)
                for family in sorted({str(item.get("object_family")) for item in objects if item.get("object_family")})
            },
            "hierarchy": {
                "status": "not_derived",
                "reason": (
                    "The owner has no admitted hierarchy-relation registry; "
                    "generic relation claims are exposed without being reinterpreted as parentage."
                ),
            },
        },
        "relations": relation_edges,
        "attribute_claims": [
            _claim_summary(claim, claim_type="attribute_claim") for claim in attribute_claims
        ],
        "relation_claims": [
            _claim_summary(claim, claim_type="relation_claim") for claim in relation_claims
        ],
        "sources": source_lens,
        "uncertainty": {
            "attention_proof_statuses": sorted(ATTENTION_PROOF_STATUSES),
            "claims_requiring_attention": attention_claims,
            "certainty_is_reported_not_approved": True,
        },
        "unmapped_material": unmapped,
        "coverage": {
            "status": "not_persisted",
            "reason": (
                "Observation Bundle coverage is not persisted by the current executable APU owner."
            ),
            "absence_inference_allowed": False,
        },
        "authority": authority,
    }


def get_project_anatomy_projection(conn, *, project_id: str) -> dict[str, Any]:
    """Read the canonical owner and calculate the bounded Cockpit projection."""
    anatomy = apu_owner.get_project_anatomy(conn, project_id=project_id)
    return build_project_anatomy_projection(
        anatomy,
        model_doctrine_ref=anatomy.get("model_doctrine_ref"),
    )
