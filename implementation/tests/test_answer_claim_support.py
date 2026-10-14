"""Answer-level support binding stays exact without becoming truth verification."""

from __future__ import annotations

from pathlib import Path

import pytest

from mvp_vertical import runner
from mvp_vertical.contract import load_contract
from mvp_vertical.drafting import DraftRejected, claim_support_review, verify_draft
from mvp_vertical.store import RetrievedChunk


ROOT = Path(__file__).resolve().parents[1]
SOURCE = "dossiers/devis_reprise/sources/cctp_lot_06.md"


def _contract():
    return load_contract(ROOT / "dossiers/devis_reprise" / "task_contract.yaml")


def _chunk(
    *,
    digest: str = "a" * 64,
    page_start: int | None = 7,
    structural_locator: str = "section:CCTP/lot-06",
    distance: float = 0.2,
) -> RetrievedChunk:
    return RetrievedChunk(
        source_ref=SOURCE,
        chunk_no=0,
        body="Le passage décrit le périmètre du lot 06.",
        distance=distance,
        source_digest=digest,
        content_type="paragraph",
        page_start=page_start,
        page_end=page_start,
        structural_locator=structural_locator,
        section_path=("CCTP", "lot 06"),
    )


def test_same_textual_citation_is_rejected_when_two_digests_make_it_ambiguous() -> None:
    draft = f"Selon [{SOURCE}#chunk-0], le devis est conforme au CCTP."
    old = _chunk(digest="a" * 64)
    new = _chunk(digest="b" * 64)

    with pytest.raises(DraftRejected, match="ambiguous across retrieved source revisions"):
        verify_draft(draft, [old, new])


def test_claim_support_binding_keeps_digest_and_exact_locator_without_promoting_truth() -> None:
    chunk = _chunk()
    draft = f"Selon [{SOURCE}#chunk-0], le devis est conforme au CCTP."

    review = claim_support_review(draft, [chunk])

    assert review["status"] == "sourced_not_verified"
    assert review["status"] != "verified"
    assert review["unsupported_claims"] == []
    binding = review["supported_claims"][0]
    assert binding["support_status"] == "sourced_not_verified"
    assert binding["support_status"] != "verified"
    support = binding["supports"][0]
    assert support["source_digest"] == "a" * 64
    assert support["page_start"] == 7
    assert support["page_end"] == 7
    assert support["structural_locator"] == "section:CCTP/lot-06"
    assert support["support_status"] == "sourced_not_verified"
    assert support["support_status"] != "verified"


def test_missing_page_is_visible_and_never_fabricated() -> None:
    chunk = _chunk(page_start=None, structural_locator="section:CCTP/lot-06")
    draft = f"Selon [{SOURCE}#chunk-0], le devis est conforme au CCTP."

    support = claim_support_review(draft, [chunk])["supported_claims"][0]["supports"][0]

    assert support["page_start"] is None
    assert support["page_end"] is None
    assert support["page_locator_available"] is False
    assert support["structural_locator"] == "section:CCTP/lot-06"


def test_runner_refuses_uncited_assertive_claim_without_model_fallback(monkeypatch) -> None:
    chunk = _chunk()
    monkeypatch.setattr(runner, "retrieve_scoped", lambda *_args, **_kwargs: [chunk])

    class UnsupportedDrafter:
        def draft(self, *, intent, question, chunks):
            return "Le devis est conforme au CCTP."

    output = runner.run(object(), _contract(), "Le devis est-il conforme ?", drafter=UnsupportedDrafter())

    assert output.kind == "refusal"
    refusal = output.documents[0]["refusal"]
    assert refusal["reason"] == "unsupported_claim"
    assert "model knowledge" in refusal["detail"]
    assert output.documents[0]["external_action_authorized"] is False


def test_runner_emits_exact_claim_to_evidence_binding_but_not_verification(monkeypatch) -> None:
    chunk = _chunk(distance=0.01)
    monkeypatch.setattr(runner, "retrieve_scoped", lambda *_args, **_kwargs: [chunk])

    class CitedDrafter:
        def draft(self, *, intent, question, chunks):
            return f"Selon [{SOURCE}#chunk-0], le devis est conforme au CCTP."

    output = runner.run(object(), _contract(), "Le devis est-il conforme ?", drafter=CitedDrafter())

    assert output.kind == "candidates"
    result_candidate, evidence_pack = output.documents
    assert result_candidate["claim_support_review"]["status"] == "sourced_not_verified"
    assert result_candidate["claim_support_review"]["status"] != "verified"
    assert result_candidate["citation_integrity_verified"] is True
    assert "grounding_verified" not in result_candidate

    item = evidence_pack["evidence_items"][0]
    assert item["support_status"] == "sourced_not_verified"
    assert item["support_status"] != "verified"
    assert item["retrieval_metrics"]["distance"] == 0.01
    assert item["retrieval_metrics"]["interpretation"] == "lower_is_closer_not_truth_probability"

    binding = evidence_pack["claim_support_bindings"][0]
    assert binding["support_status"] == "sourced_not_verified"
    assert binding["support_status"] != "verified"
    support = binding["supports"][0]
    assert support["support_status"] == "sourced_not_verified"
    assert support["support_status"] != "verified"
    assert support["source_digest"] == "a" * 64
    assert support["evidence_item_ref"] == item["evidence_id"]
    assert support["page_start"] == 7
    assert support["structural_locator"] == "section:CCTP/lot-06"
