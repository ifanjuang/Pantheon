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


def test_a_passage_shared_by_several_facts_is_quoted_once() -> None:
    module = _module()
    client = module.ProjectRecallClient(
        "http://127.0.0.1:8888", "KNOWLEDGE", source_kind="knowledge"
    )
    chunk = "3.2 Fixations\nLes lames sont fixées par deux pointes inox de 2,5 mm par appui."
    tags = ["source:knowledge"]
    response = {
        "results": [
            {"id": f"fact-{i}", "text": text, "document_id": "doc-1:source", "chunk_id": "chunk-1",
             "tags": tags, "metadata": {"title": "Guide.pdf"}}
            for i, text in enumerate(("Les lames sont fixées par deux pointes par appui.",
                                      "Les pointes sont en inox de 2,5 mm."))
        ],
        "chunks": {"chunk-1": {"text": chunk}},
    }
    with patch.object(client, "_post", return_value=response):
        first, second = client.recall_knowledge("fixation ?")["results"]

    assert "pointes inox de 2,5 mm" in first["quote"]
    assert "quote" not in second
    assert second["citation"] == first["citation"] == "Guide.pdf, 3.2 Fixations"


def _alpha_tags(module, *extra: str) -> list[str]:
    return ["source:project-sync", f"scope:project:{module.project_scope_token('Projet Alpha')}", *extra]


def _fact(fact_id: str, text: str, document: str, tags: list[str], chunk: str = "", title: str = "") -> dict:
    return {
        "id": fact_id, "text": text, "type": "world",
        "document_id": f"{document}:source", "chunk_id": chunk or f"{document}-chunk-1",
        "tags": tags, "metadata": {"title": title or f"{document}.pdf"},
    }


def _recall(module, results, *, older_versions: bool = False, chunks=None):
    client = module.ProjectRecallClient("http://127.0.0.1:8888", "PROJECTS")
    with patch.object(client, "_post", return_value={"results": results, "chunks": chunks or {}}) as post:
        payload = client.recall_project("Projet Alpha", "question", older_versions=older_versions)
    return payload, post.call_args.args[0]


def test_identical_passages_across_documents_are_grouped_without_loss() -> None:
    module = _module()
    tags = _alpha_tags(module)
    results = [
        _fact("f1", "Agence Exemple, 1 rue du Modèle.", "doc-1", tags),
        _fact("f2", "Le lot 02 est attribué.", "doc-1", tags),
        _fact("f3", "Agence  Exemple,\n1 rue du Modèle.", "doc-2", tags),
        _fact("f4", "Agence Exemple, 1 rue du Modèle.", "doc-3", tags),
    ]
    payload, _ = _recall(module, results)

    first, second = payload["results"]
    assert first["document_id"] == "doc-1:source"
    assert first["present_in_documents"] == 3
    assert [(o["document_id"], o["chunk_id"], o["title"]) for o in first["also_in"]] == [
        ("doc-2:source", "doc-2-chunk-1", "doc-2.pdf"),
        ("doc-3:source", "doc-3-chunk-1", "doc-3.pdf"),
    ]
    assert second["text"] == "Le lot 02 est attribué."
    assert "present_in_documents" not in second and "also_in" not in second


def test_a_passage_repeated_inside_one_document_keeps_each_chunk() -> None:
    module = _module()
    tags = _alpha_tags(module)
    results = [
        _fact("f1", "En-tête de page répété.", "doc-1", tags, chunk="c1"),
        _fact("f2", "En-tête de page répété.", "doc-1", tags, chunk="c2"),
    ]
    payload, _ = _recall(module, results)

    (row,) = payload["results"]
    assert row["present_in_documents"] == 1
    assert [o["chunk_id"] for o in row["also_in"]] == ["c2"]


def test_revision_labels_are_exposed_separately_and_never_filtered() -> None:
    module = _module()
    labelled = _alpha_tags(
        module, "indice:B", "indice_fiche:c", "revision_hint:d", "date_document:2025-03",
        "version:remplacee-sur-place", "revision:supplements:doc-0", "portee:propre_au_document",
    )
    results = [
        _fact("f1", "Plan de niveau, indice B.", "doc-1", labelled),
        _fact("f2", "Sans étiquette.", "doc-2", _alpha_tags(module)),
    ]
    payload, body = _recall(module, results)

    assert body["tags"] == _alpha_tags(module)
    first, second = payload["results"]
    # Three indices from three origins (content, cartouche, filename) stay apart.
    assert first["labels"] == {
        "indice": ["B"], "indice_fiche": ["c"], "revision_hint": ["d"],
        "date_document": ["2025-03"], "version": ["remplacee-sur-place"],
        "revision": ["supplements:doc-0"], "portee": ["propre_au_document"],
    }
    assert "labels" not in second


