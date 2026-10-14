"""The Knowledge UPDATE routes through the policy chokepoint when a client is given.

The chokepoint runs before any database access, so the block path is testable
with conn=None: a blocked verdict must raise before the write is attempted.
"""

import time

import pytest

from mvp_vertical import knowledge_update
from mvp_vertical.knowledge_update import KnowledgeUpdateError, apply_knowledge_update
from mvp_vertical.policy_gate import StandInPolicyClient

SECRET = "s" * 32
PROJECT = "P-42"
KID = "K-1"
MARKDOWN = "# Updated\n\nbody\n"


def _signed_kwargs(actor="marie", now=1_000_000):
    proposed_digest = knowledge_update._digest(MARKDOWN)
    expires = now + 300
    payload = knowledge_update._effect_payload(
        parent_project_id=PROJECT,
        knowledge_id=KID,
        expected_version=1,
        base_markdown_digest="base-digest",
        proposed_markdown_digest=proposed_digest,
        review_status=None,
        actor=actor,
        expires_at=expires,
    )
    token = knowledge_update._signature(SECRET, payload)
    return dict(
        parent_project_id=PROJECT,
        knowledge_id=KID,
        proposed_markdown=MARKDOWN,
        expected_version=1,
        base_markdown_digest="base-digest",
        actor=actor,
        signing_secret=SECRET,
        confirmation_token=token,
        confirmation_expires_at=expires,
        confirmation_phrase=knowledge_update.CONFIRMATION_PHRASE,
        idempotency_key="idem-key-123456",
        task_contract_ref="task-contract:test",
        evidence_pack_candidate_ref="evidence-pack-candidate:test",
        human_decision_ref="human-decision:test",
        now=now,
    )


class _SpyClient(StandInPolicyClient):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.preflight_candidates = []
        self.decision_payloads = []

    def preflight(self, candidate):
        self.preflight_candidates.append(candidate)
        return super().preflight(candidate)

    def validate_decision(self, payload):
        self.decision_payloads.append(payload)
        # Force a block here so the flow records the payload then stops before any
        # DB access (an eligible preflight would otherwise proceed to the write).
        return {"verdict": "invalid", "findings": ["forced block for introspection"]}


def test_blocked_preflight_raises_before_any_db_access():
    client = StandInPolicyClient(disposition="blocked_pending_scope")
    with pytest.raises(KnowledgeUpdateError, match="chokepoint blocked"):
        # conn=None: if the chokepoint did not block first, this would crash on DB access.
        apply_knowledge_update(None, policy_client=client, **_signed_kwargs())


def test_chokepoint_builds_a_scoped_decision_from_the_update_inputs():
    client = _SpyClient()  # eligible preflight, forced-invalid decision (blocks pre-DB)
    with pytest.raises(KnowledgeUpdateError):
        apply_knowledge_update(None, policy_client=client, **_signed_kwargs())
    assert client.preflight_candidates, "preflight was consulted"
    decision = client.decision_payloads[0]["decision"]
    assert decision["decided_by"] == "marie"
    assert decision["scope"] == {"scope_type": "project", "scope_id": PROJECT}
    assert decision["content_digest"] == knowledge_update._digest(MARKDOWN)


def test_issuer_signing_secret_signs_the_decision_sent_to_the_pdp():
    from mvp_vertical.decision_signing import sign_decision

    client = _SpyClient()  # eligible preflight, forced-invalid decision (blocks pre-DB)
    with pytest.raises(KnowledgeUpdateError):
        apply_knowledge_update(
            None, policy_client=client, issuer_signing_secret="issuer-secret", **_signed_kwargs()
        )
    signed = client.decision_payloads[0]["decision"]
    assert "signature" in signed
    # the attached signature verifies over the exact signed decision fields
    assert signed["signature"] == sign_decision(
        {k: signed[k] for k in signed if k != "signature"}, "issuer-secret"
    )


def test_no_policy_client_keeps_the_original_behavior():
    # Without a client the chokepoint is skipped; with conn=None the original
    # code path proceeds to its first DB access and fails there, not at a gate.
    with pytest.raises(Exception) as exc:
        apply_knowledge_update(None, **_signed_kwargs())
    assert "chokepoint" not in str(exc.value)
