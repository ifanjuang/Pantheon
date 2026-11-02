"""Cockpit discussions bound to one card, backed by a fake Hermes Sessions API."""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHAT = ROOT / "implementation" / "workspace_cockpit" / "hermes_workspace_chat.py"
SECRET = "sk-secret-prompt-and-tool-output"


def _module():
    spec = importlib.util.spec_from_file_location("hermes_workspace_chat", CHAT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeHermes:
    """Minimal Sessions API: create, rename, chat, read messages, delete."""

    def __init__(self) -> None:
        self.requests: list[tuple[str, str, dict]] = []
        self.sessions: dict[str, list[dict]] = {}
        self.fail_with_secret = False
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args) -> None:
                pass

            def _body(self) -> dict:
                length = int(self.headers.get("Content-Length") or 0)
                return json.loads(self.rfile.read(length) or b"{}") if length else {}

            def _reply(self, status: int, payload: dict | None = None, raw: bytes | None = None) -> None:
                data = raw if raw is not None else json.dumps(payload or {}).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _handle(self, method: str) -> None:
                body = self._body() if method in {"POST", "PATCH"} else {}
                fake.requests.append((method, self.path, body))
                if self.headers.get("Authorization") != "Bearer test-key":
                    return self._reply(401, {"error": "unauthorized"})
                if fake.fail_with_secret:
                    return self._reply(500, raw=SECRET.encode("utf-8"))
                parts = self.path.strip("/").split("/")
                if method == "POST" and self.path == "/api/sessions":
                    session_id = f"s-{len(fake.sessions) + 1}"
                    fake.sessions[session_id] = []
                    return self._reply(200, {"id": session_id})
                if len(parts) >= 3 and parts[:2] == ["api", "sessions"] and parts[2] in fake.sessions:
                    session_id = parts[2]
                    if method == "PATCH" and len(parts) == 3:
                        return self._reply(200, {"id": session_id})
                    if method == "POST" and parts[3:] == ["chat"]:
                        fake.sessions[session_id] += [
                            {"role": "user", "content": body.get("input", "")},
                            {"role": "assistant", "content": f"Réponse {len(fake.sessions[session_id]) // 2 + 1}"},
                        ]
                        return self._reply(200, {"ok": True})
                    if method == "GET" and parts[3:] == ["messages"]:
                        return self._reply(200, {"messages": fake.sessions[session_id]})
                    if method == "DELETE" and len(parts) == 3:
                        del fake.sessions[session_id]
                        return self._reply(200, {})
                return self._reply(404, {"error": "not found"})

            def do_GET(self) -> None:
                self._handle("GET")

            def do_POST(self) -> None:
                self._handle("POST")

            def do_PATCH(self) -> None:
                self._handle("PATCH")

            def do_DELETE(self) -> None:
                self._handle("DELETE")

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def hermes():
    fake = FakeHermes()
    try:
        yield fake
    finally:
        fake.close()


def _chat(module, hermes: FakeHermes, tmp_path: Path):
    return module.HermesWorkspaceChat(hermes.url, "test-key", tmp_path / "chat.sqlite3", timeout=10)


def test_one_card_keeps_several_discussions_bound_to_its_exact_path(hermes, tmp_path: Path) -> None:
    module = _module()
    chat = _chat(module, hermes, tmp_path)
    first, _ = chat.create_and_send("Affaires", "VERGER/Notice.pdf", "document", "Notice.pdf", "Lot menuiseries ?")
    second, messages = chat.create_and_send("Affaires", "VERGER/Notice.pdf", "document", "Notice.pdf", "Planning ?")
    other, _ = chat.create_and_send("Affaires", "VERGER", "folder", "VERGER", "Synthèse du dossier ?")

    assert first["session_id"] != second["session_id"]
    listed = chat.sessions_for_card("Affaires", "VERGER/Notice.pdf")
    assert {item["session_id"] for item in listed} == {first["session_id"], second["session_id"]}
    assert all(item["path"] == "VERGER/Notice.pdf" for item in listed)
    assert [item["session_id"] for item in chat.sessions_for_card("Affaires", "VERGER")] == [other["session_id"]]
    assert chat.sessions_for_card("Bibliotheque", "VERGER/Notice.pdf") == []
    assert messages[-1] == {"role": "assistant", "content": "Réponse 1", "created_at": None}
    # The exact card context travels with each turn sent to Hermes.
    chat_turns = [body for method, path, body in hermes.requests if method == "POST" and path.endswith("/chat")]
    assert all("VERGER" in body["input"] for body in chat_turns)


