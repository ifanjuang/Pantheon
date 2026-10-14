"""Tests for the decision-signing producer (human-issuer authentication)."""

import pytest

from mvp_vertical.decision_signing import (
    sign_decision,
    signed_decision,
    signed_decision_payload,
)

_DECISION = {
    "decision_id": "d1",
    "decided_by": "marie",
    "approval_level": "C3",
    "scope": {"scope_type": "project", "scope_id": "P-42"},
    "object_identity": "effect:x",
    "content_digest": "sha256:abc",
    "expires_at": "2026-07-25T12:00:00Z",
}
# Known-answer vector: HMAC-SHA256 over the canonical signed fields with the
# secret below. This MUST equal what the Pantheon PDP
# (mcp-server gate_validation._expected_issuer_signature) computes for the same
# inputs; if it diverges the two sides have drifted and must be re-synced.
_SECRET = "issuer-secret"
_EXPECTED = "966583cdfcca64e3fddc527a7d1e3e358289c43961cecf73dcefb562f88e14d0"


def test_known_answer_vector_matches_the_pdp_algorithm():
    assert sign_decision(_DECISION, _SECRET) == _EXPECTED


def test_key_order_does_not_change_the_signature():
    reordered = {k: _DECISION[k] for k in reversed(list(_DECISION))}
    assert sign_decision(reordered, _SECRET) == _EXPECTED


def test_signed_decision_attaches_a_verifiable_signature():
    out = signed_decision(_DECISION, _SECRET)
    assert out["signature"] == _EXPECTED
    assert "signature" not in _DECISION  # original not mutated


def test_changing_any_signed_field_changes_the_signature():
    for field, new in [
        ("scope", {"scope_type": "project", "scope_id": "OTHER"}),
        ("approval_level", "C1"),
        ("object_identity", "effect:y"),
        ("content_digest", "sha256:zzz"),
        ("expires_at", "2027-01-01T00:00:00Z"),
    ]:
        tampered = dict(_DECISION, **{field: new})
        assert sign_decision(tampered, _SECRET) != _EXPECTED, field


def test_signed_decision_payload_signs_decision_and_preserves_expectation():
    payload = {"decision": dict(_DECISION), "expectation": {"required_ceiling": "C3"}}
    out = signed_decision_payload(payload, _SECRET)
    assert out["decision"]["signature"] == _EXPECTED
    assert out["expectation"] == {"required_ceiling": "C3"}


def test_empty_secret_is_rejected():
    with pytest.raises(ValueError):
        sign_decision(_DECISION, "")
