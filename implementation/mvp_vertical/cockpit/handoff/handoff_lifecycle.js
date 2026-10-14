(() => {
  "use strict";

  const $ = id => document.getElementById(id);
  const ACTIVE_ADMISSION_KEY = "pantheon-active-hermes-admission";
  let selectedContext = [];
  let prepared = null;
  let submitted = null;
  let admitted = null;
  let lastAdmission = null;
  let generation = 0;

  const token = () => $("v2-token")?.value || "";
  const actor = () => $("v2-handoff-actor")?.value.trim() || "";
  const ttlSeconds = () => Number($("v2-handoff-ttl")?.value || 0);
  const revokeReason = () => $("v2-handoff-revoke-reason")?.value.trim() || "";
  const includeDescendants = () => Boolean($("v2-handoff-descendants")?.checked);
  const key = prefix => `${prefix}-${globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`}`;

  function currentCard() {
    const card = document.querySelector("#v2-stage .v2-card");
    if (!card) return null;
    const entity_id = card.querySelector(".v2-entity-id")?.textContent?.trim();
    const kicker = card.querySelector(".v2-card-back .v2-card-kicker")?.textContent || "";
    const entity_type = kicker.split("·").map(x => x.trim()).filter(Boolean).at(-1) || "";
    const label = card.querySelector(".v2-card-title")?.textContent?.trim() || entity_id;
    return entity_id && entity_type ? { entity_id, entity_type, label } : null;
  }

  function baseRequest() {
    const root = currentCard();
    if (!root) throw new Error("Aucune carte courante avec identité stable");
    return {
      question: $("v2-handoff-question").value.trim(),
      card_context_envelope: {
        root_entity: { entity_id: root.entity_id, entity_type: root.entity_type },
        descendants: [], source_refs: [], explicit_additions: [], explicit_exclusions: [],
        scope_widened_implicitly: false,
      },
      selected_context: selectedContext.map(({ entity_id, entity_type }) => ({ entity_id, entity_type })),
      include_declared_descendants: includeDescendants(),
    };
  }

  function scopeLabel() {
    const root = currentCard();
    $("v2-handoff-scope").textContent = root
      ? `${root.label}${includeDescendants() ? " + descendants déclarés" : ""} + ${selectedContext.length} ajout(s)`
      : "Aucune carte courante";
  }

  function buttons() {
    const human = actor();
    $("v2-handoff-submit").disabled = !prepared || !human || Boolean(submitted);
    $("v2-handoff-admit").disabled = !submitted || !human || !ttlSeconds() || Boolean(admitted);
    $("v2-handoff-revoke").disabled = !lastAdmission || lastAdmission.admission_state !== "admitted" || !human || revokeReason().length < 3;
  }

  function rows(host, values) {
    const dl = document.createElement("dl"); dl.className = "v2-handoff-refs";
    values.forEach(([name, value]) => {
      const dt = document.createElement("dt"); dt.textContent = name;
      const dd = document.createElement("dd"); dd.textContent = String(value ?? "—");
      dl.append(dt, dd);
    });
    host.append(dl);
  }

  function renderPrepared(payload) {
    const host = $("v2-handoff-preview"); host.replaceChildren();
    const h = document.createElement("strong"); h.textContent = "Handoff candidate"; host.append(h);
    rows(host, [
      ["Task Contract", payload.task_contract?.task_contract_ref],
      ["Context Pack", payload.context_pack?.context_pack_ref],
      ["Scope", payload.scope_resolution?.policy || "root_only"],
      ["Entités", payload.context_pack?.included_entities?.length ?? 0],
      ["Sources", payload.context_pack?.source_refs?.length ?? 0],
    ]);
    const p = document.createElement("p"); p.className = "v2-handoff-warning";
    p.textContent = "Candidate uniquement : aucune admission et aucun HermesRun."; host.append(p);
  }

  function renderSubmission(payload) {
    const s = document.createElement("section"); s.className = "v2-handoff-receipt";
    const h = document.createElement("strong"); h.textContent = "Work Issue créé"; s.append(h);
    rows(s, [["Work Issue", payload.work_issue?.issue_id], ["Assigné à", payload.work_issue?.assigned_to], ["HermesRun", "aucun"]]);
    $("v2-handoff-preview").append(s);
  }

  function renderAdmission(payload, title = "Admission créée", replace = false) {
    const host = $("v2-handoff-preview");
    if (replace) host.replaceChildren();
    const s = document.createElement("section"); s.className = "v2-handoff-receipt v2-handoff-receipt--admission";
    const h = document.createElement("strong"); h.textContent = title; s.append(h);
    rows(s, [
      ["Admission", payload.admission_id], ["État", payload.admission_state],
      ["Version Work Issue", payload.work_issue_version], ["Expire", payload.expires_at],
      ["Prêt Hermes", payload.ready_for_external_runtime ? "oui" : "non"],
      ["Run", payload.consumed_by_run_id || "aucun"], ["Révocation", payload.revocation_reason || "—"],
    ]);
    const p = document.createElement("p"); p.className = "v2-handoff-warning";
    p.textContent = "Pantheon n’a rien dispatché. L’expiration est vérifiée à la demande, sans scheduler."; s.append(p);
    host.append(s);
  }

  function publishAdmission(payload) {
    document.dispatchEvent(new CustomEvent("pantheon:hermes-admission", {
      detail: { admission: payload || null },
    }));
  }

  async function post(url, body, humanActor = false) {
    const headers = { Authorization: `Bearer ${token()}`, "Content-Type": "application/json" };
    if (humanActor) headers["X-Pantheon-Human-Actor"] = actor();
    const response = await fetch(url, { method: "POST", headers, body: JSON.stringify(body) });
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    if (!response.ok) throw new Error(payload.detail || response.statusText);
    return payload;
  }

  async function refreshLastAdmission({ render = true } = {}) {
    const admissionId = sessionStorage.getItem(ACTIVE_ADMISSION_KEY);
    if (!admissionId || !token()) return;
    try {
      const response = await fetch(`../cockpit/hermes-execution-admissions/${encodeURIComponent(admissionId)}`, {
        headers: { Authorization: `Bearer ${token()}` },
      });
      const payload = await response.json().catch(() => ({ detail: response.statusText }));
      if (!response.ok) throw new Error(payload.detail || response.statusText);
      lastAdmission = payload;
      if (render) renderAdmission(payload, "Dernière admission", true);
      publishAdmission(payload);
      buttons();
    } catch (e) {
      $("v2-handoff-message").textContent = `Admission mémorisée non relue : ${e.message}`;
    }
  }

  async function prepare() {
    if ($("v2-handoff-question").value.trim().length < 3 || !token()) return;
    const mine = ++generation;
    prepared = submitted = admitted = null; buttons();
    $("v2-handoff-message").textContent = "Préparation…";
    try {
      const req = baseRequest();
      const payload = await post("../cockpit/hermes-handoffs/preview", req);
      if (mine !== generation) return;
      prepared = { req, payload, submitKey: key("handoff-submit") };
      renderPrepared(payload);
      $("v2-handoff-message").textContent = "Portée préparée.";
    } catch (e) { $("v2-handoff-message").textContent = `Préparation refusée : ${e.message}`; }
    buttons();
  }

  async function submit() {
    if (!prepared || !actor()) return;
    try {
      const p = prepared.payload;
      const payload = await post("../cockpit/hermes-handoffs/submit", {
        ...prepared.req, expected_preview_digest: p.preview_digest,
        expected_task_contract_ref: p.task_contract.task_contract_ref,
        expected_context_pack_ref: p.context_pack.context_pack_ref,
        idempotency_key: prepared.submitKey,
      }, true);
      submitted = { payload, admissionKey: key("execution-admit") };
      renderSubmission(payload);
      sessionStorage.setItem("pantheon-human-actor", actor());
      $("v2-handoff-message").textContent = "Work Issue créé. Aucun HermesRun.";
    } catch (e) { $("v2-handoff-message").textContent = `Création refusée : ${e.message}`; }
    buttons();
  }

  async function admit() {
    if (!submitted || !actor() || !ttlSeconds()) return;
    try {
      const payload = await post(`../cockpit/hermes-handoffs/${encodeURIComponent(submitted.payload.handoff_id)}/admissions`, {
        ttl_seconds: ttlSeconds(), idempotency_key: submitted.admissionKey,
      }, true);
      admitted = payload;
      lastAdmission = payload;
      sessionStorage.setItem(ACTIVE_ADMISSION_KEY, payload.admission_id);
      renderAdmission(payload);
      publishAdmission(payload);
      $("v2-handoff-message").textContent = "Admission bornée créée. Pantheon n’a pas lancé Hermes.";
    } catch (e) { $("v2-handoff-message").textContent = `Admission refusée : ${e.message}`; }
    buttons();
  }

  async function revoke() {
    if (!lastAdmission || lastAdmission.admission_state !== "admitted" || revokeReason().length < 3) return;
    try {
      const payload = await post(`../cockpit/hermes-execution-admissions/${encodeURIComponent(lastAdmission.admission_id)}/revocations`, {
        reason: revokeReason(), idempotency_key: key("admission-revoke"),
      }, true);
      lastAdmission = payload;
      if (admitted?.admission_id === payload.admission_id) admitted = payload;
      renderAdmission(payload, "Admission révoquée", true);
      publishAdmission(payload);
      $("v2-handoff-message").textContent = "Admission révoquée avant consommation.";
    } catch (e) { $("v2-handoff-message").textContent = `Révocation refusée : ${e.message}`; }
    buttons();
  }

  function invalidate(message) {
    generation += 1; prepared = submitted = admitted = null;
    $("v2-handoff-preview")?.replaceChildren();
    if (lastAdmission) renderAdmission(lastAdmission, "Dernière admission", false);
    if (message) $("v2-handoff-message").textContent = message;
    scopeLabel(); buttons();
  }

  document.addEventListener("pantheon:v2-context-changed", e => {
    selectedContext = Array.isArray(e.detail?.selected) ? e.detail.selected : [];
    invalidate("Contexte modifié : le brouillon est effacé, l’admission existante reste traçable.");
  });
  new MutationObserver(() => invalidate("Carte modifiée : le brouillon est effacé, l’admission existante reste traçable.")).observe($("v2-stage"), { childList: true });

  $("v2-handoff-prepare")?.addEventListener("click", () => void prepare());
  $("v2-handoff-submit")?.addEventListener("click", () => void submit());
  $("v2-handoff-admit")?.addEventListener("click", () => void admit());
  $("v2-handoff-revoke")?.addEventListener("click", () => void revoke());
  $("v2-handoff-question")?.addEventListener("input", () => invalidate("Question modifiée : préparez à nouveau."));
  $("v2-handoff-descendants")?.addEventListener("change", () => invalidate("Scope modifié : préparez à nouveau."));
  ["v2-handoff-actor", "v2-handoff-ttl", "v2-handoff-revoke-reason"].forEach(id => $(id)?.addEventListener("input", buttons));
  $("v2-token")?.addEventListener("change", () => void refreshLastAdmission());
  document.addEventListener("pantheon:hermes-dock-open", () => void refreshLastAdmission({ render: false }));

  const remembered = sessionStorage.getItem("pantheon-human-actor");
  if (remembered && $("v2-handoff-actor")) $("v2-handoff-actor").value = remembered;
  scopeLabel(); buttons();
  void refreshLastAdmission();
})();
