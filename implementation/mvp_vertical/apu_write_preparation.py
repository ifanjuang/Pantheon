"""Prepare, authorize and apply one bounded APU match command.

The command remains an immutable candidate until a separate human authorization
exists. Application is server-side, one-shot and delegated to the project-scoped
APU owner. A V0.2 application records an exact source occurrence and proposed
identity relation; it does not create stable objects, admit Evidence or canonize
identity.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from . import apu_mapping_reviews, apu_owner, execution_results


MIGRATION = Path(__file__).resolve().parent / "sql" / "012_apu_write_preparation.sql"
APPLICATION_MIGRATION = (
    Path(__file__).resolve().parent / "sql" / "022_project_anatomy_match_application.sql"
)
COMMAND_AUTHORITY = {
    "is_fact": False,
    "is_evidence": False,
    "is_decision": False,
    "is_memory": False,
    "is_apu_write": False,
    "authorizes_external_effect": False,
}
AUTHORIZATION_ACTIONS = {"authorize_application", "reject_application"}


class ApuWritePreparationError(execution_results.ExecutionResultError):
    pass


class ApuWritePreparationNotFound(ApuWritePreparationError):
    pass


class ApuWriteApplicationConflict(execution_results.ExecutionResultConflict):
    pass


def _jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _digest(value: Any) -> str:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _required(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ApuWritePreparationError(f"{field} is required")
    return text


def _stable_id(prefix: str, *parts: str) -> str:
    return f"{prefix}.{hashlib.sha256(chr(31).join(parts).encode()).hexdigest()[:24]}"


def _document_fragment_source_representation(
    conn,
    *,
    project_ref: str,
    document_ref: str,
    structure_ref: str,
    fragment_ref: str,
    representation_id: str,
) -> dict[str, Any]:
    """Resolve one exact Document Structure fragment into a source record."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT d.parent_project_id,
                   d.media_type,
                   er.extraction_id,
                   er.source_digest,
                   sc.compiler,
                   sc.compiler_version,
                   sc.output_digest,
                   sc.created_at,
                   sc.quality_flags AS compilation_quality_flags,
                   eu.unit_id,
                   eu.content_type,
                   eu.text_digest,
                   eu.page_start,
                   eu.page_end,
                   eu.structural_locator,
                   eu.quality_flags AS fragment_quality_flags
              FROM source_documents d
              JOIN extraction_runs er
                ON er.document_id = d.document_id
              JOIN structured_compilations sc
                ON sc.extraction_id = er.extraction_id
              JOIN extraction_units eu
                ON eu.compilation_id = sc.compilation_id
               AND eu.extraction_id = sc.extraction_id
             WHERE d.document_id = %s
               AND sc.compilation_id = %s
               AND eu.unit_id = %s
            """,
            (document_ref, structure_ref, fragment_ref),
        )
        row = cur.fetchone()
    if row is None:
        raise ApuWritePreparationNotFound(
            "mapping source fragment is not present in the exact Document Structure"
        )
    row = dict(row)
    if row["parent_project_id"] != project_ref:
        raise ApuWritePreparationError(
            "mapping source Document Structure belongs to another Project"
        )

    locator: dict[str, Any] = {
        "type": "other",
        "value": _required(row.get("structural_locator"), "source structural locator"),
    }
    if row.get("page_start") is not None:
        locator["page"] = int(row["page_start"])
    if row.get("page_end") not in {None, row.get("page_start")}:
        locator["note"] = f"pages {row['page_start']}-{row['page_end']}"

    native_context = {
        "structure_ref": structure_ref,
        "fragment_ref": fragment_ref,
        "extraction_ref": row["extraction_id"],
        "content_type": row["content_type"],
    }
    if row.get("page_end") is not None:
        native_context["page_end"] = int(row["page_end"])

    quality_flags = [
        str(value).strip()
        for value in (
            list(row.get("compilation_quality_flags") or [])
            + list(row.get("fragment_quality_flags") or [])
        )
        if str(value).strip()
    ]
    limitations = [
        "Document Structure fragment candidate; stable project identity is not established."
    ]
    limitations.extend(f"Document Structure quality flag: {value}" for value in quality_flags)

    media_type = str(row.get("media_type") or "").lower()
    representation = {
        "representation_id": representation_id,
        "project_ref": project_ref,
        "source_artifact_ref": document_ref,
        "source_version_ref": f"sha256:{row['source_digest']}",
        "source_kind": "image" if media_type.startswith("image/") else "other",
        "identifiers": [
            {"scheme": "pantheon.document.fragment", "value": fragment_ref},
            {"scheme": "pantheon.document.structure", "value": structure_ref},
        ],
        "locators": [locator],
        "observed_at": _jsonable(row["created_at"]),
        "binding_ref": f"pantheon-mvp.document-structure:{row['compiler']}",
        "adapter_version": _required(row.get("compiler_version"), "compiler_version"),
        "freshness_token": f"sha256:{row['output_digest']}",
        "content_digest": f"sha256:{row['text_digest']}",
        "context": {
            "document_ref": document_ref,
            "native_context": native_context,
        },
        "proof_status": "candidate",
        "limitations": list(dict.fromkeys(limitations)),
    }
    if row.get("page_start") is not None:
        representation["context"]["page"] = int(row["page_start"])
    try:
        apu_owner._validate("source_representation", representation)
    except apu_owner.ApuOwnerError as exc:
        raise ApuWritePreparationError(str(exc)) from exc
    return representation


def _identity_relation_claim(
    *,
    command_id: str,
    source_execution_result_ref: str,
    source_mapping_result_ref: str,
    source_mapping_ref: str,
    source_review_ref: str,
    source_representation_ref: str,
    target_stable_object_ref: str,
    certainty: str | None,
    rationale: str,
) -> dict[str, Any]:
    derivation_refs = list(
        dict.fromkeys(
            [
                source_execution_result_ref,
                source_mapping_result_ref,
                source_mapping_ref,
                source_review_ref,
                command_id,
            ]
        )
    )
    claim: dict[str, Any] = {
        "relation_claim_id": _stable_id(
            "apu-relation-claim",
            command_id,
            source_representation_ref,
            target_stable_object_ref,
        ),
        "subject_ref": {
            "entity_type": "source_representation",
            "entity_id": source_representation_ref,
        },
        "relation_type": "identity.represents",
        "object_ref": {
            "entity_type": "stable_object",
            "entity_id": target_stable_object_ref,
        },
        "assertion_mode": "proposed",
        "source_authority": "model_interpretation_candidate",
        "proof_status": "candidate",
        "source_representation_refs": [source_representation_ref],
        "derivation_refs": derivation_refs,
        "notes": rationale,
    }
    if certainty:
        claim["certainty"] = certainty
    try:
        apu_owner._validate("relation_claim", claim)
    except apu_owner.ApuOwnerError as exc:
        raise ApuWritePreparationError(str(exc)) from exc
    return claim


def _mapping(
    execution: dict[str, Any], result_ref: str, mapping_ref: str
) -> tuple[dict[str, Any], dict[str, Any], str]:
    result = next(
        (item for item in execution.get("results", []) if item.get("result_id") == result_ref),
        None,
    )
    if result is None:
        raise ApuWritePreparationNotFound("unknown APU mapping result")
    payload = result.get("payload") or {}
    if result.get("result_kind") == "apu_object_mapping":
        mapping = next(
            (item for item in payload.get("mappings", []) if item.get("mapping_id") == mapping_ref),
            None,
        )
        if mapping is None:
            raise ApuWritePreparationNotFound("unknown APU mapping candidate")
        return payload, mapping, "apu_object_mapping"
    if result.get("result_kind") != "observation_bundle":
        raise ApuWritePreparationNotFound("unknown APU mapping result")
    relation = next(
        (
            item
            for item in payload.get("relation_claim_candidates", [])
            if item.get("relation_claim_id") == mapping_ref
        ),
        None,
    )
    if relation is None or relation.get("relation_type") != "identity.represents":
        raise ApuWritePreparationNotFound("unknown Observation Bundle identity candidate")
    if relation.get("assertion_mode") != "proposed" or relation.get("proof_status") != "candidate":
        raise ApuWritePreparationError(
            "Observation Bundle identity candidate must remain proposed and candidate"
        )
    subject_ref = relation.get("subject_ref") or {}
    object_ref = relation.get("object_ref") or {}
    if subject_ref.get("entity_type") != "source_representation":
        raise ApuWritePreparationError(
            "Observation Bundle identity candidate must start from a source representation"
        )
    if object_ref.get("entity_type") != "stable_object":
        raise ApuWritePreparationError(
            "Observation Bundle identity candidate must target a stable object"
        )
    representation_id = _required(subject_ref.get("entity_id"), "identity subject representation")
    representation = next(
        (
            item
            for item in payload.get("source_representations", [])
            if item.get("representation_id") == representation_id
        ),
        None,
    )
    if representation is None:
        raise ApuWritePreparationNotFound(
            "Observation Bundle identity candidate references an unknown source representation"
        )
    if representation.get("proof_status") != "candidate":
        raise ApuWritePreparationError(
            "Observation Bundle source representation must remain candidate"
        )
    mapping = {
        "mapping_id": relation["relation_claim_id"],
        "candidate_object_ref": representation_id,
        "certainty": relation.get("certainty"),
        "rationale": relation.get("notes") or "Observation Bundle identity candidate.",
        "match_candidates": [
            {
                "stable_object_ref": _required(object_ref.get("entity_id"), "identity target object"),
                "certainty": relation.get("certainty"),
                "rationale": relation.get("notes") or "Observation Bundle identity candidate.",
            }
        ],
        "source_representation": representation,
        "identity_relation_claim": relation,
    }
    return payload, mapping, "observation_bundle"


def _latest_selected_review(
    conn,
    *,
    execution_result_id: str,
    result_ref: str,
    mapping_ref: str,
) -> dict[str, Any]:
    reviews = apu_mapping_reviews.list_mapping_reviews(
        conn,
        execution_result_id=execution_result_id,
        result_ref=result_ref,
        mapping_ref=mapping_ref,
    )
    if not reviews or reviews[-1].get("action") != "select_existing_object":
        raise ApuWritePreparationError("latest mapping review must select_existing_object")
    return reviews[-1]


def _validate_command_payload(command: dict[str, Any]) -> None:
    supplied_digest = _required(command.get("payload_digest"), "command.payload_digest")
    digest_input = dict(command)
    digest_input.pop("payload_digest", None)
    if _digest(digest_input) != supplied_digest:
        raise ApuWriteApplicationConflict("APU write command payload digest is stale or corrupted")
    try:
        apu_owner._validate("write_command_candidate", command)
    except apu_owner.ApuOwnerError as exc:
        raise ApuWritePreparationError(str(exc)) from exc
    representation = command["source_representation"]
    relation = command["identity_relation_claim"]
    representation_id = _required(
        representation.get("representation_id"),
        "source_representation.representation_id",
    )
    if representation.get("project_ref") != command.get("project_ref"):
        raise ApuWritePreparationError(
            "source representation must carry the exact Project"
        )
    if relation.get("subject_ref") != {
        "entity_type": "source_representation",
        "entity_id": representation_id,
    }:
        raise ApuWritePreparationError(
            "identity relation must start from the exact source representation"
        )
    object_ref = relation.get("object_ref") or {}
    if object_ref.get("entity_type") != "stable_object" or not str(
        object_ref.get("entity_id") or ""
    ).strip():
        raise ApuWritePreparationError(
            "identity relation must target one exact stable object"
        )
    if relation.get("source_representation_refs") != [representation_id]:
        raise ApuWritePreparationError(
            "identity relation must retain its exact source representation"
        )
    if command.get("certainty") and relation.get("certainty") != command.get("certainty"):
        raise ApuWritePreparationError(
            "identity relation certainty must equal the reviewed mapping"
        )


def prepare_write_command(
    conn,
    *,
    execution_result_id: str,
    result_ref: str,
    mapping_ref: str,
    prepared_by: str,
    idempotency_key: str,
) -> dict[str, Any]:
    key = _required(idempotency_key, "idempotency_key")
    actor = _required(prepared_by, "prepared_by")
    execution = execution_results.get_execution_result(conn, execution_result_id)
    payload, mapping, mapping_kind = _mapping(execution, result_ref, mapping_ref)
    project_ref = _required(payload.get("project_ref"), "mapping.project_ref")
    review = _latest_selected_review(
        conn,
        execution_result_id=execution_result_id,
        result_ref=result_ref,
        mapping_ref=mapping_ref,
    )
    target = _required(review.get("selected_stable_object_ref"), "selected_stable_object_ref")
    candidates = {item.get("stable_object_ref") for item in mapping.get("match_candidates", [])}
    if target not in candidates:
        raise ApuWritePreparationError("selected object is no longer present in mapping candidates")
    try:
        owner = apu_owner.get_project_anatomy(conn, project_id=project_ref)
        target_object = apu_owner.get_apu_object(
            conn,
            project_id=project_ref,
            object_id=target,
        )
    except apu_owner.ApuOwnerNotFound as exc:
        raise ApuWritePreparationNotFound(str(exc)) from exc
    if target_object.get("retired_at") is not None:
        raise ApuWritePreparationError("selected APU object is retired")
    command_id = _stable_id(
        "apu-write-command",
        execution_result_id,
        result_ref,
        mapping_ref,
        review["review_id"],
    )
    source_candidate_ref = _required(
        mapping.get("candidate_object_ref"), "candidate_object_ref"
    )
    command_payload = {
        "command_id": command_id,
        "operation": "add_match_to_existing_object",
        "project_ref": project_ref,
        "source_execution_result_ref": execution_result_id,
        "source_mapping_result_ref": result_ref,
        "source_mapping_ref": mapping_ref,
        "source_review_ref": review["review_id"],
        "certainty": mapping.get("certainty"),
        "expected_owner_revision": owner["owner_revision"],
        "expected_object_revision": target_object["revision"],
        "rationale": _required(mapping.get("rationale"), "mapping.rationale"),
        "prepared_by": actor,
        "limitations": [
            "Une autorisation humaine distincte est requise avant toute application.",
            "L'application doit refuser une révision APU ou objet devenue obsolète.",
        ],
        "authority": dict(COMMAND_AUTHORITY),
    }
    if mapping_kind == "observation_bundle":
        representation = dict(mapping["source_representation"])
        relation = dict(mapping["identity_relation_claim"])
        if representation.get("project_ref") != project_ref:
            raise ApuWritePreparationError(
                "Observation Bundle source representation belongs to another Project"
            )
        if relation.get("object_ref") != {
            "entity_type": "stable_object",
            "entity_id": target,
        }:
            raise ApuWritePreparationError(
                "reviewed identity target differs from Observation Bundle candidate"
            )
        command_payload["source_representation"] = representation
        command_payload["identity_relation_claim"] = relation
        command_payload["limitations"].append(
            "La représentation et la relation appliquées proviennent exactement du Observation Bundle revu."
        )
    else:
        representation = _document_fragment_source_representation(
            conn,
            project_ref=project_ref,
            document_ref=_required(payload.get("document_ref"), "mapping.document_ref"),
            structure_ref=_required(payload.get("structure_ref"), "mapping.structure_ref"),
            fragment_ref=_required(mapping.get("fragment_ref"), "mapping.fragment_ref"),
            representation_id=source_candidate_ref,
        )
        command_payload["source_representation"] = representation
        command_payload["identity_relation_claim"] = _identity_relation_claim(
            command_id=command_id,
            source_execution_result_ref=execution_result_id,
            source_mapping_result_ref=result_ref,
            source_mapping_ref=mapping_ref,
            source_review_ref=review["review_id"],
            source_representation_ref=representation["representation_id"],
            target_stable_object_ref=target,
            certainty=mapping.get("certainty"),
            rationale=_required(mapping.get("rationale"), "mapping.rationale"),
        )
    command_payload["limitations"].append(
        "La relation appliquée reste candidate et ne valide pas professionnellement l'identité."
    )
    command_payload = {k: v for k, v in command_payload.items() if v is not None}
    digest = _digest(command_payload)
    command_payload["payload_digest"] = digest
    _validate_command_payload(command_payload)

    with conn.transaction():
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM apu_write_command_candidates WHERE idempotency_key = %s",
                (key,),
            )
            replay = cur.fetchone()
            if replay is not None:
                if replay["payload_digest"] != digest:
                    raise execution_results.ExecutionResultConflict(
                        "write-command idempotency key belongs to different content"
                    )
                return _jsonable(dict(replay)) | {
                    "command": _jsonable(replay["command_payload"]),
                    "authority": dict(COMMAND_AUTHORITY),
                }
        conn.execute(
            """INSERT INTO apu_write_command_candidates (
                command_id, execution_result_id, result_ref, mapping_ref, source_review_ref,
                operation, project_ref, target_stable_object_ref, source_candidate_ref,
                source_artifact_ref, certainty, rationale, command_payload, payload_digest,
                expected_owner_revision, expected_object_revision,
                prepared_by, idempotency_key
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                command_id,
                execution_result_id,
                result_ref,
                mapping_ref,
                review["review_id"],
                command_payload["operation"],
                project_ref,
                target,
                source_candidate_ref,
                command_payload["source_representation"].get("source_artifact_ref"),
                command_payload.get("certainty"),
                command_payload["rationale"],
                Jsonb(command_payload),
                digest,
                owner["owner_revision"],
                target_object["revision"],
                actor,
                key,
            ),
        )
    return get_write_command(conn, command_id)


