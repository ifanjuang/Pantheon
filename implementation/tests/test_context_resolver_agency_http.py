"""Behavior checks for the live-shaped Agency Data Context Resolver binding."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONTEXT_SELECTION = ROOT / "mvp_vertical" / "cockpit" / "context" / "context_selection.js"


def _run_node(script: str) -> subprocess.CompletedProcess[str]:
    node = shutil.which("node")
    if node is None:  # pragma: no cover
        pytest.skip("Node.js is unavailable; JavaScript behavior check skipped")
    return subprocess.run(
        [node, "-e", script],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_context_selection_javascript_parses() -> None:
    node = shutil.which("node")
    if node is None:  # pragma: no cover
        pytest.skip("Node.js is unavailable; JavaScript syntax check skipped")
    result = subprocess.run(
        [node, "--check", str(CONTEXT_SELECTION)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_agency_http_payloads_keep_stable_identity_and_project_code_ranking() -> None:
    script = r'''
      global.window = {};
      require("./mvp_vertical/cockpit/context_resolver.js");
      require("./mvp_vertical/cockpit/agency_data_binding.js");

      const resolver = window.PantheonContextResolver;
      const binding = window.PantheonAgencyDataBinding.create({
        mode: "read_only",
        resolver,
        transport: async request => {
          if (request.resource === "projects") return {
            system_of_record: "postgres",
            projects: [{
              project_id: "project-verger",
              code: "VERGER",
              display_name: "Maison de Verger",
              phase: "PRO",
              location: "Verger",
              revision: 12,
            }],
          };
          if (request.resource === "people") return {
            people: [{
              person_id: "person-helene",
              display_name: "Hélène Durand",
              email: "helene@example.test",
              revision: 3,
            }],
          };
          if (request.resource === "organizations") return {
            organizations: [{
              organization_id: "org-bet",
              name: "BET Exemple",
              siret: "12345678900000",
              revision: 4,
            }],
          };
          return [];
        },
      });
      binding.attach();

      (async () => {
        const project = await resolver.resolve("_VER");
        if (project.results[0]?.entity_id !== "project-verger") throw new Error("project stable id missing");
        if (project.results[0]?.matched_field !== "alias") throw new Error("project code alias was not ranked");
        if (project.results[0]?.source?.revision !== 12) throw new Error("project revision attribution missing");

        const person = await resolver.resolve("@helene");
        if (person.results[0]?.entity_id !== "person-helene") throw new Error("person stable id missing");

        const global = await resolver.resolve("*123456789");
        if (global.results[0]?.entity_id !== "org-bet") throw new Error("organization stable id missing");
        if (global.results.some(item => item.entity_type === "project_participation")) throw new Error("retired participation leaked into resolver");
        if (global.results.some(item => item.selected !== false)) throw new Error("provider result leaked selection state");
      })().catch(error => { console.error(error); process.exit(1); });
    '''
    result = _run_node(script)
    assert result.returncode == 0, result.stderr


def test_context_selection_surface_is_read_only_and_requires_explicit_selection() -> None:
    javascript = CONTEXT_SELECTION.read_text(encoding="utf-8")
    html = (ROOT / "mvp_vertical" / "cockpit" / "index.html").read_text(encoding="utf-8")

    assert 'effect !== "read_only"' in javascript
    assert 'scope_widened_implicitly: false' in javascript
    assert 'selected.set(' in javascript
    assert 'button.addEventListener("click", () => selectResult(item))' in javascript
    assert 'setTimeout(() => void search(raw, generation), 180)' in javascript
    assert 'generation !== searchGeneration' in javascript
    assert 'id="v2-context-input"' in html
    bootstrap = (ROOT / "mvp_vertical" / "cockpit" / "live_bootstrap.js").read_text(encoding="utf-8")
    assert '"context_resolver.js"' in bootstrap
    assert '"agency_data_binding.js"' in bootstrap
    assert '"context/context_selection.js"' in bootstrap
