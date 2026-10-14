from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
from urllib.request import Request, urlopen
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "implementation" / "workspace_cockpit" / "memory_reconciliation.py"
PRODUCER_PATH = ROOT / "implementation" / "workspace_cockpit" / "hindsight_producer.py"
SERVER_PATH = ROOT / "implementation" / "workspace_cockpit" / "server.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _module():
    return _load(MODULE_PATH, "workspace_memory_reconciliation")


def _producer_module():
    return _load(PRODUCER_PATH, "workspace_hindsight_producer_reconcile_tests")


class _Response:
    def __init__(self, payload: dict, *, headers: dict[str, str] | None = None) -> None:
        self.payload = json.dumps(payload).encode("utf-8")
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


class _SseResponse:
    def __init__(self, payload: dict, *, session_id: str) -> None:
        event = json.dumps(
            {"type": "response.completed", "response": payload},
            ensure_ascii=False,
        ).encode("utf-8")
        self.stream = io.BytesIO(b"event: response.completed\n" + b"data: " + event + b"\n\n")
        self.headers = {"X-Hermes-Session-Id": session_id}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def readline(self):
        return self.stream.readline()


class _TimeoutSseResponse:
    def __init__(self, session_id: str) -> None:
        self.headers = {"X-Hermes-Session-Id": session_id}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def readline(self):
        raise TimeoutError("synthetic streaming timeout")


def test_hindsight_exact_read_contracts_are_document_scoped() -> None:
    producer = _producer_module()
    requests = []

    def fake_urlopen(request, timeout):
        requests.append((request, timeout))
        return _Response({"items": [], "total": 0, "limit": 100, "offset": 0})

    client = producer.HindsightHTTPClient(
        "http://127.0.0.1:8888",
        "AFFAIRES",
        authorization="Bearer test",
    )
    with patch.object(producer, "urlopen", fake_urlopen):
        client.get_document("doc-1:source")
        client.list_document_chunks("doc-1:source")
        client.list_memories("doc-1:source")

    urls = [request.full_url for request, _timeout in requests]
    assert urls[0].endswith("/v1/default/banks/AFFAIRES/documents/doc-1%3Asource")
    assert "/documents/doc-1%3Asource/chunks?" in urls[1]
    assert "limit=100" in urls[1]
    assert "/memories/list?" in urls[2]
    assert "document_id=doc-1%3Asource" in urls[2]
    assert all(request.get_header("Authorization") == "Bearer test" for request, _ in requests)


def _safe_toolsets() -> dict:
    return {
        "object": "list",
        "platform": "api_server",
        "data": [
            {"name": "file", "enabled": False, "configured": True, "tools": ["read_file"]},
            {"name": "memory", "enabled": False, "configured": True, "tools": ["memory_store"]},
        ],
    }


def _candidate_text() -> str:
    return json.dumps(
        {
            "summary": "Mémoire globalement cohérente.",
            "findings": [
                {
                    "category": "missing",
                    "summary": "Un détail manque",
                    "detail": "Le chunk c1 contient un détail absent de la mémoire.",
                    "memory_refs": ["m1"],
                    "chunk_refs": ["c1"],
                    "suggestion": "Conserver ce détail dans une mémoire plus précise.",
                }
            ],
        },
        ensure_ascii=False,
    )


def test_hermes_client_uses_no_store_then_deletes_session() -> None:
    module = _module()
    seen = []

    def fake_urlopen(request, timeout):
        seen.append(request)
        if request.full_url.endswith("/v1/toolsets"):
            return _Response(_safe_toolsets())
        if request.full_url.endswith("/v1/responses"):
            body = json.loads(request.data.decode("utf-8"))
            assert body["store"] is False
            assert body["stream"] is True
            assert "tools" not in body
            assert "model" not in body
            return _SseResponse(
                {
                    "output": [
                        {
                            "type": "message",
                            "content": [{"type": "output_text", "text": _candidate_text()}],
                        }
                    ]
                },
                session_id="session-123",
            )
        if request.full_url.endswith("/api/sessions/session-123"):
            assert request.get_method() == "DELETE"
            return _Response({"object": "hermes.session.deleted", "deleted": True})
        raise AssertionError(request.full_url)

    client = module.HermesReconciliationClient(
        "http://127.0.0.1:8642/p/reconciliation",
        "secret",
    )
    with patch.object(module, "urlopen", fake_urlopen):
        result = client.reconcile({"chunks": [], "memories": []})

    assert result.session_deleted is True
    assert result.candidate["findings"][0]["category"] == "missing"
    assert [request.get_method() for request in seen] == ["GET", "POST", "DELETE"]
    assert all(request.get_header("Authorization") == "Bearer secret" for request in seen)


