from dataclasses import replace
from inspect import signature

import pytest

from mvp_vertical import source_intake

from labs.google_drive_read.adapter import DriveReadCandidate, GoogleDriveReadError
from labs.google_drive_read.materialization import (
    AUTHORITY,
    build_source_intake_draft,
    direct_google_content_request,
    materialize_content,
    nango_google_content_request,
)


def _candidate(**overrides):
    values = {
        "provider": "google_drive",
        "file_id": "file-1",
        "name": "CCTP.pdf",
        "mime_type": "application/pdf",
        "parents": ("folder-a",),
        "modified_time": "2026-09-02T05:00:00Z",
        "provider_version": "17",
        "web_view_link": "https://drive.google.com/file/d/file-1/view",
        "content_checksum": "provider-md5",
        "can_download": True,
        "source_locator": "gdrive://file/file-1",
        "scope_folder_id": "folder-a",
        "scope_drive_id": None,
        "requires_content_hash": True,
    }
    values.update(overrides)
    return DriveReadCandidate(**values)


def test_binary_direct_and_nango_materialize_the_same_google_resource():
    candidate = _candidate(scope_drive_id="drive-a")
    direct = direct_google_content_request(candidate)
    nango = nango_google_content_request(
        candidate,
        provider_config_key="google-drive-project",
        connection_id="opaque-connection",
    )

    assert direct["url"].endswith("/drive/v3/files/file-1")
    assert nango["url"].endswith("/drive/v3/files/file-1")
    assert direct["execution_ready"] is False
    assert nango["execution_ready"] is False
    assert direct["params"] == nango["params"] == {
        "alt": "media",
        "supportsAllDrives": True,
    }
    assert direct["export_mime_type"] is None
    assert nango["export_mime_type"] is None


def test_google_native_document_uses_explicit_reviewed_export_profile():
    candidate = _candidate(
        name="Compte rendu",
        mime_type="application/vnd.google-apps.document",
        content_checksum=None,
    )
    direct = direct_google_content_request(candidate)
    nango = nango_google_content_request(
        candidate,
        provider_config_key="google-drive-project",
        connection_id="opaque-connection",
    )
    expected = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    assert direct["url"].endswith("/drive/v3/files/file-1/export")
    assert nango["url"].endswith("/drive/v3/files/file-1/export")
    assert direct["params"] == nango["params"] == {"mimeType": expected}
    assert direct["export_mime_type"] == expected


def test_unreviewed_google_native_type_fails_closed():
    candidate = _candidate(mime_type="application/vnd.google-apps.form")
    with pytest.raises(GoogleDriveReadError, match="no reviewed deterministic export profile"):
        direct_google_content_request(candidate)


def test_sha256_depends_on_materialized_bytes_not_provider_metadata():
    content = b"same exact bytes"
    first = materialize_content(_candidate(provider_version="17"), content)
    second = materialize_content(
        _candidate(provider_version="18", modified_time="2026-09-02T06:00:00Z"),
        content,
    )

    assert first.content_sha256 == second.content_sha256
    assert first.provider_version != second.provider_version


def test_changed_bytes_change_sha256_even_when_provider_version_is_unchanged():
    candidate = _candidate(provider_version="17")
    first = materialize_content(candidate, b"revision A")
    second = materialize_content(candidate, b"revision B")

    assert first.content_sha256 != second.content_sha256


def test_native_materialization_requires_the_exact_planned_export_mime():
    candidate = _candidate(mime_type="application/vnd.google-apps.spreadsheet")
    expected = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    materialized = materialize_content(
        candidate,
        b"xlsx-export-bytes",
        export_mime_type=expected,
    )
    assert materialized.materialized_mime_type == expected
    assert materialized.export_mime_type == expected

    with pytest.raises(GoogleDriveReadError, match="export MIME"):
        materialize_content(candidate, b"other", export_mime_type="text/csv")


