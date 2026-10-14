"""Project-aware stand-in review composes currentness before drafting."""

from __future__ import annotations

from pathlib import Path

from mvp_vertical import human_access, retrieval_scope, runner
from mvp_vertical.contract import TaskContract
from mvp_vertical.retrieval import HybridRetrievedChunk
from mvp_vertical.store import RetrievedChunk


SOURCE = "sources/cctp.md"


def _contract(*, forbidden: tuple[str, ...] = ()) -> TaskContract:
    return TaskContract(
        raw={
            "object_id": "task-project-review",
            "contract_id": "task-project-review",
            "scope": {
                "parent_project_id": "project-a",
                "declared_sources": [SOURCE],
            },
            "intent": {"summary": "Préparer une revue bornée du devis."},
        },
        path=Path("task.yaml"),
        dossier="dossier-a",
        sources=(SOURCE,),
        forbidden=forbidden,
    )


def _principal() -> human_access.PrincipalContext:
    return human_access.PrincipalContext(
        principal_ref="human:test",
        issuer="https://issuer.example",
        subject="subject-1",
    )


def _chunk() -> RetrievedChunk:
    return RetrievedChunk(
        source_ref=SOURCE,
        chunk_no=3,
        body="Le CCTP prévoit une protection zinc sur le relevé.",
        distance=0.05,
        source_digest="b" * 64,
        content_type="paragraph",
        page_start=12,
        page_end=12,
        structural_locator="section:CCTP/releves",
        section_path=("CCTP", "Relevés"),
    )


def _ranked_hit(
    source_ref: str,
    source_digest: str,
    rank: int,
    *,
    distance: float = 0.2,
    lexical: bool = True,
) -> HybridRetrievedChunk:
    chunk = RetrievedChunk(
        source_ref=source_ref,
        chunk_no=rank,
        body=f"Qualification candidate {rank} from {source_ref}",
        distance=distance,
        source_digest=source_digest,
    )
    return HybridRetrievedChunk(
        chunk=chunk,
        hybrid_score=1.0 / (60 + rank),
        semantic_rank=rank,
        lexical_rank=rank if lexical else None,
    )


def _resolution() -> retrieval_scope.RetrievalScopeResolution:
    return retrieval_scope.RetrievalScopeResolution(
        project_id="project-a",
        principal_ref="human:test",
        sources=(
            retrieval_scope.ResolvedRetrievalSource(
                document_id="project-document-cctp",
                purpose="current_contractual",
                document_version_id="pdv-cctp-b",
                dossier="dossier-a",
                source_ref=SOURCE,
                source_digest="b" * 64,
                source_version=2,
                basis_refs=("decision:dce-b",),
            ),
        ),
    )


class CitedDrafter:
    def draft(self, *, intent, question, chunks):
        chunk = chunks[0]
        return (
            f"Selon [{chunk.source_ref}#chunk-{chunk.chunk_no}], "
            "le CCTP prévoit une protection zinc sur le relevé."
        )


class NeverDrafter:
    def draft(self, *, intent, question, chunks):  # pragma: no cover - must not run
        raise AssertionError("drafting must not run when scope resolution fails")


def test_project_runner_uses_existing_currentness_scope_and_projects_exact_revision(monkeypatch) -> None:
    captured = {}
    hit = HybridRetrievedChunk(
        chunk=_chunk(),
        hybrid_score=0.03,
        semantic_rank=1,
        lexical_rank=1,
    )

    def retrieve(conn, principal, **kwargs):
        captured.update(kwargs)
        assert principal.principal_ref == "human:test"
        return _resolution(), [hit]

    monkeypatch.setattr(
        runner.retrieval_scope,
        "retrieve_accessible_applicable_hybrid",
        retrieve,
    )

    output = runner.run_accessible_applicable(
        object(),
        _principal(),
        _contract(),
        "Que prévoit le CCTP pour le relevé ?",
        project_id="project-a",
        requested_documents=(("project-document-cctp", "current_contractual"),),
        drafter=CitedDrafter(),
    )

    assert output.kind == "candidates"
    assert captured["project_id"] == "project-a"
    assert captured["requested_documents"] == (("project-document-cctp", "current_contractual"),)
    assert captured["query"] == "Que prévoit le CCTP pour le relevé ?"
    assert captured["top_k"] == runner.HYBRID_CANDIDATE_K

    result_candidate, evidence_pack = output.documents
    assert result_candidate["status"] == "draft_to_review"
    assert result_candidate["external_action_authorized"] is False

    scope = evidence_pack["source_scope_resolution"]
    assert scope["resolution_status"] == "resolved_for_retrieval"
    assert scope["authority"] == {
        "decides_professional_approval": False,
        "admits_evidence": False,
        "widens_task_contract": False,
    }
    source = scope["sources"][0]
    assert source["document_id"] == "project-document-cctp"
    assert source["document_version_id"] == "pdv-cctp-b"
    assert source["source_version"] == 2
    assert source["source_digest"] == "b" * 64
    assert source["basis_refs"] == ["decision:dce-b"]

    item = evidence_pack["evidence_items"][0]
    assert item["source_ref"] == SOURCE
    assert item["retrieval_audit"]["source_digest"] == "b" * 64
    assert item["retrieval_provenance"]["page_start"] == 12
    assert item["support_status"] == "sourced_not_verified"


