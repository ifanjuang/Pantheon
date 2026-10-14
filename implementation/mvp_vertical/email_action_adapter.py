"""Provider-neutral email action adapter for Pantheon Gmail/Workspace workflows.

This module owns email transport normalization only. It does not decide Project
identity, authorize filesystem destinations, admit Evidence, retain RAW bytes,
write Hindsight, or dispatch Hermes directly.

The caller must validate the destination before materialization. ASK_HERMES uses
the existing ephemeral-context lease owner and the existing handoff/execution
path; this module never introduces a second runtime route.
"""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from datetime import datetime, timezone
from email import policy
from email.message import EmailMessage, Message
from email.parser import BytesParser
from email.utils import parseaddr, parsedate_to_datetime
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

from . import hermes_ephemeral_context, source_intake, storage_retention


MAX_RAW_BYTES = 20 * 1024 * 1024
MAX_MIME_PARTS = 250
MAX_MIME_DEPTH = 12
MAX_ATTACHMENTS = 100
MAX_VISIBLE_FILES = 5_000
MAX_ATTACHMENT_BYTES = 18 * 1024 * 1024
MAX_TOTAL_ATTACHMENT_BYTES = 19 * 1024 * 1024
MAX_BODY_CHARS = 500_000
SAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9À-ÖØ-öø-ÿ._()\- ]+")
WHITESPACE = re.compile(r"[ \t\f\v]+")


class EmailActionError(ValueError):
    pass


class RawEmailDecodeError(EmailActionError):
    pass


class RawEmailChecksumMismatch(EmailActionError):
    pass


class EmailTooLarge(EmailActionError):
    pass


class MimeLimitExceeded(EmailActionError):
    pass


class UnsafeDestination(EmailActionError):
    pass


class ArchiveCollision(EmailActionError):
    pass


@dataclass(frozen=True, slots=True)
class Attachment:
    original_filename: str
    visible_filename: str
    media_type: str
    content_id: str | None
    disposition: str
    byte_size: int
    content_sha256: str | None
    decoded_bytes: bytes | None
    nested_message: bool
    exact_decoded_bytes: bool


@dataclass(frozen=True, slots=True)
class NormalizedEmail:
    provider_account_ref: str
    gmail_message_id: str
    gmail_thread_id: str
    rfc_message_id: str | None
    raw_sha256: str
    raw_size_bytes: int
    raw_bytes: bytes
    subject: str
    sender: str
    sender_address: str
    recipients_to: tuple[str, ...]
    recipients_cc: tuple[str, ...]
    message_date: str | None
    body_text: str
    body_source_kind: str
    attachments: tuple[Attachment, ...]
    mime_part_count: int


