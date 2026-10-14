from __future__ import annotations

import json
from pathlib import Path

import pytest

from mvp_vertical import agency_claims, agency_data, agency_information, work_issues


FIXTURES = Path(__file__).parent / "fixtures" / "agency"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture
def agency_conn():
    try:
        conn = agency_data.connect()
    except Exception as exc:  # pragma: no cover - local unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    conn.execute(
        "TRUNCATE agency_project_claims, agency_information_cards, agency_project_events, "
        "agency_people, agency_organizations, agency_projects RESTART IDENTITY CASCADE"
    )
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def work_conn():
    try:
        conn = work_issues.connect()
    except Exception as exc:  # pragma: no cover - local unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    conn.execute(
        "TRUNCATE issue_comments, issue_events, hermes_runs, work_issues RESTART IDENTITY CASCADE"
    )
    conn.commit()
    yield conn
    conn.close()


def _create_project(conn, fixture: dict) -> dict:
    project = fixture["project"]
    return agency_data.create_project(
        conn,
        project_id=project["project_id"],
        code=project["code"],
        display_name=project["display_name"],
        status=project.get("status"),
        phase=project.get("phase"),
        location=project.get("location"),
        attributes=project.get("attributes") or {},
        actor="fixture.human",
        actor_kind="human",
        idempotency_key=f"fixture:{fixture['fixture_id']}:project:create",
    )


def _create_and_act_information(conn, project_id: str, item: dict) -> dict:
    draft = agency_information.create_information(
        conn,
        project_id=project_id,
        title=item["title"],
        category=item["category"],
        source_type=item["source_type"],
        source_ref=item.get("source_ref"),
        source_note=item.get("source_note"),
        source_version=item.get("source_version"),
        index_label=item["index_label"],
        summary=item.get("summary", ""),
        details=item.get("details", ""),
        limits=item.get("limits") or [],
        type_tags=item.get("type_tags") or [],
        subject_tags=item.get("subject_tags") or [],
        author=item.get("author"),
        actor_kind="human",
    )
    return agency_information.act_working_information(
        conn,
        information_id=draft["information_id"],
        expected_revision=draft["revision"],
        actor_kind="human",
        actor="architecte",
    )


def test_f01_project_claims_project_cleanly_without_bumping_project_revision(agency_conn) -> None:
    fixture = _load("f01_maison_neuve.json")
    project = _create_project(agency_conn, fixture)
    information_by_key: dict[str, dict] = {}

    needed = {
        claim["backing_information_key"]
        for claim in fixture["project_claims"]
        if claim.get("backing_information_key")
    }
    for item in fixture["information"]:
        if item["key"] in needed:
            information_by_key[item["key"]] = _create_and_act_information(
                agency_conn,
                project["project_id"],
                item,
            )

    for index, claim in enumerate(fixture["project_claims"], start=1):
        backing = information_by_key.get(claim.get("backing_information_key"))
        agency_claims.record_claim(
            agency_conn,
            project_id=project["project_id"],
            claim_type=claim["claim_type"],
            value=claim["value"],
            actor="fixture.human",
            source_kind="information" if backing else "human_assertion",
            backing_ref=(
                {
                    "entity_type": "information",
                    "entity_id": backing["information_id"],
                    "observed_status": backing["status"],
                }
                if backing
                else None
            ),
            source_ref=backing.get("source_ref") if backing else None,
            status=claim["status"],
            claim_id=f"claim.f01.{index}",
        )

    refreshed = agency_data.get_project(agency_conn, project["project_id"])

    assert refreshed["revision"] == 1
    assert refreshed["claim_values"]["plu_zone"] == "UDb"
    assert refreshed["claim_values"]["surface_projet"] == 312.11
    assert refreshed["claim_values"]["budget"] == 800000
    assert refreshed["claim_refs"]["plu_zone"]["backing_ref"]["entity_type"] == "information"
    assert refreshed["attributes"]["programme_summary"]
    assert "budget" not in refreshed["attributes"]


def test_f02_acted_and_working_information_coexist_without_index_drift(agency_conn) -> None:
    fixture = _load("f02_patrimoine_renovation.json")
    project = _create_project(agency_conn, fixture)
    source = next(item for item in fixture["information"] if item["key"] == "diagnostic-a01")
    target = next(item for item in fixture["information"] if item["key"] == "diagnostic-a02-working")

    acted = _create_and_act_information(agency_conn, project["project_id"], source)
    working = agency_information.derive_working_version(
        agency_conn,
        acted_information_id=acted["information_id"],
        new_index_label=target["index_label"],
        source_ref=target.get("source_ref"),
        source_note=target.get("source_note"),
        source_version=target.get("source_version"),
        actor_kind="human",
    )
    updated = agency_information.update_working_information(
        agency_conn,
        information_id=working["information_id"],
        changes={
            "summary": target["summary"],
            "details": target["details"],
            "limits": target["limits"],
            "type_tags": target["type_tags"],
            "subject_tags": target["subject_tags"],
            "status": "in_progress",
        },
        expected_revision=working["revision"],
        actor_kind="human",
    )
    context = agency_information.get_information_context(agency_conn, updated["information_id"])

    assert context["last_acted"]["information_id"] == acted["information_id"]
    assert context["last_acted"]["status"] == "acted"
    assert context["last_acted"]["index_label"] == "A01"
    assert context["current"]["status"] == "in_progress"
    assert context["current"]["index_label"] == "A02"
    assert context["working_assumptions_are_not_acted"] is True


def test_f03_work_review_requires_a_distinct_human_close(work_conn) -> None:
    fixture = _load("f03_chantier_reserves.json")
    item = next(work for work in fixture["work"] if work["id"] == "work-reponse-client")

    created = work_issues.create_issue(
        work_conn,
        issue_id=item["id"],
        case_ref=fixture["project"]["project_id"],
        title=item["title"],
        description=item["objective"],
        created_by="fixture.human",
        idempotency_key="fixture:f03:work:create",
        issue_type="drafting",
        requested_effect=item["requested_effect"],
    )
    in_progress = work_issues.transition_issue(
        work_conn,
        issue_id=item["id"],
        to_status="in_progress",
        actor="fixture.human",
        actor_kind="human",
        expected_version=created["work_issue"]["version"],
        idempotency_key="fixture:f03:work:start",
    )
    review = work_issues.transition_issue(
        work_conn,
        issue_id=item["id"],
        to_status="review",
        actor="fixture.human",
        actor_kind="human",
        expected_version=in_progress["work_issue"]["version"],
        idempotency_key="fixture:f03:work:review",
    )

    assert review["work_issue"]["status"] == "review"
    assert "close_reason" not in review["work_issue"]

    closed = work_issues.close_issue(
        work_conn,
        issue_id=item["id"],
        decided_by="fixture.human",
        close_reason="answered",
        expected_version=review["work_issue"]["version"],
        idempotency_key="fixture:f03:work:close",
    )

    assert closed["work_issue"]["status"] == "done"
    assert closed["work_issue"]["close_reason"] == "answered"
    assert any(event["event_type"] == "issue_closed" for event in closed["events"])
