from __future__ import annotations

from pathlib import Path

from mvp_vertical.contract import TaskContract
from mvp_vertical.retrieval import HybridRetrievedChunk
from mvp_vertical.runner import (
    MAX_USEFUL_DISTANCE,
    _is_useful,
    _metric_profile,
    _run,
)
from mvp_vertical.store import RetrievedChunk


class _Drafter:
    def draft(self, *, intent: str, question: str, chunks: list[RetrievedChunk]) -> str:
        chunk = chunks[0]
        return f"Réponse candidate [{chunk.source_ref}#chunk-{chunk.chunk_no}]"


def _contract() -> TaskContract:
    return TaskContract(
        raw={"object_id": "tc-hybrid", "contract_id": "tc-hybrid", "intent": "test"},
        path=Path("task.yaml"),
        dossier="dossier-a",
        sources=("source.md",),
        forbidden=(),
    )


def _chunk(*, distance: float = 0.5, chunk_no: int = 1) -> RetrievedChunk:
    return RetrievedChunk(
        source_ref="source.md",
        chunk_no=chunk_no,
        body="contenu déclaré",
        distance=distance,
        contract_id="tc-hybrid",
        contract_digest="digest",
        ingestion_id="ingestion",
        source_digest="source-digest",
    )


def test_lexical_match_is_useful_without_treating_rrf_as_truth_threshold() -> None:
    lexical = HybridRetrievedChunk(
        chunk=_chunk(distance=0.99),
        hybrid_score=0.02,
        semantic_rank=None,
        lexical_rank=1,
    )
    weak_semantic = HybridRetrievedChunk(
        chunk=_chunk(distance=MAX_USEFUL_DISTANCE + 0.01),
        hybrid_score=0.02,
        semantic_rank=1,
        lexical_rank=None,
    )

    assert _is_useful(lexical) is True
    assert _is_useful(weak_semantic) is False


def test_metric_profile_keeps_both_ranks_and_score_visible() -> None:
    hit = HybridRetrievedChunk(
        chunk=_chunk(),
        hybrid_score=0.03125,
        semantic_rank=2,
        lexical_rank=1,
    )

    profile = _metric_profile(hit)

    assert "weighted_rrf_v1" in profile
    assert "semantic_rank=2" in profile
    assert "lexical_rank=1" in profile
    assert "hybrid_score=0.031250000000" in profile


def test_runner_uses_hybrid_order_and_preserves_candidate_boundaries(monkeypatch) -> None:
    first = HybridRetrievedChunk(
        chunk=_chunk(distance=0.7, chunk_no=2),
        hybrid_score=0.032,
        semantic_rank=2,
        lexical_rank=1,
    )
    second = HybridRetrievedChunk(
        chunk=_chunk(distance=0.4, chunk_no=1),
        hybrid_score=0.016,
        semantic_rank=1,
        lexical_rank=None,
    )

    monkeypatch.setattr(
        "mvp_vertical.runner.retrieve_hybrid_scoped",
        lambda *args, **kwargs: [first, second],
    )

    output = _run(object(), _contract(), "question", _Drafter())

    assert output.kind == "candidates"
    result, evidence = output.documents
    assert result["status"] == "draft_to_review"
    assert result["external_action_authorized"] is False
    assert evidence["status"] == "candidate"
    assert [item["retrieval_metrics"]["rank"] for item in evidence["evidence_items"]] == [1, 2]
    first_metrics = evidence["evidence_items"][0]["retrieval_metrics"]
    assert first_metrics["metric"] == "cosine_distance"
    assert "semantic_rank=2" in first_metrics["profile"]
    assert "lexical_rank=1" in first_metrics["profile"]
    assert "hybrid_score=0.032000000000" in first_metrics["profile"]
    assert evidence["evidence_items"][0]["support_status"] == "sourced_not_verified"
    assert any("score ne mesure ni la vérité" in item for item in evidence["limitations"])


def test_runner_refuses_when_hybrid_results_have_no_useful_signal(monkeypatch) -> None:
    weak = HybridRetrievedChunk(
        chunk=_chunk(distance=MAX_USEFUL_DISTANCE + 0.1),
        hybrid_score=0.02,
        semantic_rank=1,
        lexical_rank=None,
    )
    monkeypatch.setattr(
        "mvp_vertical.runner.retrieve_hybrid_scoped",
        lambda *args, **kwargs: [weak],
    )

    output = _run(object(), _contract(), "hors périmètre", _Drafter())

    assert output.kind == "refusal"
    assert output.documents[0]["status"] == "refused_capability_gap"
    assert output.documents[0]["external_action_authorized"] is False
