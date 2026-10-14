"""Bounded local ephemeral context for read-only Hermes handoffs.

The lease owner stores temporary UTF-8 context outside AFFAIRES, Hindsight,
Source and Evidence owners. Handoffs persist only immutable lease descriptors.
Bytes are materialized only after an admitted launch is reserved.

This module owns no scheduler, queue, runtime dispatch, provider credential or
professional retention policy. Expiry is enforced on every read and cleanup is
lazy/best-effort.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


MIN_TTL_SECONDS = 60
MAX_TTL_SECONDS = 900
MAX_LEASE_ITEMS = 20
MAX_ITEM_BYTES = 60_000
MAX_TOTAL_BYTES = 100_000
MAX_PROVENANCE_ITEMS = 20
MAX_PROVENANCE_CHARS = 20_000
REPRESENTATION_KIND = "utf8_text"
ITEM_ROLES = frozenset({"target", "context", "provider_item"})

_SECRET_KEYS = {
    "password",
    "token",
    "secret",
    "credential",
    "credentials",
    "api_key",
    "authorization",
    "access_token",
    "refresh_token",
}


class EphemeralContextError(ValueError):
    pass


class EphemeralContextNotFound(EphemeralContextError):
    pass


class EphemeralContextExpired(EphemeralContextError):
    pass


class EphemeralContextIntegrityError(EphemeralContextError):
    pass


class EphemeralContextTooLarge(EphemeralContextError):
    pass


def default_root() -> Path:
    raw = os.getenv("PANTHEON_EPHEMERAL_CONTEXT_ROOT", "").strip()
    if raw:
        return Path(raw)
    return Path(tempfile.gettempdir()) / "pantheon-hermes-ephemeral-context"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _parse_time(value: Any, *, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise EphemeralContextIntegrityError(f"{label} is missing")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise EphemeralContextIntegrityError(f"{label} is invalid") from exc
    if parsed.tzinfo is None:
        raise EphemeralContextIntegrityError(f"{label} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require_sha256(value: Any, *, label: str) -> str:
    digest = str(value or "").strip().lower()
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise EphemeralContextError(f"{label} must be a lowercase SHA-256 digest")
    return digest


def _contains_secret_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if normalized in _SECRET_KEYS:
                return True
            if _contains_secret_key(item):
                return True
    elif isinstance(value, list):
        return any(_contains_secret_key(item) for item in value)
    return False


def _normalize_provenance(value: Any, *, label: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise EphemeralContextError(f"{label} must be an array")
    if len(value) > MAX_PROVENANCE_ITEMS:
        raise EphemeralContextTooLarge(
            f"{label} exceeds {MAX_PROVENANCE_ITEMS} entries"
        )
    output: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise EphemeralContextError(f"{label}[{index}] must be an object")
        if _contains_secret_key(item):
            raise EphemeralContextError(
                f"{label}[{index}] contains credential-like material"
            )
        try:
            rendered = _canonical(item)
        except (TypeError, ValueError) as exc:
            raise EphemeralContextError(
                f"{label}[{index}] must be JSON-serializable"
            ) from exc
        if len(rendered) > MAX_PROVENANCE_CHARS:
            raise EphemeralContextTooLarge(
                f"{label}[{index}] exceeds {MAX_PROVENANCE_CHARS} characters"
            )
        output.append(json.loads(rendered))
    return output


def _normalize_item(raw: dict[str, Any], *, index: int) -> tuple[dict[str, Any], bytes]:
    if not isinstance(raw, dict):
        raise EphemeralContextError(f"items[{index}] must be an object")
    representation = str(raw.get("representation_kind") or REPRESENTATION_KIND).strip()
    if representation != REPRESENTATION_KIND:
        raise EphemeralContextError(
            f"items[{index}].representation_kind must be {REPRESENTATION_KIND}"
        )
    role = str(raw.get("role") or "provider_item").strip()
    if role not in ITEM_ROLES:
        raise EphemeralContextError(
            f"items[{index}].role must be one of: {', '.join(sorted(ITEM_ROLES))}"
        )
    content = raw.get("content_utf8")
    if not isinstance(content, str):
        raise EphemeralContextError(f"items[{index}].content_utf8 must be a string")
    payload = content.encode("utf-8")
    if not payload:
        raise EphemeralContextError(f"items[{index}].content_utf8 may not be empty")
    if len(payload) > MAX_ITEM_BYTES:
        raise EphemeralContextTooLarge(
            f"items[{index}] exceeds {MAX_ITEM_BYTES} bytes"
        )
    claimed = _require_sha256(
        raw.get("content_sha256"),
        label=f"items[{index}].content_sha256",
    )
    actual = _sha256_bytes(payload)
    if claimed != actual:
        raise EphemeralContextIntegrityError(
            f"items[{index}] checksum mismatch"
        )
    media_type = str(raw.get("media_type") or "text/plain; charset=utf-8").strip()
    if not media_type or len(media_type) > 200:
        raise EphemeralContextError(f"items[{index}].media_type is invalid")
    provenance = _normalize_provenance(
        raw.get("source_provenance"),
        label=f"items[{index}].source_provenance",
    )
    descriptor = {
        "item_id": f"item-{index + 1:02d}-{actual[:12]}",
        "content_sha256": actual,
        "byte_size": len(payload),
        "media_type": media_type,
        "representation_kind": REPRESENTATION_KIND,
        "role": role,
        "source_provenance": provenance,
    }
    return descriptor, payload


def _lease_dir(root: Path, lease_ref: str) -> Path:
    if not lease_ref.startswith("ephemeral-context-"):
        raise EphemeralContextError("lease_ref is invalid")
    if "/" in lease_ref or "\\" in lease_ref or ".." in lease_ref:
        raise EphemeralContextError("lease_ref is invalid")
    return root / lease_ref


def _metadata_path(root: Path, lease_ref: str) -> Path:
    return _lease_dir(root, lease_ref) / "lease.json"


def _descriptor(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "lease_ref": metadata["lease_ref"],
        "lease_digest": metadata["lease_digest"],
        "created_at": metadata["created_at"],
        "expires_at": metadata["expires_at"],
        "item_count": len(metadata["items"]),
        "total_bytes": sum(int(item["byte_size"]) for item in metadata["items"]),
        "items": [
            {
                "item_id": item["item_id"],
                "content_sha256": item["content_sha256"],
                "byte_size": item["byte_size"],
                "media_type": item["media_type"],
                "representation_kind": item["representation_kind"],
                "role": item["role"],
                "source_provenance": item["source_provenance"],
            }
            for item in metadata["items"]
        ],
        "transient": True,
        "professional_persistence": False,
    }


def cleanup_expired(
    *,
    root: Path | None = None,
    now: datetime | None = None,
) -> int:
    root = Path(root or default_root())
    now = (now or _utcnow()).astimezone(timezone.utc)
    if not root.exists():
        return 0
    removed = 0
    for candidate in root.iterdir():
        if not candidate.is_dir() or not candidate.name.startswith("ephemeral-context-"):
            continue
        metadata_path = candidate / "lease.json"
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            expires_at = _parse_time(metadata.get("expires_at"), label="expires_at")
        except Exception:
            continue
        if expires_at <= now:
            shutil.rmtree(candidate, ignore_errors=True)
            removed += 1
    return removed


def create_lease(
    *,
    items: list[dict[str, Any]],
    ttl_seconds: int,
    actor: str,
    root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    actor = str(actor or "").strip()
    if not actor:
        raise EphemeralContextError("human actor is required")
    if not isinstance(ttl_seconds, int) or isinstance(ttl_seconds, bool):
        raise EphemeralContextError("ttl_seconds must be an integer")
    if not MIN_TTL_SECONDS <= ttl_seconds <= MAX_TTL_SECONDS:
        raise EphemeralContextError(
            f"ttl_seconds must be between {MIN_TTL_SECONDS} and {MAX_TTL_SECONDS}"
        )
    if not isinstance(items, list) or not items:
        raise EphemeralContextError("items must contain at least one entry")
    if len(items) > MAX_LEASE_ITEMS:
        raise EphemeralContextTooLarge(
            f"items exceeds {MAX_LEASE_ITEMS} entries"
        )

    normalized: list[dict[str, Any]] = []
    payloads: list[bytes] = []
    total_bytes = 0
    for index, raw in enumerate(items):
        descriptor, payload = _normalize_item(raw, index=index)
        total_bytes += len(payload)
        if total_bytes > MAX_TOTAL_BYTES:
            raise EphemeralContextTooLarge(
                f"lease exceeds {MAX_TOTAL_BYTES} total bytes"
            )
        normalized.append(descriptor)
        payloads.append(payload)

    root = Path(root or default_root())
    root.mkdir(parents=True, exist_ok=True)
    try:
        root.chmod(0o700)
    except OSError:
        pass
    cleanup_expired(root=root, now=now)

    created_at = (now or _utcnow()).astimezone(timezone.utc)
    expires_at = created_at + timedelta(seconds=ttl_seconds)
    lease_ref = f"ephemeral-context-{uuid.uuid4().hex}"
    digest_basis = {
        "lease_ref": lease_ref,
        "created_at": _iso(created_at),
        "expires_at": _iso(expires_at),
        "items": normalized,
    }
    lease_digest = _digest(digest_basis)
    metadata = {
        "schema": "pantheon/hermes-ephemeral-context-lease/v1",
        **digest_basis,
        "lease_digest": lease_digest,
        "created_by": actor,
        "state": "active",
    }

    final_dir = _lease_dir(root, lease_ref)
    temporary = root / f".tmp-{uuid.uuid4().hex}"
    temporary.mkdir(mode=0o700)
    try:
        for index, payload in enumerate(payloads):
            path = temporary / f"{index + 1:02d}.txt"
            path.write_bytes(payload)
            try:
                path.chmod(0o600)
            except OSError:
                pass
        metadata_file = temporary / "lease.json"
        metadata_file.write_text(
            json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        try:
            metadata_file.chmod(0o600)
        except OSError:
            pass
        os.replace(temporary, final_dir)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return _descriptor(metadata)


def _load_verified(
    *,
    lease_ref: str,
    expected_digest: str,
    root: Path | None = None,
    now: datetime | None = None,
) -> tuple[dict[str, Any], Path]:
    root = Path(root or default_root())
    expected_digest = _require_sha256(expected_digest, label="lease_digest")
    lease_dir = _lease_dir(root, lease_ref)
    metadata_path = lease_dir / "lease.json"
    if not metadata_path.is_file():
        raise EphemeralContextNotFound(f"ephemeral context lease is missing: {lease_ref}")
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EphemeralContextIntegrityError(
            f"ephemeral context lease metadata is unreadable: {lease_ref}"
        ) from exc
    if not isinstance(metadata, dict):
        raise EphemeralContextIntegrityError("ephemeral context lease metadata is invalid")
    if metadata.get("schema") != "pantheon/hermes-ephemeral-context-lease/v1":
        raise EphemeralContextIntegrityError("ephemeral context lease schema is invalid")
    if metadata.get("lease_ref") != lease_ref:
        raise EphemeralContextIntegrityError("ephemeral context lease identity changed")
    if metadata.get("state") != "active":
        raise EphemeralContextIntegrityError("ephemeral context lease is not active")
    basis = {
        "lease_ref": metadata.get("lease_ref"),
        "created_at": metadata.get("created_at"),
        "expires_at": metadata.get("expires_at"),
        "items": metadata.get("items"),
    }
    actual_lease_digest = _digest(basis)
    if metadata.get("lease_digest") != actual_lease_digest:
        raise EphemeralContextIntegrityError("ephemeral context lease metadata digest changed")
    if expected_digest != actual_lease_digest:
        raise EphemeralContextIntegrityError("ephemeral context lease digest does not match handoff basis")

    current = (now or _utcnow()).astimezone(timezone.utc)
    expires_at = _parse_time(metadata.get("expires_at"), label="expires_at")
    if expires_at <= current:
        raise EphemeralContextExpired(f"ephemeral context lease expired: {lease_ref}")

    items = metadata.get("items")
    if not isinstance(items, list) or not items or len(items) > MAX_LEASE_ITEMS:
        raise EphemeralContextIntegrityError("ephemeral context lease items are invalid")
    total = 0
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise EphemeralContextIntegrityError("ephemeral context lease item is invalid")
        payload_path = lease_dir / f"{index + 1:02d}.txt"
        try:
            payload = payload_path.read_bytes()
        except OSError as exc:
            raise EphemeralContextNotFound(
                f"ephemeral context payload is missing: {lease_ref}"
            ) from exc
        total += len(payload)
        if len(payload) != item.get("byte_size"):
            raise EphemeralContextIntegrityError("ephemeral context payload size changed")
        if _sha256_bytes(payload) != item.get("content_sha256"):
            raise EphemeralContextIntegrityError("ephemeral context payload digest changed")
        try:
            payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise EphemeralContextIntegrityError(
                "ephemeral context payload is no longer UTF-8"
            ) from exc
    if total > MAX_TOTAL_BYTES:
        raise EphemeralContextIntegrityError("ephemeral context lease exceeds bounded size")
    return metadata, lease_dir


def inspect_lease(
    *,
    lease_ref: str,
    expected_digest: str,
    root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    metadata, _ = _load_verified(
        lease_ref=lease_ref,
        expected_digest=expected_digest,
        root=root,
        now=now,
    )
    return _descriptor(metadata)


def materialize_lease(
    *,
    lease_ref: str,
    expected_digest: str,
    root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    metadata, lease_dir = _load_verified(
        lease_ref=lease_ref,
        expected_digest=expected_digest,
        root=root,
        now=now,
    )
    descriptor = _descriptor(metadata)
    materialized: list[dict[str, Any]] = []
    for index, item in enumerate(metadata["items"]):
        payload = (lease_dir / f"{index + 1:02d}.txt").read_bytes()
        materialized.append(
            {
                **descriptor["items"][index],
                "content_utf8": payload.decode("utf-8"),
            }
        )
    return {
        **descriptor,
        "items": materialized,
        "materialized": True,
        "source_admitted": False,
        "affaires_write_performed": False,
        "hindsight_write_performed": False,
        "evidence_admitted": False,
    }


def resolve_lease_refs(
    refs: list[dict[str, Any]] | None,
    *,
    root: Path | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    refs = refs or []
    if len(refs) > MAX_LEASE_ITEMS:
        raise EphemeralContextTooLarge(
            f"ephemeral_context_leases exceeds {MAX_LEASE_ITEMS} entries"
        )
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(refs):
        if not isinstance(raw, dict):
            raise EphemeralContextError(
                f"ephemeral_context_leases[{index}] must be an object"
            )
        lease_ref = str(raw.get("lease_ref") or "").strip()
        lease_digest = _require_sha256(
            raw.get("lease_digest"),
            label=f"ephemeral_context_leases[{index}].lease_digest",
        )
        if not lease_ref:
            raise EphemeralContextError(
                f"ephemeral_context_leases[{index}].lease_ref is required"
            )
        if lease_ref in seen:
            raise EphemeralContextError("ephemeral_context_leases contains a duplicate lease")
        seen.add(lease_ref)
        output.append(
            inspect_lease(
                lease_ref=lease_ref,
                expected_digest=lease_digest,
                root=root,
                now=now,
            )
        )
    return output


def validate_context_pack_leases(
    context_pack: dict[str, Any],
    *,
    root: Path | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    raw = context_pack.get("ephemeral_context_leases") or []
    refs = [
        {
            "lease_ref": item.get("lease_ref"),
            "lease_digest": item.get("lease_digest"),
        }
        for item in raw
        if isinstance(item, dict)
    ]
    if len(refs) != len(raw):
        raise EphemeralContextIntegrityError(
            "context pack contains malformed ephemeral context lease descriptors"
        )
    resolved = resolve_lease_refs(refs, root=root, now=now)
    if resolved != raw:
        raise EphemeralContextIntegrityError(
            "ephemeral context lease descriptor changed since handoff preview"
        )
    return resolved


def materialize_context_pack_leases(
    context_pack: dict[str, Any],
    *,
    root: Path | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    descriptors = validate_context_pack_leases(context_pack, root=root, now=now)
    return [
        materialize_lease(
            lease_ref=item["lease_ref"],
            expected_digest=item["lease_digest"],
            root=root,
            now=now,
        )
        for item in descriptors
    ]
