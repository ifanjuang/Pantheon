(() => {
  "use strict";

  const $ = id => document.getElementById(id);
  const SUPPORTED = new Set(["Modifier avec Hermès", "Acter", "Nouvelle version", "Valider", "Refuser", "Inspecter les chunks"]);
  const DECISION_REQUEST_PREFIX = "decision-request:";

  const key = prefix => `${prefix}-${globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`}`;

  function credentials() {
    const token = $("v2-token")?.value?.trim() || "";
    const actor = $("v2-handoff-actor")?.value?.trim() || "";
    if (!token) throw new Error("Clé éditeur requise pour cette action.");
    if (!actor) throw new Error("Renseignez l’acteur humain dans le dock Hermès.");
    return { token, actor };
  }

  function currentIdentity() {
    const card = document.querySelector("#v2-stage :is(.card, .v2-card)");
    const entityId = card?.querySelector(":is(.card-entity-id, .v2-entity-id)")?.textContent?.trim() || "";
    const title = card?.querySelector(":is(.card-title, .v2-card-title)")?.textContent?.trim() || entityId;
    if (!entityId) throw new Error("La carte courante n’expose pas d’identité stable.");
    return { entityId, title };
  }

  function informationId(entityId) {
    if (!entityId.startsWith("information:")) throw new Error("Cette action exige une Carte Information.");
    return entityId.slice("information:".length);
  }

  function workIssueId(entityId) {
    const prefix = "decision:work:";
    if (!entityId.startsWith(prefix)) throw new Error("Cette action exige une Carte Décision issue d’un Travail.");
    return entityId.slice(prefix.length);
  }

  function documentId(entityId) {
    if (!entityId.startsWith("document:")) throw new Error("Cette action exige une Carte Document.");
    return entityId.slice("document:".length);
  }

  function readToken() {
    const token = $("v2-token")?.value?.trim() || "";
    if (!token) throw new Error("Clé de lecture requise pour inspecter les chunks.");
    return token;
  }

  function chunkInspector() {
    let dialog = document.querySelector(".v2-document-chunk-inspector");
    if (dialog) return dialog;
    dialog = document.createElement("dialog");
    dialog.className = "v2-document-chunk-inspector";
    dialog.innerHTML = `
      <div class="v2-document-chunk-shell">
        <header class="v2-document-chunk-header">
          <div><p class="v2-document-chunk-eyebrow">Document · contenu dérivé</p><h2>Chunks</h2></div>
          <button type="button" data-chunk-close aria-label="Fermer">×</button>
        </header>
        <form class="v2-document-chunk-filters">
          <label>Type
            <select name="content_type">
              <option value="">Tous</option><option value="heading">Titres</option>
              <option value="paragraph">Texte</option><option value="table">Tableaux</option>
              <option value="list">Listes</option><option value="figure_caption">Légendes</option>
              <option value="page_fragment">Fragments</option>
            </select>
          </label>
          <label class="v2-document-chunk-check"><input type="checkbox" name="flagged_only"> Signalés uniquement</label>
        </form>
        <p class="v2-document-chunk-note">Le score de proximité dépend d’une requête et n’est pas une qualité permanente du chunk.</p>
        <p class="v2-document-chunk-message" aria-live="polite"></p>
        <div class="v2-document-chunk-list"></div>
        <footer class="v2-document-chunk-pagination">
          <button type="button" data-chunk-previous>Précédents</button>
          <span data-chunk-range></span>
          <button type="button" data-chunk-next>Suivants</button>
        </footer>
      </div>`;
    document.body.append(dialog);
    dialog.querySelector("[data-chunk-close]").addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", event => {
      if (event.target === dialog) dialog.close();
    });
    return dialog;
  }

  function pageLabel(chunk) {
    if (!chunk.page_start) return "Page non localisée";
    return chunk.page_end && chunk.page_end !== chunk.page_start
      ? `Pages ${chunk.page_start}–${chunk.page_end}`
      : `Page ${chunk.page_start}`;
  }

  function renderChunks(dialog, payload) {
    const list = dialog.querySelector(".v2-document-chunk-list");
    list.replaceChildren();
    for (const chunk of payload.chunks || []) {
      const article = document.createElement("article");
      article.className = "v2-document-chunk-item";
      const flags = (chunk.quality_flags || []).join(" · ") || "Aucun signal structurel";
      const section = (chunk.section_path || []).join(" › ") || chunk.parent_heading || "Section non renseignée";
      article.innerHTML = `
        <header><strong></strong><span></span></header>
        <p class="v2-document-chunk-section"></p>
        <blockquote></blockquote>
        <dl>
          <div><dt>Retrieval</dt><dd></dd></div>
          <div><dt>Vérification source</dt><dd></dd></div>
          <div><dt>Signaux</dt><dd></dd></div>
          <div><dt>Localisateur</dt><dd></dd></div>
        </dl>`;
      article.querySelector("strong").textContent = chunk.chunk_ref;
      article.querySelector("header span").textContent = `${pageLabel(chunk)} · ${chunk.content_type}`;
      article.querySelector(".v2-document-chunk-section").textContent = section;
      article.querySelector("blockquote").textContent = chunk.body;
      const values = article.querySelectorAll("dd");
      values[0].textContent = chunk.retrieval_status === "indexed" ? "Indexé" : chunk.retrieval_status;
      values[1].textContent = chunk.verification_status === "not_observed" ? "Non observée" : chunk.verification_status;
      values[2].textContent = flags;
      values[3].textContent = chunk.structural_locator;
      list.append(article);
    }
    if (!list.childElementCount) {
      const empty = document.createElement("p");
      empty.className = "v2-document-chunk-empty";
      empty.textContent = "Aucun chunk ne correspond à ces filtres.";
      list.append(empty);
    }
    const start = payload.total ? payload.offset + 1 : 0;
    const end = Math.min(payload.offset + (payload.chunks || []).length, payload.total);
    dialog.querySelector("[data-chunk-range]").textContent = `${start}–${end} sur ${payload.total}`;
    dialog.querySelector("[data-chunk-previous]").disabled = payload.offset === 0;
    dialog.querySelector("[data-chunk-next]").disabled = end >= payload.total;
  }

  async function inspectChunks() {
    const { entityId, title } = currentIdentity();
    const id = documentId(entityId);
    const dialog = chunkInspector();
    const filters = dialog.querySelector(".v2-document-chunk-filters");
    const message = dialog.querySelector(".v2-document-chunk-message");
    const limit = 20;
    let offset = 0;

    async function load() {
      const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
      const type = new FormData(filters).get("content_type");
      if (type) params.set("content_type", type);
      if (filters.elements.flagged_only.checked) params.set("flagged_only", "true");
      message.textContent = "Chargement…";
      const response = await fetch(`../documents/${encodeURIComponent(id)}/chunks?${params}`, {
        headers: { Authorization: `Bearer ${readToken()}` },
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || response.statusText);
      renderChunks(dialog, payload);
      message.textContent = `${title} · compilation ${payload.compilation_id}`;
    }

    filters.onchange = () => { offset = 0; void load().catch(error => { message.textContent = error.message; }); };
    const reload = () => void load().catch(error => { message.textContent = error.message; });
    dialog.querySelector("[data-chunk-previous]").onclick = () => { offset = Math.max(0, offset - limit); reload(); };
    dialog.querySelector("[data-chunk-next]").onclick = () => { offset += limit; reload(); };
    dialog.showModal();
    await load();
  }

  async function request(path, { method = "GET", body = null } = {}) {
    const { token, actor } = credentials();
    const headers = {
      Authorization: `Bearer ${token}`,
      "X-Pantheon-Actor": actor,
      "X-Pantheon-Human-Actor": actor,
    };
    if (body !== null) headers["Content-Type"] = "application/json";
    const response = await fetch(path, {
      method,
      headers,
      body: body === null ? undefined : JSON.stringify(body),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || response.statusText);
    return payload;
  }

  function nextIndex(value) {
    const match = String(value || "").trim().match(/^([A-Z]+)(\d+)$/i);
    if (!match) return "A01";
    const width = Math.max(2, match[2].length);
    return `${match[1].toUpperCase()}${String(Number(match[2]) + 1).padStart(width, "0")}`;
  }

  function reloadProject() {
    $("v2-load")?.click();
  }

  async function informationContextForCurrent() {
    const { entityId, title } = currentIdentity();
    const id = informationId(entityId);
    const payload = await request(`../agency/information/${encodeURIComponent(id)}/context`);
    const context = payload.information_context || {};
    if (!context.current) throw new Error("L’Information courante n’est plus disponible.");
    return { id, title, context, current: context.current };
  }

  async function prepareHermesEdit() {
    const { title, current } = await informationContextForCurrent();
    if (!["draft", "in_progress"].includes(current.status)) {
      throw new Error("Hermès ne peut préparer une modification que sur une version de travail.");
    }
    const instruction = window.prompt(
      `Que doit faire Hermès sur « ${title} » ?`,
      "Améliorer, détailler et développer cette version de travail sans modifier ce qui est ACTÉ."
    );
    if (!instruction?.trim()) return;
    const question = $("v2-handoff-question");
    const descendants = $("v2-handoff-descendants");
    if (!question) throw new Error("Le dock Hermès n’est pas disponible.");
    question.value = instruction.trim();
    question.dispatchEvent(new Event("input", { bubbles: true }));
    if (descendants) descendants.checked = true;
    question.focus();
    $("v2-handoff-prepare")?.click();
  }

  async function actInformation() {
    const { id, title, current } = await informationContextForCurrent();
    if (!["draft", "in_progress"].includes(current.status)) {
      throw new Error("Seule une version de travail peut être actée.");
    }
    if (!window.confirm(`Acter « ${title} » ${current.index_label || ""} ?\n\nCette version deviendra immuable.`)) return;
    await request(`../agency/information/${encodeURIComponent(id)}/act`, {
      method: "POST",
      body: { expected_revision: current.revision },
    });
    reloadProject();
  }

  async function deriveInformation() {
    const { id, title, current: acted } = await informationContextForCurrent();
    if (acted.status !== "acted") throw new Error("La nouvelle version doit dériver d’une Information ACTÉE.");

    const newIndex = window.prompt("Nouvel indice", nextIndex(acted.index_label));
    if (!newIndex?.trim()) return;
    const sourceRef = window.prompt(
      `Nouvelle source pour « ${title} »\n(fichier, email, dossier, URL… ; laisser vide pour une note)`,
      ""
    );
    let sourceNote = null;
    if (!sourceRef?.trim()) {
      sourceNote = window.prompt("Note / brouillon constituant la nouvelle source", "");
      if (!sourceNote?.trim()) return;
    }
    const sourceVersion = window.prompt("Version portée par la source (optionnel)", "") || null;

    await request(`../agency/information/${encodeURIComponent(id)}/working-version`, {
      method: "POST",
      body: {
        new_index_label: newIndex.trim(),
        source_ref: sourceRef?.trim() || null,
        source_note: sourceNote?.trim() || null,
        source_version: sourceVersion?.trim() || null,
      },
    });
    reloadProject();
  }

  async function decide(action) {
    const { entityId, title } = currentIdentity();
    const issueId = workIssueId(entityId);
    const snapshot = await request(`../work/issues/${encodeURIComponent(issueId)}/decision`);
    const issue = snapshot.work_issue;
    if (!snapshot.decision_available || issue?.status !== "review") {
      throw new Error("Cette décision n’est plus disponible dans l’état courant du Travail.");
    }

    const validate = action === "Valider";
    const message = validate
      ? `Valider « ${title} » et clôturer le Travail comme répondu ?`
      : `Refuser « ${title} » et renvoyer le Travail en cours ?`;
    if (!window.confirm(message)) return;

    await request(`../work/issues/${encodeURIComponent(issueId)}/decision/${validate ? "validate" : "refuse"}`, {
      method: "POST",
      body: {
        expected_version: issue.version,
        idempotency_key: key(validate ? "decision-validate" : "decision-refuse"),
      },
    });
    reloadProject();
  }

  async function runAction(label) {
    if (label === "Inspecter les chunks") return inspectChunks();
    if (label === "Modifier avec Hermès") return prepareHermesEdit();
    if (label === "Acter") return actInformation();
    if (label === "Nouvelle version") return deriveInformation();
    if (label === "Valider" || label === "Refuser") return decide(label);
  }

  function hasCompiledDocument(card) {
    const sections = [...(card?.querySelectorAll?.(".v2-back-section") || [])];
    const extraction = sections.find(section => section.querySelector("h3")?.textContent?.trim() === "Extraction structurée");
    if (!extraction) return false;
    const heading = extraction.querySelector("h3")?.textContent || "";
    const status = extraction.textContent.replace(heading, "").trim().toLowerCase();
    return Boolean(status && !["non disponible", "failed", "échec"].includes(status));
  }

  function enableRenderedActions(root = document) {
    for (const button of root.querySelectorAll?.(":is(.card-actions, .v2-card-actions) button") || []) {
      const card = button.closest?.(":is(.card, .v2-card)");
      const entityId = card?.querySelector(":is(.card-entity-id, .v2-entity-id)")?.textContent?.trim() || "";
      if (entityId.startsWith(DECISION_REQUEST_PREFIX)) continue;
      const label = button.textContent?.trim();
      if (!SUPPORTED.has(label)) continue;
      if (label === "Inspecter les chunks" && !hasCompiledDocument(button.closest(":is(.card, .v2-card)"))) {
        button.remove();
        continue;
      }
      button.disabled = false;
      button.title = "";
      button.dataset.cardAction = label;
    }
  }

  function install() {
    const stage = $("v2-stage");
    if (!stage) return;
    enableRenderedActions(stage);
    new MutationObserver(() => enableRenderedActions(stage)).observe(stage, { childList: true, subtree: true });
    stage.addEventListener("click", event => {
      const button = event.target.closest?.("button[data-card-action]");
      if (!button) return;
      event.preventDefault();
      button.disabled = true;
      void runAction(button.dataset.cardAction)
        .catch(error => window.alert(error.message || String(error)))
        .finally(() => enableRenderedActions(stage));
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install, { once: true });
  else install();
})();