def test_context_selection_keeps_one_useful_hit_per_resolved_source() -> None:
    dpgf = ("sources/dpgf.md", "d" * 64)
    cctp = ("sources/cctp.md", "c" * 64)
    quote = ("sources/quote.md", "q" * 64)
    hits = [
        _ranked_hit(*dpgf, 1),
        _ranked_hit(*cctp, 2),
        _ranked_hit(*dpgf, 3),
        _ranked_hit(*dpgf, 4),
        _ranked_hit(*quote, 5, distance=0.9),
    ]

    selected = runner._select_useful_context_hits(
        hits,
        required_sources=(dpgf, cctp, quote),
        limit=4,
    )

    assert [hit.semantic_rank for hit in selected] == [1, 2, 3, 5]
    assert {(hit.chunk.source_ref, hit.chunk.source_digest) for hit in selected} == {
        dpgf,
        cctp,
        quote,
    }


def test_context_selection_does_not_force_non_useful_resolved_source() -> None:
    dpgf = ("sources/dpgf.md", "d" * 64)
    cctp = ("sources/cctp.md", "c" * 64)
    quote = ("sources/quote.md", "q" * 64)
    hits = [
        _ranked_hit(*dpgf, 1),
        _ranked_hit(*cctp, 2),
        _ranked_hit(*dpgf, 3),
        _ranked_hit(*dpgf, 4),
        _ranked_hit(*quote, 5, distance=0.9, lexical=False),
    ]

    selected = runner._select_useful_context_hits(
        hits,
        required_sources=(dpgf, cctp, quote),
        limit=4,
    )

    assert [hit.semantic_rank for hit in selected] == [1, 2, 3, 4]
    assert quote not in {
        (hit.chunk.source_ref, hit.chunk.source_digest) for hit in selected
    }


def test_project_runner_refuses_unresolved_currentness_before_drafting(monkeypatch) -> None:
    def unresolved(*args, **kwargs):
        raise retrieval_scope.RetrievalScopeUnresolved("not resolved")

    monkeypatch.setattr(
        runner.retrieval_scope,
        "retrieve_accessible_applicable_hybrid",
        unresolved,
    )

    output = runner.run_accessible_applicable(
        object(),
        _principal(),
        _contract(),
        "Quel est le périmètre contractuel ?",
        project_id="project-a",
        requested_documents=(("project-document-cctp", "current_contractual"),),
        drafter=NeverDrafter(),
    )

    assert output.kind == "refusal"
    refusal = output.documents[0]["refusal"]
    assert refusal["reason"] == "applicability_unresolved"
    assert "no applicable document revision" in refusal["detail"]
    assert output.documents[0]["external_action_authorized"] is False


def test_external_send_refusal_happens_before_project_scope_lookup(monkeypatch) -> None:
    def forbidden_lookup(*args, **kwargs):  # pragma: no cover - must not run
        raise AssertionError("scope lookup must not run for a forbidden send request")

    monkeypatch.setattr(
        runner.retrieval_scope,
        "retrieve_accessible_applicable_hybrid",
        forbidden_lookup,
    )

    output = runner.run_accessible_applicable(
        object(),
        _principal(),
        _contract(forbidden=("external_send",)),
        "Envoie la validation à l'entreprise.",
        project_id="project-a",
        requested_documents=(("project-document-cctp", "current_contractual"),),
        drafter=NeverDrafter(),
    )

    assert output.kind == "refusal"
    refusal = output.documents[0]["refusal"]
    assert refusal["reason"] == "forbidden_scope"
    assert "external_send" in refusal["detail"]
