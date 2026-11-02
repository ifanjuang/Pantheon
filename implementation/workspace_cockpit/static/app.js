// 1. État partagé, constantes et échappement HTML
const STATUS = {
  COMPLETE: { label: "Complet", color: "#287652", icon: "circle-check" },
  FOLDER_SCOPED: { label: "Contexte dossier", color: "#247a67", icon: "folder-open" },
  PENDING_SCOPE: { label: "Projet à identifier", color: "#8a5a20", icon: "folder-search" },
  CHECK: { label: "À vérifier", color: "#a76800", icon: "circle-warning" },
  SOURCE_ONLY: { label: "Source seule", color: "#6648a8", icon: "file" },
  SOURCE_MISSING: { label: "Source manquante", color: "#a53535", icon: "file-close" },
  FOLDER: { label: "Dossier", color: "#315d9c", icon: "folder" },
};

// Coolicons line / sharp (24 px, stroke 2).
const CARD_ICONS = {
  "circle-check": "M3 12C3 16.97056 7.02944 21 12 21C16.97056 21 21 16.97056 21 12C21 7.02944 16.97056 3 12 3C7.02944 3 3 7.02944 3 12ZM8 12L11 15L16 9",
  "circle-warning": "M3 12C3 16.97056 7.02944 21 12 21C16.97056 21 21 16.97056 21 12C21 7.02944 16.97056 3 12 3C7.02944 3 3 7.02944 3 12ZM12 8V13M12 16H12.01",
  "circle-close": "M3 12C3 16.97056 7.02944 21 12 21C16.97056 21 21 16.97056 21 12C21 7.02944 16.97056 3 12 3C7.02944 3 3 7.02944 3 12ZM9 9L15 15M15 9L9 15",
  "cloud-off": "M18 19H7C4.23858 19 2 16.76142 2 14C2 11.23858 4.23858 9 7 9C7.07444 8.73946 6.90699 8.23842 7 8M10 5C13.35902 3.13197 18 5.24164 18 11C20.20914 11 22 12.79086 22 15C22 15.58694 22.22709 15.49786 22 16M2 3L21 22",
  "file-edit": "M13 3H5V21H19V9M13 3L19 9M13 3V9H19M9 18V16L13 12L15 14L11 18Z",
  "file-close": "M13 3H5V21H19V9M13 3L19 9M13 3V9H19M10 13L14 17M14 13L10 17",
  file: "M13 3H5V21H19V9M13 3L19 9M13 3V9H19",
  folder: "M12 6H21V20H3V4H10L12 6",
  "folder-open": "M5 20L8 11H21L18 20H5ZM19 11V6H12L10 4H3V20H5",
  "folder-search": "M12 6H21V20H3V4H10L12 6M9 12C9 13.10457 9.89543 14 11 14C12.10457 14 13 13.10457 13 12C13 10.89543 12.10457 10 11 10C9.89543 10 9 10.89543 9 12ZM13 14L15 16",
  clock: "M3 12C3 16.97056 7.02944 21 12 21C16.97056 21 21 16.97056 21 12C21 7.02944 16.97056 3 12 3C7.02944 3 3 7.02944 3 12ZM12 7V12H17",
  open: "M14 4H20V10M20 4L11 13M18 13V20H4V6H11",
  preview: "M2 12C4.5 7.5 8 5 12 5S19.5 7.5 22 12C19.5 16.5 16 19 12 19S4.5 16.5 2 12ZM12 15C13.65685 15 15 13.65685 15 12S13.65685 9 12 9S9 10.34315 9 12S10.34315 15 12 15Z",
  share: "M12 16V3M7 8L12 3L17 8M5 13V20H19V13",
  edit: "M4 20H8L19 9L15 5L4 16V20ZM13.5 6.5L17.5 10.5",
  analyze: "M11 3H5V21H19V11M11 3L19 11M11 3V11H19M14 16L16 18L21 13",
  refresh: "M20 7V3L17 6M20 7H15M4 17V21L7 18M4 17H9M6.1 8.1A7 7 0 0 1 18 6M17.9 15.9A7 7 0 0 1 6 18",
  undo: "M9 14 4 9l5-5M4 9h10a6 6 0 0 1 0 12h-2",
  ocr: "M5 3H14L19 8V21H5V3ZM14 3V8H19M8 12H16M8 16H13",
  memorize: "M5 3H14L19 8V21H5V3ZM14 3V8H19M8 13H16M8 17H16",
  verify: "M3 12C3 16.97056 7.02944 21 12 21C16.97056 21 21 16.97056 21 12C21 7.02944 16.97056 3 12 3C7.02944 3 3 7.02944 3 12ZM8 12L11 15L16 9",
  pause: "M8 5H10V19H8ZM14 5H16V19H14Z",
  resume: "M7 4V20L20 12Z",
  continue: "M5 4V20L17 12ZM19 5V19",
  archive: "M3 5H21V9H3V5ZM5 9V20H19V9M10 13H14",
  trash: "M4 7H20M10 11V17M14 11V17M6 7L7 20H17L18 7M9 7V4H15V7",
  unarchive: "M12 3V15M7 8L12 3L17 8M4 14V20H20V14",
  prohibit: "M12 3C16.97056 3 21 7.02944 21 12C21 16.97056 16.97056 21 12 21C7.02944 21 3 16.97056 3 12C3 7.02944 7.02944 3 12 3ZM5.64 5.64L18.36 18.36",
  loading: "M5 14C5 14.55228 5.44772 15 6 15C6.55228 15 7 14.55228 7 14C7 13.44772 6.55228 13 6 13C5.44772 13 5 13.44772 5 14ZM17 10C17 10.55228 17.44772 11 18 11C18.55228 11 19 10.55228 19 10C19 9.44772 18.55228 9 18 9C17.44772 9 17 9.44772 17 10ZM11 12C11 12.55228 11.44772 13 12 13C12.55228 13 13 12.55228 13 12C13 11.44772 12.55228 11 12 11C11.44772 11 11 11.44772 11 12Z",
};

function cardLabelIcon(icon, label, color = "", pulse = false) {
  const path = CARD_ICONS[icon] || CARD_ICONS.file;
  const fixedColor = color.startsWith("#") ? ` style="color:${color}"` : "";
  return `<span class="card-label-icon${color && !color.startsWith("#") ? ` is-${color}` : ""}${pulse ? " is-pulse" : ""}" role="img" aria-label="${escapeHtml(label)}" title="${escapeHtml(label)}"${fixedColor}><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="${path}"></path></svg></span>`;
}

function actionIconButton(icon, label, attributes = "") {
  const path = CARD_ICONS[icon] || CARD_ICONS.file;
  return `<button type="button" class="icon-action" aria-label="${escapeHtml(label)}" title="${escapeHtml(label)}" ${attributes}><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="${path}"></path></svg></button>`;
}

function hermesChatIconButton(label, attributes = "", disabled = false) {
  return `<button type="button" class="hermes-chat-trigger" ${attributes} aria-label="${escapeHtml(label)}" title="${escapeHtml(label)}"${disabled ? " disabled" : ""}><img src="/workspace/vendor/hermes-agent-light.svg" alt="" aria-hidden="true"></button>`;
}

function hermesChatButton(card) {
  const available = card.hermes_chat_available === true;
  return hermesChatIconButton(
    available ? `Dialoguer avec Hermes à propos de ${card.title || card.name}` : "Hermes Chat n’est pas configuré",
    `data-hermes-chat-new data-workspace="${escapeHtml(card.workspace)}" data-card-path="${escapeHtml(card.path)}" data-card-kind="${escapeHtml(card.kind)}" data-card-title="${escapeHtml(card.title || card.name)}"`,
    !available,
  );
}

function hermesDiscussionItemTemplate(item) {
  const sessionId = escapeHtml(item.session_id);
  const archived = item.archived === true;
  const action = archived
    ? actionIconButton("unarchive", "Restaurer la discussion", `data-hermes-chat-restore="${sessionId}"`)
    : actionIconButton("archive", "Archiver la discussion", `data-hermes-chat-archive="${sessionId}"`);
  return `<li class="hermes-discussion-item"><button type="button" class="hermes-discussion-open" data-hermes-chat-open="${sessionId}" aria-label="Reprendre ${escapeHtml(item.title || "la discussion")}"><strong>${escapeHtml(item.title || "Discussion Hermes")}</strong>${item.preview ? `<span>${escapeHtml(item.preview)}</span>` : ""}</button><div class="hermes-discussion-actions">${action}${actionIconButton("trash", "Supprimer la discussion", `data-hermes-chat-delete="${sessionId}"`)}</div></li>`;
}

function hermesDiscussionsTemplate(card) {
  if (card.hermes_chat_available !== true) return "";
  const discussions = Array.isArray(card.hermes_discussions) ? card.hermes_discussions : [];
  const active = discussions.filter((item) => !item.archived);
  const archived = discussions.filter((item) => item.archived);
  return `<section class="hermes-discussions" aria-label="Discussions Hermes pour ${escapeHtml(card.title || card.name)}"><div class="hermes-discussions-head"><span>Discussions Hermes · ${discussions.length}</span></div>${active.length ? `<ul>${active.map(hermesDiscussionItemTemplate).join("")}</ul>` : '<p class="hermes-discussions-empty">Aucune discussion active.</p>'}${archived.length ? `<details class="hermes-discussions-archived"><summary>Archivées · ${archived.length}</summary><ul>${archived.map(hermesDiscussionItemTemplate).join("")}</ul></details>` : ""}</section>`;
}

const PAGE_SIZE = 24;
const WORKSPACE_BASE_PATH = "/workspace/";
const workspaceUrl = (path) => `${WORKSPACE_BASE_PATH}${String(path).replace(/^\/+/, "")}`;
const state = { data: null, workspace: "", status: "all", query: "", path: "", offset: 0, children: null, levelCache: Object.create(null), navigationLevels: [], siblingSwipers: [], focusCardPath: "", requestId: 0 };
const visibleVaults = new Set();
const vaultSwitch = document.getElementById("workspace-vault-switch");
let vaultSwitchExpanded = false;
const elements = Object.fromEntries(
  ["package-count", "status-counts", "status-filters", "filter-summary", "breadcrumbs", "folder-pager", "page-previous", "page-next", "page-label", "search", "search-clear", "refresh", "loading", "error", "cards", "empty", "tool-links"]
    .map((id) => [id, document.getElementById(id)]),
);

const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;").replaceAll("'", "&#039;");

let dialogPageScrollY = null;

function syncDialogPageScrollLock() {
  const hasOpenDialog = [...document.querySelectorAll("dialog")].some((dialog) => dialog.open);
  if (hasOpenDialog && dialogPageScrollY === null) {
    dialogPageScrollY = window.scrollY;
    document.documentElement.style.setProperty("--dialog-page-scroll-y", `${dialogPageScrollY}px`);
    document.documentElement.classList.add("dialog-open");
    return;
  }
  if (!hasOpenDialog && dialogPageScrollY !== null) {
    const scrollY = dialogPageScrollY;
    dialogPageScrollY = null;
    document.documentElement.classList.remove("dialog-open");
    document.documentElement.style.removeProperty("--dialog-page-scroll-y");
    window.scrollTo(0, scrollY);
  }
}

function showCockpitDialog(dialog) {
  if (!dialog || dialog.open) return;
  syncDialogPageScrollLock();
  if (dialogPageScrollY === null) {
    dialogPageScrollY = window.scrollY;
    document.documentElement.style.setProperty("--dialog-page-scroll-y", `${dialogPageScrollY}px`);
    document.documentElement.classList.add("dialog-open");
  }
  dialog.showModal();
}

for (const dialog of document.querySelectorAll("dialog")) {
  dialog.addEventListener("close", syncDialogPageScrollLock);
}

// Prevent browser-level page zoom; PDF.js keeps its own controls inside its iframe.
document.addEventListener("wheel", (event) => {
  if (event.ctrlKey || event.metaKey) event.preventDefault();
}, { passive: false });
document.addEventListener("touchmove", (event) => {
  if (event.touches.length > 1) event.preventDefault();
}, { passive: false });
for (const gestureEvent of ["gesturestart", "gesturechange", "gestureend"]) {
  document.addEventListener(gestureEvent, (event) => event.preventDefault(), { passive: false });
}
document.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && ["+", "=", "-", "0", "Add", "Subtract"].includes(event.key)) event.preventDefault();
});

// 2. Présentation des métadonnées de préflight et Hindsight
function tagTemplate(tag) {
  const prefix = String(tag).split(":", 1)[0];
  const family = ["scope", "folder", "workspace", "source", "project_hint", "phase_hint", "family", "revision_hint", "tag"].includes(prefix) ? prefix : "other";
  return `<span class="tag tag-${family}" title="${escapeHtml(tag)}"><small>${escapeHtml(prefix)}</small>${escapeHtml(String(tag).slice(prefix.length + 1))}</span>`;
}

function tagsTemplate(tags, label = "Tags du cartouche") {
  if (!Array.isArray(tags) || tags.length === 0) return "";
  return `<div class="tag-group"><span class="tag-group-label">${escapeHtml(label)}</span><div class="tags" aria-label="${escapeHtml(label)}">${tags.map(tagTemplate).join("")}</div></div>`;
}

function preflightStatusLabel(status) {
  return ({
    complete: "Champs repérés",
    partial: "Partiel",
    no_explicit_fields: "Aucun champ explicite",
    no_native_text: "Pas de texte natif",
    extractor_unavailable: "Extracteur indisponible",
    read_failed: "Lecture en échec",
    not_pdf: "Non applicable au format",
    not_run: "À effectuer",
  })[status] || status || "À effectuer";
}