def test_source_intake_draft_uses_existing_owner_fields_without_claiming_admission():
    candidate = _candidate()
    materialized = materialize_content(candidate, b"pdf bytes", content_type="application/pdf")
    draft = build_source_intake_draft(candidate, materialized)

    assert draft["source_kind"] == "document"
    assert draft["origin_system"] == "google_drive"
    assert draft["origin_external_ref"] == "file-1"
    assert draft["raw_source_ref"] == "gdrive://file/file-1"
    assert "checksum" not in draft
    assert draft["mime_type"] == "application/pdf"
    assert draft["metadata"]["google_drive"]["materialized_mime_type"] == "application/pdf"
    assert draft["metadata"]["google_drive"]["provider_version"] == "17"
    assert draft["metadata"]["google_drive"]["materialized_content_sha256"] == materialized.content_sha256
    assert draft["metadata"]["google_drive"]["materialized_representation_preserved"] is False
    assert "source_id" not in draft
    assert "actor" not in draft
    assert "idempotency_key" not in draft
    assert "received_at" not in draft


def test_intake_draft_refuses_materialized_identity_substitution():
    candidate = _candidate()
    materialized = materialize_content(candidate, b"pdf bytes")
    substituted = replace(materialized, source_locator="gdrive://file/file-2")

    with pytest.raises(GoogleDriveReadError, match="identity or revision differs"):
        build_source_intake_draft(candidate, substituted)


@pytest.mark.parametrize(
    "revision_override",
    [
        {"provider_version": "18"},
        {"modified_time": "2026-09-03T07:00:00Z"},
        {"mime_type": "application/octet-stream"},
    ],
)
def test_intake_draft_rejects_materialization_from_another_revision(
    revision_override,
):
    previous = _candidate()
    materialized = materialize_content(previous, b"old revision bytes")
    refreshed = replace(previous, **revision_override)

    with pytest.raises(GoogleDriveReadError, match="identity or revision differs"):
        build_source_intake_draft(refreshed, materialized)


def test_materialization_lab_has_no_source_write_authority():
    assert AUTHORITY == {
        "read_only": True,
        "owns_credentials": False,
        "computes_content_sha256": True,
        "promotes_content_sha256_to_source_checksum": False,
        "carries_provider_secret": False,
        "executes_provider_request": False,
        "admits_source": False,
        "persists_source": False,
        "retains_bytes": False,
        "decides_currentness": False,
        "admits_evidence": False,
        "authorizes": False,
        "write_surface": False,
    }


def test_materialization_requires_provider_download_capability():
    for value in (False, None):
        candidate = _candidate(can_download=value)
        with pytest.raises(GoogleDriveReadError, match="canDownload"):
            direct_google_content_request(candidate)
        with pytest.raises(GoogleDriveReadError, match="canDownload"):
            materialize_content(candidate, b"unexpected bytes")


def test_intake_draft_keys_remain_compatible_with_current_source_owner():
    candidate = _candidate()
    materialized = materialize_content(candidate, b"pdf bytes", content_type="application/pdf")
    draft = build_source_intake_draft(candidate, materialized)
    owner_fields = set(signature(source_intake.create_source).parameters) - {"conn"}
    assert set(draft) <= owner_fields
    assert {"source_id", "received_at", "actor", "actor_kind", "idempotency_key"}.isdisjoint(draft)


def test_native_source_mime_remains_distinct_from_export_representation():
    candidate = _candidate(
        mime_type="application/vnd.google-apps.document",
        content_checksum=None,
    )
    exported = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    materialized = materialize_content(
        candidate,
        b"docx bytes",
        export_mime_type=exported,
    )
    draft = build_source_intake_draft(candidate, materialized)
    assert draft["mime_type"] == "application/vnd.google-apps.document"
    assert draft["metadata"]["google_drive"]["materialized_mime_type"] == exported
    assert draft["metadata"]["google_drive"]["export_mime_type"] == exported
