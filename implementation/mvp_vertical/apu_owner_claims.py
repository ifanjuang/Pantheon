"""Progressive claim writes for the Project Anatomy owner.

`apu_owner` installs one reviewed dossier per Project and records identity
matches. This module adds the two claim operations that follow an import:

```text
add_claim        one new attribute or relation claim
supersede_claim  one new claim that replaces one existing claim
```

Both arrive only as an authorized write command (review -> command ->
authorization -> application, see `apu_write_preparation`). Claims stay
append-only: a replacement is a new claim plus a row in
`agency_apu_claim_supersessions`, never an edit. An applied claim keeps its
candidate posture; nothing here validates it professionally, admits Evidence or
canonizes it.

A later operation (for example object retirement) belongs in its own module
next to this one, called from the same application chain.
"""

from __future__ import annotations

import uuid
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from . import apu_owner
from .apu_owner import ApuOwnerConflict, ApuOwnerError, ApuOwnerNotFound


CLAIM_OPERATIONS = {"add_claim", "supersede_claim"}
CLAIM_FAMILIES = {"attribute", "relation"}
EVENT_TYPES = {"add_claim": "claim_added", "supersede_claim": "claim_superseded"}
CLAIM_APPLICATION_AUTHORITY = {
    "claim_recorded": True,
    "claim_professionally_validated": False,
    "is_evidence": False,
    "is_decision": False,
    "is_memory": False,
    "canonizes_claims": False,
    "closes_work_issue": False,
    "resolves_decision_request": False,
    "authorizes_external_effect": False,
}

_TABLES = {
    "attribute": ("agency_apu_attribute_claims", "attribute_claim_id", "attribute_key"),
    "relation": ("agency_apu_relation_claims", "relation_claim_id", "relation_type"),
}


def claim_family_of(claim: Any) -> str:
    """Name the family of one claim payload from its identifier field."""
    if not isinstance(claim, dict):
        raise ApuOwnerError("claim must be an object")
    has_attribute = "attribute_claim_id" in claim
    has_relation = "relation_claim_id" in claim
    if has_attribute == has_relation:
        raise ApuOwnerError("claim must be exactly one attribute or relation claim")
    return "attribute" if has_attribute else "relation"


def claim_id_of(claim: dict[str, Any]) -> str:
    family = claim_family_of(claim)
    return apu_owner._required(claim.get(_TABLES[family][1]), _TABLES[family][1])


def validate_claim_payload(claim_family: str, claim: Any) -> dict[str, Any]:
    """Check one claim against its governed contract and the write posture."""
    if claim_family not in CLAIM_FAMILIES:
        raise ApuOwnerError(f"unsupported claim family: {claim_family}")
    if claim_family_of(claim) != claim_family:
        raise ApuOwnerError("claim_family does not match the claim payload")
    apu_owner._validate(f"{claim_family}_claim", claim)
    if claim.get("proof_status") != "candidate":
        raise ApuOwnerError("an applied claim must remain candidate")
    if claim_family == "relation" and str(claim.get("relation_type") or "").startswith("identity."):
        # identity.represents is a source match; merge, split and object
        # supersession belong to the identity lifecycle, which this path does not open.
        raise ApuOwnerError("identity relations are not claim writes")
    return dict(claim)


def _entity_state(conn, project_id: str, ref: dict[str, Any]) -> str:
    """Return 'present', 'retired' or 'missing' for one APU entity ref."""
    entity_type = ref.get("entity_type")
    entity_id = ref.get("entity_id")
    with conn.cursor(row_factory=dict_row) as cur:
        if entity_type == "stable_object":
            cur.execute(
                "SELECT retired_at FROM agency_apu_objects "
                "WHERE project_id = %s AND object_id = %s",
                (project_id, entity_id),
            )
            row = cur.fetchone()
            if row is None:
                return "missing"
            return "retired" if row["retired_at"] is not None else "present"
        if entity_type == "source_representation":
            cur.execute(
                "SELECT 1 FROM agency_apu_source_representations "
                "WHERE project_id = %s AND representation_id = %s",
                (project_id, entity_id),
            )
            return "present" if cur.fetchone() is not None else "missing"
    raise ApuOwnerError(f"the executable owner does not persist {entity_type} entities")


