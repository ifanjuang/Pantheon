"""PostgreSQL acceptance tests for Agency Data directory projections."""

from __future__ import annotations

import uuid

import pytest

from mvp_vertical import agency_data, agency_directory


@pytest.fixture
def conn():
    try:
        connection = agency_data.connect()
    except Exception as exc:  # pragma: no cover - local unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(
        "TRUNCATE agency_project_events, agency_people, agency_organizations, "
        "agency_projects RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def test_people_and_organizations_are_optional_directory_sources(conn) -> None:
    project = agency_data.create_project(
        conn,
        project_id=_id("project"),
        code="VERGER",
        display_name="Verger",
        contacts=[
            {
                "group": "Bureaux d’études",
                "name": "Hélène Durand",
                "organization": "BET Exemple",
                "role": "BET STRUCTURE",
            }
        ],
        actor="human-reviewer",
        actor_kind="human",
        idempotency_key=_id("create"),
    )
    person_id = _id("person")
    organization_id = _id("organization")
    conn.execute(
        """
        INSERT INTO agency_people (
            person_id, display_name, email, phone, created_by, updated_by
        ) VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (person_id, "Hélène Durand", "helene@example.test", "0600000000", "human", "human"),
    )
    conn.execute(
        """
        INSERT INTO agency_organizations (
            organization_id, name, email, siret, created_by, updated_by
        ) VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (organization_id, "BET Exemple", "bet@example.test", "12345678900000", "human", "human"),
    )
    conn.commit()

    people = agency_directory.list_people(conn, query="helene")
    assert people[0]["person_id"] == person_id
    assert agency_directory.get_person(conn, person_id)["owner_system"] == "postgres"

    organizations = agency_directory.list_organizations(conn, query="123456789")
    assert organizations[0]["organization_id"] == organization_id
    assert agency_directory.get_organization(conn, organization_id)["owner_system"] == "postgres"

    stored_project = agency_data.get_project(conn, project["project_id"])
    assert stored_project["contacts"] == [
        {
            "group": "Bureaux d’études",
            "name": "Hélène Durand",
            "organization": "BET Exemple",
            "role": "BET STRUCTURE",
        }
    ]


def test_directory_limit_is_bounded(conn) -> None:
    with pytest.raises(agency_directory.AgencyDirectoryError, match="between 1 and 500"):
        agency_directory.list_people(conn, limit=501)
    with pytest.raises(agency_directory.AgencyDirectoryError, match="between 1 and 500"):
        agency_directory.list_organizations(conn, limit=0)
