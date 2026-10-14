#!/usr/bin/env python3
"""Read-only MCP binding for bounded agency project discovery and Markdown reads."""

from __future__ import annotations

import json
import os
import secrets
import sys
from pathlib import Path
from typing import Callable

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from vault_sources import VaultSourceError, VaultSources


mcp = MCPServer(
    "vault-read",
    instructions=(
        "Read-only agency vault mirror discovery. Paths are source leads, not project "
        "identity or Evidence. Search previews are not inspected passages; use "
        "read_vault_markdown_lines for line-located source content. PDFs require "
        "the separately admitted Docling binding."
    ),
)
READ_ONLY = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=False,
)


def _reply(method: Callable[[], dict]) -> str:
    try:
        return json.dumps(method(), ensure_ascii=False)
    except (VaultSourceError, OSError) as exc:
        return json.dumps({"status": "error", "reason": str(exc)}, ensure_ascii=False)


@mcp.tool(annotations=READ_ONLY)
def find_vault_projects(designation: str, max_items: int = 12) -> str:
    """Find bounded project-directory candidates by explicit name; no identity admission."""
    return _reply(lambda: VaultSources.from_environment().find_projects(designation, max_items))


@mcp.tool(annotations=READ_ONLY)
def list_vault_project_sources(project_ref: str, topic: str = "", max_items: int = 30) -> str:
    """Inventory Markdown/PDF paths in one selected project; path matches are only leads."""
    return _reply(lambda: VaultSources.from_environment().list_project_sources(
        project_ref, topic, max_items
    ))


@mcp.tool(annotations=READ_ONLY)
def search_vault_markdown(
    source_path: str, term: str, project_ref: str = "", max_hits: int = 8
) -> str:
    """Find line-numbered previews in one exact Markdown source, scoped to its family."""
    return _reply(lambda: VaultSources.from_environment().search_markdown(
        source_path, term, project_ref, max_hits
    ))


@mcp.tool(annotations=READ_ONLY)
def read_vault_markdown_lines(
    source_path: str, start_line: int = 1, max_lines: int = 24, project_ref: str = ""
) -> str:
    """Read a bounded line-located passage from one exact Markdown source."""
    return _reply(lambda: VaultSources.from_environment().read_markdown_lines(
        source_path, start_line, max_lines, project_ref
    ))


class BearerGuard:
    """Require the node-local bearer token before any HTTP MCP request."""

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
        "VAULT_TOKEN_FILE", "/etc/pantheon-node/vault-read.token"
    ))
    token = token_file.read_text(encoding="ascii").strip()
    if len(token) < 32 or not token.isascii():
        raise RuntimeError("agency vault reader token is missing or too short")
    app = BearerGuard(mcp.streamable_http_app(host="127.0.0.1"), token)
    port = int(os.environ.get("VAULT_MCP_PORT", "8021"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--http":
        run_http()
    elif len(sys.argv) == 1:
        mcp.run()
    else:
        raise SystemExit("usage: vault_mcp.py [--http]")
