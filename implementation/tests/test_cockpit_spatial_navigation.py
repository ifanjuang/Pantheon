"""Behavior and boundary checks for the executable Cockpit spatial surface."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
PROJECTION = COCKPIT / "projection" / "cockpit_projection.js"
ASSEMBLER = COCKPIT / "projection" / "child_collection_assembler.js"
DATA_LOADER = COCKPIT / "data" / "cockpit_data_loader.js"
CARD_PROJECTION_DEFINITIONS = COCKPIT / "registries" / "card_projection_definitions.json"
SHELL_CONTROLS = COCKPIT / "shell_controls.js"


def _run_node(script: str) -> subprocess.CompletedProcess[str]:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is unavailable; JavaScript behavior check skipped")
    return subprocess.run([node, "-e", script], cwd=ROOT, check=False, capture_output=True, text=True)


@pytest.mark.parametrize("path", [COCKPIT / "spatial_navigation.js", ASSEMBLER, PROJECTION, SHELL_CONTROLS, COCKPIT / "actions" / "card_actions.js", COCKPIT / "live_bootstrap.js"], ids=lambda path: str(path.relative_to(COCKPIT)))
def test_cockpit_javascript_parses(path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is unavailable; JavaScript syntax check skipped")
    result = subprocess.run([node, "--check", str(path)], check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_spatial_navigation_keeps_sibling_and_parent_boundaries() -> None:
    script = r'''
      global.window = {};
      require("./mvp_vertical/cockpit/spatial_navigation.js");
      const nav = window.PantheonSpatialNavigation.create({ root_collection_id: "primary-spaces", root_item_ids: ["pantheon", "affaires", "knowledge", "tools"] });
      nav.selectSibling("affaires");
      if (nav.snapshot().current_id !== "affaires") throw new Error("root selection failed");
      nav.descend({ parent_entity_id: "affaires", collection_id: "projects", item_ids: ["verger", "pinede", "ormeaux"] });
      nav.moveHorizontal(1);
      if (nav.snapshot().current_id !== "pinede") throw new Error("sibling navigation escaped collection");
      if (nav.snapshot().depth !== 1) throw new Error("horizontal navigation changed depth");
      nav.ascend();
      if (nav.snapshot().current_id !== "affaires" || nav.snapshot().depth !== 0) throw new Error("ascend did not restore parent");
      nav.returnToRoot("tools");
      if (nav.snapshot().current_id !== "tools") throw new Error("explicit root jump failed");
    '''
    result = _run_node(script)
    assert result.returncode == 0, result.stderr


def test_cockpit_derives_header_spaces_from_registry_and_keeps_live_agency_project_collection() -> None:
    html = (COCKPIT / "index.html").read_text(encoding="utf-8")
    bootstrap = (COCKPIT / "live_bootstrap.js").read_text(encoding="utf-8")
    shell_controls = SHELL_CONTROLS.read_text(encoding="utf-8")
    cards_css = (COCKPIT / "styles" / "cards.css").read_text(encoding="utf-8")
    families_css = (COCKPIT / "styles" / "families.css").read_text(encoding="utf-8")
    javascript = PROJECTION.read_text(encoding="utf-8")
    root_definitions = CARD_PROJECTION_DEFINITIONS.read_text(encoding="utf-8")
    assembler = ASSEMBLER.read_text(encoding="utf-8")
    data_loader = DATA_LOADER.read_text(encoding="utf-8")

    # The Navigation Registry is the single owner of root identities/order.
    # Static HTML must not carry a competing subset of root spaces.
    assert 'data-space="' not in html
    assert "PantheonNavigationRegistry" in shell_controls
    assert "PantheonCardProjectionDefinitions" in shell_controls
    assert 'headerMenu.querySelectorAll("[data-space]").forEach' in shell_controls
    assert 'button.dataset.space = spaceId.slice("space:".length)' in shell_controls
    assert "button.textContent = definition.title" in shell_controls

    for control in ("v2-previous", "v2-next", "v2-descend", "v2-ascend", "v2-flip", "v2-breadcrumb", "v2-project", "v2-token", "v2-load"):
        assert f'id="{control}"' in html
    assert 'class="v2-hermes-dock"' in html
    assert 'src="cockpit_bootstrap.js"' in html
    for module in ("spatial_navigation.js", "projection/navigation_registry_adapter.js", "projection/child_collection_assembler.js", "projection/cockpit_projection.js", "actions/card_actions.js"):
        assert f'"{module}"' in bootstrap
    assert 'v2_' + 'app_schema.js' not in bootstrap
    assert 'v2_app.js' not in bootstrap
    assert 'params.get("mode") === "demo"' in bootstrap
    assert 'import("./demo_bootstrap.js")' in bootstrap
    for family in ("project", "information", "contact", "work", "decision", "tool"):
        assert f'[data-family="{family}"]' in families_css or f'[data-kind="{family}"]' in families_css
    assert 'prefers-reduced-motion: reduce' not in cards_css
    assert '.indicator-rail' in cards_css
    assert '.card-back' in cards_css
    assert "navigationProjection.rootItemIds" in javascript
    assert "navigationProjection.sourcesFor" in javascript
    assert 'space:decisions' not in javascript
    for operation in ("state.navigator.descend", "state.navigator.ascend", "state.navigator.returnToRoot"):
        assert operation in javascript
    assert 'state.flipped' in javascript
    assert 'PostgreSQL Agency Data' in root_definitions
    assert '../agency/projects?limit=200' in data_loader
    assert '../v1/agency/' not in data_loader
    assert "dataLoader.loadAgencyProjects(token)" in javascript
    assert "Array.isArray(payload.projects) ? payload.projects : []" in data_loader
    assert 'entity_type: "project_contacts"' in javascript
    assert 'title: "Contacts"' in javascript
    assert "projects(context)" in assembler
    assert '/participations' not in javascript


def test_pantheon_and_decisions_spaces_keep_distinct_projection_responsibilities() -> None:
    javascript = PROJECTION.read_text(encoding="utf-8")
    assembler = ASSEMBLER.read_text(encoding="utf-8")
    assert "pending_change_candidates(context)" in assembler
    assert "decision_requests(_context)" in assembler
    assert "(window.PantheonGlobalDecisionRequests || [])" in assembler
    assert "work_decisions(context)" not in assembler
    assert "current_runs(context)" in assembler
    assert 'entity_type: "work_decision"' not in javascript
    assert 'entity_type: "project_change_candidate"' in javascript
    assert 'entity_type: item.entity_type || "hermes_run"' in javascript
    assert 'available_actions: item.available_actions || []' in javascript
    assert 'window.addEventListener("pantheon:current-runs"' in javascript
    # Root identity/order comes from the registry while Pantheon and Decisions
    # retain distinct child-source projections and no authority is inferred.
    assert "navigationProjection.rootItemIds.map" in javascript
    assert 'card({ entity_id: "space:pantheon"' not in javascript
    assert 'if (rootId === "space:decisions")' in assembler
    assert 'decisionProjection().rootCard()' in assembler


def test_handoff_never_dispatches_or_starts_hermes_from_spatial_ui() -> None:
    html = (COCKPIT / "index.html").read_text(encoding="utf-8")
    handoff = (COCKPIT / "handoff" / "handoff_lifecycle.js").read_text(encoding="utf-8")
    app = PROJECTION.read_text(encoding="utf-8")
    actions = (COCKPIT / "actions" / "card_actions.js").read_text(encoding="utf-8")
    for control in ("v2-handoff-submit", "v2-handoff-admit", "v2-handoff-revoke"):
        assert f'id="{control}"' in html
    assert '>Admettre</button>' in html
    assert '>Révoquer</button>' in html
    assert '../cockpit/hermes-handoffs/submit' in handoff
    assert '../v1/cockpit/hermes-handoffs/submit' not in handoff
    assert '/admissions`' in handoff
    assert '/revocations`' in handoff
    assert '/runs/start' not in handoff
    assert '/v1/hermes/execution-admissions' not in handoff
    assert '$("v2-handoff-prepare")?.click()' in actions
    assert '$("v2-handoff-submit")?.click()' not in actions
    assert '$("v2-handoff-admit")?.click()' not in actions
    assert "direct_database_credentials" not in app
    assert "notion_token" not in app.lower()
