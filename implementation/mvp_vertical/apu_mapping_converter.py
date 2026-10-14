"""Deterministic conversion from reviewed fragment qualifications to APU mappings.

The converter prepares a new candidate result only. It does not create stable
objects, confirm identity, admit Evidence, promote memory or authorize effects.
"""

from __future__ import annotations

import hashlib
from typing import Any

from . import execution_results


SCHEMA_REF = "schemas/architecture-project-understanding/adapter_result.schema.yaml"
SEMANTIC_FIELDS = (
    "topic",
    "discipline",
    "representation_kind",
    "project_state",
    "variant_ref",
    "coverage_refs",
)
QUALIFICATION_KIND_TO_FAMILY = {
    "space": "spatial",
    "boundary": "element",
    "opening": "element",
    "path": "spatial",
    "level": "spatial",
    "grid": "datum",
    "vertical_connection": "spatial",
}


class MappingConversionError(execution_results.ExecutionResultError):
    pass


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:24]
    return f"{prefix}.{digest}"


def _latest_disposition(execution: dict[str, Any], result_ref: str) -> dict[str, Any] | None:
    matching = [
        event
        for event in execution.get("review_dispositions", [])
        if event.get("result_ref") == result_ref
    ]
    return matching[-1] if matching else None


def build_mapping_execution(
    source_execution: dict[str, Any],
    *,
    source_result_ref: str,
) -> dict[str, Any]:
    """Build a deterministic candidate execution from one accepted qualification."""
    header = source_execution.get("execution_result") or {}
    results = source_execution.get("results") or []
    source = next((item for item in results if item.get("result_id") == source_result_ref), None)
    if source is None:
        raise MappingConversionError("source result does not belong to execution result")
    if source.get("result_kind") != "fragment_qualification":
        raise MappingConversionError("source result must be fragment_qualification")

    disposition = _latest_disposition(source_execution, source_result_ref)
    if disposition is None or disposition.get("disposition") != "accepted_for_mapping":
        raise MappingConversionError("fragment qualification is not currently accepted_for_mapping")

    payload = source.get("payload")
    if not isinstance(payload, dict):
        raise MappingConversionError("fragment qualification payload must be an object")
    document_ref = str(payload.get("document_ref") or "").strip()
    structure_ref = str(payload.get("structure_ref") or "").strip()
    qualifications = payload.get("qualifications")
    if not document_ref or not structure_ref:
        raise MappingConversionError("fragment qualification requires document_ref and structure_ref")
    if not isinstance(qualifications, list) or not qualifications:
        raise MappingConversionError("fragment qualification requires non-empty qualifications")

    execution_id = str(header.get("execution_result_id") or "").strip()
    if not execution_id:
        raise MappingConversionError("source execution identity is missing")

    mappings: list[dict[str, Any]] = []
    clarification_requests: list[dict[str, Any]] = []
    seen_fragments: set[str] = set()
    for qualification in qualifications:
        if not isinstance(qualification, dict):
            raise MappingConversionError("every qualification must be an object")
        fragment_ref = str(qualification.get("fragment_ref") or "").strip()
        if not fragment_ref or fragment_ref in seen_fragments:
            raise MappingConversionError("qualification fragment_ref must be unique and non-empty")
        seen_fragments.add(fragment_ref)
        certainty = str(qualification.get("certainty") or "")
        if certainty not in {"E0", "E1", "E2", "E3", "E4"}:
            raise MappingConversionError("qualification certainty must use E0-E4")
        rationale = str(qualification.get("rationale") or "").strip()
        if not rationale:
            raise MappingConversionError("qualification rationale is required")

        coverage_refs = qualification.get("coverage_refs") or []
        if not isinstance(coverage_refs, list) or any(
            not isinstance(ref, str) or not ref.strip() for ref in coverage_refs
        ):
            raise MappingConversionError("coverage_refs must be an array of non-empty strings")
        coverage_refs = list(dict.fromkeys(ref.strip() for ref in coverage_refs))
        question = str(qualification.get("question") or "").strip()
        status = "candidate_matches" if coverage_refs else "unmatched"
        if question:
            status = "needs_clarification"

        mapping_id = _stable_id("mapping", execution_id, source_result_ref, fragment_ref)
        mapping: dict[str, Any] = {
            "mapping_id": mapping_id,
            "fragment_ref": fragment_ref,
            "candidate_object_ref": _stable_id(
                "candidate", execution_id, source_result_ref, fragment_ref
            ),
            "status": status,
            "certainty": certainty,
            "rationale": rationale,
            "qualification_snapshot": {
                key: qualification[key] for key in SEMANTIC_FIELDS if key in qualification
            },
            "match_candidates": [
                {
                    "stable_object_ref": ref,
                    "certainty": certainty,
                    "rationale": "Référence de couverture proposée par la qualification revue.",
                }
                for ref in coverage_refs
            ],
        }
        object_kind = qualification.get("object_kind")
        if object_kind in QUALIFICATION_KIND_TO_FAMILY:
            mapping["proposed_object_family"] = QUALIFICATION_KIND_TO_FAMILY[object_kind]
        if question:
            mapping["clarification_question"] = question
            clarification_requests.append(
                {
                    "clarification_id": _stable_id("clarification", mapping_id),
                    "related_result_refs": [
                        _stable_id("result.apu-mapping", execution_id, source_result_ref)
                    ],
                    "question": question,
                    "answer_kind": "free_text",
                    "options": [],
                    "rationale": "La qualification revue conserve une ambiguïté matérielle.",
                }
            )
        mappings.append(mapping)

    result_id = _stable_id("result.apu-mapping", execution_id, source_result_ref)
    for clarification in clarification_requests:
        clarification["related_result_refs"] = [result_id]

    authority = dict(execution_results.AUTHORITY)
    mapping_payload = {
        "mapping_set_id": _stable_id("mapping-set", execution_id, source_result_ref),
        "source_execution_result_ref": execution_id,
        "source_qualification_result_ref": source_result_ref,
        "project_ref": header.get("project_ref"),
        "document_ref": document_ref,
        "structure_ref": structure_ref,
        "mappings": mappings,
        "limitations": [
            "Le rapprochement reste candidat jusqu’à une revue humaine distincte."
        ],
        "authority": authority,
    }
    if mapping_payload["project_ref"] is None:
        mapping_payload.pop("project_ref")

    return {
        "execution_result_id": _stable_id("execution.apu-mapping", execution_id, source_result_ref),
        "task_contract_ref": str(header.get("task_contract_ref") or ""),
        "project_ref": header.get("project_ref"),
        "producer": {
            "capability": "apu-object-mapping-converter",
            "implementation": "pantheon-mvp",
            "version": "0.1.0",
        },
        "produced_at": disposition.get("occurred_at"),
        "evidence_pack_candidate_ref": header.get("evidence_pack_candidate_ref"),
        "authority": authority,
        "results": [
            {
                "result_id": result_id,
                "result_kind": "apu_object_mapping",
                "schema_ref": SCHEMA_REF,
                "payload": mapping_payload,
            }
        ],
        "clarification_requests": clarification_requests,
    }


def convert_and_store(
    conn,
    *,
    execution_result_id: str,
    source_result_ref: str,
    idempotency_key: str,
) -> dict[str, Any]:
    source = execution_results.get_execution_result(conn, execution_result_id)
    candidate = build_mapping_execution(source, source_result_ref=source_result_ref)
    return execution_results.store_execution_result(
        conn,
        execution_result=candidate,
        idempotency_key=idempotency_key,
    )