function usablePreflightTitle(preflight) {
  const candidate = String(preflight?.document_title_candidate?.value || "").trim();
  const compact = candidate.replace(/\b(?:[A-Z]\s+)+[A-Z]{2,}\b/g, (label) => label.replace(/\s+/g, ""));
  const noise = /\b(?:affaire\s*n[°ºo]?|date\s+r[eé]dacteur|v[eé]rificateur|modification\s+document|indice\b|quantit[eé]\b|d[eé]signation\b|montant\b|consid[eé]rant\b|attendu\b|vu\s+le\s+code|ne\s+peuvent\s+[eê]tre\s+reproduits|droits\s+d['’]auteur|sans\s+autorisation\s+[eé]crite)\b/i;
  const supplierAddress = /\b\d{5}\s+[A-ZÀ-Ý][A-ZÀ-Ý'’ -]{2,}\b/;
  const titleBlockLabels = /\b(?:projet|phase|[eé]metteur|lot|niveau|zone|[eé]chelle|format|n\s*[°ºo]\s*(?:de\s+)?plan)\b/gi;
  const moneyCells = compact.match(/\b\d[\d\s.,]*\s*(?:€|euros?)/gi) || [];
  const labelCount = compact.match(titleBlockLabels) || [];
  const issuerValues = [preflight?.fields?.issuer?.value, ...(preflight?.issuer_candidates || []).map((item) => item.value)]
    .map((value) => String(value || "").trim().toLocaleLowerCase("fr"));
  if (
    !candidate
    || candidate.length > 140
    || noise.test(compact)
    || supplierAddress.test(compact)
    || (compact.includes("|") && labelCount.length >= 4)
    || moneyCells.length >= 2
    || issuerValues.includes(candidate.toLocaleLowerCase("fr"))
  ) return "";
  return candidate;
}

function usablePreflightSummary(preflight) {
  const candidate = String(preflight?.document_summary_candidate?.value || "").trim();
  if (!candidate) return "";
  if (/\b(?:ne\s+peuvent\s+(?:être|etre)\s+reproduits?|ne\s+peut\s+(?:être|etre)\s+divulgu[eé]s?|droits\s+d['’]auteur|sans\s+autorisation\s+[eé]crite|tous\s+droits\s+r[eé]serv[eé]s)\b/i.test(candidate)) return "";
  const labels = candidate.match(/\b(?:projet|phase|[eé]metteur|lot|niveau|zone|[eé]chelle|format|n\s*[°ºo]\s*(?:de\s+)?plan)\b/gi) || [];
  return candidate.includes("|") && labels.length >= 4 ? "" : candidate;
}

function preflightTemplate(preflight, fallbackStatus, overrides = {}) {
  preflight = preflight && typeof preflight === "object" ? preflight : {};
  const classification = preflight.document_classification || {};
  const confirmedFamily = Object.hasOwn(overrides, "family") ? overrides.family : classification.family;
  const confirmedType = Object.hasOwn(overrides, "document_type") ? overrides.document_type : classification.document_type;
  const titleCandidate = usablePreflightTitle(preflight);
  const summaryCandidate = Object.hasOwn(overrides, "summary")
    ? String(overrides.summary ?? "").trim()
    : usablePreflightSummary(preflight);
  const fields = preflight.fields || {};
  const facets = [
    {
      icon: "🗂️", label: "Famille / type",
      items: [confirmedFamily, confirmedType].filter(Boolean).length
        ? [{
            value: [confirmedFamily, confirmedType].filter(Boolean).join(" · "),
            page: classification.page,
            evidence: classification.evidence,
          }]
        : [],
    },
    { icon: "🔧", label: "Corps d’état", items: preflight.corps_etat_candidates || [] },
    { icon: "🧭", label: "Sujets techniques", items: preflight.sujet_technique_candidates || [] },
  ].filter((facet) => facet.items.length);
  const chips = facets.map(({ icon, label, items }) => items.map((item) => {
    const value = typeof item === "string" ? item : item.value;
    if (!value) return "";
    const source = typeof item === "object" ? [
      item.page ? `page ${item.page}` : "",
      item.evidence ? `preuve : ${item.evidence}` : "",
    ].filter(Boolean).join(" · ") : "";
    const hint = [`${label} — candidat automatique à confirmer`, source].filter(Boolean).join(" · ");
    return `<span class="preflight-chip" title="${escapeHtml(hint)}"><span aria-hidden="true">${icon}</span><span class="visually-hidden">${escapeHtml(label)} : </span>${escapeHtml(value)}</span>`;
  }).join("")).join("");
  const issuer = (preflight.issuer_candidates || [])[0]?.value;
  const status = preflight.status || fallbackStatus || "not_run";
  const sourceLabel = preflight.text_source === "ocr_markdown" ? "texte OCR" : "texte natif PDF";
  const statusChip = `<span class="preflight-status" title="État et source de l’analyse des métadonnées">🔎 Analyse : ${escapeHtml(preflightStatusLabel(status))} · ${sourceLabel}</span>`;
  const hasConfirmedTitle = Object.hasOwn(overrides, "title");
  const confirmedTitle = String(overrides.title ?? "").trim();
  const title = hasConfirmedTitle ? confirmedTitle : titleCandidate;
  const primaryDescription = title
    ? `<p class="preflight-title"><span aria-hidden="true">📄</span> ${confirmedTitle ? "Titre confirmé" : "Titre candidat"} : ${escapeHtml(title)}</p>`
    : summaryCandidate
      ? `<p class="preflight-summary"><strong>Résumé extrait :</strong> ${escapeHtml(summaryCandidate)}</p>`
      : "";
  const meta = [
    statusChip,
    primaryDescription,
    chips ? `<div class="preflight-chips" aria-label="Métadonnées d’analyse, candidates à confirmer">${chips}</div>` : "",
  ].filter(Boolean).join("");
  return meta || (issuer ? `<p class="preflight-summary">Émetteur candidat : ${escapeHtml(issuer)}.</p>` : "");
}

function hindsightTagGroups(tags) {
  if (!tags || !Array.isArray(tags.values) || tags.values.length === 0) return "";
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

// 3. Données des cartes et rendu des documents
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

function documentNoteEditor(card) {
  if (!card.source_present) return "";
  return `<section class="document-note" data-document-note data-note-workspace="${escapeHtml(card.workspace)}" data-note-path="${escapeHtml(card.path)}">
    <label for="${escapeHtml(`note-${card.workspace}-${card.path}`)}">Note</label>
    <textarea id="${escapeHtml(`note-${card.workspace}-${card.path}`)}" maxlength="4000" rows="3" data-document-note-input>${escapeHtml(card.document_note || "")}</textarea>
    <div class="document-note-actions"><button type="button" data-save-document-note>Enregistrer la note</button><span role="status" aria-live="polite" data-document-note-status></span></div>
    <small>Note manuelle conservée dans la base de cet espace, séparément de l’analyse automatique.</small>
  </section>`;
}

function documentMetadataEditor(card, preflight) {
  if (!card.source_present) return "";
  const fields = preflight.fields || {};
  const classification = preflight.document_classification || {};
  const override = card.metadata_override || {};
  const values = override.values || {};
  const candidate = (key, fallback = "") => Object.hasOwn(values, key) ? (values[key] ?? "") : (fallback ?? "");
  const issuerCandidate = preflight.issuer_candidates?.[0]?.value || fields.issuer?.value || "";
  const recipientCandidate = fields.recipient?.value || "";
  const titleCandidate = usablePreflightTitle(preflight) || card.name || "";
  const summaryCandidate = preflight.document_summary_candidate?.value || card.summary || "";
  const listValue = (key, candidates) => candidate(key, (candidates || []).map((item) => item.value).filter(Boolean).join("\n"));
  const stale = override.stale === true;
  const status = Object.keys(values).length
    ? `<span class="metadata-override-status ${stale ? "is-stale" : "is-confirmed"}" data-metadata-override-status>${stale ? "À revalider : le fichier a changé" : "Valeurs confirmées par vous"}</span>`
    : `<span class="metadata-override-status" data-metadata-override-status>Aucune correction enregistrée</span>`;
  const hasTagValues = metadataHasTagValues(values);
  const hindsightStatus = String(card.processing_hindsight_status || "").toUpperCase();
  const hindsightReady = hindsightStatus === "MEMORIZED";
  const lastSync = card.hindsight_metadata_sync || null;
  const lastSyncText = lastSync?.status === "FAILED"
    ? `Échec de la dernière demande : ${lastSync.error || "à relancer après vérification"}`
    : lastSync?.status === "COMPLETED"
      ? (lastSync.mode === "tags" ? "Dernière synchronisation des tags terminée." : "Dernière réingestion terminée.")
      : lastSync?.status === "SUBMITTED"
        ? "Hindsight traite le document…"
        : lastSync?.status === "PROCESSING"
          ? "Synchronisation en cours…"
          : lastSync?.status === "PENDING"
            ? "En attente du producteur…"
            : "";
  const syncActions = `<div class="metadata-sync-actions">
        <button type="button" data-hindsight-metadata-sync="tags"${!hasTagValues || stale || !hindsightReady ? " disabled" : ""}>Synchroniser les tags</button>
        <button type="button" data-hindsight-metadata-sync="reingest"${!Object.keys(values).length || stale || !hindsightReady ? " disabled" : ""}>Réingérer le document</button>
        <span role="status" aria-live="polite" data-hindsight-metadata-sync-status>${escapeHtml(lastSyncText)}</span>
      </div>
      <small data-hindsight-metadata-sync-help>${hindsightReady
        ? "Enregistrez d’abord vos corrections. La synchronisation des tags conserve les mémoires; la réingestion les reconstruit avec le fichier et les métadonnées corrigées."
        : "Les métadonnées sont enregistrées dans le Cockpit. La synchronisation ou la réingestion devient disponible après mémorisation du document dans Hindsight."}</small>`;
  const fieldControl = (key, control, label) => `<div class="metadata-field-control">${control}<button class="metadata-field-reset" type="button" data-metadata-field-reset="${key}" aria-label="Annuler la modification du champ ${escapeHtml(label)}" title="Annuler la modification" disabled><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="${CARD_ICONS.undo}"></path></svg></button></div>`;
  const input = (key, label, value, maxLength, hint = "") => `<label class="metadata-field"><span>${escapeHtml(label)}</span>${fieldControl(key, `<input type="text" maxlength="${maxLength}" data-metadata-field="${key}" data-metadata-previous-value="${escapeHtml(value)}" value="${escapeHtml(value)}">`, label)}${hint ? `<small>${escapeHtml(hint)}</small>` : ""}</label>`;
  const list = (key, label, value) => `<label class="metadata-field"><span>${escapeHtml(label)}</span>${fieldControl(key, `<textarea rows="2" maxlength="2019" data-metadata-field="${key}" data-metadata-previous-value="${escapeHtml(value)}">${escapeHtml(value)}</textarea>`, label)}<small>Jusqu’à 20 valeurs, 100 caractères chacune.</small></label>`;
  return `<details class="metadata-editor" data-document-metadata data-metadata-workspace="${escapeHtml(card.workspace)}" data-metadata-path="${escapeHtml(card.path)}" data-hindsight-status="${escapeHtml(hindsightStatus)}" data-sync-has-tags="${hasTagValues}" data-sync-has-metadata="${Boolean(Object.keys(values).length)}" data-metadata-stale="${stale}">
    <summary>Modifier les métadonnées</summary>
    <div class="metadata-editor-content">
      ${status}
      <p class="metadata-editor-help">Les valeurs enregistrées remplacent les candidats dans le Cockpit et restent séparées de l’analyse automatique.</p>
      <div class="metadata-fields">
        ${input("title", "Titre", candidate("title", titleCandidate), 300)}
        ${input("document_date", "Date du document", candidate("document_date", fields.document_date?.value || ""), 80)}
        ${input("index", "Indice / version", candidate("index", fields.index?.value || card.index || ""), 80)}
        ${input("issuer", "Émetteur", candidate("issuer", issuerCandidate), 250)}
        ${input("recipient", "Destinataire", candidate("recipient", recipientCandidate), 250)}
        ${input("family", "Famille", candidate("family", classification.family || ""), 100)}
        ${input("document_type", "Type de document", candidate("document_type", classification.document_type || card.document_type || ""), 120)}
        ${list("corps_etat", "Corps d’état", listValue("corps_etat", preflight.corps_etat_candidates))}
        ${list("sujet_technique", "Sujets techniques", listValue("sujet_technique", preflight.sujet_technique_candidates))}
        <label class="metadata-field metadata-field-wide"><span>Résumé</span>${fieldControl("summary", `<textarea rows="3" maxlength="1200" data-metadata-field="summary" data-metadata-previous-value="${escapeHtml(candidate("summary", summaryCandidate))}">${escapeHtml(candidate("summary", summaryCandidate))}</textarea>`, "Résumé")}</label>
      </div>
      <div class="document-note-actions"><button type="button" data-save-document-metadata>Enregistrer les métadonnées</button><button type="button" class="secondary" data-restore-automatic-metadata${Object.keys(values).length ? "" : " disabled"}>Rétablir les valeurs automatiques</button><span role="status" aria-live="polite" data-document-metadata-status></span></div>
      ${syncActions}
      <small>Vider un champ puis enregistrer l’efface volontairement. « Rétablir les valeurs automatiques » supprime toutes les corrections et tous les effacements de ce document.</small>
    </div>
  </details>`;
}

function metadataHasTagValues(values) {
  return ["family", "document_type", "corps_etat", "sujet_technique"].some((key) => Object.hasOwn(values || {}, key));
}

function trackMetadataFieldEdit(field) {
  field.dataset.metadataExplicitNull = String(
    !field.value.trim() && field.value !== (field.dataset.metadataPreviousValue || ""),
  );
  const reset = field.closest(".metadata-field-control")?.querySelector("[data-metadata-field-reset]");
  if (reset) reset.disabled = field.value === (field.dataset.metadataPreviousValue || "");
}

function updateMetadataSyncAvailability(editor, values, stale = false, deleted = false) {
  const hasValues = !deleted && Object.keys(values || {}).length > 0;
  editor.dataset.syncHasTags = String(hasValues && metadataHasTagValues(values));
  editor.dataset.syncHasMetadata = String(hasValues);
  editor.dataset.metadataStale = String(stale);
  refreshMetadataSyncButtons(editor);
}

function refreshMetadataSyncButtons(editor) {
  const stale = editor.dataset.metadataStale === "true";
  const ready = editor.dataset.hindsightStatus === "MEMORIZED" && !stale;
  editor.querySelectorAll("[data-hindsight-metadata-sync]").forEach((button) => {
    button.disabled = !ready || (button.dataset.hindsightMetadataSync === "tags"
      ? editor.dataset.syncHasTags !== "true"
      : editor.dataset.syncHasMetadata !== "true");
  });
}

function openSharedMetadataEditor(workspace, path) {
  const card = allCards().find((item) => item.workspace === workspace && item.path === path)
    || processingData.items.find((item) => item.workspace === workspace && item.source_path === path);
  if (!card || card.source_present === false) return;
  const editableCard = {
    ...card,
    path,
    name: card.name || path.split("/").filter(Boolean).at(-1),
    // Processing-queue rows do not carry the card-view source flag; an indexed
    // row is editable and the server revalidates source availability on save.
    source_present: card.source_present !== false,
  };
  const mount = document.getElementById("metadata-editor-mount");
  const dialog = document.getElementById("metadata-editor-dialog");
  mount.innerHTML = documentMetadataEditor(editableCard, card.preflight_metadata || {});
  const editor = mount.querySelector("[data-document-metadata]");
  if (editor) editor.open = true;
  document.getElementById("metadata-dialog-title").textContent = `Métadonnées · ${editableCard.name}`;
  showCockpitDialog(dialog);
}

function openDocumentSource(workspace, path) {
  const href = workspaceUrl(`api/source?workspace=${encodeURIComponent(workspace)}&path=${encodeURIComponent(path)}`);
  window.open(href, "_blank", "noopener");
}

function openCardSource(workspace, path) {
  const card = allCards().find((item) => item.workspace === workspace && item.path === path);
  if (/\.pdf$/i.test(path) && card) {
    void openDocumentReader({ ...card, source_path: card.source_path || card.path }, "pdf");
    return;
  }
  openDocumentSource(workspace, path);
}

function documentCardBody(card) {
  const preflight = card.preflight_metadata || {};
  const overrideValues = card.metadata_override?.values || {};
  const preflightFields = preflight.fields || {};
  const preflightClassification = preflight.document_classification || {};
  const confirmed = (key, fallback) => Object.hasOwn(overrideValues, key)
    ? (overrideValues[key] ?? "")
    : (fallback ?? "");
  const details = [
    card.phase,
    confirmed("index", card.index || preflightFields.index?.value) ? `Indice ${confirmed("index", card.index || preflightFields.index?.value)}` : "",
    confirmed("document_date", card.document_date || preflightFields.document_date?.value),
    !preflightClassification.document_type ? confirmed("document_type", card.document_type) : "",
  ].filter(Boolean);

  const cardSummary = usablePreflightSummary({ document_summary_candidate: { value: card.summary } });
  const summary = !Object.hasOwn(overrideValues, "summary") && !usablePreflightSummary(preflight) && cardSummary
    ? `<p class="card-summary">${escapeHtml(cardSummary)}</p>`
    : "";
  const preflightFallbackStatus = String(card.extension || "").toLocaleLowerCase("en") === ".pdf"
    ? "not_run"
    : "not_pdf";
  const preflightDetails = preflightTemplate(preflight, preflightFallbackStatus, overrideValues);
  return `
    ${searchResultPath(card)}
    <div class="document-meta">
      ${card.extension ? `<span class="file-type">${escapeHtml(card.extension.replace(/^\./, "").toLocaleUpperCase("fr"))}</span>` : ""}
      ${details.length ? `<span>${escapeHtml(details.join(" · "))}</span>` : ""}
    </div>
    <div class="document-front-summary">${preflightDetails}${summary}</div>
    ${hermesDiscussionsTemplate(card)}
  `;
}

function documentCardBack(card) {
  const preflight = card.preflight_metadata || {};
  const overrideValues = card.metadata_override?.values || {};
  const preflightFields = preflight.fields || {};
  const confirmed = (key, fallback) => Object.hasOwn(overrideValues, key)
    ? (overrideValues[key] ?? "")
    : (fallback ?? "");
  const facts = [
    card.source_present ? (card.source && card.source !== card.name ? fact("Source", card.source) : "") : fact("Source", "Manquante", "fact-alert"),
    card.cartouche_present ? fact("Cartouche", card.cartouche) : "",
    fact("Identité déclarée", card.document_id),
    fact("Identité technique", card.technical_document_id),
    fact("État de mémorisation", card.hindsight_status || (card.hindsight_eligible ? "Non synchronisé" : "Non éligible"), card.hindsight_last_error ? "fact-alert" : ""),
    card.hindsight_ocr_needed
      ? fact("Décryptage", "À demander pour ce fichier", "fact-alert")
      : card.hindsight_extraction_quality && card.hindsight_extraction_quality !== "NOT_CHECKED"
        ? fact("Décryptage", card.hindsight_extraction_quality, "fact-muted")
        : "",
    fact(
      "Reclassement",
      card.hindsight_reclassification_required
        ? `${card.hindsight_previous_project || "sans projet"} → ${card.hindsight_requested_project || "sans projet"} — confirmation requise`
        : "",
      "fact-alert",
    ),
    fact("Émetteur", confirmed("issuer", card.issuer || preflight.issuer_candidates?.[0]?.value)),
    fact("Destinataire", confirmed("recipient", preflightFields.recipient?.value)),
    fact(
      card.revision_mode === "supersedes" ? "Remplace" : card.revision_mode === "supplements" ? "Complète" : "Relation",
      card.revision_of,
      card.revision_target_status === "MISSING" || card.revision_target_status === "AMBIGUOUS" ? "fact-alert" : "",
    ),
  ].join("");
  const hindsightTags = hindsightTagGroups(card.hindsight_tags_projected === null || card.hindsight_tags_projected === undefined ? null : { values: card.hindsight_tags_projected, projectionState: card.hindsight_tags_projection_state });
  const reconcile = card.status === "COMPLETE"
    && card.document_id
    && card.hindsight_representation_candidate === "source"
    ? `<div class="reconcile-action" data-reconcile-document="${escapeHtml(card.document_id)}">
        <label><span>Focus optionnel</span><input type="text" maxlength="2000" data-reconcile-focus placeholder="Ex. vérifier les contradictions de dates"></label>
        <button type="button" data-reconcile-button>Réconcilier avec Hermes</button>
        <small>Analyse transitoire de la mémoire Hindsight. La source NAS n’est pas ouverte.</small>
        <div class="reconcile-result" data-reconcile-result hidden></div>
      </div>`
    : "";
  return `<div class="document-back-content">
    ${tagsTemplate(card.tags, "Tags déclarés dans le cartouche")}
    ${hindsightTags}
    ${facts ? `<div class="facts">${facts}</div>` : ""}
    ${documentNoteEditor(card)}
    ${reconcile}
  </div>`;
}

function folderCardBody(card) {
  const summary = card.summary ? `<p class="card-summary">${escapeHtml(card.summary)}</p>` : "";
  const facts = [
    fact("Chemin", card.path),
    fact("Cartouche dossier", card.folder_context_present ? (card.folder_context || "_folder.md") : "Absent", card.folder_context_present ? "" : "fact-muted"),
    fact("Phase", card.phase),
    fact("Projet", card.project),
  ].join("");
  const open = `<button class="folder-open" type="button" data-folder-path="${escapeHtml(card.path)}" aria-label="Ouvrir le dossier ${escapeHtml(card.title || card.name)}">Ouvrir <span aria-hidden="true">↓</span></button>`;
  return `
    ${searchResultPath(card)}
    ${summary}
    ${tagsTemplate(card.tags, "Tags du contexte dossier")}
    <div class="facts folder-facts">${facts}</div>
    ${hermesDiscussionsTemplate(card)}
    ${open}
  `;
}

function cardTemplate(card) {
  const warnings = card.warnings?.length
    ? `<ul class="warnings">${card.warnings.map((warning) => `<li>${escapeHtml(warning)}</li>`).join("")}</ul>`
    : "";
  const isFolder = card.kind === "folder";
  const body = isFolder ? folderCardBody(card) : documentCardBody(card);
  const backBody = isFolder ? (warnings || "") : documentCardBack(card);
  const stage = card.kind === "document" ? processingStage(card) : null;
  const subtitle = card.kind === "folder" ? "" : card.subtitle || "";
  const visibleSubtitle = card.status === "FOLDER_SCOPED" && /contexte h[eé]rit[eé]/i.test(subtitle) ? "" : subtitle;
  const title = card.title || card.name;
  const heading = isFolder
    ? `<span class="folder-card-icon" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false"><path d="${CARD_ICONS.folder}"></path></svg></span><span class="folder-card-title-text">${escapeHtml(title)}/</span>`
    : escapeHtml(title);
  const actions = `<div class="card-document-actions">
      ${!isFolder ? actionIconButton("open", "Ouvrir l’original", `data-open-source data-workspace="${escapeHtml(card.workspace)}" data-source-path="${escapeHtml(card.path)}"${card.source_present === false ? " disabled" : ""}`) : ""}
      ${!isFolder ? actionIconButton("edit", "Éditer les métadonnées", `data-open-metadata-editor data-workspace="${escapeHtml(card.workspace)}" data-source-path="${escapeHtml(card.path)}"${card.source_present === false ? " disabled" : ""}`) : ""}
      ${hermesChatButton(card)}
    </div>`;
  const classes = [
    "card",
    card.kind === "folder" ? "folder-card" : "document-card",
    card.status === "SOURCE_ONLY" ? "source-only" : "",
    card.status === "SOURCE_MISSING" ? "missing-source" : "",
  ].filter(Boolean).join(" ");

  return `<article class="${classes}" data-status="${escapeHtml(card.status)}" data-card-path="${escapeHtml(card.path)}">
    <div class="card-heading">
      <div class="card-head">
        <div class="card-kicker"><span class="card-label-icons">${stage ? cardLabelIcon(stage.icon, stage.label, stage.color, stage.pulse) : ""}${cardLabelIcon(STATUS[card.status]?.icon, STATUS[card.status]?.label || card.status, STATUS[card.status]?.color || "")}</span>${actions}</div>
        ${title ? `<h2${isFolder ? ' class="folder-card-title"' : ""} title="${escapeHtml(`${title}${isFolder ? "/" : ""}`)}">${heading}</h2>` : ""}
      </div>
      ${visibleSubtitle ? `<p class="subtitle card-subtitle">${escapeHtml(visibleSubtitle)}</p>` : ""}
    </div>
    <div class="card-face card-front">${body}<button class="card-turn" type="button" data-card-turn aria-label="Afficher les détails">Détails ↗</button></div>
    <div class="card-face card-back" hidden><div class="card-back-head"><strong>${isFolder ? "Détails du dossier" : "Détails du document"}</strong><button class="card-turn" type="button" data-card-turn aria-label="Revenir au recto">Retour ↩</button></div>${backBody}${isFolder ? "" : warnings}${card.path ? `<div class="card-back-path">${escapeHtml(card.path)}</div>` : ""}</div>
  </article>`;
}

function canReanalyze(value, preflight) {
  return Boolean(value)
    && !["MEMORIZING", "MEMORIZED", "ARCHIVED", "VERIFY", "OCR_PROCESSING"].includes(String(value || "").toUpperCase())
    && String(preflight || "").toUpperCase() !== "ANALYZING";
}

function processingStage(card) {
  const queue = String(card.processing_queue_status || "").toUpperCase();
  const hindsight = String(card.hindsight_status || "").toUpperCase();
  const preflight = String(card.preflight_status || "").toUpperCase();
  const ocr = String(card.ocr_status || "").toUpperCase();
  if (queue === "VERIFY") return { label: "À vérifier", icon: "circle-warning", color: "red", pulse: true };
  if (queue === "VERIFYING" || hindsight === "VERIFYING") return { label: "Vérification de la mémorisation", icon: "loading", color: "yellow", pulse: true };
  if (queue === "OCR_PROCESSING" || ocr === "PROCESSING") return { label: "Décryptage en cours", icon: "loading", color: "blue", pulse: true };
  if (queue === "OCR_READY" || (ocr === "READY" && preflight === "ANALYZING")) return { label: "Analyse du texte décrypté", icon: "loading", color: "blue", pulse: true };
  if (queue === "ANALYZING" || preflight === "ANALYZING") return { label: "Analyse en cours", icon: "loading", color: "yellow", pulse: true };
  if (["MEMORIZING", "SUBMITTING", "SUBMITTED", "PENDING", "PROCESSING"].includes(queue) || ["SUBMITTING", "SUBMITTED", "PENDING", "PROCESSING"].includes(hindsight)) return { label: "Mémorisation en cours", icon: "loading", color: "blue", pulse: true };
  if (queue === "UNAVAILABLE") return { label: "Mémorisation indisponible · réessai automatique", icon: "cloud-off", color: "yellow" };
  if (queue === "FAILED") return { label: "Échec", icon: "circle-close", color: "red" };
  if (["MODIFIED", "STABILIZING"].includes(queue)) return { label: queue === "STABILIZING" ? "Stabilisation" : "Fichier modifié", icon: queue === "STABILIZING" ? "clock" : "file-edit", color: "magenta", pulse: queue === "STABILIZING" };
  if (queue === "MEMORIZED") return { label: "Mémorisé", icon: "circle-check", color: "green" };
  if (queue === "QUEUED") return { label: "Analysé", icon: "clock", color: "blue" };
  if (queue === "ANALYZED") return { label: "Analysé", icon: "circle-check", color: "blue" };
  const sync = hindsight;
  const preflightMetadata = card.preflight_metadata || {};
  if (sync === "UNAVAILABLE") return { label: "Mémorisation indisponible · réessai automatique", icon: "cloud-off", color: "yellow" };
  if (["FAILED", "CANCELLED", "SUBMIT_ERROR"].includes(sync)) return { label: "Échec", icon: "circle-close", color: "red" };
  if (["STALE", "SOURCE_CHANGED"].includes(sync)) return { label: "Fichier modifié", icon: "file-edit", color: "magenta" };
  if (sync === "COMPLETED") return { label: "Mémorisé", icon: "circle-check", color: "green" };
  if (["SUBMITTED", "PENDING", "PROCESSING"].includes(sync)) return { label: "Mémorisation en cours", icon: "loading", color: "blue", pulse: true };
  if (sync === "QUEUED") return { label: "Analysé", icon: "clock", color: "blue" };
  if (preflightMetadata.status === "running") return { label: "Analyse en cours", icon: "loading", color: "yellow", pulse: true };
  if (preflightMetadata.status && !["not_run", "not_pdf", "no_native_text", "extractor_unavailable", "read_failed"].includes(preflightMetadata.status)) return { label: "Analysé", icon: "circle-check", color: "blue" };
  if (["BLOCKED", "RECLASSIFICATION_REQUIRED"].includes(sync)) return { label: "À vérifier", icon: "circle-warning", color: "red", pulse: true };
  return { label: "À traiter", icon: "file", color: "yellow" };
}

function allCards() {
  return state.children?.cards || [];
}

function filteredCards(source) {
  const terms = state.query.trim().split(/\s+/).filter(Boolean).map(foldSearchText);
  return (source || []).filter((card) => {
    const workspaceMatch = card.workspace === state.workspace;
    const statusMatch = state.status === "all" || card.status === state.status;
    const preflight = card.preflight_metadata || {};
    const overrideValues = card.metadata_override?.values || {};
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
      card.project,
      card.phase,
      card.issuer,
      card.document_type,
      preflight.document_title_candidate?.value,
      preflight.document_summary_candidate?.value,
      preflight.document_classification?.family,
      preflight.document_classification?.document_type,
      ...Object.values(preflight.fields || {}).map((item) => item?.value),
      ...(preflight.corps_etat_candidates || []).map((item) => item.value),
      ...(preflight.sujet_technique_candidates || []).map((item) => item.value),
      ...Object.values(overrideValues).flat(Infinity),
      ...(card.tags || []),
      ...(card.hindsight_tags_projected || []),
    ].filter(Boolean).join(" ");
    const foldedText = foldSearchText(text);
    return workspaceMatch && statusMatch && terms.every((term) => foldedText.includes(term));
  });
}

function foldSearchText(value) {
  return String(value ?? "").normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("fr");
}

function searchResultPath(card) {
  return state.query.trim() && card.path
    ? `<p class="search-result-path">${escapeHtml(card.path)}</p>`
    : "";
}

function renderCards() {
  const levels = state.navigationLevels;
  const currentLevel = levels.at(-1);
  elements.cards.innerHTML = currentLevel ? navigationLevelMarkup(currentLevel) : "";
  elements.cards.hidden = levels.length === 0;
  elements.empty.hidden = levels.length !== 0;
  renderBreadcrumbs();
  renderFolderPager();
  initializeNavigationSwipers();
}

// 4. Navigation hiérarchique et Swiper
function navigationLevelMarkup(level) {
  const cards = filteredCards(level.children?.cards);
  const pathParts = String(level.path || "").split("/").filter(Boolean);
  const ancestorParts = pathParts.slice(-2);
  const ancestorStart = pathParts.length - ancestorParts.length;
  const ancestors = ancestorParts.length
    ? `<div class="folder-ancestor-stack" aria-label="Dossiers parents">${ancestorParts.map((part, partIndex) => {
        const ancestorPath = pathParts.slice(0, ancestorStart + partIndex + 1).join("/");
        return `<button class="folder-ancestor" type="button" data-parent-card-path="${escapeHtml(ancestorPath)}" aria-label="Afficher la fiche du dossier ${escapeHtml(part)}" title="${escapeHtml(part)}/"><span class="folder-ancestor-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="${CARD_ICONS.folder}"></path></svg></span><span>${escapeHtml(part)}/</span></button>`;
      }).join("")}</div>`
    : "";
  const deck = cards.length
    ? `<div class="swiper sibling-swiper"><div class="swiper-wrapper">${cards.map((card) => `<div class="swiper-slide sibling-slide">${cardTemplate(card)}</div>`).join("")}</div><div class="sibling-navigation"><button class="sibling-nav-prev" type="button" aria-label="Fiche précédente" title="Fiche précédente">‹</button><div class="swiper-pagination" aria-live="polite"></div><button class="sibling-nav-next" type="button" aria-label="Fiche suivante" title="Fiche suivante">›</button></div></div>`
    : '<p class="message">Aucun élément dans ce niveau.</p>';
  return `<section class="navigation-level" data-level-path="${escapeHtml(level.path)}">${ancestors}${deck}</section>`;
}

function renderFolderPager() {
  const total = state.children?.total || 0;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const page = Math.floor(state.offset / PAGE_SIZE) + 1;
  const currentCards = filteredCards(allCards());
  const visibleTotal = state.query.trim() || state.status === "all" ? total : currentCards.length;
  elements["folder-pager"].hidden = visibleTotal <= PAGE_SIZE;
  elements["page-label"].textContent = `Page ${page} / ${pageCount} · ${visibleTotal} éléments frères`;
  elements["page-previous"].disabled = state.offset <= 0;
  elements["page-next"].disabled = state.offset + PAGE_SIZE >= total;
}

function setChoiceMenuOpen(container, activeButton, alternateButtons, open) {
  if (!container || !activeButton) return;
  container.dataset.expanded = String(open);
  container.classList.toggle("is-expanded", open);
  activeButton.setAttribute("aria-expanded", String(open));
  for (const button of alternateButtons) button.hidden = !open;
}

function toggleChoiceMenu(container, activeButton, alternateButtons) {
  const open = container?.dataset.expanded !== "true";
  setChoiceMenuOpen(container, activeButton, alternateButtons, open);
  return open;
}

function setVaultChoiceMenuOpen(open) {
  if (!vaultSwitch) return;
  vaultSwitchExpanded = Boolean(open);
  const activeButton = vaultSwitch.querySelector('.workspace-vault-toggle[aria-pressed="true"]');
  const alternatives = [...vaultSwitch.querySelectorAll('.workspace-vault-toggle:not([aria-pressed="true"])')];
  setChoiceMenuOpen(vaultSwitch, activeButton, alternatives, vaultSwitchExpanded);
  if (activeButton) {
    const name = activeButton.dataset.vaultToggle;
    const instruction = vaultSwitchExpanded ? "masquer les autres vaults" : "afficher les autres vaults";
    activeButton.setAttribute("aria-label", `${name} · ${instruction}`);
    activeButton.title = `${name} · ${instruction}`;
  }
}

function renderVaultSwitch() {
  if (!state.data || !vaultSwitch) return;
  const names = state.data.workspaces.map(({ name }) => name);
  const selected = names.includes(state.workspace) ? state.workspace : names[0];
  vaultSwitch.replaceChildren(...[selected, ...names.filter((name) => name !== selected)].map((name) => {
    const library = name.toLocaleLowerCase("fr").startsWith("biblioth");
    const button = document.createElement("button");
    button.type = "button";
    button.className = `workspace-vault-toggle ${library ? "is-bibliotheque" : "is-affaires"}`;
    button.dataset.vaultToggle = name;
    const active = name === selected;
    button.addEventListener("click", () => {
      if (active) {
        setVaultChoiceMenuOpen(!vaultSwitchExpanded);
        return;
      }
      toggleVaultVisibility(name);
    });
    button.hidden = !active && !vaultSwitchExpanded;
    button.setAttribute("aria-pressed", String(active));
    const activeLabel = vaultSwitchExpanded ? "masquer les autres vaults" : "afficher les autres vaults";
    button.setAttribute("aria-label", active ? `${name} · ${activeLabel}` : name);
    if (active) button.setAttribute("aria-expanded", String(vaultSwitchExpanded));
    button.title = active ? `${name} · ${activeLabel}` : name;
    button.innerHTML = library
      ? '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5h10.5v14H4zM14.5 7H20v12h-5.5M7 9h4.5M7 12h4.5M7 15h4.5"/></svg><span class="visually-hidden"></span>'
      : '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 8h18v12H3zM8 8V5h8v3M3 12h18M10 12v2h4v-2"/></svg><span class="visually-hidden"></span>';
    button.querySelector("span").textContent = name;
    return button;
  }));
  setVaultChoiceMenuOpen(vaultSwitchExpanded);
}

function toggleVaultVisibility(name) {
  const names = state.data?.workspaces.map((item) => item.name) || [];
  if (!names.includes(name)) return;
  if (name === state.workspace) {
    vaultSwitchExpanded = !vaultSwitchExpanded;
    renderVaultSwitch();
    return;
  }
  state.workspace = name;
  visibleVaults.clear();
  visibleVaults.add(name);
  vaultSwitchExpanded = false;
  renderVaultSwitch();
  vaultSwitch.querySelector(`[data-vault-toggle="${CSS.escape(name)}"]`)?.focus();
  state.path = "";
  state.offset = 0;
  state.levelCache = Object.create(null);
  state.navigationLevels = [];
  if (processingView.hidden) void loadChildren();
  else {
    updateProcessingFilterOptions();
    renderProcessingItems();
  }
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
    `<div class="count" data-status="${name}"><strong>${state.data.totals[name] || 0}</strong><span>${item.label}</span></div>`,
  ).join("");
}

function renderBreadcrumbs() {
  const crumbs = state.workspace ? [{ label: state.workspace, path: "" }] : [];
  const parts = state.path ? state.path.split("/") : [];
  let current = "";
  for (const part of parts) {
    current = current ? `${current}/${part}` : part;
    crumbs.push({ label: part, path: current });
  }
  elements.breadcrumbs.hidden = crumbs.length === 0;
  elements.breadcrumbs.innerHTML = crumbs.map((crumb, index) =>
    `${index ? '<span class="breadcrumb-separator" aria-hidden="true">›</span>' : ""}${index === crumbs.length - 1 ? `<span aria-current="page">${escapeHtml(crumb.label)}</span>` : `<button type="button" data-breadcrumb-path="${escapeHtml(crumb.path)}">${escapeHtml(crumb.label)}</button>`}`,
  ).join("");
}

function initializeNavigationSwipers() {
  for (const swiper of state.siblingSwipers) swiper.destroy(true, true);
  state.siblingSwipers = [];
  if (elements.cards.hidden) return;
  const target = state.focusCardPath
    ? [...elements.cards.querySelectorAll("[data-card-path]")]
      .find((card) => card.dataset.cardPath === state.focusCardPath)
    : null;
  if (typeof window.Swiper !== "function") {
    if (target) {
      target.scrollIntoView({ block: "start", behavior: "smooth" });
    }
    state.focusCardPath = "";
    return;
  }
  let focused = false;
  for (const deck of elements.cards.querySelectorAll(".sibling-swiper")) {
    const swiper = createNavigationSwiper(deck);
    state.siblingSwipers.push(swiper);
    if (state.focusCardPath) {
      const targetIndex = [...deck.querySelectorAll(".sibling-slide")]
        .findIndex((slide) => slide.querySelector("[data-card-path]")?.dataset.cardPath === state.focusCardPath);
      if (targetIndex >= 0) {
        swiper.slideTo(targetIndex, 0, false);
        focused = true;
      }
    }
  }
  if (focused || state.focusCardPath) state.focusCardPath = "";
}

function createNavigationSwiper(deck) {
  return new window.Swiper(deck, {
    slidesPerView: 1, spaceBetween: 16, watchOverflow: true,
    noSwipingSelector: "button, a, input, textarea, select",
    keyboard: { enabled: true, onlyInViewport: true },
    pagination: { el: deck.querySelector(".swiper-pagination"), type: "fraction" },
    navigation: { prevEl: deck.querySelector(".sibling-nav-prev"), nextEl: deck.querySelector(".sibling-nav-next") },
  });
}

function navigateIntoFolder(path) {
  if (!path || path === state.path) return;
  state.path = path;
  state.offset = 0;
  void loadChildren();
}

function navigateToPath(path) {
  state.requestId++;
  const levelIndex = state.navigationLevels.findIndex((level) => level.path === path);
  if (levelIndex >= 0) {
    const level = state.navigationLevels[levelIndex];
    state.navigationLevels = state.navigationLevels.slice(0, levelIndex + 1);
    state.path = level.path;
    state.children = level.children;
    state.offset = level.offset || 0;
    renderCards();
    return;
  }
  state.path = path;
  state.offset = 0;
  state.navigationLevels = [];
  void loadChildren();
}

function returnToFolderCard(cardPath) {
  const value = String(cardPath || "");
  const separator = value.lastIndexOf("/");
  const containingPath = separator >= 0 ? value.slice(0, separator) : "";
  state.focusCardPath = value;
  navigateToPath(containingPath);
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
    // Keep folders navigable as a static list when Swiper is unavailable.
  }
  document.documentElement.dataset.swiperReady = "false";
  return false;
}

async function loadChildren() {
  const requestId = ++state.requestId;
  const path = state.path;
  const offset = state.offset;
  elements.loading.hidden = false;
  elements.error.hidden = true;
  elements.cards.hidden = state.navigationLevels.length === 0;
  elements.empty.hidden = true;
  try {
    const params = new URLSearchParams({ workspace: state.workspace, path, offset: String(offset), limit: String(PAGE_SIZE), q: state.query.trim() });
    const response = await fetch(workspaceUrl(`api/workspace-children?${params}`), { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const result = await response.json();
    if (requestId !== state.requestId) return;
    state.children = result;
    state.levelCache[path] = { ...result, offset };
    const existingLevel = state.navigationLevels.findIndex((level) => level.path === path);
    if (existingLevel >= 0) {
      state.navigationLevels = state.navigationLevels.slice(0, existingLevel);
    } else {
      const parentPath = path.includes("/") ? path.slice(0, path.lastIndexOf("/")) : "";
      const parentLevel = state.navigationLevels.findIndex((level) => level.path === parentPath);
      state.navigationLevels = parentLevel >= 0 ? state.navigationLevels.slice(0, parentLevel + 1) : [];
    }
    state.navigationLevels.push({ path, offset, children: result });
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
    renderSummary(); filtersTemplate();
    const names = state.data.workspaces.map((item) => item.name);
    if (!names.includes(state.workspace)) state.workspace = names[0] || "";
    visibleVaults.clear();
    if (state.workspace) visibleVaults.add(state.workspace);
    vaultSwitchExpanded = false;
    renderVaultSwitch();
    state.path = "";
    state.offset = 0;
    state.levelCache = Object.create(null);
    state.navigationLevels = [];
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

// 5. Réconciliation, notes et corrections de métadonnées
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

async function saveDocumentNote(button) {
  const editor = button.closest("[data-document-note]");
  const input = editor?.querySelector("[data-document-note-input]");
  const status = editor?.querySelector("[data-document-note-status]");
  if (!editor || !input || !status) return;
  button.disabled = true;
  status.textContent = "Enregistrement…";
  try {
    const response = await fetch(workspaceUrl("api/document-notes"), {
      method: "POST",
      cache: "no-store",
      headers: { "Content-Type": "application/json", "X-Pantheon-Intent": "document-note-save" },
      body: JSON.stringify({ workspace: editor.dataset.noteWorkspace, path: editor.dataset.notePath, note: input.value }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    const card = allCards().find((item) => item.workspace === editor.dataset.noteWorkspace && item.path === editor.dataset.notePath);
    if (card) {
      if (payload.status === "deleted") delete card.document_note;
      else card.document_note = payload.note;
    }
    status.textContent = payload.status === "deleted" ? "Note effacée." : "Note enregistrée.";
  } catch (_error) {
    status.textContent = "Échec de l’enregistrement. Vérifiez l’accès au Cockpit et au fichier.";
  } finally {
    button.disabled = false;
  }
}

async function saveDocumentMetadata(button) {
  const editor = button.closest("[data-document-metadata]");
  const status = editor?.querySelector("[data-document-metadata-status]");
  if (!editor || !status) return;
  const values = {};
  editor.querySelectorAll("[data-metadata-field]").forEach((field) => {
    const key = field.dataset.metadataField;
    if (key === "corps_etat" || key === "sujet_technique") {
      const entries = field.value.split(/[\n;,]+/).map((item) => item.trim()).filter(Boolean);
      if (entries.length) values[key] = entries;
      else if (field.dataset.metadataExplicitNull === "true") values[key] = null;
    } else if (field.value.trim()) {
      values[key] = field.value;
    } else if (field.dataset.metadataExplicitNull === "true") {
      values[key] = null;
    }
  });
  const scalarLimits = { title: 300, document_date: 80, index: 80, issuer: 250, recipient: 250, family: 100, document_type: 120, summary: 1200 };
  for (const [key, limit] of Object.entries(scalarLimits)) {
    if (String(values[key] || "").trim().length > limit) {
      status.textContent = `Le champ « ${editor.querySelector(`[data-metadata-field="${key}"]`)?.closest("label")?.querySelector("span")?.textContent || key} » dépasse ${limit} caractères.`;
      editor.querySelector(`[data-metadata-field="${key}"]`)?.focus();
      return;
    }
  }
  for (const key of ["corps_etat", "sujet_technique"]) {
    const field = editor.querySelector(`[data-metadata-field="${key}"]`);
    const label = field?.closest("label")?.querySelector("span")?.textContent || key;
    if ((values[key] || []).length > 20) {
      status.textContent = `« ${label} » accepte au maximum 20 valeurs.`;
      field?.focus();
      return;
    }
    if ((values[key] || []).some((value) => value.length > 100)) {
      status.textContent = `Chaque valeur de « ${label} » doit rester sous 100 caractères.`;
      field?.focus();
      return;
    }
  }
  button.disabled = true;
  status.textContent = "Enregistrement…";
  try {
    const response = await fetch(workspaceUrl("api/document-metadata-overrides"), {
      method: "POST",
      cache: "no-store",
      headers: { "Content-Type": "application/json", "X-Pantheon-Intent": "document-metadata-save" },
      body: JSON.stringify({ workspace: editor.dataset.metadataWorkspace, path: editor.dataset.metadataPath, values }),
    });
    const payload = await response.json();
    if (!response.ok) {
      const field = payload.field && editor.querySelector(`[data-metadata-field="${payload.field}"]`);
      const fieldLabel = field?.closest("label")?.querySelector("span")?.textContent;
      const messages = {
        metadata_value_too_long: fieldLabel ? `La valeur de « ${fieldLabel} » dépasse la limite autorisée.` : "Une valeur dépasse la limite autorisée.",
        invalid_metadata_list: fieldLabel ? `La liste « ${fieldLabel} » doit contenir au maximum 20 valeurs.` : "La liste de valeurs est invalide.",
        source_not_available: "Le fichier source n’est plus disponible dans cet espace.",
        workspace_index_unavailable: "L’index de cet espace est indisponible.",
        document_metadata_storage_unavailable: "La base de métadonnées est indisponible.",
        metadata_identity_conflict: "L’identité du document a changé; actualisez la page avant de modifier ses métadonnées.",
      };
      if (field) field.focus();
      throw new Error(messages[payload.error] || payload.error || `HTTP ${response.status}`);
    }
    const card = allCards().find((item) => item.workspace === editor.dataset.metadataWorkspace && item.path === editor.dataset.metadataPath);
    if (card) {
      if (payload.status === "deleted") delete card.metadata_override;
      else card.metadata_override = { values: payload.values, stale: false, updated_at: payload.updated_at };
      delete card.hindsight_metadata_sync;
    }
    const queued = processingData.items.find((item) => item.workspace === editor.dataset.metadataWorkspace && item.source_path === editor.dataset.metadataPath);
    if (queued) {
      if (payload.status === "deleted") delete queued.metadata_override;
      else queued.metadata_override = { values: payload.values, stale: false, updated_at: payload.updated_at };
      delete queued.hindsight_metadata_sync;
    }
    const savedValues = payload.status === "deleted" ? {} : (payload.values || {});
    editor.querySelectorAll("[data-metadata-field]").forEach((field) => {
      const key = field.dataset.metadataField;
      if (Object.hasOwn(savedValues, key)) {
        const saved = savedValues[key];
        field.value = saved == null ? "" : Array.isArray(saved) ? saved.join("\n") : String(saved);
      }
      field.dataset.metadataPreviousValue = field.value;
      field.dataset.metadataExplicitNull = "false";
      trackMetadataFieldEdit(field);
    });
    updateMetadataSyncAvailability(editor, savedValues, false, payload.status === "deleted");
    const syncStatus = editor.querySelector("[data-hindsight-metadata-sync-status]");
    if (syncStatus) syncStatus.textContent = payload.status === "deleted"
      ? "Enregistrez des métadonnées avant synchronisation."
      : editor.dataset.hindsightStatus === "MEMORIZED"
        ? "Corrections enregistrées; choisissez une action Hindsight."
        : "Corrections enregistrées; attendez la mémorisation dans Hindsight pour les synchroniser.";
    status.textContent = payload.status === "deleted" ? "Corrections effacées." : "Métadonnées enregistrées.";
    status.classList.toggle("is-confirmed", payload.status !== "deleted");
    status.classList.remove("is-stale");
  } catch (error) {
    status.textContent = `Échec de l’enregistrement : ${error.message || error}`;
  } finally {
    button.disabled = false;
  }
}

async function restoreAutomaticMetadata(button) {
  const editor = button.closest("[data-document-metadata]");
  const status = editor?.querySelector("[data-document-metadata-status]");
  if (!editor || !status) return;
  const confirmed = window.confirm("Rétablir les valeurs détectées automatiquement ? Toutes les corrections et tous les effacements enregistrés pour ce document seront supprimés.");
  if (!confirmed) return;
  const workspace = editor.dataset.metadataWorkspace;
  const path = editor.dataset.metadataPath;
  button.disabled = true;
  status.textContent = "Rétablissement…";
  try {
    const response = await fetch(workspaceUrl("api/document-metadata-overrides"), {
      method: "POST",
      cache: "no-store",
      headers: { "Content-Type": "application/json", "X-Pantheon-Intent": "document-metadata-save" },
      body: JSON.stringify({ workspace, path, reset: true }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    const card = allCards().find((item) => item.workspace === workspace && item.path === path);
    const queued = processingData.items.find((item) => item.workspace === workspace && item.source_path === path);
    for (const item of [card, queued]) {
      if (!item) continue;
      delete item.metadata_override;
      delete item.hindsight_metadata_sync;
    }
    const source = card || queued;
    const template = document.createElement("template");
    template.innerHTML = source
      ? documentMetadataEditor({ ...source, workspace, path, source_present: source.source_present !== false }, source.preflight_metadata || {}).trim()
      : "";
    const replacement = template.content.firstElementChild;
    if (replacement) {
      replacement.open = editor.open;
      editor.replaceWith(replacement);
      const replacementStatus = replacement.querySelector("[data-document-metadata-status]");
      if (replacementStatus) replacementStatus.textContent = "Valeurs automatiques rétablies.";
    } else {
      status.textContent = "Valeurs automatiques rétablies.";
    }
  } catch (error) {
    status.textContent = `Échec du rétablissement : ${error.message || error}`;
    button.disabled = false;
  }
}

async function syncDocumentMetadata(button) {
  const editor = button.closest("[data-document-metadata]");
  const status = editor?.querySelector("[data-hindsight-metadata-sync-status]");
  const mode = button.dataset.hindsightMetadataSync;
  if (!editor || !status || !["tags", "reingest"].includes(mode)) return;
  const confirmed = mode === "tags"
    ? window.confirm("Mettre à jour les tags Hindsight pour ce document ? Les autres tags seront conservés et les mémoires ne seront pas réingérées.")
    : window.confirm("Réingérer ce document dans Hindsight ? Le contenu sera retraité avec les métadonnées corrigées. Hindsight supprimera d’abord les mémoires actuelles de ce document, puis les reconstruira. Cette opération peut prendre du temps ou échouer.");
  if (!confirmed) return;
  const buttons = editor.querySelectorAll("[data-hindsight-metadata-sync]");
  buttons.forEach((item) => { item.disabled = true; });
  status.textContent = mode === "tags" ? "Synchronisation des tags…" : "Réingestion demandée…";
  try {
    const response = await fetch(workspaceUrl("api/document-hindsight-metadata-sync"), {
      method: "POST",
      cache: "no-store",
      headers: { "Content-Type": "application/json", "X-Pantheon-Intent": "document-hindsight-metadata-sync" },
      body: JSON.stringify({
        workspace: editor.dataset.metadataWorkspace,
        path: editor.dataset.metadataPath,
        mode,
      }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    const actionMode = payload.mode || mode;
    for (let attempt = 0; attempt < 300; attempt += 1) {
      if (payload.status === "COMPLETED") {
        status.textContent = actionMode === "tags" ? "Tags Hindsight synchronisés." : "Réingestion terminée; mémoires reconstruites.";
        return;
      }
      if (payload.status === "FAILED") throw new Error(payload.error || "La synchronisation a échoué.");
      await new Promise((resolve) => window.setTimeout(resolve, 2000));
      const stateResponse = await fetch(workspaceUrl(`api/document-hindsight-metadata-sync/${encodeURIComponent(payload.request_id)}`), { cache: "no-store" });
      const state = await stateResponse.json();
      if (!stateResponse.ok) throw new Error(state.error || `HTTP ${stateResponse.status}`);
      payload.status = state.status;
      payload.error = state.error;
      status.textContent = state.status === "SUBMITTED"
        ? (actionMode === "tags" ? "Tags synchronisés; vérification en cours…" : "Hindsight traite le document…")
        : "En attente du producteur…";
    }
    status.textContent = "La demande est toujours en cours. Actualisez la fiche pour suivre son état.";
  } catch (error) {
    const friendlyErrors = {
      document_must_be_memorized_before_sync: "Le document n’est pas encore mémorisé dans Hindsight. Vos métadonnées restent enregistrées; réessayez après sa mémorisation.",
      document_identity_or_metadata_changed: "Le document ou ses métadonnées ont changé. Actualisez la fiche avant de réessayer.",
    };
    if (error.message === "document_must_be_memorized_before_sync") {
      editor.dataset.hindsightStatus = "NOT_MEMORIZED";
      const help = editor.querySelector("[data-hindsight-metadata-sync-help]");
      if (help) help.textContent = "Le dernier état Hindsight n’est plus à jour. Fermez puis rouvrez la fiche après mémorisation pour réactiver ces actions.";
    }
    status.textContent = `Échec : ${friendlyErrors[error.message] || error.message || error}`;
  } finally {
    refreshMetadataSyncButtons(editor);
  }
}

// 6. Événements de la vue dossiers et démarrage
elements.cards.addEventListener("click", (event) => {
  const parentCard = event.target.closest("[data-parent-card-path]");
  if (parentCard) {
    returnToFolderCard(parentCard.dataset.parentCardPath);
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
  const noteButton = event.target.closest("[data-save-document-note]");
  if (noteButton) {
    void saveDocumentNote(noteButton);
    return;
  }
  const restoreMetadataButton = event.target.closest("[data-restore-automatic-metadata]");
  if (restoreMetadataButton) {
    void restoreAutomaticMetadata(restoreMetadataButton);
    return;
  }
  const metadataButton = event.target.closest("[data-save-document-metadata]");
  if (metadataButton) {
    void saveDocumentMetadata(metadataButton);
    return;
  }
  const hindsightMetadataButton = event.target.closest("[data-hindsight-metadata-sync]");
  if (hindsightMetadataButton) {
    void syncDocumentMetadata(hindsightMetadataButton);
    return;
  }
  const button = event.target.closest("[data-reconcile-button]");
  if (!button) return;
  const action = button.closest("[data-reconcile-document]");
  if (action) void runMemoryReconciliation(action);
});

elements.cards.addEventListener("input", (event) => {
  const metadataField = event.target.closest("[data-metadata-field]");
  if (!metadataField) return;
  const editor = metadataField.closest("[data-document-metadata]");
  if (!editor) return;
  const status = editor.querySelector("[data-hindsight-metadata-sync-status]");
  if (status) status.textContent = "Métadonnées modifiées; enregistrez avant synchronisation.";
  editor.querySelectorAll("[data-hindsight-metadata-sync]").forEach((syncButton) => { syncButton.disabled = true; });
});

const searchSuggestions = document.getElementById("search-suggestions");
const searchSuggestionList = document.getElementById("search-suggestions-list");
const searchSuggestionStatus = document.getElementById("search-suggestions-status");
let searchTimer;
let searchSuggestionTimer;
let searchSuggestionController = null;
let searchSuggestionRequest = 0;
let searchSuggestionResults = [];
let activeSearchSuggestion = -1;

function closeSearchSuggestions() {
  searchSuggestionRequest++;
  searchSuggestionController?.abort();
  searchSuggestionController = null;
  searchSuggestions.hidden = true;
  elements.search.setAttribute("aria-expanded", "false");
  elements.search.removeAttribute("aria-activedescendant");
  searchSuggestionList.replaceChildren();
  searchSuggestionStatus.hidden = true;
  searchSuggestionStatus.textContent = "";
  searchSuggestionResults = [];
  activeSearchSuggestion = -1;
}

function setSearchSuggestionStatus(message) {
  searchSuggestionStatus.textContent = message;
  searchSuggestionStatus.hidden = !message;
}

function renderSearchSuggestions(cards, query, total) {
  const foldedQuery = foldSearchText(query);
  const ranked = cards.map((card) => {
    const filename = String(card.name || "");
    const preflightTitle = card.preflight_metadata?.document_title_candidate?.value;
    const title = String(preflightTitle || card.title || filename);
    const foldedName = foldSearchText(filename);
    const foldedTitle = foldSearchText(title);
    const foldedPath = foldSearchText(card.path);
    let score = 7;
    if (foldedName === foldedQuery) score = 0;
    else if (foldedTitle === foldedQuery) score = 1;
    else if (foldedName.startsWith(foldedQuery)) score = 2;
    else if (foldedTitle.startsWith(foldedQuery)) score = 3;
    else if (foldedName.includes(foldedQuery)) score = 4;
    else if (foldedTitle.includes(foldedQuery)) score = 5;
    else if (foldedPath.includes(foldedQuery)) score = 6;
    return { card, filename, title, score };
  });
  ranked.sort((a, b) => a.score - b.score || String(a.card.path).localeCompare(String(b.card.path), "fr"));
  searchSuggestionResults = ranked.slice(0, 12).map((entry) => entry.card);
  activeSearchSuggestion = -1;
  elements.search.removeAttribute("aria-activedescendant");
  searchSuggestionList.replaceChildren(...ranked.slice(0, 12).map(({ card, filename, title }, index) => {
    const option = document.createElement("button");
    option.type = "button"; option.className = "search-suggestion"; option.id = `search-suggestion-${index}`;
    option.setAttribute("role", "option"); option.setAttribute("aria-selected", "false");
    option.dataset.searchSuggestionIndex = String(index);
    option.dataset.searchWorkspace = String(card.workspace || state.workspace);
    option.dataset.searchPath = String(card.path || "");
    option.dataset.searchKind = card.kind === "folder" ? "folder" : "document";
    const heading = document.createElement("span"); heading.className = "search-suggestion-title";
    const kind = document.createElement("span"); kind.className = "search-suggestion-kind";
    kind.textContent = card.kind === "folder" ? "Dossier" : "Document";
    heading.append(kind, document.createTextNode(title));
    const path = document.createElement("span"); path.className = "search-suggestion-path";
    path.textContent = `${card.workspace || state.workspace} / ${card.path || ""}`;
    option.append(heading);
    if (filename && filename !== title) {
      const file = document.createElement("span"); file.className = "search-suggestion-file";
      file.textContent = `Nom du fichier ou dossier : ${filename}`;
      option.append(file);
    }
    option.append(path);
    return option;
  }));
  searchSuggestions.hidden = false;
  elements.search.setAttribute("aria-expanded", "true");
  setSearchSuggestionStatus(searchSuggestionResults.length
    ? `${Math.min(total, searchSuggestionResults.length)} correspondance(s) affichée(s) sur ${total}. Choisissez une ligne pour ouvrir son emplacement.`
    : "Aucune correspondance dans le vault actif.");
}

async function loadSearchSuggestions(query) {
  if (query.length < 2 || !state.workspace) { closeSearchSuggestions(); return; }
  searchSuggestionController?.abort();
  const controller = new AbortController();
  searchSuggestionController = controller;
  const requestId = ++searchSuggestionRequest;
  searchSuggestions.hidden = false;
  searchSuggestionList.replaceChildren();
  elements.search.setAttribute("aria-expanded", "true");
  setSearchSuggestionStatus("Recherche des titres, noms et chemins…");
  try {
    const params = new URLSearchParams({ workspace: state.workspace, path: "", offset: "0", limit: "200", q: query });
    const response = await fetch(workspaceUrl(`api/workspace-children?${params}`), { cache: "no-store", signal: controller.signal });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const result = await response.json();
    if (requestId !== searchSuggestionRequest || query !== state.query) return;
    renderSearchSuggestions(Array.isArray(result.cards) ? result.cards : [], query, Number(result.total) || 0);
  } catch (error) {
    if (error.name === "AbortError" || requestId !== searchSuggestionRequest) return;
    searchSuggestionList.replaceChildren();
    setSearchSuggestionStatus("Suggestions momentanément indisponibles.");
  }
}

async function findSearchSuggestionPosition(workspace, parentPath, targetPath, signal) {
  const limit = 200;
  let offset = 0;
  while (true) {
    const params = new URLSearchParams({ workspace, path: parentPath, offset: String(offset), limit: String(limit) });
    const response = await fetch(workspaceUrl(`api/workspace-children?${params}`), { cache: "no-store", signal });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const result = await response.json();
    const cards = Array.isArray(result.cards) ? result.cards : [];
    const matchIndex = cards.findIndex((card) => card.path === targetPath);
    if (matchIndex >= 0) return offset + matchIndex;
    offset += cards.length;
    if (!cards.length || offset >= Number(result.total || 0)) throw new Error("entry_not_found");
  }
}

async function chooseSearchSuggestion(index) {
  const button = searchSuggestionList.querySelector(`[data-search-suggestion-index="${index}"]`);
  const suggestion = searchSuggestionResults[index];
  if (!button || !suggestion?.path) return;
  const workspace = button.dataset.searchWorkspace;
  const path = button.dataset.searchPath;
  const parentPath = String(suggestion.parent_path || "");
  searchSuggestionController?.abort();
  const controller = new AbortController();
  searchSuggestionController = controller;
  const requestId = ++searchSuggestionRequest;
  setSearchSuggestionStatus("Repérage de la fiche dans son dossier…");
  try {
    const siblingIndex = await findSearchSuggestionPosition(workspace, parentPath, path, controller.signal);
    if (requestId !== searchSuggestionRequest || !button.isConnected) return;
    closeSearchSuggestions();
    clearTimeout(searchTimer);
    clearTimeout(searchSuggestionTimer);
    state.query = "";
    state.path = parentPath;
    state.offset = Math.floor(siblingIndex / PAGE_SIZE) * PAGE_SIZE;
    state.status = "all";
    state.workspace = workspace;
    state.levelCache = Object.create(null);
    state.navigationLevels = [];
    state.focusCardPath = path;
    elements.search.value = "";
    elements["search-clear"].hidden = true;
    visibleVaults.clear();
    visibleVaults.add(workspace);
    renderVaultSwitch();
    filtersTemplate();
    if (!processingView.hidden) setProcessingView(false);
    else void loadChildren();
  } catch (error) {
    if (requestId !== searchSuggestionRequest) return;
    setSearchSuggestionStatus(error.name === "AbortError"
      ? ""
      : "Cette correspondance n’est plus disponible dans l’index. Actualisez la recherche.");
  }
}

function activateSearchSuggestion(index) {
  const options = [...searchSuggestionList.querySelectorAll("[role=option]")];
  if (!options.length) return;
  activeSearchSuggestion = Math.max(0, Math.min(index, options.length - 1));
  options.forEach((option, optionIndex) => option.setAttribute("aria-selected", String(optionIndex === activeSearchSuggestion)));
  const active = options[activeSearchSuggestion];
  elements.search.setAttribute("aria-activedescendant", active.id);
  active.scrollIntoView({ block: "nearest" });
}

elements.search.addEventListener("input", (event) => {
  state.query = event.target.value.trim();
  elements["search-clear"].hidden = !state.query;
  clearTimeout(searchTimer);
  clearTimeout(searchSuggestionTimer);
  searchSuggestionController?.abort();
  searchSuggestionController = null;
  searchSuggestionRequest++;
  searchSuggestionList.replaceChildren();
  searchSuggestionResults = [];
  activeSearchSuggestion = -1;
  elements.search.removeAttribute("aria-activedescendant");
  if (state.query.length >= 2 && state.workspace) {
    searchSuggestions.hidden = false;
    elements.search.setAttribute("aria-expanded", "true");
    setSearchSuggestionStatus("Recherche des titres, noms et chemins…");
  } else {
    closeSearchSuggestions();
  }
  searchSuggestionTimer = setTimeout(() => void loadSearchSuggestions(state.query), 180);
  if (processingView.hidden) {
    state.path = "";
    state.offset = 0;
    state.navigationLevels = [];
    state.levelCache = Object.create(null);
    searchTimer = setTimeout(() => void loadChildren(), 120);
  } else {
    renderProcessingItems();
  }
});
elements.search.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !searchSuggestions.hidden) { event.preventDefault(); closeSearchSuggestions(); return; }
  if (searchSuggestions.hidden) return;
  const count = searchSuggestionResults.length;
  if (event.key === "ArrowDown" && count) { event.preventDefault(); activateSearchSuggestion(activeSearchSuggestion + 1); }
  else if (event.key === "ArrowUp" && count) { event.preventDefault(); activateSearchSuggestion(activeSearchSuggestion < 0 ? count - 1 : activeSearchSuggestion - 1); }
  else if (event.key === "Enter" && count) { event.preventDefault(); chooseSearchSuggestion(activeSearchSuggestion < 0 ? 0 : activeSearchSuggestion); }
});
searchSuggestionList.addEventListener("click", (event) => {
  const option = event.target.closest("[data-search-suggestion-index]");
  if (option) chooseSearchSuggestion(Number(option.dataset.searchSuggestionIndex));
});
document.addEventListener("pointerdown", (event) => {
  if (!event.target.closest(".workspace-search") && !searchSuggestions.hidden) closeSearchSuggestions();
});
elements["search-clear"].addEventListener("click", () => {
  elements.search.value = "";
  elements.search.dispatchEvent(new Event("input", { bubbles: true }));
  elements.search.focus();
});
elements.refresh.addEventListener("click", () => {
  if (!processingView.hidden) {
    void loadProcessingQueue();
    return;
  }
  void load();
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
  if (state.query.trim()) {
    clearTimeout(searchTimer);
    state.query = "";
    elements.search.value = "";
    elements["search-clear"].hidden = true;
  }
  navigateIntoFolder(button.dataset.folderPath);
});
elements.breadcrumbs.addEventListener("click", (event) => {
  const button = event.target.closest("[data-breadcrumb-path]");
  if (!button) return;
  navigateToPath(button.dataset.breadcrumbPath);
});
elements["page-previous"].addEventListener("click", () => { state.offset = Math.max(0, state.offset - PAGE_SIZE); void loadChildren(); });
elements["page-next"].addEventListener("click", () => { state.offset += PAGE_SIZE; void loadChildren(); });

void loadSwiper().then(() => initializeNavigationSwipers());
load();

// 7. Activité Hermes et jalons d’exécution
const ROLE_ICONS = Object.freeze({ Athena: "🦉", Argos: "🔎", Themis: "⚖", Apollo: "☀", Hephaistos: "🛠", Iris: "📨", Zeus: "⚡", Mnemosyne: "🧠", Hermes: "⚙" });
const ROLE_ORDER = Object.freeze(["Athena", "Argos", "Hermes", "Hephaistos", "Themis", "Apollo", "Zeus", "Iris", "Mnemosyne"]);
const roleView = {
  runId: "", cursor: 0, controller: null, stages: new Map(), stageEvents: new Map(), observedOrder: new Map(),
  observationCounter: 0, activeView: "dialogue", selectedStageId: "",
  discoveryUnavailable: false, discoveryTimer: null, discoveryPending: false,
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
  if (roleView.discoveryUnavailable || roleView.discoveryPending) return;
  roleView.discoveryPending = true;
  try {
    const response = await fetch(workspaceUrl("api/role-traces/latest"), { cache: "no-store" });
    if (response.status === 404) {
      const detail = await response.json().catch(() => ({}));
      if (detail.error === "role_trace_not_configured") {
        roleView.discoveryUnavailable = true;
        window.clearInterval(roleView.discoveryTimer);
        roleState("Relais de traces non configuré");
      } else {
        roleState("Aucune trace");
      }
      return;
    }
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const trace = await response.json();
    if (trace.run_id && trace.run_id !== roleView.runId) void followRoleTrace(trace.run_id);
  } catch (_error) {
    roleState("Relais indisponible");
  } finally {
    roleView.discoveryPending = false;
  }
}

for (const button of document.querySelectorAll("[data-role-trace-view]")) {
  button.addEventListener("click", () => setRoleTraceView(button.dataset.roleTraceView));
}
setRoleTraceView("dialogue");
void loadNavigation();
void discoverLatestRoleTrace();
roleView.discoveryTimer = window.setInterval(discoverLatestRoleTrace, 5000);

// 8. État et actions du producteur source
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
    const coordinator = data.coordinator || {};
    const multivault = Boolean(coordinator.vaults && Object.keys(coordinator.vaults).length);
    if (multivault) {
      let queueLabel = "File indisponible";
      try {
        const queueResponse = await fetch(workspaceUrl("api/processing-queue"), { cache: "no-store" });
        if (queueResponse.ok) {
          const queue = await queueResponse.json();
          const globallyPaused = queue.controls?.some((control) => control.scope === "global" && control.paused);
          queueLabel = `${globallyPaused ? "pause globale" : "file active"} · ${(queue.items || []).length} élément(s)`;
        }
      } catch (_queueError) { /* Keep producer status visible if queue reads fail. */ }
      producerScopeState.textContent = coordinator.active === "active"
        ? `Coordinateur actif · ${queueLabel}`
        : "Coordinateur multivault arrêté";
    } else {
      producerScopeState.textContent = data.scope_ok ? "Portée conforme" :
        data.config_ok && affaires.active !== "active" ? "Portée prête · ingestion arrêtée" : "Portée à vérifier";
    }
    producerWarning.textContent = (data.warnings || []).join(" · ") || "";
    const rows = multivault ? [
      ["Coordinateur", `${coordinator.active || "inconnu"} · PID ${coordinator.pid || 0} · ${coordinator.process_state || "état inconnu"}`],
      ["Vault Affaires", affaires.root || affaires.configured_root || "indisponible"],
      ["Source Affaires", data.actual_source || "indisponible"],
      ["Vault Bibliothèque", bibliotheque.root || bibliotheque.configured_root || "indisponible"],
      ["Source Bibliothèque", data.library_actual_source || "indisponible"],
      ["Index partagé", coordinator.state_db || coordinator.configured_state_db || "indisponible"],
    ] : [
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
    producerConfigure.hidden = multivault || !data.expected_root || !data.expected_source;
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

// 9. File de traitement : filtres, actions, pause et ordre
// 9.1 État, filtres et libellés de la file
const processingView = document.getElementById("processing-view");
const processingToggle = document.getElementById("processing-toggle");
const folderViewToggle = document.getElementById("folder-view-toggle");
const workspaceViewSwitch = document.getElementById("workspace-view-switch");
const processingItems = document.getElementById("processing-items");
const processingProjectFilter = document.getElementById("processing-project-filter");
const processingStageTabs = document.getElementById("processing-stage-tabs");
const processingMessage = document.getElementById("processing-message");
const processingPauseList = document.getElementById("processing-pause-list");
const processingResumeList = document.getElementById("processing-resume-list");
const processingRetryAll = document.getElementById("processing-retry-all");
const processingLaneStatus = document.getElementById("processing-lane-status");
const processingLaneDialog = document.getElementById("processing-lane-dialog");
const processingLaneDialogTitle = document.getElementById("processing-lane-dialog-title");
const processingLaneDialogDescription = document.getElementById("processing-lane-dialog-description");
const processingLaneDialogStatus = document.getElementById("processing-lane-dialog-status");
const processingLaneActivityList = document.getElementById("processing-lane-activity-list");
let selectedProcessingLane = "";
let processingStatusPayload = null;
let processingData = { items: [], controls: [], revision: 0 };
let processingLaneActivityItems = [];
let processingStageFilter = "hindsight";
let processingDrag = null;
let processingOrderSaving = false;
let processingBulkRetryInProgress = false;
let processingRenderSignature = "";
const processingSorter = typeof window.Sortable === "function" ? new window.Sortable(processingItems, {
  animation: 120,
  handle: "[data-processing-handle]",
  draggable: ".processing-row",
  filter: ".processing-retry",
  preventOnFilter: false,
  forceFallback: true,
  fallbackOnBody: true,
  fallbackTolerance: 5,
  delay: 140,
  delayOnTouchOnly: true,
  touchStartThreshold: 4,
  scroll: true,
  scrollSensitivity: 72,
  scrollSpeed: 12,
  bubbleScroll: true,
  onStart: () => { processingDrag = true; },
  onEnd: ({ item, oldIndex, newIndex }) => {
    processingDrag = null;
    if (oldIndex !== newIndex && item?.dataset.workspace && item?.dataset.documentId) {
      void saveProcessingOrder([item.dataset.workspace, item.dataset.documentId]);
    }
  },
}) : null;

function processingLabel(item) {
  const status = String(item.hindsight_status || "").toUpperCase();
  const preflight = String(item.preflight_status || "").toUpperCase();
  const ocrStatus = String(item.ocr_status || "").toUpperCase();
  if (status === "NOT_MEMORIZED" && item.user_decision === "DO_NOT_SEND") {
    return { label: "Erreur ignorée · file poursuivie", color: "yellow", pulse: false };
  }
  const waitingForMemorization = status === "QUEUED"
    || (status === "OCR_READY" && preflight === "ANALYZED")
    || (!status && preflight === "ANALYZED");
  if (waitingForMemorization && processingWorkerLane(item) === "hindsight" && item.paused_hindsight) {
    return { label: "Analysé · Mémorisation en pause", color: "yellow", pulse: false };
  }
  if (ocrStatus === "READY" && preflight === "ANALYZING") return { label: "Analyse du texte décrypté", color: "blue", pulse: true };
  if (preflight === "ANALYZING") return { label: "Analyse en cours", color: "yellow", pulse: true };
  if (ocrStatus === "READY" && ["TO_PROCESS", "STABILIZING"].includes(preflight)) return { label: "Analyse du texte décrypté en attente", color: "yellow", pulse: false };
  if (ocrStatus === "FAILED") return { label: "Échec du décryptage OCR", color: "red", pulse: false };
  if (status === "OCR_READY" && preflight === "ANALYZED") return { label: "Décrypté · en attente de mémorisation", color: "blue", pulse: false };
  if (status === "VERIFY") return { label: "À vérifier", color: "red", pulse: true };
  if (status === "NOT_MEMORIZED") return { label: "Non mémorisé", color: "gray", pulse: false };
  if (status === "OCR_QUEUED") return { label: "Décryptage en attente", color: "yellow", pulse: false };
  if (status === "OCR_PROCESSING") return { label: "Décryptage en cours", color: "blue", pulse: true };
  if (status === "OCR_READY") return { label: "Analyse du texte décrypté", color: "blue", pulse: true };
  if (status === "VERIFYING") return { label: "Vérification de la mémorisation", color: "yellow", pulse: true };
  if (status === "UNAVAILABLE") return { label: "Mémorisation indisponible · réessai automatique", color: "yellow", pulse: false };
  if (status === "FAILED") return { label: "Échec", color: "red", pulse: false };
  if (preflight === "STABILIZING") return { label: "Stabilisation", color: "magenta", pulse: true };
  if (status === "MODIFIED" && item.ocr_is_revision) return { label: "Décryptage modifié · mémorisation à réaligner", color: "magenta", pulse: false };
  if (["MODIFIED", "STABILIZING"].includes(status)) return { label: status === "STABILIZING" ? "Stabilisation" : "Fichier modifié", color: "magenta", pulse: status === "STABILIZING" };
  if (["MEMORIZING", "SUBMITTING", "SUBMITTED", "PENDING", "PROCESSING"].includes(status)) return { label: "Mémorisation en cours", color: "blue", pulse: true };
  if (status === "MEMORIZED") return { label: "Mémorisé", color: "green", pulse: false };
  if (status === "QUEUED" || preflight === "ANALYZED") return { label: "Analysé · en attente de mémorisation", color: "blue", pulse: false };
  return { label: "À traiter", color: "yellow", pulse: false };
}

function processingDot(item) {
  const state = processingLabel(item);
  return `<span class="processing-stage is-${state.color}${state.pulse ? " is-pulse" : ""}"><span class="processing-dot" aria-hidden="true"></span><span>${escapeHtml(state.label)}</span></span>`;
}

// 9.1 Conversations Hermes rattachées à une fiche
const hermesChatDialog = document.getElementById("hermes-chat-dialog");
const hermesChatMessages = document.getElementById("hermes-chat-messages");
const hermesChatForm = document.getElementById("hermes-chat-form");
const hermesChatInput = document.getElementById("hermes-chat-input");
const hermesChatStatus = document.getElementById("hermes-chat-status");
const hermesChatSend = document.getElementById("hermes-chat-send");
const hermesChatTitle = document.getElementById("hermes-chat-title");
const hermesChatContext = document.getElementById("hermes-chat-context");
let hermesChatTarget = null;
let hermesChatBusy = false;

function renderHermesChatMessages(messages) {
  hermesChatMessages.replaceChildren();
  for (const message of messages || []) {
    const item = document.createElement("li");
    item.className = `hermes-chat-message is-${message.role || "assistant"}`;
    const label = document.createElement("strong");
    label.textContent = ({ user: "Vous", assistant: "Hermes", tool: "Outil", system: "Système" })[message.role] || "Hermes";
    const content = document.createElement("p");
    content.textContent = String(message.content || "");
    item.append(label, content);
    hermesChatMessages.append(item);
  }
  hermesChatMessages.scrollTop = hermesChatMessages.scrollHeight;
}

async function hermesChatRequest(path, method = "GET", body = null) {
  const response = await fetch(workspaceUrl(path), {
    method,
    cache: "no-store",
    headers: body === null ? {} : { "Content-Type": "application/json", "X-Pantheon-Intent": "hermes-chat" },
    ...(body === null ? {} : { body: JSON.stringify(body) }),
  });
  let payload = {};
  try { payload = await response.json(); } catch (_error) { /* status below is enough */ }
  if (!response.ok) throw new Error(payload.error || `Hermes indisponible · HTTP ${response.status}`);
  return payload;
}

function updateCardDiscussion(card, discussion) {
  card.hermes_discussions = Array.isArray(card.hermes_discussions) ? card.hermes_discussions : [];
  const index = card.hermes_discussions.findIndex((item) => item.session_id === discussion.session_id);
  if (index < 0) card.hermes_discussions.unshift(discussion);
  else card.hermes_discussions[index] = discussion;
  card.hermes_discussions.sort((left, right) => Number(left.archived) - Number(right.archived) || String(right.updated_at).localeCompare(String(left.updated_at)));
  renderCards();
}

async function refreshCardDiscussions(workspace, path) {
  const card = allCards().find((item) => item.workspace === workspace && item.path === path);
  if (!card) return;
  const query = new URLSearchParams({ workspace, path, include_archived: "true" });
  const payload = await hermesChatRequest(`api/hermes-chat/sessions?${query}`);
  card.hermes_discussions = Array.isArray(payload.discussions) ? payload.discussions : [];
  renderCards();
}

async function openHermesCardChat(card, discussion = null) {
  if (!card || card.hermes_chat_available !== true) return;
  hermesChatTarget = {
    card,
    sessionId: discussion?.session_id || "",
    title: discussion?.title || "",
    archived: discussion?.archived === true,
  };
  hermesChatTitle.textContent = discussion?.title || `Hermes · ${card.title || card.name}`;
  hermesChatContext.textContent = `${card.workspace} · ${card.path}`;
  hermesChatStatus.textContent = discussion?.archived ? "Discussion archivée · restaurez-la depuis la fiche pour répondre." : "";
  hermesChatInput.value = "";
  hermesChatInput.disabled = hermesChatTarget.archived;
  hermesChatSend.disabled = hermesChatTarget.archived;
  renderHermesChatMessages([]);
  showCockpitDialog(hermesChatDialog);
  if (!hermesChatTarget.sessionId) {
    hermesChatStatus.textContent = "Nouvelle discussion · votre premier message ouvrira la session Hermes.";
    hermesChatInput.focus();
    return;
  }
  hermesChatStatus.textContent = "Chargement de la discussion…";
  try {
    const payload = await hermesChatRequest(`api/hermes-chat/sessions/${encodeURIComponent(hermesChatTarget.sessionId)}/messages`);
    renderHermesChatMessages(payload.messages);
    hermesChatStatus.textContent = hermesChatTarget.archived ? "Discussion archivée · lecture seule." : "";
    if (!hermesChatTarget.archived) hermesChatInput.focus();
  } catch (error) {
    hermesChatStatus.textContent = error.message || "Lecture de la discussion impossible.";
  }
}

async function sendHermesChatMessage(event) {
  event.preventDefault();
  const text = hermesChatInput.value.trim();
  if (!text || !hermesChatTarget?.card || hermesChatBusy) return;
  hermesChatBusy = true;
  hermesChatSend.disabled = true;
  hermesChatInput.disabled = true;
  hermesChatStatus.textContent = "Hermes prépare sa réponse…";
  const creatingSession = !hermesChatTarget.sessionId;
  const previousSessionIds = new Set((hermesChatTarget.card.hermes_discussions || []).map((item) => item.session_id));
  try {
    const { card } = hermesChatTarget;
    const payload = hermesChatTarget.sessionId
      ? await hermesChatRequest(`api/hermes-chat/sessions/${encodeURIComponent(hermesChatTarget.sessionId)}/messages`, "POST", { message: text })
      : await hermesChatRequest("api/hermes-chat/sessions", "POST", { workspace: card.workspace, path: card.path, kind: card.kind, message: text });
    hermesChatTarget.sessionId = payload.discussion.session_id;
    hermesChatTarget.title = payload.discussion.title;
    updateCardDiscussion(card, payload.discussion);
    renderHermesChatMessages(payload.messages);
    hermesChatInput.value = "";
    hermesChatStatus.textContent = "";
  } catch (error) {
    if (creatingSession) {
      try {
        const { card } = hermesChatTarget;
        const query = new URLSearchParams({ workspace: card.workspace, path: card.path, include_archived: "true" });
        const indexed = await hermesChatRequest(`api/hermes-chat/sessions?${query}`);
        card.hermes_discussions = Array.isArray(indexed.discussions) ? indexed.discussions : [];
        const recovered = card.hermes_discussions.find((item) => !previousSessionIds.has(item.session_id));
        if (recovered) {
          hermesChatTarget.sessionId = recovered.session_id;
          hermesChatTarget.title = recovered.title;
          const history = await hermesChatRequest(`api/hermes-chat/sessions/${encodeURIComponent(recovered.session_id)}/messages`);
          renderHermesChatMessages(history.messages);
        }
        renderCards();
      } catch (_recoveryError) { /* keep the original Hermes failure visible */ }
    }
    hermesChatStatus.textContent = error.message || "Envoi à Hermes impossible.";
  } finally {
    hermesChatBusy = false;
    hermesChatInput.disabled = hermesChatTarget?.archived === true;
    hermesChatSend.disabled = hermesChatInput.disabled;
  }
}

hermesChatForm.addEventListener("submit", (event) => { void sendHermesChatMessage(event); });
hermesChatDialog.addEventListener("click", (event) => {
  if (event.target.closest("[data-close-hermes-chat]")) hermesChatDialog.close();
});
document.addEventListener("click", (event) => {
  const newChat = event.target.closest("[data-hermes-chat-new]");
  if (newChat) {
    const card = allCards().find((item) => item.workspace === newChat.dataset.workspace && item.path === newChat.dataset.cardPath);
    if (card) void openHermesCardChat(card);
    return;
  }
  const openChat = event.target.closest("[data-hermes-chat-open]");
  if (openChat) {
    const cardNode = openChat.closest("[data-card-path]");
    const card = allCards().find((item) => item.workspace === state.workspace && item.path === cardNode?.dataset.cardPath);
    const discussion = card?.hermes_discussions?.find((item) => item.session_id === openChat.dataset.hermesChatOpen);
    if (card && discussion) void openHermesCardChat(card, discussion);
    return;
  }
  const action = event.target.closest("[data-hermes-chat-archive], [data-hermes-chat-restore], [data-hermes-chat-delete]");
  if (!action) return;
  const cardNode = action.closest("[data-card-path]");
  const card = allCards().find((item) => item.workspace === state.workspace && item.path === cardNode?.dataset.cardPath);
  const sessionId = action.dataset.hermesChatArchive || action.dataset.hermesChatRestore || action.dataset.hermesChatDelete;
  if (!card || !sessionId) return;
  if (action.dataset.hermesChatDelete && !window.confirm("Supprimer définitivement cette discussion Hermes et son historique ?")) return;
  const operation = action.dataset.hermesChatArchive ? "archive" : action.dataset.hermesChatRestore ? "restore" : "delete";
  const body = operation === "delete" ? { confirm: true } : {};
  action.disabled = true;
  void hermesChatRequest(`api/hermes-chat/sessions/${encodeURIComponent(sessionId)}/${operation}`, "POST", body)
    .then(() => refreshCardDiscussions(card.workspace, card.path))
    .catch((error) => { window.alert(error.message || "Action Hermes impossible."); })
    .finally(() => { action.disabled = false; });
});

// 9.2 Lecteur PDF/Markdown et partage
function markdownInline(value) {
  const tokens = String(value).split(/(`[^`]+`|\*\*[^*]+\*\*|__[^_]+__|\*[^*]+\*|_[^_]+_)/g);
  return tokens.map((token) => {
    if (token.startsWith("`") && token.endsWith("`")) return `<code>${escapeHtml(token.slice(1, -1))}</code>`;
    if ((token.startsWith("**") && token.endsWith("**")) || (token.startsWith("__") && token.endsWith("__")))
      return `<strong>${escapeHtml(token.slice(2, -2))}</strong>`;
    if ((token.startsWith("*") && token.endsWith("*")) || (token.startsWith("_") && token.endsWith("_")))
      return `<em>${escapeHtml(token.slice(1, -1))}</em>`;
    return escapeHtml(token);
  }).join("");
}

function markdownTableCells(line) {
  return line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((cell) => cell.trim());
}

function renderOcrMarkdown(markdown) {
  const lines = String(markdown || "").replaceAll("\r\n", "\n").split("\n");
  const blocks = [];
  let index = 0;
  const isBlockStart = (line) => /^\s*(?:#{1,6}\s|```|>|[-*+]\s|\d+[.)]\s|(?:---+|___+|\*\*\*+)\s*$)/.test(line);

  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) { index += 1; continue; }
    if (/^\s*```/.test(line)) {
      const code = [];
      index += 1;
      while (index < lines.length && !/^\s*```/.test(lines[index])) code.push(lines[index++]);
      if (index < lines.length) index += 1;
      blocks.push(`<pre><code>${escapeHtml(code.join("\n"))}</code></pre>`);
      continue;
    }
    const heading = line.match(/^\s*(#{1,6})\s+(.+?)\s*#*\s*$/);
    if (heading) {
      const level = heading[1].length;
      blocks.push(`<h${level}>${markdownInline(heading[2])}</h${level}>`);
      index += 1;
      continue;
    }
    if (/^\s*(?:---+|___+|\*\*\*+)\s*$/.test(line)) {
      blocks.push("<hr>");
      index += 1;
      continue;
    }
    if (/^\s*>/.test(line)) {
      const quote = [];
      while (index < lines.length && /^\s*>/.test(lines[index])) quote.push(lines[index++].replace(/^\s*>\s?/, ""));
      blocks.push(`<blockquote><p>${quote.map(markdownInline).join("<br>")}</p></blockquote>`);
      continue;
    }
    if (line.includes("|") && index + 1 < lines.length) {
      const headerCells = markdownTableCells(line);
      const separator = markdownTableCells(lines[index + 1]);
      if (headerCells.length > 1 && separator.length === headerCells.length && separator.every((cell) => /^:?-{3,}:?$/.test(cell))) {
        const rows = [];
        index += 2;
        while (index < lines.length && lines[index].includes("|") && lines[index].trim()) rows.push(markdownTableCells(lines[index++]));
        const head = headerCells.map((cell) => `<th scope="col">${markdownInline(cell)}</th>`).join("");
        const body = rows.map((row) => `<tr>${headerCells.map((_cell, cellIndex) => `<td>${markdownInline(row[cellIndex] || "")}</td>`).join("")}</tr>`).join("");
        blocks.push(`<div class="ocr-markdown-table-scroll"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`);
        continue;
      }
    }
    const list = line.match(/^\s*(?:([-*+])|(\d+)[.)])\s+(.+)$/);
    if (list) {
      const ordered = Boolean(list[2]);
      const items = [];
      while (index < lines.length) {
        const entry = lines[index].match(/^\s*(?:([-*+])|(\d+)[.)])\s+(.+)$/);
        if (!entry || Boolean(entry[2]) !== ordered) break;
        items.push(`<li>${markdownInline(entry[3])}</li>`);
        index += 1;
      }
      blocks.push(`<${ordered ? "ol" : "ul"}>${items.join("")}</${ordered ? "ol" : "ul"}>`);
      continue;
    }
    const paragraph = [line.trim()];
    index += 1;
    while (index < lines.length && lines[index].trim() && !isBlockStart(lines[index])) paragraph.push(lines[index++].trim());
    blocks.push(`<p>${paragraph.map(markdownInline).join("<br>")}</p>`);
  }
  return blocks.join("") || '<p class="ocr-preview-empty">Aucun texte OCR disponible.</p>';
}

