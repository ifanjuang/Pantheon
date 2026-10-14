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
    client = module.ProjectRecallClient("http://127.0.0.1:8888", "AGENCY_PROJECTS")
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
    assert body["include"] == {"entities": None, "chunks": {}, "source_facts": None}
    assert result["project_scope"] == f"scope:project:{module.project_scope_token('Projet Alpha')}"
    assert result["mode"] == "source-grounded-evidence"
    assert result["results"][0]["document_id"] == "doc-1:source"


def test_french_accents_normalize_to_stable_ascii_scope() -> None:
    module = _module()
    assert module.tag_value("Médiathèque André") == "mediatheque-andre"


def test_folder_can_only_narrow_an_existing_project_scope() -> None:
    module = _module()
    client = module.ProjectRecallClient("http://127.0.0.1:8888", "AGENCY_PROJECTS")
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
    client = module.ProjectRecallClient("http://127.0.0.1:8888", "AGENCY_PROJECTS")
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
    assert set(result["chunks"]) == {f"chunk-{index}" for index in range(8)}


def test_pending_or_empty_project_is_rejected_before_hindsight_call() -> None:
    module = _module()
    client = module.ProjectRecallClient("http://127.0.0.1:8888", "AGENCY_PROJECTS")
    for project in ("", "pending identification"):
        with pytest.raises(module.ProjectRecallError):
            client.recall_project(project, "question")


def test_out_of_scope_or_untagged_result_fails_closed() -> None:
    module = _module()
    client = module.ProjectRecallClient("http://127.0.0.1:8888", "AGENCY_PROJECTS")
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