def _require_live_entity(conn, project_id: str, ref: Any, label: str) -> None:
    if not isinstance(ref, dict):
        raise ApuOwnerError(f"{label} must be an APU entity ref")
    state = _entity_state(conn, project_id, ref)
    if state == "missing":
        raise ApuOwnerNotFound(f"{label} is not in this Project's APU")
    if state == "retired":
        raise ApuOwnerConflict(f"{label} is a retired APU object")


def _claim_row(conn, claim_family: str, claim_id: str, *, lock: bool = False):
    table, _id_field, key_column = _TABLES[claim_family]
    suffix = " FOR UPDATE" if lock else ""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"SELECT project_id, subject_entity_type, subject_entity_id, {key_column} AS claim_key "
            f"FROM {table} WHERE claim_id = %s" + suffix,
            (claim_id,),
        )
        row = cur.fetchone()
    return dict(row) if row is not None else None


def check_claim_write(
    conn: psycopg.Connection,
    *,
    project_id: str,
    claim_family: str,
    claim: dict[str, Any],
    superseded_claim_ref: str | None,
    lock: bool = False,
) -> None:
    """Refuse a claim write the current APU state cannot take.

    Read-only. Preparation calls it to fail early; application calls it again
    under the owner lock, because the state may have moved in between.
    """
    claim = validate_claim_payload(claim_family, claim)
    claim_id = claim_id_of(claim)
    _require_live_entity(conn, project_id, claim.get("subject_ref"), "claim subject")
    if claim_family == "relation":
        _require_live_entity(conn, project_id, claim.get("object_ref"), "relation object")
    for representation_id in claim.get("source_representation_refs") or []:
        ref = {"entity_type": "source_representation", "entity_id": representation_id}
        if _entity_state(conn, project_id, ref) != "present":
            raise ApuOwnerNotFound(
                "claim source_representation_ref is not in this Project's APU"
            )
    for family in CLAIM_FAMILIES:
        if _claim_row(conn, family, claim_id) is not None:
            raise ApuOwnerConflict(f"APU claim already exists: {claim_id}")

    declared = claim.get("supersedes_claim_ref")
    if superseded_claim_ref is None:
        if declared:
            raise ApuOwnerError(
                "the claim declares a replacement the review did not accept"
            )
        return
    if declared and declared != superseded_claim_ref:
        raise ApuOwnerError("the claim declares a different replaced claim than the review")
    previous = _claim_row(conn, claim_family, superseded_claim_ref, lock=lock)
    if previous is None or previous["project_id"] != project_id:
        raise ApuOwnerNotFound(
            f"replaced claim is not a {claim_family} claim of this Project: {superseded_claim_ref}"
        )
    subject = claim["subject_ref"]
    key = claim["attribute_key"] if claim_family == "attribute" else claim["relation_type"]
    if (
        previous["subject_entity_type"] != subject["entity_type"]
        or previous["subject_entity_id"] != subject["entity_id"]
        or previous["claim_key"] != key
    ):
        raise ApuOwnerError("a claim can only replace a claim on the same subject and key")
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM agency_apu_claim_supersessions WHERE superseded_claim_id = %s",
            (superseded_claim_ref,),
        )
        if cur.fetchone() is not None:
            raise ApuOwnerConflict(f"claim was already replaced: {superseded_claim_ref}")


def _event_payload(
    command: dict[str, Any],
    *,
    authorization_id: str,
    claim_family: str,
    claim: dict[str, Any],
    superseded_claim_ref: str | None,
) -> dict[str, Any]:
    return {
        "command_ref": command["command_id"],
        "command_payload_digest": command["payload_digest"],
        "authorization_ref": authorization_id,
        "claim_family": claim_family,
        "claim_ref": claim_id_of(claim),
        "superseded_claim_ref": superseded_claim_ref,
        "subject_ref": claim["subject_ref"],
        "source_execution_result_ref": command.get("source_execution_result_ref"),
        "source_mapping_result_ref": command.get("source_mapping_result_ref"),
        "source_mapping_ref": command.get("source_mapping_ref"),
        "source_review_ref": command.get("source_review_ref"),
        "claim_status": "candidate",
        "claim_professionally_validated": False,
        "evidence_admitted": False,
        "work_issue_closed": False,
        "decision_request_resolved": False,
    }


