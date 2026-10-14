(() => {
  "use strict";

  const $ = id => document.getElementById(id);
  const key = prefix => `${prefix}-${globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`}`;

  function credentials() {
    const token = $("v2-token")?.value?.trim() || "";
    const actor = $("v2-handoff-actor")?.value?.trim() || "";
    if (!token) throw new Error("Clé éditeur requise pour cette décision.");
    if (!actor) throw new Error("Renseignez l’acteur humain dans le dock Hermès.");
    return { token, actor };
  }

  function currentCandidate() {
    const card = document.querySelector("#v2-stage :is(.card, .v2-card)");
    const entityId = card?.querySelector(":is(.card-entity-id, .v2-entity-id)")?.textContent?.trim() || "";
    const prefix = "decision:change:";
    if (!entityId.startsWith(prefix)) return null;
    return {
      candidateId: entityId.slice(prefix.length),
      title: card?.querySelector(":is(.card-title, .v2-card-title)")?.textContent?.trim() || "Modification proposée",
    };
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
    if (!response.ok) throw new Error(payload.detail || response.statusText);
    return payload;
  }

  async function decideCandidate(action, candidate) {
    const validate = action === "Valider";
    if (validate) {
      if (!window.confirm(`Valider « ${candidate.title} » ?\n\nLa révision de base sera revérifiée côté serveur avant toute mutation du Projet.`)) return;
      const result = await request(`../agency/change-candidates/${encodeURIComponent(candidate.candidateId)}/apply`, {
        idempotency_key: key("change-apply"),
      });
      if (!result.applied) window.alert("La proposition est devenue obsolète : aucune modification du Projet n’a été appliquée.");
    } else {
      const reason = window.prompt(`Pourquoi refuser « ${candidate.title} » ?`, "");
      if (!reason?.trim()) return;
      await request(`../agency/change-candidates/${encodeURIComponent(candidate.candidateId)}/reject`, {
        reason: reason.trim(),
        idempotency_key: key("change-reject"),
      });
    }
    $("v2-load")?.click();
  }

  function install() {
    const stage = $("v2-stage");
    if (!stage) return;
    stage.addEventListener("click", event => {
      const button = event.target.closest?.("button[data-card-action]");
      if (!button || !["Valider", "Refuser"].includes(button.dataset.cardAction)) return;
      const candidate = currentCandidate();
      if (!candidate) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      button.disabled = true;
      void decideCandidate(button.dataset.cardAction, candidate)
        .catch(error => window.alert(error.message || String(error)))
        .finally(() => { button.disabled = false; });
    }, true);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install, { once: true });
  else install();
})();