#!/usr/bin/env python3
"""Authenticated loopback MCP exposing only project-scoped project-platform recall."""

from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
import sys

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from hindsight_project_recall import ProjectRecallClient, ProjectRecallError


mcp = MCPServer(
    "hindsight-project",
    instructions=(
        "Read-only project-platform Hindsight recall. Every request is forced into one exact "
        "project with source:project-sync and tags_match=all_strict. It returns at "
        "most eight source-grounded world/experience facts, each carrying an exact "
        "document_id and chunk_id. Consolidated observations without provenance are "
        "not exposed. Verify material claims against the referenced document. This "
        "service cannot perform bank-wide recall."
    ),
)
READ_ONLY = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=False,
)


def _client() -> ProjectRecallClient:
    return ProjectRecallClient(
        os.environ.get("HINDSIGHT_PROJECT_URL", "http://127.0.0.1:8888"),
        os.environ.get("HINDSIGHT_PROJECT_BANK_ID", "AGENCY_PROJECTS"),
        source_kind=os.environ.get("HINDSIGHT_PROJECT_SOURCE_KIND", "project-sync"),
        authorization=os.environ.get("HINDSIGHT_PROJECT_AUTHORIZATION", ""),
        timeout_seconds=float(os.environ.get("HINDSIGHT_PROJECT_TIMEOUT_SECONDS", "45")),
    )


@mcp.tool(annotations=READ_ONLY)
def recall_project_memory(
    project: str,
    query: str,
    folder: str = "",
    max_tokens: int = 2048,
) -> str:
    """Recall up to eight facts from one exact project.

    Put the resolved project hint or folder designation in ``project`` exactly
    (for example ``resolved-project-slug``); never put the generic word "project"
    there. Put the user's complete factual question and the designation in
    ``query``. Resolve a partial or ambiguous designation with
    ``vault-read:find_vault_projects`` before calling this tool.
    """
    try:
        payload = _client().recall_project(
            project, query, folder=folder, max_tokens=max_tokens
        )
    except (ProjectRecallError, OSError, ValueError) as exc:
        payload = {"status": "error", "reason": str(exc)}
    return json.dumps(payload, ensure_ascii=False)


@mcp.tool(annotations=READ_ONLY)
def hindsight_project_list(limit: int = 100) -> str:
    """List indexed project scopes and memory counts; does not read documents."""
    try:
        payload = _client().list_project_scopes(limit)
    except (ProjectRecallError, OSError, ValueError) as exc:
        payload = {"status": "error", "reason": str(exc)}
    return json.dumps(payload, ensure_ascii=False)


class BearerGuard:
    def __init__(self, app, token: str):
        self.app = app
        self.expected = f"Bearer {token}".encode("ascii")

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            supplied = next(
                (value for name, value in scope.get("headers", []) if name.lower() == b"authorization"),
                b"",
            )
            if not secrets.compare_digest(supplied, self.expected):
                await send({"type": "http.response.start", "status": 401, "headers": []})
                await send({"type": "http.response.body", "body": b""})
                return
        await self.app(scope, receive, send)


def run_http() -> None:
    import uvicorn

    token_file = Path(os.environ.get(
        "HINDSIGHT_PROJECT_TOKEN_FILE",
        "/srv/pantheon/hindsight-project-router/token",
    ))
    token = token_file.read_text(encoding="ascii").strip()
    if len(token) < 32 or not token.isascii():
        raise RuntimeError("Hindsight project router token is missing or too short")
    app = BearerGuard(
        mcp.streamable_http_app(host="127.0.0.1", stateless_http=True), token
    )
    port = int(os.environ.get("HINDSIGHT_PROJECT_MCP_PORT", "8022"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--http":
        run_http()
    elif len(sys.argv) == 1:
        mcp.run()
    else:
        raise SystemExit("usage: hindsight_project_mcp.py [--http]")
