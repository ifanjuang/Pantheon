const $ = id => document.getElementById(id);
const state = {
  items: [],
  current: null,
  baseMarkdown: "",
  token: "",
  project: "",
  actor: "",
  pendingUpdate: null,
};

const instructionLabels = {
  rewrite: "Reformuler la sélection sans en changer le sens.",
  expand: "Détailler la sélection avec les précisions utiles.",
  simplify: "Simplifier la sélection sans perdre les exigences.",
  verify: "Vérifier la sélection et signaler les points à confirmer.",
  move_to_lot: "Proposer le déplacement de la sélection dans un autre lot.",
};

function uuid(prefix) {
  if (globalThis.crypto?.randomUUID) return `${prefix}-${globalThis.crypto.randomUUID()}`;
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function headers(extra = {}) {
  return {
    Authorization: `Bearer ${state.token}`,
    "Content-Type": "application/json",
    ...extra,
  };
}

function key(id) { return `pantheon-knowledge:${id}`; }
function legacyDraftKey(id) { return `pantheon-knowledge:legacy-revision:${id}`; }
function queueKey() { return "pantheon-knowledge:queue"; }
function queue() { return JSON.parse(localStorage.getItem(queueKey()) || "[]"); }
function setQueue(value) { localStorage.setItem(queueKey(), JSON.stringify(value)); }
function message(text) { $("message").textContent = text; }
function setNetwork() { $("network").textContent = navigator.onLine ? "en ligne" : "hors ligne"; }

function recoveredLegacyDraft(knowledgeId) {
  return JSON.parse(localStorage.getItem(legacyDraftKey(knowledgeId)) || "null");
}

function migrateLegacyRevisions() {
  const remaining = [];
  let recovered = 0;
  for (const operation of queue()) {
    if (operation?.type !== "revision") {
      remaining.push(operation);
      continue;
    }
    const knowledgeId = String(operation.knowledge_id || "").trim();
    const markdown = operation.body?.markdown;
    if (!knowledgeId || typeof markdown !== "string") {
      remaining.push({ ...operation, conflict: "ancienne révision incomplète ; récupération manuelle requise" });
      continue;
    }
    try {
      localStorage.setItem(
        legacyDraftKey(knowledgeId),
        JSON.stringify({
          markdown,
          expectedVersion: operation.body?.expected_version,
          actor: operation.body?.actor,
          legacyIdempotencyKey: operation.body?.idempotency_key,
          recoveredAt: new Date().toISOString(),
        }),
      );
      recovered += 1;
    } catch (error) {
      remaining.push({ ...operation, conflict: `récupération locale impossible : ${error.message}` });
    }
  }
  setQueue(remaining);
  return recovered;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { ...headers(), ...(options.headers || {}) },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(payload.detail || response.statusText);
  }
  return response;
}

function renderItems() {
  $("items").innerHTML = "";
  for (const item of state.items) {
    const button = document.createElement("button");
    button.className = `item ${state.current?.knowledge_id === item.knowledge_id ? "active" : ""}`;
    button.append(document.createTextNode(item.title));
    const detail = document.createElement("small");
    detail.textContent = `${item.family} · v${item.version} · ${item.review_status}`;
    button.append(detail);
    button.onclick = () => openItem(item);
    $("items").append(button);
  }
  if (!state.items.length) $("items").innerHTML = '<p class="muted">Aucun sujet Knowledge.</p>';
}

