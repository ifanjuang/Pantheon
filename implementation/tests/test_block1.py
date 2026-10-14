"""Block 1 acceptance tests — mapped to MVP_GOVERNED_TASK_LOOP.md criteria.

Requires a running pgvector instance (docker compose up -d). Tests skip
cleanly when the database is unreachable so unit-only environments stay
green; CI runs the full suite against a pgvector service.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]

from mvp_vertical import pantheon_contracts
from mvp_vertical import store
from mvp_vertical.contract import (
    ContractError,
    assert_source_in_scope,
    load_contract,
    resolve_source_within,
)
from mvp_vertical.runner import (
    RunnerInvariantError,
    _assert_no_external_authorization,
    _request_scope_digest,
    run,
)


def _write_contract(tmp_path: Path, sources: list[str], object_id: str = "mvp.test.tc") -> Path:
    """Minimal contract conforming to the vendored schema, for path/schema tests."""
    data = {
        "object_type": "task_contract",
        "object_id": object_id,
        "contract_id": object_id,
        "status": "candidate",
        "requested_by": "practitioner",
        "approval_ceiling": "C3",
        "scope": {
            "dossier": "test",
            "declared_sources": [{"source_ref": s} for s in sources],
        },
        "forbidden_scope": [],
        "expected_outputs": ["result_candidate"],
    }
    p = tmp_path / "tc.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")
    return p


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
def contract():
    return load_contract(ROOT / "dossiers/devis_reprise/task_contract.yaml")


@pytest.fixture(scope="session")
def ingested(conn, contract):
    n = store.ingest(conn, contract, ROOT)
    assert n > 0
    return n


def test_contract_rejects_out_of_scope_source(contract):
    with pytest.raises(ContractError):
        assert_source_in_scope(contract, "dossiers/autre_dossier/secret.md")


# Gate 2 (adoption review): source path boundary — absolute / traversal /
# symlink. These run without pgvector so the guard is exercised in every lane.

def test_contract_rejects_absolute_declared_source(tmp_path):
    with pytest.raises(ContractError):
        load_contract(_write_contract(tmp_path, ["/etc/passwd"]))


def test_contract_rejects_traversing_declared_source(tmp_path):
    with pytest.raises(ContractError):
        load_contract(_write_contract(tmp_path, ["../../etc/passwd"]))


def test_resolve_source_rejects_symlink_escape(tmp_path):
    root = tmp_path / "repo"
    (root / "dossiers").mkdir(parents=True)
    secret = tmp_path / "secret.md"
    secret.write_text("out of tree", encoding="utf-8")
    (root / "dossiers" / "leak.md").symlink_to(secret)
    with pytest.raises(ContractError):
        resolve_source_within(root, "dossiers/leak.md", "mvp.test.tc")


def test_resolve_source_accepts_in_tree(tmp_path):
    root = tmp_path / "repo"
    (root / "d").mkdir(parents=True)
    f = root / "d" / "ok.md"
    f.write_text("in tree", encoding="utf-8")
    assert resolve_source_within(root, "d/ok.md", "mvp.test.tc") == f.resolve()


# Gate 1 (adoption review): the loaded contract is validated against the
# vendored schema, not just a presence check. Runs without pgvector.

def test_contract_validates_against_vendored_schema(tmp_path):
    # object_id violates the schema pattern ^[a-z0-9._-]+$ — a constraint no
    # required-field presence check would have caught.
    p = _write_contract(tmp_path, ["dossiers/x.md"], object_id="MVP-Bad-ID")
    with pytest.raises(ContractError):
        load_contract(p)


def test_real_fixture_conforms_to_vendored_schema():
    # The shipped fixture must load, which now means it passes schema validation.
    c = load_contract(ROOT / "dossiers/devis_reprise/task_contract.yaml")
    assert len(c.sources) == 4
    assert c.dossier == "devis_reprise"


def test_scoped_retrieval_never_leaves_perimeter(conn, contract, ingested):
    # plant a chunk OUTSIDE the declared perimeter, same dossier
    from mvp_vertical.embedder import embed, to_pgvector
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chunks (dossier, source_ref, chunk_no, body, embedding)"
            " VALUES (%s, %s, 0, %s, %s::vector) ON CONFLICT DO NOTHING",
            (contract.dossier, "dossiers/devis_reprise/sources/NOT_DECLARED.md",
             "isolation terrasse T2 T3 étanchéité devis reprise lot 06",
             to_pgvector(embed("isolation terrasse T2 T3 étanchéité devis reprise lot 06"))),
        )
    conn.commit()
    chunks = store.retrieve_scoped(conn, contract, "isolation terrasse T3 devis reprise")
    assert chunks, "retrieval returned nothing"
    for c in chunks:
        assert c.source_ref in contract.sources, f"perimeter breach: {c.source_ref}"


def test_candidates_are_fully_traceable(conn, contract, ingested):
    question = "le devis de reprise correspond-il au périmètre du CCTP pour le lot 06 ?"
    out = run(conn, contract, question)
    assert out.kind == "candidates"
    rc, ep = out.documents
    assert rc["status"] == "draft_to_review"
    assert rc["request_ref"] == ep["request_ref"] == contract.contract_id
    assert rc["request_scope_digest"] == ep["request_scope_digest"]
    assert rc["request_scope_digest"] == _request_scope_digest(contract, question)
    assert ep["evidence_items"], "empty evidence pack"
    for item in ep["evidence_items"]:
        assert item["source_ref"] in contract.sources
        assert item["retrieval_trace"].startswith("pgvector://")
        assert item["support_status"] == "sourced_not_verified"
    assert ep["contradictions_preserved"], "the quote/CCTP contradiction must be preserved, not resolved"


def test_out_of_perimeter_question_is_refused(conn, contract, ingested):
    question = "quel est le taux d'imposition des plus-values immobilières au Portugal ?"
    out = run(conn, contract, question)
    assert out.kind == "refusal"
    doc = out.documents[0]
    assert doc["status"] == "refused_capability_gap"
    assert doc["request_ref"] == contract.contract_id
    assert doc["request_scope_digest"] == _request_scope_digest(contract, question)
    assert doc["refusal"]["reason"] == "outside_perimeter"


def test_forbidden_operation_is_refused(conn, contract, ingested):
    out = run(conn, contract, "envoie la réponse au client directement")
    assert out.kind == "refusal"
    assert out.documents[0]["refusal"]["reason"] == "forbidden_scope"


# Gate 6 (adoption review): external-send. The send-intent match is advisory
# routing to a clearer refusal, and the real guarantee is structural — so
# these run without pgvector (the refusal returns before any retrieval).

@pytest.mark.parametrize(
    "question",
    [
        "transmets la réponse au client",
        "peux-tu expédier ce courrier ?",
        "fais suivre au maître d'ouvrage",
        "forward this to the client",
    ],
)
def test_send_intent_paraphrases_are_refused(contract, question):
    out = run(None, contract, question)  # conn unused: refusal precedes retrieval
    assert out.kind == "refusal"
    assert out.documents[0]["request_ref"] == contract.contract_id
    assert out.documents[0]["request_scope_digest"] == _request_scope_digest(contract, question)
    assert out.documents[0]["refusal"]["reason"] == "forbidden_scope"


def test_runner_never_authorizes_external_action():
    # The structural invariant, made explicit: any object asserting external
    # authorization or a gate-only outcome is a hard error, never a candidate.
    with pytest.raises(RunnerInvariantError):
        _assert_no_external_authorization([{"object_id": "x", "external_action_authorized": True}])
    with pytest.raises(RunnerInvariantError):
        _assert_no_external_authorization([{"object_id": "x", "status": "sent"}])
    # a well-formed, non-authorizing object passes
    _assert_no_external_authorization([{"object_id": "x", "status": "draft_to_review",
                                        "external_action_authorized": False}])


def test_output_validates_against_vendored_schema(conn, contract, ingested):
    import jsonschema
    schema = pantheon_contracts.load_schema("mvp_governed_loop_objects")
    out = run(conn, contract, "le devis de reprise correspond-il au périmètre du CCTP pour le lot 06 ?")
    for doc in out.documents:
        jsonschema.validate(doc, schema)


# Gates 4 & 5 (adoption review): the terminal decision-gate stand-in. All
# DB-free — the gate records a decision on a candidate stream, no pgvector.

from mvp_vertical import terminal_gate_standin as gate
from mvp_vertical.terminal_gate_standin import GateRefusal, record_decision


def _sample_candidates(status: str = "draft_to_review") -> list:
    """A candidate stream shaped like the runner's output, for gate tests."""
    request_ref = "mvp.test.tc"
    request_scope_digest = "sha256:" + "4" * 64
    return [
        {
            "object_type": "result_candidate",
            "object_id": "mvp.test.tc.rc-001",
            "result_candidate_id": "mvp.test.tc.rc-001",
            "applies_to": "mvp.test.tc",
            "status": status,
            "request_ref": request_ref,
            "request_scope_digest": request_scope_digest,
            "body": "Bonjour, …",
            "external_action_authorized": False,
        },
        {
            "object_type": "evidence_pack_candidate",
            "object_id": "mvp.test.tc.ep-001",
            "evidence_pack_id": "mvp.test.tc.ep-001",
            "applies_to": "mvp.test.tc",
            "supports": "mvp.test.tc.rc-001",
            "status": "candidate",
            "request_ref": request_ref,
            "request_scope_digest": request_scope_digest,
            "evidence_items": [
                {"claim": "…", "source_ref": "s.md", "support_status": "sourced_not_verified"},
            ],
            "possible_decisions": ["approve", "refuse", "request_revision", "request_more_evidence"],
        },
    ]


