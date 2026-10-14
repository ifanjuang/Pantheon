"""Retrieval audit identity (external review, finding #6).

Every ingested chunk — and every evidence item derived from it — must be
provably tied to the contract version, the ingestion run, and the source
version that produced it:

    contract_id + contract_digest + ingestion_id + source_digest (per chunk)

The digest helper is DB-free; the round-trip through ingest → retrieve → run
is gated on a reachable pgvector (and, per finding #11, fails rather than skips
in CI).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]

from mvp_vertical import pantheon_contracts
from mvp_vertical import store
from mvp_vertical.contract import load_contract
from mvp_vertical.runner import run

CONTRACT = ROOT / "dossiers/devis_reprise/task_contract.yaml"


# ---- DB-free: the contract digest is a stable, content-bound sha256 ----------

def test_contract_digest_is_stable_and_content_bound():
    c = load_contract(CONTRACT)
    d1 = store.contract_digest(c)
    d2 = store.contract_digest(c)
    assert d1 == d2 and len(d1) == 64
    # a changed contract changes the digest (contract_digest reads only .raw)
    import copy
    from types import SimpleNamespace
    raw = copy.deepcopy(c.raw)
    raw["approval_ceiling"] = "C4"
    assert store.contract_digest(SimpleNamespace(raw=raw)) != d1


def test_retrieved_chunk_audit_defaults_are_empty_not_missing():
    # A manually constructed chunk (test helpers, legacy rows) stays valid.
    rc = store.RetrievedChunk("a.md", 0, "body", 0.3)
    assert rc.retrieval_audit == {
        "contract_id": "", "contract_digest": "", "ingestion_id": "", "source_digest": "",
    }
    assert rc.retrieval_provenance == {
        "content_type": "",
        "page_start": None,
        "page_end": None,
        "structural_locator": "",
        "parent_heading": None,
        "section_path": [],
        "quality_flags": [],
    }


# ---- DB-gated: the identity survives ingest → retrieve → run ----------------

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
    return load_contract(CONTRACT)


def test_ingested_chunks_carry_the_audit_identity(conn, contract):
    store.ingest(conn, contract, ROOT, ingestion_id="ing-fixed-001")
    chunks = store.retrieve_scoped(conn, contract, "isolation terrasse T2 lot 06 devis reprise")
    assert chunks, "retrieval returned nothing"
    cdigest = store.contract_digest(contract)
    for c in chunks:
        assert c.contract_id == contract.contract_id
        assert c.contract_digest == cdigest
        assert c.ingestion_id == "ing-fixed-001"
        assert len(c.source_digest) == 64  # sha256 of the source content
        assert c.structural_locator
        assert c.content_type


def test_reingesting_changes_the_ingestion_id(conn, contract):
    store.ingest(conn, contract, ROOT, ingestion_id="ing-A")
    first = store.retrieve_scoped(conn, contract, "devis reprise lot 06")
    store.ingest(conn, contract, ROOT, ingestion_id="ing-B")
    second = store.retrieve_scoped(conn, contract, "devis reprise lot 06")
    assert {c.ingestion_id for c in first} == {"ing-A"}
    assert {c.ingestion_id for c in second} == {"ing-B"}
    # same source content -> same source_digest across the two runs
    assert {c.source_digest for c in first} == {c.source_digest for c in second}


def test_evidence_items_carry_the_retrieval_audit(conn, contract):
    store.ingest(conn, contract, ROOT, ingestion_id="ing-ep-001")
    out = run(conn, contract, "le devis de reprise correspond-il au périmètre du CCTP pour le lot 06 ?")
    assert out.kind == "candidates"
    _, ep = out.documents
    assert ep["evidence_items"], "empty evidence pack"
    for item in ep["evidence_items"]:
        audit = item["retrieval_audit"]
        assert audit["contract_id"] == contract.contract_id
        assert audit["ingestion_id"] == "ing-ep-001"
        assert len(audit["contract_digest"]) == 64
        assert len(audit["source_digest"]) == 64
        provenance = item["retrieval_provenance"]
        assert provenance["structural_locator"]
        assert provenance["content_type"]
        metrics = item["retrieval_metrics"]
        assert metrics["rank"] >= 1
        assert 0 <= metrics["distance"] <= metrics["useful_distance_threshold"]
        assert metrics["metric"] == "cosine_distance"
        assert metrics["interpretation"] == "lower_is_closer_not_truth_probability"


def test_output_still_validates_against_vendored_schema(conn, contract):
    import jsonschema
    schema = pantheon_contracts.load_schema("mvp_governed_loop_objects")
    store.ingest(conn, contract, ROOT)
    out = run(conn, contract, "le devis de reprise correspond-il au périmètre du CCTP pour le lot 06 ?")
    for doc in out.documents:
        jsonschema.validate(doc, schema)  # retrieval_audit rides additionalProperties: true
