from __future__ import annotations

import pytest

from mvp_vertical.retrieval import reciprocal_rank_fusion
from mvp_vertical.store import RetrievedChunk


def _chunk(source_ref: str, chunk_no: int, distance: float = 0.5) -> RetrievedChunk:
    return RetrievedChunk(
        source_ref=source_ref,
        chunk_no=chunk_no,
        body=f"{source_ref}:{chunk_no}",
        distance=distance,
    )


def test_rrf_rewards_candidates_present_in_both_rankings() -> None:
    shared = _chunk("a.md", 1)
    semantic_only = _chunk("a.md", 2)
    lexical_only = _chunk("b.md", 1)

    hits = reciprocal_rank_fusion(
        [semantic_only, shared],
        [lexical_only, shared],
        top_k=3,
        candidate_k=3,
        rrf_k=10,
    )

    assert hits[0].chunk == shared
    assert hits[0].semantic_rank == 2
    assert hits[0].lexical_rank == 2
    assert hits[0].retrieval_methods == ("semantic", "lexical")


def test_rrf_is_deterministic_for_equal_scores() -> None:
    first = _chunk("a.md", 1)
    second = _chunk("b.md", 1)

    hits = reciprocal_rank_fusion(
        [second, first],
        [first, second],
        top_k=2,
        candidate_k=2,
        rrf_k=60,
    )

    assert [(hit.chunk.source_ref, hit.chunk.chunk_no) for hit in hits] == [
        ("b.md", 1),
        ("a.md", 1),
    ]


def test_rrf_keeps_method_specific_candidates() -> None:
    semantic = _chunk("semantic.md", 1)
    lexical = _chunk("lexical.md", 1)

    hits = reciprocal_rank_fusion(
        [semantic],
        [lexical],
        top_k=2,
        candidate_k=2,
    )

    by_source = {hit.chunk.source_ref: hit for hit in hits}
    assert by_source["semantic.md"].retrieval_methods == ("semantic",)
    assert by_source["lexical.md"].retrieval_methods == ("lexical",)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"top_k": 0}, "top_k"),
        ({"top_k": 4, "candidate_k": 3}, "candidate_k"),
        ({"candidate_k": 101}, "candidate_k"),
        ({"rrf_k": 0}, "rrf_k"),
        ({"semantic_weight": -1}, "weights"),
        ({"semantic_weight": 0, "lexical_weight": 0}, "at least one"),
    ],
)
def test_rrf_rejects_invalid_configuration(kwargs: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        reciprocal_rank_fusion([_chunk("a.md", 1)], [], **kwargs)
