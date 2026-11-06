"""One human gesture for the claim candidates of one Observation Bundle.

The batch replays the existing per-candidate chain (review -> write command ->
authorization -> application) for the exact preview a human approved, all or
nothing, and keeps every candidate's own trail.
"""

from __future__ import annotations

import pytest

from mvp_vertical import apu_batch, apu_mapping_reviews, apu_owner
from test_apu_progressive_claims import (  # noqa: F401 - conn is a fixture
    DOOR,
    _bundle,
    _claim_ids,
    _import,
    _project,
    _width,
    conn,
)

HUMAN = "human:architect"
MACHINE = "system:apu-batch"


def _setup(conn, extra=None):
    project_id = _project(conn)
    _import(conn, project_id)
    candidates = [
        _width("claim.door.width.t1", 0.93, supersedes_claim_ref="claim.door.width.t0"),
        {**_width("claim.door.width.note", 0.9), "attribute_key": "geometry.observed_width"},
        *(extra or []),
    ]
    execution_id, result_id = _bundle(conn, project_id, candidates, [])
    return project_id, execution_id, result_id


REFS = ["claim.door.width.t1", "claim.door.width.note"]


def _reviews(conn, execution_id, result_id, refs=REFS):
    return [
        review
        for ref in refs
        for review in apu_mapping_reviews.list_mapping_reviews(
            conn, execution_result_id=execution_id, result_ref=result_id, mapping_ref=ref
        )
    ]


def _apply(conn, execution_id, result_id, digest, reject=None):
    return apu_batch.apply_batch(
        conn, execution_result_id=execution_id, result_ref=result_id, batch_digest=digest,
        reviewer=HUMAN, authorized_by=HUMAN, applied_by=MACHINE, reject=reject,
    )


def test_preview_writes_nothing_and_its_digest_covers_the_decisions(conn) -> None:
    project_id, execution_id, result_id = _setup(conn)
    first = apu_batch.preview_batch(conn, execution_result_id=execution_id, result_ref=result_id)
    again = apu_batch.preview_batch(conn, execution_result_id=execution_id, result_ref=result_id)
    rejecting = apu_batch.preview_batch(
        conn, execution_result_id=execution_id, result_ref=result_id, reject=["claim.door.width.note"]
    )
    assert first["batch_digest"] == again["batch_digest"] != rejecting["batch_digest"]
    assert [item["decision"] for item in rejecting["items"]] == ["accept", "reject"]
    assert _reviews(conn, execution_id, result_id) == []
    assert apu_owner.get_project_anatomy(conn, project_id=project_id)["owner_revision"] == 1


def test_one_approval_applies_every_candidate_with_its_own_trail(conn) -> None:
    project_id, execution_id, result_id = _setup(conn)
    digest = apu_batch.preview_batch(conn, execution_result_id=execution_id, result_ref=result_id)["batch_digest"]
    result = _apply(conn, execution_id, result_id, digest)
    assert result["applied"] == ["claim.door.width.t1", "claim.door.width.note"]
    anatomy = apu_owner.get_project_anatomy(conn, project_id=project_id)
    assert anatomy["owner_revision"] == 3
    assert {"claim.door.width.t1", "claim.door.width.note"} <= _claim_ids(anatomy, "attribute")
    reviews = _reviews(conn, execution_id, result_id)
    assert len(reviews) == 2
    assert all(review["note"].startswith(f"batch:{digest}") for review in reviews)


def test_rejected_candidates_are_reviewed_but_not_written(conn) -> None:
    project_id, execution_id, result_id = _setup(conn)
    reject = ["claim.door.width.note"]
    digest = apu_batch.preview_batch(
        conn, execution_result_id=execution_id, result_ref=result_id, reject=reject
    )["batch_digest"]
    result = _apply(conn, execution_id, result_id, digest, reject=reject)
    assert (result["applied"], result["rejected"]) == (["claim.door.width.t1"], reject)
    anatomy = apu_owner.get_project_anatomy(conn, project_id=project_id)
    assert "claim.door.width.note" not in _claim_ids(anatomy, "attribute")
    actions = {r["mapping_ref"]: r["action"] for r in _reviews(conn, execution_id, result_id)}
    assert actions == {"claim.door.width.t1": "accept_claim_candidate", "claim.door.width.note": "reject_mapping"}


def test_a_batch_that_differs_from_the_approved_preview_is_refused(conn) -> None:
    project_id, execution_id, result_id = _setup(conn)
    digest = apu_batch.preview_batch(conn, execution_result_id=execution_id, result_ref=result_id)["batch_digest"]
    with pytest.raises(apu_batch.ApuBatchError, match="changed since it was approved"):
        _apply(conn, execution_id, result_id, digest, reject=["claim.door.width.note"])
    assert apu_owner.get_project_anatomy(conn, project_id=project_id)["owner_revision"] == 1


def test_one_failing_candidate_leaves_nothing_of_the_batch(conn) -> None:
    unknown = {**_width("claim.ghost.width", 1.2), "subject_ref": {"entity_type": "stable_object", "entity_id": "OBJ-GHOST"}}
    project_id, execution_id, result_id = _setup(conn, extra=[unknown])
    digest = apu_batch.preview_batch(conn, execution_result_id=execution_id, result_ref=result_id)["batch_digest"]
    with pytest.raises(Exception):
        _apply(conn, execution_id, result_id, digest)
    assert apu_owner.get_project_anatomy(conn, project_id=project_id)["owner_revision"] == 1
    assert _reviews(conn, execution_id, result_id, REFS + ["claim.ghost.width"]) == []


def test_unknown_rejected_refs_are_refused(conn) -> None:
    _, execution_id, result_id = _setup(conn)
    with pytest.raises(apu_batch.ApuBatchError, match="not candidates"):
        apu_batch.preview_batch(conn, execution_result_id=execution_id, result_ref=result_id, reject=["nope"])
