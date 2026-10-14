from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from mvp_vertical import (
    agency_change_candidate_review,
    agency_change_candidates,
    agency_data,
)


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


@pytest.fixture
def conn():
    try:
        connection = agency_data.connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    agency_change_candidate_review.ensure_schema(connection)
    connection.execute(
        "TRUNCATE agency_change_candidate_events, agency_change_candidates, "
        "agency_project_events, agency_projects RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.execute(
        "TRUNCATE agency_change_candidate_events, agency_change_candidates, "
        "agency_project_events, agency_projects RESTART IDENTITY CASCADE"
    )
    connection.commit()
    connection.close()


def _candidate(conn) -> tuple[dict, dict]:
    project = agency_data.create_project(
        conn,
        project_id=_id("project"),
        code=_id("REV")[:24],
        display_name="Projet en revue",
        actor="human",
        actor_kind="human",
        idempotency_key=_id("project-create"),
        attributes={"programme_summary": "Maison individuelle"},
    )
    candidate = agency_change_candidates.create_project_candidate(
        conn,
        project_id=project["project_id"],
        base_revision=project["revision"],
        proposed_attributes={
            "programme_summary": "Maison individuelle avec piscine",
            "agency_notes": "Local technique à préciser",
        },
        proposer="hermes-reviewer",
        proposer_kind="hermes",
        reason="Programme complété",
        source_refs=["document://programme/A02"],
        idempotency_key=_id("candidate"),
    )
    return project, candidate


def test_revision_request_records_structured_annotations_without_project_mutation(conn) -> None:
    project, candidate = _candidate(conn)
    idempotency_key = _id("revision-request")

    review = agency_change_candidate_review.request_project_candidate_revision(
        conn,
        candidate_id=candidate["candidate_id"],
        actor="architecte",
        annotations=[
            {
                "annotation_type": "source_required",
                "field": "programme_summary",
                "message": "Joindre la dernière validation écrite du maître d’ouvrage.",
                "source_refs": ["mail://client/2026-08-04"],
            },
            {
                "annotation_type": "question",
                "field": "agency_notes",
                "message": "Le local technique est-il inclus dans l’emprise annoncée ?",
                "source_refs": [],
            },
        ],
        note="Réviser la proposition sans modifier les autres champs.",
        idempotency_key=idempotency_key,
    )

    reviewed = review["change_candidate"]
    assert reviewed["status"] == "revision_requested"
    assert reviewed["base_revision"] == project["revision"]
    assert reviewed["decision_note"] == "Réviser la proposition sans modifier les autres champs."
    assert [item["annotation_type"] for item in reviewed["review_annotations"]] == [
        "source_required",
        "question",
    ]
    assert review["review_events"][-1]["event_type"] == "revision_requested"
    assert review["review_events"][-1]["payload"]["project_mutated"] is False
    assert review["review_events"][-1]["payload"]["task_authorized"] is False
    assert review["review_events"][-1]["payload"]["evidence_admitted"] is False

    current = agency_data.get_project(conn, project["project_id"])
    assert current["revision"] == project["revision"]
    assert current["attributes"] == project["attributes"]

    replayed = agency_change_candidate_review.request_project_candidate_revision(
        conn,
        candidate_id=candidate["candidate_id"],
        actor="architecte",
        annotations=[
            {
                "annotation_type": "source_required",
                "field": "programme_summary",
                "message": "Cette charge utile n’est pas réévaluée lors du replay.",
                "source_refs": [],
            }
        ],
        idempotency_key=idempotency_key,
    )
    assert replayed["change_candidate"]["status"] == "revision_requested"
    assert len([event for event in replayed["review_events"] if event["event_type"] == "revision_requested"]) == 1


def test_revision_requested_candidate_cannot_be_applied_rejected_or_reviewed_twice(conn) -> None:
    _, candidate = _candidate(conn)
    agency_change_candidate_review.request_project_candidate_revision(
        conn,
        candidate_id=candidate["candidate_id"],
        actor="architecte",
        annotations=[
            {
                "annotation_type": "contradiction",
                "field": "programme_summary",
                "message": "Le programme proposé contredit le dernier compte rendu.",
                "source_refs": ["information://cr/12"],
            }
        ],
        idempotency_key=_id("revision-request"),
    )

    with pytest.raises(agency_change_candidates.ChangeCandidateConflict):
        agency_change_candidates.apply_project_candidate(
            conn,
            candidate_id=candidate["candidate_id"],
            actor="architecte",
            idempotency_key=_id("apply"),
        )
    with pytest.raises(agency_change_candidates.ChangeCandidateConflict):
        agency_change_candidates.reject_project_candidate(
            conn,
            candidate_id=candidate["candidate_id"],
            actor="architecte",
            reason="Refus tardif",
            idempotency_key=_id("reject"),
        )
    with pytest.raises(agency_change_candidate_review.ChangeCandidateReviewConflict):
        agency_change_candidate_review.request_project_candidate_revision(
            conn,
            candidate_id=candidate["candidate_id"],
            actor="architecte",
            annotations=[
                {
                    "annotation_type": "question",
                    "field": None,
                    "message": "Deuxième demande concurrente",
                    "source_refs": [],
                }
            ],
            idempotency_key=_id("revision-request-two"),
        )


def test_revision_review_event_remains_append_only(conn) -> None:
    _, candidate = _candidate(conn)
    agency_change_candidate_review.request_project_candidate_revision(
        conn,
        candidate_id=candidate["candidate_id"],
        actor="architecte",
        annotations=[
            {
                "annotation_type": "needs_deeper_review",
                "field": None,
                "message": "Vérifier les conséquences sur le sommaire du programme.",
                "source_refs": [],
            }
        ],
        idempotency_key=_id("revision-request"),
    )
    event_id = conn.execute(
        "SELECT event_id FROM agency_change_candidate_events "
        "WHERE candidate_id=%s AND event_type='revision_requested'",
        (candidate["candidate_id"],),
    ).fetchone()[0]
    with pytest.raises(Exception, match="append-only"):
        conn.execute(
            "UPDATE agency_change_candidate_events SET actor='x' WHERE event_id=%s",
            (event_id,),
        )
    conn.rollback()


def test_review_api_is_human_only_and_keeps_non_authority_flags() -> None:
    root = Path(__file__).resolve().parents[1]
    api = (root / "mvp_vertical" / "agency_change_candidate_review_api.py").read_text(encoding="utf-8")
    composed = (root / "mvp_vertical" / "agency_change_candidate_api.py").read_text(encoding="utf-8")

    assert '/agency/change-candidates/{candidate_id}' in api
    assert '/agency/change-candidates/{candidate_id}/request-revision' in api
    assert "require_human_writer" in api
    assert '"project_mutated": False' in api
    assert '"execution_authorized": False' in api
    assert '"task_authorized": False' in api
    assert '"evidence_admitted": False' in api
    assert "runs/start" not in api
    assert "install_agency_change_candidate_review_routes" in composed
