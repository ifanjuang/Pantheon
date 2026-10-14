from __future__ import annotations

import uuid
from datetime import date

import pytest

from mvp_vertical import agency_data, agency_information


@pytest.fixture
def conn():
    try:
        connection = agency_data.connect()
    except Exception as exc:  # pragma: no cover - local unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(
        "TRUNCATE agency_information_cards, agency_project_events, agency_people, "
        "agency_organizations, agency_projects RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _project(conn) -> dict:
    return agency_data.create_project(
        conn,
        project_id=_id("project"),
        code=_id("INFO")[:24],
        display_name="Projet Information",
        actor="human",
        actor_kind="human",
        idempotency_key=_id("create"),
    )


def _draft(conn, project_id: str) -> dict:
    return agency_information.create_information(
        conn,
        project_id=project_id,
        title="PLU — Zone UDb",
        category="PLU",
        source_type="document",
        source_ref="paperless://doc/42",
        source_version="1",
        index_label="REV-C / 03",
        information_date=date(2026, 8, 12),
        summary="Résumé initial",
        details="Détails initiaux",
        limits=["consultatif"],
        type_tags=["etude"],
        subject_tags=["urbanisme"],
        author="Commune",
        actor_kind="human",
    )


def test_working_edits_keep_same_source_index(conn) -> None:
    project = _project(conn)
    draft = _draft(conn, project["project_id"])

    updated = agency_information.update_working_information(
        conn,
        information_id=draft["information_id"],
        changes={"summary": "Résumé développé", "details": "Détails développés"},
        expected_revision=1,
        actor_kind="human",
    )

    assert updated["index_label"] == "REV-C / 03"
    assert updated["revision"] == 2
    assert updated["summary"] == "Résumé développé"
    assert updated["created_at"] == draft["created_at"]
    assert updated["information_date"] == draft["information_date"] == "2026-08-12"
    assert updated["updated_at"] >= draft["updated_at"]


def test_hermes_needs_admitted_capability_to_edit_working_information(conn) -> None:
    project = _project(conn)
    draft = _draft(conn, project["project_id"])

    with pytest.raises(agency_information.InformationGateRequired, match="admitted bounded capability"):
        agency_information.update_working_information(
            conn,
            information_id=draft["information_id"],
            changes={"details": "Développement Hermes"},
            expected_revision=1,
            actor_kind="hermes",
        )

    updated = agency_information.update_working_information(
        conn,
        information_id=draft["information_id"],
        changes={"details": "Développement Hermes admis"},
        expected_revision=1,
        actor_kind="hermes",
        hermes_admitted=True,
    )
    assert updated["details"] == "Développement Hermes admis"
    assert updated["index_label"] == "REV-C / 03"


def test_acted_information_is_immutable_and_next_source_derives_from_it(conn) -> None:
    project = _project(conn)
    draft = _draft(conn, project["project_id"])

    acted = agency_information.act_working_information(
        conn,
        information_id=draft["information_id"],
        expected_revision=1,
        actor_kind="human",
        actor="architecte",
    )
    assert acted["status"] == "acted"
    assert acted["acted_at"]

    with pytest.raises(agency_information.ImmutableActedInformation):
        agency_information.update_working_information(
            conn,
            information_id=acted["information_id"],
            changes={"summary": "Réécriture interdite"},
            expected_revision=acted["revision"],
            actor_kind="human",
        )

    working = agency_information.derive_working_version(
        conn,
        acted_information_id=acted["information_id"],
        new_index_label="Indice B2 — VISA",
        source_ref="paperless://doc/43",
        source_note=None,
        source_version="2",
        actor_kind="human",
    )

    assert working["status"] == "draft"
    assert working["index_label"] == "Indice B2 — VISA"
    assert working["base_acted_id"] == acted["information_id"]
    assert working["previous_source_id"] == acted["information_id"]
    assert working["summary"] == acted["summary"]

    context = agency_information.get_information_context(conn, working["information_id"])
    assert context["current"]["information_id"] == working["information_id"]
    assert context["last_acted"]["information_id"] == acted["information_id"]
    assert context["working_assumptions_are_not_acted"] is True


def test_acting_next_source_archives_previous_acted_version(conn) -> None:
    project = _project(conn)
    first = _draft(conn, project["project_id"])
    acted_first = agency_information.act_working_information(
        conn,
        information_id=first["information_id"],
        expected_revision=1,
        actor_kind="human",
        actor="architecte",
    )
    second = agency_information.derive_working_version(
        conn,
        acted_information_id=acted_first["information_id"],
        new_index_label="B2 / EXE",
        source_ref="paperless://doc/43",
        source_note=None,
        actor_kind="human",
    )
    acted_second = agency_information.act_working_information(
        conn,
        information_id=second["information_id"],
        expected_revision=1,
        actor_kind="human",
        actor="architecte",
    )

    previous = conn.execute(
        "SELECT status, revision, updated_at FROM agency_information_cards WHERE information_id = %s",
        (acted_first["information_id"],),
    ).fetchone()
    assert previous[0] == "superseded"
    assert previous[1] == acted_first["revision"] + 1
    assert previous[2].isoformat() >= acted_first["updated_at"]
    assert acted_second["status"] == "acted"
    assert acted_second["revision"] == 2
