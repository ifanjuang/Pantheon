#!/usr/bin/env python3
"""Authenticated loopback MCP exposing scoped, read-only Hindsight recall.

HINDSIGHT_ROUTER_MODE selects one surface per service instance:
``project`` (default) forces one exact project scope; ``knowledge`` serves the
knowledge vault (reference documents) restricted to its source tag, optionally narrowed to a folder.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
import sys

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from hindsight_project_recall import ProjectRecallClient, ProjectRecallError


MODE = os.environ.get("HINDSIGHT_ROUTER_MODE", "project").strip() or "project"
if MODE not in {"project", "knowledge"}:
    raise SystemExit("HINDSIGHT_ROUTER_MODE must be 'project' or 'knowledge'")

_SHARED_INSTRUCTIONS = (
    "It returns at most eight source-grounded world/experience facts, each carrying "
    "an exact document_id and chunk_id. Consolidated observations without "
    "provenance are not exposed. 'text' is a Hindsight summary, not a quotation; "
    "'quote' (when present) is the verbatim source passage, given once when facts "
    "share it; 'section' is the heading "
    "above it and 'citation' a ready reference. Quote only 'quote', cite only "
    "'citation', and never add an article, page or edition they do not contain. "
    "A row with representation 'text' is a raw passage of a document, given only as 'quote'. "
    "'present_in_documents' and 'also_in' mean the same passage appears in other documents "
    "(each is listed); nothing is dropped. 'labels' are descriptive facts read from the "
    "documents (indice, date_document, emetteur, destinataire, revision...): report them "
    "with the source they come from, never infer a version, a validity or a replacement from "
    "them, and never treat an index as ordering documents. A 'notice' qualifies a row "
    "(general conditions of a company are not a rule; an earlier-dated document of the same "
    "file-name family is shown after the most recent, which does not make it replaced): repeat it "
    "when you use the row. Set older_versions only when the user "
    "asks for earlier versions or what changed. "
    "This service cannot write to Hindsight."
)
if MODE == "project":
    mcp = MCPServer(
        "hindsight-project",
        instructions=(
            "Read-only project-platform Hindsight recall. Every request is forced into one exact "
            "project with source:project-sync and tags_match=all_strict. "
            + _SHARED_INSTRUCTIONS
            + " This service cannot perform bank-wide recall."
        ),
    )
else:
    mcp = MCPServer(
        "hindsight-knowledge",
        instructions=(
            "Read-only knowledge-vault Hindsight recall (standards, guides, insurer "
            "recommendations, glossaries). Every request is forced into the knowledge "
            "source tag with tags_match=all_strict and may be narrowed to one folder. "
            + _SHARED_INSTRUCTIONS
            + " Knowledge-vault content is transversal reference, never a project fact."
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
        os.environ.get("HINDSIGHT_PROJECT_BANK_ID", "PROJECTS"),
        source_kind=os.environ.get("HINDSIGHT_PROJECT_SOURCE_KIND", "project-sync"),
        authorization=os.environ.get("HINDSIGHT_PROJECT_AUTHORIZATION", ""),
        timeout_seconds=float(os.environ.get("HINDSIGHT_PROJECT_TIMEOUT_SECONDS", "45")),
    )


def recall_project_memory(
    project: str,
    query: str,
    folder: str = "",
    max_tokens: int = 2048,
    older_versions: bool = False,
) -> str:
    """Recall up to eight facts from one exact project.

    Put the resolved project hint or folder designation in ``project`` exactly
    (for example ``resolved-project-slug``); never put the generic word "project"
    there. Put the user's complete factual question and the designation in
    ``query``. Resolve a partial or ambiguous designation with
    ``vault-read:find_vault_projects`` before calling this tool. The most recent
    document of a family is presented first; set ``older_versions`` to true only when
    the user asks for earlier versions or what changed, to get them in relevance order.
    """
    try:
        payload = _client().recall_project(
            project, query, folder=folder, max_tokens=max_tokens, older_versions=older_versions
        )
    except (ProjectRecallError, OSError, ValueError) as exc:
        payload = {"status": "error", "reason": str(exc)}
    return json.dumps(payload, ensure_ascii=False)


def hindsight_project_list(limit: int = 100) -> str:
    """List indexed project scopes and memory counts; does not read documents.

    Call it only when the question names a project whose exact scope is unknown,
    never for a general reference question and never as a routine first step.
    """
    try:
        payload = _client().list_project_scopes(limit)
    except (ProjectRecallError, OSError, ValueError) as exc:
        payload = {"status": "error", "reason": str(exc)}
    return json.dumps(payload, ensure_ascii=False)


def recall_knowledge_memory(
    query: str, folder: str = "", max_tokens: int = 2048, older_versions: bool = False
) -> str:
    """Recall up to eight facts from the knowledge vault.

    Put the user's complete question in ``query``. Use ``folder`` only to narrow
    to one folder returned by ``hindsight_knowledge_folders`` (for example a
    standards or insurer folder); leave it empty to search the whole knowledge vault.
    A fact is a lead: open the document it cites, by the path it gives, rather than
    recalling again. Recall again only with terms the first results did not
    contain; after two recalls, say what was not found instead of rephrasing. An
    edition declared superseded is shown after the editions in force; set
    ``older_versions`` to true only when the user asks for earlier editions.
    """
    try:
        payload = _client().recall_knowledge(
            query, folder=folder, max_tokens=max_tokens, older_versions=older_versions
        )
    except (ProjectRecallError, OSError, ValueError) as exc:
        payload = {"status": "error", "reason": str(exc)}
    return json.dumps(payload, ensure_ascii=False)


def hindsight_knowledge_folders(limit: int = 100) -> str:
    """List indexed knowledge-vault folders and memory counts; does not read documents.

    Not needed before a first recall, which searches the whole knowledge vault:
    call it only to narrow a recall that missed to one folder.
    """
    try:
        payload = _client().list_knowledge_folders(limit)
    except (ProjectRecallError, OSError, ValueError) as exc:
        payload = {"status": "error", "reason": str(exc)}
    return json.dumps(payload, ensure_ascii=False)


TOOLS = {
    "project": (recall_project_memory, hindsight_project_list),
    "knowledge": (recall_knowledge_memory, hindsight_knowledge_folders),
}
for _tool in TOOLS[MODE]:
    # structured_output=False: the tools return JSON text; a structured copy
    # ({"result": <same text>}) would reach the model twice.
    mcp.tool(annotations=READ_ONLY, structured_output=False)(_tool)


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
