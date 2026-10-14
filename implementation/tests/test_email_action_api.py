"""HTTP contract tests for the two-intent email action seam."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from email.message import EmailMessage
from email import policy
import hashlib
import json
from pathlib import Path
import sqlite3

from fastapi import FastAPI
from fastapi.testclient import TestClient

from mvp_vertical import email_action_adapter
from mvp_vertical.email_action_api import install_email_action_routes


def _raw_message() -> tuple[str, str]:
    message = EmailMessage()
    message["From"] = "Alice <alice@example.test>"
    message["To"] = "Ifan <ifan@example.test>"
    message["Subject"] = "Question chantier"
    message["Message-ID"] = "<msg@example.test>"
    message.set_content("Pouvez-vous vérifier ce point ?")
    raw = message.as_bytes(policy=policy.SMTP)
    return (
        base64.urlsafe_b64encode(raw).decode("ascii").rstrip("="),
        hashlib.sha256(raw).hexdigest(),
    )


def _message_body(*, destination_project: str | None = None) -> dict:
    encoded, digest = _raw_message()
    payload = {
        "provider_account_ref": "mailbox:agency",
        "gmail_message_id": "gmail-msg-1",
        "gmail_thread_id": "gmail-thread-1",
        "raw_rfc822_base64url": encoded,
        "client_raw_sha256": digest,
        "received_at": datetime(2026, 10, 10, 10, 0, tzinfo=timezone.utc).isoformat(),
    }
    if destination_project is not None:
        payload["destination_project"] = destination_project
    return payload


def _app(**kwargs) -> FastAPI:
    app = FastAPI()

    def with_connection(operation):
        return operation(object())

    def require_editor_key():
        return None

    def require_human_actor():
        return "ifan"

    install_email_action_routes(
        app,
        with_connection=with_connection,
        require_editor_key=require_editor_key,
        require_human_actor=require_human_actor,
        **kwargs,
    )
    return app


def _catalogue_db(path: Path, *, state: str = "active") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    project = {
        "name": "VERGER",
        "workspace": "Affaires" if state == "active" else "ArchivesProjet",
        "state": state,
        "root_kind": "AFFAIRES" if state == "active" else "ARCHIVES_PROJET",
        "relative_root": "VERGER",
        "available": True,
        "write_requires_confirmation": state == "archived",
        "routing_status": "valid",
        "automatic_routing_allowed": state == "active",
    }
    payload = {
        "read_only": True,
        "bounded": True,
        "limit": 10_000,
        "truncated": False,
        "project_count": 1,
        "conflict_count": 0,
        "projects": [project],
        "conflicts": [],
        "roots": [],
    }
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "CREATE TABLE workspace_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO workspace_meta(key, value) VALUES ('project_catalogue', ?)",
            (json.dumps(payload),),
        )
        connection.commit()
    finally:
        connection.close()


def test_ask_creates_lease_but_does_not_dispatch_without_governed_root(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("PANTHEON_EPHEMERAL_CONTEXT_ROOT", str(tmp_path / "leases"))
    client = TestClient(_app())

    response = client.post(
        "/cockpit/email-actions",
        json={
            "intent": "ASK_HERMES",
            "messages": [_message_body()],
            "question": "Est-ce cohérent ?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "ASK_HERMES"
    assert payload["archive_performed"] is False
    assert payload["handoff_status"] == "governed_root_required"
    assert payload["hermes_dispatched"] is False
    assert payload["lease"]["items"][0]["role"] == "provider_item"
    assert "content_utf8" not in response.text


def test_ask_with_explicit_governed_root_prepares_existing_handoff_request(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("PANTHEON_EPHEMERAL_CONTEXT_ROOT", str(tmp_path / "leases"))
    client = TestClient(_app())

    response = client.post(
        "/cockpit/email-actions",
        json={
            "intent": "ASK_HERMES",
            "messages": [_message_body()],
            "question": "Vérifie le contenu.",
            "hermes_root_entity": {
                "entity_id": "project:verger",
                "entity_type": "project",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["handoff_status"] == "preview_request_ready"
    request = payload["handoff_preview_request"]
    assert request["question"] == "Vérifie le contenu."
    assert request["card_context_envelope"]["root_entity"] == {
        "entity_id": "project:verger",
        "entity_type": "project",
    }
    assert request["ephemeral_context_leases"][0]["lease_ref"] == payload["lease"]["lease_ref"]
    assert payload["hermes_dispatched"] is False


def test_archive_uses_fresh_server_catalogue_and_never_accepts_client_path(
    monkeypatch,
    tmp_path: Path,
) -> None:
    state_db = tmp_path / "state.sqlite3"
    _catalogue_db(state_db)
    projects_root = tmp_path / "AFFAIRES"
    project_root = projects_root / "VERGER"
    project_root.mkdir(parents=True)
    observed: dict = {}

    def fake_archive(_conn, _message, **kwargs):
        observed.update(kwargs)
        return {
            "intent": "ARCHIVE",
            "document_id": "gmail-thread-test",
            "source": {"source_id": "gmail-email-test"},
            "storage_object": {"storage_object_id": "storage-test"},
            "visible_projection": {"html_state": "created"},
            "project_link_created": False,
            "raw_retention_performed": True,
            "source_admitted": True,
            "hindsight_write_performed": False,
        }

    monkeypatch.setattr(
        email_action_adapter,
        "archive_email_to_authorized_root",
        fake_archive,
    )
    client = TestClient(
        _app(
            project_catalogue_state_db=state_db,
            project_roots={"AFFAIRES": projects_root},
            raw_retention_root=tmp_path / "retention",
            raw_storage_provider_ref="gmail-retention",
        )
    )

    response = client.post(
        "/cockpit/email-actions",
        json={
            "intent": "ARCHIVE",
            "messages": [_message_body(destination_project="VERGER")],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert observed["destination_root"] == project_root.resolve()
    assert payload["destination"] == {
        "name": "VERGER",
        "state": "active",
        "root_kind": "AFFAIRES",
        "relative_root": "VERGER",
        "governed_project_identity_asserted": False,
    }

    forbidden = client.post(
        "/cockpit/email-actions",
        json={
            "intent": "ARCHIVE",
            "messages": [
                {
                    **_message_body(destination_project="VERGER"),
                    "destination_path": "/tmp/attacker-selected",
                }
            ],
        },
    )
    assert forbidden.status_code == 422


def test_archive_requires_server_configuration_and_one_message_per_request() -> None:
    client = TestClient(_app())

    unconfigured = client.post(
        "/cockpit/email-actions",
        json={
            "intent": "ARCHIVE",
            "messages": [_message_body(destination_project="VERGER")],
        },
    )
    assert unconfigured.status_code == 503

    multiple = client.post(
        "/cockpit/email-actions",
        json={
            "intent": "ARCHIVE",
            "messages": [
                _message_body(destination_project="VERGER"),
                {
                    **_message_body(destination_project="VERGER"),
                    "gmail_message_id": "gmail-msg-2",
                    "gmail_thread_id": "gmail-thread-2",
                },
            ],
        },
    )
    assert multiple.status_code == 422