class _HTMLTextExtractor(HTMLParser):
    BLOCK_TAGS = {
        "address",
        "article",
        "aside",
        "blockquote",
        "br",
        "div",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "main",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "tr",
        "ul",
    }
    DROP_TAGS = {"script", "style", "noscript", "svg"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._drop_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.casefold()
        if normalized in self.DROP_TAGS:
            self._drop_depth += 1
            return
        if not self._drop_depth and normalized in self.BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.casefold()
        if normalized in self.DROP_TAGS and self._drop_depth:
            self._drop_depth -= 1
            return
        if not self._drop_depth and normalized in self.BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._drop_depth:
            self._chunks.append(data)

    def text(self) -> str:
        return _normalize_text("".join(self._chunks))


def _normalize_text(value: str) -> str:
    lines: list[str] = []
    blank = False
    for raw in value.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = WHITESPACE.sub(" ", raw).strip()
        if line:
            lines.append(line)
            blank = False
        elif lines and not blank:
            lines.append("")
            blank = True
    while lines and not lines[-1]:
        lines.pop()
    text = "\n".join(lines)
    if len(text) > MAX_BODY_CHARS:
        raise MimeLimitExceeded(f"normalized body exceeds {MAX_BODY_CHARS} characters")
    return text


def _html_to_text(value: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(value)
    parser.close()
    return parser.text()


def _header(message: Message, name: str) -> str:
    value = message.get(name)
    return str(value).strip() if value is not None else ""


def _addresses(message: Message, name: str) -> tuple[str, ...]:
    values = message.get_all(name, [])
    rendered: list[str] = []
    for value in values:
        text = str(value).strip()
        if text:
            rendered.append(text)
    return tuple(rendered)


def _safe_filename(value: str | None, *, fallback: str) -> str:
    name = Path(str(value or "")).name.replace("\x00", "").strip()
    if not name:
        name = fallback
    name = SAFE_FILENAME_CHARS.sub("_", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    if not name:
        name = fallback
    if len(name) > 180:
        stem = Path(name).stem[:130].rstrip(" .")
        suffix = Path(name).suffix[:20]
        name = f"{stem}{suffix}" if stem else fallback
    return name


def _decoded_attachment(part: Message) -> tuple[bytes | None, bool]:
    if part.get_content_type().casefold() == "message/rfc822":
        # The stdlib exposes a parsed nested Message, not the original decoded
        # MIME octets. Do not claim exact decoded bytes or materialize a rebuilt
        # .eml as if it were the original nested payload.
        return None, False
    try:
        payload = part.get_payload(decode=True)
    except (TypeError, ValueError):
        payload = None
    if payload is None:
        return b"", True
    return bytes(payload), True


def _part_text(part: Message) -> str:
    try:
        content = part.get_content()
    except (LookupError, UnicodeError, ValueError):
        payload = part.get_payload(decode=True) or b""
        charset = part.get_content_charset() or "utf-8"
        try:
            content = payload.decode(charset, errors="replace")
        except LookupError:
            content = payload.decode("utf-8", errors="replace")
    return str(content)


def _is_attachment(part: Message) -> bool:
    disposition = (part.get_content_disposition() or "").casefold()
    return disposition == "attachment" or bool(part.get_filename())


def _body_candidate(message: Message, *, depth: int = 0) -> tuple[str, str]:
    if depth > MAX_MIME_DEPTH:
        raise MimeLimitExceeded(f"MIME nesting exceeds {MAX_MIME_DEPTH}")
    content_type = message.get_content_type().casefold()

    if content_type == "message/rfc822":
        return "", "none"
    if not message.is_multipart():
        if _is_attachment(message):
            return "", "none"
        if content_type == "text/plain":
            return _normalize_text(_part_text(message)), "text/plain"
        if content_type == "text/html":
            return _html_to_text(_part_text(message)), "text/html"
        return "", "none"

    children = list(message.iter_parts())
    if content_type == "multipart/alternative":
        plain: tuple[str, str] | None = None
        html_candidate: tuple[str, str] | None = None
        for child in children:
            candidate = _body_candidate(child, depth=depth + 1)
            if not candidate[0]:
                continue
            if candidate[1] == "text/plain" and plain is None:
                plain = candidate
            elif candidate[1] == "text/html" and html_candidate is None:
                html_candidate = candidate
        return plain or html_candidate or ("", "none")

    for child in children:
        if _is_attachment(child):
            continue
        candidate = _body_candidate(child, depth=depth + 1)
        if candidate[0]:
            return candidate
    return "", "none"


def _walk_parts(message: Message, *, depth: int = 0) -> list[tuple[Message, int]]:
    if depth > MAX_MIME_DEPTH:
        raise MimeLimitExceeded(f"MIME nesting exceeds {MAX_MIME_DEPTH}")
    output: list[tuple[Message, int]] = [(message, depth)]
    if message.get_content_type().casefold() == "message/rfc822":
        return output
    if message.is_multipart():
        for child in message.iter_parts():
            output.extend(_walk_parts(child, depth=depth + 1))
            if len(output) > MAX_MIME_PARTS:
                raise MimeLimitExceeded(f"MIME part count exceeds {MAX_MIME_PARTS}")
    return output


def decode_raw_rfc822(
    raw_rfc822_base64url: str,
    *,
    client_raw_sha256: str,
) -> tuple[bytes, str]:
    encoded = str(raw_rfc822_base64url or "").strip()
    claimed = str(client_raw_sha256 or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", claimed):
        raise RawEmailDecodeError("client_raw_sha256 must be a lowercase SHA-256 digest")
    if not encoded:
        raise RawEmailDecodeError("raw_rfc822_base64url is required")
    try:
        ascii_payload = encoded.encode("ascii")
    except UnicodeEncodeError as exc:
        raise RawEmailDecodeError("raw_rfc822_base64url must be ASCII") from exc
    padding = b"=" * (-len(ascii_payload) % 4)
    try:
        raw = base64.b64decode(
            ascii_payload + padding,
            altchars=b"-_",
            validate=True,
        )
    except (binascii.Error, ValueError) as exc:
        raise RawEmailDecodeError("raw_rfc822_base64url is invalid") from exc
    if not raw:
        raise RawEmailDecodeError("decoded RFC822 message is empty")
    if len(raw) > MAX_RAW_BYTES:
        raise EmailTooLarge(f"decoded RFC822 message exceeds {MAX_RAW_BYTES} bytes")
    actual = hashlib.sha256(raw).hexdigest()
    if actual != claimed:
        raise RawEmailChecksumMismatch(
            f"RAW SHA-256 mismatch: client={claimed} server={actual}"
        )
    return raw, actual


def normalize_message(
    *,
    provider_account_ref: str,
    gmail_message_id: str,
    gmail_thread_id: str,
    raw_rfc822_base64url: str,
    client_raw_sha256: str,
) -> NormalizedEmail:
    for label, value in {
        "provider_account_ref": provider_account_ref,
        "gmail_message_id": gmail_message_id,
        "gmail_thread_id": gmail_thread_id,
    }.items():
        if not str(value or "").strip():
            raise EmailActionError(f"{label} is required")

    raw, digest = decode_raw_rfc822(
        raw_rfc822_base64url,
        client_raw_sha256=client_raw_sha256,
    )
    try:
        message = BytesParser(policy=policy.default).parsebytes(raw)
    except Exception as exc:
        raise RawEmailDecodeError("RFC822/MIME parsing failed") from exc

    parts = _walk_parts(message)
    if len(parts) > MAX_MIME_PARTS:
        raise MimeLimitExceeded(f"MIME part count exceeds {MAX_MIME_PARTS}")

    body_text, body_kind = _body_candidate(message)
    attachments: list[Attachment] = []
    total_attachment_bytes = 0

    for part, _depth in parts[1:]:
        content_type = part.get_content_type().casefold()
        nested = content_type == "message/rfc822"
        disposition = (part.get_content_disposition() or ("attachment" if nested else "inline")).casefold()
        filename = part.get_filename()
        content_id = _header(part, "Content-ID").strip("<>") or None
        should_capture = _is_attachment(part) or nested or (
            disposition == "inline" and content_id is not None and not content_type.startswith("text/")
        )
        if not should_capture:
            continue
        if len(attachments) >= MAX_ATTACHMENTS:
            raise MimeLimitExceeded(f"attachment count exceeds {MAX_ATTACHMENTS}")

        payload, exact = _decoded_attachment(part)
        size = len(payload) if payload is not None else 0
        if size > MAX_ATTACHMENT_BYTES:
            raise EmailTooLarge(f"attachment exceeds {MAX_ATTACHMENT_BYTES} bytes")
        total_attachment_bytes += size
        if total_attachment_bytes > MAX_TOTAL_ATTACHMENT_BYTES:
            raise EmailTooLarge(
                f"decoded attachments exceed {MAX_TOTAL_ATTACHMENT_BYTES} total bytes"
            )
        attachment_digest = hashlib.sha256(payload).hexdigest() if payload is not None else None
        fallback_suffix = ".eml" if nested else ""
        fallback = f"attachment-{len(attachments) + 1:02d}{fallback_suffix}"
        safe = _safe_filename(filename, fallback=fallback)
        attachments.append(
            Attachment(
                original_filename=str(filename or fallback),
                visible_filename=safe,
                media_type=content_type,
                content_id=content_id,
                disposition=disposition,
                byte_size=size,
                content_sha256=attachment_digest,
                decoded_bytes=payload,
                nested_message=nested,
                exact_decoded_bytes=exact,
            )
        )

    sender = _header(message, "From")
    sender_address = parseaddr(sender)[1]
    raw_date = _header(message, "Date")
    parsed_date: str | None = None
    if raw_date:
        try:
            dt = parsedate_to_datetime(raw_date)
            if dt is not None:
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                parsed_date = dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        except (TypeError, ValueError, OverflowError):
            parsed_date = None

    return NormalizedEmail(
        provider_account_ref=str(provider_account_ref).strip(),
        gmail_message_id=str(gmail_message_id).strip(),
        gmail_thread_id=str(gmail_thread_id).strip(),
        rfc_message_id=_header(message, "Message-ID") or None,
        raw_sha256=digest,
        raw_size_bytes=len(raw),
        raw_bytes=raw,
        subject=_header(message, "Subject"),
        sender=sender,
        sender_address=sender_address,
        recipients_to=_addresses(message, "To"),
        recipients_cc=_addresses(message, "Cc"),
        message_date=parsed_date,
        body_text=body_text,
        body_source_kind=body_kind,
        attachments=tuple(attachments),
        mime_part_count=len(parts),
    )


def _attachment_manifest(item: Attachment) -> dict[str, Any]:
    return {
        "original_filename": item.original_filename,
        "visible_filename": item.visible_filename,
        "media_type": item.media_type,
        "content_id": item.content_id,
        "disposition": item.disposition,
        "byte_size": item.byte_size,
        "content_sha256": item.content_sha256,
        "nested_message": item.nested_message,
        "exact_decoded_bytes": item.exact_decoded_bytes,
        "materializable": item.decoded_bytes is not None and item.exact_decoded_bytes,
    }


def normalized_context_text(message: NormalizedEmail) -> str:
    manifest = [_attachment_manifest(item) for item in message.attachments]
    fields = [
        f"From: {message.sender}",
        f"To: {', '.join(message.recipients_to)}",
    ]
    if message.recipients_cc:
        fields.append(f"Cc: {', '.join(message.recipients_cc)}")
    fields.extend(
        [
            f"Date: {message.message_date or ''}",
            f"Subject: {message.subject}",
            f"RFC-Message-ID: {message.rfc_message_id or ''}",
            f"Gmail-Message-ID: {message.gmail_message_id}",
            f"Gmail-Thread-ID: {message.gmail_thread_id}",
            f"RAW-SHA256: {message.raw_sha256}",
            "",
            message.body_text,
            "",
            "Attachments:",
            json.dumps(manifest, ensure_ascii=False, sort_keys=True),
        ]
    )
    return "\n".join(fields)


def create_ask_lease(
    messages: list[NormalizedEmail],
    *,
    actor: str,
    ttl_seconds: int = 900,
) -> dict[str, Any]:
    if not messages:
        raise EmailActionError("ASK_HERMES requires at least one current working email")
    items: list[dict[str, Any]] = []
    for message in messages:
        context = normalized_context_text(message)
        payload = context.encode("utf-8")
        items.append(
            {
                "content_utf8": context,
                "content_sha256": hashlib.sha256(payload).hexdigest(),
                "media_type": "text/plain; charset=utf-8",
                "representation_kind": hermes_ephemeral_context.REPRESENTATION_KIND,
                "role": "provider_item",
                "source_provenance": [
                    {
                        "provider": "gmail",
                        "provider_account_ref": message.provider_account_ref,
                        "gmail_message_id": message.gmail_message_id,
                        "gmail_thread_id": message.gmail_thread_id,
                        "raw_sha256": message.raw_sha256,
                        "rfc_message_id": message.rfc_message_id,
                    }
                ],
            }
        )
    return hermes_ephemeral_context.create_lease(
        items=items,
        ttl_seconds=ttl_seconds,
        actor=actor,
    )


def _provider_message_identity(message: NormalizedEmail) -> str:
    raw = (
        f"{message.provider_account_ref}\0{message.gmail_message_id}"
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def source_id_for_message(message: NormalizedEmail) -> str:
    return f"gmail-email-{_provider_message_identity(message)[:32]}"


def bundle_document_id_for_thread(message: NormalizedEmail) -> str:
    raw = (
        f"{message.provider_account_ref}\0{message.gmail_thread_id}"
    ).encode("utf-8")
    return f"gmail-thread-{hashlib.sha256(raw).hexdigest()[:32]}"


def retain_and_admit_raw_email(
    conn,
    message: NormalizedEmail,
    *,
    retention_root: Path,
    storage_provider_ref: str,
    actor: str,
    received_at: str | datetime,
) -> dict[str, Any]:
    """Retain exact RAW bytes then admit one provider-scoped email Source.

    The Source remains unlinked to any governed Project. A later visible
    AFFAIRES projection is routing/persistence, not Project identity.
    """

    retained = storage_retention.retain_exact_bytes(
        conn,
        content=message.raw_bytes,
        retention_root=retention_root,
        storage_provider_ref=storage_provider_ref,
        media_type="message/rfc822",
        expected_digest=message.raw_sha256,
    )
    storage_object = retained["storage_object"]
    source_id = source_id_for_message(message)
    origin_external_ref = (
        f"gmail-account:{message.provider_account_ref}:message:{message.gmail_message_id}"
    )
    identity_digest = _provider_message_identity(message)
    idempotency_key = (
        f"gmail-source-create-{identity_digest[:24]}-{message.raw_sha256[:24]}"
    )
    source = source_intake.create_source(
        conn,
        source_id=source_id,
        source_kind="email",
        origin_system="gmail",
        origin_external_ref=origin_external_ref,
        origin_producer="pantheon-workspace-addon",
        received_by=actor,
        raw_source_ref=f"storage-object://{storage_object['storage_object_id']}",
        received_at=received_at,
        actor=actor,
        actor_kind="human",
        idempotency_key=idempotency_key,
        declared_project_name=None,
        source_date=message.message_date,
        mime_type="message/rfc822",
        checksum=message.raw_sha256,
        metadata={
            "provider_account_ref": message.provider_account_ref,
            "gmail_message_id": message.gmail_message_id,
            "gmail_thread_id": message.gmail_thread_id,
            "rfc_message_id": message.rfc_message_id,
            "storage_object_id": storage_object["storage_object_id"],
            "raw_size_bytes": message.raw_size_bytes,
        },
    )
    return {
        "source": source,
        "storage_object": storage_object,
        "project_link_created": False,
        "visible_projection_written": False,
        "hindsight_write_performed": False,
    }


def render_archive_html(
    message: NormalizedEmail,
    *,
    document_id: str,
    attachment_paths: dict[str, str] | None = None,
) -> str:
    attachment_paths = attachment_paths or {}
    provenance = {
        "document_id": document_id,
        "provider_account_ref": message.provider_account_ref,
        "gmail_message_id": message.gmail_message_id,
        "gmail_thread_id": message.gmail_thread_id,
        "rfc_message_id": message.rfc_message_id,
        "server_verified_raw_sha256": message.raw_sha256,
        "raw_size_bytes": message.raw_size_bytes,
        "message_date": message.message_date,
        "body_source_kind": message.body_source_kind,
        "attachments": [_attachment_manifest(item) for item in message.attachments],
    }
    provenance_text = html.escape(
        json.dumps(provenance, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )
    rows = [
        ("De", message.sender),
        ("À", ", ".join(message.recipients_to)),
        ("Cc", ", ".join(message.recipients_cc)),
        ("Date", message.message_date or ""),
        ("Objet", message.subject),
        ("Message-ID", message.rfc_message_id or ""),
        ("Gmail message", message.gmail_message_id),
        ("Gmail thread", message.gmail_thread_id),
        ("SHA-256 RAW", message.raw_sha256),
    ]
    header_rows = "".join(
        f"<dt>{html.escape(label)}</dt><dd>{html.escape(value)}</dd>"
        for label, value in rows
        if value
    )
    attachment_items: list[str] = []
    for item in message.attachments:
        key = item.content_sha256 or f"nested:{item.original_filename}"
        visible = attachment_paths.get(key, item.visible_filename)
        label = html.escape(item.original_filename)
        if item.decoded_bytes is not None and item.exact_decoded_bytes:
            attachment_items.append(
                f'<li><a href="{html.escape(visible, quote=True)}">{label}</a>'
                f" <small>{html.escape(item.media_type)} · {item.byte_size} octets · "
                f"sha256:{html.escape(item.content_sha256 or '')}</small></li>"
            )
        else:
            attachment_items.append(
                f"<li>{label} <small>{html.escape(item.media_type)} · "
                "message imbriqué représenté mais non matérialisé comme octets exacts</small></li>"
            )
    attachments_html = (
        "<ul>" + "".join(attachment_items) + "</ul>"
        if attachment_items
        else "<p>Aucune pièce jointe.</p>"
    )
    body = html.escape(message.body_text).replace("\n", "<br>\n")
    return (
        "<!doctype html>\n"
        '<html lang="fr"><head><meta charset="utf-8">'
        "<title>" + html.escape(message.subject or "Courriel") + "</title>"
        '<meta name="pantheon-derived-representation" content="gmail-rfc822-html">'
        "</head><body>"
        "<main>"
        "<h1>" + html.escape(message.subject or "(sans objet)") + "</h1>"
        "<dl>" + header_rows + "</dl>"
        '<section aria-label="Corps du message"><p>' + body + "</p></section>"
        '<section aria-label="Pièces jointes"><h2>Pièces jointes</h2>'
        + attachments_html
        + "</section>"
        '<section aria-label="Provenance Pantheon"><h2>Provenance</h2>'
        '<pre id="pantheon-email-provenance">' + provenance_text + "</pre></section>"
        "</main></body></html>\n"
    )


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _existing_files_by_digest(destination: Path) -> tuple[dict[str, str], dict[str, str]]:
    by_digest: dict[str, str] = {}
    by_name: dict[str, str] = {}
    count = 0
    for entry in sorted(destination.iterdir(), key=lambda item: item.name.casefold()):
        if count >= MAX_VISIBLE_FILES:
            raise ArchiveCollision(
                f"destination contains more than {MAX_VISIBLE_FILES} visible files"
            )
        if entry.is_symlink() or not entry.is_file():
            continue
        count += 1
        digest = _file_sha256(entry)
        by_digest.setdefault(digest, entry.name)
        by_name[entry.name.casefold()] = digest
    return by_digest, by_name


def _collision_safe_name(
    desired: str,
    *,
    digest: str,
    by_name: dict[str, str],
) -> str:
    if desired.casefold() not in by_name:
        return desired
    if by_name[desired.casefold()] == digest:
        return desired
    path = Path(desired)
    stem = path.stem or "attachment"
    suffix = path.suffix
    for size in (8, 12, 16, 24, 32, 64):
        candidate = _safe_filename(
            f"{stem}--{digest[:size]}{suffix}",
            fallback=f"attachment--{digest[:size]}{suffix}",
        )
        current = by_name.get(candidate.casefold())
        if current is None or current == digest:
            return candidate
    raise ArchiveCollision("could not derive a collision-safe attachment filename")


def _atomic_write(path: Path, data: bytes) -> None:
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp: Path | None = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            raise ArchiveCollision(f"refusing to overwrite existing file: {path.name}")
        os.replace(tmp, path)
        tmp = None
    finally:
        if tmp is not None and tmp.exists():
            tmp.unlink()


def _thread_suffix(message: NormalizedEmail) -> str:
    raw = f"{message.provider_account_ref}\0{message.gmail_thread_id}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:12]


def _archive_html_name(message: NormalizedEmail) -> str:
    subject = _safe_filename(message.subject, fallback="Courriel")
    stem = Path(subject).stem[:90].rstrip(" .") or "Courriel"
    return f"{stem}--thread-{_thread_suffix(message)}.html"


def materialize_visible_archive(
    message: NormalizedEmail,
    *,
    destination_root: Path,
    relative_directory: str = "Echanges",
    document_id: str,
) -> dict[str, Any]:
    """Write the visible HTML + exact decoded attachments into an already-authorized root.

    This is not the RAW retention owner. The caller must retain exact RFC822 bytes
    separately before claiming a complete ARCHIVE effect.
    """

    root = destination_root.expanduser().resolve()
    if not root.is_dir():
        raise UnsafeDestination("destination_root must already exist as a directory")
    relative = Path(relative_directory or ".")
    if relative.is_absolute() or ".." in relative.parts:
        raise UnsafeDestination("relative_directory must remain below destination_root")
    candidate = root / relative
    if candidate.is_symlink():
        raise UnsafeDestination("archive destination may not be a symlink")
    destination = candidate.resolve(strict=False)
    if not destination.is_relative_to(root):
        raise UnsafeDestination("archive destination escaped destination_root")
    destination.mkdir(parents=True, exist_ok=True)

    by_digest, by_name = _existing_files_by_digest(destination)
    attachment_paths: dict[str, str] = {}
    added: list[str] = []
    reused: list[str] = []
    collisions: list[str] = []

    for item in message.attachments:
        if item.decoded_bytes is None or not item.exact_decoded_bytes or not item.content_sha256:
            continue
        digest = item.content_sha256
        existing = by_digest.get(digest)
        if existing:
            attachment_paths[digest] = existing
            reused.append(existing)
            continue
        name = _collision_safe_name(
            item.visible_filename,
            digest=digest,
            by_name=by_name,
        )
        if name != item.visible_filename:
            collisions.append(name)
        path = destination / name
        _atomic_write(path, item.decoded_bytes)
        by_digest[digest] = name
        by_name[name.casefold()] = digest
        attachment_paths[digest] = name
        added.append(name)

    suffix = f"--thread-{_thread_suffix(message)}.html"
    existing_html = [
        item
        for item in destination.iterdir()
        if item.is_file() and not item.is_symlink() and item.name.endswith(suffix)
    ]
    if len(existing_html) > 1:
        raise ArchiveCollision("multiple current HTML projections exist for one Gmail thread")
    html_name = existing_html[0].name if existing_html else _archive_html_name(message)
    html_path = destination / html_name
    rendered = render_archive_html(
        message,
        document_id=document_id,
        attachment_paths=attachment_paths,
    ).encode("utf-8")

    if html_path.exists():
        fd, tmp_name = tempfile.mkstemp(prefix=f".{html_name}.", suffix=".tmp", dir=destination)
        tmp: Path | None = Path(tmp_name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(rendered)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, html_path)
            tmp = None
        finally:
            if tmp is not None and tmp.exists():
                tmp.unlink()
        html_state = "updated"
    else:
        _atomic_write(html_path, rendered)
        html_state = "created"

    return {
        "document_id": document_id,
        "html_relative_path": str(html_path.relative_to(root)),
        "html_state": html_state,
        "attachments_added": added,
        "attachments_reused": reused,
        "filename_collisions_disambiguated": collisions,
        "raw_retention_performed": False,
        "source_admitted": False,
        "hindsight_write_performed": False,
    }



def archive_email_to_authorized_root(
    conn,
    message: NormalizedEmail,
    *,
    destination_root: Path,
    retention_root: Path,
    storage_provider_ref: str,
    actor: str,
    received_at: str | datetime,
    relative_directory: str = "Echanges",
) -> dict[str, Any]:
    """Archive one email after a separate caller has authorized the root.

    RAW retention and Source admission happen before the visible projection.
    The standalone workspace producer remains responsible for later filesystem
    observation/Hindsight production.
    """

    raw = retain_and_admit_raw_email(
        conn,
        message,
        retention_root=retention_root,
        storage_provider_ref=storage_provider_ref,
        actor=actor,
        received_at=received_at,
    )
    document_id = bundle_document_id_for_thread(message)
    visible = materialize_visible_archive(
        message,
        destination_root=destination_root,
        relative_directory=relative_directory,
        document_id=document_id,
    )
    return {
        "intent": "ARCHIVE",
        "document_id": document_id,
        "source": raw["source"],
        "storage_object": raw["storage_object"],
        "visible_projection": visible,
        "project_link_created": False,
        "raw_retention_performed": True,
        "source_admitted": True,
        "hindsight_write_performed": False,
    }