def apply_claim_write(
    conn: psycopg.Connection,
    *,
    command: dict[str, Any],
    authorization_id: str,
    actor: str,
    idempotency_key: str,
) -> dict[str, Any]:
    """Apply one authorized add_claim or supersede_claim command."""
    operation = command.get("operation")
    if operation not in CLAIM_OPERATIONS:
        raise ApuOwnerError("unsupported APU claim write operation")
    project_id = apu_owner._required(command.get("project_ref"), "command.project_ref")
    command_id = apu_owner._required(command.get("command_id"), "command.command_id")
    apu_owner._required(command.get("payload_digest"), "command.payload_digest")
    authorization_id = apu_owner._required(authorization_id, "authorization_id")
    actor = apu_owner._required(actor, "actor")
    key = apu_owner._required(idempotency_key, "idempotency_key")
    claim_family = command.get("claim_family")
    claim = validate_claim_payload(claim_family, command.get("claim"))
    superseded_claim_ref = command.get("superseded_claim_ref")
    if (operation == "supersede_claim") != bool(superseded_claim_ref):
        raise ApuOwnerError("only supersede_claim names a replaced claim, and it must")
    try:
        expected_owner_revision = int(command["expected_owner_revision"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ApuOwnerError("command owner revision is required") from exc
    if expected_owner_revision < 1:
        raise ApuOwnerError("command owner revision must be positive")
    event_type = EVENT_TYPES[operation]
    event_payload = _event_payload(
        command,
        authorization_id=authorization_id,
        claim_family=claim_family,
        claim=claim,
        superseded_claim_ref=superseded_claim_ref,
    )
    event_digest = apu_owner._digest(event_payload)

    with conn.transaction():
        state = apu_owner._project_state(conn, project_id, lock=True)
        if state is None:
            raise ApuOwnerNotFound(f"Project has no executable APU owner state: {project_id}")
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM agency_apu_events WHERE idempotency_key = %s", (key,))
            replay = cur.fetchone()
            if replay is not None:
                if (
                    replay["event_type"] != event_type
                    or replay.get("command_ref") != command_id
                    or replay["payload_digest"] != event_digest
                ):
                    raise ApuOwnerConflict(
                        "APU application idempotency key belongs to another effect"
                    )
                return {
                    "status": "replayed",
                    "event": dict(replay),
                    "owner_revision": int(replay["resulting_revision"]),
                    "claim_family": claim_family,
                    "claim": claim,
                    "superseded_claim_ref": superseded_claim_ref,
                    "authority": dict(CLAIM_APPLICATION_AUTHORITY),
                }
            cur.execute(
                "SELECT 1 FROM agency_apu_events WHERE command_ref = %s "
                "AND event_type IN ('claim_added', 'claim_superseded')",
                (command_id,),
            )
            if cur.fetchone() is not None:
                raise ApuOwnerConflict("APU write command was already applied")
        if int(state["revision"]) != expected_owner_revision:
            raise ApuOwnerConflict(
                f"stale APU owner revision: expected {expected_owner_revision}, "
                f"found {state['revision']}"
            )
        check_claim_write(
            conn,
            project_id=project_id,
            claim_family=claim_family,
            claim=claim,
            superseded_claim_ref=superseded_claim_ref,
            lock=True,
        )
        if claim_family == "attribute":
            apu_owner._insert_attribute_claim(conn, claim, project_id=project_id, actor=actor)
        else:
            apu_owner._insert_relation_claim(conn, claim, project_id=project_id, actor=actor)
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
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                event_id, project_id, event_type, expected_owner_revision,
                next_owner_revision, actor, key, event_digest, Jsonb(event_payload),
                command_id, authorization_id,
            ),
        )
        if superseded_claim_ref:
            conn.execute(
                """
                INSERT INTO agency_apu_claim_supersessions (
                    superseded_claim_id, superseding_claim_id, claim_family,
                    project_id, event_id
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (superseded_claim_ref, claim_id_of(claim), claim_family, project_id, event_id),
            )
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM agency_apu_events WHERE event_id = %s", (event_id,))
            event = dict(cur.fetchone())
    return {
        "status": "applied",
        "event": event,
        "owner_revision": next_owner_revision,
        "claim_family": claim_family,
        "claim": claim,
        "superseded_claim_ref": superseded_claim_ref,
        "authority": dict(CLAIM_APPLICATION_AUTHORITY),
    }
