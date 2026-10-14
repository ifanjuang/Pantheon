from __future__ import annotations

import uuid

import pytest

from mvp_vertical import agency_claims, agency_data, project_claim_conflicts


def _id(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex}"


@pytest.fixture
def conn():
    try:
        connection = agency_data.connect()
    except Exception as exc:  # pragma: no cover - unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(
        "TRUNCATE agency_project_claim_conflict_candidates, agency_project_claims, "
        "agency_change_candidate_events, agency_change_candidates, "
        "agency_project_events, agency_projects RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _project(conn, label: str) -> dict:
    return agency_data.create_project(
        conn,
        project_id=_id("project"),
        code=_id("SQL")[:24],
        display_name=f"Projet {label}",
        actor="human:test",
        actor_kind="human",
        idempotency_key=_id("project-create"),
        attributes={"programme_summary": "SQL authority conflict fixture"},
    )


def _claim(
    conn,
    project_id: str,
    value: int,
    *,
    effective_at: str | None = None,
    supersedes: str | None = None,
) -> dict:
    return agency_claims.record_claim(
        conn,
        project_id=project_id,
        claim_type="budget",
        value=value,
        actor="human:test",
        source_kind="human_assertion",
        status="asserted",
        certainty="E2",
        observed_at="2026-09-04T05:00:00+00:00",
        effective_at=effective_at,
        supersedes=supersedes,
    )


def _insert_direct(
    conn,
    candidate: dict,
    *,
    detector_id: str = project_claim_conflicts.DETECTOR_ID,
    detector_version: str = project_claim_conflicts.DETECTOR_VERSION,
) -> None:
    claim_ids = [item["claim_id"] for item in candidate["claim_refs"]]
    conn.execute(
        """
        INSERT INTO agency_project_claim_conflict_candidates (
            conflict_candidate_id, project_id, claim_type,
            left_claim_id, right_claim_id, classification,
            detector_id, detector_version, submitted_by
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            candidate["conflict_candidate_id"],
            candidate["project_id"],
            candidate["claim_type"],
            claim_ids[0],
            claim_ids[1],
            candidate["classification"],
            detector_id,
            detector_version,
            "sql:test",
        ),
    )


def test_sql_refuses_forged_temporal_classification(conn) -> None:
    project = _project(conn, "classification")
    effective = "2026-09-01T00:00:00+00:00"
    _claim(conn, project["project_id"], 350000, effective_at=effective)
    _claim(conn, project["project_id"], 375000, effective_at=effective)
    candidate = project_claim_conflicts.detect_project_claim_conflicts(
        conn, project["project_id"]
    )[0]
    candidate["classification"] = "temporal_ambiguity"

    with pytest.raises(Exception, match="classification does not match"):
        with conn.transaction():
            _insert_direct(conn, candidate)
    assert project_claim_conflicts.list_project_candidates(conn, project["project_id"]) == []


def test_sql_refuses_cross_project_pair(conn) -> None:
    first_project = _project(conn, "A")
    second_project = _project(conn, "B")
    left = _claim(conn, first_project["project_id"], 350000)
    right = _claim(conn, second_project["project_id"], 375000)
    ordered = sorted((left, right), key=lambda item: item["claim_id"])
    candidate = {
        "conflict_candidate_id": "pcc-" + "1" * 24,
        "project_id": first_project["project_id"],
        "claim_type": "budget",
        "claim_refs": [
            {"claim_id": ordered[0]["claim_id"]},
            {"claim_id": ordered[1]["claim_id"]},
        ],
        "classification": "value_conflict_undated",
    }

    with pytest.raises(Exception, match="declared Project"):
        with conn.transaction():
            _insert_direct(conn, candidate)


def test_sql_refuses_candidate_after_one_bound_claim_is_superseded(conn) -> None:
    project = _project(conn, "supersession")
    first = _claim(conn, project["project_id"], 350000)
    second = _claim(conn, project["project_id"], 375000)
    candidate = project_claim_conflicts.detect_project_claim_conflicts(
        conn, project["project_id"]
    )[0]

    _claim(
        conn,
        project["project_id"],
        360000,
        supersedes=first["claim_id"],
    )

    with pytest.raises(Exception, match="unsuperseded"):
        with conn.transaction():
            _insert_direct(conn, candidate)

    # The failed insert rolls back only its savepoint; the setup remains intact.
    active_ids = {
        item["claim_id"]
        for item in agency_claims.active_project_claims(conn, project["project_id"])
    }
    assert first["claim_id"] not in active_ids
    assert second["claim_id"] in active_ids


def test_sql_storage_has_no_candidate_payload_or_authority_promotion_columns(conn) -> None:
    rows = conn.execute(
        """
        SELECT column_name
          FROM information_schema.columns
         WHERE table_name = 'agency_project_claim_conflict_candidates'
        """
    ).fetchall()
    columns = {row[0] for row in rows}
    assert "candidate" not in columns
    assert "candidate_digest" not in columns
    assert "authority" not in columns
    assert "decision_id" not in columns
    assert "evidence_id" not in columns
    assert "resolution" not in columns


def test_sql_refuses_unqualified_detector_identity(conn) -> None:
    project = _project(conn, "detector")
    _claim(conn, project["project_id"], 350000)
    _claim(conn, project["project_id"], 375000)
    candidate = project_claim_conflicts.detect_project_claim_conflicts(
        conn, project["project_id"]
    )[0]

    with pytest.raises(Exception):
        with conn.transaction():
            _insert_direct(conn, candidate, detector_version="999")
