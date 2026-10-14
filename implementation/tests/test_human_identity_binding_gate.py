"""The chokepoint on the act that makes an external identity a governed principal.

`bind_oidc_identity` writes the row `resolve_principal_context` resolves every
authenticated request against. It is the root of trust for the whole principal
regime, and until now nothing in production called it at all.

It is not authorized by a grant, and that is deliberate rather than missing:
`033_human_project_access_management.sql` states that `project.access.manage`
carries no IdP invitation authority and remains a locally provisioned bootstrap
capability, and `human_resource_grants.project_id` is NOT NULL against
`agency_projects`, so the table cannot express a system-wide permission. A
project-scoped grant minting a system-wide identity would be an escalation.

So the authority is the chokepoint, and the decision must cover the exact
binding rather than name it.
"""

from __future__ import annotations

import uuid

import pytest

from mvp_vertical import human_access
from mvp_vertical.policy_gate import StandInPolicyClient


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


class _UnreachablePolicyClient:
    def preflight(self, candidate):
        raise RuntimeError("decision point unreachable")

    def validate_decision(self, payload):  # pragma: no cover - never reached
        raise AssertionError("validation must not be attempted after a failed preflight")


def test_the_digest_covers_the_binding_and_nothing_else() -> None:
    """A decision bound to a name is worth less than one bound to a content."""
    base = {"principal_ref": "human:a", "issuer": "https://idp", "subject": "sub-1"}
    digest = human_access.binding_digest(**base)

    assert digest == human_access.binding_digest(**base), "the digest must be stable"
    for field, other in (
        ("principal_ref", "human:b"),
        ("issuer", "https://other-idp"),
        ("subject", "sub-2"),
    ):
        assert human_access.binding_digest(**{**base, field: other}) != digest, (
            f"changing {field} must change the digest the decision has to cover"
        )
    assert (
        human_access.binding_digest(**base, valid_until="2027-01-01T00:00:00Z") != digest
    ), "a bounded binding is not the same binding as an unbounded one"


