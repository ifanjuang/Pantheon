const STATUS = {
  COMPLETE: { label: "Complet", color: "#287652" },
  FOLDER_SCOPED: { label: "Contexte dossier", color: "#247a67" },
  PENDING_SCOPE: { label: "Projet à identifier", color: "#8a5a20" },
  CHECK: { label: "À vérifier", color: "#a76800" },
  SOURCE_ONLY: { label: "Source seule", color: "#6648a8" },
  SOURCE_MISSING: { label: "Source manquante", color: "#a53535" },
  FOLDER: { label: "Dossier", color: "#315d9c" },
};

const PAGE_SIZE = 24;
const WORKSPACE_BASE_PATH = "/workspace/";
const workspaceUrl = (path) => `${WORKSPACE_BASE_PATH}${String(path).replace(/^\/+/, "")}`;
const state = { data: null, workspace: "", status: "all", query: "", path: "", offset: 0, children: null, levelCache: Object.create(null), siblingSwiper: null, requestId: 0 };
const elements = Object.fromEntries(
  ["package-count", "status-counts", "workspace-tabs", "status-filters", "filter-summary", "breadcrumbs", "folder-pager", "page-previous", "page-next", "page-label", "search", "refresh", "loading", "error", "cards", "empty", "tool-links"]
    .map((id) => [id, document.getElementById(id)]),
);

const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;").replaceAll("'", "&#039;");

function tagTemplate(tag) {
  const prefix = String(tag).split(":", 1)[0];
  const family = ["scope", "folder", "workspace", "source", "project_hint", "phase_hint", "family", "revision_hint", "tag"].includes(prefix) ? prefix : "other";
  return `<span class="tag tag-${family}" title="${escapeHtml(tag)}"><small>${escapeHtml(prefix)}</small>${escapeHtml(String(tag).slice(prefix.length + 1))}</span>`;
}

function tagsTemplate(tags, label = "Tags du cartouche") {
  if (!Array.isArray(tags) || tags.length === 0) return "";
  return `<div class="tag-group"><span class="tag-group-label">${escapeHtml(label)}</span><div class="tags" aria-label="${escapeHtml(label)}">${tags.map(tagTemplate).join("")}</div></div>`;
}

function hindsightTagGroups(tags) {
  if (!tags || !Array.isArray(tags.values)) return '<p class="tag-projection-empty">Tags Hindsight non disponibles dans cet ancien état producteur.</p>';
  if (tags.values.length === 0) return '<p class="tag-projection-empty">Aucun tag Hindsight projeté par le producteur.</p>';
  const groups = [
    ["scope", "Portée mémoire"], ["folder", "Chemin Hindsight"],
    ["workspace", "Espace"], ["source", "Source"],
    ["project_hint", "Indice projet"], ["phase_hint", "Indice phase"],
    ["family", "Famille"], ["revision_hint", "Indice de révision"], ["tag", "Sujets"],
  ];
  const stateLabel = tags.projectionState === "LOCAL_PRODUCER_STATE" ? "état local du producteur, sans relecture distante" : "intention locale du producteur, synchronisation non confirmée";
  const values = tags.values || [];
  return `<div class="hindsight-tag-projection"><span class="tag-projection-label">Tags Hindsight · ${escapeHtml(stateLabel)}</span>${groups.map(([prefix, label]) => {
    const selected = values.filter((tag) => tag.startsWith(`${prefix}:`));
    return selected.length ? `<div class="tag-group"><span class="tag-group-label">${escapeHtml(label)}</span><div class="tags">${selected.map(tagTemplate).join("")}</div></div>` : "";
  }).join("")}</div>`;
}

