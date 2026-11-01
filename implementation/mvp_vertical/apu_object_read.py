"""Bounded read projection for one Project Anatomy stable object.

This module reads the existing executable APU owner tables without becoming a
second owner. It exposes one exact stable object plus only claims directly
attached to that identity. It does not interpret relation semantics, follow
relation edges, match requirements, search globally, admit Evidence, persist
state or authorize effects.
"""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row


AUTHORITY = {
    "projection_only": True,
    "creates_project_fact": False,
    "creates_relation_claim": False,
    "resolves_relation_semantics": False,
    "matches_requirements": False,
    "is_evidence": False,
    "is_decision": False,
    "is_memory": False,
    "authorizes_effect": False,
}


class ApuObjectReadError(ValueError):
    pass


class ApuObjectReadNotFound(ApuObjectReadError):
    pass


def _required(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ApuObjectReadError(f"{field} is required")
    return text


def get_stable_object_context(
    conn: psycopg.Connection,
    *,
    object_id: str,
) -> dict[str, Any]:
    """Read one current stable object and its direct claims only.

    `object_id` is globally unique in the executable APU owner. Direct relation
    claims are returned when the selected object is either endpoint. Endpoint
    references are not followed and no neighbouring object record is read.
    """

    object_id = _required(object_id, "object_id")
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT o.object_id,
                   o.project_id,
                   o.object_family,
                   o.stable_object_payload,
                   o.revision AS object_revision,
                   s.revision AS owner_revision
              FROM agency_apu_objects o
              JOIN agency_apu_project_state s ON s.project_id = o.project_id
             WHERE o.object_id = %s
               AND o.retired_at IS NULL
            """,
            (object_id,),
        )
        object_row = cur.fetchone()
        if object_row is None:
            raise ApuObjectReadNotFound(f"unknown active APU stable object: {object_id}")

        project_id = str(object_row["project_id"])
        cur.execute(
            """
            SELECT claim_payload
              FROM agency_apu_attribute_claims
             WHERE project_id = %s
               AND subject_entity_type = 'stable_object'
               AND subject_entity_id = %s
             ORDER BY claim_id
            """,
            (project_id, object_id),
        )
        attribute_claims = [dict(row["claim_payload"]) for row in cur.fetchall()]

        cur.execute(
            """
            SELECT claim_payload
              FROM agency_apu_relation_claims
             WHERE project_id = %s
               AND (
                    (subject_entity_type = 'stable_object' AND subject_entity_id = %s)
                    OR
                    (object_entity_type = 'stable_object' AND object_entity_id = %s)
               )
             ORDER BY claim_id
            """,
            (project_id, object_id, object_id),
        )
        relation_claims = [dict(row["claim_payload"]) for row in cur.fetchall()]

        # Use the same non-superseded claim rule as get_project_anatomy:
        # replaced assertions remain traceable, but not in the active lists.
        # Only IDs for the selected object are queried; no graph traversal.
        direct_claim_ids = [
            *[claim["attribute_claim_id"] for claim in attribute_claims],
            *[claim["relation_claim_id"] for claim in relation_claims],
        ]
        supersession_rows = []
        if direct_claim_ids:
            cur.execute(
                """
                SELECT superseded_claim_id, superseding_claim_id, claim_family, event_id
                  FROM agency_apu_claim_supersessions
                 WHERE project_id = %s
                   AND superseded_claim_id = ANY(%s)
                 ORDER BY created_at, superseded_claim_id
                """,
                (project_id, direct_claim_ids),
            )
            supersession_rows = [dict(row) for row in cur.fetchall()]

    replaced_ids = {row["superseded_claim_id"] for row in supersession_rows}
    attribute_claims = [
        claim for claim in attribute_claims
        if claim["attribute_claim_id"] not in replaced_ids
    ]
    relation_claims = [
        claim for claim in relation_claims
        if claim["relation_claim_id"] not in replaced_ids
    ]
    superseded_claims = [
        {
            "claim_family": row["claim_family"],
            "superseded_claim_ref": row["superseded_claim_id"],
            "superseding_claim_ref": row["superseding_claim_id"],
            "event_ref": row["event_id"],
        }
        for row in supersession_rows
    ]

    source_representation_refs: set[str] = set()
    for claim in [*attribute_claims, *relation_claims]:
        for ref in claim.get("source_representation_refs") or []:
            text = str(ref or "").strip()
            if text:
                source_representation_refs.add(text)

    return {
        "object_id": str(object_row["object_id"]),
        "project_ref": project_id,
        "object_family": object_row["object_family"],
        "stable_object": dict(object_row["stable_object_payload"]),
        "revision": int(object_row["object_revision"]),
        "owner_revision": int(object_row["owner_revision"]),
        "attribute_claims": attribute_claims,
        "relation_claims": relation_claims,
        "superseded_claims": superseded_claims,
        "source_representation_refs": sorted(source_representation_refs),
        "scope": {
            "exact_stable_object_only": True,
            "direct_attribute_claims_only": True,
            "direct_relation_claims_only": True,
            "relation_traversal_performed": False,
            "neighbour_records_materialized": False,
            "global_search_performed": False,
            "global_listing_performed": False,
        },
        "authority": dict(AUTHORITY),
        "non_equivalences": [
            "stable object projection != project truth",
            "relation reference != neighbour context admission",
            "relation claim != relation semantics",
            "source representation ref != source dereference authority",
            "projection != persistence",
        ],
    }
