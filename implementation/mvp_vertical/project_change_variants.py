"""Human selection of immutable Project change variants.

Variants remain Execution Result candidates until a human selects one. Selection
records a review disposition and creates the existing Agency ChangeCandidate; it
does not mutate the Project, create a Decision, admit Evidence or authorize an
external effect.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row

from . import (
    agency_change_candidates,
    agency_data,
    agency_schema,
    execution_results,
    pantheon_contracts,
)


VARIANT_CONTRACT = "project_change_variant_candidate"
VARIANT_KIND = "project_change_variant"
VARIANT_SCHEMA_REF = "schemas/project_change_variant_candidate.schema.yaml"
SELECTION_DISPOSITION = "selected_for_change_candidate"


class ProjectChangeVariantError(ValueError):
    pass


class ProjectChangeVariantConflict(ProjectChangeVariantError):
    pass


def _jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _required_text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ProjectChangeVariantError(f"{field} is required")
    return text


def _selection_row_by_id(conn: psycopg.Connection, disposition_id: str | None) -> dict[str, Any]:
    """The selection disposition a stored ChangeCandidate already points at.

    Looked up by its id, not by an idempotency key. A replay reaches this
    through `_candidate_for_source`, which matches on `source_result_id`, so the
    replaying call need not carry the key the original selection was made under
    — and the candidate row already names the disposition.
    """
    if not disposition_id:
        raise ProjectChangeVariantError(
            "selected variant ChangeCandidate carries no selection disposition"
        )
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM execution_result_review_dispositions WHERE disposition_id = %s",
            (disposition_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise ProjectChangeVariantError("variant selection disposition was not retained")
    return _jsonable(dict(row))


def _candidate_for_source(conn: psycopg.Connection, result_id: str) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT candidate_id FROM agency_change_candidates WHERE source_result_id = %s",
            (result_id,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return agency_change_candidates._candidate_row(conn, row["candidate_id"])


def _candidate_for_scope(
    conn: psycopg.Connection,
    *,
    project_id: str,
    request_ref: str,
    scope_digest: str,
) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT candidate_id
              FROM agency_change_candidates
             WHERE entity_id = %s
               AND variant_request_ref = %s
               AND variant_scope_digest = %s
             FOR UPDATE
            """,
            (project_id, request_ref, scope_digest),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return agency_change_candidates._candidate_row(conn, row["candidate_id"])


