from __future__ import annotations

from pathlib import Path

from mvp_vertical.policy_gate import StandInPolicyClient, enforce_consequential


def _candidate() -> dict:
    return {
        "intent": "act_working_information",
        "decision_expectation": {
            "required_ceiling": "C2",
            "required_scope": {"scope_type": "project", "scope_id": "project-a"},
            "object_identity": "agency_information:info-a",
            "expected_digest": "sha256:effect-a",
        },
        "request": {
            "intent": "act_working_information",
            "external_effect": False,
            "writes_state": True,
            "scope": {"scope_type": "project", "scope_id": "project-a"},
        },
    }


def _decision() -> dict:
    return {
        "decision": {
            "decision_id": "decision-a",
            "decided_by": "human-reviewer",
            "approval_level": "C2",
            "scope": {"scope_type": "project", "scope_id": "project-a"},
            "object_identity": "agency_information:info-a",
            "content_digest": "sha256:effect-a",
            "expires_at": "2099-01-01T00:00:00Z",
            "signature": "signed-canonical-decision",
        }
    }


def test_bare_decision_reference_cannot_be_upgraded_by_the_effect_owner() -> None:
    client = StandInPolicyClient()

    verdict = enforce_consequential(
        client,
        candidate=_candidate(),
        decision_payload={"decision": {"decision_id": "decision-a"}},
    )

    assert verdict.allowed is False
    assert verdict.disposition == "blocked_invalid_decision_envelope"
    assert "complete canonical signed Decision credential" in verdict.reasons[0]
    assert client.last_preflight is None
    assert client.last_decision is None


def test_owner_filled_unsigned_decision_still_fails_closed() -> None:
    client = StandInPolicyClient()
    owner_filled = {
        "decision": {
            "decision_id": "decision-a",
            "decided_by": "human-reviewer",
            "approval_level": "C2",
            "scope": {"scope_type": "project", "scope_id": "project-a"},
            "object_identity": "agency_information:info-a",
            "content_digest": "sha256:effect-a",
        }
    }

    verdict = enforce_consequential(
        client,
        candidate=_candidate(),
        decision_payload=owner_filled,
    )

    assert verdict.allowed is False
    assert verdict.disposition == "blocked_invalid_decision_envelope"
    assert "expires_at" in verdict.reasons[0]
    assert "signature" in verdict.reasons[0]
    assert client.last_preflight is None
    assert client.last_decision is None


def test_human_response_cannot_substitute_for_a_direct_human_decision() -> None:
    client = StandInPolicyClient()

    verdict = enforce_consequential(
        client,
        candidate=_candidate(),
        decision_payload={
            "human_response": {
                "response_id": "human-response-a",
                "responded_by": "human-reviewer",
                "response_text": "Proceed.",
            }
        },
    )

    assert verdict.allowed is False
    assert verdict.disposition == "blocked_invalid_decision_envelope"
    assert verdict.reasons == ["decision_payload.decision must be a mapping"]
    assert client.last_preflight is None
    assert client.last_decision is None


def test_direct_human_effect_refuses_valid_but_unauthenticated_issuer() -> None:
    client = StandInPolicyClient(issuer_authenticated=False)

    verdict = enforce_consequential(
        client,
        candidate=_candidate(),
        decision_payload=_decision(),
    )

    assert verdict.allowed is False
    assert verdict.disposition == "blocked_unauthenticated_human_decision"
    assert client.last_preflight is not None
    assert client.last_decision is not None


def test_direct_human_effect_accepts_complete_authenticated_matching_decision() -> None:
    client = StandInPolicyClient(issuer_authenticated=True)

    verdict = enforce_consequential(
        client,
        candidate=_candidate(),
        decision_payload=_decision(),
    )

    assert verdict.allowed is True
    assert client.last_decision == {
        "decision": _decision()["decision"],
        "expectation": _candidate()["decision_expectation"],
    }


def test_non_direct_effect_does_not_inherit_direct_human_issuer_requirement() -> None:
    candidate = {
        "intent": "capability:install",
        "decision_expectation": {
            "required_ceiling": "C2",
            "required_scope": {"scope_type": "project", "scope_id": "project-a"},
            "object_identity": "capability:tool-a",
            "expected_digest": "sha256:tool-a",
        },
        "request": {
            "intent": "capability:install",
            "external_effect": False,
            "writes_state": True,
        },
    }
    decision = {
        "decision": {
            "decision_id": "decision-a",
            "decided_by": "human-reviewer",
            "approval_level": "C2",
            "scope": {"scope_type": "project", "scope_id": "project-a"},
            "object_identity": "capability:tool-a",
            "content_digest": "sha256:tool-a",
        }
    }
    client = StandInPolicyClient(issuer_authenticated=False)

    verdict = enforce_consequential(
        client,
        candidate=candidate,
        decision_payload=decision,
    )

    assert verdict.allowed is True


ROOT = Path(__file__).resolve().parents[2]

_DIRECT_HUMAN_OWNER_FILES = (
    "implementation/mvp_vertical/human_access.py",
    "implementation/mvp_vertical/apu_owner.py",
    "implementation/mvp_vertical/knowledge.py",
    "implementation/mvp_vertical/agency_information.py",
)


def test_direct_human_effect_owners_never_manufacture_decision_fields() -> None:
    for relative_path in _DIRECT_HUMAN_OWNER_FILES:
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "decision.setdefault(" not in source
        assert 'bound_decision["decision"] = decision' not in source


def test_direct_human_callers_load_canonical_decisions_before_effects() -> None:
    cli = (ROOT / "implementation/mvp_vertical/cli.py").read_text(encoding="utf-8")
    cockpit = (ROOT / "implementation/mvp_vertical/cockpit_api.py").read_text(encoding="utf-8")
    agency = (ROOT / "implementation/mvp_vertical/agency_data_api.py").read_text(encoding="utf-8")
    variants = (
        ROOT / "implementation/mvp_vertical/knowledge_edit_variant_api.py"
    ).read_text(encoding="utf-8")

    assert cli.count("decision_requests.policy_decision_payload(") >= 2
    assert cockpit.count("decision_requests.policy_decision_payload(") >= 2
    assert "decision_requests.policy_decision_payload(" in agency
    assert "decision_requests.policy_decision_payload(" in variants

    legacy_sparse_fragments = (
        'decision_payload={"decision": {"decision_id": decision_ref}}',
        '"decision_id": body.human_decision_ref,\n                        "decided_by": actor,',
    )
    combined = "\n".join((cli, cockpit, agency, variants))
    for fragment in legacy_sparse_fragments:
        assert fragment not in combined
