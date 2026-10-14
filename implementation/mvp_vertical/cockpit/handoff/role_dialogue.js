(() => {
  "use strict";

  const ACTIVE_ADMISSION_KEY = "pantheon-active-hermes-admission";
  const ROLE_ICONS = Object.freeze({
    Athena: "🦉", Argos: "🔎", Themis: "⚖", Apollo: "☀",
    Hephaistos: "🛠", Iris: "📨", Zeus: "⚡", Mnemosyne: "🧠", Hermes: "⚙",
  });
  const ROLE_ORDER = Object.freeze([
    "Athena", "Argos", "Hermes", "Hephaistos", "Themis", "Apollo", "Zeus", "Iris", "Mnemosyne",
  ]);
  const DETAIL_LABELS = Object.freeze({
    action: "Action", raison: "Raison", but: "But", sources: "Sources",
    method: "Méthode", skill: "Skill", outil: "Outil", result: "Résultat",
    limite: "Limite", next_action: "Prochaine action", gate: "Gate", handoff: "Relais",
  });

  const $ = id => document.getElementById(id);
  const token = () => $("v2-token")?.value || "";
  const dockOpen = () => !$("v2-hermes-dock")?.hidden;
  let currentRun = "";
  let lastCursor = 0;
  let streamController = null;
  let admissionTimer = null;
  let reconnectTimer = null;
  let reconnects = 0;
  let observationCounter = 0;
  let activeView = "dialogue";
  let selectedStageId = "";
  const stages = new Map();
  const stageEvents = new Map();
  const observedOrder = new Map();

  function setState(message) {
    const node = $("v2-role-dialogue-state");
    if (node) node.textContent = message;
  }

  function stop() {
    streamController?.abort();
    streamController = null;
    window.clearTimeout(admissionTimer);
    window.clearTimeout(reconnectTimer);
    admissionTimer = reconnectTimer = null;
  }

  function resetGraph() {
    $("v2-role-graph-lanes")?.replaceChildren();
    $("v2-role-graph-detail")?.replaceChildren();
  }

  function resetForRun(runId) {
    if (runId === currentRun) return;
    stop();
    currentRun = runId;
    lastCursor = 0;
    reconnects = 0;
    observationCounter = 0;
    selectedStageId = "";
    stages.clear();
    stageEvents.clear();
    observedOrder.clear();
    $("v2-role-dialogue-events")?.replaceChildren();
    resetGraph();
    window.PantheonRuntimeTopology?.reset?.(runId);
  }

  function stageDetails(host, values) {
    const entries = Object.entries(values || {}).filter(([, value]) => value != null && value !== "");
    if (!entries.length) return;
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = "Détails observables";
    const list = document.createElement("dl");
    for (const [key, value] of entries) {
      const dt = document.createElement("dt");
      const dd = document.createElement("dd");
      dt.textContent = DETAIL_LABELS[key] || key.replaceAll("_", " ");
      dd.textContent = String(value);
      list.append(dt, dd);
    }
    details.append(summary, list);
    host.append(details);
  }

  function stageSort(left, right) {
    const leftSequence = Number(left?.sequence);
    const rightSequence = Number(right?.sequence);
    const leftHasSequence = Number.isSafeInteger(leftSequence);
    const rightHasSequence = Number.isSafeInteger(rightSequence);
    if (leftHasSequence && rightHasSequence && leftSequence !== rightSequence) return leftSequence - rightSequence;
    return (observedOrder.get(left.stage_id) ?? 0) - (observedOrder.get(right.stage_id) ?? 0);
  }

  function orderedStages() {
    return [...stageEvents.values()].sort(stageSort);
  }

  function roleOrder(events) {
    const present = new Set(events.map(event => event.visible_role));
    const canonical = ROLE_ORDER.filter(role => present.has(role));
    const extras = [...present].filter(role => !ROLE_ORDER.includes(role));
    return [...canonical, ...extras];
  }

  function renderGraphDetail(event) {
    const host = $("v2-role-graph-detail");
    if (!host) return;
    host.replaceChildren();
    if (!event) {
      const empty = document.createElement("p");
      empty.className = "v2-role-graph-detail-empty";
      empty.textContent = "Sélectionnez un jalon pour afficher ses détails observables.";
      host.append(empty);
      return;
    }

    const head = document.createElement("div");
    head.className = "v2-role-graph-detail-head";
    const title = document.createElement("strong");
    title.textContent = `${event.visible_role} — ${event.semantic_function || event.role_family || "Jalon"}`;
    const status = document.createElement("span");
    status.textContent = event.phase === "completed" ? "terminé" : "en cours";
    head.append(title, status);

    const summary = document.createElement("p");
    summary.className = "v2-role-graph-detail-summary";
    summary.textContent = event.summary || "Jalon public observé.";
    const origin = document.createElement("p");
    origin.className = "v2-role-graph-detail-origin";
    origin.textContent = event.projection === "derived_transient"
      ? "Projection transitoire dérivée du flux public Hermes."
      : "Événement structuré émis par le runtime.";
    host.append(head, summary, origin);
    stageDetails(host, event.details);
  }

  function renderGraph() {
    const host = $("v2-role-graph-lanes");
    if (!host) return;
    const events = orderedStages();
    host.replaceChildren();
    if (!events.length) {
      const empty = document.createElement("p");
      empty.className = "v2-role-graph-empty";
      empty.textContent = "Aucun jalon observable pour cette exécution.";
      host.append(empty);
      renderGraphDetail(null);
      return;
    }

    const stageColumns = new Map(events.map((event, index) => [event.stage_id, index + 1]));
    for (const role of roleOrder(events)) {
      const lane = document.createElement("div");
      lane.className = "v2-role-graph-lane";
      const label = document.createElement("div");
      label.className = "v2-role-graph-label";
      const icon = document.createElement("span");
      icon.setAttribute("aria-hidden", "true");
      icon.textContent = ROLE_ICONS[role] || "•";
      const name = document.createElement("strong");
      name.textContent = role;
      label.append(icon, name);

      const rail = document.createElement("div");
      rail.className = "v2-role-graph-rail";
      rail.style.gridTemplateColumns = `repeat(${events.length}, 3.1rem)`;
      for (const event of events.filter(candidate => candidate.visible_role === role)) {
        const node = document.createElement("button");
        node.type = "button";
        node.className = "v2-role-graph-node";
        node.style.gridColumn = String(stageColumns.get(event.stage_id));
        node.dataset.phase = event.phase || "updated";
        node.dataset.projection = event.projection || "native";
        node.classList.toggle("is-selected", event.stage_id === selectedStageId);
        node.textContent = ROLE_ICONS[role] || "•";
        node.title = event.summary || `${role} — jalon observable`;
        node.setAttribute(
          "aria-label",
          `${role}, ${event.semantic_function || event.role_family || "jalon"}, ${event.summary || "jalon public observé"}`,
        );
        node.addEventListener("click", () => {
          selectedStageId = event.stage_id;
          renderGraph();
        });
        rail.append(node);
      }
      lane.append(label, rail);
      host.append(lane);
    }

    if (selectedStageId && !stageEvents.has(selectedStageId)) selectedStageId = "";
    renderGraphDetail(selectedStageId ? stageEvents.get(selectedStageId) : null);
  }

  function setView(view) {
    activeView = view === "graph" ? "graph" : "dialogue";
    const dialogue = $("v2-role-dialogue-events");
    const graph = $("v2-role-graph");
    if (dialogue) dialogue.hidden = activeView !== "dialogue";
    if (graph) graph.hidden = activeView !== "graph";
    for (const button of document.querySelectorAll("[data-role-trace-view]")) {
      const selected = button.dataset.roleTraceView === activeView;
      button.setAttribute("aria-selected", String(selected));
      button.tabIndex = selected ? 0 : -1;
    }
    if (activeView === "graph") renderGraph();
  }

  function renderStage(event) {
    if (!event?.stage_id || !event?.visible_role) return;
    if (!observedOrder.has(event.stage_id)) observedOrder.set(event.stage_id, observationCounter++);
    stageEvents.set(event.stage_id, { ...event });

    let item = stages.get(event.stage_id);
    if (!item) {
      item = document.createElement("li");
      item.className = "v2-role-stage";
      stages.set(event.stage_id, item);
      $("v2-role-dialogue-events")?.append(item);
    }
    const completed = event.phase === "completed";
    item.classList.toggle("is-running", !completed);
    item.replaceChildren();

    const icon = document.createElement("span");
    icon.className = "v2-role-stage-icon";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = ROLE_ICONS[event.visible_role] || "•";
    const title = document.createElement("strong");
    title.className = "v2-role-stage-title";
    title.textContent = `${event.visible_role} — ${event.semantic_function || event.role_family || "Jalon"}`;
    const status = document.createElement("span");
    status.className = "v2-role-stage-status";
    status.textContent = completed ? "terminé" : "en cours";
    const summary = document.createElement("p");
    summary.className = "v2-role-stage-summary";
    summary.textContent = event.summary || "Jalon public observé.";
    const origin = document.createElement("span");
    origin.className = "v2-role-stage-origin";
    origin.textContent = event.projection === "derived_transient" ? "dérivé" : "natif";
    origin.title = event.projection === "derived_transient"
      ? "Projection transitoire dérivée du flux public Hermes"
      : "Événement structuré émis par le runtime";
    item.append(icon, title, status, origin, summary);
    stageDetails(item, event.details);
    if (activeView === "graph") renderGraph();
  }

  function consumeBlock(block) {
    let kind = "message";
    let id = null;
    const data = [];
    for (const line of block.split("\n")) {
      if (line.startsWith("event:")) kind = line.slice(6).trim();
      else if (line.startsWith("id:")) id = Number(line.slice(3).trim());
      else if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
    }
    if (!data.length) return;
    const payload = JSON.parse(data.join("\n"));
    if (Number.isSafeInteger(id) && id > lastCursor) lastCursor = id;
    if (kind === "role.stage") renderStage(payload);
    else if (kind === "runtime.subagent") window.PantheonRuntimeTopology?.consume?.(payload);
    else if (kind === "role.trace.error") setState("Rejeu incomplet");
  }

  async function traceStatus(runId) {
    const response = await fetch(`../cockpit/role-traces/${encodeURIComponent(runId)}`, {
      headers: { Authorization: `Bearer ${token()}` }, cache: "no-store",
    });
    if (!response.ok) return null;
    return response.json();
  }

  function retryStream(runId) {
    if (!dockOpen() || runId !== currentRun || reconnects >= 5) return;
    reconnects += 1;
    reconnectTimer = window.setTimeout(() => void connect(runId), Math.min(1000 * reconnects, 5000));
  }

  async function connect(runId) {
    if (!runId || !token() || !dockOpen()) return;
    resetForRun(runId);
    streamController?.abort();
    streamController = new AbortController();
    setState(lastCursor ? "Reconnexion…" : "Connexion…");
    try {
      const headers = { Authorization: `Bearer ${token()}` };
      if (lastCursor) headers["Last-Event-ID"] = String(lastCursor);
      const response = await fetch(`../cockpit/role-traces/${encodeURIComponent(runId)}/events`, {
        headers, cache: "no-store", signal: streamController.signal,
      });
      if (!response.ok || !response.body) {
        setState(response.status === 404 ? "Trace en attente" : "Trace indisponible");
        retryStream(runId);
        return;
      }
      reconnects = 0;
      setState("En direct");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done }).replaceAll("\r\n", "\n");
        let boundary;
        while ((boundary = buffer.indexOf("\n\n")) >= 0) {
          const block = buffer.slice(0, boundary);
          buffer = buffer.slice(boundary + 2);
          if (block.trim()) consumeBlock(block);
        }
        if (done) break;
      }
      const status = await traceStatus(runId);
      setState(status?.diagnostic ? "Trace incomplète" : status?.terminal ? "Terminé" : "Interrompu");
      if (!status?.terminal) retryStream(runId);
    } catch (error) {
      if (error?.name !== "AbortError") {
        setState("Connexion interrompue");
        retryStream(runId);
      }
    }
  }

  function scheduleAdmissionRead(delay = 3000) {
    window.clearTimeout(admissionTimer);
    if (!dockOpen() || currentRun) return;
    admissionTimer = window.setTimeout(() => void readActiveAdmission(), delay);
  }

  async function readActiveAdmission() {
    const admissionId = sessionStorage.getItem(ACTIVE_ADMISSION_KEY);
    if (!admissionId || !token() || !dockOpen()) {
      setState("Aucune exécution");
      return;
    }
    try {
      const response = await fetch(`../cockpit/hermes-execution-admissions/${encodeURIComponent(admissionId)}`, {
        headers: { Authorization: `Bearer ${token()}` }, cache: "no-store",
      });
      const admission = await response.json();
      if (!response.ok) throw new Error(admission.detail || response.statusText);
      const runId = String(admission.consumed_by_run_id || "");
      if (runId) void connect(runId);
      else {
        resetForRun("");
        setState(admission.admission_state === "admitted" ? "En attente d’Hermes" : "Aucune exécution");
        scheduleAdmissionRead();
      }
    } catch (_error) {
      setState("Admission indisponible");
      scheduleAdmissionRead(5000);
    }
  }

  document.addEventListener("pantheon:hermes-admission", event => {
    const runId = String(event.detail?.admission?.consumed_by_run_id || "");
    if (runId) void connect(runId);
    else {
      resetForRun("");
      scheduleAdmissionRead();
    }
  });
  document.addEventListener("pantheon:hermes-dock-open", () => void readActiveAdmission());
  document.addEventListener("pantheon:hermes-dock-close", stop);
  $("v2-token")?.addEventListener("change", () => {
    resetForRun("");
    if (dockOpen()) void readActiveAdmission();
  });
  for (const button of document.querySelectorAll("[data-role-trace-view]")) {
    button.addEventListener("click", () => setView(button.dataset.roleTraceView));
  }
  setView("dialogue");
})();
