from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_document_knowledge_contract_keeps_machine_boundary_and_drops_client_owner():
    text = _read("docs/governance/DOCUMENT_KNOWLEDGE_SLICE_CONTRACT.md")
    schema = _read("schemas/document_knowledge_slice.schema.yaml")

    assert "OpenWebUI" not in text
    assert "schemas/document_knowledge_slice.schema.yaml" in text
    for family in (
        "source_document",
        "extraction",
        "document_structure",
        "chunk[]",
        "project_document_card",
        "knowledge_publication[]",
        "version_event[]",
    ):
        assert family in text
    assert "Pantheon Cockpit" in text
    assert "runtime success != approval" in text
    assert "automatic_evidence_admission: false" in schema
    assert "memory_promotion: false" in schema
    assert "automatic_approval: false" in schema


def test_source_ingestion_model_is_provider_and_client_agnostic():
    text = _read("docs/governance/SOURCE_INGESTION_RETRIEVAL_MODEL.md")
    assert "OpenWebUI" not in text
    assert "ifanjuang/pantheon-mvp" not in text
    assert "linked != approved" in text
    assert "cached != retained" in text
    assert "ingested != Evidence" in text
    assert "retrieved != true" in text
    assert "provider selected != authority transfer" in text
    assert "Direct source/context access is valid when sufficient" in text
    assert "Pantheon Cockpit" in text


def test_layered_record_model_preserves_seven_distinct_layers():
    text = _read("docs/governance/RAW_DERIVED_GOVERNED_RECORDS.md")
    assert "OpenWebUI" not in text
    for label in (
        "1. Raw content",
        "2. Derived content",
        "3. Governed records",
        "4. Retrieval objects",
        "5. Provenance objects",
        "6. Evidence objects",
        "7. Approval and decision records",
    ):
        assert label in text
    assert "projection != persistence" in text
    assert "retrieval score != authority" in text
    assert "runtime completion != authorization" in text


def test_information_acquisition_reuses_existing_owners_without_new_router():
    lifecycle = _read("docs/governance/REQUEST_LIFECYCLE.md")
    sources = _read("docs/governance/SOURCE_NEED_AND_REGISTRY.md")
    adapters = _read("docs/governance/ADAPTERS_AND_BINDINGS.md")

    assert "least indirect admitted route" in lifecycle
    assert "typed query against its existing operational owner" in lifecycle
    assert "creates no Pantheon router" in lifecycle
    assert "query_operational_owner" in sources
    assert "an acquisition route, not a source family" in sources
    assert "AI-specific shadow store" in adapters
    assert "runtime -> typed adapter -> existing operational owner" in adapters


def test_workspace_source_notebook_reuses_registry_owner_without_parallel_authority():
    sources = _read("docs/governance/SOURCE_NEED_AND_REGISTRY.md")

    for invariant in (
        "workspace source notebook != Source Registry",
        "notebook entry != Source Registry Entry",
        "listed route != inspected source",
        "workspace path != governed identity",
    ):
        assert invariant in sources

    assert "one note, manifest or governed object per website" in sources
    assert "Source Addition Candidate" in sources
    assert "Hermes and other consumers must not hard-code an Obsidian-specific" in sources
