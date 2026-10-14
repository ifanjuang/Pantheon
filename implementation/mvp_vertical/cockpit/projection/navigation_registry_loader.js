const REGISTRY_URL = new URL("../registries/navigation_registry.json", import.meta.url);
const SCHEMA_ID = "cockpit.navigation.registry";
const SCHEMA_REVISION = 1;
const ALLOWED_SOURCES = new Set([
  "pending_change_candidates",
  "decision_requests",
  "current_runs",
  "projects",
  "category_roots",
  "workspace_roots",
  "tools",
]);

let loadPromise = null;

function deepFreeze(value) {
  if (!value || typeof value !== "object" || Object.isFrozen(value)) return value;
  Object.freeze(value);
  for (const child of Object.values(value)) deepFreeze(child);
  return value;
}

function validate(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new Error("Navigation registry must be an object");
  }
  if (payload.schema_id !== SCHEMA_ID || payload.revision !== SCHEMA_REVISION) {
    throw new Error(`Unsupported navigation registry: ${String(payload.schema_id)}@${String(payload.revision)}`);
  }

  const root = payload.root_collection;
  if (!root || typeof root.id !== "string" || !root.id.trim() || !Array.isArray(root.items)) {
    throw new Error("Navigation registry requires one root collection with items");
  }

  const ids = new Set();
  for (const item of root.items) {
    if (!item || typeof item.id !== "string" || !item.id.startsWith("space:")) {
      throw new Error("Navigation root items require stable space identities");
    }
    if (ids.has(item.id)) throw new Error(`Duplicate navigation root: ${item.id}`);
    ids.add(item.id);

    if (!Array.isArray(item.sources) || !item.sources.length) {
      throw new Error(`Navigation root ${item.id} requires at least one abstract source`);
    }
    for (const source of item.sources) {
      if (!ALLOWED_SOURCES.has(source)) throw new Error(`Unknown navigation source: ${source}`);
    }
  }

  return deepFreeze(payload);
}

export async function loadNavigationRegistry() {
  if (!loadPromise) {
    loadPromise = fetch(REGISTRY_URL, { cache: "no-store" })
      .then(response => {
        if (!response.ok) throw new Error(`Navigation registry unavailable (${response.status})`);
        return response.json();
      })
      .then(validate)
      .then(registry => {
        window.PantheonNavigationRegistry = registry;
        return registry;
      });
  }
  return loadPromise;
}

export function navigationRoot(registry = window.PantheonNavigationRegistry) {
  if (!registry) throw new Error("Navigation registry has not been loaded");
  return {
    collectionId: registry.root_collection.id,
    itemIds: registry.root_collection.items.map(item => item.id),
  };
}

export function navigationSources(spaceId, registry = window.PantheonNavigationRegistry) {
  const item = registry?.root_collection?.items?.find(entry => entry.id === spaceId);
  return item ? item.sources.slice() : [];
}
