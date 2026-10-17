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
from mcp.server.mcpserver.utilities.types import Image
from mcp.types import ToolAnnotations

from vault_sources import VaultSourceError, VaultSources


mcp = MCPServer(
    "vault-read",
    instructions=(
        "Read-only agency vault mirror discovery. Paths are source leads, not project "
        "identity or Evidence. Search previews are not inspected passages; use "
        "read_vault_markdown_lines for line-located source content. read_vault_pdf_pages "
        "returns the text layer of a few pages of one exact PDF (a scan as an image); "
        "the separately admitted Docling binding converts whole documents and tables; "
        "read_vault_pdf_figures returns caption-located figure crops from one exact PDF."
    ),
)
READ_ONLY = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=False,
)
# Tools are registered with structured_output=False: they return JSON text, and a
# structured copy ({"result": <same text>}) would reach the model twice.


def _reply(method: Callable[[], dict]) -> str:
    try:
        return json.dumps(method(), ensure_ascii=False)
    except (VaultSourceError, OSError) as exc:
        return json.dumps({"status": "error", "reason": str(exc)}, ensure_ascii=False)


@mcp.tool(annotations=READ_ONLY, structured_output=False)
def find_vault_projects(designation: str, max_items: int = 12) -> str:
    """Find bounded project-directory candidates by explicit name; no identity admission.

    Only for a project, dossier or operation the question names. The knowledge
    library is not a project: a standard or reference question never calls this.
    """
    return _reply(lambda: VaultSources.from_environment().find_projects(designation, max_items))


@mcp.tool(annotations=READ_ONLY, structured_output=False)
def list_vault_project_sources(project_ref: str, topic: str = "", max_items: int = 30) -> str:
    """Inventory Markdown/PDF paths in one selected project; path matches are only leads.

    ``project_ref`` is a candidate returned by ``find_vault_projects``, never a guess.
    """
    return _reply(lambda: VaultSources.from_environment().list_project_sources(
        project_ref, topic, max_items
    ))


@mcp.tool(annotations=READ_ONLY, structured_output=False)
def search_vault_markdown(
    source_path: str, term: str, project_ref: str = "", max_hits: int = 8
) -> str:
    """Find line-numbered previews in one exact Markdown source, scoped to its family."""
    return _reply(lambda: VaultSources.from_environment().search_markdown(
        source_path, term, project_ref, max_hits
    ))


@mcp.tool(annotations=READ_ONLY, structured_output=False)
def read_vault_markdown_lines(
    source_path: str, start_line: int = 1, max_lines: int = 24, project_ref: str = ""
) -> str:
    """Read a bounded line-located passage from one exact Markdown source."""
    return _reply(lambda: VaultSources.from_environment().read_markdown_lines(
        source_path, start_line, max_lines, project_ref
    ))


@mcp.tool(annotations=READ_ONLY, structured_output=False)
def read_vault_pdf_figures(
    source_path: str, page: int = 0, text: str = "", project_ref: str = "", max_items: int = 3
) -> list:
    """Crop the figures of one exact PDF page with their captions, as images.

    source_path is the path as knowledge recall or the source inventory gives it
    (« DTU/guide.pdf » is read in the knowledge vault). Give the 1-based page, or
    a few words of the passage or caption to locate it.
    Compare each figure with the question before showing it; a figure without a
    caption, or one that does not match, is not shown. Never Evidence.
    """
    try:
        result, images = VaultSources.from_environment().pdf_figures(
            source_path, page, text, project_ref, max_items
        )
    except (VaultSourceError, OSError) as exc:
        return [json.dumps({"status": "error", "reason": str(exc)}, ensure_ascii=False)]
    return [json.dumps(result, ensure_ascii=False), *(Image(data=data, format="png") for data in images)]


@mcp.tool(annotations=READ_ONLY, structured_output=False)
def read_vault_pdf_pages(
    source_path: str, page: int = 0, text: str = "", project_ref: str = "", max_pages: int = 2
) -> list:
    """Read the text of one to three pages of an exact PDF, as the PDF stores it.

    Fast, no conversion or OCR: prefer it to a Docling conversion for a passage.
    source_path is the path as knowledge recall or the source inventory gives it.
    Give the 1-based page, or a few words to find the first pages containing them.
    A page without a text layer (a scan) is returned as an image to read instead.
    Each page carries its citation; the text is a source passage, never Evidence.
    """
    try:
        result, images = VaultSources.from_environment().pdf_pages(
            source_path, page, text, project_ref, max_pages
        )
    except (VaultSourceError, OSError) as exc:
        return [json.dumps({"status": "error", "reason": str(exc)}, ensure_ascii=False)]
    return [json.dumps(result, ensure_ascii=False), *(Image(data=data, format="png") for data in images)]


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
