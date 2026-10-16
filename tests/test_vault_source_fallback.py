"""Synthetic regression for exact-source fallback across agency source families."""

from __future__ import annotations

import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "implementation/hermes/skills/vault-search/scripts"
sys.path.insert(0, str(SCRIPTS))

from vault_sources import VaultSourceError, VaultSources  # noqa: E402


@pytest.fixture()
def vaults(tmp_path: Path) -> tuple[VaultSources, dict[str, Path]]:
    affaires = tmp_path / "affaires"
    documentaires = tmp_path / "documentaires"
    alpha = affaires / "Project Alpha"
    beta = affaires / "Project Beta"
    cerfa = alpha / "Production" / "Permis" / "cerfa_project_alpha" / "cerfa_project_alpha.md"
    visit = beta / "PROJECT BETA VISIT.md"
    plui = beta / "Urbanisme" / "PLUi synthetic zone extract.md"
    maf = documentaires / "MAF" / "PERMIS" / "MAF_OUTILS_PERMIS.md"
    for path in (cerfa, visit, plui, maf):
        path.parent.mkdir(parents=True, exist_ok=True)
    cerfa.write_text("# Synthetic CERFA\nSurface déclarée : exemple fictif.\n", encoding="utf-8")
    visit.write_text("# Synthetic visit\nTerrain observé : exemple fictif.\n", encoding="utf-8")
    plui.write_text("# Zone UB1\nRègle à vérifier sur le projet.\n", encoding="utf-8")
    maf.write_text("# Outil MAF\nConseil général, sans fait de projet.\n", encoding="utf-8")
    return VaultSources(affaires, documentaires), {
        "cerfa": cerfa, "visit": visit, "plui": plui, "maf": maf,
    }


def test_project_is_resolved_before_permit_terms_and_beta_is_not_absent(vaults) -> None:
    reader, files = vaults
    found = reader.find_projects("Project Beta")
    assert found["items"] == [{
        "project_ref": "Project Beta", "name": "Project Beta", "match": "exact_name"
    }]
    inventory = reader.list_project_sources("Project Beta", "permis")
    paths = {item["source_path"] for item in inventory["items"]}
    assert paths == {str(files["visit"]), str(files["plui"])}
    assert {item["source_path"] for item in inventory["items"][:2]} == {
        str(files["visit"]), str(files["plui"])
    }
    assert inventory["path_match_is_content_support"] is False
    assert inventory["scan_complete"] is True
    assert inventory["logical_document_count_in_scanned_scope"] == 2
    assert inventory["returned_count"] == 2
    assert inventory["topic_path_match_count"] == 1
    assert str(files["cerfa"]) not in paths


def test_project_discovery_accepts_partial_and_bounded_typo_candidates(vaults) -> None:
    reader, _ = vaults
    assert reader.find_projects("Beta")["items"][0]["match"] == "partial_name"
    fuzzy = reader.find_projects("Projevt Beta")
    assert fuzzy["items"] == [{
        "project_ref": "Project Beta", "name": "Project Beta", "match": "fuzzy_name"
    }]
    assert fuzzy["identity_confirmed"] is False


def test_ocr_derivatives_are_one_logical_source_family(vaults) -> None:
    reader, files = vaults
    original = files["visit"].parent / "Site report.pdf"
    markdown = files["visit"].parent / "Site report.ocr.md"
    searchable = files["visit"].parent / "Site report.ocr.pdf"
    authored = files["visit"].parent / "Site report.md"
    original.write_bytes(b"%PDF-1.4 synthetic")
    markdown.write_text("OCR text", encoding="utf-8")
    searchable.write_bytes(b"%PDF-1.4 searchable synthetic")
    authored.write_text("Independent authored note", encoding="utf-8")

    inventory = reader.list_project_sources("Project Beta", "site report")
    family = next(
        item for item in inventory["items"]
        if item["logical_document_family"] == "Site report"
    )
    assert family["source_path"] == str(original)
    assert family["representation"] == "document_family"
    assert family["derivative_count"] == 2
    assert [row["kind"] for row in family["representations"]] == [
        "original_pdf", "ocr_markdown", "ocr_pdf"
    ]
    assert any(item["source_path"] == str(authored) for item in inventory["items"])
    assert sum("Site report.ocr" in item["source_path"] for item in inventory["items"]) == 0


def test_inventory_reports_counts_and_never_overstates_a_truncated_listing(vaults) -> None:
    reader, files = vaults
    for number in range(70):
        (files["visit"].parent / f"Document {number:02d}.pdf").write_bytes(b"%PDF-1.4 synthetic")

    inventory = reader.list_project_sources("Project Beta", max_items=5)

    assert inventory["scan_complete"] is True
    assert inventory["logical_document_count_in_scanned_scope"] == 72
    assert inventory["returned_count"] == 5
    assert inventory["truncated"] is True


