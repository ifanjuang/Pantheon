from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "templates" / "hermes" / "dashboard-plugins" / "pantheon-modules"
MANIFEST = PLUGIN / "dashboard" / "manifest.json"
DIST = PLUGIN / "dashboard" / "dist" / "index.js"
CSS = PLUGIN / "dashboard" / "dist" / "style.css"
NIGHT_OPERATIONS = PLUGIN / "night-operations.template.yaml"


def _function_block(source: str, name: str, next_name: str) -> str:
    start = source.index(f"function {name}(")
    end = source.index(f"function {next_name}(", start)
    return source[start:end]


def _marked_block(source: str, start_marker: str, end_marker: str) -> str:
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    return source[start:end]


def test_dashboard_manifest_and_installer_manifest_are_aligned() -> None:
    dashboard = json.loads(MANIFEST.read_text(encoding="utf-8"))
    plugin = yaml.safe_load((PLUGIN / "plugin.yaml").read_text(encoding="utf-8"))

    assert dashboard["name"] == plugin["name"] == "pantheon-modules"
    assert dashboard["version"] == plugin["version"] == "0.3.0"
    assert dashboard["entry"] == "dist/index.js"
    assert dashboard["css"] == "dist/style.css"
    assert "api" not in dashboard
    marker = (PLUGIN / "__init__.py").read_text(encoding="utf-8")
    assert "registers no hooks, tools, providers, routes" in marker
    assert "def register(_ctx) -> None:" in marker
    assert ".register_" not in marker
    assert not plugin.get("hooks")
    assert not plugin.get("provides_tools")

    assert DIST.is_file()
    assert CSS.is_file()


def test_hermes_plugin_implements_control_v1_visual_contract() -> None:
    plugin_css = CSS.read_text(encoding="utf-8")
    for token in (
        "--pm-bg: #090a0d",
        "--pm-card: #0d1016",
        "--pm-blue: #88bbff",
        ".pm-hero",
        ".pm-card",
        ".pm-states",
        ".pm-mode-live",
        "@media (max-width: 520px)",
    ):
        assert token in plugin_css

    plugin = DIST.read_text(encoding="utf-8")
    assert 'data-pantheon-design' in plugin
    assert 'control-v1' in plugin
    assert 'pm-hero-actions' in plugin
    assert 'pm-badge' in plugin

    for state_label in (
        "Listed",
        "Detected",
        "Installed",
        "Configured",
        "Hermes enabled",
        "Reachable",
        "Health",
        "Governance",
        "Task use",
    ):
        assert f'"{state_label}"' in plugin

def test_bundle_uses_host_sdk_and_preserves_state_axes() -> None:
    source = DIST.read_text(encoding="utf-8")

    assert "window.__HERMES_PLUGIN_SDK__" in source
    assert 'registry.register("pantheon-modules", PantheonModulesPage)' in source
    assert "__HERMES_SESSION_TOKEN__" not in source
    assert "localStorage." not in source
    assert "fetch(" not in source

    for api_method in (
        "getMemory",
        "getMcpCatalog",
        "getMcpServers",
        "getPluginsHub",
        "getCronJobs",
        "setMemoryProvider",
        "installMcpCatalogEntry",
        "setMcpServerEnabled",
        "testMcpServer",
        "enableAgentPlugin",
        "disableAgentPlugin",
        "pauseCronJob",
        "resumeCronJob",
        "updateCronJob",
        "triggerCronJob",
    ):
        assert f'"{api_method}"' in source

    for label in (
        "Listed",
        "Detected",
        "Installed",
        "Configured",
        "Hermes enabled",
        "Reachable",
        "Health",
        "Governance",
        "Task use",
    ):
        assert f'"{label}"' in source

    assert "Activer un module dans Hermes ne l’autorise pas automatiquement pour une tâche." in source

    for forbidden_cron_mutation in (
        "createCronJob",
        "deleteCronJob",
    ):
        assert f'"{forbidden_cron_mutation}"' not in source