async function loadNavigation() {
  try {
    const response = await fetch(workspaceUrl("api/navigation"), { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const { links } = await response.json();
    if (!Array.isArray(links) || links.length === 0) return;
    elements["tool-links"].replaceChildren(...links.map((link) => {
      const anchor = document.createElement("a");
      anchor.href = link.url;
      anchor.target = "_blank";
      anchor.rel = "noopener noreferrer";
      anchor.textContent = link.label;
      anchor.title = link.description || link.label;
      return anchor;
    }));
    elements["tool-links"].hidden = false;
  } catch (_error) {
    // Navigation is optional and must never prevent document browsing.
  }
}

function fact(label, value, stateClass = "") {
  if (value === null || value === undefined || value === "") return "";
  return `<div class="fact ${stateClass}"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
}

function sourceLink(card) {
  const source = workspaceUrl(`api/source?workspace=${encodeURIComponent(card.workspace)}&path=${encodeURIComponent(card.path)}`);
  const isPdf = String(card.extension || "").replace(/^\./, "").toLocaleLowerCase("en") === "pdf";
  const href = isPdf
    ? workspaceUrl(`vendor/pdfjs/web/viewer.html?file=${encodeURIComponent(source)}`)
    : source;
  return `<a href="${escapeHtml(href)}" target="_blank" rel="noopener">${isPdf ? "Lire le PDF" : "Ouvrir le fichier"}</a>`;
}

function documentCardBody(card) {
  const details = [
    card.document_type,
    card.phase,
    card.index ? `Indice ${card.index}` : "",
    card.document_date,
  ].filter(Boolean);

  const summary = card.summary
    ? `<p class="card-summary">${escapeHtml(card.summary)}</p>`
    : "";

  const facts = [
    fact("Chemin", card.path),
    fact("Source", card.source_present ? (card.source || card.name) : "Manquante", card.source_present ? "" : "fact-alert"),
    fact("Cartouche", card.cartouche_present ? card.cartouche : "Optionnelle", "fact-muted"),
    fact("Identité déclarée", card.document_id),
    fact("Identité technique", card.technical_document_id),
    fact("Hindsight", card.hindsight_status || (card.hindsight_eligible ? "Non synchronisé" : "Non éligible"), card.hindsight_last_error ? "fact-alert" : ""),
    fact(
      "Reclassement",
      card.hindsight_reclassification_required
        ? `${card.hindsight_previous_project || "sans projet"} → ${card.hindsight_requested_project || "sans projet"} — confirmation requise`
        : "",
      "fact-alert",
    ),
    fact(
      "OCR",
      card.hindsight_ocr_needed ? "À demander pour ce fichier" : card.hindsight_extraction_quality,
      card.hindsight_ocr_needed ? "fact-alert" : "fact-muted",
    ),
    fact("Émetteur", card.issuer),
    fact(
      card.revision_mode === "supersedes" ? "Remplace" : card.revision_mode === "supplements" ? "Complète" : "Relation",
      card.revision_of,
      card.revision_target_status === "MISSING" || card.revision_target_status === "AMBIGUOUS" ? "fact-alert" : "",
    ),
  ].join("");

  const openSource = card.source_present
    ? `<div class="card-action">
        ${sourceLink(card)}
        <small>Ouverture depuis le chemin NAS validé par le producer.</small>
      </div>`
    : "";

  const reconcile = card.status === "COMPLETE"
    && card.document_id
    && card.hindsight_representation_candidate === "source"
    ? `<div class="reconcile-action" data-reconcile-document="${escapeHtml(card.document_id)}">
        <label>
          <span>Focus optionnel</span>
          <input type="text" maxlength="2000" data-reconcile-focus placeholder="Ex. vérifier les contradictions de dates">
        </label>
        <button type="button" data-reconcile-button>Réconcilier avec Hermes</button>
        <small>Analyse transitoire de la mémoire Hindsight. La source NAS n’est pas ouverte.</small>
        <div class="reconcile-result" data-reconcile-result hidden></div>
      </div>`
    : "";

  return `
    <div class="document-meta">
      <span class="file-type">${escapeHtml(card.extension || "FILE")}</span>
      ${details.length ? `<span>${escapeHtml(details.join(" · "))}</span>` : ""}
    </div>
    ${summary}
    ${hindsightTagGroups(card.hindsight_tags_projected === null || card.hindsight_tags_projected === undefined ? null : { values: card.hindsight_tags_projected, projectionState: card.hindsight_tags_projection_state })}
    ${tagsTemplate(card.tags, "Tags déclarés dans le cartouche")}
    <div class="facts">${facts}</div>
    ${reconcile}
    ${openSource}
  `;
}

function folderCardBody(card) {
  const summary = card.summary
    ? `<p class="card-summary">${escapeHtml(card.summary)}</p>`
    : `<p class="card-summary muted">Contexte de dossier non renseigné.</p>`;
  const facts = [
    fact("Chemin", card.path),
    fact("Cartouche dossier", card.folder_context_present ? (card.folder_context || "_folder.md") : "Absent", card.folder_context_present ? "" : "fact-muted"),
    fact("Phase", card.phase),
    fact("Projet", card.project),
  ].join("");
  const contextBadge = card.folder_context_present
    ? '<span class="folder-context-state is-present">Cartouche présent</span>'
    : '<span class="folder-context-state is-missing">Sans _folder.md</span>';
  const open = `<button class="folder-open" type="button" data-folder-path="${escapeHtml(card.path)}" aria-label="Descendre dans le dossier ${escapeHtml(card.title || card.name)}">Descendre dans ce dossier <span aria-hidden="true">↓</span></button>`;
  return `
    <div class="document-meta"><span class="file-type">DOSSIER</span>${contextBadge}</div>
    ${open}
    ${summary}
    ${tagsTemplate(card.tags, "Tags du contexte dossier")}
    <div class="facts">${facts}</div>
  `;
}

function cardTemplate(card) {
  const warnings = card.warnings?.length
    ? `<ul class="warnings">${card.warnings.map((warning) => `<li>${escapeHtml(warning)}</li>`).join("")}</ul>`
    : "";
  const body = card.kind === "folder" ? folderCardBody(card) : documentCardBody(card);
  const classes = [
    "card",
    card.kind === "folder" ? "folder-card" : "document-card",
    card.status === "SOURCE_ONLY" ? "source-only" : "",
    card.status === "SOURCE_MISSING" ? "missing-source" : "",
  ].filter(Boolean).join(" ");

  return `<article class="${classes}" data-status="${escapeHtml(card.status)}" data-card-path="${escapeHtml(card.path)}">
    <div class="card-head">
      <div class="card-kicker"><span class="status">${escapeHtml(STATUS[card.status]?.label || card.status)}</span></div>
      <h2>${escapeHtml(card.title || card.name)}</h2>
      <p class="subtitle">${escapeHtml(card.subtitle || "")}</p>
    </div>
    <div class="card-face card-front">${body}<button class="card-turn" type="button" data-card-turn aria-label="Afficher les détails">Détails ↗</button></div>
    <div class="card-face card-back" hidden><div class="card-back-head"><strong>Détails</strong><button class="card-turn" type="button" data-card-turn aria-label="Revenir au recto">Retour ↩</button></div>${warnings || '<p class="muted">Aucun avertissement.</p>'}<div class="card-back-path">${escapeHtml(card.path)}</div></div>
  </article>`;
}

function allCards() {
  return state.children?.cards || [];
}

function renderCards() {
  const query = state.query.trim().toLocaleLowerCase("fr");
  const cards = allCards().filter((card) => {
    const workspaceMatch = card.workspace === state.workspace;
    const statusMatch = state.status === "all" || card.status === state.status;
    const text = [
      card.name,
      card.title,
      card.subtitle,
      card.summary,
      card.path,
      card.source,
      card.cartouche,
      card.revision_mode,
      card.revision_of,
      ...(card.tags || []),
      ...(card.hindsight_tags_projected || []),
    ].filter(Boolean).join(" ").toLocaleLowerCase("fr");
    return workspaceMatch && statusMatch && (!query || text.includes(query));
  });
  const title = state.path ? state.path.split("/").at(-1) : state.workspace;
  const parentPath = state.path.includes("/") ? state.path.slice(0, state.path.lastIndexOf("/")) : "";
  const heading = `<div class="depth-heading"><strong>${escapeHtml(title)}</strong>${state.path ? `<button type="button" data-ascend-path="${escapeHtml(parentPath)}">Remonter ↑</button>` : ""}</div>`;
  const deck = `<div class="swiper sibling-swiper"><div class="swiper-wrapper">${cards.map((card) => `<div class="swiper-slide sibling-slide">${cardTemplate(card)}</div>`).join("")}</div><div class="swiper-pagination"></div><button class="swiper-button-prev" type="button" aria-label="Élément précédent">‹</button><button class="swiper-button-next" type="button" aria-label="Élément suivant">›</button></div>`;
  elements.cards.innerHTML = `${heading}${deck}`;
  elements.cards.hidden = cards.length === 0;
  elements.empty.hidden = cards.length !== 0;
  const total = state.children?.total || 0;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const page = Math.floor(state.offset / PAGE_SIZE) + 1;
  const visibleTotal = state.status === "all" && !query ? total : cards.length;
  elements["folder-pager"].hidden = visibleTotal <= PAGE_SIZE;
  elements["page-label"].textContent = `Page ${page} / ${pageCount} · ${visibleTotal} éléments frères`;
  elements["page-previous"].disabled = state.offset <= 0;
  elements["page-next"].disabled = state.offset + PAGE_SIZE >= total;
  initializeNavigationSwipers();
}

function tabsTemplate() {
  const tabs = state.data.workspaces.map((item) => ({ name: item.name, label: item.name }));
  elements["workspace-tabs"].innerHTML = tabs.map((tab) =>
    `<button class="tab" type="button" data-workspace="${escapeHtml(tab.name)}" aria-selected="${state.workspace === tab.name}">${escapeHtml(tab.label)}</button>`,
  ).join("");
}

function filtersTemplate() {
  const filters = [{ name: "all", label: "Tous les états" }, ...Object.entries(STATUS).map(([name, item]) => ({ name, label: item.label }))];
  elements["filter-summary"].textContent = state.status === "all"
    ? "Filtrer par état"
    : `État : ${STATUS[state.status]?.label || state.status}`;
  elements["status-filters"].innerHTML = filters.map((filter) =>
    `<button class="filter" type="button" data-status="${filter.name}" aria-pressed="${state.status === filter.name}">${filter.label}</button>`,
  ).join("");
}

function renderSummary() {
  elements["package-count"].textContent = state.data.item_count ?? state.data.package_count ?? 0;
  elements["status-counts"].innerHTML = Object.entries(STATUS).map(([name, item]) =>
    `<div class="count" style="--state:${item.color}"><strong>${state.data.totals[name] || 0}</strong><span>${item.label}</span></div>`,
  ).join("");
}

function renderBreadcrumbs() {
  const crumbs = [{ label: state.workspace, path: "" }];
  const parts = state.path ? state.path.split("/") : [];
  let current = "";
  for (const part of parts) {
    current = current ? `${current}/${part}` : part;
    crumbs.push({ label: part, path: current });
  }
  elements.breadcrumbs.innerHTML = crumbs.map((crumb, index) =>
    `${index ? '<span class="breadcrumb-separator" aria-hidden="true">›</span>' : ""}${index === crumbs.length - 1 ? `<span aria-current="page">${escapeHtml(crumb.label)}</span>` : `<button type="button" data-breadcrumb-path="${escapeHtml(crumb.path)}">${escapeHtml(crumb.label)}</button>`}`,
  ).join("");
}

function initializeNavigationSwipers() {
  state.siblingSwiper?.destroy(true, true);
  state.siblingSwiper = null;
  if (typeof window.Swiper !== "function" || elements.cards.hidden) return;
  const deck = elements.cards.querySelector(".sibling-swiper");
  if (!deck) return;
  state.siblingSwiper = new window.Swiper(deck, {
    slidesPerView: 1, spaceBetween: 16, watchOverflow: true, resistanceRatio: 0.82,
    touchAngle: 35, threshold: 8, nested: false, autoHeight: true,
    noSwipingSelector: "button, a, input, textarea, select",
    keyboard: { enabled: true, onlyInViewport: true },
    pagination: { el: deck.querySelector(".swiper-pagination"), type: "fraction" },
    navigation: { prevEl: deck.querySelector(".swiper-button-prev"), nextEl: deck.querySelector(".swiper-button-next") },
  });
}

function navigateIntoFolder(path) {
  if (!path || path === state.path) return;
  state.path = path;
  state.offset = 0;
  void loadChildren();
}

function navigateToParent() {
  if (!state.path) return;
  state.path = state.path.includes("/") ? state.path.slice(0, state.path.lastIndexOf("/")) : "";
  const cached = state.levelCache[state.path];
  if (cached) {
    state.children = cached;
    state.offset = cached.offset || 0;
    renderBreadcrumbs();
    renderCards();
  } else {
    state.offset = 0;
    void loadChildren();
  }
}

async function loadSwiper() {
  if (typeof window.Swiper === "function") return true;
  const version = "14.3.0";
  const integrity = "sha384-nimz5qRuF8SOYqiuzkhgKleYiz6jIj9pUhB/LlAAsbB6I3fI9v9s5RMwMTzEyOAY";
  try {
    await new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = workspaceUrl(`vendor/swiper-${version}-bundle.min.js`);
      script.integrity = integrity;
      script.onload = resolve;
      script.onerror = reject;
      document.head.append(script);
    });
    if (typeof window.Swiper === "function") {
      document.documentElement.dataset.swiperReady = "true";
      document.documentElement.dataset.swiperVersion = version;
      return true;
    }
  } catch (_error) {
    // Keep the explicit folder and previous/next controls as the local fallback.
  }
  document.documentElement.dataset.swiperReady = "false";
  return false;
}

async function loadChildren() {
  const requestId = ++state.requestId;
  elements.loading.hidden = false;
  elements.error.hidden = true;
  elements.cards.hidden = true;
  elements.empty.hidden = true;
  try {
    const params = new URLSearchParams({ workspace: state.workspace, path: state.path, offset: String(state.offset), limit: String(PAGE_SIZE), q: state.query.trim() });
    const response = await fetch(workspaceUrl(`api/workspace-children?${params}`), { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const result = await response.json();
    if (requestId !== state.requestId) return;
    state.children = result;
    state.levelCache[state.path] = result;
    renderBreadcrumbs();
    renderCards();
  } catch (_error) {
    if (requestId !== state.requestId) return;
    elements.error.textContent = "Impossible de lire les éléments de ce dossier. Vérifiez le service et l’index Workspace.";
    elements.error.hidden = false;
  } finally {
    elements.loading.hidden = true;
  }
}

async function load() {
  elements.loading.hidden = false;
  elements.error.hidden = true;
  elements.cards.hidden = true;
  elements.empty.hidden = true;
  elements.refresh.disabled = true;
  try {
    const response = await fetch(workspaceUrl("api/workspace-overview"), { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.data = await response.json();
    renderSummary(); tabsTemplate(); filtersTemplate();
    if (!state.workspace || !state.data.workspaces.some((item) => item.name === state.workspace)) {
      state.workspace = state.data.workspaces[0]?.name || "";
    }
    state.path = "";
    state.offset = 0;
    state.levelCache = Object.create(null);
    if (state.workspace) await loadChildren();
  } catch (error) {
    elements.error.textContent = "Impossible de lire AFFAIRES. Vérifiez le service, le montage NAS et ses permissions.";
    elements.error.hidden = false;
  } finally {
    elements.loading.hidden = true;
    elements.refresh.disabled = false;
  }
}

function reconciliationFindingNode(finding) {
  const item = document.createElement("li");
  const title = document.createElement("strong");
  title.textContent = `${finding.category} — ${finding.summary || "Constat"}`;
  const detail = document.createElement("p");
  detail.textContent = finding.detail || "";
  item.append(title, detail);
  if (finding.suggestion) {
    const suggestion = document.createElement("p");
    suggestion.className = "reconcile-suggestion";
    suggestion.textContent = `Proposition : ${finding.suggestion}`;
    item.append(suggestion);
  }
  const refs = [...(finding.memory_refs || []), ...(finding.chunk_refs || [])];
  if (refs.length) {
    const ref = document.createElement("small");
    ref.textContent = `Références : ${refs.join(", ")}`;
    item.append(ref);
  }
  return item;
}

function renderReconciliationResult(container, result) {
  container.replaceChildren();
  const summary = document.createElement("p");
  summary.className = "reconcile-summary";
  summary.textContent = result.summary || "Analyse terminée.";
  container.append(summary);
  const findings = Array.isArray(result.findings) ? result.findings : [];
  if (findings.length) {
    const list = document.createElement("ol");
    list.className = "reconcile-findings";
    for (const finding of findings) list.append(reconciliationFindingNode(finding));
    container.append(list);
  } else {
    const empty = document.createElement("p");
    empty.className = "reconcile-empty";
    empty.textContent = "Aucune incohérence bornée relevée dans les éléments transmis.";
    container.append(empty);
  }
  const boundary = document.createElement("small");
  const chunks = result.inputs?.hindsight_chunks_sent ?? 0;
  const memories = result.inputs?.hindsight_memories_sent ?? 0;
  boundary.textContent = `Hindsight uniquement · ${chunks} chunks · ${memories} mémoires · source NAS non ouverte · aucune écriture`;
  container.append(boundary);
  container.hidden = false;
}

async function runMemoryReconciliation(action) {
  const button = action.querySelector("[data-reconcile-button]");
  const input = action.querySelector("[data-reconcile-focus]");
  const resultNode = action.querySelector("[data-reconcile-result]");
  const documentId = action.dataset.reconcileDocument;
  if (!button || !input || !resultNode || !documentId) return;
  button.disabled = true;
  button.textContent = "Analyse…";
  resultNode.hidden = true;
  resultNode.replaceChildren();
  try {
    const response = await fetch(workspaceUrl(`api/documents/${encodeURIComponent(documentId)}/reconcile-memory`), {
      method: "POST",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "X-Pantheon-Intent": "memory-reconcile",
      },
      body: JSON.stringify({ focus: input.value.trim() }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || payload.error || `HTTP ${response.status}`);
    renderReconciliationResult(resultNode, payload);
  } catch (error) {
    const message = document.createElement("p");
    message.className = "reconcile-error";
    message.textContent = `Réconciliation impossible : ${error.message || error}`;
    resultNode.replaceChildren(message);
    resultNode.hidden = false;
  } finally {
    button.disabled = false;
    button.textContent = "Réconcilier avec Hermes";
  }
}

elements.cards.addEventListener("click", (event) => {
  const ascend = event.target.closest("[data-ascend-path]");
  if (ascend) {
    state.path = ascend.dataset.ascendPath;
    state.children = state.levelCache[state.path] || null;
    state.offset = state.children?.offset || 0;
    renderBreadcrumbs();
    renderCards();
    return;
  }
  const turnButton = event.target.closest("[data-card-turn]");
  if (turnButton) {
    const card = turnButton.closest(".card");
    const showingVerso = !card.querySelector(".card-back").hidden;
    card.querySelector(".card-front").hidden = !showingVerso;
    card.querySelector(".card-back").hidden = showingVerso;
    card.classList.toggle("is-verso", !showingVerso);
    return;
  }
  const button = event.target.closest("[data-reconcile-button]");
  if (!button) return;
  const action = button.closest("[data-reconcile-document]");
  if (action) void runMemoryReconciliation(action);
});

let searchTimer;
elements.search.addEventListener("input", (event) => {
  state.query = event.target.value;
  state.offset = 0;
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => void loadChildren(), 180);
});
elements.refresh.addEventListener("click", load);
elements["workspace-tabs"].addEventListener("click", (event) => {
  const button = event.target.closest("[data-workspace]");
  if (!button) return;
  state.workspace = button.dataset.workspace; state.path = ""; state.offset = 0; state.levelCache = Object.create(null); tabsTemplate(); void loadChildren();
});
elements["status-filters"].addEventListener("click", (event) => {
  const button = event.target.closest("[data-status]");
  if (!button) return;
  state.status = button.dataset.status; state.offset = 0; filtersTemplate(); void loadChildren();
});

elements.cards.addEventListener("click", (event) => {
  if (event.target.closest("[data-card-turn], [data-reconcile-button]")) return;
  const button = event.target.closest("[data-folder-path]");
  if (!button) return;
  navigateIntoFolder(button.dataset.folderPath);
});
elements.breadcrumbs.addEventListener("click", (event) => {
  const button = event.target.closest("[data-breadcrumb-path]");
  if (!button) return;
  state.path = button.dataset.breadcrumbPath;
  state.offset = 0;
  void loadChildren();
});
elements["page-previous"].addEventListener("click", () => { state.offset = Math.max(0, state.offset - PAGE_SIZE); void loadChildren(); });
elements["page-next"].addEventListener("click", () => { state.offset += PAGE_SIZE; void loadChildren(); });

void loadSwiper().then(() => initializeNavigationSwipers());
load();

const ROLE_ICONS = Object.freeze({ Athena: "🦉", Argos: "🔎", Themis: "⚖", Apollo: "☀", Hephaistos: "🛠", Iris: "📨", Zeus: "⚡", Mnemosyne: "🧠", Hermes: "⚙" });
const ROLE_ORDER = Object.freeze(["Athena", "Argos", "Hermes", "Hephaistos", "Themis", "Apollo", "Zeus", "Iris", "Mnemosyne"]);
const roleView = {
  runId: "", cursor: 0, controller: null, stages: new Map(), stageEvents: new Map(), observedOrder: new Map(),
  observationCounter: 0, activeView: "dialogue", selectedStageId: "",
  state: document.getElementById("role-dialogue-state"),
  events: document.getElementById("role-dialogue-events"),
  graph: document.getElementById("role-graph"),
  graphLanes: document.getElementById("role-graph-lanes"),
  graphDetail: document.getElementById("role-graph-detail"),
};

function roleState(value) { roleView.state.textContent = value; }

function roleStageSort(left, right) {
  const leftSequence = Number(left?.sequence);
  const rightSequence = Number(right?.sequence);
  const leftHasSequence = Number.isSafeInteger(leftSequence);
  const rightHasSequence = Number.isSafeInteger(rightSequence);
  if (leftHasSequence && rightHasSequence && leftSequence !== rightSequence) return leftSequence - rightSequence;
  return (roleView.observedOrder.get(left.stage_id) ?? 0) - (roleView.observedOrder.get(right.stage_id) ?? 0);
}

function orderedRoleStages() { return [...roleView.stageEvents.values()].sort(roleStageSort); }

function visibleRoleOrder(events) {
  const present = new Set(events.map((event) => event.visible_role));
  return [...ROLE_ORDER.filter(role => present.has(role)), ...[...present].filter(role => !ROLE_ORDER.includes(role))];
}

function renderRoleGraphDetail(event) {
  roleView.graphDetail.replaceChildren();
  if (!event) {
    const empty = document.createElement("p");
    empty.className = "role-graph-detail-empty";
    empty.textContent = "Sélectionnez un jalon pour afficher ses détails observables.";
    roleView.graphDetail.append(empty);
    return;
  }
  const head = document.createElement("div");
  head.className = "role-graph-detail-head";
  const title = document.createElement("strong");
  title.textContent = `${event.visible_role} — ${event.semantic_function || event.role_family || "Jalon"}`;
  const status = document.createElement("span");
  status.textContent = event.phase === "completed" ? "terminé" : "en cours";
  head.append(title, status);
  const summary = document.createElement("p");
  summary.className = "role-graph-detail-summary";
  summary.textContent = event.summary || "Jalon public observé.";
  const origin = document.createElement("p");
  origin.className = "role-graph-detail-origin";
  origin.textContent = event.projection === "derived_transient"
    ? "Projection transitoire dérivée du flux public Hermes."
    : "Événement structuré émis par le runtime.";
  roleView.graphDetail.append(head, summary, origin);
  const entries = Object.entries(event.details || {}).filter(([, value]) => value != null && value !== "");
  if (entries.length) {
    const list = document.createElement("dl");
    for (const [key, value] of entries) {
      const dt = document.createElement("dt");
      const dd = document.createElement("dd");
      dt.textContent = key.replaceAll("_", " ");
      dd.textContent = String(value);
      list.append(dt, dd);
    }
    roleView.graphDetail.append(list);
  }
}

function renderRoleGraph() {
  const events = orderedRoleStages();
  roleView.graphLanes.replaceChildren();
  if (!events.length) {
    const empty = document.createElement("p");
    empty.className = "role-graph-empty";
    empty.textContent = "Aucun jalon observable pour cette exécution.";
    roleView.graphLanes.append(empty);
    renderRoleGraphDetail(null);
    return;
  }

  const stageColumns = new Map(events.map((event, index) => [event.stage_id, index + 1]));
  for (const role of visibleRoleOrder(events)) {
    const lane = document.createElement("div");
    lane.className = "role-graph-lane";
    const label = document.createElement("div");
    label.className = "role-graph-label";
    const icon = document.createElement("span");
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = ROLE_ICONS[role] || "•";
    const name = document.createElement("strong");
    name.textContent = role;
    label.append(icon, name);

    const rail = document.createElement("div");
    rail.className = "role-graph-rail";
    rail.style.gridTemplateColumns = `repeat(${events.length}, 3.1rem)`;
    for (const event of events.filter(candidate => candidate.visible_role === role)) {
      const node = document.createElement("button");
      node.type = "button";
      node.className = "role-graph-node";
      node.style.gridColumn = String(stageColumns.get(event.stage_id));
      node.dataset.phase = event.phase || "updated";
      node.dataset.projection = event.projection || "native";
      node.classList.toggle("is-selected", event.stage_id === roleView.selectedStageId);
      node.textContent = ROLE_ICONS[role] || "•";
      node.title = event.summary || `${role} — jalon observable`;
      node.setAttribute("aria-label", `${role}, ${event.semantic_function || event.role_family || "jalon"}, ${event.summary || "jalon public observé"}`);
      node.addEventListener("click", () => {
        roleView.selectedStageId = event.stage_id;
        renderRoleGraph();
      });
      rail.append(node);
    }
    lane.append(label, rail);
    roleView.graphLanes.append(lane);
  }

  if (roleView.selectedStageId && !roleView.stageEvents.has(roleView.selectedStageId)) roleView.selectedStageId = "";
  renderRoleGraphDetail(roleView.selectedStageId ? roleView.stageEvents.get(roleView.selectedStageId) : null);
}

function setRoleTraceView(view) {
  roleView.activeView = view === "graph" ? "graph" : "dialogue";
  roleView.events.hidden = roleView.activeView !== "dialogue";
  roleView.graph.hidden = roleView.activeView !== "graph";
  for (const button of document.querySelectorAll("[data-role-trace-view]")) {
    const selected = button.dataset.roleTraceView === roleView.activeView;
    button.setAttribute("aria-selected", String(selected));
    button.tabIndex = selected ? 0 : -1;
  }
  if (roleView.activeView === "graph") renderRoleGraph();
}

function renderRoleStage(event) {
  if (!event?.stage_id || !event?.visible_role) return;
  if (!roleView.observedOrder.has(event.stage_id)) roleView.observedOrder.set(event.stage_id, roleView.observationCounter++);
  roleView.stageEvents.set(event.stage_id, { ...event });
  let item = roleView.stages.get(event.stage_id);
  if (!item) {
    item = document.createElement("li");
    item.className = "role-stage";
    roleView.stages.set(event.stage_id, item);
    roleView.events.append(item);
  }
  item.dataset.phase = event.phase || "updated";
  item.replaceChildren();
  const icon = document.createElement("span"); icon.className = "role-stage-icon"; icon.setAttribute("aria-hidden", "true"); icon.textContent = ROLE_ICONS[event.visible_role] || "•";
  const title = document.createElement("strong"); title.className = "role-stage-title"; title.textContent = `${event.visible_role} — ${event.semantic_function || event.role_family || "Jalon"}`;
  const status = document.createElement("span"); status.className = "role-stage-status"; status.textContent = event.phase === "completed" ? "terminé" : "en cours";
  const summary = document.createElement("p"); summary.className = "role-stage-summary"; summary.textContent = event.summary || "Jalon public observé.";
  const origin = document.createElement("span"); origin.className = "role-stage-origin"; origin.textContent = event.projection === "derived_transient" ? "Dérivé du flux public" : "Événement natif";
  item.append(icon, title, status, summary, origin);
  if (roleView.activeView === "graph") renderRoleGraph();
}

function consumeRoleBlock(block) {
  let kind = "message";
  let id = 0;
  const data = [];
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) kind = line.slice(6).trim();
    else if (line.startsWith("id:")) id = Number(line.slice(3).trim());
    else if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
  }
  if (!data.length) return;
  const event = JSON.parse(data.join("\n"));
  if (Number.isSafeInteger(id) && id > roleView.cursor) roleView.cursor = id;
  if (kind === "role.stage") renderRoleStage(event);
  else if (kind === "role.trace.error") roleState("Rejeu incomplet");
}

async function followRoleTrace(runId) {
  if (!runId) return;
  if (runId !== roleView.runId) {
    roleView.controller?.abort();
    roleView.runId = runId;
    roleView.cursor = 0;
    roleView.observationCounter = 0;
    roleView.selectedStageId = "";
    roleView.stages.clear();
    roleView.stageEvents.clear();
    roleView.observedOrder.clear();
    roleView.events.replaceChildren();
    roleView.graphLanes.replaceChildren();
    roleView.graphDetail.replaceChildren();
  }
  roleView.controller = new AbortController();
  const headers = roleView.cursor ? { "Last-Event-ID": String(roleView.cursor) } : {};
  try {
    roleState("En direct");
    const response = await fetch(workspaceUrl(`api/role-traces/${encodeURIComponent(runId)}/events`), { headers, cache: "no-store", signal: roleView.controller.signal });
    if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`);
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value || new Uint8Array(), { stream: !done }).replaceAll("\r\n", "\n");
      let end;
      while ((end = buffer.indexOf("\n\n")) >= 0) {
        const block = buffer.slice(0, end); buffer = buffer.slice(end + 2);
        if (block.trim()) consumeRoleBlock(block);
      }
      if (done) break;
    }
    roleState("Terminé");
  } catch (error) {
    if (error?.name !== "AbortError") roleState("Trace indisponible");
  }
}

