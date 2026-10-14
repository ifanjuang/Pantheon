(() => {
  "use strict";

  const $ = id => document.getElementById(id);
  const PREFIX = "decision:change:";
  const TYPE_LABELS = Object.freeze({
    source_required: "Source requise",
    question: "Question",
    hypothesis: "Hypothèse",
    contradiction: "Contradiction",
    needs_deeper_review: "Point à approfondir",
  });
  const EVENT_LABELS = Object.freeze({
    proposed: "Proposition créée",
    revision_requested: "Révision demandée",
    applied: "Proposition appliquée",
    rejected: "Proposition refusée",
    stale: "Proposition obsolète",
  });
  const key = prefix => `${prefix}-${globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`}`;
  let returnFocus = null;

  function readToken() {
    const token = $("v2-token")?.value?.trim() || "";
    if (!token) throw new Error("Clé de lecture requise pour examiner la proposition.");
    return token;
  }

  function credentials() {
    const token = readToken();
    const actor = $("v2-handoff-actor")?.value?.trim() || "";
    if (!actor) throw new Error("Renseignez l’acteur humain dans le dock Hermès.");
    return { token, actor };
  }

  function candidateId(card) {
    const identity = card?.querySelector(":is(.card-entity-id, .v2-entity-id)")?.textContent?.trim() || "";
    return identity.startsWith(PREFIX) ? identity.slice(PREFIX.length) : "";
  }

  async function request(path, { method = "GET", body = null, human = false } = {}) {
    const auth = human ? credentials() : { token: readToken(), actor: "" };
    const headers = { Authorization: `Bearer ${auth.token}` };
    if (human) headers["X-Pantheon-Actor"] = auth.actor;
    if (body !== null) headers["Content-Type"] = "application/json";
    const response = await fetch(path, {
      method,
      headers,
      cache: "no-store",
      body: body === null ? undefined : JSON.stringify(body),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || response.statusText);
    return payload;
  }

  function textSection(heading, value, marker) {
    const section = document.createElement("section");
    section.className = "card-back-section v2-back-section";
    if (marker) section.dataset.changeCandidateReview = marker;
    const title = document.createElement("h3");
    title.textContent = heading;
    const content = document.createElement("p");
    content.className = "card-back-multiline v2-back-multiline";
    for (const line of String(value || "").split("\n").filter(Boolean)) {
      const span = document.createElement("span");
      span.textContent = line;
      content.append(span);
    }
    section.append(title, content);
    return section;
  }

  function annotationLine(annotation) {
    const scope = annotation.field ? ` · ${annotation.field}` : "";
    const refs = (annotation.source_refs || []).length ? ` · Sources : ${annotation.source_refs.join(", ")}` : "";
    return `${TYPE_LABELS[annotation.annotation_type] || annotation.annotation_type}${scope} — ${annotation.message}${refs}`;
  }

  function eventLine(event) {
    const date = event.occurred_at ? String(event.occurred_at).slice(0, 19).replace("T", " ") : "Date non renseignée";
    return `${date} · ${EVENT_LABELS[event.event_type] || event.event_type} · ${event.actor}`;
  }

  function projectReview(card, payload) {
    const body = card.querySelector(":is(.card-back-body, .v2-back-body)");
    if (!body) return;
    body.querySelectorAll("[data-change-candidate-review]").forEach(node => node.remove());
    const candidate = payload.change_candidate || {};
    const annotations = Array.isArray(candidate.review_annotations) ? candidate.review_annotations : [];
    if (annotations.length) {
      body.append(textSection("Annotations de revue", annotations.map(annotationLine).join("\n"), "annotations"));
    }
    if (candidate.decision_note) {
      body.append(textSection("Note de décision", candidate.decision_note, "note"));
    }
    const events = Array.isArray(payload.review_events) ? payload.review_events : [];
    if (events.length) {
      body.append(textSection("Historique", events.map(eventLine).join("\n"), "history"));
    }
    card.dataset.changeCandidateReviewState = "ready";
  }

  async function enhance(card) {
    const id = candidateId(card);
    if (!id || card.dataset.changeCandidateReviewState) return;
    card.dataset.changeCandidateReviewState = "loading";
    try {
      const payload = await request(`../agency/change-candidates/${encodeURIComponent(id)}`);
      projectReview(card, payload);
      const candidate = payload.change_candidate || {};
      const actions = card.querySelector(":is(.card-actions, .v2-card-actions)");
      if (actions && candidate.status === "pending_review" && !actions.querySelector("[data-change-review-action]")) {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = "Demander une révision";
        button.dataset.changeReviewAction = "request-revision";
        button.disabled = false;
        button.title = "Renvoyer cette proposition avec des annotations structurées, sans modifier le Projet.";
        actions.append(button);
      }
    } catch (error) {
      card.dataset.changeCandidateReviewState = "error";
      card.dataset.changeCandidateReviewError = error.message || String(error);
    }
  }

  function reviewDialog() {
    let dialog = document.querySelector(".change-candidate-review-dialog");
    if (dialog) return dialog;
    dialog = document.createElement("dialog");
    dialog.className = "change-candidate-review-dialog";
    dialog.setAttribute("aria-labelledby", "change-candidate-review-title");
    dialog.innerHTML = `
      <form method="dialog" class="change-candidate-review-shell">
        <header>
          <div><p class="change-candidate-review-eyebrow">Décision humaine</p><h2 id="change-candidate-review-title">Demander une révision</h2></div>
          <button type="button" data-review-close aria-label="Fermer">×</button>
        </header>
        <p class="change-candidate-review-boundary">La demande clôt la proposition courante. Elle ne modifie pas le Projet et ne relance pas automatiquement Hermès.</p>
        <section class="change-candidate-review-builder" aria-label="Ajouter une annotation">
          <label>Type
            <select name="annotation_type">
              <option value="source_required">Source requise</option>
              <option value="question">Question</option>
              <option value="hypothesis">Hypothèse</option>
              <option value="contradiction">Contradiction</option>
              <option value="needs_deeper_review">Point à approfondir</option>
            </select>
          </label>
          <label>Champ concerné
            <select name="field"><option value="">Proposition globale</option></select>
          </label>
          <label class="change-candidate-review-wide">Annotation
            <textarea name="message" rows="4" maxlength="5000" required></textarea>
          </label>
          <label class="change-candidate-review-wide">Références source, une par ligne
            <textarea name="source_refs" rows="2" maxlength="10000"></textarea>
          </label>
          <button type="button" data-review-add>Ajouter l’annotation</button>
        </section>
        <section aria-label="Annotations préparées">
          <h3>Annotations</h3>
          <ol class="change-candidate-review-list"></ol>
        </section>
        <label>Note générale
          <textarea name="note" rows="3" maxlength="10000"></textarea>
        </label>
        <p class="change-candidate-review-message" aria-live="polite"></p>
        <footer>
          <button type="button" data-review-cancel>Annuler</button>
          <button type="submit" data-review-submit>Envoyer la demande</button>
        </footer>
      </form>`;
    document.body.append(dialog);
    const close = () => dialog.close();
    dialog.querySelector("[data-review-close]").addEventListener("click", close);
    dialog.querySelector("[data-review-cancel]").addEventListener("click", close);
    dialog.addEventListener("click", event => { if (event.target === dialog) close(); });
    dialog.addEventListener("close", () => { returnFocus?.focus?.(); returnFocus = null; });
    return dialog;
  }

  function renderDrafts(dialog, drafts) {
    const list = dialog.querySelector(".change-candidate-review-list");
    list.replaceChildren();
    drafts.forEach((annotation, index) => {
      const item = document.createElement("li");
      const text = document.createElement("span");
      text.textContent = annotationLine(annotation);
      const remove = document.createElement("button");
      remove.type = "button";
      remove.textContent = "Retirer";
      remove.setAttribute("aria-label", `Retirer l’annotation ${index + 1}`);
      remove.addEventListener("click", () => { drafts.splice(index, 1); renderDrafts(dialog, drafts); });
      item.append(text, remove);
      list.append(item);
    });
    if (!drafts.length) {
      const empty = document.createElement("li");
      empty.className = "change-candidate-review-empty";
      empty.textContent = "Aucune annotation ajoutée.";
      list.append(empty);
    }
  }

  function draftFromBuilder(dialog) {
    const form = dialog.querySelector("form");
    const data = new FormData(form);
    const message = String(data.get("message") || "").trim();
    if (!message) throw new Error("Renseignez le contenu de l’annotation.");
    return {
      annotation_type: String(data.get("annotation_type") || ""),
      field: String(data.get("field") || "").trim() || null,
      message,
      source_refs: String(data.get("source_refs") || "").split("\n").map(value => value.trim()).filter(Boolean),
    };
  }

  async function openReview(card, trigger) {
    const id = candidateId(card);
    if (!id) throw new Error("Cette carte n’expose pas une proposition stable.");
    const payload = await request(`../agency/change-candidates/${encodeURIComponent(id)}`);
    const candidate = payload.change_candidate || {};
    if (candidate.status !== "pending_review") throw new Error("Cette proposition n’attend plus une revue humaine.");

    const dialog = reviewDialog();
    const form = dialog.querySelector("form");
    const field = form.elements.field;
    field.replaceChildren(new Option("Proposition globale", ""));
    for (const change of candidate.changes || []) field.append(new Option(change.field, change.field));
    form.elements.message.value = "";
    form.elements.source_refs.value = "";
    form.elements.note.value = "";
    const drafts = [];
    renderDrafts(dialog, drafts);
    dialog.querySelector(".change-candidate-review-message").textContent = "";
    dialog.querySelector("[data-review-add]").onclick = () => {
      try {
        drafts.push(draftFromBuilder(dialog));
        form.elements.message.value = "";
        form.elements.source_refs.value = "";
        renderDrafts(dialog, drafts);
        form.elements.message.focus();
      } catch (error) {
        dialog.querySelector(".change-candidate-review-message").textContent = error.message || String(error);
      }
    };
    form.onsubmit = event => {
      event.preventDefault();
      const message = dialog.querySelector(".change-candidate-review-message");
      if (!drafts.length) {
        message.textContent = "Ajoutez au moins une annotation structurée.";
        return;
      }
      const submit = dialog.querySelector("[data-review-submit]");
      submit.disabled = true;
      message.textContent = "Enregistrement…";
      void request(`../agency/change-candidates/${encodeURIComponent(id)}/request-revision`, {
        method: "POST",
        human: true,
        body: {
          annotations: drafts,
          note: String(form.elements.note.value || "").trim() || null,
          idempotency_key: key("change-revision"),
        },
      }).then(() => {
        dialog.close();
        $("v2-load")?.click();
      }).catch(error => {
        message.textContent = error.message || String(error);
      }).finally(() => { submit.disabled = false; });
    };
    returnFocus = trigger;
    dialog.showModal();
    form.elements.annotation_type.focus();
  }

  function scan(root = document) {
    for (const card of root.querySelectorAll?.("#v2-stage :is(.card, .v2-card)") || []) void enhance(card);
  }

  function install() {
    const stage = $("v2-stage");
    if (!stage) return;
    scan(stage);
    new MutationObserver(() => scan(stage)).observe(stage, { childList: true, subtree: true });
    stage.addEventListener("click", event => {
      const trigger = event.target.closest?.("button[data-change-review-action='request-revision']");
      if (!trigger) return;
      const card = trigger.closest(":is(.card, .v2-card)");
      if (!card) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      trigger.disabled = true;
      void openReview(card, trigger)
        .catch(error => window.alert(error.message || String(error)))
        .finally(() => { trigger.disabled = false; });
    }, true);
    $("v2-load")?.addEventListener("click", () => {
      document.querySelectorAll("[data-change-candidate-review-state]").forEach(card => {
        delete card.dataset.changeCandidateReviewState;
      });
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install, { once: true });
  else install();
})();