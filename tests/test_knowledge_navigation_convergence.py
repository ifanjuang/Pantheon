from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/governance/KNOWLEDGE_NAVIGATION_UX.md"


def test_knowledge_navigation_uses_category_as_backend_owner() -> None:
    text = DOC.read_text(encoding="utf-8")

    assert "Category owns the logical hierarchy" in text
    assert "UI folder\n= presentation of a Category as a navigation container" in text
    assert "knowledge_folder\nknowledge_folder_item_link" in text
    assert "retired as independent backend concepts" in text
    assert "Do not persist a parallel Folder tree for Knowledge navigation" in text

    assert (ROOT / "implementation/mvp_vertical/category_collection_read.py").is_file()
    assert (ROOT / "implementation/tests/test_cockpit_category_root_navigation.py").is_file()


def test_knowledge_navigation_keeps_distinct_ux_responsibility() -> None:
    text = DOC.read_text(encoding="utf-8")

    assert "documented non-implemented as dedicated UX" in text
    assert "CATEGORY_CLASSIFICATION_MODEL.md" in text
    assert "DOCUMENT_LIFECYCLE_GOVERNANCE.md" in text
    assert "DOCUMENT_PRODUCTION_LIFECYCLE.md" in text
    assert "HERMES_PROGRESS_ERROR_RETRY_UX.md" in text

    assert "Category container = filled gradient" in text
    assert "Knowledge item      = gradient outline, neutral fill" in text
    assert "projection != persistence" in text
    assert "classification != authorization" in text


def test_knowledge_navigation_does_not_reown_existing_lifecycles() -> None:
    text = DOC.read_text(encoding="utf-8")

    assert "This document does not duplicate the document lifecycle" in text
    assert "Generated or materially rewritten documents remain governed by `DOCUMENT_PRODUCTION_LIFECYCLE.md`" in text
    assert "Progress, errors, diagnosis and retry semantics are owned by `HERMES_PROGRESS_ERROR_RETRY_UX.md`" in text