def test_nested_alpha_cerfa_is_read_at_exact_lines_not_from_a_directory(vaults) -> None:
    reader, files = vaults
    inventory = reader.list_project_sources("Project Alpha", "permis CERFA")
    assert inventory["items"][0]["source_path"] == str(files["cerfa"])
    hit = reader.search_markdown(str(files["cerfa"]), "surface", "Project Alpha")
    assert hit["hits"][0]["line"] == 2
    assert hit["search_hit_is_source_inspection"] is False
    passage = reader.read_markdown_lines(str(files["cerfa"]), 2, 1, "Project Alpha")
    assert passage["lines"] == [{"line": 2, "text": "Surface déclarée : exemple fictif."}]
    assert passage["source_family"] == "projects"
    with pytest.raises(VaultSourceError, match="Markdown file"):
        reader.read_markdown_lines(str(files["cerfa"].parent), project_ref="Project Alpha")


def test_maf_stays_documentary_and_cross_project_reads_are_rejected(vaults) -> None:
    reader, files = vaults
    maf = reader.read_markdown_lines(str(files["maf"]))
    assert maf["source_family"] == "knowledge"
    assert maf["evidence_admitted"] is False
    with pytest.raises(VaultSourceError, match="must not be presented as a project"):
        reader.read_markdown_lines(str(files["maf"]), project_ref="Project Beta")
    with pytest.raises(VaultSourceError, match="does not belong"):
        reader.read_markdown_lines(str(files["cerfa"]), project_ref="Project Beta")
    with pytest.raises(VaultSourceError, match="does not belong"):
        reader.search_markdown(str(files["visit"]), "terrain", project_ref="Project Alpha")


def test_reader_rejects_escape_symlinks_and_unbounded_results(vaults, tmp_path: Path) -> None:
    reader, files = vaults
    outside = tmp_path / "outside.md"
    outside.write_text("private", encoding="utf-8")
    link = files["visit"].parent / "outside.md"
    link.symlink_to(outside)
    with pytest.raises(VaultSourceError, match="outside"):
        reader.read_markdown_lines(str(outside))
    with pytest.raises(VaultSourceError, match="not a directory or link"):
        reader.read_markdown_lines(str(link), project_ref="Project Beta")
    with pytest.raises(VaultSourceError, match="project_ref"):
        reader.list_project_sources("Project Beta/../Project Alpha")
    with pytest.raises(VaultSourceError, match="between 1 and"):
        reader.read_markdown_lines(str(files["visit"]), max_lines=1000,
                                   project_ref="Project Beta")

    redirected_root = tmp_path / "redirected-affaires"
    redirected_root.symlink_to(reader.projects_root, target_is_directory=True)
    with pytest.raises(VaultSourceError, match="source roots"):
        VaultSources(redirected_root, reader.knowledge_root)


def test_runtime_binding_is_explicitly_read_only_and_bounded() -> None:
    script = (SCRIPTS / "vault_mcp.py").read_text(encoding="utf-8")
    configure = (ROOT / "deployment/ubuntu/configure-hermes-activity-projection").read_text(
        encoding="utf-8"
    )
    for tool in (
        "find_vault_projects", "list_vault_project_sources",
        "search_vault_markdown", "read_vault_markdown_lines", "read_vault_pdf_figures",
    ):
        assert tool in script and tool in configure
    assert "read_only_hint=True" in script
    assert '"vault-read"' in configure
    assert '"prompts": false, "resources": false' in configure
    assert '"sampling": {"enabled": false}' in configure
    assert "--bind-local-mcp requires --with-vault-adapter" in configure
    assert 'VAULT_MCP_URL="http://127.0.0.1:8021/mcp"' in configure
    assert '"headers": {"Authorization": ("Bearer " + $vault_token)}' in configure


def test_local_service_keeps_vault_acl_off_hermes_and_authenticates_http() -> None:
    installer = (ROOT / "deployment/ubuntu/configure-vault-read-local").read_text(
        encoding="utf-8"
    )
    assert "User=pantheon-docling" in installer
    assert "Group=pantheon-docling" in installer
    assert "--apply --projects-root PATH --knowledge-root PATH [--enable]" in installer
    assert "--projects-root" in installer
    assert "PROJECTS_ROOT" in installer
    assert "--knowledge-root" in installer
    assert 'KNOWLEDGE_ROOT="${KNOWLEDGE_ROOT:-}"' in installer
    assert 'Environment=VAULT_KNOWLEDGE_ROOT=$KNOWLEDGE_ROOT' in installer
    assert 'ReadOnlyPaths=$PROJECTS_ROOT $KNOWLEDGE_ROOT $TOKEN_FILE' in installer
    assert 'RequiresMountsFor=$PROJECTS_ROOT $KNOWLEDGE_ROOT' in installer
    assert "/mnt/nas/BIBLIOTHEQUE" not in installer
    assert "/srv/pantheon/obsidian-affaires" not in installer
    assert "openssl rand -hex 32" in installer
    assert "ProtectSystem=strict" in installer
    assert "setfacl" not in installer
    assert '"127.0.0.1"' in (SCRIPTS / "vault_mcp.py").read_text(encoding="utf-8")


