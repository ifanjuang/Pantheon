"""Static contract checks for the cross-source competency corpus.

These checks verify that the documented evaluation scenarios retain their
essential contrast cases. They do NOT validate Hermes reasoning, APU ingestion,
or the longitudinal H5.8 runtime.
"""

from pathlib import Path
from unittest.mock import patch
import importlib.util
import re
import sys

import yaml

CORPUS = (
    Path(__file__).resolve().parents[1]
    / "docs/domain-packs/architecture/CROSS_SOURCE_COMPETENCY_CORPUS.md"
)


def _read() -> str:
    return CORPUS.read_text(encoding="utf-8")


def test_ten_cross_source_scenarios_are_distinct() -> None:
    text = _read()
    ids = re.findall(r"^### (C\d{2}) — ", text, flags=re.MULTILINE)
    assert ids == [f"C{i:02d}" for i in range(1, 11)]


def test_context_contrasts_are_present_without_new_phase_engine() -> None:
    text = _read()
    variants = re.findall(r"^\| (C\d{2}-[A-Z]) \|", text, flags=re.MULTILINE)
    assert variants == [
        "C01-A", "C01-B", "C01-C", "C01-D",
        "C03-A", "C03-B", "C03-C",
        "C08-A", "C08-B", "C08-C",
    ]
    assert "phase engine" in text.lower()
    assert "mixed-phase" in text


def test_epistemic_and_authorization_boundaries_are_explicit() -> None:
    # Markdown line wrapping is formatting, not a change of the invariant.
    text = " ".join(_read().lower().split())
    for phrase in (
        "never infer approval",
        "actual execution",
        "identity from a matching label",
        "without automatic write",
        "an explicitly asked question",
        "not executed acceptance",
    ):
        assert phrase.lower() in text


def _hindsight_router():
    """Import the existing read-only router, not a second memory adapter."""
    path = (
        Path(__file__).resolve().parents[1]
        / "implementation/hermes/hindsight_project_router/hindsight_project_recall.py"
    )
    spec = importlib.util.spec_from_file_location("core_first_hindsight_router", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_core_recall_lead_does_not_rewrite_source_candidates() -> None:
    """C03/C08: memory can locate a document, not decide a source conflict."""
    root = Path(__file__).resolve().parents[1]
    bundle = yaml.safe_load(
        (
            root
            / "schemas/examples/architecture-project-understanding/"
            "ifc_cross_source_conflict.example.yaml"
        ).read_text(encoding="utf-8")
    )
    # The already-validated H5.4 bundle reports incompatible source values.
    # A memory about the same project is an orientation lead, not a third claim.
    assert bundle["project_ref"] == "project-a"
    values = {
        claim["value"]["value"]
        for claim in bundle["attribute_claim_candidates"]
    }
    assert values == {"EI30", "EI60"}
    assert bundle["relation_claim_candidates"] == []
    assert all(value is False for value in bundle["authority"].values())

    router = _hindsight_router()
    scope_tag = f"scope:project:{router.project_scope_token('project-a')}"
    memory_hit = {
        "id": "memory-of-older-schedule",
        "text": "Le tableau des portes prévoit EI60.",
        "document_id": "doc-older-schedule:source",
        "chunk_id": "chunk-04",
        "tags": ["source:project-sync", scope_tag],
        "metadata": {
            "title": "Tableau ancien",
            "source_path": "AFFAIRES/project-a/tableau-B.pdf",
            "source_sha256": "a" * 64,
        },
    }
    client = router.ProjectRecallClient("http://127.0.0.1:8888", "PROJECTS")
    with patch.object(client, "_post", return_value={"results": [memory_hit]}):
        recalled = client.recall_project("project-a", "Quelle porte coupe-feu ?")

    assert recalled["project_scope"] == scope_tag
    assert recalled["source_scope"] == "source:project-sync"
    assert len(recalled["results"]) == 1
    assert recalled["results"][0]["document_id"] == "doc-older-schedule:source"
    assert "is_evidence" not in recalled["results"][0]
    # The recall cannot supply an admitted identity, replace an observed claim,
    # or make one of the contradictory source versions the universal winner.
    assert [claim["value"]["value"] for claim in bundle["attribute_claim_candidates"]] == [
        "EI30", "EI60"
    ]
    assert not any(claim.get("source_representation_refs") == ["doc-older-schedule:source"]
                   for claim in bundle["attribute_claim_candidates"])


def test_core_excludes_unprovenanced_memory_instead_of_inventing_a_reader() -> None:
    """A similarity hit cannot create a missing observation or source citation."""
    router = _hindsight_router()
    scope_tag = f"scope:project:{router.project_scope_token('project-a')}"
    client = router.ProjectRecallClient("http://127.0.0.1:8888", "PROJECTS")
    with patch.object(client, "_post", return_value={
        "results": [{
            "id": "unsupported-memory",
            "text": "Tout est approuvé et terminé.",
            "tags": ["source:project-sync", scope_tag],
        }],
    }):
        recalled = client.recall_project("project-a", "Est-ce terminé ?")

    # The existing router drops results with no exact document AND chunk.
    assert recalled["results"] == []
    core_contract = _read().lower()
    for boundary in (
        "cad vectors are geometric entities",
        "source_present_not_inspected",
        "observation bundle candidate",
        "context pack is temporary task context",
        "no memory summary may be recycled as new source",
    ):
        assert boundary in core_contract
