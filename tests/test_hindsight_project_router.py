from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "implementation" / "hermes" / "hindsight_project_router" / "hindsight_project_recall.py"


def _module():
    spec = importlib.util.spec_from_file_location("hindsight_project_recall_test", MODULE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_recall_forces_source_project_and_all_strict() -> None:
    module = _module()
    client = module.ProjectRecallClient("http://127.0.0.1:8888", "PROJECTS")
    response = {
        "results": [{
            "id": "fact-1",
            "text": "Décision projet Alpha",
            "document_id": "doc-1:source",
            "chunk_id": "chunk-1",
            "tags": ["source:project-sync", f"scope:project:{module.project_scope_token('Projet Alpha')}"],
        }],
        "entities": {},
        "chunks": {"chunk-1": {"document_id": "doc-1:source"}},
    }
    with patch.object(client, "_post", return_value=response) as post:
        result = client.recall_project("Projet Alpha", "Quelle décision ?")

    body = post.call_args.args[0]
    assert body["tags"] == ["source:project-sync", f"scope:project:{module.project_scope_token('Projet Alpha')}"]
    assert body["tags_match"] == "all_strict"
    assert body["types"] == ["world", "experience"]
    assert body["prefer_observations"] is False
    assert body["include"] == {"entities": None, "chunks": {"max_tokens": module.CHUNK_TOKENS}, "source_facts": None}
    assert result["project_scope"] == f"scope:project:{module.project_scope_token('Projet Alpha')}"
    assert result["mode"] == "source-grounded-evidence"
    assert result["results"][0]["document_id"] == "doc-1:source"


def test_french_accents_normalize_to_stable_ascii_scope() -> None:
    module = _module()
    assert module.tag_value("Médiathèque André") == "mediatheque-andre"


def test_folder_can_only_narrow_an_existing_project_scope() -> None:
    module = _module()
    client = module.ProjectRecallClient("http://127.0.0.1:8888", "PROJECTS")
    response = {
        "results": [{
            "id": "fact-1",
            "text": "Plan",
            "document_id": "doc-1:source",
            "chunk_id": "chunk-1",
            "tags": [
                "source:project-sync",
                f"scope:project:{module.project_scope_token('Projet Alpha')}",
                "folder:projet-alpha-dce-plans",
            ],
        }]
    }
    with patch.object(client, "_post", return_value=response) as post:
        client.recall_project(
            "Projet Alpha", "Quel plan ?", folder="Projet Alpha/DCE/Plans"
        )

    assert post.call_args.args[0]["tags"] == [
        "source:project-sync",
        f"scope:project:{module.project_scope_token('Projet Alpha')}",
        "folder:projet-alpha-dce-plans",
    ]


def test_recall_omits_unprovenanced_results_and_caps_evidence() -> None:
    module = _module()
    client = module.ProjectRecallClient("http://127.0.0.1:8888", "PROJECTS")
    tags = ["source:project-sync", f"scope:project:{module.project_scope_token('Projet Alpha')}"]
    results = [{"id": "observation", "text": "lead", "tags": tags}]
    results.extend(
        {
            "id": f"fact-{index}",
            "text": f"Fact {index}",
            "document_id": f"doc-{index}:source",
            "chunk_id": f"chunk-{index}",
            "tags": tags,
        }
        for index in range(10)
    )
    response = {
        "results": results,
        "chunks": {
            f"chunk-{index}": {"document_id": f"doc-{index}:source"}
            for index in range(10)
        },
    }

    with patch.object(client, "_post", return_value=response):
        result = client.recall_project("Projet Alpha", "question")

    assert len(result["results"]) == 8
    assert all(row["document_id"] for row in result["results"])
    assert "chunks" not in result


def test_pending_or_empty_project_is_rejected_before_hindsight_call() -> None:
    module = _module()
    client = module.ProjectRecallClient("http://127.0.0.1:8888", "PROJECTS")
    for project in ("", "pending identification"):
        with pytest.raises(module.ProjectRecallError):
            client.recall_project(project, "question")


def test_out_of_scope_or_untagged_result_fails_closed() -> None:
    module = _module()
    client = module.ProjectRecallClient("http://127.0.0.1:8888", "PROJECTS")
    for tags in ([], ["source:project-sync", f"scope:project:{module.project_scope_token('Projet Beta')}"]):
        with patch.object(
            client,
            "_post",
            return_value={"results": [{"id": "leak", "text": "wrong", "tags": tags}]},
        ):
            with pytest.raises(module.ProjectRecallError):
                client.recall_project("Projet Alpha", "question")



def test_project_scope_token_disambiguates_slug_collisions() -> None:
    module = _module()
    assert module.tag_value("Projet A") == module.tag_value("Projet-A")
    assert module.project_scope_token("Projet A") != module.project_scope_token("Projet-A")


def test_knowledge_recall_forces_source_and_optional_folder_only() -> None:
    module = _module()
    client = module.ProjectRecallClient(
        "http://127.0.0.1:8888", "KNOWLEDGE", source_kind="knowledge"
    )
    response = {
        "results": [{
            "id": "fact-1",
            "text": "Réception avec réserves",
            "document_id": "doc-1:source",
            "chunk_id": "chunk-1",
            "tags": ["source:knowledge", "folder:insurer", "scope:project:insurer-0123456789ab"],
        }],
        "chunks": {"chunk-1": {"document_id": "doc-1:source"}},
    }
    with patch.object(client, "_post", return_value=response) as post:
        whole = client.recall_knowledge("Que conseille l'assureur à la réception ?")
        narrowed = client.recall_knowledge("Réserves ?", folder="Insurer")

    first, second = (call.args[0] for call in post.call_args_list)
    assert first["tags"] == ["source:knowledge"]
    assert second["tags"] == ["source:knowledge", "folder:insurer"]
    assert first["tags_match"] == second["tags_match"] == "all_strict"
    assert whole["source_scope"] == "source:knowledge"
    assert whole["folder_scope"] is None
    assert narrowed["folder_scope"] == "folder:insurer"
    assert "project_scope" not in whole
    assert whole["results"][0]["document_id"] == "doc-1:source"


def test_knowledge_recall_fails_closed_outside_source_or_folder() -> None:
    module = _module()
    client = module.ProjectRecallClient(
        "http://127.0.0.1:8888", "KNOWLEDGE", source_kind="knowledge"
    )
    for tags, folder in (
        ([], ""),
        (["source:project-sync"], ""),
        (["source:knowledge", "folder:standards"], "insurer"),
    ):
        with patch.object(
            client, "_post",
            return_value={"results": [{"id": "leak", "text": "wrong", "tags": tags}]},
        ):
            with pytest.raises(module.ProjectRecallError):
                client.recall_knowledge("question", folder=folder)


def test_knowledge_recall_rejects_empty_query_before_hindsight_call() -> None:
    module = _module()
    client = module.ProjectRecallClient(
        "http://127.0.0.1:8888", "KNOWLEDGE", source_kind="knowledge"
    )
    with patch.object(client, "_post") as post:
        with pytest.raises(module.ProjectRecallError):
            client.recall_knowledge("   ")
    post.assert_not_called()


def test_fact_budget_is_bounded_and_chunks_stay_internal() -> None:
    module = _module()
    for requested, expected in ((6, 256), (1200, 1200), (100000, 4096)):
        body = module.ProjectRecallClient._recall_body("q", ["source:x"], requested)
        assert body["max_tokens"] == expected
        assert body["include"]["chunks"] == {"max_tokens": module.CHUNK_TOKENS}


def test_evidence_keeps_text_and_provenance_but_drops_index_bookkeeping() -> None:
    module = _module()
    client = module.ProjectRecallClient(
        "http://127.0.0.1:8888", "KNOWLEDGE", source_kind="knowledge"
    )
    response = {
        "results": [{
            "id": "fact-1",
            "text": "Épaisseur minimale 15 mm",
            "type": "world",
            "document_id": "doc-1:source",
            "chunk_id": "chunk-1",
            "tags": ["source:knowledge", "folder:standards"],
            "context": "professional source document; title=Standard.pdf; folder ancestry=Standards",
            "scores": {"semantic": 0.61, "bm25": 3.2, "rerank": 0.8},
            "entities": None,
            "occurred_start": None,
            "source_fact_ids": [],
            "metadata": {
                "title": "Standard.pdf",
                "revision": "B",
                "source_path": "Standards/Standard.pdf",
                "source_sha256": "0" * 64,
                "workspace": "Library",
                "parent_path": "Standards",
                "source_kind": "knowledge",
                "folder_ancestry": "Standards",
                "pantheon_document_id": "doc-1",
            },
        }],
        "chunks": {
            "chunk-1": {
                "id": "chunk-1",
                "text": "3.2.2.3 Epaisseur\nL'épaisseur minimale des lames est de 15 mm pour des\nsupports courants.",
                "chunk_index": 3, "truncated": False, "attachments": [],
            },
            "chunk-other": {"id": "chunk-other", "text": "unrelated"},
        },
    }
    with patch.object(client, "_post", return_value=response):
        result = client.recall_knowledge("épaisseur ?", folder="standards")

    assert result["results"] == [{
        "text": "Épaisseur minimale 15 mm",
        "type": "world",
        "document_id": "doc-1:source",
        "chunk_id": "chunk-1",
        "metadata": {
            "title": "Standard.pdf",
            "revision": "B",
            "source_path": "Standards/Standard.pdf",
            "source_sha256": "0" * 64,
        },
        "quote": "3.2.2.3 Epaisseur L'épaisseur minimale des lames est de 15 mm pour des supports courants.",
        "section": "3.2.2.3 Epaisseur",
        "citation": "Standard.pdf, 3.2.2.3 Epaisseur",
    }]
    assert "chunks" not in result


def test_quote_is_verbatim_and_located_under_its_heading() -> None:
    module = _module()
    chunk = (
        "8.6 Lame d'air ventilée\n"
        "La lame d'air ventilée est spécifique au bardage et ne peut servir à la\n"
        "ventilation d'autres ouvrages.\n"
        "8.6.1  Section de ventilation\n"
        "Les entrées basses sont de section suffisante : 50 cm2 /ml pour une hauteur\n"
        "au plus égale à 3 m ; 65 cm2 /ml pour une hauteur de 3 m à 6 m.\n"
    )
    quote, section = module.locate_quote(
        "Les entrées basses ont une section de 50 cm²/ml jusqu'à 3 m de hauteur.", chunk
    )
    assert "Les entrées basses sont de section suffisante : 50 cm2 /ml" in quote
    assert " ".join(quote.split()) in " ".join(chunk.split())
    assert section == "8.6.1 Section de ventilation"


def test_no_quote_when_a_figure_of_the_summary_is_absent() -> None:
    module = _module()
    # The formula is an image in the source: the extracted text lacks "1000".
    chunk = "8.6.1 Section de ventilation\nLa section est calculée selon la formule suivante :\noù K = 50 pour les autres cas"
    assert module.locate_quote(
        "La section est calculée selon la formule S = K × H / 1000, où K = 50.", chunk
    ) == (None, None)


def test_no_quote_when_the_chunk_does_not_carry_the_summary() -> None:
    module = _module()
    assert module.locate_quote(
        "Les acrotères reçoivent une couvertine.", "Les menuiseries sont alignées à 4 mm près."
    ) == (None, None)


def test_quote_elides_print_footers_contacts_and_vertical_margin_text() -> None:
    module = _module()
    chunk = (
        "Les sorties de la lame d'air sont protégées en tête par couvertine ou appui de\n"
        "http://intranet:8080/print.jsp?code=X Page 19 of 65 contact@example.org\n"
        "baie avec un recouvrement suffisant.\n"
        "e r u t i o t - s u o S 1 0 5\n"
    )
    quote, _ = module.locate_quote(
        "Les sorties de la lame d'air sont protégées en tête par couvertine ou appui de baie.", chunk
    )
    assert "http" not in quote and "@" not in quote and "Page 19" not in quote
    assert "[…]" in quote
    assert "e r u t" not in quote