const documentReaderDialog = document.getElementById("document-reader-dialog");
const documentReaderTitle = document.getElementById("document-reader-title");
const documentReaderPdf = document.getElementById("document-reader-pdf");
const documentReaderMarkdown = document.getElementById("document-reader-markdown");
const documentReaderStatus = document.getElementById("document-reader-status");
const documentReaderShare = document.getElementById("document-reader-share");
let documentReaderItem = null;
let documentReaderFormat = "pdf";
let documentReaderMarkdownSource = "";
function indexedSourceUrl(item) {
  return workspaceUrl(`api/source?workspace=${encodeURIComponent(item.workspace)}&path=${encodeURIComponent(item.source_path)}`);
}

function ocrMarkdownUrl(item) {
  const query = new URLSearchParams({ workspace: item.workspace, document_id: item.document_id, source_sha256: item.source_sha256 });
  return workspaceUrl(`api/ocr-markdown?${query}`);
}

async function openDocumentReader(item, format = "pdf") {
  documentReaderItem = item;
  documentReaderFormat = format === "markdown" ? "markdown" : "pdf";
  documentReaderMarkdownSource = "";
  documentReaderTitle.textContent = String(item.source_path || "").split("/").pop() || "document";
  documentReaderStatus.textContent = "";
  documentReaderPdf.hidden = documentReaderFormat !== "pdf";
  documentReaderMarkdown.hidden = documentReaderFormat !== "markdown";
  documentReaderMarkdown.replaceChildren();
  showCockpitDialog(documentReaderDialog);

  if (documentReaderFormat === "pdf") {
    const source = new URL(indexedSourceUrl(item), window.location.origin).href;
    const viewer = new URL(workspaceUrl("vendor/pdfjs/web/viewer.html"), window.location.origin);
    viewer.searchParams.set("file", source);
    documentReaderPdf.src = viewer.toString();
    return;
  }

  documentReaderPdf.src = "about:blank";
  documentReaderMarkdown.innerHTML = '<p class="ocr-preview-empty">Chargement du texte OCR…</p>';
  try {
    const response = await fetch(ocrMarkdownUrl(item), { cache: "no-store" });
    if (!response.ok) throw new Error(response.status === 404 ? "Résultat OCR introuvable dans le cache." : `HTTP ${response.status}`);
    documentReaderMarkdownSource = await response.text();
    documentReaderMarkdown.innerHTML = renderOcrMarkdown(documentReaderMarkdownSource);
  } catch (error) {
    documentReaderMarkdown.innerHTML = `<p class="ocr-preview-empty">Impossible de lire le résultat OCR : ${escapeHtml(error.message || "erreur inconnue")}</p>`;
  }
}

