(() => {
  "use strict";

  const $ = id => document.getElementById(id);
  const selected = new Map();
  let searchTimer = null;
  let searchGeneration = 0;

  function token() {
    return $("v2-token")?.value || "";
  }

  function queryString(request) {
    const params = new URLSearchParams();
    if (request.query) params.set("q", request.query);
    if (request.limit) params.set("limit", String(request.limit));
    return params.toString();
  }

  async function fetchAgency(path) {
    const currentToken = token();
    if (!currentToken) throw new Error("Clé d’accès requise pour le Context Resolver");
    const response = await fetch(path, {
      headers: { Authorization: `Bearer ${currentToken}` },
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(payload.detail || response.statusText);
    }
    return response.json();
  }

  async function transport(request) {
    if (request.effect !== "read_only" || request.owner_system !== "postgres") {
      throw new Error("Context Resolver Agency Data transport is read-only");
    }
    const query = queryString(request);
    const paths = {
      projects: `../agency/projects?${query}`,
      people: `../agency/people?${query}`,
      organizations: `../agency/organizations?${query}`,
    };
    const path = paths[request.resource];
    if (!path) throw new Error(`Unsupported Agency Data resolver resource: ${request.resource}`);
    return fetchAgency(path);
  }

  const binding = window.PantheonAgencyDataBinding?.create({
    mode: "read_only",
    resolver: window.PantheonContextResolver,
    transport,
  });
  binding?.attach();

  function sourceLabel(item) {
    const source = item.source || {};
    if (source.system === "postgres") return `PostgreSQL · ${source.resource || item.entity_type}`;
    return source.system || item.entity_type;
  }

  function setMessage(message) {
    $("v2-context-message").textContent = message;
  }

  function emitSelection() {
    document.dispatchEvent(new CustomEvent("pantheon:v2-context-changed", {
      detail: {
        selected: [...selected.values()].map(item => ({
          entity_id: item.entity_id,
          entity_type: item.entity_type,
          label: item.label,
          source: item.source,
        })),
        scope_widened_implicitly: false,
      },
    }));
  }

  function renderSelected() {
    const host = $("v2-context-selected");
    host.replaceChildren();
    if (!selected.size) {
      const empty = document.createElement("span");
      empty.className = "v2-context-empty";
      empty.textContent = "Aucun contexte ajouté";
      host.append(empty);
      emitSelection();
      return;
    }
    for (const item of selected.values()) {
      const chip = document.createElement("span");
      chip.className = "v2-context-chip";
      const label = document.createElement("span");
      label.textContent = item.label;
      const remove = document.createElement("button");
      remove.type = "button";
      remove.setAttribute("aria-label", `Retirer ${item.label} du contexte`);
      remove.textContent = "×";
      remove.addEventListener("click", () => {
        selected.delete(`${item.entity_type}:${item.entity_id}`);
        renderSelected();
      });
      chip.append(label, remove);
      host.append(chip);
    }
    emitSelection();
  }

  function selectResult(item) {
    if (!item.entity_id) {
      setMessage("Ce résultat n’a pas encore d’identité stable et ne peut pas être ajouté durablement.");
      return;
    }
    selected.set(`${item.entity_type}:${item.entity_id}`, item);
    renderSelected();
    setMessage(`${item.label} ajouté au contexte sélectionné. Sélection ≠ Evidence.`);
  }

  function renderResults(payload) {
    const host = $("v2-context-results");
    host.replaceChildren();
    if (payload.reason === "namespace_required") {
      setMessage("Commencez par _ pour une Affaire, @ pour une Personne ou * pour la recherche globale.");
      return;
    }
    if (payload.provider_errors?.length) {
      setMessage(`${payload.provider_errors.length} provider(s) indisponible(s) ; les résultats sains restent affichés.`);
    } else if (!payload.results.length) {
      setMessage("Aucun résultat dans le périmètre autorisé.");
    } else {
      setMessage(`${payload.results.length} résultat(s) candidat(s). Aucun n’est sélectionné automatiquement.`);
    }

    for (const item of payload.results) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "v2-context-result";
      if (!item.entity_id) button.disabled = true;

      const copy = document.createElement("span");
      copy.className = "v2-context-result-copy";
      const title = document.createElement("strong");
      title.textContent = item.label;
      const secondary = document.createElement("span");
      secondary.textContent = [item.secondary_label, sourceLabel(item)].filter(Boolean).join(" · ");
      copy.append(title, secondary);

      const reason = document.createElement("span");
      reason.className = "v2-context-match";
      reason.textContent = item.matched_field ? `${item.matched_field} · ${item.match_reason}` : "candidat";

      button.append(copy, reason);
      button.addEventListener("click", () => selectResult(item));
      host.append(button);
    }
  }

  async function search(raw, generation) {
    try {
      const payload = await window.PantheonContextResolver.resolve(raw, { limit: 10 });
      if (generation !== searchGeneration) return;
      renderResults(payload);
    } catch (error) {
      if (generation !== searchGeneration) return;
      $("v2-context-results").replaceChildren();
      setMessage(`Recherche refusée : ${error.message}`);
    }
  }

  function scheduleSearch() {
    const raw = $("v2-context-input").value.trim();
    clearTimeout(searchTimer);
    searchGeneration += 1;
    const generation = searchGeneration;
    if (!raw) {
      $("v2-context-results").replaceChildren();
      setMessage("Utilisez _Affaire, @Personne ou *recherche globale.");
      return;
    }
    setMessage("Recherche…");
    searchTimer = setTimeout(() => void search(raw, generation), 180);
  }

  $("v2-context-input")?.addEventListener("input", scheduleSearch);
  renderSelected();
})();
