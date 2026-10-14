"""Frontend contract tests for Knowledge navigation through Category roots."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
REGISTRY = COCKPIT / "registries" / "navigation_registry.json"
REGISTRY_LOADER = COCKPIT / "projection" / "navigation_registry_loader.js"
ASSEMBLER = COCKPIT / "projection" / "child_collection_assembler.js"


def _run_node(body: str) -> subprocess.CompletedProcess[str]:
    node = shutil.which("node")
    if node is None:  # pragma: no cover - runner dependent
        pytest.skip("Node.js is unavailable; Category root navigation check skipped")
    return subprocess.run(
        [node, "--input-type=module", "-e", body],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_navigation_registry_declares_category_roots_without_endpoint_routing() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    knowledge_space = next(
        item
        for item in registry["root_collection"]["items"]
        if item["id"] == "space:connaissances"
    )

    assert knowledge_space["sources"] == ["category_roots"]
    assert "knowledge" not in {
        source
        for item in registry["root_collection"]["items"]
        for source in item["sources"]
    }
    serialized = json.dumps(registry)
    assert "/cockpit/" not in serialized
    assert "/agency/" not in serialized
    assert "endpoint" not in serialized

    loader_source = REGISTRY_LOADER.read_text(encoding="utf-8")
    assert '"category_roots"' in loader_source
    assert '"knowledge"' not in loader_source


def test_knowledge_root_is_available_until_loaded_and_project_knowledge_remains_visible() -> None:
    result = _run_node(
        f"""
        globalThis.window = {{
          PantheonDecisionRequestProjection: {{
            normalize(value) {{ return value; }},
            rootCard() {{ return {{ entity_id: "space:decisions" }}; }},
          }},
          PantheonProjectAnatomyProjection: {{ projectCards() {{ return null; }} }},
          PantheonGlobalDecisionRequests: [],
          PantheonProjectDecisionRequests: [],
        }};
        await import({json.dumps(ASSEMBLER.as_uri())});

        const cards = new Map([
          ["space:affaires", {{ entity_id: "space:affaires" }}],
          ["space:connaissances", {{ entity_id: "space:connaissances" }}],
        ]);
        const children = new Map();
        const state = {{
          cards,
          children,
          projects: [{{ project_id: "P1" }}],
          information: [],
          legacyDocuments: [],
          knowledge: [{{ knowledge_id: "K1", title: "Knowledge 1" }}],
          workIssues: [],
          changeCandidates: [],
          currentRuns: [],
          projectAnatomy: null,
        }};
        const putCard = model => {{ cards.set(model.entity_id, model); return model.entity_id; }};
        const setChildren = (parent, ids) => children.set(parent, ids.slice());

        window.PantheonChildCollectionAssembler.assemble({{
          rootItemIds: ["space:affaires", "space:connaissances"],
          sourcesFor(rootId) {{
            return rootId === "space:affaires" ? ["projects"] : ["category_roots"];
          }},
          state,
          selected: {{ project_id: "P1", contacts: [] }},
          selectedProjectId: "P1",
          selectedCardId: "project:P1",
          putCard,
          setChildren,
          normalizeProject(item) {{
            return {{
              entity_id: `project:${{item.project_id}}`,
              entity_type: "project",
              source_project_id: item.project_id,
            }};
          }},
          normalizeKnowledge(item) {{
            return {{
              entity_id: `knowledge:${{item.knowledge_id}}`,
              entity_type: "knowledge",
              title: item.title,
            }};
          }},
          normalizeChangeCandidate: value => value,
          normalizeCurrentRun: value => value,
          normalizeContacts(projectId) {{ return {{ entity_id: `project:${{projectId}}:contacts` }}; }},
          normalizeInformation: value => value,
          normalizeLegacyDocument: value => value,
          normalizeWork: value => value,
          buildToolCards() {{ return []; }},
          workData: value => value,
          currentRunItems() {{ return []; }},
        }});

        const knowledgeRoot = cards.get("space:connaissances");
        if (knowledgeRoot.child_collection?.state !== "available") throw new Error("Knowledge root was treated as loaded");
        if (knowledgeRoot.child_collection?.collection_id !== "children:space:connaissances") throw new Error("Knowledge collection identity missing");
        if (knowledgeRoot.child_collection?.load_action?.kind !== "collection_read") throw new Error("Knowledge root is not using generic collection_read");
        if (knowledgeRoot.child_collection?.load_action?.href !== "/cockpit/category-collections") throw new Error("Knowledge root Cockpit projection href mismatch");
        if (children.has("space:connaissances")) throw new Error("unloaded Knowledge root was projected as an empty child relation");

        const projectChildren = children.get("project:P1") || [];
        if (!projectChildren.includes("knowledge:K1")) throw new Error("unclassified Project Knowledge disappeared");
        if (cards.get("knowledge:K1")?.entity_type !== "knowledge") throw new Error("Knowledge Card identity changed");
        """
    )
    assert result.returncode == 0, result.stderr


def test_category_roots_are_supported_as_lazy_source_not_eager_business_resolver() -> None:
    source = ASSEMBLER.read_text(encoding="utf-8")

    assert "const LAZY_COLLECTION_SOURCES" in source
    assert 'category_roots: Object.freeze({' in source
    assert 'href: "/cockpit/category-collections"' in source
    assert "knowledge(context)" not in source
    assert "...context.state.knowledge.map(context.normalizeKnowledge)" in source
    assert "Lazy navigation source must own its root collection exclusively" in source
    assert "supportedSourceNames()" in source