async function loadProject() {
  state.token = $("token").value;
  state.project = $("project").value.trim();
  state.actor = $("actor").value.trim();
  if (state.actor) sessionStorage.setItem("pantheon-human-actor", state.actor);
  if (!state.project) return message("Indiquez le projet.");
  const recovered = migrateLegacyRevisions();
  try {
    const response = await api(`../projects/${encodeURIComponent(state.project)}/knowledge`);
    state.items = (await response.json()).knowledge;
    localStorage.setItem(`pantheon-project:${state.project}`, JSON.stringify(state.items));
    renderItems();
    message(recovered
      ? `${state.items.length} sujet(s) chargé(s). ${recovered} ancienne(s) révision(s) récupérée(s) comme brouillon local.`
      : `${state.items.length} sujet(s) chargé(s).`);
    await syncQueue();
  } catch (error) {
    state.items = JSON.parse(localStorage.getItem(`pantheon-project:${state.project}`) || "[]");
    renderItems();
    message(`Mode hors ligne : ${error.message}${recovered ? ` · ${recovered} ancienne(s) révision(s) récupérée(s).` : ""}`);
  }
}

async function openItem(item) {
  state.current = item;
  state.pendingUpdate = null;
  renderItems();
  let markdown;
  let loadedRemote = false;
  const recovered = recoveredLegacyDraft(item.knowledge_id);
  try {
    const remoteMarkdown = await (await api(`../knowledge/${encodeURIComponent(item.knowledge_id)}/markdown`)).text();
    loadedRemote = true;
    state.baseMarkdown = remoteMarkdown;
    markdown = recovered?.markdown ?? remoteMarkdown;
    localStorage.setItem(
      key(item.knowledge_id),
      JSON.stringify({ item, markdown, baseMarkdown: remoteMarkdown }),
    );
  } catch {
    const cached = JSON.parse(localStorage.getItem(key(item.knowledge_id)) || "null");
    if (!cached && !recovered) return message("Ce sujet n’est pas encore disponible hors ligne.");
    if (cached) {
      item = cached.item;
      state.current = item;
      state.baseMarkdown = cached.baseMarkdown || cached.markdown;
      markdown = recovered?.markdown ?? cached.markdown;
    } else {
      state.baseMarkdown = recovered.markdown;
      markdown = recovered.markdown;
    }
  }
  if (loadedRemote && !recovered) state.baseMarkdown = markdown;
  $("title").textContent = item.title;
  $("status").textContent = `${item.family} · version ${item.version} · ${item.review_status}`;
  $("markdown").value = markdown;
  $("markdown").disabled = false;
  $("save").disabled = false;
  document.querySelectorAll("[data-action]").forEach(button => { button.disabled = false; });
  message(recovered
    ? "Une ancienne révision hors ligne a été récupérée. Prévisualisez puis confirmez son UPDATE signé ; elle ne sera pas écrasée par le serveur."
    : "Le brouillon reste local jusqu’à un UPDATE confirmé.");
}

function storeDraft() {
  if (!state.current) return;
  localStorage.setItem(
    key(state.current.knowledge_id),
    JSON.stringify({
      item: state.current,
      markdown: $("markdown").value,
      baseMarkdown: state.baseMarkdown,
    }),
  );
}

async function previewRevision() {
  if (!state.current) return;
  storeDraft();
  state.actor = $("actor").value.trim();
  if (!state.actor) return message("Indiquez l’identité humaine avant toute révision.");
  sessionStorage.setItem("pantheon-human-actor", state.actor);
  if (!navigator.onLine) {
    return message("Brouillon conservé localement. La prévisualisation signée nécessite une connexion.");
  }
  const candidateMarkdown = $("markdown").value;
  if (candidateMarkdown === state.baseMarkdown) return message("Aucune modification à prévisualiser.");

  $("save").disabled = true;
  message("Calcul du diff signé…");
  try {
    const response = await api(
      `../projects/${encodeURIComponent(state.project)}/knowledge/${encodeURIComponent(state.current.knowledge_id)}/updates/preview`,
      {
        method: "POST",
        headers: { "X-Pantheon-Human-Actor": state.actor },
        body: JSON.stringify({
          proposed_markdown: candidateMarkdown,
          expected_version: state.current.version,
          review_status: null,
        }),
      },
    );
    const preview = await response.json();
    state.pendingUpdate = {
      preview,
      candidateMarkdown,
      idempotencyKey: uuid("mobile-update"),
      knowledgeId: state.current.knowledge_id,
      expectedVersion: state.current.version,
    };
    renderConfirmation();
    message("Diff prêt. La révision n’est pas encore appliquée.");
  } catch (error) {
    message(`Prévisualisation refusée : ${error.message}`);
  } finally {
    $("save").disabled = false;
  }
}