def _source_refs(payload: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for raw in payload.get("basis_refs") or []:
        if not isinstance(raw, dict):
            continue
        entity_type = str(raw.get("entity_type") or "").strip()
        entity_id = str(raw.get("entity_id") or "").strip()
        if entity_type and entity_id:
            refs.append(f"{entity_type}:{entity_id}")
    return refs


def _validate_target_fields(payload: dict[str, Any]) -> dict[str, Any]:
    registry = agency_schema.get_project_registry()
    target_schema_id = _required_text(payload.get("target_schema_id"), "target_schema_id")
    if target_schema_id != registry.get("schema_id"):
        raise ProjectChangeVariantConflict(
            f"stale Project schema: expected {target_schema_id}, current {registry.get('schema_id')}"
        )

    proposed = payload.get("proposed_attributes")
    if not isinstance(proposed, dict) or not proposed:
        raise ProjectChangeVariantError("proposed_attributes must be a non-empty object")

    fields = {field["key"]: field for field in registry["fields"]}
    for key in proposed:
        field = fields.get(key)
        if field is None:
            raise ProjectChangeVariantError(f"Project field {key} is not editable")
        if field.get("semantics") == "claim" or field.get("storage") == "projection":
            raise ProjectChangeVariantError(
                f"Project field {key} is a ProjectClaim projection and is not editable here"
            )
        if (
            field.get("storage") != "attributes"
            or field.get("mutable") is not True
            or field.get("hermes_mode") != "candidate"
        ):
            raise ProjectChangeVariantError(f"Project field {key} is not editable here")

    try:
        return agency_schema.normalize_project_attributes(proposed)
    except agency_schema.AgencySchemaError as exc:
        raise ProjectChangeVariantError(str(exc)) from exc


def _validate_sibling_scope(
    conn: psycopg.Connection,
    *,
    execution_id: str,
    payload: dict[str, Any],
) -> None:
    request_ref = payload["request_ref"]
    scope_digest = payload["request_scope_digest"]
    expected = (
        payload["project_ref"],
        payload["base_revision"],
        payload["target_schema_id"],
    )
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT result_id, payload
              FROM execution_result_items
             WHERE execution_result_id = %s
               AND result_kind = 'project_change_variant'
             ORDER BY ordinal, result_id
            """,
            (execution_id,),
        )
        rows = cur.fetchall()

    matching = 0
    labels: set[str] = set()
    for row in rows:
        sibling = dict(row["payload"])
        if (
            sibling.get("request_ref") != request_ref
            or sibling.get("request_scope_digest") != scope_digest
        ):
            continue
        matching += 1
        found = (
            sibling.get("project_ref"),
            sibling.get("base_revision"),
            sibling.get("target_schema_id"),
        )
        if found != expected:
            raise ProjectChangeVariantConflict(
                "sibling variants do not share the same Project revision and target schema"
            )
        label = _required_text(sibling.get("variant_label"), "variant_label")
        if label in labels:
            raise ProjectChangeVariantConflict("sibling variants repeat a variant_label")
        labels.add(label)
    if matching < 1:
        raise ProjectChangeVariantError("variant request scope has no retained candidate")


def select_variant_for_change_candidate(
    conn: psycopg.Connection,
    *,
    execution_id: str,
    result_id: str,
    actor: str,
    idempotency_key: str,
) -> dict[str, Any]:
    execution_id = _required_text(execution_id, "execution_id")
    result_id = _required_text(result_id, "result_id")
    actor = _required_text(actor, "human actor")
    idempotency_key = _required_text(idempotency_key, "idempotency_key")
    if len(idempotency_key) < 8:
        raise ProjectChangeVariantError("idempotency_key must contain at least 8 characters")

    selection_key = f"{idempotency_key}:selection"
    candidate_key = f"{idempotency_key}:change-candidate"

    try:
        with conn.transaction():
            with conn.cursor(row_factory=dict_row) as cur:
                # All siblings of one execution share this lock, so two concurrent
                # selections cannot independently pass the scope check.
                cur.execute(
                    "SELECT * FROM execution_results WHERE execution_result_id = %s FOR UPDATE",
                    (execution_id,),
                )
                execution = cur.fetchone()
                if execution is None:
                    raise ProjectChangeVariantError(f"unknown execution result: {execution_id}")
                cur.execute(
                    """
                    SELECT * FROM execution_result_items
                     WHERE execution_result_id = %s AND result_id = %s
                    """,
                    (execution_id, result_id),
                )
                item = cur.fetchone()
            if item is None:
                raise ProjectChangeVariantError(
                    f"unknown result candidate {result_id} for execution {execution_id}"
                )
            if item["result_kind"] != VARIANT_KIND:
                raise ProjectChangeVariantError("result is not a project_change_variant")
            if item["schema_ref"] != VARIANT_SCHEMA_REF:
                raise ProjectChangeVariantError("variant uses a non-canonical schema_ref")

            payload = dict(item["payload"])
            try:
                pantheon_contracts.validate(VARIANT_CONTRACT, payload)
            except pantheon_contracts.ContractViolation as exc:
                raise ProjectChangeVariantError(str(exc)) from exc

            project_id = _required_text(payload.get("project_ref"), "project_ref")
            if execution.get("project_ref") != project_id:
                raise ProjectChangeVariantConflict(
                    "execution and variant refer to different Projects"
                )
            _validate_sibling_scope(conn, execution_id=execution_id, payload=payload)

            replayed = _candidate_for_source(conn, result_id)
            if replayed is not None:
                selection = _selection_row_by_id(
                    conn, replayed["source_review_disposition_id"]
                )
                return {
                    "selection": selection,
                    "change_candidate": replayed,
                    "project_mutated": False,
                    "decision_created": False,
                    "evidence_admitted": False,
                    "external_effect_authorized": False,
                }

            existing_scope = _candidate_for_scope(
                conn,
                project_id=project_id,
                request_ref=payload["request_ref"],
                scope_digest=payload["request_scope_digest"],
            )
            if existing_scope is not None:
                raise ProjectChangeVariantConflict(
                    "a sibling variant in this request scope is already selected"
                )

            current = agency_data.get_project(conn, project_id)
            if current["revision"] != payload["base_revision"]:
                raise ProjectChangeVariantConflict(
                    f"stale Project revision for variant: expected {payload['base_revision']}, "
                    f"current {current['revision']}"
                )
            proposed = _validate_target_fields(payload)

            reviewed = execution_results.append_review_disposition(
                conn,
                result_ref=result_id,
                disposition=SELECTION_DISPOSITION,
                reviewer=actor,
                reviewer_kind="human",
                note=f"Selected variant {payload['variant_label']} for ChangeCandidate review.",
                idempotency_key=selection_key,
            )
            selection = next(
                (
                    disposition
                    for disposition in reviewed["review_dispositions"]
                    if disposition["idempotency_key"] == selection_key
                ),
                None,
            )
            if selection is None:
                raise ProjectChangeVariantError("variant selection disposition was not retained")

            candidate = agency_change_candidates.create_project_candidate(
                conn,
                project_id=project_id,
                base_revision=payload["base_revision"],
                proposed_attributes=proposed,
                proposer=actor,
                proposer_kind="human",
                idempotency_key=candidate_key,
                reason=payload["rationale"],
                source_refs=_source_refs(payload),
                variant_provenance={
                    "source_execution_result_id": execution_id,
                    "source_result_id": result_id,
                    "source_review_disposition_id": selection["disposition_id"],
                    "variant_request_ref": payload["request_ref"],
                    "variant_scope_digest": payload["request_scope_digest"],
                    "variant_label": payload["variant_label"],
                    "variant_title": payload["variant_title"],
                },
            )
            return {
                "selection": selection,
                "change_candidate": candidate,
                "project_mutated": False,
                "decision_created": False,
                "evidence_admitted": False,
                "external_effect_authorized": False,
            }
    except agency_change_candidates.ChangeCandidateConflict as exc:
        raise ProjectChangeVariantConflict(str(exc)) from exc
    except agency_change_candidates.ChangeCandidateError as exc:
        raise ProjectChangeVariantError(str(exc)) from exc
    except psycopg.errors.UniqueViolation as exc:
        raise ProjectChangeVariantConflict(
            "a sibling variant in this request scope is already selected"
        ) from exc
