"""Bounded Google Drive read qualification adapter.

This lab normalizes provider responses before any Pantheon Source admission.
It owns no credentials, source identity, currentness, Evidence admission or
retrieval policy. A Drive item returned here is a read candidate only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import quote


class GoogleDriveReadError(ValueError):
    """Fail-closed provider-read qualification error."""


@dataclass(frozen=True)
class DriveReadScope:
    folder_id: str
    drive_id: str | None = None

    def __post_init__(self) -> None:
        if not self.folder_id.strip():
            raise GoogleDriveReadError("folder_id is required")
        if self.drive_id is not None and not self.drive_id.strip():
            raise GoogleDriveReadError("drive_id must be non-empty when supplied")


@dataclass(frozen=True)
class DriveReadCandidate:
    provider: str
    file_id: str
    name: str
    mime_type: str
    parents: tuple[str, ...]
    modified_time: str | None
    provider_version: str | None
    web_view_link: str | None
    content_checksum: str | None
    can_download: bool | None
    source_locator: str
    scope_folder_id: str
    scope_drive_id: str | None
    requires_content_hash: bool


_FIELDS = (
    "nextPageToken,incompleteSearch,files("
    "id,name,mimeType,parents,modifiedTime,version,webViewLink,md5Checksum,trashed,driveId,capabilities(canDownload))"
)


def _drive_query_literal(value: str) -> str:
    """Escape an opaque Drive id before embedding it in a Drive query literal."""
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _source_locator(file_id: str) -> str:
    return f"gdrive://file/{quote(file_id, safe='')}"


def direct_google_list_request(scope: DriveReadScope) -> dict[str, Any]:
    folder_literal = _drive_query_literal(scope.folder_id)
    params: dict[str, Any] = {
        "q": f"'{folder_literal}' in parents and trashed = false",
        "fields": _FIELDS,
        "pageSize": 1000,
    }
    if scope.drive_id:
        params.update(
            {
                "corpora": "drive",
                "driveId": scope.drive_id,
                "includeItemsFromAllDrives": True,
                "supportsAllDrives": True,
            }
        )
    return {
        "method": "GET",
        "url": "https://www.googleapis.com/drive/v3/files",
        "params": params,
        "execution_ready": False,
        "credential_requirement": "external_google_oauth",
    }


def nango_google_list_request(
    scope: DriveReadScope,
    *,
    provider_config_key: str,
    connection_id: str,
) -> dict[str, Any]:
    if not provider_config_key.strip() or not connection_id.strip():
        raise GoogleDriveReadError("opaque Nango provider and connection handles are required")
    direct = direct_google_list_request(scope)
    return {
        "method": "GET",
        "url": "https://api.nango.dev/proxy/drive/v3/files",
        "params": direct["params"],
        "headers": {
            "Provider-Config-Key": provider_config_key,
            "Connection-Id": connection_id,
        },
        "execution_ready": False,
        "credential_requirement": "external_nango_environment_secret",
    }


def normalize_list_response(scope: DriveReadScope, payload: Mapping[str, Any]) -> tuple[DriveReadCandidate, ...]:
    if payload.get("incompleteSearch") is True:
        raise GoogleDriveReadError("provider reported incomplete scoped search")
    if str(payload.get("nextPageToken") or "").strip():
        raise GoogleDriveReadError("provider page requires explicit pagination before inventory is complete")

    candidates: list[DriveReadCandidate] = []
    for raw in payload.get("files") or ():
        if raw.get("trashed") is True:
            raise GoogleDriveReadError("trashed item returned inside read-only scope")

        file_id = str(raw.get("id") or "").strip()
        name = str(raw.get("name") or "").strip()
        mime_type = str(raw.get("mimeType") or "").strip()
        parents = tuple(str(parent) for parent in raw.get("parents") or () if str(parent).strip())
        if not file_id or not name or not mime_type:
            raise GoogleDriveReadError("provider item is missing stable identity metadata")
        if scope.folder_id not in parents:
            raise GoogleDriveReadError("provider returned item outside explicit folder scope")
        if scope.drive_id and str(raw.get("driveId") or "").strip() != scope.drive_id:
            raise GoogleDriveReadError("provider did not prove the explicit shared-drive scope")

        checksum = str(raw.get("md5Checksum") or "").strip() or None
        capabilities = raw.get("capabilities") or {}
        can_download = (
            capabilities.get("canDownload")
            if isinstance(capabilities, Mapping)
            and isinstance(capabilities.get("canDownload"), bool)
            else None
        )
        candidates.append(
            DriveReadCandidate(
                provider="google_drive",
                file_id=file_id,
                name=name,
                mime_type=mime_type,
                parents=parents,
                modified_time=str(raw.get("modifiedTime") or "").strip() or None,
                provider_version=str(raw.get("version") or "").strip() or None,
                web_view_link=str(raw.get("webViewLink") or "").strip() or None,
                content_checksum=checksum,
                can_download=can_download,
                source_locator=_source_locator(file_id),
                scope_folder_id=scope.folder_id,
                scope_drive_id=scope.drive_id,
                requires_content_hash=True,
            )
        )
    return tuple(candidates)


AUTHORITY = {
    "read_only": True,
    "owns_credentials": False,
    "carries_provider_secret": False,
    "executes_provider_request": False,
    "admits_source": False,
    "creates_source_digest": False,
    "decides_currentness": False,
    "admits_evidence": False,
    "authorizes": False,
    "persists_state": False,
    "write_surface": False,
}
