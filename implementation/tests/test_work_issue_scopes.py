"""PostgreSQL acceptance tests for aggregate-owned WorkIssue scopes."""

from __future__ import annotations

import uuid

import psycopg
import pytest

from mvp_vertical import agency_data, store, work_issue_scopes, work_issues


@pytest.fixture
def conn():
    try:
        connection = store.connect()
    except Exception as exc:  # pragma: no cover - local unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(work_issues.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(agency_data.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(work_issue_scopes.MIGRATION.read_text(encoding="utf-8"))
    connection.execute(
        """
        TRUNCATE work_issue_scope_events, work_issue_scope_links,
                 issue_events, hermes_runs, issue_comments, work_card_metadata,
                 work_issues, agency_information_cards, agency_people,
                 agency_organizations, agency_projects
        RESTART IDENTITY CASCADE
        """
    )
    connection.commit()
    yield connection
    connection.close()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _project(conn, project_id: str = "project-alpha") -> str:
    conn.execute(
        """
        INSERT INTO agency_projects (
            project_id, code, display_name, created_by, updated_by
        ) VALUES (%s, %s, %s, 'human', 'human')
        """,
        (project_id, project_id.upper(), "Projet Alpha"),
    )
    conn.commit()
    return project_id


def _information(conn, project_id: str, information_id: str = "information-alpha") -> str:
    conn.execute(
        """
        INSERT INTO agency_information_cards (
            information_id, series_id, project_id, title, category,
            source_type, source_note, index_label, status
        ) VALUES (%s, %s, %s, 'Note projet', 'note', 'draft',
                  'Texte source', 'A01', 'draft')
        """,
        (information_id, f"series-{information_id}", project_id),
    )
    conn.commit()
    return information_id


def _create_scoped(conn, *, scopes: list[dict], issue_id: str | None = None) -> dict:
    return work_issue_scopes.create_scoped_issue(
        conn,
        issue_id=issue_id or _id("issue"),
        case_ref="project-alpha",
        title="Vérifier le devis structure",
        description="Comparer le devis aux pièces du projet.",
        created_by="human-reviewer",
        idempotency_key=_id("create"),
        scopes=scopes,
    )


def test_same_work_issue_is_projected_from_project_and_information(conn) -> None:
    project_id = _project(conn)
    information_id = _information(conn, project_id)
    issue_id = _id("issue")
    projection = _create_scoped(
        conn,
        issue_id=issue_id,
        scopes=[
            {
                "scope_link_id": _id("scope-project"),
                "entity_type": "project",
                "entity_id": project_id,
                "scope_role": "primary",
            },
            {
                "scope_link_id": _id("scope-information"),
                "entity_type": "information",
                "entity_id": information_id,
                "scope_role": "related",
            },
        ],
    )

    assert projection["work_issue"]["issue_id"] == issue_id
    assert len(projection["scope_links"]) == 2
    assert projection["scope_is_not_authorization"] is True

    project_view = work_issue_scopes.list_scoped_issue_projections(
        conn,
        entity_type="project",
        entity_id=project_id,
    )
    information_view = work_issue_scopes.list_scoped_issue_projections(
        conn,
        entity_type="information",
        entity_id=information_id,
    )
    assert [item["work_issue"]["issue_id"] for item in project_view] == [issue_id]
    assert [item["work_issue"]["issue_id"] for item in information_view] == [issue_id]


def test_agency_scope_needs_no_project(conn) -> None:
    projection = work_issue_scopes.create_scoped_issue(
        conn,
        issue_id=_id("issue"),
        case_ref="agency:agency",
        title="Mettre à jour le modèle de courrier",
        description="Tâche interne à l’agence sans Projet associé.",
        created_by="human-reviewer",
        idempotency_key=_id("create"),
        scopes=[
            {
                "scope_link_id": _id("scope-agency"),
                "entity_type": "agency",
                "entity_id": "agency",
                "scope_role": "primary",
            }
        ],
    )
    assert projection["scope_links"][0]["scope_ref"] == {
        "entity_type": "agency",
        "entity_id": "agency",
    }


def test_unknown_endpoint_is_refused_without_persisting_issue(conn) -> None:
    issue_id = _id("issue")
    with pytest.raises(work_issue_scopes.WorkIssueScopeError):
        _create_scoped(
            conn,
            issue_id=issue_id,
            scopes=[
                {
                    "scope_link_id": _id("scope-project"),
                    "entity_type": "project",
                    "entity_id": "missing-project",
                    "scope_role": "primary",
                }
            ],
        )
    with pytest.raises(work_issues.IssueNotFound):
        work_issues.get_issue(conn, issue_id)