def test_every_native_operation_has_an_immediate_human_confirmation() -> None:
    source = DIST.read_text(encoding="utf-8")

    blocks = (
        _function_block(source, "handleMemory", "handlePlugin"),
        _function_block(source, "handlePlugin", "handleMcpToggle"),
        _function_block(source, "handleMcpToggle", "handleProbe"),
        _function_block(source, "handleProbe", "handleEnvChange"),
        _marked_block(source, "function handleInstall(", "const actionProps ="),
        _function_block(source, "handleOperationToggle", "handleOperationTiming"),
        _function_block(source, "handleOperationTiming", "handleOperationRunNow"),
        _marked_block(source, "function handleOperationRunNow(", "const actionProps ="),
    )
    for block in blocks:
        assert "window.confirm(" in block


def test_known_capability_policies_remain_cautious() -> None:
    source = DIST.read_text(encoding="utf-8")

    for capability in ("mem0", "n8n", "pantheon-policy", "langgraph", "memvid"):
        assert capability in source

    for tool in (
        "health",
        "list_workflows",
        "get_workflow",
        "find_workflows",
        "list_executions",
        "get_execution",
        "recent_failures",
        "export_workflow",
        "activate_workflow",
        "deactivate_workflow",
        "container_logs",
    ):
        assert f'"{tool}"' in source

    assert "No native activation action is exposed for this candidate." in source
    assert "Only one external Hermes memory provider" in source
    assert "Installation or Hermes enablement never authorizes" in source


def test_review_first_install_documentation_uses_supported_subdirectory_form() -> None:
    readme = (PLUGIN / "README.md").read_text(encoding="utf-8")

    assert (
        "ifanjuang/Pantheon/templates/hermes/dashboard-plugins/pantheon-modules"
        in readme
    )
    assert "--no-enable" in readme
    assert "hermes plugins enable pantheon-modules" in readme
    assert "8b209e0dd7b8e308d5b923fa80f7a72f71042636" in readme
    assert "7a9ae00795593aa1fdb4e61ecd640e8bfd0c3841" in readme
    assert "host's local timezone" in readme
    assert "never creates or deletes Cron jobs" in readme
    assert "re-enabled,\nretimed, or launched" in readme


