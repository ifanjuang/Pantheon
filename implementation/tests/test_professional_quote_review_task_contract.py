from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from mvp_vertical import runner
from mvp_vertical.contract import load_contract
from mvp_vertical.drafting import DeterministicDrafter
from mvp_vertical.retrieval import HybridRetrievedChunk
from mvp_vertical.store import RetrievedChunk


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "dossiers/devis_reprise/task_contract.yaml"
METHOD_PATH = ROOT.parent / "docs/domain-packs/architecture/DOCUMENT_REVIEW.md"
ORACLE_PATH = ROOT / "tests/fixtures/professional_quote_review_cases.yaml"
SUMMARY_ONLY_CONTRACT_PATHS = (
    ROOT / "dossiers/dce_relecture/task_contract.yaml",
    ROOT / "dossiers/litige_facture/task_contract.yaml",
    ROOT / "dossiers/permis_amenagement/task_contract.yaml",
    ROOT / "dossiers/strategie_energetique/task_contract.yaml",
)


def _text_block_after(marker: str) -> list[str]:
    text = METHOD_PATH.read_text(encoding="utf-8")
    tail = text.split(marker, 1)[1]
    match = re.search(r"```text\n(.*?)\n```", tail, re.DOTALL)
    assert match is not None, marker
    return [line.strip() for line in match.group(1).splitlines() if line.strip()]


def test_devis_reprise_contract_projects_current_document_review_method() -> None:
    contract = load_contract(CONTRACT_PATH)
    intent = contract.raw["intent"]
    method = intent["method_projection"]

    assert method["authority_ref"] == "docs/domain-packs/architecture/DOCUMENT_REVIEW.md"
    assert method["status"] == "task_scoped_non_authoritative_projection"
    assert method["use_case"] == "cctp_quote_comparison"
    assert method["acceptable_claim_types"] == _text_block_after("Acceptable claim types:")
    assert method["forbidden_outputs"] == _text_block_after("Forbidden output:")
    assert method["default_recommended_status"] == "requires_human_review"

    # Method projection is task data, not a parallel Capability/Skill admission.
    assert "capability_id" not in intent
    assert "skill" not in intent


def test_summary_only_contracts_keep_legacy_plain_drafter_intent() -> None:
    for path in SUMMARY_ONLY_CONTRACT_PATHS:
        contract = load_contract(path)
        assert set(contract.raw["intent"]) == {"summary"}
        assert contract.intent == contract.intent_summary
        assert isinstance(contract.intent, str)


@pytest.mark.parametrize(
    "summary",
    [
        "null",
        "123",
        '{"action":"review"}',
        '{"summary":"literal summary text"}',
    ],
)
def test_deterministic_drafter_preserves_json_looking_plain_summary(summary: str) -> None:
    body = DeterministicDrafter().draft(
        intent=summary,
        question="fallback question",
        chunks=[],
    )

    assert f"Votre demande : {summary}" in body
    assert "Votre demande : fallback question" not in body


def test_runner_transports_complete_review_method_to_drafter() -> None:
    contract = load_contract(CONTRACT_PATH)
    source_ref = contract.sources[0]
    chunk = RetrievedChunk(
        source_ref=source_ref,
        chunk_no=0,
        body="Le lot 06 décrit une prestation à examiner.",
        distance=0.01,
        source_digest="a" * 64,
        content_type="paragraph",
        page_start=1,
        page_end=1,
        structural_locator="section:lot-06",
        section_path=("lot 06",),
    )
    hit = HybridRetrievedChunk(
        chunk=chunk,
        hybrid_score=1.0,
        semantic_rank=1,
        lexical_rank=1,
    )
    observed: dict[str, object] = {}

    class CapturingDrafter:
        def draft(self, *, intent, question, chunks):
            observed["intent"] = intent
            return f"Point à examiner [{source_ref}#chunk-0]."

    output = runner._run_with_hits(
        contract,
        "Analyse le devis du lot couverture.",
        CapturingDrafter(),
        [hit],
    )

    assert output.kind == "candidates"
    assert observed["intent"] == contract.raw["intent"]
    assert observed["intent"] is not contract.raw["intent"]
    projected = observed["intent"]
    assert isinstance(projected, dict)
    assert projected["method_projection"]["authority_ref"] == (
        "docs/domain-packs/architecture/DOCUMENT_REVIEW.md"
    )
    assert projected["method_projection"]["status"] == (
        "task_scoped_non_authoritative_projection"
    )


def test_professional_oracle_uses_only_document_review_claim_types() -> None:
    contract = load_contract(CONTRACT_PATH)
    method_types = set(contract.raw["intent"]["method_projection"]["acceptable_claim_types"])
    oracle = yaml.safe_load(ORACLE_PATH.read_text(encoding="utf-8"))
    expected_types = {
        case["expected_claim_type"]
        for case in oracle["cases"]
        if case.get("expected_claim_type")
    }

    assert expected_types <= method_types


def test_devis_reprise_contract_no_longer_routes_a_reply_surface() -> None:
    contract = load_contract(CONTRACT_PATH)
    raw = contract.raw
    operations = raw["scope"]["operations"]

    assert "exposure_surface" not in raw
    assert "draft_reply_candidate" not in operations
    assert "prepare_result_candidate" in operations
    assert raw["expected_outputs"] == ["result_candidate", "evidence_pack_candidate"]
    assert "email" not in contract.intent_summary.casefold()
    assert raw["forbidden_scope"] == [
        "external_send",
        "source_outside_declared_perimeter",
        "register_write",
        "approval_of_any_kind",
    ]