def test_general_conditions_come_after_project_specific_facts_with_a_notice() -> None:
    module = _module()
    results = [
        _fact("f1", "Paiement à 30 jours fin de mois.", "devis-1", _alpha_tags(module, "portee:conditions_generales")),
        _fact("f2", "Montant du devis : 12 400 € HT.", "devis-1", _alpha_tags(module, "portee:propre_au_document")),
    ]
    payload, _ = _recall(module, results)

    specific, general = payload["results"]
    assert specific["text"].startswith("Montant")
    assert "notice" not in specific
    assert "conditions générales d'entreprise, pas une règle" in general["notice"]


def test_project_mode_presents_the_most_recent_family_member_first() -> None:
    module = _module()
    family = "family:family-0123456789abcdef01234567"
    results = [
        _fact("f1", "Hauteur sous plafond 2,50 m.", "plan-a", _alpha_tags(module, family, "date_document:2024-11", "indice:A")),
        _fact("f2", "Hauteur sous plafond 2,60 m.", "plan-c", _alpha_tags(module, family, "date_document:2025-03", "indice:C")),
        _fact("f3", "Toiture terrasse végétalisée.", "notice-1", _alpha_tags(module)),
        _fact("f4", "Hauteur sous plafond 2,55 m.", "plan-b", _alpha_tags(module, family, "date_document:2025-03", "indice:B")),
    ]
    payload, _ = _recall(module, results)

    order = [row["document_id"] for row in payload["results"]]
    assert order == ["plan-c:source", "notice-1:source", "plan-b:source", "plan-a:source"]
    newest, _, same_date, older = payload["results"]
    # plan-b shares the latest date: it is not earlier, only less relevant.
    assert newest["earlier_in_family"] == 1
    assert "notice" not in same_date and "earlier_in_family" not in same_date
    assert "présentée après" in older["notice"] and "remplacement" in older["notice"]
    assert "earlier_in_family" not in older


def test_family_recency_compares_documents_not_passages() -> None:
    module = _module()
    family = "family:family-0123456789abcdef01234567"
    results = [
        _fact("f1", "Hauteur sous plafond 2,60 m.", "plan-c", _alpha_tags(module, family, "date_document:2025-03")),
        _fact("f2", "Hauteur sous plafond 2,50 m.", "plan-a", _alpha_tags(module, family, "date_document:2024-11")),
        _fact("f3", "Garde-corps vitré au R+1.", "plan-c", _alpha_tags(module, family, "date_document:2025-03")),
    ]
    payload, _ = _recall(module, results)

    order = [row["document_id"] for row in payload["results"]]
    assert order == ["plan-c:source", "plan-c:source", "plan-a:source"]
    first, second, older = payload["results"]
    # A second passage of the most recent document is neither demoted nor called earlier.
    assert first["earlier_in_family"] == 1
    assert "notice" not in second and "earlier_in_family" not in second
    assert "présentée après" in older["notice"]


def test_older_versions_on_request_keep_their_relevance_rank() -> None:
    module = _module()
    family = "family:family-0123456789abcdef01234567"
    results = [
        _fact("f1", "Hauteur 2,50 m.", "plan-a", _alpha_tags(module, family, "date_document:2024-11")),
        _fact("f2", "Hauteur 2,60 m.", "plan-c", _alpha_tags(module, family, "date_document:2025-03")),
    ]
    payload, _ = _recall(module, results, older_versions=True)

    assert [row["document_id"] for row in payload["results"]] == ["plan-a:source", "plan-c:source"]
    assert payload["results"][1]["earlier_in_family"] == 1


def test_family_member_without_a_read_date_or_index_is_not_ranked() -> None:
    module = _module()
    family = "family:family-0123456789abcdef01234567"
    results = [
        _fact("f1", "Sans date ni indice.", "plan-x", _alpha_tags(module, family)),
        _fact("f2", "Daté.", "plan-y", _alpha_tags(module, family, "date_document:2025")),
    ]
    payload, _ = _recall(module, results)

    first, second = payload["results"]
    assert first["document_id"] == "plan-x:source" and "notice" not in first
    assert "earlier_in_family" not in second