def test_night_operations_are_finite_review_candidates_not_hidden_jobs() -> None:
    manifest = yaml.safe_load(NIGHT_OPERATIONS.read_text(encoding="utf-8"))

    assert manifest["execution_owner"] == "hermes_native_cron"
    assert manifest["scheduling_posture"] == "control_existing_bounded_jobs_only"
    assert manifest["runtime_timezone"] == "REQUIRED"
    activation = manifest["activation_contract"]
    assert activation["direct_dashboard_creation_supported"] is False
    assert activation["expiry_or_run_limit"] == "REQUIRED"
    assert activation["profile"] == "REQUIRED"
    assert activation["workdir"] == "REQUIRED_ABSOLUTE_PATH"
    assert activation["existing_bounded_job_controls"] == {
        "pause": "separately_confirmed",
        "resume": "separately_confirmed",
        "retime_while_paused": "separately_confirmed",
        "trigger_now_while_enabled": "separately_confirmed",
        "delete": "forbidden",
    }

    operations = manifest["operations"]
    assert [operation["id"] for operation in operations] == [
        "backup_preflight",
        "pdf_ingestion_vectorization",
        "retrieval_quality_review",
        "memory_consolidation_review",
        "contradiction_drift_review",
        "morning_decision_digest",
    ]
    assert [operation["order"] for operation in operations] == sorted(
        operation["order"] for operation in operations
    )
    assert all(operation["trial_runs"] > 0 for operation in operations)
    assert all(
        operation["recommended_schedule"]["timezone_basis"]
        == "hermes_host_local"
        for operation in operations
    )
    assert all(
        operation["job_name"].startswith("pantheon-night:")
        for operation in operations
    )

    ingestion = next(
        operation
        for operation in operations
        if operation["id"] == "pdf_ingestion_vectorization"
    )
    assert "indexed_means_evidence" in ingestion["forbidden_effects"]
    assert "cross_project_indexing" in ingestion["forbidden_effects"]

    memory = next(
        operation
        for operation in operations
        if operation["id"] == "memory_consolidation_review"
    )
    assert "automatic Registre Probatoire promotion" in memory["forbidden_effects"]

    digest = next(
        operation
        for operation in operations
        if operation["id"] == "morning_decision_digest"
    )
    assert "external delivery without approval" in digest["forbidden_effects"]


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")
def test_bundle_syntax_and_normalizers_with_a_mock_host() -> None:
    subprocess.run(["node", "--check", str(DIST)], check=True, capture_output=True, text=True)

    script = f"""
global.window = {{
  __HERMES_PLUGIN_SDK__: {{
    React: {{ createElement: function () {{ return null; }} }},
    hooks: {{}},
    components: {{}},
    api: {{}}
  }},
  __HERMES_PLUGINS__: {{ register: function () {{}} }}
}};
require({json.dumps(str(DIST))});
const t = window.__PANTHEON_MODULES_TEST__;
const inventory = t.normalizeInventory({{
  memory: {{ active: "mem0", providers: [{{
    name: "mem0", status: "ready", configured: true, description: "memory"
  }}] }},
  catalog: {{ entries: [{{
    name: "n8n", description: "automation", installed: false, enabled: false,
    required_env: [{{ name: "N8N_API_KEY", required: true }}],
    default_enabled: ["health"]
  }}] }},
  servers: {{ servers: [{{ name: "pantheon-policy", enabled: true }}] }},
  hub: {{ plugins: [{{ name: "example", runtime_status: "disabled" }}] }}
}}, {{ "pantheon-policy": {{ ok: true, tools: [{{ name: "list_sources" }}] }} }});
if (!t.isSecretEnv("N8N_API_KEY") || t.isSecretEnv("N8N_BASE_URL")) process.exit(2);
if (t.timeFromCron("45 2 * * *") !== "02:45") process.exit(10);
if (t.cronWithTime("45 3 * * 0", "04:15") !== "15 4 * * 0") process.exit(11);
if (t.cronWithTime("@daily", "04:15") !== null) process.exit(12);
if (!inventory.memory[0].enabled || inventory.memory[0].policy.governance !== "candidate") process.exit(3);
if (inventory.mcps[0].id !== "n8n" || inventory.mcps[0].configured !== null) process.exit(4);
const wiki = inventory.mcps.find(function (item) {{ return item.id === "pantheon-policy"; }});
if (!wiki || wiki.reachable !== true || wiki.policy.risk !== "low") process.exit(5);
if (inventory.plugins[0].enabled !== false) process.exit(6);
const operations = t.normalizeOperations([{{
  id: "job-1",
  name: "pantheon-night:pdf-ingestion-vectorization",
  profile_name: "default",
  schedule_display: "0 1 * * *",
  repeat: {{ times: 7, completed: 2 }},
  enabled: true,
  state: "scheduled",
  last_status: "ok",
  next_run_at: "2026-07-16T01:00:00+02:00"
}}, {{
  id: "job-2",
  name: "pantheon-night:memory-consolidation-review",
  repeat: {{ times: null, completed: 1 }},
  enabled: true,
  state: "scheduled",
  last_status: "error"
}}, {{
  id: "job-3",
  name: "pantheon-night:morning-decision-digest",
  profile_name: "default",
  schedule: {{ expr: "15 6 * * *" }},
  repeat: {{ times: 1, completed: 1 }},
  enabled: false,
  state: "paused",
  last_status: "ok"
}}]);
const ingestion = operations.find(function (item) {{ return item.id === "pdf_ingestion_vectorization"; }});
if (!ingestion || ingestion.bounded !== true || ingestion.governance !== "bounded_trial_observed") process.exit(7);
const memory = operations.find(function (item) {{ return item.id === "memory_consolidation_review"; }});
if (!memory || memory.bounded !== false || memory.governance !== "blocked_unbounded") process.exit(8);
const backup = operations.find(function (item) {{ return item.id === "backup_preflight"; }});
if (!backup || backup.detected !== false || backup.bounded !== null) process.exit(9);
const exhausted = operations.find(function (item) {{ return item.id === "morning_decision_digest"; }});
if (!exhausted || exhausted.trialRemaining !== 0 || exhausted.governance !== "blocked_trial_exhausted") process.exit(13);
"""
    subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
