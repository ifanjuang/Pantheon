(() => {
  "use strict";

  const $ = id => document.getElementById(id);
  const GROUPS = Object.freeze([
    "Maîtrise d’ouvrage",
    "Équipe de maîtrise d’œuvre",
    "Bureaux d’études",
    "Bureau de contrôle",
    "SSI",
    "Entreprises de travaux",
    "Autres intervenants",
  ]);

  const state = {
    dialog: null,
    rows: null,
    title: null,
    message: null,
    project: null,
  };

  const key = prefix => `${prefix}-${globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`}`;

  function credentials() {
    const token = $("v2-token")?.value?.trim() || "";
    const actor = $("v2-handoff-actor")?.value?.trim() || "";
    if (!token) throw new Error("Clé éditeur requise pour modifier les contacts.");
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

  function currentContactsEntity() {
    const entityId = document.querySelector("#v2-stage .v2-entity-id")?.textContent?.trim() || "";
    const match = entityId.match(/^project:(.+):contacts$/);
    if (!match) throw new Error("Cette action exige la Carte Contacts d’un Projet.");
    return { entityId, projectId: match[1] };
  }

  function field(name, value = "", { type = "text", placeholder = "" } = {}) {
    const input = document.createElement("input");
    input.name = name;
    input.type = type;
    input.value = value ?? "";
    input.placeholder = placeholder;
    input.autocomplete = "off";
    return input;
  }

  function row(contact = {}) {
    const item = document.createElement("section");
    item.className = "v2-contact-editor-row";

    const group = document.createElement("select");
    group.name = "group";
    for (const label of GROUPS) {
      const option = document.createElement("option");
      option.value = label;
      option.textContent = label;
      group.append(option);
    }
    group.value = GROUPS.includes(contact.group) ? contact.group : "Autres intervenants";

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "v2-contact-editor-remove";
    remove.textContent = "Supprimer";
    remove.addEventListener("click", () => item.remove());

    const head = document.createElement("div");
    head.className = "v2-contact-editor-row-head";
    head.append(group, remove);

    const grid = document.createElement("div");
    grid.className = "v2-contact-editor-grid";
    const inputs = [
      ["name", "Nom / personne", contact.name],
      ["organization", "Société", contact.organization],
      ["role", "Fonction / rôle", contact.role],
      ["email", "Email", contact.email, "email"],
      ["phone", "Téléphone", contact.phone, "tel"],
      ["address", "Adresse", contact.address],
      ["source_ref", "Source / Google Contact", contact.source_ref],
    ];
    for (const [name, placeholder, value, type] of inputs) {
      const wrapper = document.createElement("label");
      const label = document.createElement("span");
      label.textContent = placeholder;
      wrapper.append(label, field(name, value, { type: type || "text", placeholder }));
      grid.append(wrapper);
    }

    const notesWrap = document.createElement("label");
    notesWrap.className = "v2-contact-editor-notes";
    const notesLabel = document.createElement("span");
    notesLabel.textContent = "Notes projet";
    const notes = document.createElement("textarea");
    notes.name = "notes";
    notes.rows = 2;
    notes.value = contact.notes ?? "";
    notesWrap.append(notesLabel, notes);
    grid.append(notesWrap);

    item.append(head, grid);
    return item;
  }

  function ensureDialog() {
    if (state.dialog) return state.dialog;
    const dialog = document.createElement("dialog");
    dialog.className = "v2-contacts-editor";

    const shell = document.createElement("div");
    shell.className = "v2-contacts-editor-shell";
    const header = document.createElement("header");
    header.className = "v2-contacts-editor-header";
    const heading = document.createElement("div");
    const eyebrow = document.createElement("p");
    eyebrow.className = "eyebrow";
    eyebrow.textContent = "AGENCY DATA · CONTACTS PROJET";
    const title = document.createElement("h2");
    heading.append(eyebrow, title);
    const close = document.createElement("button");
    close.type = "button";
    close.textContent = "Fermer";
    close.addEventListener("click", () => dialog.close());
    header.append(heading, close);

    const rows = document.createElement("div");
    rows.className = "v2-contacts-editor-rows";

    const add = document.createElement("button");
    add.type = "button";
    add.className = "v2-contacts-editor-add";
    add.textContent = "+ Ajouter un contact";
    add.addEventListener("click", () => rows.append(row()));

    const message = document.createElement("p");
    message.className = "v2-contacts-editor-message";
    message.setAttribute("aria-live", "polite");

    const actions = document.createElement("footer");
    actions.className = "v2-contacts-editor-actions";
    const cancel = document.createElement("button");
    cancel.type = "button";
    cancel.textContent = "Annuler";
    cancel.addEventListener("click", () => dialog.close());
    const save = document.createElement("button");
    save.type = "button";
    save.className = "primary-action";
    save.textContent = "Enregistrer";
    save.addEventListener("click", () => {
      save.disabled = true;
      void persist()
        .catch(error => setMessage(error.message || String(error), true))
        .finally(() => { save.disabled = false; });
    });
    actions.append(cancel, save);

    shell.append(header, rows, add, message, actions);
    dialog.append(shell);
    document.body.append(dialog);
    state.dialog = dialog;
    state.rows = rows;
    state.title = title;
    state.message = message;
    return dialog;
  }

  function setMessage(message, error = false) {
    state.message.textContent = message || "";
    state.message.dataset.error = error ? "true" : "false";
  }

  function clean(value) {
    const output = String(value ?? "").trim();
    return output || null;
  }

  function serialize() {
    const contacts = [];
    for (const item of state.rows.querySelectorAll(".v2-contact-editor-row")) {
      const get = name => item.querySelector(`[name="${name}"]`)?.value;
      const contact = {
        group: get("group") || "Autres intervenants",
        name: clean(get("name")),
        organization: clean(get("organization")),
        role: clean(get("role")),
        email: clean(get("email")),
        phone: clean(get("phone")),
        address: clean(get("address")),
        notes: clean(get("notes")),
        source_ref: clean(get("source_ref")),
      };
      const hasIdentity = contact.name || contact.organization || contact.email || contact.phone;
      if (!hasIdentity) continue;
      contacts.push(Object.fromEntries(Object.entries(contact).filter(([, value]) => value != null)));
    }
    return contacts;
  }

  async function persist() {
    const contacts = serialize();
    setMessage("Enregistrement…");
    const payload = await request(`../agency/projects/${encodeURIComponent(state.project.project_id)}`, {
      method: "PATCH",
      body: {
        expected_revision: state.project.revision,
        idempotency_key: key("contacts-edit"),
        contacts,
      },
    });
    state.project = payload.project;
    state.dialog.close();
    $("v2-load")?.click();
  }

  async function openProject(projectId) {
    const dialog = ensureDialog();
    setMessage("Chargement…");
    const payload = await request(`../agency/projects/${encodeURIComponent(projectId)}`);
    state.project = payload.project;
    state.title.textContent = state.project.display_name || state.project.code || projectId;
    state.rows.replaceChildren();
    for (const contact of state.project.contacts || []) state.rows.append(row(contact));
    if (!(state.project.contacts || []).length) state.rows.append(row());
    setMessage(`Révision ${state.project.revision} · Contacts stockés dans le snapshot du Projet.`);
    dialog.showModal();
  }

  function ensureEditAction() {
    const actions = document.querySelector("#v2-stage .v2-card-actions");
    if (!actions) return;
    const existing = actions.querySelector('[data-contacts-edit="project"]');
    let identity;
    try { identity = currentContactsEntity(); } catch (_) { identity = null; }
    if (!identity) {
      existing?.remove();
      return;
    }
    if (existing) return;
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "Modifier";
    button.dataset.contactsEdit = "project";
    button.addEventListener("click", () => {
      button.disabled = true;
      void openProject(identity.projectId)
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

  window.PantheonContactsEditor = Object.freeze({ openProject, groups: GROUPS });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install, { once: true });
  else install();
})();