const CP1252_SPECIAL = new Map([
  [0x20ac, 0x80], [0x201a, 0x82], [0x0192, 0x83], [0x201e, 0x84], [0x2026, 0x85], [0x2020, 0x86],
  [0x2021, 0x87], [0x02c6, 0x88], [0x2030, 0x89], [0x0160, 0x8a], [0x2039, 0x8b], [0x0152, 0x8c],
  [0x017d, 0x8e], [0x2018, 0x91], [0x2019, 0x92], [0x201c, 0x93], [0x201d, 0x94], [0x2022, 0x95],
  [0x2013, 0x96], [0x2014, 0x97], [0x02dc, 0x98], [0x2122, 0x99], [0x0161, 0x9a], [0x203a, 0x9b],
  [0x0153, 0x9c], [0x017e, 0x9e], [0x0178, 0x9f],
]);

function pdfTextHex(text) {
  const bytes = [];
  for (const character of String(text)) {
    const point = character.codePointAt(0);
    const byte = CP1252_SPECIAL.get(point) ?? (point <= 0x7f || (point >= 0xa0 && point <= 0xff) ? point : 0x3f);
    bytes.push(byte.toString(16).padStart(2, "0"));
  }
  return `<${bytes.join("").toUpperCase()}>`;
}

function markdownPdfEntries(markdown) {
  return String(markdown || "").replaceAll("\r\n", "\n").split("\n").map((raw) => {
    const line = raw.trim();
    if (!line) return { text: "", size: 8, gap: true };
    if (/^\s*```/.test(raw)) return null;
    if (/^\s*(?:---+|___+|\*\*\*+)\s*$/.test(line)) return { text: "────────────────────────", size: 8, rule: true };
    const heading = line.match(/^#{1,6}\s+(.+?)\s*#*$/);
    if (heading) {
      const level = (line.match(/^#+/) || [""])[0].length;
      return { text: heading[1], size: level === 1 ? 12 : level === 2 ? 10 : 9, bold: true, gapBefore: 4 };
    }
    const cells = line.includes("|") ? markdownTableCells(line) : null;
    if (cells && cells.length > 1 && cells.every((cell) => /^:?-{3,}:?$/.test(cell))) return { text: "", size: 8, gap: true };
    let text = cells && cells.length > 1 ? cells.join("   |   ") : line;
    let indent = 0;
    if (/^>/.test(text)) { text = text.replace(/^>\s?/, ""); indent = 14; }
    else if (/^[-*+]\s+/.test(text)) { text = `•  ${text.replace(/^[-*+]\s+/, "")}`; indent = 10; }
    else if (/^\d+[.)]\s+/.test(text)) { indent = 10; }
    text = text.replace(/!\[([^\]]*)\]\([^)]*\)/g, "[Image: $1]")
      .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
      .replace(/(`|\*\*|__|\*|_)/g, "");
    return { text, size: 8, indent };
  }).filter(Boolean);
}