def test_unknown_decision_record_is_refused_without_persisting_issue(conn) -> None:
    issue_id = _id("issue")
    with pytest.raises(
        work_issue_scopes.WorkIssueScopeError,
        match="unknown WorkIssue scope endpoint: decision",
    ):
        _create_scoped(
            conn,
            issue_id=issue_id,
            scopes=[
                {
                    "scope_link_id": _id("scope-decision"),
                    "entity_type": "decision",
                    "entity_id": "decision-missing",
                    "scope_role": "primary",
                }
            ],
        )
    with pytest.raises(work_issues.IssueNotFound):
        work_issues.get_issue(conn, issue_id)


def test_scope_effects_are_idempotent_and_versioned(conn) -> None:
    project_id = _project(conn)
    projection = _create_scoped(
        conn,
        scopes=[
            {
                "scope_link_id": "scope-primary",
                "entity_type": "project",
                "entity_id": project_id,
                "scope_role": "primary",
            }
        ],
    )
    issue = projection["work_issue"]
    key = _id("scope-add")
    first = work_issue_scopes.add_scope(
        conn,
        issue_id=issue["issue_id"],
        scope_link_id="scope-agency-related",
        entity_type="agency",
        entity_id="agency",
        scope_role="related",
        actor="human-reviewer",
        expected_version=issue["version"],
        idempotency_key=key,
    )
    replay = work_issue_scopes.add_scope(
        conn,
        issue_id=issue["issue_id"],
        scope_link_id="scope-agency-related",
        entity_type="agency",
        entity_id="agency",
        scope_role="related",
        actor="human-reviewer",
        expected_version=issue["version"],
        idempotency_key=key,
    )
    assert replay["work_issue"]["version"] == first["work_issue"]["version"]
    assert len(replay["scope_links"]) == 2
    assert len(replay["scope_events"]) == len(first["scope_events"])


def test_primary_scope_is_replaced_atomically(conn) -> None:
    first_project = _project(conn, "project-alpha")
    second_project = _project(conn, "project-beta")
    projection = _create_scoped(
        conn,
        scopes=[
            {
                "scope_link_id": "scope-primary-alpha",
                "entity_type": "project",
                "entity_id": first_project,
                "scope_role": "primary",
            }
        ],
    )
    replaced = work_issue_scopes.replace_primary_scope(
        conn,
        issue_id=projection["work_issue"]["issue_id"],
        current_scope_link_id="scope-primary-alpha",
        replacement_scope_link_id="scope-primary-beta",
        entity_type="project",
        entity_id=second_project,
        actor="human-reviewer",
        expected_version=projection["work_issue"]["version"],
        idempotency_key=_id("replace-primary"),
    )
    active_primary = [
        link
        for link in replaced["scope_links"]
        if link["scope_role"] == "primary" and link.get("retired_at") is None
    ]
    assert len(active_primary) == 1
    assert active_primary[0]["scope_ref"]["entity_id"] == second_project
    assert replaced["scope_events"][-1]["event_type"] == "primary_scope_replaced"


def test_scope_links_and_events_keep_history(conn) -> None:
    project_id = _project(conn)
    projection = _create_scoped(
        conn,
        scopes=[
            {
                "scope_link_id": "scope-primary",
                "entity_type": "project",
                "entity_id": project_id,
                "scope_role": "primary",
            },
            {
                "scope_link_id": "scope-related",
                "entity_type": "agency",
                "entity_id": "agency",
                "scope_role": "related",
            },
        ],
    )
    retired = work_issue_scopes.retire_scope(
        conn,
        issue_id=projection["work_issue"]["issue_id"],
        scope_link_id="scope-related",
        actor="human-reviewer",
        expected_version=projection["work_issue"]["version"],
        idempotency_key=_id("retire"),
    )
    assert any(link["scope_link_id"] == "scope-related" for link in retired["scope_links"])

    with pytest.raises(psycopg.errors.RaiseException, match="retire instead of deleting"):
        conn.execute(
            "DELETE FROM work_issue_scope_links WHERE scope_link_id = 'scope-related'"
        )
    conn.rollback()
    event_id = retired["scope_events"][-1]["event_id"]
    with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
        conn.execute(
            "UPDATE work_issue_scope_events SET actor = 'rewritten' WHERE event_id = %s",
            (event_id,),
        )
    conn.rollback()
