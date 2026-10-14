"""Runner output validation (external review, finding #10). All DB-free.

Two things this covers:
  1. commitment_flags matches the vendored schema's commitment_flag def — an
     array of {phrase, risk} OBJECTS (see canonical governed-loop schema). It diverged invisibly
     when empty, which is why systematic validation matters.
  2. run() validates every emitted object against the vendored schema, so a
     later change (a divergent shape, a Block 2 LLM drafter) cannot quietly
     emit a malformed object — a broken cage is a bug, not a candidate.
"""

from __future__ import annotations

import pytest

from mvp_vertical.runner import (
    RunnerInvariantError,
    _assert_conforms_to_schema,
    _detect_commitments,
)


def test_commitment_flags_are_objects_with_phrase_and_risk():
    flags = _detect_commitments("Bonjour, nous acceptons votre offre et vous pouvez lancer.")
    assert flags, "a commitment phrase must be flagged"
    assert all(isinstance(f, dict) and f.keys() == {"phrase", "risk"} for f in flags), \
        "commitment_flags must be {phrase, risk} objects (schema commitment_flag)"
    assert all(f["phrase"] and f["risk"] for f in flags), "both fields non-empty"


def test_neutral_text_raises_no_commitment_flag():
    assert _detect_commitments("Voici les éléments retenus, sans conclusion.") == []


def _valid_candidate() -> dict:
    return {
        "object_type": "result_candidate",
        "object_id": "mvp.test.tc.rc-001",
        "result_candidate_id": "mvp.test.tc.rc-001",
        "status": "draft_to_review",
        "request_ref": "mvp.test.tc",
        "request_scope_digest": "sha256:" + "4" * 64,
        "body": "Bonjour, …",
        "external_action_authorized": False,
        "commitment_flags": [{"phrase": "nous acceptons", "risk": "engagement externe si envoyé tel quel"}],
    }


def test_schema_validation_passes_a_conforming_candidate():
    _assert_conforms_to_schema([_valid_candidate()])  # must not raise


def test_schema_validation_catches_string_commitment_flags():
    # The schema's commitment_flag is an OBJECT; a bare string is rejected.
    bad = _valid_candidate()
    bad["commitment_flags"] = ["nous acceptons"]
    with pytest.raises(RunnerInvariantError):
        _assert_conforms_to_schema([bad])


def test_schema_validation_catches_a_commitment_flag_missing_risk():
    # commitment_flag requires both phrase and risk (additionalProperties: false).
    bad = _valid_candidate()
    bad["commitment_flags"] = [{"phrase": "nous acceptons"}]
    with pytest.raises(RunnerInvariantError):
        _assert_conforms_to_schema([bad])


def test_schema_validation_catches_a_missing_required_field():
    bad = _valid_candidate()
    del bad["body"]  # body is required by the schema
    with pytest.raises(RunnerInvariantError):
        _assert_conforms_to_schema([bad])
