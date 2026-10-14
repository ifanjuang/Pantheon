from __future__ import annotations

import copy
import uuid

import pytest

from mvp_vertical import agency_claims, agency_data, pantheon_contracts, project_claim_conflicts


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


def _project(conn, label: str = "Conflits") -> dict:
    return agency_data.create_project(
        conn,
        project_id=_id("project"),
        code=_id("CF")[:24],
        display_name=f"Projet {label}",
        actor="human:test",
        actor_kind="human",
        idempotency_key=_id("project-create"),
        attributes={"programme_summary": "Qualification des ProjectClaims"},
    )


def _claim(
    conn,
    project_id: str,
    *,
    claim_type: str = "budget",
    value=350000,
    effective_at: str | None = None,
    supersedes: str | None = None,
    source_ref: str | None = None,
    backing_ref: dict | None = None,
) -> dict:
    source_kind = "information" if backing_ref is not None else "human_assertion"
    status = "source_backed" if backing_ref is not None else "asserted"
    return agency_claims.record_claim(
        conn,
        project_id=project_id,
        claim_type=claim_type,
        value=value,
        actor="human:test",
        source_kind=source_kind,
        source_ref=source_ref,
        backing_ref=backing_ref,
        status=status,
        certainty="E2",
        observed_at="2026-09-04T05:00:00+00:00",
        effective_at=effective_at,
        supersedes=supersedes,
    )


def test_equal_scalar_claims_do_not_create_conflict_candidate(conn) -> None:
    project = _project(conn)
    _claim(conn, project["project_id"], value=350000)
    _claim(conn, project["project_id"], value=350000)

    assert project_claim_conflicts.detect_project_claim_conflicts(
        conn, project["project_id"]
    ) == []


def test_same_effective_start_different_values_create_unresolved_candidate(conn) -> None:
    project = _project(conn)
    effective = "2026-09-01T00:00:00+00:00"
    first = _claim(conn, project["project_id"], value=350000, effective_at=effective)
    second = _claim(conn, project["project_id"], value=375000, effective_at=effective)

    detected = project_claim_conflicts.detect_project_claim_conflicts(
        conn, project["project_id"]
    )
    assert len(detected) == 1
    candidate = detected[0]
    assert candidate["classification"] == "value_conflict_same_effective_start"
    assert candidate["comparison"] == {
        "effective_time_relation": "same_explicit_start",
        "basis_relation": "no_structured_basis",
        "backing_relation": "none",
        "scope_relation": "same_project_same_claim_type_only",
    }
    assert {item["claim_id"] for item in candidate["claim_refs"]} == {
        first["claim_id"], second["claim_id"]
    }
    assert all(set(item) == {"claim_id"} for item in candidate["claim_refs"])
    assert candidate["authority"] == project_claim_conflicts.AUTHORITY
    assert all(value is False for value in candidate["authority"].values())
    pantheon_contracts.validate("project_claim_conflict_candidate", candidate)

    # Detection is read-only: it does not silently turn either Claim into contested state.
    assert {item["status"] for item in agency_claims.list_project_claims(
        conn, project["project_id"]
    )} == {"asserted"}


def test_different_effective_starts_are_temporal_ambiguity_not_contradiction(conn) -> None:
    project = _project(conn)
    _claim(
        conn,
        project["project_id"],
        value=350000,
        effective_at="2026-01-01T00:00:00+00:00",
    )
    _claim(
        conn,
        project["project_id"],
        value=375000,
        effective_at="2026-07-01T00:00:00+00:00",
    )

    candidate = project_claim_conflicts.detect_project_claim_conflicts(
        conn, project["project_id"]
    )[0]
    assert candidate["classification"] == "temporal_ambiguity"
    assert candidate["comparison"]["effective_time_relation"] == "different_explicit_start"
    assert "validity end" in " ".join(candidate["limitations"])
    # An empty candidate list must not be readable as "nothing contradicts": the
    # detector never looks at geometric or relational Claims, and says so to the
    # consumer rather than only in its own configuration constant.
    limitations = " ".join(candidate["limitations"])
    assert "scalar Claim values only" in limitations
    assert "geometric and relational" in limitations


def test_missing_effective_time_is_not_invented(conn) -> None:
    project = _project(conn)
    _claim(conn, project["project_id"], value=350000)
    _claim(
        conn,
        project["project_id"],
        value=375000,
        effective_at="2026-07-01T00:00:00+00:00",
    )

    candidate = project_claim_conflicts.detect_project_claim_conflicts(
        conn, project["project_id"]
    )[0]
    assert candidate["classification"] == "temporal_ambiguity"
    assert candidate["comparison"]["effective_time_relation"] == "partially_unknown"