def get_write_command(conn, command_id: str) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM apu_write_command_candidates WHERE command_id = %s",
            (command_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise ApuWritePreparationNotFound(f"unknown APU write command: {command_id}")
    return _jsonable(dict(row)) | {
        "command": _jsonable(row["command_payload"]),
        "authority": dict(COMMAND_AUTHORITY),
    }


def _lock_write_command(conn, command_id: str) -> None:
    """Take the command row as the mutex for the authorize/apply race.

    The row is append-only — the trigger in `012_apu_write_preparation.sql`
    refuses UPDATE and DELETE on it — so this never changes it. `FOR UPDATE` is
    used only to give the authorization writer and the applying reader one row
    to serialise on. Both must take it: locking a row one side never touches
    orders nothing, and the authorization events themselves cannot serve as the
    lock because the rejection that has to be seen is a row that does not exist
    yet when the applying side reads.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT command_id FROM apu_write_command_candidates"
            " WHERE command_id = %s FOR UPDATE",
            (command_id,),
        )
        if cur.fetchone() is None:
            raise ApuWritePreparationNotFound(f"unknown APU write command: {command_id}")


def append_authorization(
    conn,
    *,
    command_id: str,
    action: str,
    note: str | None,
    authorized_by: str,
    idempotency_key: str,
) -> dict[str, Any]:
    if action not in AUTHORIZATION_ACTIONS:
        raise ApuWritePreparationError("unsupported authorization action")
    key = _required(idempotency_key, "idempotency_key")
    actor = _required(authorized_by, "authorized_by")
    command = get_write_command(conn, command_id)
    _validate_command_payload(command["command"])
    digest = command["payload_digest"]
    payload = {
        "command_ref": command_id,
        "command_payload_digest": digest,
        "action": action,
        "note": (note or "").strip() or None,
        "authorized_by": actor,
    }
    payload_digest = _digest(payload)
    with conn.transaction():
        # The applying side takes this same row lock and re-reads the events
        # under it, so a rejection appended here either lands before that read
        # or waits for the apply to finish. Without both halves the apply can
        # still act on an authorization a committed rejection has superseded.
        _lock_write_command(conn, command_id)
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM apu_write_authorization_events WHERE idempotency_key = %s",
                (key,),
            )
            replay = cur.fetchone()
            if replay is not None:
                if replay["payload_digest"] != payload_digest:
                    raise execution_results.ExecutionResultConflict(
                        "write-authorization idempotency key belongs to different content"
                    )
                return _jsonable(dict(replay)) | {
                    "authority": _authorization_authority(replay["action"])
                }
        authorization_id = _stable_id("apu-write-authorization", command_id, key)
        conn.execute(
            """INSERT INTO apu_write_authorization_events (
                authorization_id, command_ref, command_payload_digest, action, note,
                authorized_by, idempotency_key, payload_digest
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                authorization_id,
                command_id,
                digest,
                action,
                payload["note"],
                actor,
                key,
                payload_digest,
            ),
        )
    return get_authorization(conn, authorization_id)


