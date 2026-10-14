from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_document_lifecycle_is_client_and_provider_agnostic():
    text = _read("docs/governance/DOCUMENT_LIFECYCLE_GOVERNANCE.md")
    assert "OpenWebUI" not in text
    assert "OPENWEBUI_INTEGRATION.md" not in text
    assert "pantheon-document-intake" not in text
    assert "PaddleOCR" not in text
    assert "Qwen" not in text
    assert "pgvector" not in text
    assert "Hermes is the preferred candidate execution binding" not in text


def test_document_lifecycle_preserves_core_boundaries():
    text = _read("docs/governance/DOCUMENT_LIFECYCLE_GOVERNANCE.md")
    for invariant in (
        "source received != source accepted",
        "summary generated != Evidence",
        "Knowledge publication != Evidence admission",
        "retrieved != truth",
        "runtime success != authorization",
        "projection != persistence",
        "Card != source",
        "Processing Attestation != proof that extracted meaning is correct",
    ):
        assert invariant in text


def test_document_lifecycle_composes_existing_machine_owner():
    text = _read("docs/governance/DOCUMENT_LIFECYCLE_GOVERNANCE.md")
    schema = _read("schemas/document_knowledge_slice.schema.yaml")
    assert "schemas/document_knowledge_slice.schema.yaml" in text
    assert "DOCUMENT_KNOWLEDGE_SLICE_CONTRACT.md" in text
    assert "SOURCE_INGESTION_RETRIEVAL_MODEL.md" in text
    assert "RAW_DERIVED_GOVERNED_RECORDS.md" in text
    assert "source_document:" in schema
    assert "document_structure:" in schema
    assert "knowledge_publications:" in schema
    assert "automatic_evidence_admission: false" in schema
    assert "memory_promotion: false" in schema


def test_document_lifecycle_keeps_classification_index_and_evidence_distinct():
    text = _read("docs/governance/DOCUMENT_LIFECYCLE_GOVERNANCE.md")
    assert "classified != indexed" in text
    assert "Knowledge published != indexed" in text
    assert "index revoked != source deleted" in text
    assert "retrieval result\n-> deliberate selection for a scoped assertion\n-> Evidence Candidate / Evidence Item" in text
