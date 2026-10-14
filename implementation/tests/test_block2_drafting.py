"""Block 2 — the drafting seam.

The deterministic default drafter must be dossier-general (no devis_reprise
hardcode) and must assert nothing — it assembles evidence and defers to the
human gate. The pure drafter is tested without pgvector; the run()-level
injection is tested against a live pgvector service in CI.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from mvp_vertical import store
from mvp_vertical.contract import load_contract
from mvp_vertical.drafting import (
    DeterministicDrafter,
    DraftRejected,
    duty_of_care_flags,
    grounding_review,
    review_flags,
    verify_draft,
)
from mvp_vertical.runner import run
from mvp_vertical.store import RetrievedChunk


def _chunk(source_ref: str, body: str, chunk_no: int = 0, distance: float = 0.3) -> RetrievedChunk:
    return RetrievedChunk(source_ref=source_ref, chunk_no=chunk_no, body=body, distance=distance)


# ---- DB-free: the deterministic drafter generalises and asserts nothing ------

def test_deterministic_drafter_speaks_to_the_actual_dossier():
    drafter = DeterministicDrafter()
    chunks = [
        _chunk(
            "dossiers/permis_amenagement/sources/note_plu_hauteurs.md",
            "En zone UB, la hauteur maximale est de 9 m à l'égout. Une surélévation d'un niveau est admise.",
        )
    ]
    body = drafter.draft(
        intent="Vérifier la faisabilité d'une surélévation au regard du PLU.",
        question="quelle hauteur maximale ?",
        chunks=chunks,
    )
    # speaks to THIS dossier via the cited passage…
    assert "surélévation" in body or "PLU" in body
    # …and carries none of the devis_reprise hardcode Block 1 emitted
    assert "Q-2026-041" not in body
    assert "terrasses" not in body


def test_deterministic_drafter_asserts_no_conclusion():
    body = DeterministicDrafter().draft(intent="", question="x", chunks=[_chunk("s.md", "texte source")])
    assert "candidat soumis à votre décision" in body
    assert "aucune conclusion n'est tirée" in body.lower()
    # it must never author an acceptance/commitment on the practitioner's behalf
    for banned in ("nous acceptons", "nous validons", "bon pour accord", "nous confirmons"):
        assert banned not in body.lower()


def test_deterministic_drafter_preserves_contradictions_by_restating():
    # Two conflicting passages both appear verbatim — the drafter neither
    # detects nor resolves the conflict; it is preserved by inclusion.
    chunks = [
        _chunk("a.md", "le poste 4 couvre les terrasses T2 et T3"),
        _chunk("b.md", "le lot 06 est limité à la seule terrasse T2"),
    ]
    body = DeterministicDrafter().draft(intent="", question="x", chunks=chunks)
    assert "T2 et T3" in body
    assert "la seule terrasse T2" in body


def test_deterministic_drafter_satisfies_the_seam():
    # A Hermes-side LLM drafter would satisfy the same Drafter seam; the default
    # is this offline deterministic one (no provider wired in this repo).
    drafter = DeterministicDrafter()
    assert callable(getattr(drafter, "draft", None))
    body = drafter.draft(intent="i", question="q", chunks=[_chunk("s.md", "b")])
    assert isinstance(body, str) and body


def test_query_metrics_remain_trace_scoped_not_truth_scores(monkeypatch):
    contract = load_contract(ROOT / "dossiers" / "devis_reprise" / "task_contract.yaml")
    chunks = [
        _chunk("dossiers/devis_reprise/sources/cctp_lot_06.md", "Passage le plus proche", 0, 0.2),
        _chunk("dossiers/devis_reprise/sources/devis_q-2026-041.md", "Passage suivant", 1, 0.4),
    ]
    monkeypatch.setattr("mvp_vertical.runner.retrieve_scoped", lambda *_args, **_kwargs: chunks)

    output = run(object(), contract, "Quels passages sont proches ?")
    evidence_items = output.documents[1]["evidence_items"]

    assert [item["retrieval_metrics"]["rank"] for item in evidence_items] == [1, 2]
    assert [item["retrieval_metrics"]["distance"] for item in evidence_items] == [0.2, 0.4]
    assert all(
        item["retrieval_metrics"]["interpretation"]
        == "lower_is_closer_not_truth_probability"
        for item in evidence_items
    )
    assert all(item["support_status"] == "sourced_not_verified" for item in evidence_items)


# ---- DB-free: the draft verifier makes the seam safe for an untrusted drafter -

def test_verifier_accepts_the_deterministic_drafter_output():
    chunks = [_chunk("dossiers/d/a.md", "un extrait", 0), _chunk("dossiers/d/b.md", "un autre", 3)]
    body = DeterministicDrafter().draft(intent="i", question="q", chunks=chunks)
    verify_draft(body, chunks)  # must not raise on its own default drafter


def test_verifier_rejects_a_fabricated_source():
    # An (LLM) drafter that cites a source it was never given.
    chunks = [_chunk("dossiers/d/a.md", "un extrait", 0)]
    forged = "Voici l'appui : - [dossiers/d/secret_non_declare.md#chunk-0] inventé…"
    with pytest.raises(DraftRejected):
        verify_draft(forged, chunks)


def test_verifier_rejects_a_fabricated_chunk_index():
    # Real source, but a chunk number that was not retrieved.
    chunks = [_chunk("dossiers/d/a.md", "un extrait", 0)]
    forged = "Appui : - [dossiers/d/a.md#chunk-7] passage jamais récupéré…"
    with pytest.raises(DraftRejected):
        verify_draft(forged, chunks)


def test_review_flags_surface_a_professional_verdict():
    # A drafter that resolves/asserts ("le devis est conforme") is not blocked
    # structurally — it is flagged for the human gate (heuristic, advisory).
    flagged = "Après analyse, le devis est conforme au CCTP ; vous pouvez signer."
    flags = review_flags(flagged)
    assert flags and any("conclusion" in f["risk"] for f in flags)
    # the neutral deferral draft raises no such flag
    assert review_flags(DeterministicDrafter().draft(intent="", question="q",
                        chunks=[_chunk("s.md", "b")])) == []


def test_review_flags_catch_a_legal_qualification():
    # C2-bis (SPS case): asserting a point of law is exactly what objectivité/
    # équité forbids the architect from doing lightly. The old patterns missed
    # it because it carries no "je conclus / est conforme".
    legal = ("Le maître d'ouvrage est exempté des obligations de coordination "
             "SPS ; l'opération relève de la catégorie 3.")
    assert review_flags(legal), "a legal exemption asserted as settled must be flagged"


def test_duty_of_care_flags_fire_on_a_company_judgment():
    # The frequent gesture: judging/retaining a company. objectivité/équité and
    # the MAF duty-of-conseil apply; the cage surfaces the verifications it
    # cannot make, never asserting them done.
    judged = "Nous recommandons de retenir l'entreprise Alpha, la mieux-disante."
    flags = duty_of_care_flags(judged)
    assert flags, "a company judgment must raise duty-of-care flags"
    checks = flags[0]["verifications_not_established_here"]
    assert any("décennale" in c for c in checks)
    assert any("motivé par écrit" in c for c in checks)


def test_duty_of_care_flags_silent_on_neutral_restitution():
    # Merely mentioning "les entreprises" in restituted passages is not a
    # judgment — no false positive on the neutral deferral draft.
    neutral = DeterministicDrafter().draft(
        intent="", question="q",
        chunks=[_chunk("cctp.md", "les entreprises se conforment aux règles de l'art")])
    assert duty_of_care_flags(neutral) == []


# ---- DB-free: P5 advisory grounding visibility ------------------------------

def test_grounding_review_counts_citations_and_chunks():
    chunks = [_chunk("a.md", "x", 0), _chunk("b.md", "y", 1)]
    body = DeterministicDrafter().draft(intent="i", question="q", chunks=chunks)
    review = grounding_review(body, chunks)
    assert review["retrieved_chunk_count"] == 2
    assert review["citation_count"] == 2  # the default drafter cites each chunk
    assert review["uncited_claim_flags"] == []  # it asserts nothing


def test_grounding_review_flags_an_uncited_assertion():
    # Assertive prose with no citation in its sentence is surfaced (advisory).
    body = "Le devis est conforme au CCTP.\n- [a.md#chunk-0] extrait…"
    review = grounding_review(body, [_chunk("a.md", "extrait", 0)])
    assert review["uncited_claim_flags"], "an uncited verdict should be flagged"
    # uncited_claim_flags are strings (schema grounding_review def)
    assert "conforme" in review["uncited_claim_flags"][0]
    # a cited verdict in the same sentence is NOT flagged as uncited
    cited = "Selon [a.md#chunk-0], le devis est conforme."
    assert grounding_review(cited, [_chunk("a.md", "extrait", 0)])["uncited_claim_flags"] == []


def test_grounding_review_is_advisory_never_a_score():
    review = grounding_review("texte neutre", [])
    note = review["note"].lower()
    assert "not a score" in note and "not an approval" in note
    assert "absence of flags does not mean" in note


def test_cited_verdict_escapes_grounding_review_but_review_flags_catches_it():
    # Regression (review #3): a professional conclusion that carries a citation
    # in its own sentence is NOT surfaced by grounding_review.uncited_claim_flags,
    # so grounding_review alone lost the "reads as a verdict" signal. review_flags
    # detects the verdict regardless of citation — the two must both ride the
    # candidate. citation présente != conclusion professionnelle validée.
    chunks = [_chunk("a.md", "extrait", 0)]
    cited_verdict = "Selon [a.md#chunk-0], le devis est conforme au CCTP."
    assert grounding_review(cited_verdict, chunks)["uncited_claim_flags"] == []
    assert review_flags(cited_verdict), "review_flags must catch a cited verdict"


# ---- DB-gated: run() uses the injected drafter (CI pgvector) -----------------

@pytest.fixture(scope="module")
def conn():
    try:
        c = store.connect()
        # Autocommit: a module-scoped connection otherwise holds the implicit
        # transaction of its last statement — and its read locks — for the whole
        # module, stalling any TRUNCATE another suite runs. Code needing atomicity
        # uses conn.transaction() explicitly.
        c.autocommit = True
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"pgvector unreachable: {exc}")
    try:
        yield c
    finally:
        c.close()


@pytest.fixture(scope="module")
def contract():
    return load_contract(ROOT / "dossiers/devis_reprise/task_contract.yaml")


@pytest.fixture(scope="module")
def ingested(conn, contract):
    return store.ingest(conn, contract, ROOT)


def test_run_uses_the_injected_drafter(conn, contract, ingested):
    class StubDrafter:
        def draft(self, *, intent, question, chunks):
            return f"STUB::{len(chunks)}"

    out = run(conn, contract,
              "le devis de reprise correspond-il au périmètre du CCTP pour le lot 06 ?",
              drafter=StubDrafter())
    assert out.kind == "candidates"
    assert out.documents[0]["body"].startswith("STUB::")


def test_default_run_is_dossier_general_on_devis(conn, contract, ingested):
    out = run(conn, contract, "le devis de reprise correspond-il au périmètre du CCTP pour le lot 06 ?")
    assert out.kind == "candidates"
    rc, ep = out.documents
    body = rc["body"]
    # the default drafter no longer authors the hardcoded devis analysis…
    assert "poste 4 du devis" not in body
    # …but the contradiction is still preserved, now by including both passages
    assert ep["contradictions_preserved"]
    assert len(ep["evidence_items"]) >= 2
    # the candidate carries the honest structural trace — citation integrity,
    # not a grounding/truth claim (review #4: grounding_verified overclaimed)
    assert rc["citation_integrity_verified"] is True
    assert "grounding_verified" not in rc  # the overclaiming key is gone
    # …the citation-independent professional-verdict flags (review #3)…
    assert "professional_assertion_flags" in rc
    # …the duty-of-care flags (advisory, deontology anchor)…
    assert "duty_of_care_flags" in rc
    assert "docs/governance/PROFESSIONAL_DUTY_OF_CARE.md" in rc["governance_refs"]
    # …and the advisory grounding-visibility block (counts + note, no score)
    gr = rc["grounding_review"]
    assert gr["retrieved_chunk_count"] >= 2 and gr["citation_count"] >= 1
    assert "not a score" in gr["note"].lower()


def test_run_rejects_a_drafter_that_fabricates_a_source(conn, contract, ingested):
    class FabricatingDrafter:
        def draft(self, *, intent, question, chunks):
            return "Appui : - [dossiers/devis_reprise/sources/INVENTE.md#chunk-0] faux…"

    with pytest.raises(DraftRejected):
        run(conn, contract,
            "le devis de reprise correspond-il au périmètre du CCTP pour le lot 06 ?",
            drafter=FabricatingDrafter())