function renderConfirmation() {
  const pending = state.pendingUpdate;
  if (!pending) return;
  const { preview } = pending;
  $("update-diff").textContent = preview.diff || "Aucune différence textuelle affichable.";
  $("update-identity").textContent = [
    `Acteur déclaré : ${preview.identity.declared_actor}.`,
    `Assurance : ${preview.identity.assurance}.`,
    `Expiration : ${new Date(preview.confirmation.expires_at * 1000).toLocaleTimeString("fr-FR")}.`,
    `Statut de revue conservé : ${preview.target.current_review_status}.`,
  ].join(" ");
  $("confirmation-label").firstChild.textContent = `Saisir exactement « ${preview.confirmation.phrase} » `;
  $("confirmation").value = "";
  $("confirmation").disabled = false;
  $("apply-update").disabled = true;
  $("update-message").textContent = "Relisez le diff avant de confirmer.";
  $("update-dialog").showModal();
}

async function applyPendingUpdate() {
  const pending = state.pendingUpdate;
  if (!pending || !state.current) return;
  const phrase = $("confirmation").value;
  if (phrase !== pending.preview.confirmation.phrase) return;
  if ($("markdown").value !== pending.candidateMarkdown) {
    $("update-message").textContent = "Le Markdown a changé après signature. Recalculez le diff.";
    $("apply-update").disabled = true;
    return;
  }
  if (!navigator.onLine) {
    $("update-message").textContent = "L’application nécessite une connexion.";
    return;
  }

  $("apply-update").disabled = true;
  $("update-message").textContent = "Application transactionnelle…";
  try {
    const response = await api(
      `../projects/${encodeURIComponent(state.project)}/knowledge/${encodeURIComponent(pending.knowledgeId)}/updates/apply`,
      {
        method: "POST",
        headers: { "X-Pantheon-Human-Actor": state.actor },
        body: JSON.stringify({
          proposed_markdown: pending.candidateMarkdown,
          expected_version: pending.expectedVersion,
          review_status: null,
          base_markdown_digest: pending.preview.base_markdown_digest,
          confirmation_token: pending.preview.confirmation.token,
          confirmation_expires_at: pending.preview.confirmation.expires_at,
          confirmation_phrase: phrase,
          idempotency_key: pending.idempotencyKey,
        }),
      },
    );
    const applied = await response.json();
    const updated = applied.knowledge;
    state.current = updated;
    state.baseMarkdown = pending.candidateMarkdown;
    state.items = state.items.map(item => item.knowledge_id === updated.knowledge_id ? updated : item);
    localStorage.removeItem(legacyDraftKey(updated.knowledge_id));
    localStorage.setItem(
      key(updated.knowledge_id),
      JSON.stringify({
        item: updated,
        markdown: pending.candidateMarkdown,
        baseMarkdown: pending.candidateMarkdown,
      }),
    );
    localStorage.setItem(`pantheon-project:${state.project}`, JSON.stringify(state.items));
    renderItems();
    $("status").textContent = `${updated.family} · version ${updated.version} · ${updated.review_status}`;
    $("update-message").textContent = `UPDATE appliqué en version ${updated.version}. Le statut de revue n’a pas été promu.`;
    $("confirmation").disabled = true;
    state.pendingUpdate = null;
    message(`Révision appliquée en version ${updated.version}. Knowledge révisée ≠ Evidence.`);
  } catch (error) {
    $("update-message").textContent = `Application refusée : ${error.message}`;
    $("apply-update").disabled = false;
  }
}

