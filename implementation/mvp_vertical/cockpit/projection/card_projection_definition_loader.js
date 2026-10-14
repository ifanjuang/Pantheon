const REGISTRY_URL = new URL("../registries/card_projection_definitions.json", import.meta.url);

function validateRegistry(payload) {
  if (payload?.schema_id !== "cockpit.card_projection_definitions" || payload?.revision !== 1) {
    throw new Error("Unsupported card projection definition registry");
  }
  if (!Array.isArray(payload.definitions)) {
    throw new Error("Card projection definitions must be an array");
  }

  const definitions = new Map();
  for (const entry of payload.definitions) {
    const entityId = String(entry?.entity_id || "").trim();
    if (!entityId || definitions.has(entityId)) {
      throw new Error("Card projection definition identities must be unique");
    }
    if (entry.entity_type !== "cockpit_space") {
      throw new Error(`Unsupported root projection entity type: ${entry.entity_type}`);
    }
    definitions.set(entityId, Object.freeze({ ...entry }));
  }
  return definitions;
}

export async function loadCardProjectionDefinitions() {
  const response = await fetch(REGISTRY_URL, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Card projection definitions unavailable (${response.status})`);
  }
  const definitions = validateRegistry(await response.json());
  window.PantheonCardProjectionDefinitions = Object.freeze({
    get(entityId) {
      return definitions.get(entityId) || null;
    },
    entityIds: Object.freeze([...definitions.keys()]),
  });
  return window.PantheonCardProjectionDefinitions;
}
