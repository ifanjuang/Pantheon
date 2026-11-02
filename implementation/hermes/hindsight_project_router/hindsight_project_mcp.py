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
if MODE not in {"project", "knowledge", "combined"}:
    raise SystemExit("HINDSIGHT_ROUTER_MODE must be 'project', 'knowledge' or 'combined'")

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
    "When metadata supplies OCR provenance (ocr_artifact_name or ocr_derived_from), "
    "workspace, pantheon_document_id and the raw-source checksum, "
    "reuse that retained OCR through vault-read:read_vault_ocr_markdown if a source "
    "check is needed. Its checksum must match the current source; do not OCR again "
    "while that matching derivative is available. The original source_path remains "
    "the authoritative file locator. Never construct a clickable link that was not returned. "
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
elif MODE == "knowledge":
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
else:
    mcp = MCPServer(
        "hindsight-vault",
        instructions=(
            "Read-only Hindsight retrieval over two strictly separate vaults. Use the project recall "
            "tools only for dossier-specific facts and require one exact project scope. Use the "
            "knowledge recall tools only for transversal standards, guides, regulatory sources and "
            "professional references; do not add a project scope there. Never combine the two banks "
            "implicitly: call both only when the user's question compares a project fact with a "
            "transversal rule, then report each source family separately. "
            + _SHARED_INSTRUCTIONS
            + " Project and knowledge banks have independent bank IDs and source tags."
        ),
    )
READ_ONLY = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=False,
)


def _client(vault: str = "project") -> ProjectRecallClient:
    if vault not in {"project", "knowledge"}:
        raise ValueError("vault must be project or knowledge")
    prefix = "HINDSIGHT_PROJECT" if vault == "project" else "HINDSIGHT_KNOWLEDGE"
    if MODE == "combined":
        project_bank = os.environ.get("HINDSIGHT_PROJECT_BANK_ID", "").strip()
        knowledge_bank = os.environ.get("HINDSIGHT_KNOWLEDGE_BANK_ID", "").strip()
        if not project_bank or not knowledge_bank:
            raise RuntimeError("both HINDSIGHT_PROJECT_BANK_ID and HINDSIGHT_KNOWLEDGE_BANK_ID are required in combined mode")
        if project_bank == knowledge_bank:
            raise RuntimeError("project and knowledge banks must be distinct in combined mode")
        project_source = os.environ.get("HINDSIGHT_PROJECT_SOURCE_KIND", "").strip()
        knowledge_source = os.environ.get("HINDSIGHT_KNOWLEDGE_SOURCE_KIND", "").strip()
        if not project_source or not knowledge_source or project_source == knowledge_source:
            raise RuntimeError("combined mode requires distinct non-empty project and knowledge source kinds")
        return ProjectRecallClient(
            os.environ.get(f"{prefix}_URL", os.environ.get("HINDSIGHT_URL", "http://127.0.0.1:8888")),
            project_bank if vault == "project" else knowledge_bank,
            source_kind=project_source if vault == "project" else knowledge_source,
            authorization=os.environ.get(f"{prefix}_AUTHORIZATION", os.environ.get("HINDSIGHT_AUTHORIZATION", "")),
            timeout_seconds=float(os.environ.get(f"{prefix}_TIMEOUT_SECONDS", "45")),
        )
    # Existing split-mode deployments use the established project-prefixed env vars.
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
        payload = _client("project").recall_project(
            project, query, folder=folder, max_tokens=max_tokens, older_versions=older_versions
        )
    except (ProjectRecallError, OSError, ValueError, RuntimeError) as exc:
        payload = {"status": "error", "reason": str(exc)}
    return json.dumps(payload, ensure_ascii=False)


def hindsight_project_list(limit: int = 100) -> str:
    """List indexed project scopes and memory counts; does not read documents.

    Call it only when the question names a project whose exact scope is unknown,
    never for a general reference question and never as a routine first step.
    """
    try:
        payload = _client("project").list_project_scopes(limit)
    except (ProjectRecallError, OSError, ValueError, RuntimeError) as exc:
        payload = {"status": "error", "reason": str(exc)}
    return json.dumps(payload, ensure_ascii=False)


def hindsight_project_overview(project: str) -> str:
    """Read the single Hindsight overview page scoped to one exact project.

    This is a concise orientation synthesis, not source evidence. The page must
    carry the exact scope:project tag derived from the confirmed project name.
    """
    try:
        payload = _client("project").project_overview(project)
    except (ProjectRecallError, OSError, ValueError, RuntimeError) as exc:
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
        payload = _client("knowledge").recall_knowledge(
            query, folder=folder, max_tokens=max_tokens, older_versions=older_versions
        )
    except (ProjectRecallError, OSError, ValueError, RuntimeError) as exc:
        payload = {"status": "error", "reason": str(exc)}
    return json.dumps(payload, ensure_ascii=False)


def hindsight_knowledge_folders(limit: int = 100) -> str:
    """List indexed knowledge-vault folders and memory counts; does not read documents.

    Not needed before a first recall, which searches the whole knowledge vault:
    call it only to narrow a recall that missed to one folder.
    """
    try:
        payload = _client("knowledge").list_knowledge_folders(limit)
    except (ProjectRecallError, OSError, ValueError, RuntimeError) as exc:
        payload = {"status": "error", "reason": str(exc)}
    return json.dumps(payload, ensure_ascii=False)


TOOLS = {
    "project": (recall_project_memory, hindsight_project_list, hindsight_project_overview),
    "knowledge": (recall_knowledge_memory, hindsight_knowledge_folders),
    "combined": (
        recall_project_memory,
        hindsight_project_list,
        hindsight_project_overview,
        recall_knowledge_memory,
        hindsight_knowledge_folders,
    ),
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
        "HINDSIGHT_VAULT_TOKEN_FILE" if MODE == "combined" else "HINDSIGHT_PROJECT_TOKEN_FILE",
        "/srv/pantheon/hindsight-vault-router/token" if MODE == "combined" else "/srv/pantheon/hindsight-project-router/token",
    ))
    token = token_file.read_text(encoding="ascii").strip()
    if len(token) < 32 or not token.isascii():
        raise RuntimeError("Hindsight router token is missing or too short")
    app = BearerGuard(
        mcp.streamable_http_app(host="127.0.0.1", stateless_http=True), token
    )
    port = int(os.environ.get(
        "HINDSIGHT_VAULT_MCP_PORT" if MODE == "combined" else "HINDSIGHT_PROJECT_MCP_PORT",
        "8024" if MODE == "combined" else "8022",
    ))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--http":
        run_http()
    elif len(sys.argv) == 1:
        mcp.run()
    else:
        raise SystemExit("usage: hindsight_project_mcp.py [--http]")