def test_http_guard_rejects_requests_without_the_service_token() -> None:
    pytest.importorskip("mcp")
    from vault_mcp import BearerGuard

    reached = []
    messages = []

    async def app(scope, receive, send):
        reached.append(scope["type"])

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    async def exercise():
        guard = BearerGuard(app, "a" * 32)
        await guard({"type": "http", "headers": []}, receive, send)
        assert messages[0]["status"] == 401
        assert not reached
        messages.clear()
        await guard({"type": "http", "headers": [(b"authorization", b"Bearer " + b"a" * 32)]},
                    receive, send)
        assert reached == ["http"]

    asyncio.run(exercise())


def test_mcp_registers_only_the_five_read_only_tools() -> None:
    pytest.importorskip("mcp")
    import vault_mcp

    tools = asyncio.run(vault_mcp.mcp.list_tools())
    assert {tool.name for tool in tools} == {
        "find_vault_projects", "list_vault_project_sources",
        "search_vault_markdown", "read_vault_markdown_lines", "read_vault_pdf_figures",
    }
    assert all(tool.annotations.read_only_hint is True for tool in tools)
    assert all(tool.annotations.destructive_hint is False for tool in tools)


def test_stdio_mcp_opens_only_the_selected_synthetic_project(vaults) -> None:
    pytest.importorskip("mcp")
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    reader, files = vaults
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(SCRIPTS / "vault_mcp.py")],
        env={
            **os.environ,
            "VAULT_PROJECTS_ROOT": str(reader.projects_root),
            "VAULT_KNOWLEDGE_ROOT": str(reader.knowledge_root),
        },
    )

    async def exercise() -> None:
        async with stdio_client(parameters) as (receive, send):
            async with ClientSession(receive, send) as session:
                await session.initialize()
                projects = await session.call_tool("find_vault_projects", {"designation": "Project Beta"})
                found = json.loads(projects.content[0].text)
                assert found["items"][0]["project_ref"] == "Project Beta"
                inventory = await session.call_tool("list_vault_project_sources", {
                    "project_ref": "Project Beta", "topic": "permis"
                })
                listed = json.loads(inventory.content[0].text)
                assert {item["source_path"] for item in listed["items"]} == {
                    str(files["visit"]), str(files["plui"])
                }
                crossing = await session.call_tool("read_vault_markdown_lines", {
                    "source_path": str(files["cerfa"]), "project_ref": "Project Beta"
                })
                assert json.loads(crossing.content[0].text)["status"] == "error"

    asyncio.run(exercise())


def test_authenticated_http_mcp_reads_beta_but_not_alpha(vaults, tmp_path: Path) -> None:
    pytest.importorskip("mcp")
    import httpx2 as httpx
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    reader, files = vaults
    token = "synthetic-test-token-0123456789abcdef"
    token_file = tmp_path / "token"
    token_file.write_text(token, encoding="ascii")
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    process = subprocess.Popen(
        [sys.executable, str(SCRIPTS / "vault_mcp.py"), "--http"],
        env={
            **os.environ,
            "VAULT_PROJECTS_ROOT": str(reader.projects_root),
            "VAULT_KNOWLEDGE_ROOT": str(reader.knowledge_root),
            "VAULT_TOKEN_FILE": str(token_file),
            "VAULT_MCP_PORT": str(port),
        },
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    url = f"http://127.0.0.1:{port}/mcp"
    try:
        for _ in range(100):
            if process.poll() is not None:
                pytest.fail(f"HTTP MCP exited: {process.stderr.read().decode(errors='replace')}")
            try:
                response = httpx.get(url, timeout=0.2)
                assert response.status_code == 401
                break
            except httpx.ConnectError:
                time.sleep(0.05)
        else:
            pytest.fail("HTTP MCP did not start on loopback")

        async def exercise() -> None:
            async with httpx.AsyncClient(headers={"Authorization": f"Bearer {token}"}) as client:
                async with streamable_http_client(url, http_client=client) as (receive, send):
                    async with ClientSession(receive, send) as session:
                        await session.initialize()
                        inventory = await session.call_tool("list_vault_project_sources", {
                            "project_ref": "Project Beta", "topic": "permis",
                        })
                        listed = json.loads(inventory.content[0].text)
                        assert {item["source_path"] for item in listed["items"]} == {
                            str(files["visit"]), str(files["plui"]),
                        }
                        crossing = await session.call_tool("read_vault_markdown_lines", {
                            "source_path": str(files["cerfa"]),
                            "project_ref": "Project Beta",
                        })
                        assert json.loads(crossing.content[0].text)["status"] == "error"

        asyncio.run(exercise())
    finally:
        process.terminate()
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=5)