def _authorization_authority(action: str) -> dict[str, bool]:
    return {
        "authorizes_command_application": action == "authorize_application",
        "applies_command": False,
        "confirms_stable_identity": False,
        "admits_evidence": False,
        "promotes_memory": False,
    }


def get_authorization(conn, authorization_id: str) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM apu_write_authorization_events WHERE authorization_id = %s",
            (authorization_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise ApuWritePreparationNotFound(
            f"unknown APU write authorization: {authorization_id}"
        )
    return _jsonable(dict(row)) | {"authority": _authorization_authority(row["action"])}


def list_authorizations(conn, command_id: str) -> list[dict[str, Any]]:
    get_write_command(conn, command_id)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM apu_write_authorization_events WHERE command_ref = %s "
            "ORDER BY authorized_at, authorization_id",
            (command_id,),
        )
        rows = cur.fetchall()
    return [
        _jsonable(dict(row)) | {"authority": _authorization_authority(row["action"])}
        for row in rows
    ]


def _latest_application_authorization(conn, command: dict[str, Any]) -> dict[str, Any]:
    items = list_authorizations(conn, command["command_id"])
    if not items or items[-1]["action"] != "authorize_application":
        raise ApuWritePreparationError(
            "latest write authorization must authorize_application"
        )
    authorization = items[-1]
    if authorization["command_payload_digest"] != command["payload_digest"]:
        raise ApuWriteApplicationConflict(
            "latest authorization does not cover the exact command payload digest"
        )
    return authorization


