"""The existing Document card exposes structured diagnostics without a new card family."""

from pathlib import Path


def test_document_verso_projects_structured_extraction_diagnostics() -> None:
    renderer = (
        Path(__file__).resolve().parents[1]
        / "mvp_vertical"
        / "cockpit"
        / "projection"
        / "cockpit_projection.js"
    ).read_text(encoding="utf-8")

    assert "const structured = item.structured_extraction || {};" in renderer
    assert "const chunks = item.chunk_summary || {};" in renderer
    assert '["Extraction structurée", text(structured.status' in renderer
    assert '["Pages / tableaux"' in renderer
    assert '["Anomalies", text(structured.anomaly_count' in renderer
    assert '["Chunks / indexés"' in renderer
    assert '["Chunks signalés"' in renderer
    assert '["Vérification source"' in renderer
    assert "subject_tags: item.subject_tags || item.tags || []" in renderer
    assert 'entity_type: "document"' in renderer


def test_document_chunk_inspection_requires_compilation_identity() -> None:
    """Inspection is offered only for documents with a real compilation identity.

    A failed or uncompiled document still projects ``chunk_summary.total`` as ``0``
    (not ``null``) while its ``document_compilation_bindings`` row is absent, so a
    gate that only checked for ``null`` exposed an inspector action whose endpoint
    then returned 404. The action must be gated on ``compilation_id`` instead.
    """

    renderer = (
        Path(__file__).resolve().parents[1]
        / "mvp_vertical"
        / "cockpit"
        / "projection"
        / "cockpit_projection.js"
    ).read_text(encoding="utf-8")

    assert 'structured.compilation_id && chunks.total ? ["Inspecter les chunks"] : []' in renderer
    # The previous null-only gate must not come back.
    assert 'chunks.total == null ? [] : ["Inspecter les chunks"]' not in renderer


def test_document_chunk_inspector_keeps_query_scores_contextual() -> None:
    root = Path(__file__).resolve().parents[1] / "mvp_vertical" / "cockpit"
    actions = (root / "actions" / "card_actions.js").read_text(encoding="utf-8")
    styles = (root / "styles" / "editors.css").read_text(encoding="utf-8")

    assert '"Inspecter les chunks"' in actions
    assert "/chunks?${params}" in actions
    assert "Le score de proximité dépend d’une requête" in actions
    assert "verification_status === \"not_observed\"" in actions
    assert ".v2-document-chunk-inspector" in styles
