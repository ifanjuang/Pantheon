"""Block 3 — Register Candidate (issue #13). All DB-free: builds a real
approved decision_record via the gate, then proposes/refuses retention."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]

from mvp_vertical import pantheon_contracts
from mvp_vertical.register import RegisterRefusal, propose_register_candidate
from mvp_vertical.terminal_gate_standin import record_decision

SCHEMA = pantheon_contracts.load_schema("mvp_governed_loop_objects")
REQUEST_REF = "mvp.test.tc"
REQUEST_SCOPE_DIGEST = "sha256:" + "4" * 64


def _candidates() -> list:
    return [
        {"object_type": "result_candidate", "object_id": "mvp.test.tc.rc-001",
         "result_candidate_id": "mvp.test.tc.rc-001", "applies_to": "mvp.test.tc",
         "status": "draft_to_review", "request_ref": REQUEST_REF,
         "request_scope_digest": REQUEST_SCOPE_DIGEST,
         "body": "…", "external_action_authorized": False},
        {"object_type": "evidence_pack_candidate", "object_id": "mvp.test.tc.ep-001",
         "evidence_pack_id": "mvp.test.tc.ep-001", "applies_to": "mvp.test.tc",
         "supports": "mvp.test.tc.rc-001", "status": "candidate",
         "request_ref": REQUEST_REF, "request_scope_digest": REQUEST_SCOPE_DIGEST,
         "evidence_items": [{"claim": "…", "source_ref": "s.md", "support_status": "sourced_not_verified"}],
         "possible_decisions": ["approve", "refuse", "request_revision", "request_more_evidence"]},
    ]


def _approved() -> dict:
    return record_decision(_candidates(), decision="approve", decided_by="Camille")


def _propose(decision, **kw):
    """Propose retention with sensible defaults for the human authorizer."""
    kw.setdefault("retention_authorized", True)
    kw.setdefault("statement", "x")
    kw.setdefault("scope", "y")
    kw.setdefault("authorized_by", "Camille")
    return propose_register_candidate(decision, **kw)


def test_approved_decision_can_propose_a_register_candidate():
    import jsonschema
    reg = _propose(_approved(), statement="Le lot 06 est limité à la terrasse T2.",
                   scope="dossier devis_reprise")
    assert reg["object_type"] == "register_candidate"
    assert reg["status"] == "candidate"
    assert reg["not_memory_until_admitted"] is True
    jsonschema.validate(reg, SCHEMA)


def test_register_candidate_links_to_the_exact_reviewed_content():
    decision = _approved()
    reg = _propose(decision)
    assert reg["created_because_of"] == decision["decision_id"]
    # the candidate digest the human reviewed is carried in the basis
    joined = " ".join(reg["basis"])
    assert decision["candidate_digest"]["value"] in joined
    assert decision["evidence_pack_digest"]["value"] in joined


def test_refuses_when_decision_is_not_approve():
    revision = record_decision(_candidates(), decision="request_revision", decided_by="Camille")
    with pytest.raises(RegisterRefusal):
        _propose(revision)


def test_refuses_without_explicit_retention_authorization():
    for value in (False, None, "true", 1):
        with pytest.raises(RegisterRefusal):
            _propose(_approved(), retention_authorized=value)


def test_refuses_missing_statement_or_scope():
    with pytest.raises(RegisterRefusal):
        _propose(_approved(), statement="  ")
    with pytest.raises(RegisterRefusal):
        _propose(_approved(), scope="")


def test_refuses_non_decision_record_input():
    with pytest.raises(RegisterRefusal):
        _propose({"object_type": "result_candidate"})


def test_candidate_promotes_no_memory_and_authorizes_nothing():
    reg = _propose(_approved())
    assert reg["not_memory_until_admitted"] is True
    assert "memory_promotion" in reg["forbidden_reuse"]
    assert "external_send" in reg["forbidden_reuse"]
    # it never asserts an external authorization…
    assert reg.get("external_action_authorized", False) is False
    # …and it is a candidate, never an admitted register entry
    assert reg["status"] == "candidate"


# --- Blocker #1 (external review, finding #1): the seam must not trust a
# hand-crafted decision_record, and retention is a distinct human act. ---------

def test_refuses_a_hand_crafted_minimal_decision_record():
    # The exact reported bypass: a plausible-looking dict that never went
    # through the gate. It is missing the gate's integrity fields and is refused.
    forged = {
        "object_type": "decision_record", "object_id": "mvp.test.tc.decision.deadbeef",
        "status": "recorded", "applies_to": "mvp.test.tc.rc-001", "decision": "approve",
        "decided_by": "Camille", "decision_surface": "terminal_gate_standin",
        "consequences": {"executed_by_gate": False},
    }
    with pytest.raises(RegisterRefusal):
        _propose(forged)


def test_refuses_a_decision_record_without_content_digests():
    # A gate record stripped of the digests that bind it to reviewed content.
    decision = _approved()
    del decision["candidate_digest"]
    with pytest.raises(RegisterRefusal):
        _propose(decision)


def test_refuses_a_decision_record_claiming_external_authorization():
    decision = _approved()
    decision["external_action_authorized"] = True
    with pytest.raises(RegisterRefusal):
        _propose(decision)


def test_refuses_a_system_signed_decision_record():
    # A hand-crafted, schema-valid record signed by the system: record_decision
    # would have refused this signer, so the register seam must too.
    for bad in ("system", "runner", "", "Hermes"):
        decision = _approved()
        decision["decided_by"] = bad
        with pytest.raises(RegisterRefusal):
            _propose(decision)


def test_refuses_a_digest_stub_without_algorithm():
    # A digest of the gate's {value: ...} shape but MISSING algorithm — the
    # basis builder would default it to sha256, so it must be refused up front.
    decision = _approved()
    decision["candidate_digest"] = {"value": "a" * 64}  # no algorithm
    with pytest.raises(RegisterRefusal):
        _propose(decision)
    decision = _approved()
    decision["evidence_pack_digest"] = {"algorithm": "sha256", "value": "not-hex"}
    with pytest.raises(RegisterRefusal):
        _propose(decision)


def test_retention_authorization_needs_a_human_authorizer():
    # Gate 5 reused: the system may not authorize its own memory.
    for bad in ("", "   ", "system", "runner", "Hermes", "assistant"):
        with pytest.raises(RegisterRefusal):
            _propose(_approved(), authorized_by=bad)


def test_retention_authorization_matches_the_vendored_schema_shape():
    # The retention_authorization def (see canonical governed-loop schema) is additionalProperties:
    # false — exactly authorized/authorized_by/identity_assurance/recorded_at/
    # decision_id. The human rationale rides the candidate at top level.
    reg = _propose(_approved(), authorized_by="Camille Architecte", rationale="périmètre stable")
    auth = reg["retention_authorization"]
    assert auth.keys() == {"authorized", "authorized_by", "identity_assurance",
                           "recorded_at", "decision_id"}
    assert auth["authorized"] is True
    assert auth["authorized_by"] == "Camille Architecte"
    assert auth["identity_assurance"] == "declared"        # declared, never authenticated
    assert "authenticated_principal" not in auth           # forbidden for declared
    assert auth["recorded_at"].endswith("Z")
    assert auth["decision_id"] == reg["created_because_of"]
    # the human rationale is preserved, outside the strict block
    assert reg["retention_rationale"] == "périmètre stable"


def test_retention_authorization_binds_to_the_decision():
    decision = _approved()
    reg = _propose(decision)
    assert reg["retention_authorization"]["decision_id"] == decision["decision_id"]