def test_two_undated_different_values_are_explicitly_undated_conflict_candidates(conn) -> None:
    project = _project(conn)
    _claim(conn, project["project_id"], value=350000)
    _claim(conn, project["project_id"], value=375000)

    candidate = project_claim_conflicts.detect_project_claim_conflicts(
        conn, project["project_id"]
    )[0]
    assert candidate["classification"] == "value_conflict_undated"
    assert candidate["comparison"]["effective_time_relation"] == "both_unknown"


def test_aggregated_parcels_are_not_pairwise_conflicts(conn) -> None:
    project = _project(conn)
    _claim(conn, project["project_id"], claim_type="parcelle", value="AA-1")
    _claim(conn, project["project_id"], claim_type="parcelle", value="AA-2")

    assert project_claim_conflicts.detect_project_claim_conflicts(
        conn, project["project_id"]
    ) == []


def test_superseded_claim_is_not_compared_with_its_successor(conn) -> None:
    project = _project(conn)
    first = _claim(conn, project["project_id"], value=350000)
    _claim(
        conn,
        project["project_id"],
        value=375000,
        supersedes=first["claim_id"],
    )

    assert project_claim_conflicts.detect_project_claim_conflicts(
        conn, project["project_id"]
    ) == []


def test_backing_support_difference_is_described_without_resolving_candidate(conn) -> None:
    project = _project(conn)
    _claim(
        conn,
        project["project_id"],
        value=350000,
        backing_ref={
            "entity_type": "information",
            "entity_id": "information.budget.a",
            "observed_status": "acted",
        },
        source_ref="information.budget.a",
    )
    _claim(
        conn,
        project["project_id"],
        value=375000,
        backing_ref={
            "entity_type": "information",
            "entity_id": "information.budget.b",
            "observed_status": "acted",
        },
        source_ref="information.budget.b",
    )

    candidate = project_claim_conflicts.detect_project_claim_conflicts(
        conn, project["project_id"]
    )[0]
    assert candidate["comparison"]["backing_relation"] == "different"
    assert candidate["comparison"]["basis_relation"] == "no_structured_basis"
    assert candidate["authority"]["resolves_conflict"] is False


def test_structured_basis_relation_remains_distinct_from_backing_relation() -> None:
    base = {
        "project_id": "project.demo",
        "claim_type": "budget",
        "unit": "EUR",
        "effective_at": None,
    }
    left = {
        **base,
        "claim_id": "claim.a",
        "value": 350000,
        "backing_ref": {
            "entity_type": "information",
            "entity_id": "information.selected.a",
            "observed_status": "acted",
        },
        "provenance": {
            "source_kind": "execution_result",
            "basis_refs": [
                {
                    "entity_type": "information",
                    "entity_id": "information.shared",
                    "observed_revision": 1,
                    "observed_status": "acted",
                },
                {
                    "entity_type": "information",
                    "entity_id": "information.left",
                    "observed_revision": 1,
                    "observed_status": "acted",
                },
            ],
        },
    }
    right = {
        **base,
        "claim_id": "claim.b",
        "value": 375000,
        "backing_ref": {
            "entity_type": "information",
            "entity_id": "information.selected.b",
            "observed_status": "acted",
        },
        "provenance": {
            "source_kind": "execution_result",
            "basis_refs": [
                {
                    "entity_type": "information",
                    "entity_id": "information.shared",
                    "observed_revision": 1,
                    "observed_status": "acted",
                },
                {
                    "entity_type": "information",
                    "entity_id": "information.right",
                    "observed_revision": 1,
                    "observed_status": "acted",
                },
            ],
        },
    }

    candidate = project_claim_conflicts._build_candidate(left, right)
    assert candidate["comparison"]["basis_relation"] == "overlapping_structured_basis"
    assert candidate["comparison"]["backing_relation"] == "different"
    assert candidate["classification"] == "value_conflict_undated"


def test_same_type_unit_mismatch_is_integrity_error_not_conflict_classification() -> None:
    left = {
        "project_id": "project.demo",
        "claim_type": "budget",
        "claim_id": "claim.a",
        "value": 350000,
        "unit": "EUR",
        "effective_at": None,
        "backing_ref": None,
        "provenance": {"basis_refs": []},
    }
    right = {
        **left,
        "claim_id": "claim.b",
        "value": 375000,
        "unit": "USD",
    }
    with pytest.raises(project_claim_conflicts.ProjectClaimConflictError, match="integrity violation"):
        project_claim_conflicts._build_candidate(left, right)


