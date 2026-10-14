from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "implementation/hermes/skills/vault-search/SKILL.md"
PDF_REFERENCE = ROOT / "implementation/hermes/skills/vault-search/references/pdf-plans.md"
PROFILE = ROOT / "implementation/hermes/skills/vault-search/references/organization-profile.yaml"


def test_docling_route_uses_conversion_source_and_shared_workspace_paths() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert "convert_document_into_docling_document(source)" in text
    assert '{"source": "/srv/pantheon/obsidian-documentaires/<document>.pdf"}' in text
    assert "get_overview_of_document_anchors(document_key)" in text
    assert "Do not call `get_prompt`, `list_prompts`, `read_resource` or `list_resources`" in text
    assert "source_not_visible_to_docling" in text
    assert "/home/hermeswebui/.hermes/webui/attachments" in text
    assert "Do not silently copy a" in text
    assert "`get_document` for an identified document" in text
    assert "A router recall is an index lead, not an inspected source" in text
    assert "open that exact local source" in text
    assert "Source coverage and inventory fallback" in text
    assert "source_present_not_indexed" in text
    assert "A document dropped into the chat is session input by default" in text


def test_pdf_reference_and_organization_binding_match_docling_route() -> None:
    reference = PDF_REFERENCE.read_text(encoding="utf-8")
    profile = PROFILE.read_text(encoding="utf-8")

    assert "source: <chemin partagé ou URL>" in reference
    assert "Ne pas appeler `get_prompt`, `list_prompts`, `read_resource` ou `list_resources`" in reference
    assert "textual_analysis_binding: docling" in profile
