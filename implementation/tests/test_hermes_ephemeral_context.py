from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from mvp_vertical import hermes_ephemeral_context as leases


NOW = datetime(2026, 9, 30, 1, 0, tzinfo=timezone.utc)


def _item(
    text: str = "MESSAGE=synthetic-1125",
    *,
    role: str = "provider_item",
) -> dict:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "content_utf8": text,
        "content_sha256": digest,
        "media_type": "text/plain; charset=utf-8",
        "representation_kind": "utf8_text",
        "role": role,
        "source_provenance": [
            {
                "provider": "synthetic",
                "source_id": "message-1125",
                "raw_sha256": "a" * 64,
            }
        ],
    }


def test_create_inspect_and_materialize_keep_payload_out_of_descriptor(
    tmp_path: Path,
) -> None:
    descriptor = leases.create_lease(
        items=[_item()],
        ttl_seconds=120,
        actor="human:test",
        root=tmp_path,
        now=NOW,
    )

    assert descriptor["lease_ref"].startswith("ephemeral-context-")
    assert len(descriptor["lease_digest"]) == 64
    assert descriptor["transient"] is True
    assert descriptor["professional_persistence"] is False
    assert "content_utf8" not in json.dumps(descriptor)

    inspected = leases.inspect_lease(
        lease_ref=descriptor["lease_ref"],
        expected_digest=descriptor["lease_digest"],
        root=tmp_path,
        now=NOW + timedelta(seconds=30),
    )
    assert inspected == descriptor

    materialized = leases.materialize_lease(
        lease_ref=descriptor["lease_ref"],
        expected_digest=descriptor["lease_digest"],
        root=tmp_path,
        now=NOW + timedelta(seconds=30),
    )
    assert materialized["items"][0]["content_utf8"] == "MESSAGE=synthetic-1125"
    assert materialized["source_admitted"] is False
    assert materialized["affaires_write_performed"] is False
    assert materialized["hindsight_write_performed"] is False
    assert materialized["evidence_admitted"] is False


def test_target_and_context_roles_are_bound_into_the_lease_digest(tmp_path: Path) -> None:
    target = leases.create_lease(
        items=[_item("same exact text", role="target")],
        ttl_seconds=120,
        actor="human:test",
        root=tmp_path / "target",
        now=NOW,
    )
    context = leases.create_lease(
        items=[_item("same exact text", role="context")],
        ttl_seconds=120,
        actor="human:test",
        root=tmp_path / "context",
        now=NOW,
    )

    assert target["items"][0]["role"] == "target"
    assert context["items"][0]["role"] == "context"
    assert target["items"][0]["content_sha256"] == context["items"][0]["content_sha256"]
    assert target["lease_digest"] != context["lease_digest"]


def test_invalid_item_role_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(
        leases.EphemeralContextError,
        match="role must be one of",
    ):
        leases.create_lease(
            items=[_item(role="write_target")],
            ttl_seconds=120,
            actor="human:test",
            root=tmp_path,
            now=NOW,
        )


def test_server_recomputes_content_digest_and_rejects_mismatch(tmp_path: Path) -> None:
    item = _item()
    item["content_sha256"] = "b" * 64

    with pytest.raises(
        leases.EphemeralContextIntegrityError,
        match="checksum mismatch",
    ):
        leases.create_lease(
            items=[item],
            ttl_seconds=120,
            actor="human:test",
            root=tmp_path,
            now=NOW,
        )

    assert list(tmp_path.glob("ephemeral-context-*")) == []


