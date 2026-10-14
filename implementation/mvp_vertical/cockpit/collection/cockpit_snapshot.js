// Cockpit — CockpitSnapshot contract.
//
// The single projection shape the cockpit consumes, whatever produces it (demo
// fixture, live renderer, or a future server endpoint). Pure data: no DOM, no
// Swiper, no rendering.
//
//   {
//     schema: { id, revision },
//     generated_at, revision, source,
//     space: { id, title },
//     collection: { id, title, can_create },
//     items: [ { id, title, ... } ],
//     navigation: { active_index, active_entity_id, path },
//     warnings: []
//   }
//
// `schema.revision` identifies the technical contract revision. The top-level
// `revision` remains the revision of the projected data. Neither is a product
// generation or an authority status.
//
// The cockpit refuses a snapshot it does not understand instead of guessing:
// an incompatible payload stays visible as a refusal, never a silent success.
//
// `actions` and `schemas` are reserved for server-owned contracts. They are
// carried through untouched and deliberately NOT interpreted here: the cockpit
// displays what a server exposes, it does not decide what is authorized.
//
//   visible != authorized

export const SNAPSHOT_SCHEMA_ID = "cockpit.snapshot";
export const SNAPSHOT_SCHEMA_REVISION = 1;

const REFUSALS = Object.freeze({
  NOT_AN_OBJECT: "snapshot_not_an_object",
  INCOMPATIBLE_SCHEMA: "snapshot_incompatible_schema",
  INVALID_ITEMS: "snapshot_invalid_items",
  ITEM_WITHOUT_IDENTITY: "snapshot_item_without_identity",
});

export const SNAPSHOT_REFUSALS = REFUSALS;

export function createSnapshot({
  space = null,
  collection = null,
  items = [],
  index = 0,
  path = [],
  warnings = [],
  revision = null,
  source = "unknown",
  generatedAt = null,
  actions = null,
  schemas = null,
} = {}) {
  const list = Array.isArray(items) ? items : [];
  const activeIndex = list.length ? clamp(index, 0, list.length - 1) : -1;

  const snapshot = {
    schema: {
      id: SNAPSHOT_SCHEMA_ID,
      revision: SNAPSHOT_SCHEMA_REVISION,
    },
    generated_at: generatedAt || new Date().toISOString(),
    revision,
    source,
    space: space ? { id: space.id ?? null, title: space.title ?? "" } : null,
    collection: {
      id: collection?.id ?? null,
      title: collection?.title ?? "",
      can_create: Boolean(collection?.canCreate ?? collection?.can_create),
    },
    items: list,
    navigation: {
      active_index: activeIndex,
      active_entity_id: activeIndex >= 0 ? list[activeIndex]?.id ?? null : null,
      path: Array.isArray(path) ? path.slice() : [],
    },
    warnings: Array.isArray(warnings) ? warnings.slice() : [],
  };

  if (actions) snapshot.actions = actions;
  if (schemas) snapshot.schemas = schemas;
  return snapshot;
}

export function readSnapshot(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return refusal(REFUSALS.NOT_AN_OBJECT, "A snapshot must be an object.");
  }
  const schema = payload.schema;
  if (
    !schema
    || typeof schema !== "object"
    || Array.isArray(schema)
    || schema.id !== SNAPSHOT_SCHEMA_ID
    || schema.revision !== SNAPSHOT_SCHEMA_REVISION
  ) {
    return refusal(
      REFUSALS.INCOMPATIBLE_SCHEMA,
      `Expected ${SNAPSHOT_SCHEMA_ID} revision ${SNAPSHOT_SCHEMA_REVISION}, received ${String(schema?.id)} revision ${String(schema?.revision)}.`,
    );
  }
  if (!Array.isArray(payload.items)) {
    return refusal(REFUSALS.INVALID_ITEMS, "`items` must be an array.");
  }
  const orphan = payload.items.findIndex(item => !item || item.id == null || item.id === "");
  if (orphan >= 0) {
    return refusal(
      REFUSALS.ITEM_WITHOUT_IDENTITY,
      `Item at index ${orphan} has no stable identity.`,
    );
  }
  return { ok: true, snapshot: payload };
}

export function collectionOf(snapshot) {
  return {
    id: snapshot.collection?.id ?? null,
    title: snapshot.collection?.title ?? "",
    canCreate: Boolean(snapshot.collection?.can_create),
    spaceId: snapshot.space?.id ?? null,
  };
}

export function activeIndexOf(snapshot) {
  const index = snapshot.navigation?.active_index;
  return Number.isInteger(index) && index >= 0 ? index : 0;
}

function refusal(reason, detail) {
  return { ok: false, reason, detail };
}

function clamp(value, min, max) {
  const numeric = Number.isFinite(value) ? value : min;
  return Math.max(min, Math.min(max, numeric));
}
