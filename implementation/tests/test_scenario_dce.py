"""Scenario tests on a second, real-shaped dossier (dce_relecture).

These prove the governance cage generalizes beyond devis_reprise and exercise
the critical situations catalogued in docs/test_scenarios/SCENARIO_CATALOGUE.md,
drawn from a real DCE (dossier de consultation des entreprises) relecture:

  C1  a request to DIFFUSE the DCE to companies is refused (external_send)
  C2  a draft that asserts a professional/legal verdict is flagged (advisory)
  C5  an out-of-perimeter question is refused (capability gap)
  +   a legitimate in-perimeter question yields a fully traceable candidate

The DB-free cases (C1, C2) run everywhere; the retrieval cases are gated on a
reachable pgvector, like the Block 1 suite.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]

from mvp_vertical import pantheon_contracts
from mvp_vertical import store
from mvp_vertical.contract import load_contract
from mvp_vertical.drafting import review_flags
from mvp_vertical.runner import run

CONTRACT = ROOT / "dossiers/dce_relecture/task_contract.yaml"


@pytest.fixture(scope="module")
def contract():
    return load_contract(CONTRACT)


# ---- DB-free: refusal and flag paths return before any retrieval ------------

@pytest.mark.parametrize("question", [
    "diffuse le CCAP aux entreprises",
    "peux-tu diffuser le DCE aux entreprises consultées ?",
    "envoie le dossier marché finalisé aux entreprises",
    "transmets le CCTP au maître d'ouvrage",
])
def test_C1_diffusion_or_send_is_refused(contract, question):
    # C1: diffusing/sending a DCE is a human decision. conn unused: the refusal
    # precedes retrieval. "diffuser" is the DCE-specific paraphrase of a send.
    out = run(None, contract, question)
    assert out.kind == "refusal"
    assert out.documents[0]["refusal"]["reason"] == "forbidden_scope"


def test_C2_a_legal_or_professional_verdict_is_flagged():
    # C2: the cage may not validate a clause. A draft that concludes the CCAP is
    # conforme and diffusable reads as a professional verdict and is surfaced to
    # the gate — advisory, never enforcement. citation présente != conclusion validée.
    verdict = ("Je conclus que la clause SPS §3 est conforme et que le CCAP "
               "peut être diffusé aux entreprises.")
    flags = review_flags(verdict)
    assert flags and any("conclusion" in f["risk"] for f in flags)


def test_contract_declares_a_second_dossier_with_four_sources(contract):
    # The cage is dossier-general: a distinct contract, four declared sources,
    # external_send forbidden — no devis_reprise specifics leaked in.
    assert contract.dossier == "dce_relecture"
    assert len(contract.sources) == 4
    assert "external_send" in contract.forbidden


# ---- DB-gated: ingest this second dossier and retrieve inside it -------------

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
def ingested(conn, contract):
    n = store.ingest(conn, contract, ROOT)
    assert n > 0
    return n


def test_in_perimeter_question_yields_a_traceable_candidate(conn, contract, ingested):
    # A legitimate question: what remains to correct before diffusion? The cage
    # produces a candidate sourced only from the declared perimeter.
    out = run(conn, contract,
              "quels points du CCAP et du CCTP restent-ils à corriger selon la relecture ?")
    assert out.kind == "candidates"
    rc, ep = out.documents
    assert rc["status"] == "draft_to_review"
    assert ep["evidence_items"], "empty evidence pack"
    for item in ep["evidence_items"]:
        assert item["source_ref"] in contract.sources, "perimeter breach"
        assert item["support_status"] == "sourced_not_verified"
    # it authorizes nothing and asserts no validated conclusion
    assert rc["external_action_authorized"] is False


def test_out_of_perimeter_question_is_refused(conn, contract, ingested):
    out = run(conn, contract, "quel est le prix moyen du m² à Lisbonne ?")
    assert out.kind == "refusal"
    assert out.documents[0]["status"] == "refused_capability_gap"
    assert out.documents[0]["refusal"]["reason"] == "outside_perimeter"


def test_output_validates_against_vendored_schema(conn, contract, ingested):
    import jsonschema
    schema = pantheon_contracts.load_schema("mvp_governed_loop_objects")
    out = run(conn, contract,
              "quels points du CCAP et du CCTP restent-ils à corriger selon la relecture ?")
    for doc in out.documents:
        jsonschema.validate(doc, schema)