def test_expired_or_lost_lease_fails_closed(tmp_path: Path) -> None:
    descriptor = leases.create_lease(
        items=[_item()],
        ttl_seconds=60,
        actor="human:test",
        root=tmp_path,
        now=NOW,
    )
    lease_dir = tmp_path / descriptor["lease_ref"]

    with pytest.raises(
        leases.EphemeralContextExpired,
        match="expired",
    ):
        leases.inspect_lease(
            lease_ref=descriptor["lease_ref"],
            expected_digest=descriptor["lease_digest"],
            root=tmp_path,
            now=NOW + timedelta(seconds=61),
        )
    assert lease_dir.exists()

    removed = leases.cleanup_expired(
        root=tmp_path,
        now=NOW + timedelta(seconds=62),
    )
    assert removed == 1
    assert not lease_dir.exists()

    with pytest.raises(leases.EphemeralContextNotFound):
        leases.inspect_lease(
            lease_ref=descriptor["lease_ref"],
            expected_digest=descriptor["lease_digest"],
            root=tmp_path,
            now=NOW + timedelta(seconds=62),
        )


def test_payload_tampering_is_detected_before_materialization(tmp_path: Path) -> None:
    descriptor = leases.create_lease(
        items=[_item()],
        ttl_seconds=120,
        actor="human:test",
        root=tmp_path,
        now=NOW,
    )
    payload = tmp_path / descriptor["lease_ref"] / "01.txt"
    payload.write_text("changed", encoding="utf-8")

    with pytest.raises(
        leases.EphemeralContextIntegrityError,
        match="payload .* changed",
    ):
        leases.materialize_lease(
            lease_ref=descriptor["lease_ref"],
            expected_digest=descriptor["lease_digest"],
            root=tmp_path,
            now=NOW + timedelta(seconds=10),
        )


def test_provenance_rejects_credential_like_fields(tmp_path: Path) -> None:
    item = _item()
    item["source_provenance"] = [
        {
            "provider": "synthetic",
            "access_token": "must-not-persist",
        }
    ]

    with pytest.raises(
        leases.EphemeralContextError,
        match="credential-like",
    ):
        leases.create_lease(
            items=[item],
            ttl_seconds=120,
            actor="human:test",
            root=tmp_path,
            now=NOW,
        )


def test_context_pack_validation_binds_exact_descriptor(tmp_path: Path) -> None:
    descriptor = leases.create_lease(
        items=[_item("exact transient basis")],
        ttl_seconds=120,
        actor="human:test",
        root=tmp_path,
        now=NOW,
    )
    context_pack = {"ephemeral_context_leases": [descriptor]}

    resolved = leases.validate_context_pack_leases(
        context_pack,
        root=tmp_path,
        now=NOW + timedelta(seconds=5),
    )
    assert resolved == [descriptor]

    changed = json.loads(json.dumps(context_pack))
    changed["ephemeral_context_leases"][0]["items"][0]["media_type"] = "text/changed"
    with pytest.raises(
        leases.EphemeralContextIntegrityError,
        match="descriptor changed",
    ):
        leases.validate_context_pack_leases(
            changed,
            root=tmp_path,
            now=NOW + timedelta(seconds=5),
        )


def test_limits_are_enforced_without_creating_a_durable_store(tmp_path: Path) -> None:
    too_many = [_item(f"item-{index}") for index in range(leases.MAX_LEASE_ITEMS + 1)]
    with pytest.raises(leases.EphemeralContextTooLarge):
        leases.create_lease(
            items=too_many,
            ttl_seconds=120,
            actor="human:test",
            root=tmp_path,
            now=NOW,
        )

    with pytest.raises(leases.EphemeralContextError):
        leases.create_lease(
            items=[_item()],
            ttl_seconds=leases.MAX_TTL_SECONDS + 1,
            actor="human:test",
            root=tmp_path,
            now=NOW,
        )


def test_lazy_cleanup_removes_only_expired_leases(tmp_path: Path) -> None:
    expired = leases.create_lease(
        items=[_item("expired")],
        ttl_seconds=60,
        actor="human:test",
        root=tmp_path,
        now=NOW,
    )
    active = leases.create_lease(
        items=[_item("active")],
        ttl_seconds=120,
        actor="human:test",
        root=tmp_path,
        now=NOW + timedelta(seconds=30),
    )

    removed = leases.cleanup_expired(
        root=tmp_path,
        now=NOW + timedelta(seconds=61),
    )
    assert removed == 1
    assert not (tmp_path / expired["lease_ref"]).exists()
    assert (tmp_path / active["lease_ref"]).exists()
