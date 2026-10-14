"""Static and bounded-behavior checks for the cards-first cockpit candidate."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _discover_scripts() -> list[Path]:
    """Every browser script we own, discovered rather than enumerated.

    A hand-maintained list silently stops covering a file the moment one is
    added, renamed or moved. Discovery keeps the syntax check exhaustive by
    construction; vendored third-party bundles stay excluded.
    """
    roots = (ROOT / "mvp_vertical" / "cockpit", ROOT / "mvp_vertical" / "mobile_editor")
    found = [
        path
        for root in roots
        for path in root.rglob("*.js")
        if "vendor" not in path.relative_to(ROOT).parts
    ]
    assert found, "no cockpit JavaScript discovered"
    return sorted(found)


SCRIPTS = _discover_scripts()


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda path: str(path.relative_to(ROOT)))
def test_cockpit_javascript_parses(script: Path) -> None:
    node = shutil.which("node")
    if node is None:  # pragma: no cover - depends on the runner image
        pytest.skip("Node.js is unavailable; JavaScript syntax check skipped")

    result = subprocess.run(
        [node, "--check", str(script)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_cockpit_foundations_are_loaded_before_schema_renderer() -> None:
    bootstrap = (ROOT / "mvp_vertical" / "cockpit" / "live_bootstrap.js").read_text(encoding="utf-8")
    resolver = (ROOT / "mvp_vertical" / "cockpit" / "context_resolver.js").read_text(encoding="utf-8")
    agency = (ROOT / "mvp_vertical" / "cockpit" / "agency_data_binding.js").read_text(encoding="utf-8")
    notion = (ROOT / "mvp_vertical" / "cockpit" / "notion_agency_binding.js").read_text(encoding="utf-8")
    contract = (ROOT / "mvp_vertical" / "cockpit" / "structured_interface.js").read_text(encoding="utf-8")

    for script in ("structured_interface.js", "context_resolver.js", "agency_data_binding.js"):
        assert f'"{script}"' in bootstrap
    assert bootstrap.index('"structured_interface.js"') < bootstrap.index('"context_resolver.js"')
    assert bootstrap.index('"context_resolver.js"') < bootstrap.index('"agency_data_binding.js"')
    assert bootstrap.index('"agency_data_binding.js"') < bootstrap.index('"projection/cockpit_projection.js"')

    for prefix in ('_', '"#"', '"@"', '"*"'):
        assert prefix in resolver
    assert "registerProvider" in resolver
    assert "Promise.allSettled" in resolver
    assert "namespace_required" in resolver
    assert "searchableText" in resolver
    assert "matched_field" in resolver
    assert "selected: false" in resolver

    assert 'system_of_record: "postgres"' in agency
    assert 'owner_system: "postgres"' in agency
    assert "buildMutationIntent" in agency
    assert "execution_authorized: false" in agency
    assert "direct_database_credentials: false" in agency
    assert "browser_write_execution: false" in agency

    assert '"disabled", "mirror_read_only", "selective_bidirectional"' in notion
    assert 'role: "optional_collaborative_projection"' in notion
    assert 'system_of_record: "postgres"' in notion
    assert "createFieldPolicyRegistry" in notion
    assert "classifyIncomingMutation" in notion
    assert "postgres_changed_since_notion_base" in notion
    assert "browser_sync_execution: false" in notion
    assert "browser_write_execution: false" in notion

    assert '"pantheon", "decisions", "affaires", "connaissances", "outils"' in contract
    assert '"conversation", "container", "entity"' in contract
    assert "buildTagProjection" in contract
    assert "buildCardContextEnvelope" in contract
    assert "scope_widened_implicitly: false" in contract


def _run_node(script: str) -> subprocess.CompletedProcess[str]:
    node = shutil.which("node")
    if node is None:  # pragma: no cover - depends on the runner image
        pytest.skip("Node.js is unavailable; JavaScript behavior check skipped")
    return subprocess.run(
        [node, "-e", script],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_context_resolver_composes_providers_and_explains_matches() -> None:
    script = r'''
      global.window = {};
      require("./mvp_vertical/cockpit/context_resolver.js");
      const resolver = window.PantheonContextResolver;

      (async () => {
        const detachA = resolver.registerProvider("affaires", async () => [
          { id: "p-verger", entity_type: "project", label: "Verger", tags: ["ABF"] },
        ]);
        const detachB = resolver.registerProvider("affaires", async () => [
          { id: "p-vergeron", entity_type: "project", label: "Vergeron", tags: ["Neuf"] },
        ]);

        const projects = await resolver.resolve("_VER");
        if (projects.results.length !== 2) throw new Error("providers were not composed");
        if (projects.results[0].matched_field !== "label") throw new Error("prefix match not explained");
        if (projects.results.some(item => item.selected !== false)) throw new Error("search result leaked selection state");

        const tagged = await resolver.resolve("*abf");
        if (tagged.results.length !== 1 || tagged.results[0].entity_id !== "p-verger") {
          throw new Error("global tag search failed");
        }
        if (tagged.results[0].matched_field !== "tag") throw new Error("tag match reason missing");

        detachA();
        detachB();
      })().catch(error => { console.error(error); process.exit(1); });
    '''
    result = _run_node(script)
    assert result.returncode == 0, result.stderr


def test_postgres_agency_data_binding_is_default_owner_projection() -> None:
    script = r'''
      global.window = {};
      require("./mvp_vertical/cockpit/context_resolver.js");
      require("./mvp_vertical/cockpit/agency_data_binding.js");

      const resolver = window.PantheonContextResolver;
      const resources = window.PantheonAgencyDataBinding.defaultResources;
      const transport = async request => {
        if (request.owner_system !== "postgres") throw new Error("wrong owner system");
        if (request.effect !== "read_only") throw new Error("write effect requested");
        if (request.resource === resources.affaires) return [{
          entity_id: "project-verger",
          revision: 42,
          display_name: "Verger",
          status: "En cours",
          phase: "PRO",
          location: "Verger",
          plu_zone: "U",
          tags: ["ABF"],
        }];
        if (request.resource === resources.people) return [{
          entity_id: "person-helene",
          display_name: "Hélène Durand",
          email: "helene@example.test",
        }];
        if (request.resource === resources.organizations) return [{
          entity_id: "company-bet",
          name: "BET Exemple",
          siret: "12345678900000",
        }];
        if (request.resource === resources.participations) return [{
          entity_id: "participation-bet",
          role: "BET STRUCTURE",
          type: "Maîtrise d'Oeuvre",
        }];
        return [];
      };

      (async () => {
        const binding = window.PantheonAgencyDataBinding.create({
          mode: "read_only",
          transport,
          resolver,
        });
        binding.attach();

        const project = await resolver.resolve("_VER");
        if (project.results[0]?.entity_type !== "project") throw new Error("Postgres project projection missing");
        if (project.results[0]?.source?.system !== "postgres") throw new Error("Postgres source attribution missing");
        if (project.results[0]?.source?.authority !== "agency_system_of_record") throw new Error("owner attribution missing");

        const person = await resolver.resolve("@helene");
        if (person.results[0]?.entity_type !== "person") throw new Error("Postgres people projection missing");

        const organization = await resolver.resolve("*123456789");
        if (organization.results[0]?.entity_type !== "organization") throw new Error("Postgres global projection missing");

        const status = binding.status();
        if (status.system_of_record !== "postgres") throw new Error("Postgres is not the declared system of record");
        if (status.direct_database_credentials !== false || status.browser_write_execution !== false) {
          throw new Error("Agency Data browser boundary regressed");
        }

        const mutation = window.PantheonAgencyDataBinding.buildMutationIntent({
          entity_type: "project",
          entity_id: "project-verger",
          field: "phase",
          value: "DCE",
          expected_revision: 42,
        });
        if (mutation.owner_system !== "postgres" || mutation.execution_authorized !== false) {
          throw new Error("mutation candidate boundary regressed");
        }

        binding.detach();
      })().catch(error => { console.error(error); process.exit(1); });
    '''
    result = _run_node(script)
    assert result.returncode == 0, result.stderr


def test_notion_selective_bidirectional_policy_rejects_undeclared_and_detects_conflict() -> None:
    script = r'''
      global.window = {};
      require("./mvp_vertical/cockpit/notion_agency_binding.js");

      const binding = window.PantheonNotionAgencyBinding.create({
        mode: "selective_bidirectional",
        fieldPolicies: [
          {
            entity_type: "project",
            field: "phase",
            notion_visible: true,
            notion_editable: true,
            sync_direction: "bidirectional",
            conflict_policy: "human_review",
          },
          {
            entity_type: "project",
            field: "evidence_status",
            notion_visible: true,
            notion_editable: false,
            sync_direction: "postgres_to_notion",
            conflict_policy: "postgres_authoritative",
          },
        ],
      });

      const accepted = binding.classifyIncomingMutation({
        entity_type: "project",
        entity_id: "project-verger",
        field: "phase",
        value: "DCE",
        base_revision: 42,
        postgres_revision: 42,
      });
      if (accepted.status !== "mutation_candidate") throw new Error("declared Notion edit not admitted as candidate");
      if (accepted.execution_authorized !== false) throw new Error("Notion edit became implicitly authorized");
      if (accepted.candidate.owner_system !== "postgres") throw new Error("Notion edit changed record ownership");

      const conflict = binding.classifyIncomingMutation({
        entity_type: "project",
        entity_id: "project-verger",
        field: "phase",
        value: "ACT",
        base_revision: 42,
        postgres_revision: 43,
      });
      if (conflict.status !== "conflict" || conflict.reason !== "postgres_changed_since_notion_base") {
        throw new Error("concurrent edit conflict not detected");
      }

      const rejected = binding.classifyIncomingMutation({
        entity_type: "project",
        entity_id: "project-verger",
        field: "evidence_status",
        value: "approved",
        base_revision: 43,
        postgres_revision: 43,
      });
      if (rejected.status !== "rejected_not_editable") throw new Error("protected field accepted from Notion");

      const unavailable = binding.buildSyncState({
        postgres_revision: 44,
        notion_revision: 43,
        notion_available: false,
      });
      if (unavailable.status !== "notion_unavailable") throw new Error("Notion outage state missing");

      const status = binding.status();
      if (status.system_of_record !== "postgres" || status.browser_sync_execution !== false) {
        throw new Error("Notion collaboration boundary regressed");
      }
    '''
    result = _run_node(script)
    assert result.returncode == 0, result.stderr


def test_static_demo_reuses_cockpit_assets_and_blocks_network() -> None:
    # demo.html is a thin redirect to the Cockpit demo mode; it no longer embeds
    # the legacy self-contained static demo (app.js / demo.js / styles/index.css).
    html = (ROOT / "mvp_vertical" / "cockpit" / "demo.html").read_text(
        encoding="utf-8"
    )
    bootstrap = (ROOT / "mvp_vertical" / "cockpit" / "demo_bootstrap.js").read_text(
        encoding="utf-8"
    )

    assert "index.html?mode=demo" in html
    assert "v2.html?mode=demo" not in html
    for legacy in ('src="app.js"', 'src="demo.js"', 'href="styles/index.css"'):
        assert legacy not in html

    assert 'method !== "GET"' in bootstrap
    assert "demo-data.json" in bootstrap
    assert "écriture désactivée" in bootstrap


def test_mobile_editor_exposes_and_clears_device_local_data() -> None:
    html = (ROOT / "mvp_vertical" / "mobile_editor" / "index.html").read_text(
        encoding="utf-8"
    )
    javascript = (ROOT / "mvp_vertical" / "mobile_editor" / "app.js").read_text(
        encoding="utf-8"
    )

    assert 'id="clear-local"' in html
    assert "sans chiffrement applicatif" in html
    assert '"pantheon-knowledge:"' in javascript
    assert '"pantheon-project:"' in javascript
    assert "localStorage.removeItem" in javascript
    assert 'sessionStorage.removeItem("pantheon-human-actor")' in javascript
    assert '$("clear-local").onclick = clearLocalData' in javascript


def test_mobile_editor_recovers_legacy_offline_revisions_before_queue_cleanup() -> None:
    javascript = (ROOT / "mvp_vertical" / "mobile_editor" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "function legacyDraftKey" in javascript
    assert "function migrateLegacyRevisions" in javascript
    assert 'operation?.type !== "revision"' in javascript
    assert "localStorage.setItem(" in javascript
    assert "legacyDraftKey(knowledgeId)" in javascript
    assert "recovered?.markdown ?? remoteMarkdown" in javascript
    assert "localStorage.removeItem(legacyDraftKey(updated.knowledge_id))" in javascript
    assert "ancienne(s) révision(s) récupérée(s) comme brouillon local" in javascript
    assert "retiredRevisions" not in javascript


def test_removed_site_list_registry_is_not_advertised_as_runtime_configuration() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "MVP_SITE_LISTS_JSON" not in compose
    assert "/config" not in compose
    assert not (ROOT / "config" / "site_lists.json").exists()
    assert not (ROOT / "config" / "README.md").exists()
