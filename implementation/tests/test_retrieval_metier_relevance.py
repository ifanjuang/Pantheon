"""Small métier relevance checks for the current bounded retrieval candidate.

These tests execute the real PostgreSQL lexical/vector paths. They lock scope,
provenance and deterministic fusion, while keeping production semantic quality
explicitly unclaimed because the active embedder is still a local placeholder.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from mvp_vertical import store
from mvp_vertical.contract import load_contract
from mvp_vertical.embedder import embed, to_pgvector
from mvp_vertical.retrieval import retrieve_hybrid_scoped, retrieve_lexical_scoped

ROOT = Path(__file__).resolve().parents[1]
CASES = yaml.safe_load(
    (ROOT / "tests/fixtures/retrieval_metier_cases.yaml").read_text(encoding="utf-8")
)
PROFESSIONAL_REVIEW = yaml.safe_load(
    (ROOT / "tests/fixtures/professional_quote_review_cases.yaml").read_text(encoding="utf-8")
)


@pytest.fixture(scope="module")
def conn():
    try:
        connection = store.connect()
        connection.autocommit = True
    except Exception as exc:  # pragma: no cover - local unit-only lane
        pytest.skip(f"pgvector unreachable: {exc}")
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture(scope="module")
def contract():
    return load_contract(ROOT / "dossiers/devis_reprise/task_contract.yaml")


@pytest.fixture(scope="module")
def ingested(conn, contract):
    # Idempotent fixture preparation. Another integration module may already
    # have ingested the same synthetic dossier.
    store.ingest(conn, contract, ROOT)
    return True


def _source_rank(chunks, expected_source: str) -> int | None:
    for rank, chunk in enumerate(chunks, start=1):
        if chunk.source_ref == expected_source:
            return rank
    return None


def _hybrid_source_rank(hits, expected_source: str) -> int | None:
    for rank, hit in enumerate(hits, start=1):
        if hit.chunk.source_ref == expected_source:
            return rank
    return None


def _hybrid_signature(hits) -> list[tuple]:
    return [
        (
            hit.chunk.source_ref,
            hit.chunk.chunk_no,
            hit.semantic_rank,
            hit.lexical_rank,
            hit.hybrid_score,
        )
        for hit in hits
    ]


def test_labelled_case_fixture_is_bounded_and_explicit() -> None:
    assert len(CASES) == 9
    assert len({case["case_id"] for case in CASES}) == len(CASES)
    for case in CASES:
        assert case["query"].strip()
        if case.get("observation_only"):
            assert case.get("known_limit")
        else:
            assert case["expected_source"]
            assert case["lexical_max_rank"] >= 1
            assert case["hybrid_max_rank"] >= 1


def test_professional_review_oracle_is_bounded_human_input(contract) -> None:
    assert PROFESSIONAL_REVIEW["corpus_id"] == "devis_reprise"
    assert PROFESSIONAL_REVIEW["status"] == "synthetic_human_labelled"
    assert "project_document_currentness" in PROFESSIONAL_REVIEW["authority_note"]
    assert "observed_results" not in PROFESSIONAL_REVIEW
    assert "quality_score" not in PROFESSIONAL_REVIEW

    declared = set(PROFESSIONAL_REVIEW["declared_source_refs"])
    controls = set(PROFESSIONAL_REVIEW["control_source_refs"])
    assert declared <= set(contract.sources)
    assert controls.isdisjoint(contract.sources)
    assert len(PROFESSIONAL_REVIEW["cases"]) == 9
    assert len({case["case_id"] for case in PROFESSIONAL_REVIEW["cases"]}) == 9

    for case in PROFESSIONAL_REVIEW["cases"]:
        assert case["expected_posture"]
        assert case["human_label"]
        assert case["required_observations"]
        assert case["forbidden_claims"]
        assert set(case["source_refs"]) <= declared


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["case_id"])
def test_labelled_metier_retrieval_cases(conn, contract, ingested, case) -> None:
    lexical = retrieve_lexical_scoped(conn, contract, case["query"], top_k=8)
    hybrid = retrieve_hybrid_scoped(
        conn,
        contract,
        case["query"],
        top_k=8,
        candidate_k=12,
    )

    assert hybrid, f"{case['case_id']}: hybrid retrieval returned no candidates"

    lexical_keys = [(chunk.source_ref, chunk.chunk_no) for chunk in lexical]
    hybrid_keys = [(hit.chunk.source_ref, hit.chunk.chunk_no) for hit in hybrid]
    assert len(lexical_keys) == len(set(lexical_keys))
    assert len(hybrid_keys) == len(set(hybrid_keys))

    for chunk in [*lexical, *(hit.chunk for hit in hybrid)]:
        assert chunk.source_ref in contract.sources
        assert chunk.contract_id == contract.contract_id
        assert chunk.contract_digest
        assert chunk.ingestion_id
        assert chunk.source_digest

    if case.get("observation_only"):
        # These cases characterize known quality limits. They still enforce the
        # hard perimeter/provenance invariants but do not invent a semantic SLA.
        return

    lexical_rank = _source_rank(lexical, case["expected_source"])
    hybrid_rank = _hybrid_source_rank(hybrid, case["expected_source"])
    assert lexical_rank is not None, f"{case['case_id']}: expected lexical source absent"
    assert hybrid_rank is not None, f"{case['case_id']}: expected hybrid source absent"
    assert lexical_rank <= case["lexical_max_rank"]
    assert hybrid_rank <= case["hybrid_max_rank"]


def test_hybrid_relevance_order_is_repeatable(conn, contract, ingested) -> None:
    query = "membrane bicouche élastomère"
    first = retrieve_hybrid_scoped(conn, contract, query, top_k=8, candidate_k=12)
    second = retrieve_hybrid_scoped(conn, contract, query, top_k=8, candidate_k=12)
    assert _hybrid_signature(first) == _hybrid_signature(second)


def test_semantic_order_is_total_when_distances_tie(conn, contract, ingested) -> None:
    """Equal distances must be separated by the query, not by the row layout.

    `test_hybrid_relevance_order_is_repeatable` asserts the property but can only
    catch a violation when the planner happens to reorder, which made it a
    recurring CI failure rather than a signal. This plants the tie instead of
    waiting for one: two chunks with the same body embed to the same vector, so
    the query that is that body puts both at distance 0 and the ORDER BY has
    nothing left to separate them except its tiebreak.

    Planting once is not enough to detect the regression. `chunks` carries no
    vector index, so the tied rows reach the sort in heap order, which follows
    insertion order; if they were only ever inserted in ascending key order,
    `ORDER BY distance` alone would return them already sorted and the test
    would pass on the defect. So the tie is planted in both insertion orders
    and the same ascending answer is required from both. A query that sorts on
    distance alone follows its input and can satisfy at most one of them.
    """
    body = "zzz tie-break probe chunk, identical in both sources"
    declared = list(contract.sources)[:2]
    assert len(declared) == 2, "this dossier needs two declared sources"

    digests: dict[str, str] = {}
    with conn.cursor() as cur:
        for source_ref in declared:
            cur.execute(
                "SELECT source_digest FROM source_documents"
                " WHERE dossier = %s AND source_ref = %s LIMIT 1",
                (contract.dossier, source_ref),
            )
            row = cur.fetchone()
            assert row is not None, f"{source_ref} is not ingested"
            digests[source_ref] = row[0]

    keys = {(source_ref, digest, 920) for source_ref, digest in digests.items()}

    def _clear() -> None:
        with conn.cursor() as cur:
            for source_ref, digest, chunk_no in keys:
                cur.execute(
                    "DELETE FROM chunks WHERE dossier = %s AND source_ref = %s"
                    "   AND source_digest = %s AND chunk_no = %s",
                    (contract.dossier, source_ref, digest, chunk_no),
                )

    def _plant(insertion_order: list[str]) -> list[tuple[str, str, int]]:
        _clear()
        with conn.cursor() as cur:
            for source_ref in insertion_order:
                cur.execute(
                    """
                    INSERT INTO chunks
                        (dossier, source_ref, source_digest, chunk_no, body, embedding)
                    VALUES (%s, %s, %s, 920, %s, %s::vector)
                    """,
                    (
                        contract.dossier,
                        source_ref,
                        digests[source_ref],
                        body,
                        to_pgvector(embed(body)),
                    ),
                )
        seen = [
            (chunk.source_ref, chunk.source_digest, chunk.chunk_no)
            for chunk in store.retrieve_scoped(conn, contract, body, top_k=12)
        ]
        return [item for item in seen if item in keys]

    try:
        for insertion_order in (declared, list(reversed(declared))):
            tied = _plant(insertion_order)
            assert len(tied) == 2, f"both planted chunks should rank; got {tied}"
            assert tied == sorted(tied), (
                "tied chunks came back out of the declared tiebreak order after "
                f"inserting them as {insertion_order}: {tied}. ORDER BY distance "
                "alone follows the row layout instead of deciding."
            )
    finally:
        _clear()


def test_lexical_and_hybrid_paths_reject_planted_scope_markers(
    conn, contract, ingested
) -> None:
    marker = "xylophoniquezeta"
    undeclared_source = "dossiers/devis_reprise/sources/NOT_DECLARED_RELEVANCE.md"
    other_dossier = "retrieval_other_dossier"
    declared_source = contract.sources[0]

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO chunks (dossier, source_ref, source_digest, chunk_no, body, embedding)
            VALUES (%s, %s, '', 910, %s, %s::vector)
            ON CONFLICT (dossier, source_ref, source_digest, chunk_no) DO UPDATE SET
                body = EXCLUDED.body,
                embedding = EXCLUDED.embedding
            """,
            (
                contract.dossier,
                undeclared_source,
                marker,
                to_pgvector(embed(marker)),
            ),
        )
        cur.execute(
            """
            INSERT INTO chunks (dossier, source_ref, source_digest, chunk_no, body, embedding)
            VALUES (%s, %s, '', 911, %s, %s::vector)
            ON CONFLICT (dossier, source_ref, source_digest, chunk_no) DO UPDATE SET
                body = EXCLUDED.body,
                embedding = EXCLUDED.embedding
            """,
            (
                other_dossier,
                declared_source,
                marker,
                to_pgvector(embed(marker)),
            ),
        )

    try:
        lexical = retrieve_lexical_scoped(conn, contract, marker, top_k=8)
        hybrid = retrieve_hybrid_scoped(
            conn,
            contract,
            marker,
            top_k=8,
            candidate_k=12,
        )
        returned = [*lexical, *(hit.chunk for hit in hybrid)]
        assert all(chunk.source_ref in contract.sources for chunk in returned)
        assert all(marker not in chunk.body for chunk in returned)
    finally:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM chunks WHERE dossier = %s AND source_ref = %s AND chunk_no = 910",
                (contract.dossier, undeclared_source),
            )
            cur.execute(
                "DELETE FROM chunks WHERE dossier = %s AND source_ref = %s AND chunk_no = 911",
                (other_dossier, declared_source),
            )
