from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/governance/CATEGORY_CLASSIFICATION_MODEL.md"

COLOCATED_ARTIFACTS = (
    ROOT / "schemas/category_classification.schema.yaml",
    ROOT / "implementation/mvp_vertical/sql/034_category_classification.sql",
    ROOT / "implementation/mvp_vertical/agency_classification.py",
    ROOT / "implementation/mvp_vertical/agency_classification_api.py",
    ROOT / "implementation/mvp_vertical/category_collection_read.py",
    ROOT / "implementation/mvp_vertical/category_collection_read_api.py",
    ROOT / "implementation/mvp_vertical/cockpit_card_projection.py",
    ROOT / "implementation/tests/test_agency_classification.py",
    ROOT / "implementation/tests/test_agency_classification_concurrency.py",
    ROOT / "implementation/tests/test_category_collection_read.py",
    ROOT / "implementation/tests/test_category_root_collection_read.py",
)


def test_category_owner_reports_colocated_partial_implementation() -> None:
    text = DOC.read_text(encoding="utf-8")

    for artifact in COLOCATED_ARTIFACTS:
        assert artifact.exists(), artifact

    assert "bounded co-located implementation partial" in text
    assert "implementation/mvp_vertical/" in text
    assert "Historical implementation work in `ifanjuang/pantheon-mvp` PRs #328–#331 remains provenance" in text
    assert "It is no longer the current repository placement owner" in text


def test_category_projection_done_but_legacy_and_multi_project_gaps_remain() -> None:
    text = DOC.read_text(encoding="utf-8")

    assert "4. move Cockpit navigation to Category Card/Collection projection;   DONE" in text
    assert "3. map existing scalar categories explicitly where justified;       NOT DONE" in text
    assert "5. retire legacy scalar classification after all consumers migrate;  NOT DONE" in text
    assert "General multi-Project reuse remains a separate unresolved responsibility" in text

    assert "projection != persistence" in text
    assert "implementation present != adopted or production-active" in text