def test_hermes_client_fails_closed_when_any_toolset_is_enabled() -> None:
    module = _module()
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(request.full_url)
        return _Response(
            {
                "object": "list",
                "platform": "api_server",
                "data": [{"name": "file", "enabled": True, "configured": True, "tools": ["read_file"]}],
            }
        )

    client = module.HermesReconciliationClient("http://127.0.0.1:8642/p/reconciliation", "secret")
    with patch.object(module, "urlopen", fake_urlopen):
        try:
            client.reconcile({})
        except module.ReconciliationError as exc:
            assert "exposes toolsets" in str(exc)
        else:
            raise AssertionError("enabled Hermes tools must block reconciliation")

    assert calls == ["http://127.0.0.1:8642/p/reconciliation/v1/toolsets"]


def test_invalid_hermes_output_still_deletes_transient_session() -> None:
    module = _module()
    methods = []

    def fake_urlopen(request, timeout):
        methods.append(request.get_method())
        if request.full_url.endswith("/v1/toolsets"):
            return _Response(_safe_toolsets())
        if request.full_url.endswith("/v1/responses"):
            return _SseResponse(
                {"output": [{"type": "message", "content": [{"type": "output_text", "text": "not-json"}]}]},
                session_id="session-bad",
            )
        if request.full_url.endswith("/api/sessions/session-bad"):
            return _Response({"object": "hermes.session.deleted", "deleted": True})
        raise AssertionError(request.full_url)

    client = module.HermesReconciliationClient("http://127.0.0.1:8642/p/reconciliation", "secret")
    with patch.object(module, "urlopen", fake_urlopen):
        try:
            client.reconcile({})
        except module.ReconciliationError as exc:
            assert "strict JSON" in str(exc)
        else:
            raise AssertionError("malformed model output must fail")

    assert methods == ["GET", "POST", "DELETE"]


def test_hermes_tool_call_output_is_rejected_and_session_is_deleted() -> None:
    module = _module()
    deleted = []

    def fake_urlopen(request, timeout):
        if request.full_url.endswith("/v1/toolsets"):
            return _Response(_safe_toolsets())
        if request.full_url.endswith("/v1/responses"):
            return _SseResponse(
                {
                    "output": [
                        {"type": "function_call", "name": "read_file", "call_id": "call-1", "arguments": "{}"},
                        {"type": "message", "content": [{"type": "output_text", "text": _candidate_text()}]},
                    ]
                },
                session_id="session-tool",
            )
        if request.full_url.endswith("/api/sessions/session-tool"):
            deleted.append(True)
            return _Response({"object": "hermes.session.deleted", "deleted": True})
        raise AssertionError(request.full_url)

    client = module.HermesReconciliationClient("http://127.0.0.1:8642/p/reconciliation", "secret")
    with patch.object(module, "urlopen", fake_urlopen):
        try:
            client.reconcile({})
        except module.ReconciliationError as exc:
            assert "attempted to use a tool" in str(exc)
        else:
            raise AssertionError("tool use must fail closed")

    assert deleted == [True]


def test_stream_timeout_deletes_session_known_from_early_headers() -> None:
    module = _module()
    methods = []

    def fake_urlopen(request, timeout):
        methods.append(request.get_method())
        if request.full_url.endswith("/v1/toolsets"):
            return _Response(_safe_toolsets())
        if request.full_url.endswith("/v1/responses"):
            return _TimeoutSseResponse("session-timeout")
        if request.full_url.endswith("/api/sessions/session-timeout"):
            return _Response({"object": "hermes.session.deleted", "deleted": True})
        raise AssertionError(request.full_url)

    client = module.HermesReconciliationClient(
        "http://127.0.0.1:8642/p/reconciliation", "secret"
    )
    with patch.object(module, "urlopen", fake_urlopen):
        try:
            client.reconcile({})
        except module.ReconciliationError as exc:
            assert "synthetic streaming timeout" in str(exc)
        else:
            raise AssertionError("stream timeout must fail")

    assert methods == ["GET", "POST", "DELETE"]


