"""Qualify bounded Hermes visibility of workspace PDF document metadata."""

from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    ROOT
    / "docs"
    / "examples"
    / "workspace_manifest_inspector"
    / "qualification"
    / "m5_hermes_pdf_context.yaml"
)
SCOPED_CONTEXT = ROOT / "implementation" / "mvp_vertical" / "hermes_scoped_context.py"


def _load() -> dict:
    with FIXTURE.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    assert isinstance(value, dict)
    return value


def test_admitted_pdf_metadata_is_materializable_without_hindsight() -> None:
    fixture = _load()
    source = SCOPED_CONTEXT.read_text(encoding="utf-8")
    projection = fixture["expected_hermes_document_projection"]
    fields = projection["record_fields"]

    assert fixture["qualification"]["runtime_change_required"] is False
    assert fixture["workspace_observation"]["media_type"] == "application/pdf"
    assert fixture["context_pack"]["included_entities"] == [
        {
            "entity_type": "document",
            "entity_id": "document:22222222-2222-4222-8222-222222222222",
        }
    ]
    assert fields["media_type"] == "application/pdf"
    assert fields["source_ref"] == "source:verger-etude-g2-pdf"
    assert fields["source_digest"].startswith("sha256:")
    assert fixture["boundaries"]["hindsight_is_not_required_for_file_existence"] is True

    for field in (
        "document_id",
        "source_ref",
        "source_digest",
        "media_type",
        "byte_size",
        "analysis_status",
    ):
        assert f'"{field}",' in source
    assert '"document",' in source


def test_pdf_context_does_not_widen_into_global_workspace_access() -> None:
    fixture = _load()
    expected = fixture["expected_hermes_manifest"]
    source = SCOPED_CONTEXT.read_text(encoding="utf-8")

    assert expected["document_entity_materializable"] is True
    assert expected["source_dereference_available"] is False
    assert expected["global_search_available"] is False
    assert expected["global_listing_available"] is False
    assert '"source_dereference_available": False' in source
    assert '"global_search_available": False' in source
    assert '"global_listing_available": False' in source


def test_unadmitted_pdf_remains_workspace_observation_not_governed_document() -> None:
    fixture = _load()
    case = fixture["unmanifested_or_unadmitted_pdf"]

    assert case["observable_through_bounded_workspace_filesystem"] is True
    assert case["automatically_admitted_to_context_pack"] is False
    assert case["automatically_materializable_as_governed_document"] is False
    assert case["requires_hindsight_to_know_file_exists"] is False
    assert fixture["boundaries"]["manifest_present_is_not_document_admission"] is True
    assert fixture["boundaries"]["workspace_path_is_not_governed_identity"] is True


def test_document_projection_never_smuggles_source_binary_or_redefines_authority() -> None:
    fixture = _load()
    representation = fixture["expected_hermes_document_projection"]["optional_representation"]
    boundaries = fixture["boundaries"]
    source = SCOPED_CONTEXT.read_text(encoding="utf-8")

    assert representation["kind"] == "derived_markdown"
    assert representation["source_binary_included"] is False
    assert representation["may_be_absent"] is True
    assert '"source_binary_included": False' in source

    for key in (
        "pdf_observed_is_not_pdf_content_understood",
        "source_ref_is_not_source_dereference_authority",
        "context_pack_inclusion_is_not_evidence",
        "document_projection_is_not_source_binary",
        "derived_markdown_is_not_exact_source",
        "global_listing_is_not_implicitly_authorized",
        "projection_is_not_persistence",
    ):
        assert boundaries[key] is True
