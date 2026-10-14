from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
BOOTSTRAP = COCKPIT / "live_bootstrap.js"
LOADER = COCKPIT / "data" / "cockpit_data_loader.js"
PROJECTION = COCKPIT / "projection" / "cockpit_projection.js"
DECISION_PROJECTION = COCKPIT / "projection" / "decision_request_projection.js"


def test_data_loader_is_loaded_before_projection() -> None:
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
    loader = '"data/cockpit_data_loader.js"'
    projection = '"projection/cockpit_projection.js"'
    decision_projection = '"projection/decision_request_projection.js"'

    assert loader in bootstrap
    assert decision_projection in bootstrap
    assert bootstrap.index(decision_projection) < bootstrap.index(loader)
    assert bootstrap.index(loader) < bootstrap.index(projection)


def test_projection_delegates_network_transport() -> None:
    source = PROJECTION.read_text(encoding="utf-8")

    assert "window.PantheonCockpitDataLoader.create()" in source
    assert "dataLoader.loadAgencyProjects(token)" in source
    assert "dataLoader.loadProjectSchema(token)" in source
    assert "dataLoader.loadDecisionInbox(token)" in source
    assert "dataLoader.loadProjectBundle(project, token)" in source
    assert "dataLoader.loadChildCollection(childLoadAction, token)" in source
    assert "fetch(" not in source


def test_data_loader_has_a_bounded_read_only_role() -> None:
    source = LOADER.read_text(encoding="utf-8")

    for endpoint in (
        "../agency/projects?limit=200",
        "../decision-inbox?status=pending&limit=200",
        "../agency/schema/project",
        "../agency/projects/${encoded}/information",
        "../projects/${encoded}/documents",
        "../projects/${encoded}/knowledge",
        "../work/scopes/project/${encoded}/issues",
        "../agency/projects/${encoded}/decision-requests?status=pending&limit=100",
        "../agency/projects/${encoded}/change-candidates?status=pending_review&limit=100",
    ):
        assert endpoint in source

    assert "../decision-requests?status=pending&limit=200" not in source
    assert "../work/issues?case_ref=${encoded}" not in source
    assert "../v1/agency/" not in source
    assert "../v1/projects/" not in source
    assert "/work-issues" not in source

    for forbidden in (
        "document.",
        "render",
        "navigator",
        "ChangeCandidate",
        "Evidence",
        "dispatch",
        "approve",
        "apply",
        "reject",
    ):
        assert forbidden not in source


def test_data_loader_and_projections_parse_in_node() -> None:
    for path in (LOADER, PROJECTION, DECISION_PROJECTION):
        subprocess.run(["node", "--check", str(path)], check=True, capture_output=True, text=True)


def test_data_loader_keeps_optional_metadata_failures_non_blocking() -> None:
    script = f"""
global.window = {{ fetch: async () => ({{
  ok: false,
  statusText: "Unavailable",
  json: async () => ({{ detail: "Unavailable" }}),
}}) }};
require({str(LOADER)!r});
(async () => {{
  const loader = window.PantheonCockpitDataLoader.create();
  const registries = await loader.loadRegistry("registry.json", "values");
  const tools = await loader.loadToolCatalog();
  if (registries.length !== 0 || tools.length !== 0) process.exit(1);
}})().catch(() => process.exit(2));
"""
    subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)


def test_project_schema_requests_are_coalesced_per_token_and_refreshable() -> None:
    script = f"""
let calls = 0;
global.window = {{ fetch: async () => {{
  calls += 1;
  await new Promise(resolve => setTimeout(resolve, 5));
  return {{ ok: true, statusText: "OK", json: async () => ({{ schema: {{ revision: calls }} }}) }};
}} }};
require({str(LOADER)!r});
(async () => {{
  const loader = window.PantheonCockpitDataLoader.create();
  const results = await Promise.all([
    loader.loadProjectSchema("token-a"),
    loader.loadProjectSchema("token-a"),
    loader.loadProjectSchema("token-a"),
  ]);
  if (calls !== 1) process.exit(1);
  if (!results.every(item => item.revision === 1)) process.exit(2);
  await loader.loadProjectSchema("token-a", {{ forceRefresh: true }});
  if (calls !== 2) process.exit(3);
  await loader.loadProjectSchema("token-b");
  if (calls !== 3) process.exit(4);
}})().catch(() => process.exit(5));
"""
    subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)


def test_failed_project_schema_request_is_evicted_and_retryable() -> None:
    script = f"""
let calls = 0;
global.window = {{ fetch: async () => {{
  calls += 1;
  if (calls === 1) {{
    return {{ ok: false, statusText: "Unavailable", json: async () => ({{ detail: "Unavailable" }}) }};
  }}
  return {{ ok: true, statusText: "OK", json: async () => ({{ schema: {{ revision: 2 }} }}) }};
}} }};
require({str(LOADER)!r});
(async () => {{
  const loader = window.PantheonCockpitDataLoader.create();
  try {{
    await loader.loadProjectSchema("token-a");
    process.exit(1);
  }} catch (_) {{}}
  const schema = await loader.loadProjectSchema("token-a");
  if (calls !== 2 || schema.revision !== 2) process.exit(2);
}})().catch(() => process.exit(3));
"""
    subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