class _FakeHindsight:
    def get_document(self, document_id: str):
        return {
            "id": document_id,
            "content_hash": "hash-1",
            "memory_unit_count": 1,
            "nodes_by_fact_type": {"world": 1},
            "tags": ["workspace:affaires"],
            "original_text": "SECRET ORIGINAL TEXT MUST NOT LEAK",
            "document_metadata": {"source_path": "/mnt/NAS/AFFAIRES/secret.pdf"},
        }

    def list_document_chunks(self, document_id: str, *, limit: int, offset: int):
        return {
            "items": [
                {
                    "chunk_id": "c1",
                    "document_id": document_id,
                    "chunk_index": 0,
                    "chunk_text": "Contenu extrait du document.",
                    "attachments": [{"path": "/mnt/NAS/secret"}],
                }
            ],
            "total": 1,
            "limit": limit,
            "offset": offset,
        }

    def list_memories(self, document_id: str, *, limit: int, offset: int):
        return {
            "items": [
                {
                    "id": "m1",
                    "text": "Mémoire dérivée.",
                    "context": "Contexte dérivé.",
                    "document_id": document_id,
                    "chunk_id": "c1",
                    "metadata": {"source_path": "/mnt/NAS/secret.pdf"},
                    "state": "valid",
                }
            ],
            "total": 1,
            "limit": limit,
            "offset": offset,
        }


class _FakeHermes:
    def __init__(self):
        self.packet = None

    def reconcile(self, packet):
        self.packet = packet
        return SimpleNamespace(
            candidate={
                "summary": "Cohérent",
                "findings": [
                    {
                        "category": "organization",
                        "summary": "Organisation",
                        "detail": "Regrouper les faits.",
                        "suggestion": "Regroupement proposé.",
                        "memory_refs": ["m1"],
                        "chunk_refs": ["c1"],
                    }
                ],
            },
            session_deleted=True,
        )


def _snapshot() -> dict:
    return {
        "workspaces": [
            {
                "name": "Affaires",
                "cards": [
                    {
                        "workspace": "Affaires",
                        "kind": "document",
                        "status": "COMPLETE",
                        "document_id": "doc-1",
                        "title": "Notice",
                        "project": "Projet",
                        "phase": "DCE",
                        "document_type": "NOTICE",
                        "index": "C",
                        "document_date": "2026-09-01",
                        "issuer": "agency",
                        "revision_mode": None,
                        "revision_of": None,
                        "revision_target_status": "NONE",
                        "source_integrity": "UNDECLARED",
                        "tags": ["test"],
                        "summary": "Cartouche dérivé.",
                        "warnings": [],
                        "path": "PROJET/DCE/Notice.pdf",
                        "source": "Notice.pdf",
                        "hindsight_representation_candidate": "source",
                    }
                ],
            }
        ]
    }


def test_service_sends_only_bounded_hindsight_and_cartouche_projection() -> None:
    module = _module()
    hermes = _FakeHermes()
    service = module.MemoryReconciliationService(
        hindsight_client=_FakeHindsight(),
        hermes_client=hermes,
        max_context_chars=12000,
    )

    result = service.reconcile(_snapshot(), "doc-1", focus="Contradictions")

    encoded = json.dumps(hermes.packet, ensure_ascii=False)
    assert "SECRET ORIGINAL TEXT MUST NOT LEAK" not in encoded
    assert "/mnt/NAS" not in encoded
    assert "PROJET/DCE/Notice.pdf" not in encoded
    assert hermes.packet["source_access"] == "hindsight_only_no_nas_source"
    assert hermes.packet["chunks"][0]["chunk_id"] == "c1"
    assert hermes.packet["memories"][0]["id"] == "m1"
    assert result["kind"] == "memory_reconciliation_candidate"
    assert result["status"] == "candidate_only"
    assert result["inputs"]["exact_nas_source"] is False
    assert result["writes"] == {
        "hindsight": False,
        "workspace": False,
        "nas": False,
        "candidate_persisted": False,
    }


