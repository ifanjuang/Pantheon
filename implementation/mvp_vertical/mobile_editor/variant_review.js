(() => {
  "use strict";

  const variantQueueKey = "pantheon-knowledge:variant-queue";
  const instructionLabels = {
    rewrite: "Reformuler la sélection sans en changer le sens.",
    expand: "Détailler la sélection avec les précisions utiles.",
    simplify: "Simplifier la sélection sans perdre les exigences.",
    verify: "Vérifier la sélection et signaler les points à confirmer.",
    move_to_lot: "Proposer le déplacement de la sélection dans un autre lot.",
  };
  let loadingReviews = false;

  function variantQueue() {
    try {
      return JSON.parse(localStorage.getItem(variantQueueKey) || "[]");
    } catch (_) {
      return [];
    }
  }

  function setVariantQueue(value) {
    localStorage.setItem(variantQueueKey, JSON.stringify(value));
  }

  function humanHeaders() {
    const actor = $("actor").value.trim();
    if (!actor) throw new Error("Indiquez l’identité humaine.");
    return { "X-Pantheon-Human-Actor": actor };
  }

  function refreshAvailability() {
    const active = Boolean(state.current);
    $("variant-ab").disabled = !active;
    $("refresh-reviews").disabled = !active || loadingReviews;
  }

  async function requestVariantEdit(kind, requestedVariantCount = 1) {
    if (!state.current) return message("Ouvrez d’abord un sujet Knowledge.");
    state.actor = $("actor").value.trim();
    if (!state.actor) return message("Indiquez l’identité humaine avant une demande Hermes.");
    const textarea = $("markdown");
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    if (textarea.value !== state.baseMarkdown) {
      return message("Confirmez d’abord le brouillon avant une demande intelligente.");
    }
    if (start === end) return message("Sélectionnez d’abord une zone du texte.");
    const baseInstruction = instructionLabels[kind] || instructionLabels.rewrite;
    const operation = {
      type: "variant_edit_request",
      knowledge_id: state.current.knowledge_id,
      body: {
        request_id: uuid("edit"),
        instruction_kind: kind,
        instruction: requestedVariantCount === 2
          ? `${baseInstruction} Produire deux variantes réellement distinctes, A et B.`
          : baseInstruction,
        base_version: state.current.version,
        selection_start: start,
        selection_end: end,
        selected_text: textarea.value.slice(start, end),
        requested_by: state.actor,
        requested_variant_count: requestedVariantCount,
        idempotency_key: uuid("mobile-edit-variant"),
      },
    };
    setVariantQueue([...variantQueue(), operation]);
    message(requestedVariantCount === 2
      ? "Demande A/B mise en file. Le retour d’exécution, la sélection et l’application resteront séparés."
      : "Demande intelligente mise en file. Le texte ne sera pas modifié par la proposition.");
    await syncVariantQueue();
  }

  async function syncVariantQueue() {
    if (!navigator.onLine || !state.token) return;
    const remaining = [];
    for (const operation of variantQueue()) {
      try {
        await api(
          `../knowledge/${encodeURIComponent(operation.knowledge_id)}/variant-edit-requests`,
          { method: "POST", body: JSON.stringify(operation.body) },
        );
      } catch (error) {
        remaining.push({ ...operation, conflict: String(error.message) });
      }
    }
    setVariantQueue(remaining);
    if (remaining.length) {
      message(`${remaining.length} demande(s) de variantes en attente ou en conflit.`);
    } else if (state.current) {
      await loadReviews();
    }
  }

  function reviewStatusLabel(status) {
    return {
      queued_for_hermes: "En attente d’Hermès",
      proposed: "À examiner",
      applied: "Appliquée",
      conflict: "Conflit de version",
      rejected: "Refusée",
    }[status] || status;
  }

  function makeButton(label, action, options = {}) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.disabled = options.disabled === true;
    button.className = options.className || "";
    button.addEventListener("click", action);
    return button;
  }

  function renderVariant(requestId, variant, requestStatus) {
    const article = document.createElement("article");
    article.className = `proposal-variant ${variant.selected ? "selected" : ""}`;
    const header = document.createElement("header");
    const title = document.createElement("h4");
    title.textContent = `Variante ${variant.variant_label}`;
    const digest = document.createElement("small");
    digest.textContent = variant.replacement_digest?.slice(0, 19) || "digest absent";
    header.append(title, digest);
    const diff = document.createElement("pre");
    diff.tabIndex = 0;
    diff.textContent = variant.diff || variant.replacement_markdown;
    const actions = document.createElement("div");
    actions.className = "proposal-actions";
    if (requestStatus === "proposed") {
      actions.append(makeButton(
        variant.selected ? "Variante sélectionnée" : `Sélectionner ${variant.variant_label}`,
        () => selectVariant(requestId, variant.variant_id),
        { disabled: variant.selected },
      ));
    }
    article.append(header, diff, actions);
    return article;
  }

  function renderReview(review) {
    const request = review.edit_request;
    const article = document.createElement("article");
    article.className = `edit-review edit-review--${request.status}`;
    const header = document.createElement("header");
    const title = document.createElement("div");
    const heading = document.createElement("h3");
    heading.textContent = request.requested_variant_count === 2 ? "Proposition A/B" : "Proposition";
    const meta = document.createElement("p");
    meta.className = "muted";
    meta.textContent = `${reviewStatusLabel(request.status)} · base v${request.base_version} · ${request.scope_status}`;
    title.append(heading, meta);
    const selected = document.createElement("blockquote");
    selected.textContent = request.selected_text || "Sélection non disponible";
    selected.setAttribute("aria-label", "Sélection source");
    header.append(title);
    article.append(header, selected);

    if (review.variants.length) {
      const variants = document.createElement("div");
      variants.className = "proposal-variants";
      for (const variant of review.variants) {
        variants.append(renderVariant(request.request_id, variant, request.status));
      }
      article.append(variants);
    } else {
      const waiting = document.createElement("p");
      waiting.className = "muted";
      waiting.textContent = "Aucune variante projetée. Un Execution Result stocké ne vaut pas encore proposition affichée.";
      article.append(waiting);
    }

    if (request.status === "proposed") {
      const actions = document.createElement("div");
      actions.className = "proposal-actions proposal-actions--request";
      actions.append(
        makeButton(
          "Appliquer la variante sélectionnée",
          () => applySelected(request.request_id),
          { disabled: !request.selected_variant_id, className: "danger" },
        ),
        makeButton("Refuser la proposition", () => rejectRequest(request.request_id)),
      );
      article.append(actions);
    }
    return article;
  }

  async function loadReviews() {
    if (loadingReviews || !state.current || !state.token || !navigator.onLine) {
      refreshAvailability();
      return;
    }
    loadingReviews = true;
    refreshAvailability();
    const container = $("edit-reviews");
    try {
      const response = await api(
        `../knowledge/${encodeURIComponent(state.current.knowledge_id)}/edit-reviews?limit=20`,
      );
      const payload = await response.json();
      container.replaceChildren();
      const reviews = payload.edit_reviews || [];
      for (const review of reviews) container.append(renderReview(review));
      if (!reviews.length) {
        const empty = document.createElement("p");
        empty.className = "muted";
        empty.textContent = "Aucune demande intelligente pour ce sujet.";
        container.append(empty);
      }
    } catch (error) {
      container.replaceChildren();
      const failure = document.createElement("p");
      failure.className = "muted";
      failure.textContent = `Propositions indisponibles : ${error.message}`;
      container.append(failure);
    } finally {
      loadingReviews = false;
      refreshAvailability();
    }
  }

  async function selectVariant(requestId, variantId) {
    try {
      await api(`../edit-requests/${encodeURIComponent(requestId)}/select-variant`, {
        method: "POST",
        headers: humanHeaders(),
        body: JSON.stringify({
          variant_id: variantId,
          idempotency_key: uuid("mobile-variant-selection"),
        }),
      });
      message("Variante sélectionnée. Aucun Markdown n’a encore été modifié.");
      await loadReviews();
    } catch (error) {
      message(`Sélection refusée : ${error.message}`);
    }
  }

  async function rejectRequest(requestId) {
    const reason = window.prompt("Motif du refus de cette proposition :", "Proposition non retenue");
    if (!reason?.trim()) return;
    try {
      await api(`../edit-requests/${encodeURIComponent(requestId)}/reject`, {
        method: "POST",
        headers: humanHeaders(),
        body: JSON.stringify({
          reason: reason.trim(),
          idempotency_key: uuid("mobile-edit-reject"),
        }),
      });
      message("Proposition refusée. La Knowledge reste inchangée.");
      await loadReviews();
    } catch (error) {
      message(`Refus non enregistré : ${error.message}`);
    }
  }

  async function applySelected(requestId) {
    if (!window.confirm("Appliquer exactement la variante sélectionnée à la Knowledge courante ?")) return;
    try {
      const response = await api(`../edit-requests/${encodeURIComponent(requestId)}/apply-selected`, {
        method: "POST",
        headers: humanHeaders(),
        body: JSON.stringify({ idempotency_key: uuid("mobile-edit-apply-selected") }),
      });
      const payload = await response.json();
      const updated = payload.knowledge;
      const markdown = await (await api(`../knowledge/${encodeURIComponent(updated.knowledge_id)}/markdown`)).text();
      state.current = updated;
      state.baseMarkdown = markdown;
      state.items = state.items.map(item => item.knowledge_id === updated.knowledge_id ? updated : item);
      $("markdown").value = markdown;
      $("status").textContent = `${updated.family} · version ${updated.version} · ${updated.review_status}`;
      localStorage.setItem(
        key(updated.knowledge_id),
        JSON.stringify({ item: updated, markdown, baseMarkdown: markdown }),
      );
      localStorage.setItem(`pantheon-project:${state.project}`, JSON.stringify(state.items));
      renderItems();
      message(`Variante appliquée en version ${updated.version}. Le statut de revue n’a pas été promu.`);
      await loadReviews();
    } catch (error) {
      message(`Application refusée : ${error.message}`);
    }
  }

  function install() {
    document.querySelectorAll("[data-action]").forEach(button => {
      button.onclick = () => requestVariantEdit(button.dataset.action, 1);
    });
    $("variant-ab").onclick = () => requestVariantEdit("rewrite", 2);
    $("refresh-reviews").onclick = loadReviews;
    new MutationObserver(() => {
      refreshAvailability();
      if (state.current) void loadReviews();
    }).observe($("status"), { childList: true, characterData: true, subtree: true });
    window.addEventListener("online", () => { void syncVariantQueue().then(loadReviews); });
    $("load").addEventListener("click", () => { setTimeout(() => void syncVariantQueue(), 0); });
    refreshAvailability();
    void syncVariantQueue();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", install, { once: true });
  } else {
    install();
  }
})();
