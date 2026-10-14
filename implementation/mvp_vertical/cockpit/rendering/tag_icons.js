const REGISTRY_URL = new URL("../registries/tag_registry.json", import.meta.url);
const REGISTRY_SCHEMA = Object.freeze({ id: "cockpit.tag_registry", revision: 1 });
const registries = { type: new Map(), subject: new Map() };
const FALLBACK_PRESENTATION = Object.freeze({
  title: "Tag",
  description: "Tag hors registre de présentation.",
  icon_provider: "material-symbols",
  icon_key: "label",
  color: "slate",
});
let loadPromise = null;

function slug(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function validateRegistry(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new Error("Tag registry must be an object");
  }
  if (payload.schema_id !== REGISTRY_SCHEMA.id || payload.revision !== REGISTRY_SCHEMA.revision) {
    throw new Error("Unsupported tag registry");
  }
  if (!Array.isArray(payload.groups) || !Array.isArray(payload.tags)) {
    throw new Error("Tag registry requires groups and tags");
  }
  const groupIds = new Set(payload.groups.map(group => group?.id).filter(Boolean));
  if (!groupIds.has("type") || !groupIds.has("subject")) {
    throw new Error("Tag registry requires type and subject groups");
  }
  return payload;
}

async function fetchRegistry() {
  const response = await fetch(REGISTRY_URL, { cache: "no-store" });
  if (!response.ok) throw new Error(`Tag registry unavailable (${response.status})`);
  const payload = validateRegistry(await response.json());
  registries.type.clear();
  registries.subject.clear();

  for (const entry of payload.tags) {
    const group = entry?.group;
    if (!registries[group]) continue;
    const key = slug(entry.slug || entry.title);
    if (!key) continue;
    const presentation = entry.presentation || {};
    const normalized = {
      ...entry,
      ...presentation,
      title: entry.title || key,
      description: entry.description || "",
    };
    registries[group].set(key, normalized);
    for (const alias of entry.aliases || []) registries[group].set(slug(alias), normalized);
  }
}

export function loadTagIconRegistries() {
  if (!loadPromise) {
    loadPromise = fetchRegistry()
      .catch(error => console.warn("Tag registry unavailable; using visible fallback icons", error));
  }
  return loadPromise;
}

export function tagPresentation(value, kind = "subject") {
  const label = String(value?.title ?? value?.label ?? value?.name ?? value?.slug ?? value ?? "Tag").trim() || "Tag";
  const registry = kind === "type" ? registries.type : registries.subject;
  const registered = registry.get(slug(value?.slug ?? value)) || null;
  return { ...FALLBACK_PRESENTATION, ...(registered || {}), title: registered?.title || label };
}

export function createTagIcon(presentation) {
  const icon = document.createElement("span");
  icon.className = "tag-icon";
  icon.setAttribute("aria-hidden", "true");
  if (presentation.icon_provider === "radix") {
    icon.classList.add("radix-icon");
    icon.dataset.icon = presentation.icon_key;
  } else {
    icon.classList.add("material-symbols-rounded");
    icon.textContent = presentation.icon_key || FALLBACK_PRESENTATION.icon_key;
  }
  return icon;
}

export function createTagToken(value, kind, { className, legacyClassName = "", labelled = false } = {}) {
  const presentation = tagPresentation(value, kind);
  const node = document.createElement("span");
  node.className = [className, legacyClassName].filter(Boolean).join(" ");
  node.title = presentation.description || presentation.title;
  node.setAttribute("aria-label", presentation.title);
  node.dataset.iconProvider = presentation.icon_provider;
  node.dataset.iconKey = presentation.icon_key;
  if (presentation.color) node.dataset.tokenColor = presentation.color;
  node.append(createTagIcon(presentation));
  if (labelled) {
    const label = document.createElement("span");
    label.className = "tag-label";
    label.textContent = presentation.title;
    node.append(label);
  }
  return node;
}

const API = Object.freeze({ loadTagIconRegistries, tagPresentation, createTagIcon, createTagToken });
if (typeof window !== "undefined") window.PantheonTagIcons = API;
