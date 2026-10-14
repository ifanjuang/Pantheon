"""Measured Pantheon-Next#908 comparison between Haystack and the current native retrieval lane.

This is a qualification observation, not a provider-selection SLA. Both providers
receive the same Pantheon-resolved exact source identities and the same derivative
chunk text. Quality observations are printed for review while hard assertions stay
on execution, scope and provenance boundaries.
"""

from __future__ import annotations

import importlib.util
import json
import runpy
from pathlib import Path
from statistics import median
import sys
from time import perf_counter_ns

import pytest
import yaml

pytest.importorskip("haystack")

from mvp_vertical import retrieval, retrieval_scope


ROOT = Path(__file__).resolve().parents[1]
BASELINE = runpy.run_path(
    str(Path(__file__).with_name("test_professional_quote_review_baseline.py"))
)
ORACLE = BASELINE["ORACLE"]
_connect_or_skip = BASELINE["_connect_or_skip"]
_qualification_contract = BASELINE["_qualification_contract"]
_prepare_project_review_scope = BASELINE["_prepare_project_review_scope"]
METIER_CASES = yaml.safe_load(
    (ROOT / "tests/fixtures/retrieval_metier_cases.yaml").read_text(encoding="utf-8")
)

LAB = ROOT / "labs" / "haystack_retrieval" / "adapter.py"
SPEC = importlib.util.spec_from_file_location("pantheon_haystack_908_comparison_adapter", LAB)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

BoundedSourceMaterial = MODULE.BoundedSourceMaterial
HaystackBoundedRetrievalAdapter = MODULE.HaystackBoundedRetrievalAdapter


def _ordered_unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _native_source_refs(hits) -> list[str]:
    return _ordered_unique([hit.source_ref for hit in hits])


def _haystack_source_refs(result) -> list[str]:
    return _ordered_unique([candidate.source_ref for candidate in result.candidates])


def _rank(source_refs: list[str], expected_source: str) -> int | None:
    try:
        return source_refs.index(expected_source) + 1
    except ValueError:
        return None


def _median_ms(callable_, repeats: int = 5) -> float:
    callable_()  # warm the already-created provider/runtime path
    samples: list[float] = []
    for _ in range(repeats):
        started = perf_counter_ns()
        callable_()
        samples.append((perf_counter_ns() - started) / 1_000_000)
    return round(float(median(samples)), 3)


def _material_from_exact_chunks(conn, source):
    rows = conn.execute(
        """
        SELECT chunk_no, body
          FROM chunks
         WHERE dossier = %s
           AND source_ref = %s
           AND source_digest = %s
         ORDER BY chunk_no ASC
        """,
        (source.dossier, source.source_ref, source.source_digest),
    ).fetchall()
    assert rows, f"no native chunks found for exact source {source.source_ref}"
    return BoundedSourceMaterial(
        source=source,
        content="\n\n".join(row[1] for row in rows),
    )