def test_archived_discussion_is_kept_refuses_replies_and_can_be_restored(hermes, tmp_path: Path) -> None:
    module = _module()
    chat = _chat(module, hermes, tmp_path)
    discussion, _ = chat.create_and_send("Affaires", "VERGER", "folder", "VERGER", "Premier échange")
    session_id = discussion["session_id"]

    assert chat.set_archived(session_id, True)["archived"] is True
    assert session_id in hermes.sessions  # archiving stays local to the Cockpit
    calls_before = len(hermes.requests)
    with pytest.raises(module.HermesChatError, match="archivée"):
        chat.send_message(session_id, "Encore une question")
    assert len(hermes.requests) == calls_before

    assert chat.set_archived(session_id, False)["archived"] is False
    updated, _ = chat.send_message(session_id, "Encore une question")
    assert updated["archived"] is False


def test_unknown_or_malformed_sessions_are_refused_without_calling_hermes(hermes, tmp_path: Path) -> None:
    module = _module()
    chat = _chat(module, hermes, tmp_path)
    hermes.sessions["s-foreign"] = []  # exists in Hermes, not created by this Cockpit
    for action in (
        lambda: chat.send_message("s-foreign", "question"),
        lambda: chat.set_archived("s-foreign", True),
        lambda: chat.delete("s-foreign"),
        lambda: chat.messages("../admin"),
    ):
        with pytest.raises(module.HermesChatError):
            action()
    assert hermes.requests == []
    assert "s-foreign" in hermes.sessions


def test_delete_removes_the_remote_session_and_the_card_binding(hermes, tmp_path: Path) -> None:
    module = _module()
    chat = _chat(module, hermes, tmp_path)
    keep, _ = chat.create_and_send("Affaires", "VERGER", "folder", "VERGER", "À garder")
    drop, _ = chat.create_and_send("Affaires", "VERGER", "folder", "VERGER", "À supprimer")

    chat.delete(drop["session_id"])
    assert drop["session_id"] not in hermes.sessions
    assert keep["session_id"] in hermes.sessions
    assert [item["session_id"] for item in chat.sessions_for_card("Affaires", "VERGER")] == [keep["session_id"]]


@pytest.mark.parametrize("message", ["", "   ", "x" * 8001])
def test_empty_or_oversized_messages_never_open_a_session(hermes, tmp_path: Path, message: str) -> None:
    module = _module()
    chat = _chat(module, hermes, tmp_path)
    with pytest.raises(module.HermesChatError, match="8 000"):
        chat.create_and_send("Affaires", "VERGER", "folder", "VERGER", message)
    assert hermes.requests == []
    assert chat.sessions_for_card("Affaires", "VERGER") == []


def test_hermes_errors_do_not_relay_upstream_content(hermes, tmp_path: Path) -> None:
    module = _module()
    chat = _chat(module, hermes, tmp_path)
    hermes.fail_with_secret = True
    with pytest.raises(module.HermesChatError) as caught:
        chat.create_and_send("Affaires", "VERGER", "folder", "VERGER", "question")
    assert SECRET not in str(caught.value)
    assert "500" in str(caught.value)


def test_cockpit_route_refuses_delete_without_explicit_confirmation() -> None:
    server = (ROOT / "implementation" / "workspace_cockpit" / "server.py").read_text(encoding="utf-8")
    route = server[server.index("def _hermes_chat_post"):]
    route = route[: route.index("\n    def ", 1)]
    assert 'body.get("confirm") is not True' in route
    assert "explicit_delete_confirmation_required" in route
    assert route.index('body.get("confirm") is not True') < route.index("self.hermes_chat.delete(")
    assert 'self.headers.get("X-Pantheon-Intent", "").strip() != "hermes-chat"' in server
