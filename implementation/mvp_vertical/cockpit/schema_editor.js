(() => {
  "use strict";

  const $ = id => document.getElementById(id);
  const GROUP_LABELS = Object.freeze({
    identity: "Identité",
    business: "Projet",
    classification: "Classement",
    programme: "Programme",
    urbanisme: "Urbanisme",
    chantier: "Chantier",
    reglementaire: "Réglementaire",
    content: "Contenu",
    state: "État",
    source: "Source",
    lineage: "Historique",
  });

  const state = {
    dialog: null,
    form: null,
    title: null,
    message: null,
    entity: null,
    schema: null,
    profile: null,
    fields: [],
  };

  const key = prefix => `${prefix}-${globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`}`;

  function credentials() {
    const token = $("v2-token")?.value?.trim() || "";
    const actor = $("v2-handoff-actor")?.value?.trim() || "";
    if (!token) throw new Error("Clé éditeur requise pour cette modification.");
    if (!actor) throw new Error("Renseignez l’acteur humain dans le dock Hermès.");
    return { token, actor };
  }

  async function request(path, { method = "GET", body = null } = {}) {
    const { token, actor } = credentials();
    const headers = {
      Authorization: `Bearer ${token}`,
      "X-Pantheon-Actor": actor,
    };
    if (body !== null) headers["Content-Type"] = "application/json";
    const response = await fetch(path, {
      method,
      headers,
      body: body === null ? undefined : JSON.stringify(body),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || response.statusText || "Erreur Agency Data");
    return payload;
  }

  function currentCard() {
    return document.querySelector("#v2-stage .v2-card");
  }

  function currentEntityId() {
    return currentCard()?.querySelector(".v2-entity-id")?.textContent?.trim() || "";
  }

  function sameValue(a, b) {
    return JSON.stringify(a ?? null) === JSON.stringify(b ?? null);
  }

  function localizedNumber(value) {
    if (value == null || value === "") return "";
    return new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 8 }).format(Number(value));
  }

  function parseNumber(value, field) {
    const raw = String(value ?? "").trim();
    if (!raw) {
      if (field.nullable || !field.required) return null;
      throw new Error(`${field.label || field.key} est requis.`);
    }
    const normalized = raw.replace(/[\s\u00a0\u202f]/g, "").replace(",", ".");
    const parsed = Number(normalized);
    if (!Number.isFinite(parsed)) throw new Error(`${field.label || field.key} doit être un nombre.`);
    return parsed;
  }

  function parseString(value, field) {
    const parsed = String(value ?? "").trim();
    if (!parsed && field.required) throw new Error(`${field.label || field.key} est requis.`);
    return parsed;
  }

  function parseStringList(value) {
    const output = [];
    const seen = new Set();
    for (const part of String(value ?? "").split(/[\n,;]+/)) {
      const item = part.trim();
      const normalized = item.toLocaleLowerCase("fr-FR");
      if (!item || seen.has(normalized)) continue;
      seen.add(normalized);
      output.push(item);
    }
    return output;
  }

  function parseDate(value, field) {
    const parsed = String(value ?? "").trim();
    if (!parsed) {
      if (field.nullable || !field.required) return null;
      throw new Error(`${field.label || field.key} est requis.`);
    }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(parsed)) throw new Error(`${field.label || field.key} doit être une date ISO.`);
    return parsed;
  }

  const renderers = new Map();

  function registerRenderer(type, renderer) {
    renderers.set(type, Object.freeze(renderer));
  }

  function baseInput(field, value) {
    const node = document.createElement(field.editor?.widget === "textarea" ? "textarea" : "input");
    if (node instanceof HTMLTextAreaElement) node.rows = 4;
    else node.type = "text";
    node.value = value == null ? "" : String(value);
    return node;
  }

  registerRenderer("string", {
    render(field, value) { return baseInput(field, value); },
    read(field, input) { return parseString(input.value, field); },
  });

  registerRenderer("enum", {
    render(field, value) {
      const select = document.createElement("select");
      if (!field.required) {
        const empty = document.createElement("option");
        empty.value = "";
        empty.textContent = "—";
        select.append(empty);
      }
      for (const optionValue of field.editor?.values || field.values || []) {
        const option = document.createElement("option");
        option.value = String(optionValue);
        option.textContent = String(optionValue);
        select.append(option);
      }
      select.value = value == null ? "" : String(value);
      return select;
    },
    read(field, input) { return parseString(input.value, field) || null; },
  });

  registerRenderer("number", {
    render(field, value) {
      const input = document.createElement("input");
      input.type = "text";
      input.inputMode = "decimal";
      input.value = localizedNumber(value);
      return input;
    },
    read(field, input) { return parseNumber(input.value, field); },
  });

  registerRenderer("date", {
    render(_field, value) {
      const input = document.createElement("input");
      input.type = "date";
      input.value = value == null ? "" : String(value).slice(0, 10);
      return input;
    },
    read(field, input) { return parseDate(input.value, field); },
  });

  registerRenderer("string_list", {
    render(_field, value) {
      const input = document.createElement("textarea");
      input.rows = 3;
      input.value = Array.isArray(value) ? value.join("\n") : "";
      input.placeholder = "Une valeur par ligne";
      return input;
    },
    read(_field, input) { return parseStringList(input.value); },
  });

  function projectId(entityId) {
    if (!entityId.startsWith("project:") || entityId.includes(":contacts")) throw new Error("Cette action exige une Carte Projet.");
    return entityId.slice("project:".length);
  }

  function informationId(entityId) {
    if (!entityId.startsWith("information:")) throw new Error("Cette action exige une Carte Information.");
    return entityId.slice("information:".length);
  }

  const PROFILES = Object.freeze({
    project: Object.freeze({
      matches(entityId) {
        return entityId.startsWith("project:") && !entityId.includes(":contacts");
      },
      editable() { return true; },
      async load(entityId) {
        const id = projectId(entityId);
        const [schemaPayload, projectPayload] = await Promise.all([
          request("../agency/schema/project?view=edit"),
          request(`../agency/projects/${encodeURIComponent(id)}`),
        ]);
        return { entity: projectPayload.project, schema: schemaPayload.schema };
      },
      title(entity) { return entity.display_name || entity.code || entity.project_id; },
      value(entity, field) {
        return field.storage === "attributes" ? entity.attributes?.[field.key] : entity[field.key];
      },
      serialize(entity, changes) {
        const core = {};
        const attributes = { ...(entity.attributes || {}) };
        let attributesChanged = false;
        for (const [key, change] of Object.entries(changes)) {
          if (change.field.storage === "attributes") {
            attributes[key] = change.value;
            attributesChanged = true;
          } else if (change.field.storage === "core") {
            core[key] = change.value;
          }
        }
        if (attributesChanged) core.attributes = attributes;
        return {
          expected_revision: entity.revision,
          idempotency_key: key("schema-edit"),
          ...core,
        };
      },
      async save(entity, payload) {
        const result = await request(`../agency/projects/${encodeURIComponent(entity.project_id)}`, {
          method: "PATCH",
          body: payload,
        });
        return result.project;
      },
      message(entity) { return `Révision ${entity.revision} · PostgreSQL reste la source de vérité.`; },
    }),
    information: Object.freeze({
      matches(entityId) { return entityId.startsWith("information:"); },
      editable(card) { return ["draft", "in_progress"].includes(card?.dataset.status || ""); },
      async load(entityId) {
        const id = informationId(entityId);
        const payload = await request(`../agency/information/${encodeURIComponent(id)}/context`);
        const context = payload.information_context || {};
        const entity = context.current;
        if (!entity || !["draft", "in_progress"].includes(entity.status)) {
          throw new Error("Une Information ACTÉE est immuable. Créez d’abord une nouvelle version.");
        }
        if (!context.edit_schema) throw new Error("Le schéma d’édition Information n’est pas disponible.");
        return { entity, schema: context.edit_schema };
      },
      title(entity) { return entity.title || entity.information_id; },
      value(entity, field) { return entity[field.key]; },
      serialize(entity, changes) {
        const payload = { expected_revision: entity.revision };
        for (const [key, change] of Object.entries(changes)) {
          if (change.field.storage === "core") payload[key] = change.value;
        }
        return payload;
      },
      async save(entity, payload) {
        const result = await request(`../agency/information/${encodeURIComponent(entity.information_id)}`, {
          method: "PATCH",
          body: payload,
        });
        return result.information;
      },
      message(entity) {
        return `${entity.index_label || ""} · révision ${entity.revision} · source et indice se modifient uniquement par Nouvelle version.`;
      },
    }),
  });

  function profileFor(entityId, card = currentCard()) {
    return Object.values(PROFILES).find(profile => profile.matches(entityId) && profile.editable(card)) || null;
  }

  function ensureDialog() {
    if (state.dialog) return state.dialog;
    const dialog = document.createElement("dialog");
    dialog.className = "v2-schema-editor";
    dialog.setAttribute("aria-labelledby", "v2-schema-editor-title");

    const shell = document.createElement("div");
    shell.className = "v2-schema-editor-shell";
    const header = document.createElement("header");
    header.className = "v2-schema-editor-header";
    const heading = document.createElement("div");
    const eyebrow = document.createElement("p");
    eyebrow.className = "eyebrow";
    eyebrow.textContent = "AGENCY DATA · ÉDITION";
    const title = document.createElement("h2");
    title.id = "v2-schema-editor-title";
    heading.append(eyebrow, title);
    const close = document.createElement("button");
    close.type = "button";
    close.className = "v2-schema-editor-close";
    close.textContent = "Fermer";
    close.addEventListener("click", () => dialog.close());
    header.append(heading, close);

    const form = document.createElement("form");
    form.className = "v2-schema-editor-form";
    form.method = "dialog";
    form.addEventListener("submit", event => {
      event.preventDefault();
      void save().catch(error => setMessage(error.message || String(error), true));
    });

    const message = document.createElement("p");
    message.className = "v2-schema-editor-message";
    message.setAttribute("aria-live", "polite");
    const actions = document.createElement("footer");
    actions.className = "v2-schema-editor-actions";
    const cancel = document.createElement("button");
    cancel.type = "button";
    cancel.textContent = "Annuler";
    cancel.addEventListener("click", () => dialog.close());
    const submit = document.createElement("button");
    submit.type = "submit";
    submit.className = "primary-action";
    submit.textContent = "Enregistrer";
    actions.append(cancel, submit);

    shell.append(header, form, message, actions);
    dialog.append(shell);
    document.body.append(dialog);
    state.dialog = dialog;
    state.form = form;
    state.title = title;
    state.message = message;
    return dialog;
  }

  function setMessage(message, error = false) {
    if (!state.message) return;
    state.message.textContent = message || "";
    state.message.dataset.error = error ? "true" : "false";
  }

  function fieldControl(field) {
    const renderer = renderers.get(field.type);
    if (!renderer) return null;
    const wrapper = document.createElement("label");
    wrapper.className = "v2-schema-field";
    const label = document.createElement("span");
    label.className = "v2-schema-field-label";
    label.textContent = field.label || field.key;
    const value = state.profile.value(state.entity, field);
    const input = renderer.render(field, value);
    input.name = field.key;
    input.dataset.fieldKey = field.key;
    input.dataset.storage = field.storage;
    input.disabled = field.mutable === false;
    input.required = Boolean(field.required);
    input.autocomplete = "off";
    const meta = document.createElement("small");
    meta.className = "v2-schema-field-meta";
    meta.textContent = [field.unit, field.storage === "attributes" ? "champ extensible" : null].filter(Boolean).join(" · ");
    wrapper.append(label, input);
    if (meta.textContent) wrapper.append(meta);
    return { wrapper, input, renderer, field, original: value };
  }

  function buildForm() {
    state.form.replaceChildren();
    state.fields = [];
    const groups = new Map();
    for (const field of state.schema?.fields || []) {
      if (field.mutable === false) continue;
      const control = fieldControl(field);
      if (!control) continue;
      const group = field.group || "business";
      if (!groups.has(group)) groups.set(group, []);
      groups.get(group).push(control);
      state.fields.push(control);
    }

    for (const [group, controls] of groups) {
      const section = document.createElement("fieldset");
      section.className = "v2-schema-group";
      const legend = document.createElement("legend");
      legend.textContent = GROUP_LABELS[group] || group;
      section.append(legend);
      for (const control of controls) section.append(control.wrapper);
      state.form.append(section);
    }
  }

  function changedFields() {
    const changes = {};
    for (const control of state.fields) {
      const next = control.renderer.read(control.field, control.input);
      if (sameValue(next, control.original)) continue;
      changes[control.field.key] = { field: control.field, value: next };
    }
    return changes;
  }

  async function save() {
    const changes = changedFields();
    if (!Object.keys(changes).length) {
      setMessage("Aucune modification à enregistrer.");
      return;
    }
    const submit = state.dialog.querySelector('button[type="submit"]');
    submit.disabled = true;
    setMessage("Enregistrement…");
    try {
      const payload = state.profile.serialize(state.entity, changes);
      state.entity = await state.profile.save(state.entity, payload);
      setMessage(`Enregistré · révision ${state.entity.revision}.`);
      state.dialog.close();
      $("v2-load")?.click();
    } finally {
      submit.disabled = false;
    }
  }

  async function openEntity(entityId) {
    const profile = profileFor(entityId, currentCard());
    if (!profile) throw new Error("Cette carte n’expose pas d’édition schema-driven dans son état courant.");
    const dialog = ensureDialog();
    setMessage("Chargement…");
    const loaded = await profile.load(entityId);
    state.profile = profile;
    state.schema = loaded.schema;
    state.entity = loaded.entity;
    state.title.textContent = profile.title(state.entity);
    buildForm();
    setMessage(profile.message(state.entity));
    dialog.showModal();
  }

  function openCurrent() {
    return openEntity(currentEntityId());
  }

  function ensureEditAction() {
    const entityId = currentEntityId();
    const actions = document.querySelector("#v2-stage .v2-card-actions");
    if (!actions) return;
    const existing = actions.querySelector('[data-schema-edit="entity"]');
    const profile = profileFor(entityId, currentCard());
    if (!profile) {
      existing?.remove();
      return;
    }
    if (existing) return;
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "Modifier";
    button.dataset.schemaEdit = "entity";
    button.addEventListener("click", () => {
      button.disabled = true;
      void openCurrent()
        .catch(error => window.alert(error.message || String(error)))
        .finally(() => { button.disabled = false; });
    });
    actions.prepend(button);
  }

  function install() {
    const stage = $("v2-stage");
    if (!stage) return;
    ensureEditAction();
    new MutationObserver(ensureEditAction).observe(stage, { childList: true, subtree: true });
  }

  window.PantheonSchemaEditor = Object.freeze({
    openEntity,
    openCurrent,
    openProject(projectId) { return openEntity(`project:${projectId}`); },
    openInformation(informationId) { return openEntity(`information:${informationId}`); },
    registerRenderer,
    supportedTypes: Object.freeze(Array.from(renderers.keys())),
  });

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install, { once: true });
  else install();
})();