def test_gate_records_conforming_decision():
    rec = record_decision(_sample_candidates(), decision="approve",
                          decided_by="Camille Architecte", rationale="périmètre clarifié")
    assert rec["object_type"] == "decision_record"
    assert rec["decision"] == "approve"
    assert rec["decided_by"] == "Camille Architecte"
    assert rec["decision_surface"] == "terminal_gate_standin"
    assert rec["applies_to"] == "mvp.test.tc.rc-001"
    assert rec["related_evidence_pack"] == "mvp.test.tc.ep-001"
    # conforms to the vendored schema (validated inside record_decision)
    import jsonschema
    schema = pantheon_contracts.load_schema("mvp_governed_loop_objects")
    jsonschema.validate(rec, schema)


def test_gate_approval_authorizes_nothing_external():
    rec = record_decision(_sample_candidates(), decision="approve", decided_by="Un Humain")
    assert rec["external_action_authorized"] is False
    assert rec["consequences"]["executed_by_gate"] is False
    assert "never granted by approval" in rec["consequences"]["external_send"]


@pytest.mark.parametrize("signer", ["", "   ", "system", "runner", "Hermes", "MVP-Vertical", "assistant"])
def test_gate_refuses_system_or_empty_signer(signer):
    # Gate 5: the system may never sign; a human must.
    with pytest.raises(GateRefusal):
        record_decision(_sample_candidates(), decision="approve", decided_by=signer)


def test_gate_refuses_unknown_decision():
    with pytest.raises(GateRefusal):
        record_decision(_sample_candidates(), decision="send", decided_by="Un Humain")


def test_gate_refuses_non_reviewable_candidate():
    docs = _sample_candidates(status="refused_capability_gap")
    with pytest.raises(GateRefusal):
        record_decision(docs, decision="approve", decided_by="Un Humain")
