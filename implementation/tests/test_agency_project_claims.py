from __future__ import annotations

import uuid

import pytest

from mvp_vertical import agency_claims, agency_data


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


@pytest.fixture
def conn():
    try:
        connection = agency_data.connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(
        "TRUNCATE agency_project_claims, agency_change_candidate_events, agency_change_candidates, "
        "agency_project_events, agency_projects RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _project(conn) -> dict:
    return agency_data.create_project(
        conn,
        project_id=_id("project"),
        code=_id("CLAIM")[:24],
        display_name="Projet claims",
        actor="human",
        actor_kind="human",
        idempotency_key=_id("create"),
        attributes={"programme_summary": "Maison individuelle"},
    )


def test_claim_updates_derived_project_projection_without_bumping_project_revision(conn) -> None:
    project = _project(conn)
    first = agency_claims.record_claim(
        conn,
        project_id=project["project_id"],
        claim_type="budget",
        value=350000,
        actor="human:test",
        source_kind="human_assertion",
        status="asserted",
    )

    after_first = agency_data.get_project(conn, project["project_id"])
    assert after_first["revision"] == project["revision"]
    assert after_first["attributes"] == {"programme_summary": "Maison individuelle"}
    assert after_first["claim_values"]["budget"] == 350000
    assert after_first["claim_refs"]["budget"]["claim_id"] == first["claim_id"]
    assert after_first["claim_refs"]["budget"]["status"] == "asserted"

    second = agency_claims.record_claim(
        conn,
        project_id=project["project_id"],
        claim_type="budget",
        value=375000,
        actor="human:test",
        source_kind="information",
        source_ref="information-budget-a01",
        backing_ref={
            "entity_type": "information",
            "entity_id": "information-budget-a01",
            "observed_status": "acted",
        },
        status="source_backed",
        supersedes=first["claim_id"],
    )

    current = agency_data.get_project(conn, project["project_id"])
    assert current["revision"] == project["revision"]
    assert current["claim_values"]["budget"] == 375000
    assert current["claim_refs"]["budget"]["claim_id"] == second["claim_id"]
    assert current["claim_refs"]["budget"]["backing_ref"] == {
        "entity_type": "information",
        "entity_id": "information-budget-a01",
        "observed_status": "acted",
    }
    assert [claim["claim_id"] for claim in agency_claims.list_project_claims(conn, project["project_id"])] == [
        second["claim_id"],
        first["claim_id"],
    ]


def test_direct_claim_cannot_assert_verified_status(conn) -> None:
    project = _project(conn)

    with pytest.raises(
        agency_claims.AgencyClaimError,
        match="verified Project claim requires a human-reviewed execution_result candidate",
    ):
        agency_claims.record_claim(
            conn,
            project_id=project["project_id"],
            claim_type="budget",
            value=350000,
            actor="human:test",
            source_kind="human_assertion",
            backing_ref={
                "entity_type": "project",
                "entity_id": project["project_id"],
                "observed_status": "active",
            },
            status="verified",
        )

    assert agency_claims.list_project_claims(conn, project["project_id"]) == []


def test_scalar_parcel_claims_are_aggregated_into_project_list_projection(conn) -> None:
    project = _project(conn)
    for value in ("AD-85", "AD-86"):
        agency_claims.record_claim(
            conn,
            project_id=project["project_id"],
            claim_type="parcelle",
            value=value,
            actor="human:test",
            source_kind="human_assertion",
            status="asserted",
        )

    current = agency_data.get_project(conn, project["project_id"])
    assert current["claim_values"]["parcelle"] == ["AD-86", "AD-85"]
    assert len(current["claim_refs"]["parcelle"]) == 2


def test_project_claim_rows_are_append_only(conn) -> None:
    project = _project(conn)
    claim = agency_claims.record_claim(
        conn,
        project_id=project["project_id"],
        claim_type="plu_zone",
        value="UDb",
        actor="human:test",
        source_kind="human_assertion",
        status="asserted",
    )

    with pytest.raises(Exception, match="append-only"):
        conn.execute(
            "UPDATE agency_project_claims SET value='\"UC0\"'::jsonb WHERE claim_id=%s",
            (claim["claim_id"],),
        )
    conn.rollback()

    with pytest.raises(Exception, match="append-only"):
        conn.execute("DELETE FROM agency_project_claims WHERE claim_id=%s", (claim["claim_id"],))
    conn.rollback()


def test_temporal_reads_separate_historical_knowledge_from_retrospective_applicability(conn) -> None:
    project = _project(conn)
    project_id = project["project_id"]

    first = agency_claims.record_claim(
        conn,
        project_id=project_id,
        claim_type="budget",
        value=350000,
        actor="human:test",
        source_kind="human_assertion",
        status="asserted",
        observed_at="2026-01-05T09:00:00+00:00",
        effective_at="2026-01-01T00:00:00+00:00",
    )
    # get_claim() starts a normal read transaction after the insert transaction;
    # close it before taking the explicit knowledge cutoff.
    conn.commit()
    knowledge_cutoff = conn.execute("SELECT clock_timestamp()").fetchone()[0]
    conn.commit()

    second = agency_claims.record_claim(
        conn,
        project_id=project_id,
        claim_type="budget",
        value=375000,
        actor="human:test",
        source_kind="human_assertion",
        status="asserted",
        observed_at="2026-03-10T09:00:00+00:00",
        effective_at="2026-02-01T00:00:00+00:00",
        supersedes=first["claim_id"],
    )
    conn.commit()

    second_recorded_at = conn.execute(
        "SELECT created_at FROM agency_project_claims WHERE claim_id = %s",
        (second["claim_id"],),
    ).fetchone()[0]
    assert second_recorded_at > knowledge_cutoff

    known_then = agency_claims.project_claims_known_as_of(
        conn, project_id, knowledge_cutoff
    )
    applicable_then = agency_claims.applicable_project_claims_as_of(
        conn,
        project_id,
        "2026-03-01T00:00:00+00:00",
        knowledge_time=knowledge_cutoff,
    )
    retrospective_march = agency_claims.applicable_project_claims_as_of(
        conn,
        project_id,
        "2026-03-01T00:00:00+00:00",
    )
    retrospective_january = agency_claims.applicable_project_claims_as_of(
        conn,
        project_id,
        "2026-01-15T00:00:00+00:00",
    )

    assert [(claim["claim_id"], claim["value"]) for claim in known_then] == [
        (first["claim_id"], 350000)
    ]
    assert [(claim["claim_id"], claim["value"]) for claim in applicable_then] == [
        (first["claim_id"], 350000)
    ]
    assert [(claim["claim_id"], claim["value"]) for claim in retrospective_march] == [
        (second["claim_id"], 375000)
    ]
    assert [(claim["claim_id"], claim["value"]) for claim in retrospective_january] == [
        (first["claim_id"], 350000)
    ]


def test_business_time_does_not_invent_effective_at_from_observation_or_recording(conn) -> None:
    project = _project(conn)
    project_id = project["project_id"]

    claim = agency_claims.record_claim(
        conn,
        project_id=project_id,
        claim_type="plu_zone",
        value="UDb",
        actor="human:test",
        source_kind="human_assertion",
        status="asserted",
        observed_at="2026-01-05T09:00:00+00:00",
    )
    conn.commit()
    after_recording = conn.execute("SELECT clock_timestamp()").fetchone()[0]

    known = agency_claims.project_claims_known_as_of(conn, project_id, after_recording)
    applicable = agency_claims.applicable_project_claims_as_of(
        conn,
        project_id,
        "2026-09-03T00:00:00+00:00",
        knowledge_time=after_recording,
    )

    assert [item["claim_id"] for item in known] == [claim["claim_id"]]
    assert applicable == []