@pytest.fixture
def conn():
    try:
        connection = human_access.connect()
    except Exception as exc:  # pragma: no cover - local unit-only lane
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(
        "TRUNCATE human_resource_grants, human_oidc_bindings, human_principals "
        "RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _principal(conn) -> str:
    principal_ref = _id("human:principal")
    human_access.create_principal(conn, principal_ref=principal_ref, created_by="admin")
    conn.commit()
    return principal_ref


def _bindings(conn, principal_ref: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM human_oidc_bindings WHERE principal_ref = %s",
            (principal_ref,),
        )
        return int(cur.fetchone()[0])


def _decision_payload(
    *,
    principal_ref: str,
    issuer: str,
    subject: str,
    decision_id: str,
    decided_by: str = "human:architect",
) -> dict:
    digest = human_access.binding_digest(
        principal_ref=principal_ref,
        issuer=issuer,
        subject=subject,
    )
    return {
        "decision": {
            "decision_id": decision_id,
            "decided_by": decided_by,
            "approval_level": "C3",
            "scope": {"scope_type": "human_principal", "scope_id": principal_ref},
            "object_identity": f"human_oidc_binding:{principal_ref}:{issuer}:{subject}",
            "content_digest": digest,
            "expires_at": "2099-01-01T00:00:00Z",
            "signature": "signed-canonical-decision",
        }
    }


def test_an_allowed_binding_carries_its_own_digest_to_the_decision_point(conn) -> None:
    principal_ref = _principal(conn)
    client = StandInPolicyClient()

    binding = human_access.bind_oidc_identity(
        conn,
        principal_ref=principal_ref,
        issuer="https://idp.example",
        subject="subject-1",
        bound_by="human:architect",
        policy_client=client,
        decision_payload=_decision_payload(
            principal_ref=principal_ref,
            issuer="https://idp.example",
            subject="subject-1",
            decision_id="decision-1",
            decided_by="human:architect",
        ),
    )
    conn.commit()

    assert binding["principal_ref"] == principal_ref
    expected = human_access.binding_digest(
        principal_ref=principal_ref,
        issuer="https://idp.example",
        subject="subject-1",
    )
    expectation = client.last_decision["expectation"]
    assert expectation["expected_digest"] == expected, (
        "the decision the PDP validated must cover this exact binding"
    )
    assert expectation["object_identity"] == (
        f"human_oidc_binding:{principal_ref}:https://idp.example:subject-1"
    )
    assert expectation["required_scope"] == {
        "scope_type": "human_principal",
        "scope_id": principal_ref,
    }, "a binding is not project-scoped and must not borrow a project scope"

    request = client.last_preflight["request"]
    assert request["writes_state"] is True
    assert request["external_effect"] is False, "a binding sends nothing outward"
    assert request["memory_promotion_requested"] is False


def test_a_refused_binding_writes_nothing(conn) -> None:
    principal_ref = _principal(conn)
    client = StandInPolicyClient(disposition="blocked_missing_task_contract")

    with pytest.raises(human_access.BindingRefused):
        human_access.bind_oidc_identity(
            conn,
            principal_ref=principal_ref,
            issuer="https://idp.example",
            subject="subject-2",
            bound_by="human:architect",
            policy_client=client,
            decision_payload=_decision_payload(
            principal_ref=principal_ref,
            issuer="https://idp.example",
            subject="subject-2",
            decision_id="decision-2",
            decided_by="human:architect",
        ),
        )
    conn.rollback()
    assert _bindings(conn, principal_ref) == 0, (
        "a refused binding must leave no identity able to act"
    )


def test_an_unreachable_decision_point_fails_closed(conn) -> None:
    principal_ref = _principal(conn)

    with pytest.raises(human_access.BindingPolicyUnavailable):
        human_access.bind_oidc_identity(
            conn,
            principal_ref=principal_ref,
            issuer="https://idp.example",
            subject="subject-3",
            bound_by="human:architect",
            policy_client=_UnreachablePolicyClient(),
            decision_payload=_decision_payload(
            principal_ref=principal_ref,
            issuer="https://idp.example",
            subject="subject-3",
            decision_id="decision-3",
            decided_by="human:architect",
        ),
        )
    conn.rollback()
    assert _bindings(conn, principal_ref) == 0, (
        "an unreachable decision point must not admit an identity"
    )


def test_a_binding_decided_by_a_non_human_is_refused(conn) -> None:
    """The stand-in refuses a system signer, and this is where that has to bite."""
    principal_ref = _principal(conn)

    with pytest.raises(human_access.BindingRefused):
        human_access.bind_oidc_identity(
            conn,
            principal_ref=principal_ref,
            issuer="https://idp.example",
            subject="subject-4",
            bound_by="hermes:profile",
            policy_client=StandInPolicyClient(),
            decision_payload=_decision_payload(
            principal_ref=principal_ref,
            issuer="https://idp.example",
            subject="subject-4",
            decision_id="decision-4",
            decided_by="hermes:profile",
        ),
        )
    conn.rollback()
    assert _bindings(conn, principal_ref) == 0


def _run_cli(monkeypatch, capsys, env: dict[str, str | None]) -> tuple[int, str]:
    from mvp_vertical import cli

    for key in ("MVP_POLICY_API_URL", "MVP_POLICY_API_KEY", "MVP_POLICY_ENFORCEMENT"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        if value is not None:
            monkeypatch.setenv(key, value)
    monkeypatch.setattr(
        "sys.argv",
        [
            "mvp-vertical",
            "bind-oidc-identity",
            "--principal-ref", "human:a",
            "--issuer", "https://idp.example",
            "--subject", "subject-1",
            "--bound-by", "human:architect",
            "--decision-ref", "decision-1",
        ],
    )
    monkeypatch.setattr(
        human_access,
        "connect",
        lambda *args, **kwargs: pytest.fail(
            "the CLI opened a connection before deciding it was allowed to bind"
        ),
    )
    code = cli.main()
    return code, capsys.readouterr().err


def test_the_cli_refuses_to_bind_without_a_decision_point(monkeypatch, capsys) -> None:
    """Optionality lives in the module; the composition point is where it bites.

    `bind_oidc_identity` takes `policy_client` optionally, like every other gated
    write here. That is exactly the shape this inventory recorded as unenforced —
    a parameter with no caller. What makes the chokepoint mandatory is this: the
    only production path refuses to reach the database at all unless a decision
    point is configured, or enforcement is declared disabled by name.
    """
    code, stderr = _run_cli(monkeypatch, capsys, {})
    assert code == 1
    assert "decision point is not configured" in stderr
    assert "MVP_POLICY_ENFORCEMENT=disabled explicitly" in stderr


def test_the_cli_refuses_an_unreadable_enforcement_setting(monkeypatch, capsys) -> None:
    code, stderr = _run_cli(monkeypatch, capsys, {"MVP_POLICY_ENFORCEMENT": "maybe"})
    assert code == 1
    assert "must be 'required' or 'disabled'" in stderr