function markdownToPdfBlob(markdown, title) {
  const width = 595.28;
  const height = 841.89;
  const margin = 42;
  const bottom = 42;
  const pages = [[]];
  let pageIndex = 0;
  let y = height - margin;
  const pushPage = () => { pages.push([]); pageIndex += 1; y = height - margin; };
  const drawLine = (text, { size = 8, bold = false, indent = 0 } = {}) => {
    const maxChars = Math.max(25, Math.floor((width - margin * 2 - indent) / (size * 0.52)));
    const chunks = [];
    let remaining = String(text);
    while (remaining.length > maxChars) {
      let split = remaining.lastIndexOf(" ", maxChars);
      if (split < Math.floor(maxChars * 0.55)) split = maxChars;
      chunks.push(remaining.slice(0, split).trim());
      remaining = remaining.slice(split).trimStart();
    }
    chunks.push(remaining);
    for (const chunk of chunks) {
      const lineHeight = size * 1.45;
      if (y - lineHeight < bottom) pushPage();
      pages[pageIndex].push(`BT /${bold ? "F2" : "F1"} ${size} Tf 1 0 0 1 ${margin + indent} ${y.toFixed(2)} Tm ${pdfTextHex(chunk)} Tj ET`);
      y -= lineHeight;
    }
  };

  drawLine(String(title || "Texte OCR"), { size: 12, bold: true });
  y -= 8;
  for (const entry of markdownPdfEntries(markdown)) {
    if (entry.gap) { y -= 4; continue; }
    if (entry.gapBefore) y -= entry.gapBefore;
    if (entry.rule) {
      if (y - 8 < bottom) pushPage();
      pages[pageIndex].push(`0.65 w ${margin} ${y.toFixed(2)} m ${width - margin} ${y.toFixed(2)} l S`);
      y -= 8;
    } else drawLine(entry.text, entry);
  }

  const objects = [
    "<< /Type /Catalog /Pages 2 0 R >>",
    "",
    "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
  ];
  const pageIds = pages.map((_page, index) => 5 + index * 2);
  objects[1] = `<< /Type /Pages /Kids [${pageIds.map((id) => `${id} 0 R`).join(" ")}] /Count ${pages.length} >>`;
  pages.forEach((page, index) => {
    const pageId = pageIds[index];
    const streamId = pageId + 1;
    const stream = [
      ...page,
      `BT /F1 8 Tf 1 0 0 1 ${width - margin - 32} 22 Tm ${pdfTextHex(`${index + 1} / ${pages.length}`)} Tj ET`,
    ].join("\n");
    objects[pageId - 1] = `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${width} ${height}] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents ${streamId} 0 R >>`;
    objects[streamId - 1] = `<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`;
  });
  let pdf = "%PDF-1.4\n";
  const offsets = [0];
  objects.forEach((body, index) => {
    offsets.push(pdf.length);
    pdf += `${index + 1} 0 obj\n${body}\nendobj\n`;
  });
  const xrefOffset = pdf.length;
  pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  for (const offset of offsets.slice(1)) pdf += `${String(offset).padStart(10, "0")} 00000 n \n`;
  pdf += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`;
  return new Blob([pdf], { type: "application/pdf" });
}

function safePdfFilename(item) {
  const basename = String(item.source_path || "document").split("/").pop() || "document";
  return `${basename.replace(/\.[^.]*$/, "").replace(/[\\/:*?"<>|]/g, "_").slice(0, 120) || "document"}.pdf`;
}

async function shareCurrentDocument() {
  if (!documentReaderItem || documentReaderShare.disabled) return;
  documentReaderShare.disabled = true;
  documentReaderStatus.textContent = documentReaderFormat === "markdown" ? "Préparation du PDF…" : "Chargement du PDF…";
  try {
    let blob;
    if (documentReaderFormat === "markdown") {
      if (!documentReaderMarkdownSource) throw new Error("Le résultat Markdown n’est pas disponible.");
      blob = markdownToPdfBlob(documentReaderMarkdownSource, String(documentReaderItem.source_path || "Texte OCR").split("/").pop());
    } else {
      const response = await fetch(indexedSourceUrl(documentReaderItem), { cache: "no-store" });
      if (!response.ok) throw new Error(`PDF introuvable (HTTP ${response.status}).`);
      blob = await response.blob();
    }
    const file = new File([blob], safePdfFilename(documentReaderItem), { type: "application/pdf" });
    if (navigator.share && navigator.canShare?.({ files: [file] })) {
      try {
        await navigator.share({ files: [file], title: file.name });
        documentReaderStatus.textContent = "PDF partagé.";
        return;
      } catch (error) {
        if (error?.name === "AbortError") {
          documentReaderStatus.textContent = "Partage annulé.";
          return;
        }
      }
    }
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = file.name;
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 30000);
    documentReaderStatus.textContent = "Partage indisponible ici; le PDF a été téléchargé pour être partagé.";
  } catch (error) {
    documentReaderStatus.textContent = `Impossible de préparer le PDF : ${error.message || "erreur inconnue"}`;
  } finally {
    documentReaderShare.disabled = false;
  }
}

documentReaderShare.addEventListener("click", () => { void shareCurrentDocument(); });

// 9.3 Classement des étapes et rendu des lignes
function processingQueueStage(item) {
  const preflight = String(item.preflight_status || "").toUpperCase();
  const status = String(item.hindsight_status || "").toUpperCase();
  const ocrStatus = String(item.ocr_status || "").toUpperCase();
  const errorText = `${item.error || ""} ${item.ocr_error || ""}`;
  const needsOcr = /no content extracted|no text extracted|ocr_needed|exceeds OCR limit/i.test(errorText);
  // Once the OCR artifact has been submitted, follow Hindsight's operation
  // state instead of leaving the row in the OCR work list.
  if (ocrStatus === "SUBMITTED" || ["VERIFY", "VERIFYING", "MEMORIZING", "MEMORIZED"].includes(status)) return "hindsight";
  if (preflight === "FAILED" || (status === "FAILED" && ocrStatus === "READY")) return "failed";
  if (ocrStatus === "FAILED") return "failed";
  if (status === "OCR_READY" || ocrStatus === "READY") {
    if (["TO_PROCESS", "ANALYZING", "STABILIZING"].includes(preflight)) return "preflight";
    if (preflight === "ANALYZED") return "hindsight";
    return "preflight";
  }
  if (["QUEUED", "PROCESSING", "FAILED"].includes(ocrStatus)
      || ["OCR_NEEDED", "OCR_QUEUED", "OCR_PROCESSING"].includes(status)
      || needsOcr
  ) return "preflight";
  if (status === "FAILED" || preflight === "FAILED" || ocrStatus === "FAILED") return "failed";
  const hasPreflightMetadata = Boolean(item.preflight_metadata && typeof item.preflight_metadata === "object");
  const preflightPending = !hasPreflightMetadata && ["TO_PROCESS", "ANALYZING", "STABILIZING"].includes(preflight);
  if (preflightPending) return "preflight";
  return "hindsight";
}

function processingWorkerLane(item) {
  const stage = processingQueueStage(item);
  if (stage === "hindsight") return "hindsight";
  if (stage !== "preflight") return null;
  const status = String(item.hindsight_status || "").toUpperCase();
  const ocrStatus = String(item.ocr_status || "").toUpperCase();
  const errorText = `${item.error || ""} ${item.ocr_error || ""}`;
  const needsOcr = /no content extracted|no text extracted|ocr_needed|exceeds OCR limit/i.test(errorText);
  return ["QUEUED", "PROCESSING"].includes(ocrStatus)
    || ["OCR_QUEUED", "OCR_PROCESSING"].includes(status)
    || needsOcr
    ? "ocr"
    : "preflight";
}

function processingProject(item) {
  const metadata = item.preflight_metadata && typeof item.preflight_metadata === "object" ? item.preflight_metadata : {};
  const explicit = item.project || metadata.project || metadata.fields?.project?.value;
  if (typeof explicit === "string" && explicit.trim()) return explicit.trim();
  const projectedTags = Array.isArray(item.hindsight_tags_projected) ? item.hindsight_tags_projected : [];
  const projectTag = projectedTags.find((tag) => String(tag).startsWith("project_hint:"));
  if (projectTag) return String(projectTag).slice("project_hint:".length).trim();
  return String(item.source_path || "").split("/").filter(Boolean)[0] || "";
}

function processingRowLabel(item) {
  const pathParts = String(item.source_path || "").split("/").filter(Boolean);
  if (String(item.workspace || "").toLocaleLowerCase("fr") === "bibliotheque") return pathParts[0] || item.workspace;
  return processingProject(item) || pathParts[0] || item.workspace;
}

function processingItemIsResolved(item) {
  const status = String(item.hindsight_status || "").toUpperCase();
  return ["MEMORIZED", "ARCHIVED"].includes(status)
    || item.user_decision === "DO_NOT_SEND";
}

function selectedVaultItems() {
  return processingData.items.filter((item) => visibleVaults.has(item.workspace)
    && !processingItemIsResolved(item));
}

function processingSearchMatches(item) {
  const terms = state.query.trim().split(/\s+/).filter(Boolean).map(foldSearchText);
  if (!terms.length) return true;
  const metadata = item.preflight_metadata && typeof item.preflight_metadata === "object"
    ? item.preflight_metadata : {};
  const collectText = (value) => {
    if (typeof value === "string" || typeof value === "number") return [String(value)];
    if (Array.isArray(value)) return value.flatMap(collectText);
    if (value && typeof value === "object") return Object.values(value).flatMap(collectText);
    return [];
  };
  const searchable = [
    item.workspace, item.source_path, item.document_id, item.project, item.phase,
    item.issuer, item.document_type, item.error, item.ocr_error, item.request_note,
    item.request_action, item.ocr_filename, item.hindsight_document_id,
    metadata.document_title_candidate?.value,
    metadata.document_summary_candidate?.value,
    metadata.document_classification,
    metadata.fields,
    metadata.issuer_candidates,
    metadata.corps_etat_candidates,
    metadata.sujet_technique_candidates,
    metadata.unresolved,
    item.metadata_override?.values,
    item.metadata_overrides,
    item.hindsight_tags_projected,
  ].flatMap(collectText).join(" ");
  const text = foldSearchText(searchable);
  return terms.every((term) => text.includes(term));
}

function selectedProjectItems() {
  const project = processingProjectFilter.value;
  return selectedVaultItems().filter((item) => (!project || processingProject(item) === project)
    && processingSearchMatches(item));
}

function selectedProcessingItems() {
  return selectedProjectItems().filter((item) => processingQueueStage(item) === processingStageFilter);
}

function updateProcessingStageTabs() {
  for (const button of processingStageTabs.querySelectorAll("[data-stage]")) {
    const selected = button.dataset.stage === processingStageFilter;
    button.setAttribute("aria-selected", String(selected));
    button.tabIndex = selected ? 0 : -1;
    const count = document.getElementById(`processing-count-${button.dataset.stage}`);
    const total = selectedProjectItems().filter((item) => processingQueueStage(item) === button.dataset.stage).length;
    if (count) count.textContent = `(${total})`;
    const label = ({ preflight: "Analyser", hindsight: "Mémoriser", failed: "Erreurs" })[button.dataset.stage];
    if (label) {
      button.setAttribute("aria-label", `${label} (${total})`);
      button.title = `${label} (${total})`;
    }
  }
}

function processingSignature(data) {
  return JSON.stringify({
    items: data.items.map((item) => [
      item.workspace, item.document_id, item.source_path, item.priority,
      item.preflight_status, item.hindsight_status, item.error, item.verification_requested_at,
      item.user_decision, item.ocr_status, item.ocr_error, item.ocr_filename, item.source_sha256, item.ocr_is_revision,
      item.preflight_metadata, item.paused_preflight, item.paused_ocr, item.paused_hindsight,
      item.request_action, item.request_note,
    ]),
    controls: data.controls.map((control) => [control.scope, Boolean(control.paused)]),
  });
}

function updateProcessingFilterOptions() {
  const selectedProject = processingProjectFilter.value;
  const projects = [...new Set(selectedVaultItems().map(processingProject).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, "fr"));
  processingProjectFilter.replaceChildren(new Option("Tous les projets", ""), ...projects.map((name) => new Option(name, name)));
  if (projects.includes(selectedProject)) processingProjectFilter.value = selectedProject;
}

function renderProcessingItems() {
  updateProcessingStageTabs();
  const all = selectedProcessingItems();
  processingItems.replaceChildren(...all.map((item) => {
    const row = document.createElement("li");
    row.className = "processing-row";
    row.dataset.workspace = item.workspace;
    row.dataset.documentId = item.document_id;
    const handle = document.createElement("button");
    handle.type = "button";
    handle.className = "processing-drag-handle";
    handle.dataset.processingHandle = "";
    handle.setAttribute("aria-label", `Déplacer ${item.source_path} dans la file`);
    handle.title = "Glisser pour changer la priorité";
    handle.textContent = "⠿";
    const itemStatus = String(item.hindsight_status || "").toUpperCase();
    const sourceName = String(item.source_path || "").split("/").filter(Boolean).pop() || "Document sans nom";
    const staleOcrSourceError = itemStatus === "OCR_READY"
      && String(item.ocr_status || "").toUpperCase() === "READY"
      && /no content extracted/i.test(String(item.error || ""));
    const visibleError = staleOcrSourceError ? "" : String(item.error || "");
    const preflightMetadata = String(item.preflight_status || "").toUpperCase() === "ANALYZED" && item.preflight_metadata
      ? `<details class="processing-row-metadata"><summary>Analyse</summary><div>${preflightTemplate(item.preflight_metadata, item.preflight_status)}</div></details>`
      : "";
    const requestNote = item.request_note
      ? `<small class="processing-request-note"><span>${escapeHtml(({ reanalyze: "Remarque · analyse", ocr: "Remarque · OCR", verify: "Remarque · vérification", memorize: "Remarque · mémorisation", replace_ocr: "Remarque · remplacement OCR" })[item.request_action] || "Remarque · relance")}</span> ${escapeHtml(item.request_note)}</small>`
      : "";
    const rowLabel = processingRowLabel(item);
    const vaultClass = String(item.workspace || "").toLocaleLowerCase("fr") === "bibliotheque" ? "is-bibliotheque" : "is-affaires";
    const currentLane = processingWorkerLane(item);
    const pauseMarker = currentLane && currentLane !== "hindsight" && item[`paused_${currentLane}`]
      ? `<span class="processing-item-paused">En pause · la file poursuit les autres</span>` : "";
    row.innerHTML = `<div class="processing-row-content">
        <div class="processing-row-heading"><span class="processing-project-badge ${vaultClass}" title="${escapeHtml(`${item.workspace} · ${rowLabel}`)}">${escapeHtml(rowLabel)}</span><strong title="${escapeHtml(item.source_path)}">${escapeHtml(sourceName)}</strong></div>
        <div class="processing-row-main"><div class="processing-row-state">${processingDot(item)}${pauseMarker}</div>${visibleError ? `<small class="processing-row-error">${escapeHtml(visibleError)}</small>` : ""}${item.ocr_error ? `<small class="processing-row-error">Décryptage : ${escapeHtml(item.ocr_error)}</small>` : ""}${requestNote}</div>
        ${preflightMetadata}
      </div>`;
    row.prepend(handle);
    const actions = document.createElement("div");
    actions.className = "processing-row-actions";
    const addAction = (label, action, disabled = false, title = "", icon = "") => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `processing-retry processing-row-action${icon ? " icon-action" : ""}`;
      button.disabled = disabled;
      button.title = title || label;
      button.setAttribute("aria-label", title || label);
      if (icon) {
        if (icon === "prohibit") {
          button.dataset.doNotMemorize = "";
          button.dataset.workspace = item.workspace;
          button.dataset.documentId = item.document_id;
        }
        button.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${CARD_ICONS[icon] || CARD_ICONS.file}"></path></svg>`;
      }
      else button.textContent = label;
      if (action) button.addEventListener("click", action);
      actions.append(button);
    };
    const isPdf = String(item.source_path || "").toLowerCase().endsWith(".pdf");
    const sourceAvailable = item.source_present !== false;
    addAction("Ouvrir", () => {
      if (isPdf) void openDocumentReader(item, "pdf");
      else openDocumentSource(item.workspace, item.source_path);
    }, !sourceAvailable, isPdf ? "Lire le PDF" : "Ouvrir le fichier source d’origine", "open");
    const editButton = document.createElement("button");
    editButton.type = "button";
    editButton.className = "processing-retry processing-row-action icon-action";
    editButton.dataset.openMetadataEditor = "";
    editButton.dataset.workspace = item.workspace;
    editButton.dataset.sourcePath = item.source_path;
    editButton.disabled = !sourceAvailable;
    editButton.title = sourceAvailable ? "Éditer les métadonnées" : "Fichier source indisponible";
    editButton.setAttribute("aria-label", editButton.title);
    editButton.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${CARD_ICONS.edit}"></path></svg>`;
    actions.append(editButton);
    if (item.ocr_filename && /^[a-f0-9]{64}$/i.test(String(item.source_sha256 || "")))
      addAction("Ouvrir le Markdown OCR", () => { void openDocumentReader(item, "markdown"); }, false, "Lire le Markdown OCR dans le dialogue", "preview");
    if (canReanalyze(item.hindsight_status, item.preflight_status))
      addAction("Analyser à nouveau", () => openProcessingActionDialog("reanalyze", item), false, "Analyser à nouveau", "analyze");
    const activeLane = currentLane;
    if (activeLane) {
      const isPaused = Boolean(item[`paused_${activeLane}`]);
      const pauseButton = document.createElement("button");
      pauseButton.type = "button";
      pauseButton.className = "processing-retry processing-row-action icon-action";
      pauseButton.dataset.itemPause = "";
      pauseButton.dataset.workspace = item.workspace;
      pauseButton.dataset.documentId = item.document_id;
      pauseButton.dataset.lane = activeLane;
      pauseButton.dataset.paused = String(!isPaused);
      pauseButton.setAttribute("aria-pressed", String(isPaused));
      pauseButton.setAttribute("aria-label", isPaused ? "Reprendre ce document" : "Mettre ce document en pause");
      pauseButton.title = pauseButton.getAttribute("aria-label");
      pauseButton.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${CARD_ICONS[isPaused ? "resume" : "pause"]}"></path></svg>`;
      actions.append(pauseButton);
    }
    if (itemStatus === "NOT_MEMORIZED") {
      addAction("Mémoriser à nouveau", () => openProcessingActionDialog("memorize", item), false, "Mémoriser à nouveau", "memorize");
    } else if (itemStatus === "VERIFY") {
      const ocrReplacementReview = String(item.error || "").includes(
        "Hindsight document already exists; OCR replacement requires operator review",
      ) || (item.request_action === "replace_ocr_after_analysis" && item.preflight_status === "FAILED");
      const hasReviewableOcr = Boolean(item.ocr_filename)
        && ["READY", "SUBMITTED"].includes(String(item.ocr_status || "").toUpperCase());
      if (ocrReplacementReview && hasReviewableOcr) {
        addAction("Remplacer par le texte OCR",
          () => openProcessingActionDialog("replace-ocr", item), false,
          "Confirmer le remplacement de la mémoire Hindsight par le texte OCR", "refresh");
      } else {
        addAction("Vérifier à nouveau",
          () => openProcessingActionDialog("verify", item), Boolean(item.verification_requested_at),
          item.verification_requested_at ? "Vérification déjà demandée" : "Vérifier à nouveau sans renvoyer le fichier", "verify");
      }
    } else {
      if (itemStatus === "FAILED") {
        const needsOcr = String(item.ocr_status || "").toUpperCase() === "FAILED"
          || /no content extracted|no text extracted|ocr_needed/i.test(`${item.error || ""} ${item.ocr_error || ""}`);
        if (isPdf && needsOcr) {
          addAction("Décrypter à nouveau", () => openProcessingActionDialog("ocr", item), false, "Décrypter à nouveau par OCR", "ocr");
        } else {
          addAction("Mémoriser à nouveau", () => openProcessingActionDialog("memorize", item), false, "Mémoriser à nouveau", "memorize");
        }
      }
      const hasTerminalError = itemStatus === "FAILED"
        || itemStatus === "OCR_NEEDED"
        || String(item.preflight_status || "").toUpperCase() === "FAILED"
        || String(item.ocr_status || "").toUpperCase() === "FAILED";
      if (hasTerminalError && !item.operation_id) {
        addAction("Continuer", () => {
          const message = `Ignorer cette erreur et poursuivre la file ?\n\n${sourceName}\n\nLe diagnostic et le résultat OCR seront conservés. Ce document ne sera pas envoyé à Hindsight. Vous pourrez le réinclure plus tard.`;
          if (!window.confirm(message)) return;
          void postProcessingQueue("continue", { workspace: item.workspace, document_id: item.document_id })
            .then(() => { processingMessage.textContent = "Erreur ignorée; le document suivant peut être traité. Le diagnostic reste conservé."; })
            .catch((error) => { processingMessage.textContent = error.message || "Impossible de continuer après cette erreur."; });
        }, false, "Ignorer cette erreur et poursuivre la file sans effacer le diagnostic");
      }
      const ocrStatus = String(item.ocr_status || "").toUpperCase();
      const ocrIsRepeatable = isPdf && itemStatus === "MODIFIED"
        && ["DONE", "READY", "FAILED"].includes(ocrStatus) && Boolean(item.ocr_filename);
      if (ocrIsRepeatable)
        addAction("Décrypter à nouveau", () => openProcessingActionDialog("ocr", item), false, "Décrypter à nouveau par OCR", "ocr");
      if (isPdf && itemStatus === "OCR_NEEDED")
        addAction("Décrypter à nouveau", () => openProcessingActionDialog("ocr", item), false, "Décrypter à nouveau par OCR", "ocr");
      if (["NOT_SENT", "FAILED", "OCR_NEEDED", "OCR_READY", "OCR_QUEUED"].includes(itemStatus)
        || (itemStatus === "QUEUED" && !item.operation_id && String(item.ocr_status || "").toUpperCase() !== "SUBMITTED")) {
        addAction("Ne pas mémoriser", null, false, "Ne pas mémoriser ce document", "prohibit");
      }
    }
    if (actions.childElementCount) row.append(actions);
    handle.addEventListener("keydown", async (event) => {
      if (!(["ArrowUp", "ArrowDown"].includes(event.key))) return;
      event.preventDefault();
      const sibling = event.key === "ArrowUp" ? row.previousElementSibling : row.nextElementSibling;
      if (!sibling) return;
      processingItems.insertBefore(row, event.key === "ArrowUp" ? sibling : sibling.nextElementSibling);
      await saveProcessingOrder([row.dataset.workspace, row.dataset.documentId]);
      handle.focus();
    });
    return row;
  }));
  const empty = document.getElementById("processing-empty");
  empty.textContent = state.query.trim()
    ? `Aucun document ne correspond à « ${state.query.trim()} » dans cette étape.`
    : `Aucun document dans la file ${({ preflight: "Analyse", hindsight: "Mémorisation", failed: "Erreurs" })[processingStageFilter]}.`;
  empty.hidden = all.length !== 0;
  const lane = ["preflight", "hindsight"].includes(processingStageFilter) ? processingStageFilter : null;
  const laneLabel = ({ preflight: "Analyse", hindsight: "Mémorisation" })[lane] || "traitement";
  const pausedCount = lane ? all.filter((item) => {
    const workerLane = processingWorkerLane(item);
    return workerLane && Boolean(item[`paused_${workerLane}`]);
  }).length : 0;
  processingPauseList.hidden = !lane;
  processingResumeList.hidden = !lane;
  processingPauseList.textContent = `Pause ${laneLabel} (${all.length})`;
  processingResumeList.textContent = `Reprendre ${laneLabel} (${pausedCount})`;
  processingPauseList.disabled = !lane || all.length === 0 || pausedCount === all.length;
  processingResumeList.disabled = !lane || pausedCount === 0;
  const retryableFailures = all.filter((item) => String(item.hindsight_status || "").toUpperCase() === "FAILED");
  processingRetryAll.hidden = processingStageFilter !== "failed" || retryableFailures.length === 0;
  processingRetryAll.textContent = `Tout reprendre (${retryableFailures.length})`;
  processingRetryAll.disabled = processingOrderSaving || processingBulkRetryInProgress;
  processingRenderSignature = processingSignature(processingData);
}

const processingActionDialog = document.getElementById("processing-action-dialog");
const processingActionForm = document.getElementById("processing-action-form");
const processingActionNote = document.getElementById("processing-action-note");
const processingActionNoteGroup = document.getElementById("processing-action-note-group");
const processingActionSubmit = document.getElementById("processing-action-submit");
const processingReplacementOptions = document.getElementById("processing-replacement-options");
let pendingProcessingAction = null;

function updateReplacementActionChoice() {
  const reanalyze = document.getElementById("processing-reanalyze-before-ingest");
  const description = document.getElementById("processing-action-description");
  const hint = document.getElementById("processing-replacement-analysis-hint");
  description.textContent = reanalyze.checked
    ? "Les métadonnées seront recalculées à partir du texte OCR, puis le document sera remplacé dans Hindsight."
    : "Le document sera remplacé dans Hindsight avec les métadonnées de la dernière analyse OCR.";
  hint.textContent = reanalyze.checked
    ? "Une analyse OCR à jour sera enregistrée avant l’ingestion."
    : "La dernière analyse correspond au fichier actuel; elle sera réutilisée sans nouveau préflight.";
  processingActionSubmit.textContent = "Confirmer le remplacement OCR";
}

document.getElementById("processing-reanalyze-before-ingest").addEventListener("change", updateReplacementActionChoice);

// 9.4 Actions confirmées, contrôles de file et navigation de vue
function openProcessingActionDialog(action, item) {
  const actionInfo = {
    reanalyze: {
      title: "Analyser à nouveau",
      description: "Refait l’analyse des métadonnées du document. Cette action ne réingère pas le document dans Hindsight.",
      submit: "Relancer l’analyse",
    },
    ocr: {
      title: "Décrypter à nouveau",
      description: "Relance l’OCR, puis l’analyse du texte produit. La suite du flux reprendra automatiquement.",
      submit: "Relancer l’OCR",
    },
    verify: {
      title: "Vérifier à nouveau",
      description: "Interroge Hindsight sur l’envoi déjà effectué, sans renvoyer le document.",
      submit: "Demander la vérification",
    },
    memorize: {
      title: "Mémoriser à nouveau",
      description: String(item.hindsight_status).toUpperCase() === "NOT_MEMORIZED"
        ? "Réintègre le document au flux automatique, qui l’analysera avant de le mémoriser."
        : "Replace l’échec dans la file de mémorisation pour une nouvelle tentative.",
      submit: "Relancer la mémorisation",
    },
    "replace-ocr": {
      title: "Remplacer la mémoire par le texte OCR",
      description: "Choisissez si les métadonnées doivent être réanalysées avant l’ingestion OCR, ou si l’ingestion doit utiliser les métadonnées actuelles.",
      submit: "Choisir le traitement",
    },
  }[action];
  if (!actionInfo) return;
  pendingProcessingAction = { action, item };
  document.getElementById("processing-action-title").textContent = actionInfo.title;
  document.getElementById("processing-action-description").textContent = actionInfo.description;
  document.getElementById("processing-action-status").textContent = "";
  processingActionSubmit.textContent = actionInfo.submit;
  processingReplacementOptions.hidden = action !== "replace-ocr";
  processingActionNoteGroup.hidden = false;
  processingActionSubmit.disabled = false;
  processingActionNote.value = "";
  const reanalyzeBeforeIngest = document.getElementById("processing-reanalyze-before-ingest");
  if (action === "replace-ocr") {
    const metadataCurrent = item.ocr_preflight_source_sha256 === item.source_sha256;
    reanalyzeBeforeIngest.checked = !metadataCurrent;
    reanalyzeBeforeIngest.disabled = !metadataCurrent;
    reanalyzeBeforeIngest.closest("label").title = metadataCurrent
      ? "Optionnel : recalculer les métadonnées OCR avant l’ingestion."
      : "Aucune analyse OCR à jour n’existe; le préflight est requis avant l’ingestion.";
    updateReplacementActionChoice();
  } else {
    reanalyzeBeforeIngest.checked = false;
    reanalyzeBeforeIngest.disabled = false;
    reanalyzeBeforeIngest.closest("label").removeAttribute("title");
  }
  showCockpitDialog(processingActionDialog);
  if (action === "replace-ocr") document.getElementById("processing-reanalyze-before-ingest").focus();
  else processingActionNote.focus();
}

async function submitProcessingAction(event) {
  event.preventDefault();
  if (!pendingProcessingAction) return;
  const { action, item } = pendingProcessingAction;
  const replacementMode = action === "replace-ocr"
    ? document.getElementById("processing-reanalyze-before-ingest").checked ? "analyze_and_ingest" : "ingest_only"
    : null;
  const routes = { reanalyze: "reanalyze", ocr: "ocr", verify: "verify", "replace-ocr": "replace-ocr" };
  const route = routes[action] || (String(item.hindsight_status).toUpperCase() === "NOT_MEMORIZED" ? "reinclude" : "retry");
  const body = { workspace: item.workspace, document_id: item.document_id, note: processingActionNote.value.trim() };
  processingActionSubmit.disabled = true;
  document.getElementById("processing-action-status").textContent = "Demande en cours…";
  try {
    if (action === "replace-ocr") body.mode = replacementMode;
    await postProcessingQueue(route, body);
    processingMessage.textContent = action === "replace-ocr"
      ? replacementMode === "analyze_and_ingest"
        ? "Analyse des métadonnées ajoutée à la file; l’ingestion OCR suivra automatiquement."
        : "Ingestion OCR ajoutée à la file avec les métadonnées actuelles."
      : ({
        reanalyze: "Nouvelle analyse ajoutée à la file.",
        ocr: "Nouvelle demande OCR ajoutée à la file.",
        verify: "Vérification distante demandée ; aucun nouvel envoi ne sera lancé.",
        memorize: "Nouvelle tentative de mémorisation ajoutée à la file.",
      })[action];
    processingActionDialog.close();
    pendingProcessingAction = null;
  } catch (error) {
    document.getElementById("processing-action-status").textContent = error.message || "Action impossible.";
    processingActionSubmit.disabled = false;
  }
}

processingActionForm.addEventListener("submit", (event) => { void submitProcessingAction(event); });
processingActionDialog.addEventListener("close", () => { pendingProcessingAction = null; });
processingActionDialog.addEventListener("click", (event) => {
  if (event.target.closest("[data-close-processing-action], [data-cancel-processing-action]")) {
    processingActionDialog.close();
    pendingProcessingAction = null;
  }
});

async function loadProcessingQueue({ silent = false } = {}) {
  if (processingDrag || processingOrderSaving || processingBulkRetryInProgress) return;
  if (!silent) processingMessage.textContent = "Lecture de la file…";
  try {
    const response = await fetch(workspaceUrl("api/processing-queue"), { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    processingData = await response.json();
    updateProcessingFilterOptions();
    if (processingSignature(processingData) !== processingRenderSignature) renderProcessingItems();
    const visibleCount = selectedProcessingItems().length;
    const stageName = ({ preflight: "Analyse", hindsight: "Mémorisation", failed: "Erreurs" })[processingStageFilter];
    const queueSummary = `${visibleCount} document${visibleCount > 1 ? "s" : ""} · ${stageName}`;
    if (!silent) {
      processingMessage.textContent = processingSorter
        ? queueSummary
        : `Glissement indisponible : SortableJS local non chargé. ${queueSummary}`;
    }
  } catch (error) {
    if (!silent) {
      processingMessage.textContent = error.message === "HTTP 404"
        ? "File non configurée sur ce serveur."
        : "File momentanément indisponible.";
    }
  }
}

async function loadProcessingStatus() {
  if (!processingLaneStatus) return;
  const labels = { preflight: "Analyse", ocr: "OCR", hindsight: "Hindsight" };
  try {
    const response = await fetch(workspaceUrl("api/processing-status"), { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    processingStatusPayload = payload;
    for (const button of processingLaneStatus.querySelectorAll("[data-processing-lane]")) {
      const laneName = button.dataset.processingLane;
      const lane = payload.lanes?.[laneName] || {};
      const stateName = ["active", "disabled", "paused", "error"].includes(lane.state) ? lane.state : "error";
      const stateLabel = ({ active: "Worker en fonctionnement", disabled: "Désactivé", paused: "En pause globale", error: "Erreur du worker" })[stateName];
      button.dataset.state = stateName;
      button.title = `${labels[laneName]} · ${stateLabel}`;
      button.setAttribute("aria-label", button.title);
    }
    if (processingLaneDialog?.open && selectedProcessingLane) updateProcessingLaneDialog();
  } catch (_error) {
    processingStatusPayload = null;
    for (const button of processingLaneStatus.querySelectorAll("[data-processing-lane]")) {
      button.dataset.state = "error";
      button.title = `${labels[button.dataset.processingLane]} · état indisponible`;
      button.setAttribute("aria-label", button.title);
    }
  }
}

function updateProcessingLaneDialog() {
  if (!selectedProcessingLane || !processingLaneDialog) return;
  const labels = { preflight: "Analyse", ocr: "OCR", hindsight: "Hindsight" };
  const lane = processingStatusPayload?.lanes?.[selectedProcessingLane] || {};
  const stateNames = { active: "active", paused: "en pause", disabled: "arrêtée", error: "en erreur" };
  processingLaneDialogTitle.textContent = `${labels[selectedProcessingLane]} · ${stateNames[lane.state] || "état indisponible"}`;
  const messages = {
    active: "Les nouveaux travaux de cette étape sont admis.",
    paused: "Les travaux en attente restent dans la file et reprendront après la reprise.",
    disabled: "Aucun nouveau travail ne démarrera pour cette étape tant qu’elle reste arrêtée.",
    error: "Le worker signale une erreur ou son état est indisponible. Vous pouvez modifier le contrôle, mais cela ne répare pas le worker.",
  };
  const globalNote = processingStatusPayload?.global_paused ? " La pause globale reste prioritaire." : "";
  processingLaneDialogDescription.textContent = `${messages[lane.state] || "État de l’étape indisponible."} Une opération déjà commencée n’est pas interrompue.${globalNote}`;
  renderProcessingLaneActivity();
}

function renderProcessingLaneActivity() {
  if (!processingLaneActivityList || !selectedProcessingLane) return;
  const laneName = selectedProcessingLane;
  const matchesLane = (item) => {
    const preflight = String(item.preflight_status || "").toUpperCase();
    const hindsight = String(item.hindsight_status || "").toUpperCase();
    const ocr = String(item.ocr_status || "").toUpperCase();
    if (laneName === "preflight") return preflight !== "" && preflight !== "NOT_RUN";
    if (laneName === "ocr") return ocr !== "" && ocr !== "NONE";
    return hindsight !== "" && !["NOT_SENT", "NOT_MEMORIZED"].includes(hindsight);
  };
  const recent = processingLaneActivityItems.filter(matchesLane)
    .sort((a, b) => String(b.updated_at || "").localeCompare(String(a.updated_at || "")))
    .slice(0, 8);
  if (!recent.length) {
    processingLaneActivityList.innerHTML = "<li class=\"processing-lane-activity-empty\">Aucune activité disponible pour cette étape.</li>";
    return;
  }
  processingLaneActivityList.innerHTML = recent.map((item) => {
    const filename = String(item.source_path || "").split("/").filter(Boolean).pop() || item.document_id || "Document";
    const status = processingLabel(item).label;
    const error = [item.error, item.ocr_error].filter(Boolean).join(" · ");
    const timestamp = item.updated_at ? new Date(item.updated_at).toLocaleString("fr-FR") : "Date inconnue";
    return `<li><div class="processing-lane-activity-heading"><strong>${escapeHtml(filename)}</strong><time>${escapeHtml(timestamp)}</time></div><small>${escapeHtml(item.workspace || "")} · ${escapeHtml(status)}</small>${error ? `<p>${escapeHtml(error.slice(0, 420))}</p>` : ""}</li>`;
  }).join("");
}

async function loadProcessingLaneActivity() {
  if (!processingLaneActivityList) return;
  processingLaneActivityList.innerHTML = "<li class=\"processing-lane-activity-empty\">Chargement…</li>";
  try {
    const response = await fetch(workspaceUrl("api/processing-queue?include_memorized=true"), { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    processingLaneActivityItems = Array.isArray(payload.items) ? payload.items : [];
    renderProcessingLaneActivity();
  } catch (_error) {
    processingLaneActivityList.innerHTML = "<li class=\"processing-lane-activity-empty\">Activité temporairement indisponible.</li>";
  }
}

async function setGlobalProcessingLaneState(state, button) {
  if (!selectedProcessingLane || !processingLaneDialogStatus) return;
  const buttons = [...processingLaneDialog.querySelectorAll("[data-lane-state]")];
  buttons.forEach((entry) => { entry.disabled = true; });
  processingLaneDialogStatus.textContent = "Enregistrement…";
  try {
    const lane = processingStatusPayload?.lanes?.[selectedProcessingLane] || {};
    const response = await fetch(workspaceUrl("api/processing-queue/lane-control"), {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Pantheon-Intent": "processing-control" },
      body: JSON.stringify({ lane: selectedProcessingLane, state, revision: lane.control_revision ?? 0 }),
      cache: "no-store",
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    processingStatusPayload = payload;
    await loadProcessingStatus();
    processingLaneDialogStatus.textContent = `Contrôle mis à jour : ${state === "active" ? "reprise" : state === "paused" ? "pause" : "arrêt"}.`;
  } catch (error) {
    processingLaneDialogStatus.textContent = `Contrôle non modifié : ${error.message}`;
  } finally {
    buttons.forEach((entry) => { entry.disabled = false; });
    if (button) button.focus();
  }
}

async function postProcessingQueue(path, body) {
  const response = await fetch(workspaceUrl(`api/processing-queue/${path}`), {
    method: "POST", headers: { "Content-Type": "application/json", "X-Pantheon-Intent": "processing-control" },
    body: JSON.stringify(body), cache: "no-store",
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
  processingData = payload;
  renderProcessingItems();
}

async function saveProcessingOrder(movedItem) {
  const visibleRows = [...processingItems.querySelectorAll(".processing-row")];
  const visibleOrder = visibleRows.map((row) => [row.dataset.workspace, row.dataset.documentId]);
  let order = processingData.items
    .filter((item) => !processingItemIsResolved(item))
    .map((item) => [item.workspace, item.document_id]);
  const visibleSet = new Set(visibleOrder.map(([workspace, id]) => `${workspace}\0${id}`));
  const visibleSlots = [];
  order.forEach(([workspace, id], index) => {
    if (visibleSet.has(`${workspace}\0${id}`)) visibleSlots.push(index);
  });
  let cursor = 0;
  for (const slot of visibleSlots) order[slot] = visibleOrder[cursor++];
  const position = order.findIndex(([workspace, id]) => workspace === movedItem[0] && id === movedItem[1]);
  if (position < 0) return;
  processingOrderSaving = true;
  let reload = false;
  try {
    await postProcessingQueue("order", {
      move: { workspace: movedItem[0], document_id: movedItem[1] },
      position,
      revision: processingData.revision,
    });
    processingMessage.textContent = "Ordre enregistré.";
  } catch (error) {
    processingMessage.textContent = error.message === "queue_revision_conflict"
      ? "La file a changé pendant le déplacement ; ordre rechargé, réessayez."
      : `Ordre non enregistré : ${error.message}`;
    reload = true;
  } finally {
    processingOrderSaving = false;
  }
  if (reload) await loadProcessingQueue({ silent: true });
}

async function retryAllVisibleFailures() {
  const failures = selectedProcessingItems().filter((item) => String(item.hindsight_status || "").toUpperCase() === "FAILED");
  if (!failures.length || processingOrderSaving || processingBulkRetryInProgress) return;
  processingBulkRetryInProgress = true;
  processingRetryAll.disabled = true;
  processingRetryAll.textContent = `Relance… 0/${failures.length}`;
  let retried = 0;
  let failed = 0;
  try {
    for (const item of failures) {
      try {
        await postProcessingQueue("retry", { workspace: item.workspace, document_id: item.document_id });
        retried += 1;
      } catch (_error) {
        failed += 1;
      }
      processingRetryAll.textContent = `Relance… ${retried + failed}/${failures.length}`;
    }
  } finally {
    processingBulkRetryInProgress = false;
  }
  processingMessage.textContent = failed
    ? `${retried} erreur${retried === 1 ? "" : "s"} replacée${retried === 1 ? "" : "s"} dans la file ; ${failed} non relancée${failed === 1 ? "" : "s"}.`
    : `${retried} erreur${retried === 1 ? "" : "s"} replacée${retried === 1 ? "" : "s"} dans la file.`;
  await loadProcessingQueue({ silent: true });
}

async function setVisibleProcessingLanePaused(paused) {
  if (!["preflight", "hindsight"].includes(processingStageFilter)) return;
  const groups = new Map();
  for (const item of selectedProcessingItems()) {
    const lane = processingWorkerLane(item);
    if (!lane) continue;
    if (!groups.has(lane)) groups.set(lane, []);
    groups.get(lane).push({ workspace: item.workspace, document_id: item.document_id });
  }
  if (!groups.size) return;
  try {
    for (const [lane, items] of groups) await postProcessingQueue("pause", { items, lane, paused });
    const total = [...groups.values()].reduce((sum, items) => sum + items.length, 0);
    const treatment = processingStageFilter === "preflight" ? "l’analyse et les OCR nécessaires" : "la mémorisation";
    processingMessage.textContent = `${total} élément${total === 1 ? "" : "s"} de la liste ${paused ? "mis en pause" : "repris"} pour ${treatment}.`;
  } catch (error) {
    processingMessage.textContent = `Commande ${paused ? "pause" : "reprise"} impossible : ${error.message || "erreur inconnue"}`;
  }
}

async function setProcessingItemPaused(workspace, documentId, lane, paused) {
  if (paused) {
    const label = ({ preflight: "l’analyse", ocr: "le décryptage OCR", hindsight: "la mémorisation Hindsight" })[lane] || "ce traitement";
    if (!window.confirm(`Mettre ${label} de ce document en pause ? Les autres éléments de la file continueront.`)) return;
  }
  try {
    await postProcessingQueue("pause", { items: [{ workspace, document_id: documentId }], lane, paused });
    processingMessage.textContent = paused
      ? "Document mis en pause ; la file poursuit les autres éléments."
      : "Document repris dans la file.";
  } catch (error) {
    processingMessage.textContent = `Commande ${paused ? "pause" : "reprise"} impossible : ${error.message || "erreur inconnue"}`;
  }
}

function setProcessingView(enabled) {
  processingView.hidden = !enabled;
  processingToggle.setAttribute("aria-pressed", String(enabled));
  folderViewToggle.setAttribute("aria-pressed", String(!enabled));
  const activeToggle = enabled ? processingToggle : folderViewToggle;
  const alternateToggle = enabled ? folderViewToggle : processingToggle;
  setChoiceMenuOpen(workspaceViewSwitch, activeToggle, [alternateToggle], false);
  const activeLabel = enabled ? "Liste de traitement" : "Vue des dossiers";
  const alternateLabel = enabled ? "Vue des dossiers" : "Liste de traitement";
  activeToggle.setAttribute("aria-label", `${activeLabel} · afficher l’autre vue`);
  activeToggle.title = `${activeLabel} · afficher l’autre vue`;
  activeToggle.setAttribute("aria-controls", alternateToggle.id);
  alternateToggle.setAttribute("aria-label", alternateLabel);
  alternateToggle.title = alternateLabel;
  activeToggle.hidden = false;
  for (const id of ["filter-disclosure", "breadcrumbs", "cards", "folder-pager", "empty", "loading", "error", "summary-disclosure"]) {
    const node = document.getElementById(id);
    if (node) node.hidden = enabled;
  }
  const syncState = document.querySelector(".sync-state");
  if (syncState) syncState.hidden = enabled;
  if (enabled) void loadProcessingQueue();
  else void loadChildren();
}

function expandWorkspaceViewSwitch() {
  const activeToggle = processingView.hidden ? folderViewToggle : processingToggle;
  const alternateToggle = processingView.hidden ? processingToggle : folderViewToggle;
  toggleChoiceMenu(workspaceViewSwitch, activeToggle, [alternateToggle]);
}

folderViewToggle.addEventListener("click", () => {
  if (folderViewToggle.getAttribute("aria-pressed") === "true") expandWorkspaceViewSwitch();
  else setProcessingView(false);
});
processingToggle.addEventListener("click", () => {
  if (processingToggle.getAttribute("aria-pressed") === "true") expandWorkspaceViewSwitch();
  else setProcessingView(true);
});
document.addEventListener("click", (event) => {
  if (workspaceViewSwitch.dataset.expanded === "true" && !event.target.closest("#workspace-view-switch")) {
    const activeToggle = processingView.hidden ? folderViewToggle : processingToggle;
    const alternateToggle = processingView.hidden ? processingToggle : folderViewToggle;
    setChoiceMenuOpen(workspaceViewSwitch, activeToggle, [alternateToggle], false);
  }
  if (vaultSwitchExpanded && !event.target.closest("#workspace-vault-switch")) {
    vaultSwitchExpanded = false;
    renderVaultSwitch();
  }
});
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  if (workspaceViewSwitch.dataset.expanded === "true") {
    const activeToggle = processingView.hidden ? folderViewToggle : processingToggle;
    const alternateToggle = processingView.hidden ? processingToggle : folderViewToggle;
    setChoiceMenuOpen(workspaceViewSwitch, activeToggle, [alternateToggle], false);
    activeToggle.focus();
  }
  if (vaultSwitchExpanded) {
    vaultSwitchExpanded = false;
    renderVaultSwitch();
    vaultSwitch.querySelector(`[data-vault-toggle="${CSS.escape(state.workspace)}"]`)?.focus();
  }
});
// 10. Menu global et branchements de la file
const workspaceMenu = document.getElementById("workspace-menu");
const metadataDialog = document.getElementById("metadata-editor-dialog");
document.addEventListener("click", (event) => {
  const closeDocumentReader = event.target.closest("[data-close-document-reader]");
  if (closeDocumentReader) {
    documentReaderDialog.close();
    return;
  }
  const closeMetadata = event.target.closest("[data-close-metadata-dialog]");
  if (closeMetadata) {
    metadataDialog.close();
    return;
  }
  const sourceButton = event.target.closest("[data-open-source]");
  if (sourceButton) {
    openCardSource(sourceButton.dataset.workspace, sourceButton.dataset.sourcePath);
    return;
  }
  const editButton = event.target.closest("[data-open-metadata-editor]");
  if (editButton) {
    openSharedMetadataEditor(editButton.dataset.workspace, editButton.dataset.sourcePath);
    return;
  }
  const pauseButton = event.target.closest("[data-item-pause]");
  if (pauseButton) {
    void setProcessingItemPaused(pauseButton.dataset.workspace, pauseButton.dataset.documentId,
      pauseButton.dataset.lane, pauseButton.dataset.paused === "true");
    return;
  }
  const excludeButton = event.target.closest("[data-do-not-memorize]");
  if (excludeButton) {
    const button = excludeButton;
    const item = processingData.items.find((row) => row.workspace === button.dataset.workspace && row.document_id === button.dataset.documentId);
    if (item && window.confirm("Confirmer l’exclusion de ce document du traitement ?")) {
      void postProcessingQueue("do-not-memorize", { workspace: item.workspace, document_id: item.document_id })
        .then(() => { processingMessage.textContent = "Suite annulée ; le document reste disponible sans être mémorisé."; })
        .catch((error) => { processingMessage.textContent = error.message || "Exclusion impossible."; });
    }
    return;
  }
  const restoreMetadataButton = event.target.closest("[data-restore-automatic-metadata]");
  if (restoreMetadataButton) {
    void restoreAutomaticMetadata(restoreMetadataButton);
    return;
  }
  const saveButton = event.target.closest("[data-save-document-metadata]");
  if (saveButton) {
    void saveDocumentMetadata(saveButton);
    return;
  }
  const syncButton = event.target.closest("[data-hindsight-metadata-sync]");
  if (syncButton) void syncDocumentMetadata(syncButton);
});
document.addEventListener("input", (event) => {
  const field = event.target.closest("#metadata-editor-dialog [data-metadata-field]");
  if (!field) return;
  trackMetadataFieldEdit(field);
  const editor = event.target.closest("[data-document-metadata]");
  const status = editor?.querySelector("[data-hindsight-metadata-sync-status]");
  if (status) status.textContent = "Métadonnées modifiées; enregistrez avant synchronisation.";
  editor?.querySelectorAll("[data-hindsight-metadata-sync]").forEach((button) => { button.disabled = true; });
});
document.addEventListener("click", (event) => {
  const resetButton = event.target.closest("#metadata-editor-dialog [data-metadata-field-reset]");
  if (resetButton) {
    const editor = resetButton.closest("[data-document-metadata]");
    const field = editor?.querySelector(`[data-metadata-field="${CSS.escape(resetButton.dataset.metadataFieldReset)}"]`);
    if (field) {
      field.value = field.dataset.metadataPreviousValue || "";
      field.dataset.metadataExplicitNull = "false";
      field.dispatchEvent(new Event("input", { bubbles: true }));
      field.focus();
    }
    return;
  }
  if (workspaceMenu?.open && !workspaceMenu.contains(event.target)) workspaceMenu.open = false;
});
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape" || !workspaceMenu?.open) return;
  workspaceMenu.open = false;
  workspaceMenu.querySelector(":scope > summary")?.focus();
});
workspaceMenu?.addEventListener("click", (event) => {
  if (event.target.closest("a")) workspaceMenu.open = false;
});
processingProjectFilter.addEventListener("change", () => { renderProcessingItems(); });
processingRetryAll.addEventListener("click", () => { void retryAllVisibleFailures(); });
processingStageTabs.addEventListener("click", (event) => {
  const button = event.target.closest("[data-stage]");
  if (!button || !["preflight", "hindsight", "failed"].includes(button.dataset.stage)) return;
  processingStageFilter = button.dataset.stage;
  renderProcessingItems();
});
processingLaneStatus?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-processing-lane]");
  if (!button) return;
  selectedProcessingLane = button.dataset.processingLane;
  processingLaneDialogStatus.textContent = "";
  updateProcessingLaneDialog();
  showCockpitDialog(processingLaneDialog);
  void loadProcessingLaneActivity();
});
processingLaneDialog?.addEventListener("click", (event) => {
  if (event.target.closest("[data-close-processing-lane]")) {
    processingLaneDialog.close();
    return;
  }
  const button = event.target.closest("[data-lane-state]");
  if (button) void setGlobalProcessingLaneState(button.dataset.laneState, button);
});
processingStageTabs.addEventListener("keydown", (event) => {
  if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
  const tabs = [...processingStageTabs.querySelectorAll("[role=tab]")];
  const current = tabs.indexOf(document.activeElement);
  if (current < 0) return;
  event.preventDefault();
  const next = event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1
    : (current + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
  tabs[next].focus();
  tabs[next].click();
});
processingPauseList.addEventListener("click", () => { void setVisibleProcessingLanePaused(true); });
processingResumeList.addEventListener("click", () => { void setVisibleProcessingLanePaused(false); });
window.setInterval(() => { if (!processingView.hidden && !processingDrag && !processingOrderSaving && !processingBulkRetryInProgress) void loadProcessingQueue(); }, 15000);
void loadProcessingStatus();
window.setInterval(() => { void loadProcessingStatus(); }, 15000);

// 10.1 Versions des assets réellement chargés dans cette page
const assetVersionFooter = document.getElementById("asset-version-footer");
if (assetVersionFooter) {
  const versionFromUrl = (element) => {
    if (!element) return "absent";
    return new URL(element.src || element.href, document.baseURI).searchParams.get("v") || "sans version";
  };
  const appScript = [...document.scripts].find((script) => new URL(script.src || document.baseURI).pathname.endsWith("/app.js"));
  const appStyle = [...document.querySelectorAll('link[rel~="stylesheet"]')].find((link) => new URL(link.href).pathname.endsWith("/styles.css"));
  const htmlVersion = document.documentElement.dataset.uiVersion || "non versionné";
  assetVersionFooter.textContent = `HTML ${htmlVersion} · JS ${versionFromUrl(appScript)} · CSS ${versionFromUrl(appStyle)}`;
}

// 11. Projection locale des traces OTEL, sans contenu métier
const otelPanel = document.getElementById("otel-panel");
let otelPending = false;
let otelSignature = "";
const otelLabels = { agent: "Agent", session: "Session", skill: "Compétence", approval: "Approbation", subagent: "Sous-agent", llm: "Modèle", api: "API", tool: "Outil", cron: "Planification", other: "Span" };
const formatOtelTime = (ns) => Number.isFinite(ns) ? new Date(ns / 1e6).toLocaleString("fr-FR") : "heure inconnue";
function formatOtelDuration(durationMs) {
  if (!Number.isFinite(durationMs)) return "durée inconnue";
  if (durationMs < 1000) return `${new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 1 }).format(durationMs)} ms`;
  return `${new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 2 }).format(durationMs / 1000)} s`;
}
function renderOtelLog(spans) {
  const summary = document.getElementById("otel-summary");
  const list = document.getElementById("otel-spans");
  const groups = new Map();
  for (const span of spans) {
    const key = span.trace_id || `isolated:${span.span_id || span.seq}`;
    if (!groups.has(key)) groups.set(key, { traceId: span.trace_id, spans: [], lastNs: null });
    const group = groups.get(key);
    group.spans.push(span);
    const activityNs = Number.isFinite(span.end_ns) ? span.end_ns : Number.isFinite(span.start_ns) ? span.start_ns : null;
    if (activityNs !== null) group.lastNs = group.lastNs === null ? activityNs : Math.max(group.lastNs, activityNs);
  }
  const orderedGroups = [...groups.values()].sort((a, b) => (b.lastNs ?? 0) - (a.lastNs ?? 0));
  const errorCount = spans.filter((span) => span.status === "ERROR").length;
  const traceCount = new Set(spans.map((span) => span.trace_id).filter(Boolean)).size;
  const summaryItems = [
    [spans.length, "spans disponibles", "spans"],
    [traceCount, "traces regroupées", "traces"],
    [errorCount, "spans en erreur", "errors"],
  ];
  summary.replaceChildren(...summaryItems.map(([value, label, kind]) => {
    const item = document.createElement("div"); item.className = "otel-summary-item"; item.dataset.kind = kind;
    const number = document.createElement("strong"); number.textContent = String(value);
    const caption = document.createElement("span"); caption.textContent = label;
    item.append(number, caption); return item;
  }));

  const fragment = document.createDocumentFragment();
  for (const group of orderedGroups) {
    group.spans.sort((a, b) => (a.start_ns ?? a.end_ns ?? 0) - (b.start_ns ?? b.end_ns ?? 0) || a.seq - b.seq);
    const trace = document.createElement("li"); trace.className = "otel-trace";
    const head = document.createElement("div"); head.className = "otel-trace-head";
    const title = document.createElement("strong");
    title.textContent = group.traceId ? `Trace ${group.traceId.slice(0, 8)}` : `Span isolé ${group.spans[0]?.seq ?? ""}`;
    if (group.traceId) title.title = group.traceId;
    const count = document.createElement("span"); count.textContent = `${group.spans.length} span${group.spans.length > 1 ? "s" : ""} · dernière activité ${formatOtelTime(group.lastNs)}`;
    head.append(title, count);
    const entries = document.createElement("ol"); entries.className = "otel-trace-spans";
    for (const span of group.spans) {
      const entry = document.createElement("li"); entry.className = "otel-span";
      const main = document.createElement("div"); main.className = "otel-span-main";
      const kind = document.createElement("strong"); kind.textContent = otelLabels[span.kind] || "Span";
      const status = document.createElement("span"); status.className = "otel-span-status"; status.dataset.status = span.status || "UNSET";
      status.textContent = span.status === "ERROR" ? "Erreur" : span.status === "OK" ? (Number.isFinite(span.end_ns) ? "Terminée" : "Fin inconnue") : (Number.isFinite(span.end_ns) ? "Terminée · statut non renseigné" : "Statut et fin inconnus");
      main.append(kind, status);
      const meta = document.createElement("div"); meta.className = "otel-span-meta";
      const duration = document.createElement("span"); duration.textContent = formatOtelDuration(span.duration_ms);
      const start = document.createElement("span"); start.textContent = `Début ${formatOtelTime(span.start_ns)}`;
      const end = document.createElement("span"); end.textContent = `Fin ${formatOtelTime(span.end_ns)}`;
      meta.append(duration, start, end);
      if (span.span_id) { const id = document.createElement("code"); id.textContent = `span ${span.span_id.slice(0, 8)}`; id.title = span.span_id; meta.append(id); }
      if (span.parent_span_id) { const parent = document.createElement("code"); parent.textContent = `parent ${span.parent_span_id.slice(0, 8)}`; parent.title = span.parent_span_id; meta.append(parent); }
      entry.append(main, meta); entries.append(entry);
    }
    trace.append(head, entries); fragment.append(trace);
  }
  if (!spans.length) { const empty = document.createElement("li"); empty.className = "message"; empty.textContent = "Aucun span dans l’aperçu récent."; fragment.append(empty); }
  list.replaceChildren(fragment);
}
async function loadOtelTelemetry() {
  if (!otelPanel?.open || document.hidden || otelPending) return;
  otelPending = true;
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 4000);
  try {
    const response = await fetch(workspaceUrl("api/telemetry"), { cache: "no-store", signal: controller.signal });
    if (!response.ok) throw new Error("telemetry");
    const result = await response.json();
    document.getElementById("otel-state").textContent = result.available ? "OTEL local" : "Indisponible";
    const list = document.getElementById("otel-spans");
    if (!result.available) { list.replaceChildren(); document.getElementById("otel-summary").replaceChildren(); otelSignature = ""; document.getElementById("otel-updated").textContent = "Aucun aperçu récent disponible."; return; }
    document.getElementById("otel-updated").textContent = `Aperçu actualisé à ${new Date(result.generated_at).toLocaleTimeString("fr-FR")}`;
    const spans = Array.isArray(result.spans) ? result.spans : [];
    const signature = JSON.stringify(spans);
    if (signature === otelSignature) return;
    otelSignature = signature;
    renderOtelLog(spans);
  } catch (_error) {
    document.getElementById("otel-state").textContent = "Indisponible";
    document.getElementById("otel-spans").replaceChildren();
    document.getElementById("otel-summary").replaceChildren();
    document.getElementById("otel-updated").textContent = "Lecture interrompue ; nouvelle tentative à la prochaine actualisation.";
    otelSignature = "";
  } finally { window.clearTimeout(timeout); otelPending = false; }
}
otelPanel?.addEventListener("toggle", () => { if (otelPanel.open) void loadOtelTelemetry(); });
window.setInterval(loadOtelTelemetry, 10000);
