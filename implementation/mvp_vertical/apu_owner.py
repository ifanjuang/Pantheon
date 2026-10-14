"""Project-scoped executable owner for the sole Project Anatomy baseline.

The owner persists reviewed V0.2 stable objects, source representations and
claims. It never creates stable identity automatically, admits Evidence,
canonizes claims, resolves Decisions or authorizes tasks.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any

import jsonschema
import psycopg
import yaml
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from . import pantheon_contracts
from .policy_gate import OBJECT_IDENTITY_KEY, PolicyClient, enforce_consequential


MIGRATION = Path(__file__).resolve().parent / "sql" / "021_project_anatomy_owner.sql"
MODEL_AUTHORITY_REF = "ifanjuang/Pantheon-Next@7cef8075525e016b7554b29bf0ed2c1cf673e855"
MODEL_DOCTRINE_REF = (
    MODEL_AUTHORITY_REF
    + "#docs/domain-packs/architecture/PROJECT_ANATOMY_MODEL.md"
)
SUPPORTED_OWNER_ENTITY_TYPES = {"stable_object", "source_representation"}

AUTHORITY = {
    "is_projection": True,
    "is_evidence": False,
    "is_decision": False,
    "is_memory": False,
    "canonizes_claims": False,
    "authorizes_tasks": False,
    "permits_runtime_writes": False,
}
APPLICATION_AUTHORITY = {
    "match_recorded": True,
    "stable_identity_professionally_validated": False,
    "is_evidence": False,
    "is_decision": False,
    "is_memory": False,
    "canonizes_claims": False,
    "closes_work_issue": False,
    "resolves_decision_request": False,
    "authorizes_external_effect": False,
}


class ApuOwnerError(ValueError):
    pass


class ApuOwnerNotFound(ApuOwnerError):
    pass


class ApuOwnerConflict(ApuOwnerError):
    pass


class ApuOwnerRefused(ApuOwnerError):
    """The chokepoint refused this write."""


class ApuOwnerPolicyUnavailable(ApuOwnerError):
    """The decision point could not be reached; the write fails closed."""


@lru_cache(maxsize=1)
def _registry() -> Registry:
    resources: list[tuple[str, Resource]] = []
    for uri, contract_name in (
        ("shared.schema.yaml", "apu_shared"),
        ("source_representation.schema.yaml", "apu_source_representation"),
        ("attribute_claim.schema.yaml", "apu_attribute_claim"),
        ("relation_claim.schema.yaml", "apu_relation_claim"),
    ):
        schema = pantheon_contracts.load_schema(contract_name)
        resources.append(
            (uri, Resource.from_contents(schema, default_specification=DRAFT202012))
        )
    return Registry().with_resources(resources)


@lru_cache(maxsize=None)
def _validator(name: str) -> jsonschema.Draft202012Validator:
    contract_name = f"apu_{name}"
    try:
        schema = pantheon_contracts.load_schema(contract_name)
    except pantheon_contracts.ContractUnavailable as exc:
        raise ApuOwnerError(f"unable to load governed APU schema: {name}") from exc
    if not isinstance(schema, dict):
        raise ApuOwnerError(f"governed APU schema must be an object: {name}")
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
        registry=_registry(),
    )


def _validate(name: str, payload: dict[str, Any]) -> None:
    errors = sorted(
        _validator(name).iter_errors(payload),
        key=lambda error: (
            tuple(str(part) for part in error.absolute_path),
            error.message,
        ),
    )
    if errors:
        rendered = "; ".join(
            f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
            for error in errors
        )
        raise ApuOwnerError(f"{name} violates its governed contract: {rendered}")


def ensure_schema(conn: psycopg.Connection) -> None:
    conn.execute(MIGRATION.read_text(encoding="utf-8"))
    conn.commit()


def _required(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ApuOwnerError(f"{field} is required")
    return text


def _digest(value: Any) -> str:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _project_exists(conn: psycopg.Connection, project_id: str) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM agency_projects WHERE project_id = %s", (project_id,))
        return cur.fetchone() is not None


def _project_state(
    conn: psycopg.Connection,
    project_id: str,
    *,
    lock: bool = False,
) -> dict[str, Any] | None:
    suffix = " FOR UPDATE" if lock else ""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM agency_apu_project_state WHERE project_id = %s" + suffix,
            (project_id,),
        )
        row = cur.fetchone()
    return dict(row) if row is not None else None


def _check_entity_ref(
    ref: Any,
    label: str,
    *,
    object_ids: set[str],
    representation_ids: set[str],
) -> None:
    if not isinstance(ref, dict):
        raise ApuOwnerError(f"{label} must be an APU entity ref")
    entity_type = _required(ref.get("entity_type"), f"{label}.entity_type")
    entity_id = _required(ref.get("entity_id"), f"{label}.entity_id")
    if entity_type not in SUPPORTED_OWNER_ENTITY_TYPES:
        raise ApuOwnerError(f"the executable owner does not persist {entity_type} entities")
    if entity_type == "stable_object" and entity_id not in object_ids:
        raise ApuOwnerError(f"{label} references an unknown stable object")
    if entity_type == "source_representation" and entity_id not in representation_ids:
        raise ApuOwnerError(f"{label} references an unknown source representation")


def _normalize_dossier(
    *,
    project_id: str,
    stable_objects: list[dict[str, Any]],
    source_representations: list[dict[str, Any]],
    attribute_claims: list[dict[str, Any]],
    relation_claims: list[dict[str, Any]],
    review_ref: str,
) -> dict[str, Any]:
    if not isinstance(stable_objects, list) or not stable_objects:
        raise ApuOwnerError("stable_objects must be a non-empty array")
    for name, value in (
        ("source_representations", source_representations),
        ("attribute_claims", attribute_claims),
        ("relation_claims", relation_claims),
    ):
        if not isinstance(value, list):
            raise ApuOwnerError(f"{name} must be an array")

    object_ids: set[str] = set()
    representation_ids: set[str] = set()
    attribute_ids: set[str] = set()
    relation_ids: set[str] = set()

    normalized_objects: list[dict[str, Any]] = []
    for item in stable_objects:
        if not isinstance(item, dict):
            raise ApuOwnerError("every stable object must be an object")
        _validate("stable_object", item)
        object_id = _required(item.get("stable_object_id"), "stable_object_id")
        if item.get("project_ref") != project_id:
            raise ApuOwnerError(f"stable object {object_id} must carry the exact Project")
        if object_id in object_ids:
            raise ApuOwnerError(f"duplicate stable_object_id: {object_id}")
        object_ids.add(object_id)
        normalized_objects.append(dict(item))

    normalized_representations: list[dict[str, Any]] = []
    for item in source_representations:
        if not isinstance(item, dict):
            raise ApuOwnerError("every source representation must be an object")
        _validate("source_representation", item)
        representation_id = _required(item.get("representation_id"), "representation_id")
        if item.get("project_ref") != project_id:
            raise ApuOwnerError(
                f"source representation {representation_id} must carry the exact Project"
            )
        if representation_id in representation_ids:
            raise ApuOwnerError(f"duplicate source representation id: {representation_id}")
        representation_ids.add(representation_id)
        normalized_representations.append(dict(item))

    normalized_attributes: list[dict[str, Any]] = []
    for item in attribute_claims:
        if not isinstance(item, dict):
            raise ApuOwnerError("every attribute claim must be an object")
        _validate("attribute_claim", item)
        claim_id = _required(item.get("attribute_claim_id"), "attribute_claim_id")
        if claim_id in attribute_ids:
            raise ApuOwnerError(f"duplicate attribute claim id: {claim_id}")
        attribute_ids.add(claim_id)
        _check_entity_ref(
            item.get("subject_ref"),
            "attribute_claim.subject_ref",
            object_ids=object_ids,
            representation_ids=representation_ids,
        )
        for representation_id in item.get("source_representation_refs") or []:
            if representation_id not in representation_ids:
                raise ApuOwnerError(
                    "attribute_claim source_representation_ref is outside the reviewed dossier"
                )
        normalized_attributes.append(dict(item))

    normalized_relations: list[dict[str, Any]] = []
    for item in relation_claims:
        if not isinstance(item, dict):
            raise ApuOwnerError("every relation claim must be an object")
        _validate("relation_claim", item)
        claim_id = _required(item.get("relation_claim_id"), "relation_claim_id")
        if claim_id in relation_ids:
            raise ApuOwnerError(f"duplicate relation claim id: {claim_id}")
        relation_ids.add(claim_id)
        _check_entity_ref(
            item.get("subject_ref"),
            "relation_claim.subject_ref",
            object_ids=object_ids,
            representation_ids=representation_ids,
        )
        _check_entity_ref(
            item.get("object_ref"),
            "relation_claim.object_ref",
            object_ids=object_ids,
            representation_ids=representation_ids,
        )
        for representation_id in item.get("source_representation_refs") or []:
            if representation_id not in representation_ids:
                raise ApuOwnerError(
                    "relation_claim source_representation_ref is outside the reviewed dossier"
                )
        normalized_relations.append(dict(item))

    normalized_objects.sort(key=lambda item: item["stable_object_id"])
    normalized_representations.sort(key=lambda item: item["representation_id"])
    normalized_attributes.sort(key=lambda item: item["attribute_claim_id"])
    normalized_relations.sort(key=lambda item: item["relation_claim_id"])
    return {
        "project_ref": project_id,
        "review_ref": review_ref,
        "stable_objects": normalized_objects,
        "source_representations": normalized_representations,
        "attribute_claims": normalized_attributes,
        "relation_claims": normalized_relations,
    }


def _insert_dossier(conn, dossier: dict[str, Any], *, actor: str) -> None:
    for stable in dossier["stable_objects"]:
        conn.execute(
            """
            INSERT INTO agency_apu_objects (
                object_id, project_id, object_family, stable_object_payload,
                payload_digest, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                stable["stable_object_id"],
                stable["project_ref"],
                stable["object_family"],
                Jsonb(stable),
                _digest(stable),
                actor,
            ),
        )
    for representation in dossier["source_representations"]:
        conn.execute(
            """
            INSERT INTO agency_apu_source_representations (
                representation_id, project_id, source_kind, proof_status,
                representation_payload, payload_digest, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                representation["representation_id"],
                representation["project_ref"],
                representation["source_kind"],
                representation["proof_status"],
                Jsonb(representation),
                _digest(representation),
                actor,
            ),
        )
    for claim in dossier["attribute_claims"]:
        subject = claim["subject_ref"]
        conn.execute(
            """
            INSERT INTO agency_apu_attribute_claims (
                claim_id, project_id, subject_entity_type, subject_entity_id,
                attribute_key, assertion_mode, source_authority, proof_status,
                claim_payload, payload_digest, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                claim["attribute_claim_id"], dossier["project_ref"],
                subject["entity_type"], subject["entity_id"], claim["attribute_key"],
                claim["assertion_mode"], claim["source_authority"], claim["proof_status"],
                Jsonb(claim), _digest(claim), actor,
            ),
        )
    for claim in dossier["relation_claims"]:
        subject = claim["subject_ref"]
        target = claim["object_ref"]
        conn.execute(
            """
            INSERT INTO agency_apu_relation_claims (
                claim_id, project_id, subject_entity_type, subject_entity_id,
                relation_type, object_entity_type, object_entity_id,
                assertion_mode, source_authority, proof_status,
                claim_payload, payload_digest, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                claim["relation_claim_id"], dossier["project_ref"],
                subject["entity_type"], subject["entity_id"], claim["relation_type"],
                target["entity_type"], target["entity_id"], claim["assertion_mode"],
                claim["source_authority"], claim["proof_status"], Jsonb(claim),
                _digest(claim), actor,
            ),
        )


def store_reviewed_dossier(
    conn: psycopg.Connection,
    *,
    project_id: str,
    stable_objects: list[dict[str, Any]],
    source_representations: list[dict[str, Any]],
    attribute_claims: list[dict[str, Any]],
    relation_claims: list[dict[str, Any]],
    review_ref: str,
    actor: str,
    idempotency_key: str,
    policy_client: PolicyClient | None = None,
    decision_payload: dict[str, Any] | None = None,
    required_ceiling: str = "C3",
) -> dict[str, Any]:
    """Install one reviewed canonical dossier; this is not a create-object API.

    `review_ref` is a caller-supplied string. Nothing in this module looks it
    up, verifies a signature against it, or checks it against a table of
    completed reviews, because no such table exists here — a provided
    reference is not a validated decision, the distinction this repository
    draws everywhere else. When `policy_client` is supplied, the chokepoint
    stands in for that missing verification: `payload_digest` is computed
    over `_normalize_dossier`'s output, which folds `review_ref` in beside
    the stable objects, representations and claims, so the decision covers
    this exact `review_ref` bundled with this exact dossier as one unit — a
    caller cannot swap either half after the decision without changing the
    digest the gate checks against. That still does not verify `review_ref`
    names a review that actually happened; it only prevents a decision taken
    over one dossier/review_ref pair from being replayed against a different
    one.
    """
    project_id = _required(project_id, "project_id")
    review_ref = _required(review_ref, "review_ref")
    actor = _required(actor, "actor")
    key = _required(idempotency_key, "idempotency_key")
    dossier = _normalize_dossier(
        project_id=project_id,
        stable_objects=stable_objects,
        source_representations=source_representations,
        attribute_claims=attribute_claims,
        relation_claims=relation_claims,
        review_ref=review_ref,
    )
    payload_digest = _digest(dossier)

    if policy_client is not None:
        scope = {"scope_type": "project", "scope_id": project_id}
        dossier_object_ref = f"apu_reviewed_dossier:{project_id}"
        expectation = {
            "required_ceiling": required_ceiling,
            "required_scope": scope,
            OBJECT_IDENTITY_KEY: dossier_object_ref,
            "expected_digest": payload_digest,
        }
        candidate = {
            "intent": "store_reviewed_dossier",
            "decision_expectation": expectation,
            "request": {
                "intent": "store_reviewed_dossier",
                "external_effect": False,
                "writes_state": True,
                "transmission_requested": False,
                "memory_promotion_requested": False,
                "professional_position": False,
                "financial_or_contractual_effect": False,
                "scope": scope,
            },
        }
        verdict = enforce_consequential(
            policy_client,
            candidate=candidate,
            decision_payload=dict(decision_payload or {}),
        )
        if not verdict.allowed:
            message = (
                "policy chokepoint blocked the reviewed-dossier import "
                f"({verdict.disposition}): {verdict.reasons}"
            )
            if verdict.disposition == "policy_unavailable":
                raise ApuOwnerPolicyUnavailable(message)
            raise ApuOwnerRefused(message)

    with conn.transaction():
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT project_id, event_type, payload_digest FROM agency_apu_events "
                "WHERE idempotency_key = %s",
                (key,),
            )
            replay = cur.fetchone()
        if replay is not None:
            if (
                replay["project_id"] != project_id
                or replay["event_type"] != "reviewed_dossier_imported"
                or replay["payload_digest"] != payload_digest
            ):
                raise ApuOwnerConflict("APU idempotency key belongs to another effect")
            return get_project_anatomy(conn, project_id=project_id)
        if not _project_exists(conn, project_id):
            raise ApuOwnerNotFound(f"unknown Project: {project_id}")
        if _project_state(conn, project_id) is not None:
            raise ApuOwnerConflict("Project APU owner is already initialized")

        conn.execute(
            """
            INSERT INTO agency_apu_project_state (
                project_id, revision, created_by, model_authority_ref, model_doctrine_ref
            ) VALUES (%s, 1, %s, %s, %s)
            """,
            (project_id, actor, MODEL_AUTHORITY_REF, MODEL_DOCTRINE_REF),
        )
        _insert_dossier(conn, dossier, actor=actor)
        conn.execute(
            """
            INSERT INTO agency_apu_events (
                event_id, project_id, event_type, expected_revision,
                resulting_revision, actor, idempotency_key, payload_digest, payload
            ) VALUES (%s, %s, 'reviewed_dossier_imported', 0, 1, %s, %s, %s, %s)
            """,
            (
                f"apu-event-{uuid.uuid4().hex}", project_id, actor, key, payload_digest,
                Jsonb(
                    {
                        "review_ref": review_ref,
                        "stable_object_refs": [
                            item["stable_object_id"] for item in dossier["stable_objects"]
                        ],
                        "source_representation_refs": [
                            item["representation_id"]
                            for item in dossier["source_representations"]
                        ],
                        "attribute_claim_refs": [
                            item["attribute_claim_id"] for item in dossier["attribute_claims"]
                        ],
                        "relation_claim_refs": [
                            item["relation_claim_id"] for item in dossier["relation_claims"]
                        ],
                        "automatic_creation": False,
                        "runtime_write": False,
                    }
                ),
            ),
        )
    return get_project_anatomy(conn, project_id=project_id)


def get_apu_object(
    conn: psycopg.Connection,
    *,
    project_id: str,
    object_id: str,
    lock: bool = False,
) -> dict[str, Any]:
    suffix = " FOR UPDATE" if lock else ""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM agency_apu_objects WHERE project_id = %s AND object_id = %s"
            + suffix,
            (project_id, object_id),
        )
        row = cur.fetchone()
    if row is None:
        raise ApuOwnerNotFound(f"unknown APU object in Project {project_id}: {object_id}")
    value = dict(row)
    return {
        "object_id": value["object_id"],
        "project_ref": value["project_id"],
        "object_family": value["object_family"],
        "stable_object": value["stable_object_payload"],
        "revision": int(value["revision"]),
        "retired_at": value.get("retired_at"),
        "retired_by": value.get("retired_by"),
    }


def get_project_anatomy(conn: psycopg.Connection, *, project_id: str) -> dict[str, Any]:
    project_id = _required(project_id, "project_id")
    state = _project_state(conn, project_id)
    if state is None:
        raise ApuOwnerNotFound(f"Project has no executable APU owner state: {project_id}")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM agency_apu_objects WHERE project_id = %s "
            "AND retired_at IS NULL ORDER BY object_id",
            (project_id,),
        )
        object_rows = [dict(row) for row in cur.fetchall()]
        cur.execute(
            "SELECT * FROM agency_apu_source_representations WHERE project_id = %s "
            "ORDER BY representation_id",
            (project_id,),
        )
        representation_rows = [dict(row) for row in cur.fetchall()]
        cur.execute(
            "SELECT * FROM agency_apu_attribute_claims WHERE project_id = %s ORDER BY claim_id",
            (project_id,),
        )
        attribute_rows = [dict(row) for row in cur.fetchall()]
        cur.execute(
            "SELECT * FROM agency_apu_relation_claims WHERE project_id = %s ORDER BY claim_id",
            (project_id,),
        )
        relation_rows = [dict(row) for row in cur.fetchall()]
    return {
        "project_ref": project_id,
        "model_version": 2,
        "model_authority_ref": state["model_authority_ref"],
        "model_doctrine_ref": state["model_doctrine_ref"],
        "owner_revision": int(state["revision"]),
        "stable_objects": [
            {
                "object_id": row["object_id"],
                "stable_object": row["stable_object_payload"],
                "revision": int(row["revision"]),
                "retired_at": row.get("retired_at"),
            }
            for row in object_rows
        ],
        "source_representations": [
            dict(row["representation_payload"]) | {"revision": int(row["revision"])}
            for row in representation_rows
        ],
        "attribute_claims": [dict(row["claim_payload"]) for row in attribute_rows],
        "relation_claims": [dict(row["claim_payload"]) for row in relation_rows],
        "authority": dict(AUTHORITY),
    }


def list_apu_events(conn: psycopg.Connection, *, project_id: str) -> list[dict[str, Any]]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM agency_apu_events WHERE project_id = %s ORDER BY occurred_at, event_id",
            (project_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def _source_match_effect(
    command: dict[str, Any],
    *,
    project_id: str,
    object_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    representation = command.get("source_representation")
    relation = command.get("identity_relation_claim")
    if not isinstance(representation, dict) or not isinstance(relation, dict):
        raise ApuOwnerError(
            "source match requires exact source representation and identity relation payloads"
        )
    _validate("source_representation", representation)
    _validate("relation_claim", relation)
    representation_id = _required(
        representation.get("representation_id"), "source_representation.representation_id"
    )
    if representation.get("project_ref") != project_id:
        raise ApuOwnerError("source representation must carry the exact Project")
    if representation.get("proof_status") != "candidate":
        raise ApuOwnerError("applied source representation must remain candidate")
    if relation.get("relation_type") != "identity.represents":
        raise ApuOwnerError("source match must use identity.represents")
    if relation.get("assertion_mode") != "proposed":
        raise ApuOwnerError("source match assertion must remain proposed")
    if relation.get("source_authority") != "model_interpretation_candidate":
        raise ApuOwnerError("source match must retain candidate source authority")
    if relation.get("proof_status") != "candidate":
        raise ApuOwnerError("source match relation must remain candidate")
    if relation.get("subject_ref") != {
        "entity_type": "source_representation",
        "entity_id": representation_id,
    }:
        raise ApuOwnerError("identity relation must start from the exact source representation")
    if relation.get("object_ref") != {
        "entity_type": "stable_object",
        "entity_id": object_id,
    }:
        raise ApuOwnerError("identity relation must target the selected stable object")
    if relation.get("source_representation_refs") != [representation_id]:
        raise ApuOwnerError("identity relation must retain its exact source representation")
    if command.get("certainty") and relation.get("certainty") != command.get("certainty"):
        raise ApuOwnerError("identity relation certainty must equal the reviewed mapping")
    return dict(representation), dict(relation)


def _store_source_match_effect(
    conn,
    *,
    representation: dict[str, Any],
    relation: dict[str, Any],
    project_id: str,
    object_id: str,
    actor: str,
) -> dict[str, Any]:
    representation_id = representation["representation_id"]
    representation_digest = _digest(representation)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM agency_apu_source_representations "
            "WHERE representation_id = %s FOR UPDATE",
            (representation_id,),
        )
        existing = cur.fetchone()
    if existing is None:
        conn.execute(
            """
            INSERT INTO agency_apu_source_representations (
                representation_id, project_id, source_kind, proof_status,
                representation_payload, payload_digest, revision, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, 1, %s)
            """,
            (
                representation_id, project_id, representation["source_kind"],
                representation["proof_status"], Jsonb(representation),
                representation_digest, actor,
            ),
        )
        representation_revision = 1
        representation_reused = False
    else:
        row = dict(existing)
        if (
            row["project_id"] != project_id
            or row["payload_digest"] != representation_digest
            or row["representation_payload"] != representation
        ):
            raise ApuOwnerConflict(
                "source representation identity belongs to different content"
            )
        representation_revision = int(row["revision"])
        representation_reused = True

    relation_id = _required(
        relation.get("relation_claim_id"), "identity_relation_claim.relation_claim_id"
    )
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM agency_apu_relation_claims WHERE claim_id = %s", (relation_id,))
        if cur.fetchone() is not None:
            raise ApuOwnerConflict("identity relation claim already exists")
    conn.execute(
        """
        INSERT INTO agency_apu_relation_claims (
            claim_id, project_id, subject_entity_type, subject_entity_id,
            relation_type, object_entity_type, object_entity_id, assertion_mode,
            source_authority, proof_status, claim_payload, payload_digest, created_by
        ) VALUES (%s, %s, 'source_representation', %s, 'identity.represents',
                  'stable_object', %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            relation_id, project_id, representation_id, object_id,
            relation["assertion_mode"], relation["source_authority"],
            relation["proof_status"], Jsonb(relation), _digest(relation), actor,
        ),
    )
    return {
        "source_representation": representation | {"revision": representation_revision},
        "identity_relation_claim": relation,
        "source_representation_reused": representation_reused,
    }


