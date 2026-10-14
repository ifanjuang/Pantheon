"""Tests for the bounded Gmail/email action adapter."""

from __future__ import annotations

import base64
from email.message import EmailMessage
from email import policy
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mvp_vertical import (
    agency_data,
    email_action_adapter,
    hermes_ephemeral_context,
    source_intake,
    storage_retention,
)


def _encoded(message: EmailMessage) -> tuple[str, str]:
    raw = message.as_bytes(policy=policy.SMTP)
    encoded = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    return encoded, hashlib.sha256(raw).hexdigest()


def _message(
    *,
    subject: str = "Validation devis",
    body: str = "Bonjour,\nMerci de valider le devis.",
    thread_id: str = "thread-1",
    attachment: tuple[str, bytes] | None = None,
) -> email_action_adapter.NormalizedEmail:
    message = EmailMessage()
    message["From"] = "Alice <alice@example.test>"
    message["To"] = "Ifan <ifan@example.test>"
    message["Cc"] = "BET <bet@example.test>"
    message["Subject"] = subject
    message["Message-ID"] = "<message-1@example.test>"
    message["Date"] = "Fri, 09 Oct 2026 10:30:00 +0200"
    message.set_content(body)
    if attachment is not None:
        name, payload = attachment
        message.add_attachment(
            payload,
            maintype="application",
            subtype="pdf",
            filename=name,
        )
    encoded, digest = _encoded(message)
    return email_action_adapter.normalize_message(
        provider_account_ref="mailbox:agency",
        gmail_message_id=f"gmail-{thread_id}",
        gmail_thread_id=thread_id,
        raw_rfc822_base64url=encoded,
        client_raw_sha256=digest,
    )


def test_server_verifies_raw_digest_and_rejects_invalid_base64() -> None:
    message = EmailMessage()
    message["From"] = "alice@example.test"
    message["To"] = "ifan@example.test"
    message["Subject"] = "Test"
    message.set_content("Bonjour")
    encoded, digest = _encoded(message)

    normalized = email_action_adapter.normalize_message(
        provider_account_ref="mailbox:agency",
        gmail_message_id="msg-1",
        gmail_thread_id="thread-1",
        raw_rfc822_base64url=encoded,
        client_raw_sha256=digest,
    )
    assert normalized.raw_sha256 == digest
    assert normalized.raw_bytes
    assert normalized.body_text == "Bonjour"

    with pytest.raises(
        email_action_adapter.RawEmailChecksumMismatch,
        match="RAW SHA-256 mismatch",
    ):
        email_action_adapter.normalize_message(
            provider_account_ref="mailbox:agency",
            gmail_message_id="msg-1",
            gmail_thread_id="thread-1",
            raw_rfc822_base64url=encoded,
            client_raw_sha256="0" * 64,
        )

    with pytest.raises(email_action_adapter.RawEmailDecodeError):
        email_action_adapter.decode_raw_rfc822(
            "not*base64",
            client_raw_sha256=digest,
        )


def test_multipart_alternative_prefers_plain_and_attachment_digest_is_exact() -> None:
    message = EmailMessage()
    message["From"] = "Alice <alice@example.test>"
    message["To"] = "ifan@example.test"
    message["Subject"] = "Plans"
    message.set_content("Version texte prioritaire.")
    message.add_alternative(
        "<p>Version <b>HTML</b> secondaire.</p>",
        subtype="html",
    )
    payload = b"%PDF-synthetic-attachment"
    message.add_attachment(
        payload,
        maintype="application",
        subtype="pdf",
        filename="plan.pdf",
    )
    encoded, digest = _encoded(message)

    normalized = email_action_adapter.normalize_message(
        provider_account_ref="mailbox:agency",
        gmail_message_id="msg-plans",
        gmail_thread_id="thread-plans",
        raw_rfc822_base64url=encoded,
        client_raw_sha256=digest,
    )

    assert normalized.body_source_kind == "text/plain"
    assert normalized.body_text == "Version texte prioritaire."
    assert len(normalized.attachments) == 1
    attachment = normalized.attachments[0]
    assert attachment.visible_filename == "plan.pdf"
    assert attachment.decoded_bytes == payload
    assert attachment.content_sha256 == hashlib.sha256(payload).hexdigest()
    assert attachment.exact_decoded_bytes is True


