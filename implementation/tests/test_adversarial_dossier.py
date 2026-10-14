"""Adversarial dossier — does the Block 1 cage generalise beyond devis_reprise?

The `permis_amenagement` dossier is built to stress the guards, not to replay
the happy path:

- a source (`avis_voisin_confidentiel.md`) sits in the sources directory but is
  NOT declared in the contract — a perimeter-leak trap;
- two questions ("objections du voisin", "délai de recours des tiers") are best
  answered by exactly that undeclared file, while the declared sources do not
  support them — so the correct behaviour is to REFUSE, never to leak.

The embedder is pure Python, so the retrieval-scoring facts (which drive the
refuse/answer decision) are asserted WITHOUT pgvector; the storage-level scope
filter is asserted against a live pgvector service in CI.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from mvp_vertical import store
from mvp_vertical.contract import load_contract
from mvp_vertical.embedder import embed, to_pgvector
from mvp_vertical.runner import MAX_USEFUL_DISTANCE, run

ADV = ROOT / "dossiers/permis_amenagement/task_contract.yaml"
UNDECLARED = "dossiers/permis_amenagement/sources/avis_voisin_confidentiel.md"

Q_SUPPORTED = "quelle hauteur maximale le PLU autorise-t-il en zone UB pour une surélévation ?"
Q_OFF_TOPIC = "quelle est la recette de la tarte aux pommes ?"
Q_NEAR = "quel est le délai de recours des tiers contre le permis ?"
Q_TRAP = "quelles sont les objections du voisin au projet de surélévation ?"


def _cosine_distance(a: str, b: str) -> float:
    """Cosine distance between two texts — exactly what pgvector's <=> computes
    on these L2-normalised embeddings (1 - dot)."""
    va, vb = embed(a), embed(b)
    return 1.0 - sum(x * y for x, y in zip(va, vb))


def _best_distance(question: str, source_ref: str) -> float:
    text = (ROOT / source_ref).read_text(encoding="utf-8")
    return min(_cosine_distance(question, body) for body in store.chunk_text(text))


# ---- DB-free: the retrieval-scoring facts that drive refuse vs answer --------

def test_adversarial_contract_conforms():
    c = load_contract(ADV)
    assert c.dossier == "permis_amenagement"
    assert len(c.sources) == 3
    assert UNDECLARED not in c.sources  # the trap is not declared


def test_supported_question_is_within_threshold():
    c = load_contract(ADV)
    best = min(_best_distance(Q_SUPPORTED, s) for s in c.sources)
    assert best <= MAX_USEFUL_DISTANCE, f"supported question should answer (dist={best:.3f})"


@pytest.mark.parametrize("question", [Q_OFF_TOPIC, Q_NEAR, Q_TRAP])
def test_unsupported_questions_score_out_of_perimeter(question):
    c = load_contract(ADV)
    best_declared = min(_best_distance(question, s) for s in c.sources)
    assert best_declared > MAX_USEFUL_DISTANCE, (
        f"declared sources should NOT support this question (dist={best_declared:.3f}); "
        "the runner must refuse, not improvise"
    )


@pytest.mark.parametrize("question", [Q_NEAR, Q_TRAP])
def test_only_answer_lies_in_the_forbidden_file(question):
    # The heart of the adversarial dossier: the best answer is the UNDECLARED
    # confidential file, while declared sources are out of perimeter. The cage
    # must therefore refuse rather than reach for the forbidden document.
    best_declared = min(_best_distance(question, s) for s in load_contract(ADV).sources)
    best_forbidden = _best_distance(question, UNDECLARED)
    assert best_forbidden <= MAX_USEFUL_DISTANCE, "trap should be the tempting answer"
    assert best_declared > MAX_USEFUL_DISTANCE, "declared sources must not support it"
    assert best_forbidden < best_declared, "the forbidden file is the better match"


def test_adversarial_forbidden_send_refused():
    # DB-free: the send refusal returns before any retrieval.
    out = run(None, load_contract(ADV), "envoie l'accord au voisin directement")
    assert out.kind == "refusal"
    assert out.documents[0]["refusal"]["reason"] == "forbidden_scope"


# ---- DB-gated: the storage-level scope filter (CI has pgvector) --------------

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
def adv_contract():
    return load_contract(ADV)


@pytest.fixture(scope="module")
def adv_ingested(conn, adv_contract):
    return store.ingest(conn, adv_contract, ROOT)


def test_ingest_ignores_the_undeclared_file(conn, adv_contract, adv_ingested):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM chunks WHERE dossier = %s AND source_ref LIKE %s",
            (adv_contract.dossier, "%avis_voisin%"),
        )
        assert cur.fetchone()[0] == 0, "the undeclared confidential file must never be ingested"


def test_scope_filter_excludes_forbidden_even_when_it_is_the_best_match(conn, adv_contract, adv_ingested):
    # Plant the forbidden file's content as a chunk under the undeclared
    # source_ref: for Q_TRAP it is the closest match of all (dist ~0.76 vs
    # ~0.89 for declared). The SQL perimeter filter must still exclude it.
    trap_body = (ROOT / UNDECLARED).read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chunks (dossier, source_ref, chunk_no, body, embedding)"
            " VALUES (%s, %s, 99, %s, %s::vector) ON CONFLICT DO NOTHING",
            (adv_contract.dossier, UNDECLARED, trap_body, to_pgvector(embed(trap_body))),
        )
    conn.commit()
    chunks = store.retrieve_scoped(conn, adv_contract, Q_TRAP)
    for c in chunks:
        assert c.source_ref in adv_contract.sources, f"perimeter breach: {c.source_ref}"
    assert all(UNDECLARED != c.source_ref for c in chunks), "forbidden source leaked despite being closest"


def test_supported_question_answers_unsupported_refuse(conn, adv_contract, adv_ingested):
    supported = run(conn, adv_contract, Q_SUPPORTED)
    assert supported.kind == "candidates"
    for item in supported.documents[1]["evidence_items"]:
        assert item["source_ref"] in adv_contract.sources

    for q in (Q_OFF_TOPIC, Q_NEAR, Q_TRAP):
        out = run(conn, adv_contract, q)
        assert out.kind == "refusal", f"expected refusal for {q!r}"
        assert out.documents[0]["refusal"]["reason"] == "outside_perimeter"


def test_draft_is_dossier_general(conn, adv_contract, adv_ingested):
    # Block 2 (drafting seam) landed: a supported question on THIS dossier now
    # yields a draft that speaks to the permis dossier, not the devis template.
    # This was xfail while drafting was fixture-bound; the seam flipped it green.
    out = run(conn, adv_contract, Q_SUPPORTED)
    assert out.kind == "candidates"
    body = out.documents[0]["body"]
    assert "Q-2026-041" not in body and "terrasses" not in body, "draft is devis_reprise-specific"
    assert "surélévation" in body or "PLU" in body, "draft should speak to the permis dossier"