def apply_authorized_write_command(
    conn,
    *,
    command_id: str,
    applied_by: str,
    idempotency_key: str,
) -> dict[str, Any]:
    """Verify the reviewed chain, then delegate the bounded mutation to APU owner."""
    actor = _required(applied_by, "applied_by")
    key = _required(idempotency_key, "idempotency_key")
    # The rejection race the review recorded: this chain used to read the
    # authorization events outside the transaction that applies, so a
    # reject_application committing between the read and the write did not
    # block the apply. Everything the decision rests on is now read under the
    # command-row lock that `append_authorization` also takes.
    with conn.transaction():
        _lock_write_command(conn, command_id)
        command_row = get_write_command(conn, command_id)
        command = dict(command_row["command"])
        _validate_command_payload(command)
        representation = command["source_representation"]
        relation = command["identity_relation_claim"]
        source_candidate_ref = representation["representation_id"]
        source_artifact_ref = representation["source_artifact_ref"]
        target_stable_object_ref = relation["object_ref"]["entity_id"]
        if (
            command_row.get("source_candidate_ref") != source_candidate_ref
            or command_row.get("source_artifact_ref") != source_artifact_ref
            or command_row.get("target_stable_object_ref") != target_stable_object_ref
        ):
            raise ApuWriteApplicationConflict(
                "stored command indexes differ from its exact embedded effect"
            )
        if command_row.get("expected_owner_revision") is None or command_row.get(
            "expected_object_revision"
        ) is None:
            raise ApuWriteApplicationConflict(
                "APU write command has no truthful target freshness and cannot be applied"
            )
        if (
            command_row["expected_owner_revision"] != command["expected_owner_revision"]
            or command_row["expected_object_revision"] != command["expected_object_revision"]
        ):
            raise ApuWriteApplicationConflict(
                "stored APU write command revisions differ from its immutable payload"
            )

        execution = execution_results.get_execution_result(
            conn, command["source_execution_result_ref"]
        )
        payload, mapping, _mapping_kind = _mapping(
            execution,
            command["source_mapping_result_ref"],
            command["source_mapping_ref"],
        )
        if payload.get("project_ref") != command["project_ref"]:
            raise ApuWriteApplicationConflict(
                "source mapping Project differs from the authorized command"
            )
        if mapping.get("candidate_object_ref") != source_candidate_ref:
            raise ApuWriteApplicationConflict(
                "source mapping candidate differs from the authorized command"
            )
        candidates = {item.get("stable_object_ref") for item in mapping.get("match_candidates", [])}
        if target_stable_object_ref not in candidates:
            raise ApuWriteApplicationConflict(
                "authorized target is no longer a member of the source mapping candidates"
            )
        if _mapping_kind == "observation_bundle":
            if mapping.get("source_representation") != representation:
                raise ApuWriteApplicationConflict(
                    "Observation Bundle source representation changed after command preparation"
                )
            if mapping.get("identity_relation_claim") != relation:
                raise ApuWriteApplicationConflict(
                    "Observation Bundle identity relation changed after command preparation"
                )
        review = _latest_selected_review(
            conn,
            execution_result_id=command["source_execution_result_ref"],
            result_ref=command["source_mapping_result_ref"],
            mapping_ref=command["source_mapping_ref"],
        )
        if review["review_id"] != command["source_review_ref"]:
            raise ApuWriteApplicationConflict(
                "a newer mapping review supersedes the authorized command"
            )
        if review.get("selected_stable_object_ref") != target_stable_object_ref:
            raise ApuWriteApplicationConflict(
                "latest mapping review selects another stable object"
            )
        authorization = _latest_application_authorization(conn, command)

        try:
            return apu_owner.apply_source_match(
                conn,
                command=command,
                authorization_id=authorization["authorization_id"],
                actor=actor,
                idempotency_key=key,
            )
        except apu_owner.ApuOwnerNotFound as exc:
            raise ApuWritePreparationNotFound(str(exc)) from exc
        except apu_owner.ApuOwnerConflict as exc:
            raise ApuWriteApplicationConflict(str(exc)) from exc
        except apu_owner.ApuOwnerError as exc:
            raise ApuWritePreparationError(str(exc)) from exc
