"""Pantheon MCP tools return JSON text once, without a structured duplicate.

A tool annotated ``-> str`` gets an output schema ``{"result": string}`` by
default, so every call also carries ``structuredContent`` holding the same
text. Hermes forwards both, which doubled each result in a local model's
context window.
"""

from __future__ import annotations

import asyncio
import importlib.util
import os
from pathlib import Path
import sys
from unittest.mock import patch

import pytest

pytest.importorskip("mcp")  # the packaging job runs the suite without the MCP SDK


ROOT = Path(__file__).resolve().parents[1]
SERVERS = {
    "policy": ROOT / "mcp-server" / "pantheon_mcp" / "server.py",
    "hindsight-project": ROOT / "implementation" / "hermes" / "hindsight_project_router" / "hindsight_project_mcp.py",
    "hindsight-knowledge": ROOT / "implementation" / "hermes" / "hindsight_project_router" / "hindsight_project_mcp.py",
    "hindsight-vault": ROOT / "implementation" / "hermes" / "hindsight_project_router" / "hindsight_project_mcp.py",
    "vault-read": ROOT / "implementation" / "hermes" / "skills" / "vault-search" / "scripts" / "vault_mcp.py",
}


def _load(name: str, path: Path):
    if name == "policy":
        sys.path.insert(0, str(ROOT / "mcp-server"))
        from pantheon_mcp import server
        return server
    sys.path.insert(0, str(path.parent))
    env = {"HINDSIGHT_ROUTER_MODE": "knowledge" if name == "hindsight-knowledge" else "combined" if name == "hindsight-vault" else "project"}
    with patch.dict(os.environ, env):
        spec = importlib.util.spec_from_file_location(f"mcp_single_text_{name.replace('-', '_')}", path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("name", sorted(SERVERS))
def test_tools_declare_no_structured_output(name: str) -> None:
    tools = asyncio.run(_load(name, SERVERS[name]).mcp.list_tools())
    assert tools
    assert [tool.name for tool in tools if tool.output_schema is not None] == []


def test_combined_router_keeps_project_and_knowledge_clients_separate(monkeypatch) -> None:
    env = {
        "HINDSIGHT_ROUTER_MODE": "combined",
        "HINDSIGHT_PROJECT_BANK_ID": "PROJECTS",
        "HINDSIGHT_PROJECT_SOURCE_KIND": "kroqui-sync",
        "HINDSIGHT_KNOWLEDGE_BANK_ID": "KNOWLEDGE",
        "HINDSIGHT_KNOWLEDGE_SOURCE_KIND": "library-sync",
    }
    with patch.dict(os.environ, env):
        module = _load("hindsight-vault", SERVERS["hindsight-vault"])
        project = module._client("project")
        knowledge = module._client("knowledge")
        tools = asyncio.run(module.mcp.list_tools())
    assert project.bank_id == "PROJECTS"
    assert project.source_kind == "kroqui-sync"
    assert knowledge.bank_id == "KNOWLEDGE"
    assert knowledge.source_kind == "library-sync"
    assert {tool.name for tool in tools} == {
        "recall_project_memory", "hindsight_project_list", "hindsight_project_overview",
        "recall_knowledge_memory", "hindsight_knowledge_folders",
    }


def test_combined_router_fails_closed_without_each_producer_source_tag() -> None:
    env = {
        "HINDSIGHT_ROUTER_MODE": "combined",
        "HINDSIGHT_PROJECT_BANK_ID": "PROJECTS",
        "HINDSIGHT_KNOWLEDGE_BANK_ID": "KNOWLEDGE",
        "HINDSIGHT_URL": "http://127.0.0.1:8888",
    }
    with patch.dict(os.environ, env, clear=True):
        module = _load("hindsight-vault", SERVERS["hindsight-vault"])
        with pytest.raises(RuntimeError, match="distinct non-empty project and knowledge source kinds"):
            module._client("project")
