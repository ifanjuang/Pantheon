(() => {
  "use strict";

  const $ = id => document.getElementById(id);
  const SOURCE_MODES = Object.freeze({
    file: Object.freeze({ source_type: "file", label: "Fichier", placeholder: "Référence gérée : paperless://…, Drive URL, document id…" }),
    link: Object.freeze({ source_type: "link", label: "Lien", placeholder: "https://…" }),
    draft: Object.freeze({ source_type: "draft", label: "Brouillon", placeholder: "Saisir ou coller le brouillon source…" }),
  });

  const state = {
    dialog: null,
    form: null,
    message: null,
    sourceMode: "file",
  };

  function credentials() {
    const token = $("v2-token")?.value?.trim() || "";
    const actor = $("v2-handoff-actor")?.value?.trim() || "";
    if (!token) throw new Error("Clé éditeur requise pour créer une Information.");
    if (!actor) throw new Error("Renseignez l’acteur humain dans le dock Hermès.");
    return { token, actor };
  }

  function currentProjectId() {
    const card = document.querySelector("#v2-stage .v2-card");
    if (!card || card.dataset.family !== "project") return "";
    const entityId = card.querySelector(".v2-entity-id")?.textContent?.trim() || "";
    if (!entityId.startsWith("project:") || entityId.includes(":contacts")) return "";
    return entityId.slice("project:".length);
  }

  function splitList(value) {
    const output = [];
    const seen = new Set();
    for (const part of String(value || "").split(/[\n,;]+/)) {
      const item = part.trim();
      const normalized = item.toLocaleLowerCase("fr-FR");
      if (!item || seen.has(normalized)) continue;
      seen.add(normalized);
      output.push(item);
    }
    return output;
  }

  async function request(path, body) {
    const { token, actor } = credentials();
    const response = await fetch(path, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "X-Pantheon-Actor": actor,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || response.statusText || "Création refusée");
    return payload;
  }

  function field(name, label, { type = "text", value = "", placeholder = "", rows = 0 } = {}) {
    const wrapper = document.createElement("label");
    wrapper.className = "v2-information-create-field";
    const title = document.createElement("span");
    title.textContent = label;
    const input = rows ? document.createElement("textarea") : document.createElement("input");
    input.name = name;
    if (!rows) input.type = type;
    else input.rows = rows;
    input.value = value;
    input.placeholder = placeholder;
    input.autocomplete = "off";
    wrapper.append(title, input);
    return wrapper;
  }

  function modeControl() {
    const wrapper = document.createElement("fieldset");
    wrapper.className = "v2-information-source-modes";
    const legend = document.createElement("legend");
    legend.textContent = "Source";
    wrapper.append(legend);
    for (const [mode, config] of Object.entries(SOURCE_MODES)) {
      const label = document.createElement("label");
      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = "source_mode";
      radio.value = mode;
      radio.checked = mode === state.sourceMode;
      radio.addEventListener("change", () => {
        state.sourceMode = mode;
        refreshSourceField();
      });
      const text = document.createElement("span");
      text.textContent = config.label;
      label.append(radio, text);
      wrapper.append(label);
    }
    return wrapper;
  }

  function sourceFieldNode() {
    const config = SOURCE_MODES[state.sourceMode];
    if (state.sourceMode === "draft") {
      return field("source_value", "Brouillon source", { rows: 8, placeholder: config.placeholder });
    }
    const label = state.sourceMode === "file" ? "Référence du fichier" : "Lien";
    return field("source_value", label, { placeholder: config.placeholder });
  }

  function refreshSourceField() {
    const host = state.form?.querySelector("[data-information-source-field]");
    if (!host) return;
    host.replaceChildren(sourceFieldNode());
    const note = state.form.querySelector("[data-information-source-note]");
    if (note) {
      note.textContent = state.sourceMode === "file"
        ? "Pantheon ne stocke pas le fichier : fournissez une référence issue du binding documentaire actif (Paperless, Drive, etc.)."
        : state.sourceMode === "link"
          ? "Le lien devient la source de référence de cette version."
          : "Le texte du brouillon est stocké comme source de cette première version.";
    }
  }

  function ensureDialog() {
    if (state.dialog) return state.dialog;
    const dialog = document.createElement("dialog");
    dialog.className = "v2-information-create-dialog";

    const shell = document.createElement("div");
    shell.className = "v2-information-create-shell";
    const header = document.createElement("header");
    const heading = document.createElement("div");
    const eyebrow = document.createElement("p");
    eyebrow.className = "eyebrow";
    eyebrow.textContent = "INFORMATION · NOUVELLE SÉRIE";
    const title = document.createElement("h2");
    title.textContent = "Créer une information";
    heading.append(eyebrow, title);
    const close = document.createElement("button");
    close.type = "button";
    close.textContent = "Fermer";
    close.addEventListener("click", () => dialog.close());
    header.append(heading, close);

    const form = document.createElement("form");
    form.className = "v2-information-create-form";
    form.append(
      modeControl(),
      field("title", "Titre", { placeholder: "Ex. PLU — Zone UDb" }),
      field("category", "Catégorie", { placeholder: "PLU, Compte rendu, Email, Étude…" }),
      field("index_label", "Indice", { value: "A01" }),
      field("information_date", "Date", { type: "date" })
    );
    const sourceHost = document.createElement("div");
    sourceHost.dataset.informationSourceField = "true";
    form.append(sourceHost);
    const sourceNote = document.createElement("p");
    sourceNote.className = "v2-information-source-note";
    sourceNote.dataset.informationSourceNote = "true";
    form.append(sourceNote);
    form.append(
      field("source_version", "Version source", { placeholder: "Optionnel" }),
      field("summary", "Résumé", { rows: 3 }),
      field("details", "Informations détaillées", { rows: 7 }),
      field("author", "Auteur", { placeholder: "Optionnel" }),
      field("type_tags", "Tags type", { rows: 2, placeholder: "email, étude, cctp…" }),
      field("subject_tags", "Tags sujet", { rows: 2, placeholder: "re2020, erp, structure…" }),
      field("limits", "Limites", { rows: 2, placeholder: "consultatif, hypothèse, contractuel…" })
    );

    const status = document.createElement("label");
    status.className = "v2-information-create-field";
    const statusLabel = document.createElement("span");
    statusLabel.textContent = "Statut initial";
    const select = document.createElement("select");
    select.name = "status";
    for (const [value, label] of [["draft", "Brouillon"], ["in_progress", "En rédaction"]]) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      select.append(option);
    }
    status.append(statusLabel, select);
    form.append(status);

    const message = document.createElement("p");
    message.className = "v2-information-create-message";
    message.setAttribute("aria-live", "polite");

    const actions = document.createElement("footer");
    const cancel = document.createElement("button");
    cancel.type = "button";
    cancel.textContent = "Annuler";
    cancel.addEventListener("click", () => dialog.close());
    const submit = document.createElement("button");
    submit.type = "submit";
    submit.className = "primary-action";
    submit.textContent = "Créer";
    actions.append(cancel, submit);

    form.addEventListener("submit", event => {
      event.preventDefault();
      void create().catch(error => {
        message.textContent = error.message || String(error);
        message.dataset.error = "true";
      });
    });

    shell.append(header, form, message, actions);
    dialog.append(shell);
    document.body.append(dialog);
    state.dialog = dialog;
    state.form = form;
    state.message = message;
    refreshSourceField();
    return dialog;
  }

  function formValue(name) {
    return state.form?.elements.namedItem(name)?.value?.trim?.() || "";
  }

  async function create() {
    const projectId = currentProjectId();
    if (!projectId) throw new Error("Ouvrez une Carte Projet pour créer une Information.");
    const sourceValue = formValue("source_value");
    if (!sourceValue) throw new Error("Une source est requise : fichier, lien ou brouillon.");
    const title = formValue("title");
    const category = formValue("category");
    const indexLabel = formValue("index_label");
    if (!title || !category || !indexLabel) throw new Error("Titre, catégorie et indice sont requis.");

    const mode = SOURCE_MODES[state.sourceMode];
    const payload = {
      title,
      category,
      source_type: mode.source_type,
      source_ref: state.sourceMode === "draft" ? null : sourceValue,
      source_note: state.sourceMode === "draft" ? sourceValue : null,
      source_version: formValue("source_version") || null,
      index_label: indexLabel,
      information_date: formValue("information_date") || null,
      summary: formValue("summary"),
      details: formValue("details"),
      author: formValue("author") || null,
      status: formValue("status") || "draft",
      limits: splitList(formValue("limits")),
      type_tags: splitList(formValue("type_tags")),
      subject_tags: splitList(formValue("subject_tags")),
    };

    const submit = state.dialog.querySelector('button[type="submit"]');
    submit.disabled = true;
    state.message.textContent = "Création…";
    state.message.dataset.error = "false";
    try {
      await request(`../agency/projects/${encodeURIComponent(projectId)}/information`, payload);
      state.dialog.close();
      state.form.reset();
      state.sourceMode = "file";
      refreshSourceField();
      $("v2-load")?.click();
    } finally {
      submit.disabled = false;
    }
  }

  function open() {
    if (!currentProjectId()) throw new Error("Ouvrez une Carte Projet pour créer une Information.");
    const dialog = ensureDialog();
    state.message.textContent = "Fichier, lien ou brouillon : la source définit la première version A01.";
    state.message.dataset.error = "false";
    dialog.showModal();
  }

  function blankCard() {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "v2-information-create-card";
    button.dataset.informationCreateCard = "true";
    const mark = document.createElement("span");
    mark.className = "v2-information-create-mark";
    mark.textContent = "+";
    const copy = document.createElement("span");
    const title = document.createElement("strong");
    title.textContent = "Nouvelle information";
    const detail = document.createElement("small");
    detail.textContent = "Fichier · Lien · Brouillon";
    copy.append(title, detail);
    button.append(mark, copy);
    button.addEventListener("click", () => void open().catch(error => window.alert(error.message || String(error))));
    return button;
  }

  function ensureBlankCard() {
    const projectId = currentProjectId();
    const body = document.querySelector("#v2-stage .v2-card-back .v2-back-body");
    if (!projectId || !body) return;
    if (body.querySelector('[data-information-create-card="true"]')) return;
    body.append(blankCard());
  }

  function install() {
    const stage = $("v2-stage");
    if (!stage) return;
    ensureBlankCard();
    new MutationObserver(ensureBlankCard).observe(stage, { childList: true, subtree: true });
  }

  window.PantheonInformationCreate = Object.freeze({ open });

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install, { once: true });
  else install();
})();