def test_identical_passage_is_represented_by_its_most_recent_family_member() -> None:
    module = _module()
    family = "family:family-0123456789abcdef01234567"
    results = [
        _fact("f1", "Mentions types du cartouche.", "plan-a", _alpha_tags(module, family, "date_document:2024-11")),
        _fact("f2", "Mentions types du cartouche.", "plan-b", _alpha_tags(module, family, "date_document:2025-03")),
    ]
    payload, _ = _recall(module, results)

    (row,) = payload["results"]
    assert row["document_id"] == "plan-b:source"
    assert [o["document_id"] for o in row["also_in"]] == ["plan-a:source"]


def test_knowledge_mode_demotes_but_never_drops_a_superseded_document() -> None:
    module = _module()
    client = module.ProjectRecallClient("http://127.0.0.1:8888", "KNOWLEDGE", source_kind="knowledge")
    results = [
        _fact("f1", "Ancienne règle de pose.", "guide-2019", ["source:knowledge", "revision:superseded-by:guide-2024"]),
        _fact("f2", "Règle de pose en vigueur.", "guide-2024", ["source:knowledge", "revision:supersedes:guide-2019"]),
    ]
    with patch.object(client, "_post", return_value={"results": results}):
        default = client.recall_knowledge("règle de pose ?")
        requested = client.recall_knowledge("règle de pose ?", older_versions=True)

    current, superseded = default["results"]
    assert current["document_id"] == "guide-2024:source"
    assert superseded["document_id"] == "guide-2019:source"
    assert "consultable sur demande" in superseded["notice"]
    assert [row["document_id"] for row in requested["results"]] == ["guide-2019:source", "guide-2024:source"]


def test_text_layer_passage_is_a_quote_only_row_kept_at_its_relevance_rank() -> None:
    module = _module()
    text_tags = _alpha_tags(module, "representation:text")
    results = [
        {"id": "t1", "text": "Article 4.2 — Les menuiseries\nsont posées en applique.", "type": "world",
         "document_id": "doc-1:text", "chunk_id": "doc-1-text-1", "tags": text_tags,
         "metadata": {"title": "doc-1.pdf"}},
        _fact("f1", "Les menuiseries sont posées en applique.", "doc-1", _alpha_tags(module)),
    ]
    payload, _ = _recall(module, results)

    text, fact = payload["results"]
    assert text["document_id"] == "doc-1:text"
    assert text["representation"] == "text"
    assert text["quote"] == "Article 4.2 — Les menuiseries sont posées en applique."
    assert text["citation"] == "doc-1.pdf"
    assert "text" not in text
    assert fact["document_id"] == "doc-1:source" and "representation" not in fact


def test_text_layer_and_facts_share_the_cap_in_hindsight_relevance_order() -> None:
    # Measured on a bank holding both layers: putting every fact before the raw text
    # discards the gain of combining them (precision@5 77 % -> 56 %), so the order
    # Hindsight's reranker produced across the two layers is kept.
    module = _module()
    results = [
        {"id": f"t{i}", "text": f"Passage {i}", "document_id": f"doc-{i}:text", "chunk_id": f"t{i}",
         "tags": _alpha_tags(module, "representation:text")}
        for i in range(3)
    ] + [_fact(f"f{i}", f"Fait {i}", f"doc-{i}", _alpha_tags(module)) for i in range(10)]
    payload, _ = _recall(module, results)

    ids = [row["document_id"] for row in payload["results"]]
    assert len(ids) == module.MAX_EVIDENCE_RESULTS
    assert ids == [f"doc-{i}:text" for i in range(3)] + [f"doc-{i}:source" for i in range(5)]


def test_text_layer_passage_is_quoted_whole_and_never_dropped_as_a_repeated_quote() -> None:
    module = _module()
    text_tags = _alpha_tags(module, "representation:text")
    passage = "Les réserves sont levées dans un délai de deux semaines. " * 3
    results = [
        {"id": f"t{i}", "text": passage + str(i), "document_id": f"doc-{i}:text", "chunk_id": f"t{i}", "tags": text_tags}
        for i in range(2)
    ]
    payload, _ = _recall(module, results)

    assert all(row["quote"].startswith("Les réserves sont levées") for row in payload["results"])


def test_out_of_scope_text_layer_chunk_fails_closed() -> None:
    module = _module()
    beta = ["source:project-sync", f"scope:project:{module.project_scope_token('Projet Beta')}", "representation:text"]
    results = [
        _fact("f1", "Fait Alpha", "doc-1", _alpha_tags(module)),
        {"id": "t1", "text": "Passage Beta", "document_id": "doc-9:text", "chunk_id": "t1", "tags": beta},
    ]
    with pytest.raises(module.ProjectRecallError):
        _recall(module, results)