async function requestEdit(kind) {
  if (!state.current) return;
  state.actor = $("actor").value.trim();
  if (!state.actor) return message("Indiquez l’identité humaine avant une demande Hermes.");
  const textarea = $("markdown");
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  if (textarea.value !== state.baseMarkdown) return message("Confirmez d’abord le brouillon avant une demande intelligente.");
  if (start === end) return message("Sélectionnez d’abord une zone du texte.");
  const operation = {
    type: "edit_request",
    knowledge_id: state.current.knowledge_id,
    body: {
      request_id: uuid("edit"),
      instruction_kind: kind,
      instruction: instructionLabels[kind],
      base_version: state.current.version,
      selection_start: start,
      selection_end: end,
      selected_text: textarea.value.slice(start, end),
      requested_by: state.actor,
      idempotency_key: uuid("mobile-edit"),
    },
  };
  setQueue([...queue(), operation]);
  message("Demande intelligente mise en file pour Hermes. Le texte n’est pas modifié tant qu’une proposition n’est pas appliquée.");
  await syncQueue();
}

async function syncQueue() {
  const recovered = migrateLegacyRevisions();
  if (!navigator.onLine || !state.token) {
    if (recovered) message(`${recovered} ancienne(s) révision(s) récupérée(s) comme brouillon local.`);
    return;
  }
  const pending = queue();
  const remaining = [];
  for (const operation of pending) {
    try {
      const path = `../knowledge/${encodeURIComponent(operation.knowledge_id)}/edit-requests`;
      await api(path, { method: "POST", body: JSON.stringify(operation.body) });
    } catch (error) {
      remaining.push({ ...operation, conflict: String(error.message) });
    }
  }
  setQueue(remaining);
  const details = [];
  if (recovered) details.push(`${recovered} ancienne(s) révision(s) récupérée(s) comme brouillon local`);
  if (remaining.length) details.push(`${remaining.length} demande(s) Hermes en attente ou en conflit`);
  message(details.length ? `${details.join(". ")}.` : "Synchronisation des demandes Hermes terminée.");
}

function clearLocalData() {
  const prefixes = ["pantheon-knowledge:", "pantheon-project:"];
  for (let index = localStorage.length - 1; index >= 0; index -= 1) {
    const storedKey = localStorage.key(index);
    if (storedKey && prefixes.some(prefix => storedKey.startsWith(prefix))) {
      localStorage.removeItem(storedKey);
    }
  }
  sessionStorage.removeItem("pantheon-human-actor");
  state.items = [];
  state.current = null;
  state.baseMarkdown = "";
  state.token = "";
  state.project = "";
  state.actor = "";
  state.pendingUpdate = null;
  window.location.reload();
}

$("load").onclick = loadProject;
$("save").onclick = previewRevision;
$("apply-update").onclick = applyPendingUpdate;
$("clear-local").onclick = clearLocalData;
$("confirmation").addEventListener("input", () => {
  const expected = state.pendingUpdate?.preview?.confirmation?.phrase;
  $("apply-update").disabled = $("confirmation").value !== expected;
});
$("update-dialog").addEventListener("close", () => {
  state.pendingUpdate = null;
  $("confirmation").value = "";
});
$("markdown").addEventListener("input", storeDraft);
document.querySelectorAll("[data-action]").forEach(button => {
  button.onclick = () => requestEdit(button.dataset.action);
});
window.addEventListener("online", () => { setNetwork(); syncQueue(); });
window.addEventListener("offline", setNetwork);
$("actor").value = sessionStorage.getItem("pantheon-human-actor") || "";
const recoveredAtStartup = migrateLegacyRevisions();
setNetwork();
if (recoveredAtStartup) message(`${recoveredAtStartup} ancienne(s) révision(s) récupérée(s) comme brouillon local.`);
if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js");
