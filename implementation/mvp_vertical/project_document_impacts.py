"""Read-only downstream review candidates for changed professional revisions.

Only executable provenance already present in the repository is considered. The
calculation never infers document dependencies from names, text similarity,
Project Anatomy proximity or professional convention. A returned item is a
review candidate, not a proven impact, WorkIssue, DecisionRequest or Evidence.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import psycopg
from psycopg.rows import dict_row

from . import project_document_comparison

AUTHORITY = {
    "is_evidence": False,
    "is_decision": False,
    "is_work_issue": False,
    "is_project_claim": False,
    "is_professional_impact": False,
    "authorizes_rewrite": False,
    "changes_project_truth": False,
}

EXCLUDED_SURFACES = {
    "project_claim": "string source_ref is not an exact executable document-version binding",
    "project_anatomy": "no reviewed relational binding from source representations to technical document versions is admitted here",
    "document_relation": "canonical Entity Relation vocabulary is not widened to Project Documents in this slice",
}


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _candidate_id(
    *,
    before_version_id: str,
    after_version_id: str,
    target_type: str,
    target_id: str,
    basis: dict[str, Any],
) -> str:
    material = {
        "before_version_id": before_version_id,
        "after_version_id": after_version_id,
        "target_type": target_type,
        "target_id": target_id,
        "basis": basis,
    }
    return f"document-impact-{_digest(material)[:24]}"


def _table_exists(conn: psycopg.Connection, name: str) -> bool:
    row = conn.execute("SELECT to_regclass(%s)", (name,)).fetchone()
    return row is not None and row[0] is not None


def _information_candidates(
    conn: psycopg.Connection,
    *,
    before: dict[str, Any],
    after: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not _table_exists(conn, "agency_information_document_links"):
        return [], [{"surface": "information", "reason": "owner_not_initialized"}]

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT information_id, document_id, role, observed_version,
                   observed_digest, created_at
              FROM agency_information_document_links
             WHERE document_id = %s
             ORDER BY information_id
            """,
            (before["source_document_id"],),
        )
        rows = [dict(row) for row in cur.fetchall()]

    candidates: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    for row in rows:
        observed_version = row.get("observed_version")
        observed_digest = row.get("observed_digest")
        version_matches = (
            observed_version is None
            or int(observed_version) == int(before["source_version"])
        )
        digest_matches = (
            observed_digest is None
            or str(observed_digest).lower() == str(before["source_digest"]).lower()
        )
        if not version_matches or not digest_matches:
            exclusions.append(
                {
                    "surface": "information",
                    "target_id": row["information_id"],
                    "reason": "declared_observed_revision_does_not_match_before_revision",
                    "observed_version": observed_version,
                    "observed_digest": observed_digest,
                }
            )
            continue

        if observed_digest is not None:
            basis_strength = "exact_digest"
            review_posture = "review_recommended"
        elif observed_version is not None:
            basis_strength = "exact_version"
            review_posture = "review_recommended"
        else:
            basis_strength = "unversioned_document_link"
            review_posture = "needs_scope_confirmation"

        basis = {
            "kind": "information_document_link",
            "strength": basis_strength,
            "document_id": row["document_id"],
            "role": row["role"],
            "observed_version": observed_version,
            "observed_digest": observed_digest,
        }
        candidates.append(
            {
                "candidate_id": _candidate_id(
                    before_version_id=before["version_id"],
                    after_version_id=after["version_id"],
                    target_type="information",
                    target_id=row["information_id"],
                    basis=basis,
                ),
                "target": {
                    "entity_type": "information",
                    "entity_id": row["information_id"],
                },
                "basis": basis,
                "review_posture": review_posture,
                "impact_established": False,
            }
        )
    return candidates, exclusions


def _knowledge_candidates(
    conn: psycopg.Connection,
    *,
    before: dict[str, Any],
    after: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not _table_exists(conn, "knowledge_items"):
        return [], [{"surface": "knowledge", "reason": "owner_not_initialized"}]

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT knowledge_id, document_id, source_version, source_digest,
                   review_status, version
              FROM knowledge_items
             WHERE document_id = %s
               AND source_version = %s
               AND lower(source_digest) = lower(%s)
             ORDER BY knowledge_id
            """,
            (
                before["source_document_id"],
                before["source_version"],
                before["source_digest"],
            ),
        )
        rows = [dict(row) for row in cur.fetchall()]

    candidates: list[dict[str, Any]] = []
    for row in rows:
        basis = {
            "kind": "knowledge_exact_source_revision",
            "strength": "exact_source_triple",
            "document_id": row["document_id"],
            "source_version": int(row["source_version"]),
            "source_digest": row["source_digest"],
            "knowledge_version": int(row["version"]),
            "knowledge_review_status": row["review_status"],
        }
        candidates.append(
            {
                "candidate_id": _candidate_id(
                    before_version_id=before["version_id"],
                    after_version_id=after["version_id"],
                    target_type="knowledge",
                    target_id=row["knowledge_id"],
                    basis=basis,
                ),
                "target": {
                    "entity_type": "knowledge",
                    "entity_id": row["knowledge_id"],
                },
                "basis": basis,
                "review_posture": "review_recommended",
                "impact_established": False,
            }
        )
    return candidates, []


def project_impact_candidates(
    conn: psycopg.Connection,
    *,
    before_version_id: str,
    after_version_id: str,
) -> dict[str, Any]:
    """Calculate review-only candidates from explicit old-revision consumers."""
    comparison = project_document_comparison.compare_revisions(
        conn,
        before_version_id=before_version_id,
        after_version_id=after_version_id,
    )
    before = comparison["before_revision"]
    after = comparison["after_revision"]

    if not comparison["summary"]["has_changes"]:
        return {
            "document_id": comparison["document_id"],
            "before_version_id": before_version_id,
            "after_version_id": after_version_id,
            "comparison_summary": comparison["summary"],
            "impact_candidates": [],
            "excluded_or_unresolved": [],
            "excluded_surfaces": dict(EXCLUDED_SURFACES),
            "reason": "no_structural_content_change_detected",
            "authority": dict(AUTHORITY),
        }

    information, information_exclusions = _information_candidates(
        conn, before=before, after=after
    )
    knowledge, knowledge_exclusions = _knowledge_candidates(
        conn, before=before, after=after
    )
    candidates = information + knowledge
    candidates.sort(
        key=lambda item: (
            item["target"]["entity_type"],
            item["target"]["entity_id"],
            item["basis"]["strength"],
            item["candidate_id"],
        )
    )

    return {
        "document_id": comparison["document_id"],
        "before_version_id": before_version_id,
        "after_version_id": after_version_id,
        "comparison_summary": comparison["summary"],
        "impact_candidates": candidates,
        "excluded_or_unresolved": information_exclusions + knowledge_exclusions,
        "excluded_surfaces": dict(EXCLUDED_SURFACES),
        "reason": "explicit_consumers_of_changed_before_revision",
        "authority": dict(AUTHORITY),
    }
