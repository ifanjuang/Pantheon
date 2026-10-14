"""The static Cockpit demo must reuse the live loader contract without network route drift."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"


def _run_node(script: str) -> subprocess.CompletedProcess[str]:
    node = shutil.which("node")
    if node is None:  # pragma: no cover - depends on the runner image
        pytest.skip("Node.js is unavailable; Cockpit demo transport check skipped")
    return subprocess.run(
        [node, "-e", script],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_demo_bootstrap_does_not_duplicate_api_routes_or_replace_global_fetch() -> None:
    bootstrap = (COCKPIT / "demo_bootstrap.js").read_text(encoding="utf-8")
    loader = (COCKPIT / "data" / "cockpit_data_loader.js").read_text(encoding="utf-8")

    assert "window.fetch =" not in bootstrap
    assert '"/agency/' not in bootstrap
    assert '"/work/' not in bootstrap
    assert '"/decision-inbox' not in bootstrap
    assert "fetchImplFactory" in bootstrap
    assert 'loadStaticJson("tool_catalog.json"' in bootstrap
    assert "fixture.tool_catalog" not in bootstrap
    assert "const ROUTES" in loader
    assert "options.fetchImplFactory?.(ROUTES)" in loader
    assert 'loadOptionalCollection(ROUTES.toolCatalog(), "items")' in loader
    assert "routes: ROUTES" not in loader


def test_demo_fixture_is_data_only_and_tracks_current_projection_owners() -> None:
    fixture = json.loads((COCKPIT / "demo-data.json").read_text(encoding="utf-8"))
    navigation = json.loads((COCKPIT / "registries" / "navigation_registry.json").read_text(encoding="utf-8"))

    # Navigation and Tool Card structure are shared application contracts, not a
    # second demo architecture embedded in the fictional Agency Data universe.
    assert "tool_catalog" not in fixture
    assert "navigation" not in fixture
    assert "root_collection" not in fixture
    assert {item["id"] for item in navigation["root_collection"]["items"]} >= {
        "space:decisions",
        "space:affaires",
        "space:outils",
    }

    assert fixture["decision_requests"], "the Decisions root must have demo data to project"
    assert fixture["decision_requests"][0]["available_actions"] == [], (
        "a visible demo Decision Request must not invent consequence-bearing authority"
    )

    vallons = fixture["project_payloads"]["demo-vallons"]
    assert vallons["decision_requests"], "VALLONS should exercise the project Decision Request path"
    assert vallons["decision_requests"][0]["available_actions"] == []

    anatomy = vallons["project_anatomy"]
    assert anatomy["project_ref"] == "demo-vallons"
    assert anatomy["coverage"]["status"] == "not_persisted"
    assert anatomy["coverage"]["absence_inference_allowed"] is False
    assert anatomy["authority"]["authorization_inferred"] is False
    assert anatomy["structure"]["hierarchy"]["status"] == "not_derived"
    assert {item["object_family"] for item in anatomy["structure"]["objects"]} == {"spatial", "element"}
    assert anatomy["unmapped_material"], "the demo should preserve unmapped source material visibly"


def test_demo_start_waits_for_initial_projection_before_clicking_load() -> None:
    script = r'''
      const fs = require("fs");
      const path = require("path");

      class TestResponse {
        constructor(body, options = {}) {
          this.body = body;
          this.status = options.status ?? 200;
          this.statusText = String(this.status);
          this.headers = options.headers || {};
        }
        get ok() { return this.status >= 200 && this.status < 300; }
        async json() { return JSON.parse(this.body); }
      }

      global.Response = TestResponse;
      const cockpitRoot = path.join(process.cwd(), "mvp_vertical", "cockpit");
      const fixtureNames = new Set(["demo-data.json", "demo-work-activity.json", "tool_catalog.json"]);
      const listeners = new Map();
      let loadClicks = 0;
      const controls = {
        "v2-project": { value: "" },
        "v2-token": { value: "" },
        "v2-network": { textContent: "" },
        "v2-load": { click() { loadClicks += 1; } },
      };

      global.document = {
        getElementById(id) { return controls[id] || null; },
      };
      global.window = {
        location: { href: "https://demo.invalid/mvp_vertical/cockpit/index.html?mode=demo" },
        fetch: async input => {
          const raw = typeof input === "string" ? input : input.url;
          const name = path.basename(new URL(raw, window.location.href).pathname);
          if (!fixtureNames.has(name)) throw new Error(`unexpected native/network fetch: ${raw}`);
          return new TestResponse(fs.readFileSync(path.join(cockpitRoot, name), "utf8"), {
            status: 200,
            headers: { "Content-Type": "application/json; charset=utf-8" },
          });
        },
        addEventListener(type, listener) { listeners.set(type, listener); },
      };

      (async () => {
        const demoSource = fs.readFileSync(path.join(cockpitRoot, "demo_bootstrap.js"), "utf8");
        const executeDemo = new Function(`return (async () => {\n${demoSource}\n})();`);
        await executeDemo();

        const started = window.PantheonDemoBootstrap.start();
        await Promise.resolve();
        if (loadClicks !== 0) throw new Error("demo autoload fired before the projection was ready");
        if (!listeners.has("pantheon:graph-updated")) {
          throw new Error("demo did not wait for the existing graph readiness signal");
        }

        window.PantheonCockpitGraph = Object.freeze({});
        listeners.get("pantheon:graph-updated")();
        await started;

        if (loadClicks !== 1) throw new Error(`expected one demo autoload, got ${loadClicks}`);
        if (controls["v2-project"].value !== "VALLONS") throw new Error("demo project was not selected");
        if (controls["v2-token"].value !== "demo-read-only") throw new Error("demo token was not set");
      })().catch(error => { console.error(error); process.exit(1); });
    '''
    result = _run_node(script)
    assert result.returncode == 0, result.stderr


def test_demo_fixture_transport_covers_the_current_live_loader_contract() -> None:
    script = r'''
      const fs = require("fs");
      const path = require("path");

      class TestResponse {
        constructor(body, options = {}) {
          this.body = body;
          this.status = options.status ?? 200;
          this.statusText = String(this.status);
          this.headers = options.headers || {};
        }
        get ok() { return this.status >= 200 && this.status < 300; }
        async json() { return JSON.parse(this.body); }
      }

      global.Response = TestResponse;
      const cockpitRoot = path.join(process.cwd(), "mvp_vertical", "cockpit");
      const fixtureNames = new Set(["demo-data.json", "demo-work-activity.json", "tool_catalog.json"]);
      const nativeCalls = [];

      global.window = {
        location: { href: "https://demo.invalid/mvp_vertical/cockpit/index.html?mode=demo" },
        setTimeout,
        fetch: async input => {
          const raw = typeof input === "string" ? input : input.url;
          nativeCalls.push(raw);
          const name = path.basename(new URL(raw, window.location.href).pathname);
          if (!fixtureNames.has(name)) {
            throw new Error(`unexpected native/network fetch: ${raw}`);
          }
          return new TestResponse(fs.readFileSync(path.join(cockpitRoot, name), "utf8"), {
            status: 200,
            headers: { "Content-Type": "application/json; charset=utf-8" },
          });
        },
      };

      (async () => {
        const demoSource = fs.readFileSync(path.join(cockpitRoot, "demo_bootstrap.js"), "utf8");
        const executeDemo = new Function(`return (async () => {\n${demoSource}\n})();`);
        await executeDemo();

        const originalFactory = window.PantheonCockpitDataLoaderOptions.fetchImplFactory;
        let demoFetch = null;
        window.PantheonCockpitDataLoaderOptions = Object.freeze({
          fetchImplFactory: routes => {
            demoFetch = originalFactory(routes);
            return demoFetch;
          },
        });

        require("./mvp_vertical/cockpit/data/cockpit_data_loader.js");
        const api = window.PantheonCockpitDataLoader;
        if (!api?.create) throw new Error("loader API was not exposed");
        if ("routes" in api) throw new Error("loader route registry leaked into the public API");

        const loader = api.create();
        const tools = await loader.loadToolCatalog();
        const projects = await loader.loadAgencyProjects("demo-read-only");
        const globalDecisions = await loader.loadDecisionInbox("demo-read-only");
        const schema = await loader.loadProjectSchema("demo-read-only");
        const bundle = await loader.loadProjectBundle("demo-vallons", "demo-read-only");

        if (!demoFetch) throw new Error("demo transport factory was not used by the loader");
        if (!tools.length) throw new Error("shared tool catalogue was not projected");
        if (projects.length !== 4) throw new Error(`unexpected project count: ${projects.length}`);
        if (schema?.schema_id !== "agency.project.v2-demo") throw new Error("project schema fixture missing");
        if (globalDecisions.length !== 1) throw new Error("global Decision Request fixture missing");
        if (window.PantheonGlobalDecisionRequests.length !== 0) throw new Error("transport mutated global projection state");
        if (bundle.information.length !== 3) throw new Error("VALLONS information fixture incomplete");
        if (bundle.legacyDocuments.length !== 1) throw new Error("VALLONS document fixture incomplete");
        if (bundle.knowledge.length !== 1) throw new Error("VALLONS knowledge fixture incomplete");
        if (bundle.workIssues.length !== 1 || !bundle.workIssues[0]?.work_activity) {
          throw new Error("strict Work activity fixture was not reused");
        }
        if (bundle.decisionRequests.length !== 1 || bundle.decisionRequests[0]?.status !== "pending") {
          throw new Error("VALLONS Decision Request fixture missing");
        }
        if (bundle.changeCandidates.length !== 1 || bundle.changeCandidates[0]?.status !== "pending_review") {
          throw new Error("change-candidate status filtering drifted");
        }
        if (!bundle.projectAnatomy || bundle.projectAnatomy.project_ref !== "demo-vallons") {
          throw new Error("current Project Anatomy projection fixture missing");
        }
        if (bundle.projectAnatomy.coverage?.absence_inference_allowed !== false) {
          throw new Error("Project Anatomy fixture inferred absence from incomplete coverage");
        }
        if (nativeCalls.length !== 3) {
          throw new Error(`loader escaped controlled static resources: ${nativeCalls.join(", ")}`);
        }

        const unknown = await demoFetch("../agency/projects/demo-vallons/unmodelled-surface");
        if (unknown.status !== 404) throw new Error("unknown loader route did not fail closed");
        if (nativeCalls.length !== 3) throw new Error("unknown route fell through to native fetch");

        const write = await demoFetch("../agency/projects", { method: "POST" });
        if (write.status !== 405) throw new Error("demo write boundary regressed");
      })().catch(error => { console.error(error); process.exit(1); });
    '''
    result = _run_node(script)
    assert result.returncode == 0, result.stderr