def test_service_rejects_reference_not_present_in_supplied_packet() -> None:
    module = _module()

    class BadHermes(_FakeHermes):
        def reconcile(self, packet):
            call = super().reconcile(packet)
            call.candidate["findings"][0]["chunk_refs"] = ["not-supplied"]
            return call

    service = module.MemoryReconciliationService(
        hindsight_client=_FakeHindsight(),
        hermes_client=BadHermes(),
    )
    try:
        service.reconcile(_snapshot(), "doc-1")
    except module.ReconciliationError as exc:
        assert "outside the supplied packet" in str(exc)
    else:
        raise AssertionError("out-of-packet reference must fail")


def test_service_rejects_non_complete_or_non_source_representation() -> None:
    module = _module()
    snapshot = _snapshot()
    snapshot["workspaces"][0]["cards"][0]["status"] = "CHECK"
    service = module.MemoryReconciliationService(
        hindsight_client=_FakeHindsight(),
        hermes_client=_FakeHermes(),
    )
    try:
        service.reconcile(snapshot, "doc-1")
    except module.ReconciliationError as exc:
        assert "COMPLETE" in str(exc)
    else:
        raise AssertionError("CHECK document must not reconcile")


def test_service_accepts_completed_eligible_technical_identity_without_cartouche() -> None:
    module = _module()
    snapshot = _snapshot()
    card = snapshot["workspaces"][0]["cards"][0]
    card.update(
        status="FOLDER_SCOPED",
        document_id=None,
        technical_document_id="doc-auto-1",
        hindsight_document_id="doc-auto-1:source",
        hindsight_eligible=True,
        hindsight_status="COMPLETED",
    )
    hermes = _FakeHermes()
    service = module.MemoryReconciliationService(
        hindsight_client=_FakeHindsight(),
        hermes_client=hermes,
    )

    result = service.reconcile(snapshot, "doc-auto-1", focus="Organisation")

    assert result["document_id"] == "doc-auto-1"
    assert result["hindsight_document_id"] == "doc-auto-1:source"
    assert hermes.packet["cartouche_projection"]["document_id"] == "doc-auto-1"


def test_cockpit_post_route_requires_explicit_intent_and_passes_only_document_id_focus() -> None:
    server_module = _load(SERVER_PATH, "workspace_cockpit_server_reconcile_route")

    class FakeIndex:
        def snapshot(self):
            return {"workspaces": []}

        def health(self):
            return {"mode": "test"}

    class FakeService:
        def __init__(self):
            self.calls = []

        def reconcile(self, snapshot, document_id, *, focus=""):
            self.calls.append((snapshot, document_id, focus))
            return {
                "kind": "memory_reconciliation_candidate",
                "status": "candidate_only",
                "document_id": document_id,
                "summary": "ok",
                "findings": [],
                "inputs": {"hindsight_chunks_sent": 0, "hindsight_memories_sent": 0},
            }

    service = FakeService()
    handler = server_module.CockpitHandler
    handler.workspace_index = FakeIndex()
    handler.memory_reconciliation = service
    httpd = server_module.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address

    try:
        body = json.dumps({"focus": "dates"}).encode("utf-8")
        missing_intent = Request(
            f"http://{host}:{port}/api/documents/doc-1/reconcile-memory",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(missing_intent, timeout=2)
        except Exception as exc:
            assert getattr(exc, "code", None) == 403
        else:
            raise AssertionError("explicit reconciliation intent header must be required")

        request = Request(
            f"http://{host}:{port}/api/documents/doc-1/reconcile-memory",
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Pantheon-Intent": "memory-reconcile",
            },
            method="POST",
        )
        with urlopen(request, timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload["kind"] == "memory_reconciliation_candidate"
        assert service.calls == [({"workspaces": []}, "doc-1", "dates")]
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)
        handler.memory_reconciliation = None
        handler.workspace_index = None
