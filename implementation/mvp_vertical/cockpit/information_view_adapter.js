(() => {
  "use strict";

  const STRUCTURAL_KEYS = new Set([
    "title",
    "category",
    "status",
    "index_label",
    "information_date",
    "limits",
    "type_tags",
    "subject_tags",
  ]);
  const schemaCache = new Map();
  const contextCache = new Map();

  function token() {
    return document.getElementById("v2-token")?.value?.trim() || "";
  }

  async function api(path) {
    const auth = token();
    if (!auth) throw new Error("Clé d’accès requise pour lire Information.");
    const response = await fetch(path, {
      headers: { Authorization: `Bearer ${auth}` },
      cache: "no-store",
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || response.statusText || "Erreur Agency Information");
    return payload;
  }

  function currentInformationId() {
    const card = document.querySelector("#v2-stage .v2-card");
    if (!card || card.dataset.family !== "information") return "";
    const entityId = card.querySelector(".v2-entity-id")?.textContent?.trim() || "";
    return entityId.startsWith("information:") ? entityId.slice("information:".length) : "";
  }

  async function informationContext(informationId) {
    const cached = contextCache.get(informationId);
    if (cached) return cached;
    const payload = await api(`../agency/information/${encodeURIComponent(informationId)}/context`);
    const context = payload.information_context || {};
    contextCache.set(informationId, context);
    return context;
  }

  async function backSchema(projectId) {
    const cached = schemaCache.get(projectId);
    if (cached) return cached;
    const payload = await api(`../agency/projects/${encodeURIComponent(projectId)}/information`);
    const schema = payload.card_contract?.back || null;
    if (!schema?.fields) throw new Error("Projection cockpit_back Information indisponible.");
    schemaCache.set(projectId, schema);
    return schema;
  }

  function hasValue(value) {
    return !(value == null || value === "" || (Array.isArray(value) && value.length === 0));
  }

  function formatValue(value) {
    if (Array.isArray(value)) return value.map(String).join("\n");
    if (typeof value === "object" && value !== null) return JSON.stringify(value, null, 2);
    return String(value ?? "");
  }

  function section(field, value) {
    const row = document.createElement("section");
    row.className = "v2-back-section";
    row.dataset.schemaField = field.key;
    const heading = document.createElement("h3");
    heading.textContent = field.title || field.label || field.key;
    const body = document.createElement("p");
    const lines = formatValue(value).split("\n").filter(Boolean);
    if (lines.length > 1) {
      body.className = "v2-back-multiline";
      for (const line of lines) {
        const span = document.createElement("span");
        span.textContent = line;
        body.append(span);
      }
    } else {
      body.textContent = lines[0] || "";
    }
    row.append(heading, body);
    return row;
  }

  async function apply() {
    const informationId = currentInformationId();
    if (!informationId) return;
    const card = document.querySelector("#v2-stage .v2-card");
    if (!card || card.dataset.informationViewPending === informationId) return;
    card.dataset.informationViewPending = informationId;

    try {
      const context = await informationContext(informationId);
      const record = context.current;
      if (!record?.project_id) return;
      const schema = await backSchema(record.project_id);
      const body = card.querySelector(".v2-card-back .v2-back-body");
      if (!body || card.dataset.informationViewApplied === `${informationId}:${record.revision}`) return;

      const title = body.querySelector(".v2-back-title") || document.createElement("h2");
      title.className = "v2-back-title";
      title.textContent = record.title || "Information";
      const nodes = [title];
      for (const field of schema.fields || []) {
        if (STRUCTURAL_KEYS.has(field.key)) continue;
        const value = record[field.key];
        if (!hasValue(value)) continue;
        nodes.push(section(field, value));
      }
      body.replaceChildren(...nodes);
      card.dataset.informationViewApplied = `${informationId}:${record.revision}`;
    } catch (error) {
      console.warn("Information schema projection unavailable", error);
    } finally {
      delete card.dataset.informationViewPending;
    }
  }

  function install() {
    const stage = document.getElementById("v2-stage");
    if (!stage) return;
    void apply();
    new MutationObserver(() => void apply()).observe(stage, { childList: true, subtree: true });
  }

  window.PantheonInformationViewAdapter = Object.freeze({ apply });

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install, { once: true });
  else install();
})();