def _get_source_match_effect(
    conn,
    *,
    representation: dict[str, Any],
    relation: dict[str, Any],
) -> dict[str, Any]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT representation_payload, revision FROM agency_apu_source_representations "
            "WHERE representation_id = %s",
            (representation["representation_id"],),
        )
        representation_row = cur.fetchone()
        cur.execute(
            "SELECT claim_payload FROM agency_apu_relation_claims WHERE claim_id = %s",
            (relation["relation_claim_id"],),
        )
        relation_row = cur.fetchone()
    if representation_row is None or relation_row is None:
        raise ApuOwnerConflict("source match event has incomplete canonical effect")
    return {
        "source_representation": dict(representation_row["representation_payload"])
        | {"revision": int(representation_row["revision"])},
        "identity_relation_claim": dict(relation_row["claim_payload"]),
        "source_representation_reused": True,
    }


def apply_source_match(
    conn: psycopg.Connection,
    *,
    command: dict[str, Any],
    authorization_id: str,
    actor: str,
    idempotency_key: str,
) -> dict[str, Any]:
    """Apply one authorized source match through the canonical carrier."""
    if command.get("operation") != "add_match_to_existing_object":
        raise ApuOwnerError("unsupported APU owner application operation")
    project_id = _required(command.get("project_ref"), "command.project_ref")
    representation_payload = command.get("source_representation") or {}
    relation_payload = command.get("identity_relation_claim") or {}
    object_id = _required(
        (relation_payload.get("object_ref") or {}).get("entity_id"),
        "command.identity_relation_claim.object_ref.entity_id",
    )
    candidate_ref = _required(
        representation_payload.get("representation_id"),
        "command.source_representation.representation_id",
    )
    command_id = _required(command.get("command_id"), "command.command_id")
    command_digest = _required(command.get("payload_digest"), "command.payload_digest")
    authorization_id = _required(authorization_id, "authorization_id")
    actor = _required(actor, "actor")
    key = _required(idempotency_key, "idempotency_key")
    try:
        expected_owner_revision = int(command["expected_owner_revision"])
        expected_object_revision = int(command["expected_object_revision"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ApuOwnerError("command target revisions are required") from exc
    if expected_owner_revision < 1 or expected_object_revision < 1:
        raise ApuOwnerError("command target revisions must be positive")
    representation, relation = _source_match_effect(
        command, project_id=project_id, object_id=object_id
    )
    event_payload = {
        "command_ref": command_id,
        "command_payload_digest": command_digest,
        "authorization_ref": authorization_id,
        "target_stable_object_ref": object_id,
        "source_candidate_ref": candidate_ref,
        "source_representation_ref": representation["representation_id"],
        "identity_relation_claim_ref": relation["relation_claim_id"],
        "source_artifact_ref": representation.get("source_artifact_ref"),
        "source_execution_result_ref": command.get("source_execution_result_ref"),
        "source_mapping_result_ref": command.get("source_mapping_result_ref"),
        "source_mapping_ref": command.get("source_mapping_ref"),
        "source_review_ref": command.get("source_review_ref"),
        "match_status": "candidate",
        "stable_identity_professionally_validated": False,
        "evidence_admitted": False,
        "work_issue_closed": False,
        "decision_request_resolved": False,
    }
    event_digest = _digest(event_payload)

    with conn.transaction():
        state = _project_state(conn, project_id, lock=True)
        if state is None:
            raise ApuOwnerNotFound(f"Project has no executable APU owner state: {project_id}")
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM agency_apu_events WHERE idempotency_key = %s", (key,))
            replay = cur.fetchone()
            if replay is not None:
                if (
                    replay["event_type"] != "source_match_applied"
                    or replay.get("command_ref") != command_id
                    or replay["payload_digest"] != event_digest
                ):
                    raise ApuOwnerConflict(
                        "APU application idempotency key belongs to another effect"
                    )
                return {
                    "status": "replayed",
                    "event": dict(replay),
                    "object": get_apu_object(conn, project_id=project_id, object_id=object_id),
                    "owner_revision": int(replay["resulting_revision"]),
                    "canonical_effect": _get_source_match_effect(
                        conn, representation=representation, relation=relation
                    ),
                    "authority": dict(APPLICATION_AUTHORITY),
                }
            cur.execute(
                "SELECT event_id FROM agency_apu_events "
                "WHERE event_type = 'source_match_applied' AND command_ref = %s",
                (command_id,),
            )
            if cur.fetchone() is not None:
                raise ApuOwnerConflict("APU write command was already applied")
        if int(state["revision"]) != expected_owner_revision:
            raise ApuOwnerConflict(
                f"stale APU owner revision: expected {expected_owner_revision}, "
                f"found {state['revision']}"
            )
        target = get_apu_object(conn, project_id=project_id, object_id=object_id, lock=True)
        if target.get("retired_at") is not None:
            raise ApuOwnerConflict("target APU object is retired")
        if target["revision"] != expected_object_revision:
            raise ApuOwnerConflict(
                f"stale APU object revision: expected {expected_object_revision}, "
                f"found {target['revision']}"
            )
        canonical_effect = _store_source_match_effect(
            conn,
            representation=representation,
            relation=relation,
            project_id=project_id,
            object_id=object_id,
            actor=actor,
        )
        next_owner_revision = expected_owner_revision + 1
        conn.execute(
            "UPDATE agency_apu_project_state SET revision = %s, "
            "updated_at = clock_timestamp() WHERE project_id = %s AND revision = %s",
            (next_owner_revision, project_id, expected_owner_revision),
        )
        event_id = f"apu-event-{uuid.uuid4().hex}"
        conn.execute(
            """
            INSERT INTO agency_apu_events (
                event_id, project_id, event_type, expected_revision,
                resulting_revision, actor, idempotency_key, payload_digest, payload,
                command_ref, authorization_ref
            ) VALUES (%s, %s, 'source_match_applied', %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                event_id, project_id, expected_owner_revision, next_owner_revision,
                actor, key, event_digest, Jsonb(event_payload), command_id, authorization_id,
            ),
        )
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM agency_apu_events WHERE event_id = %s", (event_id,))
            event = dict(cur.fetchone())
    return {
        "status": "applied",
        "event": event,
        "object": get_apu_object(conn, project_id=project_id, object_id=object_id),
        "owner_revision": next_owner_revision,
        "canonical_effect": canonical_effect,
        "authority": dict(APPLICATION_AUTHORITY),
    }
