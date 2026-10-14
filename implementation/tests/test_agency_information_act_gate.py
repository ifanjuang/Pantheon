"""The chokepoint on `act_working_information`.

This is the last of the five entry points recorded as `gate_required_not_wired`
in the consequential-mutation inventory. It was already correctly guarded on
everything the module could check locally — actor_kind, the row lock, the
working-status check, expected_revision — and the route already resolved a
real caller identity (`X-Pantheon-Actor`, via `require_agency_actor`). It
discarded that identity as `_actor` rather than recording it anywhere: the
table has no actor column, so nothing survived the write to say who acted the
version. The chokepoint's decision record is where that identity now lives.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest

from mvp_vertical import agency_data, agency_information
from mvp_vertical.policy_gate import StandInPolicyClient


class _UnreachablePolicyClient:
    def preflight(self, candidate):
        raise RuntimeError("decision point unreachable")

    def validate_decision(self, payload):  # pragma: no cover - never reached
        raise AssertionError("validation must not be attempted after a failed preflight")


@pytest.fixture
def conn():
    try:
        connection = agency_data.connect()
    except Exception as exc:  # pragma: no cover - local unit-only lane
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


def _decision_payload(
    conn,
    *,
    information_id: str,
    project_id: str,
    decision_id: str,
    decided_by: str = "architecte",
) -> dict:
    working = agency_information.get_information_context(conn, information_id)["current"]
    content_digest = agency_information._digest(
        {
            key: value
            for key, value in working.items()
            if key not in {"status", "acted_at", "revision", "updated_at"}
        }
    )
    return {
        "decision": {
            "decision_id": decision_id,
            "decided_by": decided_by,
            "approval_level": "C2",
            "scope": {"scope_type": "project", "scope_id": project_id},
            "object_identity": f"agency_information:{information_id}",
            "content_digest": content_digest,
            "expires_at": "2099-01-01T00:00:00Z",
            "signature": "signed-canonical-decision",
        }
    }


def test_acting_needs_no_decision_point_when_enforcement_is_off(conn) -> None:
    """policy_client defaults to None: existing direct callers are unchanged."""
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


def test_acting_is_refused_without_a_decision_reference(conn) -> None:
    project = _project(conn)
    draft = _draft(conn, project["project_id"])
    with pytest.raises(agency_information.AgencyInformationGateRefused, match="decision_payload.decision"):
        agency_information.act_working_information(
            conn,
            information_id=draft["information_id"],
            expected_revision=1,
            actor_kind="human",
            actor="architecte",
            policy_client=StandInPolicyClient(),
            # no decision_payload: nothing to bind the act to
        )
    unchanged = agency_information.get_information_context(conn, draft["information_id"])
    assert unchanged["current"]["status"] in agency_information.WORKING_STATUSES


def test_an_allowed_act_carries_the_content_digest_to_the_decision_point(conn) -> None:
    project = _project(conn)
    draft = _draft(conn, project["project_id"])
    client = StandInPolicyClient()

    acted = agency_information.act_working_information(
        conn,
        information_id=draft["information_id"],
        expected_revision=1,
        actor_kind="human",
        actor="architecte",
        policy_client=client,
        decision_payload=_decision_payload(conn, information_id=draft["information_id"], project_id=project["project_id"], decision_id="decision-1"),
    )
    assert acted["status"] == "acted"

    expectation = client.last_decision["expectation"]
    assert expectation["object_identity"] == f"agency_information:{draft['information_id']}"
    assert expectation["required_scope"] == {
        "scope_type": "project",
        "scope_id": project["project_id"],
    }
    decision = client.last_decision["decision"]
    assert decision["decided_by"] == "architecte"


def test_the_act_is_declared_to_the_decision_point_as_a_local_state_write(conn) -> None:
    """The policy facts must be stated, not left to the transport's defaults.

    `build_preflight_payload` keeps only the fields the policy transport
    declares and defaults `external_effect` to True for anything it is not
    told about. The first version of this gate put domain identifiers in
    `request`; they were dropped, `external_effect` defaulted to True, and
    the PDP classified acting an Information version as K4 (reaching outside
    Pantheon, ceiling C3) instead of K3/C2. It sends nothing outward.
    """
    project = _project(conn)
    draft = _draft(conn, project["project_id"])
    client = StandInPolicyClient()

    agency_information.act_working_information(
        conn,
        information_id=draft["information_id"],
        expected_revision=1,
        actor_kind="human",
        actor="architecte",
        policy_client=client,
        decision_payload=_decision_payload(conn, information_id=draft["information_id"], project_id=project["project_id"], decision_id="decision-6"),
    )

    request = client.last_preflight["request"]
    assert request["intent"] == "act_working_information"
    assert request["external_effect"] is False, (
        "acting an Information version supersedes one row and promotes another, "
        "both local; declaring an external effect inflates it to K4"
    )
    assert request["writes_state"] is True
    assert request["transmission_requested"] is False
    assert request["memory_promotion_requested"] is False
    assert request["scope"] == {
        "scope_type": "project",
        "scope_id": project["project_id"],
    }


def test_a_refused_act_leaves_the_version_working_and_retryable(conn) -> None:
    project = _project(conn)
    draft = _draft(conn, project["project_id"])
    client = StandInPolicyClient(disposition="blocked_missing_task_contract")

    with pytest.raises(agency_information.AgencyInformationGateRefused):
        agency_information.act_working_information(
            conn,
            information_id=draft["information_id"],
            expected_revision=1,
            actor_kind="human",
            actor="architecte",
            policy_client=client,
            decision_payload=_decision_payload(conn, information_id=draft["information_id"], project_id=project["project_id"], decision_id="decision-2"),
        )
    unchanged = agency_information.get_information_context(conn, draft["information_id"])
    assert unchanged["current"]["status"] in agency_information.WORKING_STATUSES
    assert unchanged["current"]["revision"] == 1, (
        "a refusal is not the same as staleness; the version must remain "
        "retryable at the same revision once a real decision exists"
    )


def test_an_unreachable_decision_point_fails_closed(conn) -> None:
    project = _project(conn)
    draft = _draft(conn, project["project_id"])
    with pytest.raises(agency_information.AgencyInformationGatePolicyUnavailable):
        agency_information.act_working_information(
            conn,
            information_id=draft["information_id"],
            expected_revision=1,
            actor_kind="human",
            actor="architecte",
            policy_client=_UnreachablePolicyClient(),
            decision_payload=_decision_payload(conn, information_id=draft["information_id"], project_id=project["project_id"], decision_id="decision-3"),
        )
    unchanged = agency_information.get_information_context(conn, draft["information_id"])
    assert unchanged["current"]["status"] in agency_information.WORKING_STATUSES


def test_the_content_digest_changes_with_the_content(conn) -> None:
    """Two different drafts must not collide on the same decision reference."""
    project = _project(conn)
    first = _draft(conn, project["project_id"])
    second = agency_information.update_working_information(
        conn,
        information_id=_draft(conn, project["project_id"])["information_id"],
        changes={"summary": "Résumé distinct"},
        expected_revision=1,
        actor_kind="human",
    )
    client_a = StandInPolicyClient()
    client_b = StandInPolicyClient()

    agency_information.act_working_information(
        conn,
        information_id=first["information_id"],
        expected_revision=1,
        actor_kind="human",
        actor="architecte",
        policy_client=client_a,
        decision_payload=_decision_payload(conn, information_id=first["information_id"], project_id=project["project_id"], decision_id="decision-4"),
    )
    agency_information.act_working_information(
        conn,
        information_id=second["information_id"],
        expected_revision=second["revision"],
        actor_kind="human",
        actor="architecte",
        policy_client=client_b,
        decision_payload=_decision_payload(conn, information_id=second["information_id"], project_id=project["project_id"], decision_id="decision-5"),
    )
    digest_a = client_a.last_decision["expectation"]["expected_digest"]
    digest_b = client_b.last_decision["expectation"]["expected_digest"]
    assert digest_a != digest_b
