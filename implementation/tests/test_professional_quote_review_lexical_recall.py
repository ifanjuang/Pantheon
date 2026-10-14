"""Regression for Pantheon-Next#827 natural-language lexical candidate recall.

The professional corpus and currentness/access setup stay owned by the existing
baseline fixture. These checks cover only the retrieval failure measured in
Pantheon-Next#868: a long natural-language instruction must not collapse lexical recall to
zero merely because ``websearch_to_tsquery`` ANDs every framing word.
"""

from __future__ import annotations

import runpy
from pathlib import Path

from mvp_vertical import retrieval, retrieval_scope


BASELINE = runpy.run_path(
    str(Path(__file__).with_name("test_professional_quote_review_baseline.py"))
)
ORACLE = BASELINE["ORACLE"]
_connect_or_skip = BASELINE["_connect_or_skip"]
_qualification_contract = BASELINE["_qualification_contract"]
_prepare_project_review_scope = BASELINE["_prepare_project_review_scope"]


def test_long_form_fallback_is_plain_request_only() -> None:
    natural = ORACLE["review_request"]
    fallback = retrieval._lexical_fallback_query(natural)

    assert fallback is not None
    terms = {term.strip().casefold() for term in fallback.split(" OR ")}
    assert {"devis", "cctp", "dpgf", "06"} <= terms
    assert "le" not in terms
    assert "du" not in terms

    assert retrieval._lexical_fallback_query("devis lot 06") is None
    assert retrieval._lexical_fallback_query(
        'Analyse le devis avec la phrase "membrane SBS" pour cette qualification'
    ) is None
    assert retrieval._lexical_fallback_query(
        "Analyse le devis OR le CCTP pour cette qualification complète"
    ) is None
    assert retrieval._lexical_fallback_query(
        "Analyse le devis -variante pour cette qualification complète"
    ) is None


def test_professional_request_recovers_all_exact_selected_sources_lexically() -> None:
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

        hits = retrieval.retrieve_lexical_exact_scoped(
            conn,
            contract,
            ORACLE["review_request"],
            sources=exact_sources,
            top_k=12,
        )

        returned_sources = {hit.source_ref for hit in hits}
        assert returned_sources == set(ORACLE["declared_source_refs"])
        assert all(
            (hit.source_ref, hit.source_digest) in exact_sources
            for hit in hits
        )
    finally:
        conn.close()