def test_html_only_body_is_normalized_as_text_without_active_content() -> None:
    message = EmailMessage()
    message["From"] = "alice@example.test"
    message["To"] = "ifan@example.test"
    message["Subject"] = "HTML"
    message.set_content(
        "<div>Bonjour <b>Ifan</b></div><script>malicious()</script><p>Suite.</p>",
        subtype="html",
    )
    encoded, digest = _encoded(message)

    normalized = email_action_adapter.normalize_message(
        provider_account_ref="mailbox:agency",
        gmail_message_id="msg-html",
        gmail_thread_id="thread-html",
        raw_rfc822_base64url=encoded,
        client_raw_sha256=digest,
    )
    assert normalized.body_source_kind == "text/html"
    assert "Bonjour Ifan" in normalized.body_text
    assert "Suite." in normalized.body_text
    assert "malicious" not in normalized.body_text

    rendered = email_action_adapter.render_archive_html(
        normalized,
        document_id="mail-thread-html",
    )
    assert "<script>malicious" not in rendered
    assert "pantheon-email-provenance" in rendered
    assert normalized.raw_sha256 in rendered


def test_ask_lease_uses_existing_ephemeral_owner_and_provider_item_role(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("PANTHEON_EPHEMERAL_CONTEXT_ROOT", str(tmp_path))
    message = _message()

    lease = email_action_adapter.create_ask_lease(
        [message],
        actor="human:ifan",
        ttl_seconds=120,
    )

    assert lease["professional_persistence"] is False
    assert lease["items"][0]["role"] == "provider_item"
    assert lease["items"][0]["source_provenance"][0]["gmail_message_id"] == message.gmail_message_id
    assert "content_utf8" not in str(lease)

    materialized = hermes_ephemeral_context.materialize_lease(
        lease_ref=lease["lease_ref"],
        expected_digest=lease["lease_digest"],
        root=tmp_path,
    )
    text = materialized["items"][0]["content_utf8"]
    assert message.raw_sha256 in text
    assert message.gmail_thread_id in text
    assert "Validation devis" in text


def test_visible_archive_reuses_exact_attachment_and_updates_one_thread_html(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "VERGER"
    project_root.mkdir()
    first = _message(
        thread_id="thread-dedupe",
        attachment=("devis.pdf", b"same-pdf-bytes"),
    )

    initial = email_action_adapter.materialize_visible_archive(
        first,
        destination_root=project_root,
        document_id="mail-thread-dedupe",
    )
    assert initial["html_state"] == "created"
    assert initial["attachments_added"] == ["devis.pdf"]
    assert initial["attachments_reused"] == []
    assert initial["raw_retention_performed"] is False
    assert initial["source_admitted"] is False

    second = _message(
        subject="Re: Validation devis",
        body="Voici la même pièce jointe.",
        thread_id="thread-dedupe",
        attachment=("devis.pdf", b"same-pdf-bytes"),
    )
    updated = email_action_adapter.materialize_visible_archive(
        second,
        destination_root=project_root,
        document_id="mail-thread-dedupe",
    )
    assert updated["html_state"] == "updated"
    assert updated["attachments_added"] == []
    assert updated["attachments_reused"] == ["devis.pdf"]

    exchange = project_root / "Echanges"
    assert len(list(exchange.glob("*--thread-*.html"))) == 1
    assert (exchange / "devis.pdf").read_bytes() == b"same-pdf-bytes"


def test_same_filename_different_bytes_gets_hash_suffix_and_old_attachment_stays(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "VERGER"
    project_root.mkdir()

    first = _message(
        thread_id="thread-collision",
        attachment=("devis.pdf", b"version-one"),
    )
    email_action_adapter.materialize_visible_archive(
        first,
        destination_root=project_root,
        document_id="mail-thread-collision",
    )

    second = _message(
        thread_id="thread-collision",
        attachment=("devis.pdf", b"version-two"),
    )
    result = email_action_adapter.materialize_visible_archive(
        second,
        destination_root=project_root,
        document_id="mail-thread-collision",
    )

    digest = hashlib.sha256(b"version-two").hexdigest()
    expected = f"devis--{digest[:8]}.pdf"
    assert result["filename_collisions_disambiguated"] == [expected]
    assert (project_root / "Echanges" / "devis.pdf").read_bytes() == b"version-one"
    assert (project_root / "Echanges" / expected).read_bytes() == b"version-two"


def test_raw_email_retention_and_source_admission_do_not_create_project_identity(
    tmp_path: Path,
) -> None:
    try:
        conn = storage_retention.connect()
        conn.execute(agency_data.MIGRATION.read_text(encoding="utf-8"))
        conn.commit()
        source_intake.initialize(conn)
    except Exception as exc:  # pragma: no cover - local unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")

    conn.execute("BEGIN")
    try:
        message = _message(thread_id="thread-source")
        first = email_action_adapter.retain_and_admit_raw_email(
            conn,
            message,
            retention_root=tmp_path / "retention",
            storage_provider_ref="gmail-raw-retention",
            actor="ifan",
            received_at=datetime(2026, 10, 10, 10, 0, tzinfo=timezone.utc),
        )
        replay = email_action_adapter.retain_and_admit_raw_email(
            conn,
            message,
            retention_root=tmp_path / "retention",
            storage_provider_ref="gmail-raw-retention",
            actor="ifan",
            received_at=datetime(2026, 10, 10, 10, 0, tzinfo=timezone.utc),
        )

        source = first["source"]
        assert source["source_kind"] == "email"
        assert source["origin_system"] == "gmail"
        assert source["project_id"] is None
        assert source["declared_project_name"] is None
        assert source["checksum"] == message.raw_sha256
        assert source["raw_source_ref"].startswith("storage-object://")
        assert first["project_link_created"] is False
        assert first["storage_object"]["content_sha256"] == message.raw_sha256
        assert replay["source"]["source_id"] == source["source_id"]
    finally:
        conn.rollback()
        conn.close()


def test_archive_to_already_authorized_root_composes_existing_owners(
    tmp_path: Path,
) -> None:
    try:
        conn = storage_retention.connect()
        conn.execute(agency_data.MIGRATION.read_text(encoding="utf-8"))
        conn.commit()
        source_intake.initialize(conn)
    except Exception as exc:  # pragma: no cover - local unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")

    conn.execute("BEGIN")
    try:
        project_root = tmp_path / "AFFAIRES" / "VERGER"
        project_root.mkdir(parents=True)
        message = _message(
            thread_id="thread-full-archive",
            attachment=("devis.pdf", b"quote-bytes"),
        )
        result = email_action_adapter.archive_email_to_authorized_root(
            conn,
            message,
            destination_root=project_root,
            retention_root=tmp_path / "raw-retention",
            storage_provider_ref="gmail-raw-retention",
            actor="ifan",
            received_at=datetime(2026, 10, 10, 10, 0, tzinfo=timezone.utc),
        )

        assert result["intent"] == "ARCHIVE"
        assert result["raw_retention_performed"] is True
        assert result["source_admitted"] is True
        assert result["project_link_created"] is False
        assert result["hindsight_write_performed"] is False
        assert result["source"]["project_id"] is None
        assert result["storage_object"]["content_sha256"] == message.raw_sha256
        assert (
            project_root / result["visible_projection"]["html_relative_path"]
        ).is_file()
        assert (project_root / "Echanges" / "devis.pdf").read_bytes() == b"quote-bytes"
    finally:
        conn.rollback()
        conn.close()


def test_same_provider_message_identity_with_changed_raw_bytes_fails_closed(
    tmp_path: Path,
) -> None:
    try:
        conn = storage_retention.connect()
        conn.execute(agency_data.MIGRATION.read_text(encoding="utf-8"))
        conn.commit()
        source_intake.initialize(conn)
    except Exception as exc:  # pragma: no cover - local unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")

    conn.execute("BEGIN")
    try:
        first = _message(
            thread_id="thread-identity-conflict",
            body="Version A",
        )
        email_action_adapter.retain_and_admit_raw_email(
            conn,
            first,
            retention_root=tmp_path / "retention",
            storage_provider_ref="gmail-raw-retention",
            actor="ifan",
            received_at=datetime(2026, 10, 10, 10, 0, tzinfo=timezone.utc),
        )

        changed = _message(
            thread_id="thread-identity-conflict",
            body="Version B changed",
        )
        with pytest.raises(source_intake.SourceIntakeError):
            email_action_adapter.retain_and_admit_raw_email(
                conn,
                changed,
                retention_root=tmp_path / "retention",
                storage_provider_ref="gmail-raw-retention",
                actor="ifan",
                received_at=datetime(2026, 10, 10, 10, 0, tzinfo=timezone.utc),
            )
    finally:
        conn.rollback()
        conn.close()


def test_archive_destination_rejects_traversal(tmp_path: Path) -> None:
    root = tmp_path / "VERGER"
    root.mkdir()
    message = _message()

    with pytest.raises(
        email_action_adapter.UnsafeDestination,
        match="below destination_root",
    ):
        email_action_adapter.materialize_visible_archive(
            message,
            destination_root=root,
            relative_directory="../OTHER",
            document_id="mail-thread-1",
        )
