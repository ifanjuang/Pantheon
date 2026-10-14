"""Gate input hardening (external review, finding #2). All DB-free.

The gate must not trust the candidate stream: exactly one well-formed
result_candidate + evidence pack, linked, with the decision vocabulary read
from the governed vendored file — never injected by the candidate."""

from __future__ import annotations

import copy

import pytest

from mvp_vertical.terminal_gate_standin import GateRefusal, allowed_decisions, record_decision


REQUEST_REF = "mvp.test.tc"
REQUEST_SCOPE_DIGEST = "sha256:" + "4" * 64


def _stream() -> list:
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


def test_well_formed_stream_is_accepted():
    rec = record_decision(_stream(), decision="approve", decided_by="Camille")
    assert rec["decision"] == "approve"


def test_vocabulary_comes_from_the_governed_file_not_the_candidate():
    # A candidate that injects an ungoverned decision vocabulary is refused,
    # and the injected decision is refused even though the candidate "offers" it.
    stream = _stream()
    stream[1]["possible_decisions"] = ["send_now"]
    with pytest.raises(GateRefusal):
        record_decision(stream, decision="send_now", decided_by="Camille")
    # and the governed set is exactly the vendored stand-in's list
    assert "send_now" not in allowed_decisions()
    assert {"approve", "refuse"} <= allowed_decisions()


def test_refuses_a_malformed_evidence_pack():
    stream = _stream()
    del stream[1]["evidence_items"]  # schema-required
    with pytest.raises(GateRefusal):
        record_decision(stream, decision="approve", decided_by="Camille")


def test_refuses_more_than_one_candidate():
    stream = _stream()
    stream.append(copy.deepcopy(stream[0]))  # two result_candidates
    with pytest.raises(GateRefusal):
        record_decision(stream, decision="approve", decided_by="Camille")


def test_refuses_evidence_pack_supporting_a_different_candidate():
    stream = _stream()
    stream[1]["supports"] = "mvp.test.tc.rc-999"
    with pytest.raises(GateRefusal):
        record_decision(stream, decision="approve", decided_by="Camille")


def test_refuses_a_pre_authorized_candidate():
    stream = _stream()
    stream[0]["external_action_authorized"] = True
    with pytest.raises(GateRefusal):
        record_decision(stream, decision="approve", decided_by="Camille")
