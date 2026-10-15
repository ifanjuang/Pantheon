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
    "vault-read": ROOT / "implementation" / "hermes" / "skills" / "vault-search" / "scripts" / "vault_mcp.py",
}


def _load(name: str, path: Path):
    if name == "policy":
        sys.path.insert(0, str(ROOT / "mcp-server"))
        from pantheon_mcp import server
        return server
    sys.path.insert(0, str(path.parent))
    env = {"HINDSIGHT_ROUTER_MODE": "knowledge" if name == "hindsight-knowledge" else "project"}
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
