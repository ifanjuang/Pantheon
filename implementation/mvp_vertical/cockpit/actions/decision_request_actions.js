(() => {
  "use strict";

  const $ = id => document.getElementById(id);
  const REQUEST_PREFIX = "decision-request:";

  function unique(prefix) {
    return `${prefix}-${globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`}`;
  }

  function credentials() {
    const token = $("v2-token")?.value?.trim() || "";
    const actor = $("v2-handoff-actor")?.value?.trim() || "";
    if (!token) throw new Error("Clé éditeur requise pour enregistrer la réponse humaine.");
    if (!actor) throw new Error("Renseignez l’acteur humain dans le dock Hermès.");
    return { token, actor };
  }

  function requestIdFromCard(card) {
    const entityId = card?.querySelector(":is(.card-entity-id, .v2-entity-id)")?.textContent?.trim() || "";
    return entityId.startsWith(REQUEST_PREFIX) ? entityId.slice(REQUEST_PREFIX.length) : null;
  }

  function currentRequestId() {
    const card = document.querySelector("#v2-stage :is(.card, .v2-card)");
    const requestId = requestIdFromCard(card);
    if (!requestId) {
      throw new Error("Cette action exige une Carte Decision Request.");
    }
    return requestId;
  }

  async function request(path, { method = "GET", body = null } = {}) {
    const { token, actor } = credentials();
    const headers = {
      Authorization: `Bearer ${token}`,
      "X-Pantheon-Human-Actor": actor,
    };
    if (body !== null) headers["Content-Type"] = "application/json";
    const response = await fetch(path, {
      method,
      headers,
      body: body === null ? undefined : JSON.stringify(body),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || response.statusText || "Réponse refusée");
    return payload;
  }

  function optionMenu(options) {
    return options.map((option, index) => `${index + 1}. ${option.label}\n   ${option.consequence}`).join("\n");
  }

  function selectedOptions(requestData) {
    const options = requestData.options || [];
    const menu = optionMenu(options);
    if (requestData.response_mode === "single_option") {
      const answer = window.prompt(`${requestData.question}\n\n${menu}\n\nNuméro retenu :`, "1");
      if (answer == null) return null;
      const index = Number(answer.trim()) - 1;
      if (!Number.isInteger(index) || !options[index]) throw new Error("Option invalide.");
      return [options[index].option_id];
    }
    if (requestData.response_mode === "multiple_options") {
      const answer = window.prompt(
        `${requestData.question}\n\n${menu}\n\nNuméros retenus, séparés par des virgules :`,
        "1",
      );
      if (answer == null) return null;
      const indexes = [...new Set(answer.split(",").map(value => Number(value.trim()) - 1))];
      if (!indexes.length || indexes.some(index => !Number.isInteger(index) || !options[index])) {
        throw new Error("Sélection d’options invalide.");
      }
      return indexes.map(index => options[index].option_id);
    }
    return [];
  }

  function responseText(requestData) {
    if (requestData.response_mode !== "free_text") return null;
    const answer = window.prompt(requestData.question, "");
    if (answer == null || !answer.trim()) return undefined;
    return answer.trim();
  }

  function decisionValue(requestData) {
    if (["single_option", "multiple_options", "free_text"].includes(requestData.response_mode)) {
      return "approve";
    }
    const answer = window.prompt(
      `${requestData.question}\n\nRéponse : approve, refuse, request_revision ou request_more_evidence`,
      "approve",
    );
    if (answer == null) return null;
    const value = answer.trim();
    if (!["approve", "refuse", "request_revision", "request_more_evidence"].includes(value)) {
      throw new Error("Valeur de décision invalide.");
    }
    return value;
  }

  async function answerQuestion(requestId, requestData) {
    if (requestData.response_mode === "decision_value") {
      throw new Error("Cette question historique utilise un mode décisionnel ambigu et doit être reclassifiée.");
    }
    const selectedOptionIds = selectedOptions(requestData);
    if (selectedOptionIds == null) return false;
    const text = responseText(requestData);
    if (text === undefined) return false;
    const { actor } = credentials();
    const confirmed = window.confirm(
      `Enregistrer la réponse de ${actor} ?\n\n` +
      "Cette opération crée une HumanResponse immuable. Elle ne crée pas de Decision, n’autorise aucune action et ne reprend pas la Tâche.",
    );
    if (!confirmed) return false;

    await request(`../decision-requests/${encodeURIComponent(requestId)}/resolve`, {
      method: "POST",
      body: {
        response_id: unique("human-response"),
        identity_assurance: "declared",
        expected_revision: requestData.revision,
        idempotency_key: unique("response-resolve"),
        selected_option_ids: selectedOptionIds,
        response_text: text,
      },
    });
    return true;
  }

  async function recordDecision(requestId, requestData) {
    const decision = decisionValue(requestData);
    if (decision == null) return false;
    const selectedOptionIds = selectedOptions(requestData);
    if (selectedOptionIds == null) return false;
    const text = responseText(requestData);
    if (text === undefined) return false;
    const rationale = window.prompt("Motif de la décision (optionnel)", "") || null;
    const { actor } = credentials();
    const confirmed = window.confirm(
      `Enregistrer la décision de ${actor} ?\n\n` +
      "Cette opération crée un Decision record immuable. Elle ne reprend pas la Tâche et n’exécute aucune action.",
    );
    if (!confirmed) return false;

    await request(`../decision-requests/${encodeURIComponent(requestId)}/resolve`, {
      method: "POST",
      body: {
        decision_id: unique("decision"),
        decision,
        identity_assurance: "declared",
        expected_revision: requestData.revision,
        idempotency_key: unique("decision-resolve"),
        selected_option_ids: selectedOptionIds,
        response_text: text,
        rationale: rationale?.trim() || null,
      },
    });
    return true;
  }

  async function decide() {
    const requestId = currentRequestId();
    const envelope = await request(`../decision-requests/${encodeURIComponent(requestId)}`);
    const requestData = envelope.decision_request || {};
    if (requestData.status !== "pending") {
      throw new Error("Cette demande ne requiert plus de réponse humaine.");
    }

    const recorded = requestData.decision_type === "question"
      ? await answerQuestion(requestId, requestData)
      : await recordDecision(requestId, requestData);
    if (recorded) $("v2-load")?.click();
  }

  function enable(root = document) {
    for (const card of root.querySelectorAll?.(":is(.card, .v2-card)") || []) {
      if (!requestIdFromCard(card)) continue;
      for (const button of card.querySelectorAll?.(":is(.card-actions, .v2-card-actions) button") || []) {
        button.disabled = false;
        button.title = "";
        button.dataset.decisionRequestAction = "resolve";
      }
    }
  }

  function install() {
    const stage = $("v2-stage");
    if (!stage) return;
    enable(stage);
    new MutationObserver(() => enable(stage)).observe(stage, { childList: true, subtree: true });
    stage.addEventListener("click", event => {
      const button = event.target.closest?.("button[data-decision-request-action]");
      if (!button) return;
      event.preventDefault();
      button.disabled = true;
      void decide()
        .catch(error => window.alert(error.message || String(error)))
        .finally(() => { button.disabled = false; });
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install, { once: true });
  else install();
})();
