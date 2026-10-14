#!/usr/bin/env python3
"""Signed local receiver for Hindsight retain-completed enrichment work.

This receiver deliberately queues work only.  A webhook proves that a Hindsight
document has finished retaining; it does not prove that a date, a revision or a
project can safely be inferred.  No NAS path is opened or changed here.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sqlite3
from typing import Any


def _ensure_schema(state_db: Path) -> None:
    state_db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(state_db) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS hindsight_enrichment_queue (
                operation_id TEXT NOT NULL,
                document_id TEXT NOT NULL,
                bank_id TEXT NOT NULL,
                received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                memory_unit_count INTEGER,
                status TEXT NOT NULL DEFAULT 'queued',
                PRIMARY KEY(operation_id, document_id)
            )"""
        )


def _queue(state_db: Path, event: dict[str, Any], expected_bank: str) -> bool:
    if event.get("event") != "retain.completed" or event.get("status") != "completed":
        return False
    if event.get("bank_id") != expected_bank:
        return False
    operation_id = event.get("operation_id")
    data = event.get("data")
    if not isinstance(operation_id, str) or not operation_id or not isinstance(data, dict):
        return False
    document_id = data.get("document_id")
    if not isinstance(document_id, str) or not document_id:
        return False
    memory_unit_count = data.get("memory_unit_count")
    if not isinstance(memory_unit_count, int):
        memory_unit_count = None
    with sqlite3.connect(state_db) as conn:
        conn.execute(
            """INSERT OR IGNORE INTO hindsight_enrichment_queue
               (operation_id, document_id, bank_id, memory_unit_count)
               VALUES (?, ?, ?, ?)""",
            (operation_id, document_id, expected_bank, memory_unit_count),
        )
    return True


def _valid_signature(secret: str, body: bytes, header: str) -> bool:
    expected = "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.strip())


class HookHandler(BaseHTTPRequestHandler):
    secret = ""
    bank_id = ""
    state_db = Path("/tmp/hindsight-enrichment.sqlite3")

    def _reply(self, status: HTTPStatus, body: dict[str, Any]) -> None:
        encoded = json.dumps(body, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._reply(HTTPStatus.OK, {"status": "ok"})
        else:
            self._reply(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/hindsight/retain-completed":
            self._reply(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1
        if length < 2 or length > 65_536:
            self._reply(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "invalid_length"})
            return
        body = self.rfile.read(length)
        signature = self.headers.get("X-Hindsight-Signature", "")
        if self.headers.get("X-Hindsight-Event") != "retain.completed" or not _valid_signature(self.secret, body, signature):
            self._reply(HTTPStatus.UNAUTHORIZED, {"error": "invalid_signature"})
            return
        try:
            event = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._reply(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
            return
        if not isinstance(event, dict) or not _queue(self.state_db, event, self.bank_id):
            self._reply(HTTPStatus.ACCEPTED, {"accepted": False})
            return
        self._reply(HTTPStatus.ACCEPTED, {"accepted": True})

    def log_message(self, _format: str, *_args: Any) -> None:
        return


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8191)
    parser.add_argument("--state-db", default="/state/index.sqlite3")
    args = parser.parse_args()
    secret = os.getenv("HINDSIGHT_ENRICHMENT_HOOK_SECRET", "")
    bank_id = os.getenv("HINDSIGHT_ENRICHMENT_BANK_ID", "")
    if not secret or not bank_id:
        raise SystemExit("HINDSIGHT_ENRICHMENT_HOOK_SECRET and HINDSIGHT_ENRICHMENT_BANK_ID are required")
    HookHandler.secret, HookHandler.bank_id = secret, bank_id
    HookHandler.state_db = Path(args.state_db)
    _ensure_schema(HookHandler.state_db)
    ThreadingHTTPServer((args.host, args.port), HookHandler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
