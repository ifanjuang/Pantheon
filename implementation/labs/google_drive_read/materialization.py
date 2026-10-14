"""Content materialization for the bounded Google Drive read qualification.

Provider metadata is not a Source digest. This module plans one exact download or
export request, hashes only the bytes actually returned, and prepares fields that
can later be presented to the existing Source intake owner. It does not persist a
Source or retain bytes.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

from .adapter import DriveReadCandidate, GoogleDriveReadError


_GOOGLE_NATIVE_EXPORT_MIME = {
    "application/vnd.google-apps.document": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.google-apps.spreadsheet": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.google-apps.presentation": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.google-apps.drawing": "application/pdf",
}
_GOOGLE_NATIVE_PREFIX = "application/vnd.google-apps."


@dataclass(frozen=True)
class DriveMaterializedContent:
    provider: str
    file_id: str
    source_locator: str
    original_mime_type: str
    materialized_mime_type: str
    export_mime_type: str | None
    provider_version: str | None
    modified_time: str | None
    content_sha256: str
    byte_size: int
    scope_folder_id: str
    scope_drive_id: str | None


def _validate_candidate_identity(candidate: DriveReadCandidate) -> None:
    expected_locator = f"gdrive://file/{quote(candidate.file_id, safe='')}"
    if candidate.provider != "google_drive" or candidate.source_locator != expected_locator:
        raise GoogleDriveReadError("Drive read candidate does not preserve its provider file identity")
    if candidate.scope_folder_id not in candidate.parents:
        raise GoogleDriveReadError("Drive read candidate no longer proves its explicit folder scope")


def _content_request_parts(candidate: DriveReadCandidate) -> tuple[str, dict[str, Any], str | None]:
    _validate_candidate_identity(candidate)
    if candidate.can_download is not True:
        raise GoogleDriveReadError("provider did not prove capabilities.canDownload before materialization")
    encoded_file_id = quote(candidate.file_id, safe="")
    export_mime = _GOOGLE_NATIVE_EXPORT_MIME.get(candidate.mime_type)
    if export_mime:
        return (
            f"/drive/v3/files/{encoded_file_id}/export",
            {"mimeType": export_mime},
            export_mime,
        )
    if candidate.mime_type.startswith(_GOOGLE_NATIVE_PREFIX):
        raise GoogleDriveReadError(
            f"no reviewed deterministic export profile for Google-native MIME type {candidate.mime_type}"
        )

    params: dict[str, Any] = {"alt": "media"}
    if candidate.scope_drive_id:
        params["supportsAllDrives"] = True
    return f"/drive/v3/files/{encoded_file_id}", params, None


def direct_google_content_request(candidate: DriveReadCandidate) -> dict[str, Any]:
    path, params, export_mime = _content_request_parts(candidate)
    return {
        "method": "GET",
        "url": f"https://www.googleapis.com{path}",
        "params": params,
        "export_mime_type": export_mime,
        "execution_ready": False,
        "credential_requirement": "external_google_oauth",
    }


def nango_google_content_request(
    candidate: DriveReadCandidate,
    *,
    provider_config_key: str,
    connection_id: str,
) -> dict[str, Any]:
    if not provider_config_key.strip() or not connection_id.strip():
        raise GoogleDriveReadError("opaque Nango provider and connection handles are required")
    path, params, export_mime = _content_request_parts(candidate)
    return {
        "method": "GET",
        "url": f"https://api.nango.dev/proxy{path}",
        "params": params,
        "export_mime_type": export_mime,
        "headers": {
            "Provider-Config-Key": provider_config_key,
            "Connection-Id": connection_id,
        },
        "execution_ready": False,
        "credential_requirement": "external_nango_environment_secret",
    }


def materialize_content(
    candidate: DriveReadCandidate,
    content: bytes,
    *,
    content_type: str | None = None,
    export_mime_type: str | None = None,
) -> DriveMaterializedContent:
    _validate_candidate_identity(candidate)
    if candidate.can_download is not True:
        raise GoogleDriveReadError("provider did not prove capabilities.canDownload before materialization")
    if not isinstance(content, bytes) or not content:
        raise GoogleDriveReadError("materialized content must be non-empty bytes")

    expected_export = _GOOGLE_NATIVE_EXPORT_MIME.get(candidate.mime_type)
    if candidate.mime_type.startswith(_GOOGLE_NATIVE_PREFIX):
        if expected_export is None:
            raise GoogleDriveReadError(
                f"no reviewed deterministic export profile for Google-native MIME type {candidate.mime_type}"
            )
        if export_mime_type != expected_export:
            raise GoogleDriveReadError("materialized Google-native export MIME does not match request profile")
        materialized_mime = expected_export
    else:
        if export_mime_type is not None:
            raise GoogleDriveReadError("binary Drive content must not claim a Google-native export MIME")
        materialized_mime = str(content_type or candidate.mime_type).strip()
        if not materialized_mime:
            raise GoogleDriveReadError("materialized content MIME type is required")

    return DriveMaterializedContent(
        provider="google_drive",
        file_id=candidate.file_id,
        source_locator=candidate.source_locator,
        original_mime_type=candidate.mime_type,
        materialized_mime_type=materialized_mime,
        export_mime_type=export_mime_type,
        provider_version=candidate.provider_version,
        modified_time=candidate.modified_time,
        content_sha256=hashlib.sha256(content).hexdigest(),
        byte_size=len(content),
        scope_folder_id=candidate.scope_folder_id,
        scope_drive_id=candidate.scope_drive_id,
    )


def build_source_intake_draft(
    candidate: DriveReadCandidate,
    materialized: DriveMaterializedContent,
) -> dict[str, Any]:
    _validate_candidate_identity(candidate)
    if (
        materialized.provider != "google_drive"
        or materialized.file_id != candidate.file_id
        or materialized.source_locator != candidate.source_locator
        or materialized.scope_folder_id != candidate.scope_folder_id
        or materialized.scope_drive_id != candidate.scope_drive_id
        or materialized.original_mime_type != candidate.mime_type
        or materialized.provider_version != candidate.provider_version
        or materialized.modified_time != candidate.modified_time
    ):
        raise GoogleDriveReadError("materialized content identity or revision differs from the bounded read candidate")

    return {
        "source_kind": "document",
        "origin_system": "google_drive",
        "origin_external_ref": candidate.file_id,
        "raw_source_ref": candidate.source_locator,
        "mime_type": candidate.mime_type,
        "metadata": {
            "google_drive": {
                "file_id": candidate.file_id,
                "name": candidate.name,
                "parents": list(candidate.parents),
                "modified_time": candidate.modified_time,
                "provider_version": candidate.provider_version,
                "web_view_link": candidate.web_view_link,
                "scope_folder_id": candidate.scope_folder_id,
                "scope_drive_id": candidate.scope_drive_id,
                "original_mime_type": candidate.mime_type,
                "materialized_mime_type": materialized.materialized_mime_type,
                "export_mime_type": materialized.export_mime_type,
                "materialized_content_sha256": materialized.content_sha256,
                "materialized_representation_preserved": False,
                "byte_size": materialized.byte_size,
            }
        },
    }


AUTHORITY = {
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