async function discoverLatestRoleTrace() {
  try {
    const response = await fetch(workspaceUrl("api/role-traces/latest"), { cache: "no-store" });
    if (response.status === 404) { roleState("Aucune trace"); return; }
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const trace = await response.json();
    if (trace.run_id && trace.run_id !== roleView.runId) void followRoleTrace(trace.run_id);
  } catch (_error) {
    roleState("Relais indisponible");
  }
}

for (const button of document.querySelectorAll("[data-role-trace-view]")) {
  button.addEventListener("click", () => setRoleTraceView(button.dataset.roleTraceView));
}
setRoleTraceView("dialogue");
void loadNavigation();
void discoverLatestRoleTrace();
window.setInterval(discoverLatestRoleTrace, 5000);

const producerPanel = document.getElementById("producer-panel");
const producerScopeState = document.getElementById("producer-scope-state");
const producerWarning = document.getElementById("producer-warning");
const producerStatus = document.getElementById("producer-status");
const producerLogs = document.getElementById("producer-logs");
const producerLogUnit = document.getElementById("producer-log-unit");
const producerConfigure = document.getElementById("producer-configure");
const producerConfigMessage = document.getElementById("producer-config-message");

async function loadProducerStatus() {
  try {
    const response = await fetch(workspaceUrl("api/producers/status"), { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    const affaires = data.services?.affaires || {};
    const bibliotheque = data.services?.bibliotheque || {};
    producerScopeState.textContent = data.scope_ok ? "Portée conforme" :
      data.config_ok && affaires.active !== "active" ? "Portée prête · ingestion arrêtée" : "Portée à vérifier";
    producerWarning.textContent = (data.warnings || []).join(" · ") || "";
    const rows = [
      ["Worker Affaires", `${affaires.active || "inconnu"} · PID ${affaires.pid || 0} · ${affaires.process_state || "état inconnu"}`],
      ["Worker Bibliothèque", `${bibliotheque.active || "inconnu"} · PID ${bibliotheque.pid || 0}`],
      ["Montage réel", `${data.mount?.source || "indisponible"} → ${data.mount?.target || "indisponible"}`],
      ["Source SMB effective", data.actual_source || "indisponible"],
      ["Source SMB configurée", data.configured_source || "indisponible"],
      ["Source SMB attendue", data.expected_source || "non configurée"],
      ["Dossier scanné", affaires.root || "indisponible"],
      ["Dossier configuré", affaires.configured_root || "indisponible"],
      ["Dossier attendu", data.expected_root || "non configuré"],
      ["Base d’index", affaires.state_db || "indisponible"],
    ];
    producerStatus.replaceChildren(...rows.flatMap(([label, value]) => {
      const term = document.createElement("dt"); term.textContent = label;
      const detail = document.createElement("dd"); detail.textContent = value;
      return [term, detail];
    }));
    producerConfigure.hidden = !data.expected_root || !data.expected_source;
    producerConfigure.disabled = affaires.configured_root === data.expected_root && affaires.active !== "active";
  } catch (_error) {
    producerScopeState.textContent = "État indisponible";
    producerWarning.textContent = "Impossible de vérifier le worker.";
  }
}

async function loadProducerLogs() {
  producerLogs.textContent = "Chargement des journaux…";
  try {
    const response = await fetch(workspaceUrl(`api/producers/logs?producer=${encodeURIComponent(producerLogUnit.value)}&lines=80`), { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    producerLogs.textContent = data.error ? "Journaux indisponibles." : (data.lines || []).join("\n") || "Aucune ligne récente.";
  } catch (_error) {
    producerLogs.textContent = "Journaux indisponibles.";
  }
}

producerPanel.addEventListener("toggle", () => {
  if (producerPanel.open) { void loadProducerStatus(); void loadProducerLogs(); }
});
document.getElementById("producer-log-refresh").addEventListener("click", () => { void loadProducerStatus(); void loadProducerLogs(); });
producerLogUnit.addEventListener("change", loadProducerLogs);
producerConfigure.addEventListener("click", async () => {
  producerConfigure.disabled = true;
  producerConfigMessage.textContent = "Configuration demandée…";
  try {
    const response = await fetch(workspaceUrl("api/producers/configure-affaires"), {
      method: "POST", headers: { "X-Pantheon-Intent": "configure-affaires-scope" },
      cache: "no-store",
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    producerConfigMessage.textContent = "Demande reçue. Cockpit peut redémarrer pendant l’application. L’ingestion restera arrêtée.";
    window.setTimeout(loadProducerStatus, 5000);
  } catch (_error) {
    producerConfigMessage.textContent = "Configuration indisponible. Vérifiez les journaux de l’unité pantheon-affaires-scope-apply.service.";
    producerConfigure.disabled = false;
  }
});
void loadProducerStatus();
window.setInterval(() => { if (producerPanel.open) void loadProducerStatus(); }, 15000);