def test_internal_persistence_rebinds_exact_active_claims_and_is_idempotent(conn) -> None:
    project = _project(conn)
    effective = "2026-09-01T00:00:00+00:00"
    _claim(conn, project["project_id"], value=350000, effective_at=effective)
    _claim(conn, project["project_id"], value=375000, effective_at=effective)
    candidate = project_claim_conflicts.detect_project_claim_conflicts(
        conn, project["project_id"]
    )[0]

    first = project_claim_conflicts._persist_candidate(
        conn,
        candidate=candidate,
        submitted_by="system:conflict-detector-test",
    )
    replay = project_claim_conflicts._persist_candidate(
        conn,
        candidate=candidate,
        submitted_by="system:conflict-detector-test",
    )
    assert replay["conflict_candidate_id"] == first["conflict_candidate_id"]
    assert replay["candidate"] == candidate
    assert project_claim_conflicts.get_candidate(
        conn, candidate["conflict_candidate_id"]
    )["candidate"] == candidate
    assert len(project_claim_conflicts.list_project_candidates(
        conn, project["project_id"]
    )) == 1

    forged = copy.deepcopy(candidate)
    forged["classification"] = "temporal_ambiguity"
    with pytest.raises(
        project_claim_conflicts.ProjectClaimConflictError,
        match="exact current detector result",
    ):
        project_claim_conflicts._persist_candidate(
            conn,
            candidate=forged,
            submitted_by="system:conflict-detector-test",
        )


def test_persisted_candidate_remains_reconstructible_after_bound_claim_is_superseded(conn) -> None:
    project = _project(conn)
    first = _claim(conn, project["project_id"], value=350000)
    _claim(conn, project["project_id"], value=375000)
    candidate = project_claim_conflicts.detect_project_claim_conflicts(
        conn, project["project_id"]
    )[0]
    project_claim_conflicts._persist_candidate(
        conn,
        candidate=candidate,
        submitted_by="system:conflict-detector-test",
    )

    _claim(
        conn,
        project["project_id"],
        value=360000,
        supersedes=first["claim_id"],
    )

    # Historical readability comes from immutable Claim references, not duplicated snapshots.
    assert project_claim_conflicts.get_candidate(
        conn, candidate["conflict_candidate_id"]
    )["candidate"] == candidate


def test_conflict_candidate_persistence_is_append_only(conn) -> None:
    project = _project(conn)
    _claim(conn, project["project_id"], value=350000)
    _claim(conn, project["project_id"], value=375000)
    candidate = project_claim_conflicts.detect_project_claim_conflicts(
        conn, project["project_id"]
    )[0]
    project_claim_conflicts._persist_candidate(
        conn,
        candidate=candidate,
        submitted_by="system:conflict-detector-test",
    )

    with pytest.raises(Exception, match="append-only"):
        with conn.transaction():
            conn.execute(
                "UPDATE agency_project_claim_conflict_candidates SET submitted_by='human:x' "
                "WHERE conflict_candidate_id=%s",
                (candidate["conflict_candidate_id"],),
            )

    with pytest.raises(Exception, match="append-only"):
        with conn.transaction():
            conn.execute(
                "DELETE FROM agency_project_claim_conflict_candidates WHERE conflict_candidate_id=%s",
                (candidate["conflict_candidate_id"],),
            )


def test_limitations_state_the_scalar_scope_to_the_consumer() -> None:
    """An empty candidate list must not read as "nothing contradicts".

    `SCAN_SCOPE` states the scalar restriction as configuration. `LIMITATIONS` is
    what actually travels to a consumer with every candidate, so the restriction
    belongs there too: the detector never looks at geometric or relational
    Claims, and a reader has no other way to learn that from the output.

    Deliberately module-level rather than candidate-level: the guarantee is a
    property of the detector, and this must hold where no database is available.
    """

    limitations = " ".join(project_claim_conflicts.LIMITATIONS)
    assert "scalar Claim values only" in limitations
    assert "geometric and relational" in limitations
    assert project_claim_conflicts.SCAN_SCOPE == "active_unsuperseded_scalar_claims"


def test_p3_exposes_detection_but_no_public_persistence_entry_point() -> None:
    assert callable(project_claim_conflicts.detect_project_claim_conflicts)
    assert not hasattr(project_claim_conflicts, "persist_candidate")
