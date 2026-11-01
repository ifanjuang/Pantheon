import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "deployment" / "ubuntu" / "configure-hindsight-project-router-local"
CORE = ROOT / "implementation" / "hermes" / "hindsight_project_router" / "hindsight_project_recall.py"
MCP = ROOT / "implementation" / "hermes" / "hindsight_project_router" / "hindsight_project_mcp.py"


def test_router_installer_is_loopback_authenticated_and_read_only() -> None:
    text = INSTALLER.read_text(encoding="utf-8")
    assert "PORT=8022" in text
    assert "127.0.0.1:$PORT" in text
    assert "HINDSIGHT_PROJECT_BANK_ID:-PROJECTS" in text
    assert "HINDSIGHT_PROJECT_SOURCE_KIND:-project-sync" in text
    assert "NoNewPrivileges=true" in text
    assert "ProtectSystem=strict" in text
    assert "--apply [--enable]" in text


def test_knowledge_instance_is_separate_and_bound_by_deployment_values() -> None:
    text = INSTALLER.read_text(encoding="utf-8")
    assert "--knowledge) MODE=\"knowledge\"" in text
    assert 'INSTANCE="pantheon-hindsight-knowledge-router"' in text
    assert 'STATE_ROOT="/srv/pantheon/hindsight-knowledge-router"' in text
    assert "PORT=8023" in text
    assert "HINDSIGHT_KNOWLEDGE_BANK_ID:-KNOWLEDGE" in text
    assert "HINDSIGHT_KNOWLEDGE_SOURCE_KIND:-knowledge" in text
    assert "Environment=HINDSIGHT_ROUTER_MODE=$MODE" in text


def test_combined_instance_has_an_isolated_runtime_and_keeps_old_services() -> None:
    text = INSTALLER.read_text(encoding="utf-8")
    assert '--combined) MODE="combined"' in text
    assert 'INSTANCE="pantheon-hindsight-vault-router"' in text
    assert 'APP_ROOT="/opt/pantheon-node/hindsight-vault-router"' in text
    assert 'APP_ROOT="/opt/pantheon-node/hindsight-project-router"' in text
    assert 'STATE_ROOT="/srv/pantheon/hindsight-vault-router"' in text
    assert "Both bank IDs must be set and distinct" in text
    assert "project and knowledge source kinds must be distinct" in text
    assert 'HINDSIGHT_PROJECT_SOURCE_KIND="${HINDSIGHT_PROJECT_SOURCE_KIND:-}"' in text
    assert 'HINDSIGHT_KNOWLEDGE_SOURCE_KIND="${HINDSIGHT_KNOWLEDGE_SOURCE_KIND:-}"' in text
    assert "matching producer source tags" in text


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
    assert "def recall_knowledge_memory(" in mcp
    assert '"project": (recall_project_memory, hindsight_project_list, hindsight_project_overview)' in mcp
    assert '"knowledge": (recall_knowledge_memory, hindsight_knowledge_folders)' in mcp
    # Listing tools narrow a search; they are not a routine first call.
    assert "never for a general reference question and never as a routine first step" in mcp
    assert "Not needed before a first recall" in mcp
    assert "def recall_knowledge(" in core
    assert "tags = [source_tag]" in core
    # Check executable operations rather than prose such as "retained OCR".
    forbidden = {"retain", "retain_file", "retain_batch", "delete", "delete_document"}
    tree = ast.parse(mcp)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            assert node.name not in forbidden
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else (
                node.func.id if isinstance(node.func, ast.Name) else ""
            )
            assert name not in forbidden
