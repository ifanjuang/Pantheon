import json
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
REGISTRY = COCKPIT / "registries" / "navigation_registry.json"
ASSEMBLER = COCKPIT / "projection" / "child_collection_assembler.js"
DATA_LOADER = COCKPIT / "data" / "cockpit_data_loader.js"
COCKPIT_PROJECTION = COCKPIT / "projection" / "cockpit_projection.js"
LIVE_ADAPTER = COCKPIT / "live_collection_adapter.js"


def _run_node(body: str) -> subprocess.CompletedProcess[str]:
    node = shutil.which("node")
    if node is None:  # pragma: no cover - runner dependent
        pytest.skip("Node.js is unavailable; Card/Collection behavior check skipped")
    return subprocess.run(
        [node, "--input-type=module", "-e", body],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_root_navigation_registry_does_not_own_entity_child_assembly() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    assert registry["revision"] == 1
    assert "entity_collections" not in registry


def test_child_collection_assembler_projects_loaded_and_available_relations() -> None:
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

        const cards = new Map([["space:affaires", {{ entity_id: "space:affaires" }}]]);
        const children = new Map();
        const state = {{
          cards,
          children,
          projects: [{{ project_id: "P1" }}, {{ project_id: "P2" }}],
          information: [],
          legacyDocuments: [],
          workIssues: [],
          changeCandidates: [],
          currentRuns: [],
          knowledge: [],
          projectAnatomy: null,
        }};
        const putCard = model => {{ cards.set(model.entity_id, model); return model.entity_id; }};
        const setChildren = (parent, ids) => children.set(parent, ids.slice());
        const normalizeProject = item => ({{
          entity_id: `project:${{item.project_id}}`,
          entity_type: "project",
          source_project_id: item.project_id,
        }});

        window.PantheonChildCollectionAssembler.assemble({{
          rootItemIds: ["space:affaires"],
          sourcesFor() {{ return ["projects"]; }},
          state,
          selected: {{ project_id: "P1", contacts: [] }},
          selectedProjectId: "P1",
          selectedCardId: "project:P1",
          putCard,
          setChildren,
          normalizeProject,
          normalizeKnowledge: value => value,
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

        const root = cards.get("space:affaires");
        const selected = cards.get("project:P1");
        const unloaded = cards.get("project:P2");
        if (root.child_collection?.state !== "loaded") throw new Error("root collection not projected loaded");
        if (root.child_collection?.collection_id !== "children:space:affaires") throw new Error("root collection identity missing");
        if (selected.child_collection?.state !== "loaded") throw new Error("selected project not projected loaded");
        if (selected.child_collection?.can_add !== true) throw new Error("selected project lost create capability");
        if (unloaded.child_collection?.state !== "available") throw new Error("unloaded project not projected available");
        if (unloaded.child_collection?.load_action?.kind !== "project_bundle") throw new Error("project load action missing");
        """
    )
    assert result.returncode == 0, result.stderr


def test_child_collection_assembler_registers_projected_loaded_and_empty_collections() -> None:
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
          ["category:urbanisme", {{
            entity_id: "category:urbanisme",
            child_collection: {{
              state: "available",
              collection_id: "children:category:urbanisme",
              load_action: {{ kind: "collection_read", href: "/cockpit/category-collections/urbanisme" }},
              can_add: false,
            }},
          }}],
          ["category:empty", {{
            entity_id: "category:empty",
            child_collection: {{
              state: "available",
              collection_id: "children:category:empty",
              load_action: {{ kind: "collection_read", href: "/cockpit/category-collections/empty" }},
              can_add: false,
            }},
          }}],
        ]);
        const children = new Map();
        const state = {{ cards, children }};
        const putCard = model => {{ cards.set(model.entity_id, model); return model.entity_id; }};
        const setChildren = (parent, ids) => children.set(parent, ids.slice());
        const context = {{ state, putCard, setChildren }};

        const ids = window.PantheonChildCollectionAssembler.registerLoadedCollection(
          "category:urbanisme",
          {{
            collection_id: "children:category:urbanisme",
            parent_entity_id: "category:urbanisme",
            state: "loaded",
            items: [{{ entity_id: "document:plui", entity_type: "document", title: "PLUi" }}],
          }},
          context,
        );
        if (ids.length !== 1 || ids[0] !== "document:plui") throw new Error("loaded items not registered");
        if (cards.get("category:urbanisme").child_collection?.state !== "loaded") throw new Error("parent not marked loaded");
        if (children.get("category:urbanisme")?.[0] !== "document:plui") throw new Error("child relation missing");

        const emptyIds = window.PantheonChildCollectionAssembler.registerLoadedCollection(
          "category:empty",
          {{
            collection_id: "children:category:empty",
            parent_entity_id: "category:empty",
            state: "empty",
            items: [],
          }},
          context,
        );
        if (emptyIds.length !== 0) throw new Error("empty collection gained children");
        if (cards.get("category:empty").child_collection?.state !== "empty") throw new Error("parent not marked empty");
        if ((children.get("category:empty") || []).length !== 0) throw new Error("empty relation missing");

        let mismatchRejected = false;
        try {{
          window.PantheonChildCollectionAssembler.registerLoadedCollection(
            "category:urbanisme",
            {{
              collection_id: "children:category:urbanisme",
              parent_entity_id: "category:other",
              state: "empty",
              items: [],
            }},
            context,
          );
        }} catch (_) {{ mismatchRejected = true; }}
        if (!mismatchRejected) throw new Error("parent mismatch was accepted");

        let loadedEmptyRejected = false;
        try {{
          window.PantheonChildCollectionAssembler.registerLoadedCollection(
            "category:empty",
            {{
              collection_id: "children:category:empty",
              parent_entity_id: "category:empty",
              state: "loaded",
              items: [],
            }},
            context,
          );
        }} catch (_) {{ loadedEmptyRejected = true; }}
        if (!loadedEmptyRejected) throw new Error("loaded collection without items was accepted");
        """
    )
    assert result.returncode == 0, result.stderr


def test_data_loader_is_transport_only_and_normalizes_internal_collection_hrefs() -> None:
    source = DATA_LOADER.read_text(encoding="utf-8")

    assert "async function loadChildCollection(action, token)" in source
    assert 'action.kind === "collection_read"' in source
    assert "loadProjectedCollection(action, token)" in source
    assert 'new URL(href, "http://pantheon.invalid/")' in source
    assert 'resolved.origin !== "http://pantheon.invalid"' in source
    assert '!resolved.pathname.startsWith("/cockpit/")' in source
    assert 'return `${resolved.pathname}${resolved.search}`;' in source
    assert "payload?.cards_are_projections !== true" in source
    assert 'action.kind === "project_bundle"' in source
    assert "return loadProjectBundle(contextId, token);" in source
    assert "loadChildCollection," in source
    assert "document." not in source
    create_body = source.split("function create", 1)[1].split("window.PantheonGlobalDecisionRequests", 1)[0]
    assert "PantheonProjectDecisionRequests =" not in create_body
    assert "PantheonGlobalDecisionRequests =" not in create_body


def test_data_loader_collection_read_behavior_preserves_transport_boundary() -> None:
    result = _run_node(
        f"""
        globalThis.window = {{ fetch() {{ throw new Error("unexpected default fetch"); }} }};
        await import({json.dumps(DATA_LOADER.as_uri())});

        const requests = [];
        const fetchImpl = async (path, options = {{}}) => {{
          requests.push({{ path, options }});
          return {{
            ok: true,
            async json() {{
              return {{
                cards_are_projections: true,
                collection: {{
                  collection_id: "children:category:urbanisme",
                  parent_entity_id: "category:urbanisme",
                  state: "loaded",
                  items: [{{ entity_id: "document:plui" }}],
                }},
              }};
            }},
          }};
        }};
        const loader = window.PantheonCockpitDataLoader.create({{ fetchImpl }});
        const collection = await loader.loadChildCollection(
          {{ kind: "collection_read", href: "/cockpit/category-collections/urbanisme" }},
          "read-token",
        );
        if (collection.collection_id !== "children:category:urbanisme") throw new Error("collection not returned");
        if (requests.length !== 1) throw new Error("unexpected request count");
        if (requests[0].path !== "/cockpit/category-collections/urbanisme") throw new Error("href rewritten incorrectly");
        if (requests[0].options.headers?.Authorization !== "Bearer read-token") throw new Error("read authorization missing");
        if (requests[0].options.cache !== "no-store") throw new Error("collection read may be cached");

        let externalRejected = false;
        try {{
          await loader.loadChildCollection(
            {{ kind: "collection_read", href: "https://example.com/collection" }},
            "read-token",
          );
        }} catch (_) {{ externalRejected = true; }}
        if (!externalRejected) throw new Error("external href was accepted");
        if (requests.length !== 1) throw new Error("external href reached transport");

        let traversalRejected = false;
        try {{
          await loader.loadChildCollection(
            {{ kind: "collection_read", href: "/cockpit/%2e%2e/agency/projects" }},
            "read-token",
          );
        }} catch (_) {{ traversalRejected = true; }}
        if (!traversalRejected) throw new Error("normalized path escaped the cockpit surface");
        if (requests.length !== 1) throw new Error("escaped href reached transport");
        """
    )
    assert result.returncode == 0, result.stderr


def test_cockpit_projection_descends_from_generic_collection_action_and_rejects_stale_graph_loads() -> None:
    source = COCKPIT_PROJECTION.read_text(encoding="utf-8")

    assert 'model.entity_type === "project"' not in source
    assert 'model?.entity_type === "project"' not in source
    assert "function canDescend(model)" in source
    assert 'childCollection?.state === "available"' in source
    assert "Boolean(childCollection.load_action)" in source
    assert '$("v2-descend").disabled = !canDescend(model);' in source
    assert "collection_id: childCollection.collection_id" in source
    assert "|| `children:${model.entity_id}`" not in source

    assert "async function loadProjectedChildCollection(model, childCollection)" in source
    assert "async function loadAvailableChildCollection(model, childCollection)" in source
    assert "childAssembler.registerLoadedCollection(parentId, collection" in source
    assert "collection.collection_id !== expectedCollectionId" in source
    assert "collection.parent_entity_id !== parentId" in source
    assert 'childCollection.load_action?.kind === "project_bundle"' in source

    assert "let projectLoadGeneration = 0;" in source
    assert "let graphLoadGeneration = 0;" in source
    assert "const generation = ++projectLoadGeneration;" in source
    assert "const graphGeneration = ++graphLoadGeneration;" in source
    assert source.count("generation !== projectLoadGeneration || graphGeneration !== graphLoadGeneration") >= 3
    assert source.count("generation !== graphLoadGeneration") >= 2
    assert "graphLoadGeneration += 1;" in source

    assert "dataLoader.loadChildCollection(childLoadAction, token)" in source
    assert "window.PantheonProjectDecisionRequests = Object.freeze" in source
    assert "window.PantheonGlobalDecisionRequests = Object.freeze" in source
    assert 'parentEntityId = snapshot.path[snapshot.path.length - 1]?.parent_entity_id || null' in source


def test_missing_token_releases_load_control_after_invalidating_an_older_project_request() -> None:
    source = COCKPIT_PROJECTION.read_text(encoding="utf-8")

    load_project = source.index("async function loadProject")
    guard = source.index("if (!token) {", load_project)
    release = source.index("loadButton.disabled = false;", guard)
    message = source.index('return setMessage("Clé d’accès requise pour lire Agency Data.");', guard)

    assert 'const loadButton = $("v2-load");' in source[load_project:]
    assert guard < release < message
    assert "if (generation === projectLoadGeneration) loadButton.disabled = false;" in source


def test_live_collection_adapter_uses_explicit_parent_relation_not_id_parsing() -> None:
    source = LIVE_ADAPTER.read_text(encoding="utf-8")

    assert 'model?.entity_type === "project"' not in source
    assert 'parent?.entity_type === "project"' not in source
    assert "CHILD_COLLECTION_PREFIX" not in source
    assert "parentIdForCollection" not in source
    assert "currentParentEntityId" in source
    assert "model?.child_collection?.collection_id === id" in source
    assert "parent?.child_collection?.can_add === true" in source
    assert "parent?.child_collection?.create_action" in source


def test_live_collection_states_keep_not_loaded_distinct_from_empty() -> None:
    source = LIVE_ADAPTER.read_text(encoding="utf-8")

    assert '{ state: "none", models: [] }' in source
    assert '{ state: "available", models: [], collection: model.child_collection }' in source
    assert '{ state: "loaded", models: loaded }' in source
    assert '{ state: "empty", models: [] }' in source


def test_information_projection_keeps_source_index_separate_from_technical_revision() -> None:
    source = COCKPIT_PROJECTION.read_text(encoding="utf-8")

    assert "index: item.index_label || null" in source
    assert "technical_revision: item.revision || null" in source
    assert '["Révision technique", text(item.revision, "Non renseignée")]' in source
    assert '["Mis à jour le", text(item.updated_at, "Non renseigné")]' in source