def test_measured_haystack_vs_native_exact_scoped_retrieval_is_observed_not_assumed() -> None:
    conn = _connect_or_skip()
    contract, project_id = _qualification_contract()

    try:
        principal, requested_documents = _prepare_project_review_scope(
            conn,
            contract,
            project_id,
        )
        resolution = retrieval_scope.resolve_accessible_applicable_sources(
            conn,
            principal,
            contract=contract,
            project_id=project_id,
            requested_documents=requested_documents,
        )
        exact_sources = tuple(
            (source.source_ref, source.source_digest) for source in resolution.sources
        )
        allowed_refs = {source_ref for source_ref, _digest in exact_sources}
        allowed_identities = set(exact_sources)
        control_refs = set(ORACLE["control_source_refs"])

        assert allowed_refs == set(ORACLE["declared_source_refs"])
        assert control_refs.isdisjoint(allowed_refs)

        materials = [
            _material_from_exact_chunks(conn, source) for source in resolution.sources
        ]
        adapter = HaystackBoundedRetrievalAdapter(
            binding_instance_id=f"lab-908-comparison-{project_id}"
        )
        projection_started = perf_counter_ns()
        adapter.reconcile(resolution, materials)
        projection_ms = round((perf_counter_ns() - projection_started) / 1_000_000, 3)

        labelled_cases = [
            case
            for case in METIER_CASES
            if not case.get("observation_only")
            and case.get("expected_source") in allowed_refs
        ]
        assert labelled_cases

        observations: list[dict] = []
        for case in labelled_cases:
            query = case["query"]

            def native_query():
                return retrieval.retrieve_lexical_exact_scoped(
                    conn,
                    contract,
                    query,
                    sources=exact_sources,
                    top_k=12,
                )

            def haystack_query():
                return adapter.retrieve(
                    resolution,
                    query=query,
                    top_k=max(1, len(exact_sources)),
                )

            native_hits = native_query()
            haystack_result = haystack_query()
            native_refs = _native_source_refs(native_hits)
            haystack_refs = _haystack_source_refs(haystack_result)

            assert set(native_refs) <= allowed_refs
            assert set(haystack_refs) <= allowed_refs
            assert control_refs.isdisjoint(native_refs)
            assert control_refs.isdisjoint(haystack_refs)
            assert all(
                (hit.source_ref, hit.source_digest) in allowed_identities
                for hit in native_hits
            )
            assert all(
                (candidate.source_ref, candidate.source_digest) in allowed_identities
                for candidate in haystack_result.candidates
            )
            assert haystack_result.evidence_admitted is False
            assert haystack_result.authorized_effect is False

            expected_source = case["expected_source"]
            native_rank = _rank(native_refs, expected_source)
            haystack_rank = _rank(haystack_refs, expected_source)
            observations.append(
                {
                    "case_id": case["case_id"],
                    "category": case["category"],
                    "query": query,
                    "expected_source": expected_source,
                    "native_source_rank": native_rank,
                    "haystack_source_rank": haystack_rank,
                    "rank_delta_haystack_minus_native": (
                        haystack_rank - native_rank
                        if native_rank is not None and haystack_rank is not None
                        else None
                    ),
                    "native_returned_sources": native_refs,
                    "haystack_returned_sources": haystack_refs,
                    "native_query_median_ms": _median_ms(native_query),
                    "haystack_query_median_ms": _median_ms(haystack_query),
                }
            )

        professional_query = ORACLE["review_request"]
        native_professional = retrieval.retrieve_lexical_exact_scoped(
            conn,
            contract,
            professional_query,
            sources=exact_sources,
            top_k=12,
        )
        haystack_professional = adapter.retrieve(
            resolution,
            query=professional_query,
            top_k=max(1, len(exact_sources)),
        )
        native_professional_refs = _native_source_refs(native_professional)
        haystack_professional_refs = _haystack_source_refs(haystack_professional)

        assert set(native_professional_refs) <= allowed_refs
        assert set(haystack_professional_refs) <= allowed_refs
        assert control_refs.isdisjoint(native_professional_refs)
        assert control_refs.isdisjoint(haystack_professional_refs)

        native_top1 = sum(
            item["native_source_rank"] == 1 for item in observations
        )
        haystack_top1 = sum(
            item["haystack_source_rank"] == 1 for item in observations
        )
        native_present = sum(
            item["native_source_rank"] is not None for item in observations
        )
        haystack_present = sum(
            item["haystack_source_rank"] is not None for item in observations
        )

        report = {
            "schema": "pantheon-haystack-native-retrieval-comparison.v1",
            "issue": 908,
            "corpus_id": ORACLE["corpus_id"],
            "posture": "qualification_observation_only_no_binding_selection",
            "scope": {
                "project_id": project_id,
                "source_refs": sorted(allowed_refs),
                "source_count": len(allowed_refs),
                "control_refs_excluded": sorted(control_refs),
            },
            "providers": {
                "native": {
                    "implementation": "retrieve_lexical_exact_scoped",
                    "store": "postgresql_pgvector_existing_runtime",
                },
                "haystack": {
                    "implementation": "InMemoryBM25Retriever",
                    "version": adapter.provider_version,
                    "store": "InMemoryDocumentStore_qualification_only",
                    "projection_ms": projection_ms,
                },
            },
            "labelled_cases": observations,
            "summary": {
                "labelled_case_count": len(observations),
                "native_expected_source_present": native_present,
                "haystack_expected_source_present": haystack_present,
                "native_top1_hits": native_top1,
                "haystack_top1_hits": haystack_top1,
                "top1_delta_haystack_minus_native": haystack_top1 - native_top1,
                "native_case_query_median_ms": round(
                    float(median(item["native_query_median_ms"] for item in observations)),
                    3,
                ),
                "haystack_case_query_median_ms": round(
                    float(median(item["haystack_query_median_ms"] for item in observations)),
                    3,
                ),
            },
            "professional_request": {
                "native_returned_sources": native_professional_refs,
                "haystack_returned_sources": haystack_professional_refs,
                "native_source_coverage": len(set(native_professional_refs) & allowed_refs),
                "haystack_source_coverage": len(set(haystack_professional_refs) & allowed_refs),
                "admitted_source_count": len(allowed_refs),
            },
            "limitations": [
                "Haystack uses the qualification-only in-memory BM25 store, while native retrieval uses the existing PostgreSQL runtime.",
                "Latency is CI-local process observation, not a production performance SLA.",
                "The active native semantic embedder remains a deterministic placeholder, so this slice compares exact lexical retrieval only.",
                "Provider scores and ranks remain candidate-context signals, not truth, Evidence quality or authorization.",
            ],
        }
        print(
            "HAYSTACK_NATIVE_RETRIEVAL_COMPARISON="
            + json.dumps(report, ensure_ascii=False, sort_keys=True)
        )
    finally:
        conn.close()
