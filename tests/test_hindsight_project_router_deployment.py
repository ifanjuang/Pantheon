from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "deployment" / "ubuntu" / "configure-hindsight-project-router-local"
CORE = ROOT / "implementation" / "hermes" / "hindsight_project_router" / "hindsight_project_recall.py"
MCP = ROOT / "implementation" / "hermes" / "hindsight_project_router" / "hindsight_project_mcp.py"


def test_router_installer_is_loopback_authenticated_and_read_only() -> None:
    text = INSTALLER.read_text(encoding="utf-8")
    assert "127.0.0.1:8022" in text
    assert "HINDSIGHT_PROJECT_BANK_ID:-AGENCY_PROJECTS" in text
    assert "HINDSIGHT_PROJECT_SOURCE_KIND:-project-sync" in text
    assert "NoNewPrivileges=true" in text
    assert "ProtectSystem=strict" in text
    assert "--apply [--enable]" in text


def test_router_exposes_no_broad_or_write_tool() -> None:
    core = CORE.read_text(encoding="utf-8")
    mcp = MCP.read_text(encoding="utf-8")
    assert '"tags_match": "all_strict"' in core
    assert 'source_tag = f"source:{self.source_kind}"' in core
    assert "def project_scope_token(" in core
    assert 'scope_tag = f"scope:project:{project_scope}"' in core
    assert '"types": ["world", "experience"]' in core
    assert '"mode": "source-grounded-evidence"' in core
    assert "MAX_EVIDENCE_RESULTS = 8" in core
    assert "def recall_project_memory(" in mcp
    assert "retain" not in mcp
    assert "delete" not in mcp
