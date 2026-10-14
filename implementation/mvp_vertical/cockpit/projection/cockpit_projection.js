(() => {
  "use strict";

  const $ = id => document.getElementById(id);
  const dataLoader = window.PantheonCockpitDataLoader.create();
  const navigationProjection = window.PantheonNavigationProjection;
  const childAssembler = window.PantheonChildCollectionAssembler;
  if (!navigationProjection) throw new Error("Navigation projection unavailable");
  if (!childAssembler?.assemble) throw new Error("Child collection assembler unavailable");

  const CONTACT_GROUPS = [
    "Maîtrise d’ouvrage",
    "Équipe de maîtrise d’œuvre",
    "Bureaux d’études",
    "Bureau de contrôle",
    "SSI",
    "Entreprises de travaux",
    "Autres intervenants",
  ];
  const STATUS_LABELS = {
    draft: "Brouillon", in_progress: "En rédaction", acted: "Acté", superseded: "Archivé",
    review: "À valider", needs_review: "À valider", pending_review: "À valider",
    generated_unreviewed: "Non revu", ready: "Prêt", reviewed: "Revu", active: "Actif",
    waiting: "En attente", running: "En cours", done: "Terminé", conflict: "Conflit",
    failed: "Échec", stale: "Obsolète", rejected: "Refusé", applied: "Appliqué",
    neutral: "Référence", open: "À faire", partial: "Partiel", candidate: "Candidat",
    watch: "À observer", unreviewed: "Non revu", not_activated: "Non activé",
  };
  const PROJECT_ACCENTS = ["#244f7b", "#6a4a77", "#356753", "#805a2c", "#76504a", "#4d5f87"];
  const WORK_ACTIVITY_SCHEMA = Object.freeze({ id: "cockpit.work_activity", revision: 1 });
  const NOT_OBSERVED = "not_observed";

  const state = {
    project: "", token: "", projects: [], projectSchema: null, information: [],
    legacyDocuments: [], knowledge: [], workIssues: [], changeCandidates: [],
    currentRuns: [], toolCatalog: [], cards: new Map(), children: new Map(),
    flipped: new Set(), navigator: null, lastMove: "none",
  };

  const text = (value, fallback = "") => value == null || value === "" ? fallback : String(value);
  const slug = value => String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  const statusLabel = value => STATUS_LABELS[value] || String(value || "À vérifier").replaceAll("_", " ");

  function stableAccent(value) {
    const input = String(value || "project");
    let hash = 0;
    for (let index = 0; index < input.length; index += 1) hash = ((hash << 5) - hash + input.charCodeAt(index)) | 0;
    return PROJECT_ACCENTS[Math.abs(hash) % PROJECT_ACCENTS.length];
  }

  function card(input) {
    const projection = window.PantheonStructuredInterface?.buildCardProjection?.(input) || {};
    return {
      role: "entity", family: "information", status: "neutral", summary: "", type_tags: [],
      subject_tags: [], limits: [], available_actions: [], back: [], ...input, ...projection,
      presentation_family: projection.presentation_family || input.presentation_family || input.family,
    };
  }

  function putCard(model) {
    state.cards.set(model.entity_id, model);
    return model.entity_id;
  }

  function setChildren(parentId, ids) {
    state.children.set(parentId, [...ids].filter(Boolean));
  }

  function rootCards() {
    return navigationProjection.rootItemIds.map(entityId => card({
      entity_id: entityId,
      entity_type: "cockpit_space",
    }));
  }

  function projectEntityId(item) {
    return `project:${item.project_id || item.entity_id || item.code || item.display_name}`;
  }

  function formattedValue(field, value) {
    if (value == null || value === "") return "Non renseigné";
    if (Array.isArray(value)) return value.join(" · ");
    if (field?.unit === "EUR" && typeof value === "number") return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(value);
    if (field?.unit === "m2" && typeof value === "number") return `${new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 2 }).format(value)} m²`;
    return String(value);
  }

  function projectSchemaRows(item) {
    if (!state.projectSchema) {
      return Object.entries(item.attributes || {})
        .filter(([, value]) => value !== null && value !== "" && !(Array.isArray(value) && !value.length))
        .map(([key, value]) => [key.replaceAll("_", " "), Array.isArray(value) ? value.join(" · ") : String(value)]);
    }
    const rows = [];
    for (const field of state.projectSchema.fields || []) {
      if (field.presentation?.hidden === true || field.storage === "system") continue;
      const value = field.storage === "attributes"
        ? item.attributes?.[field.key]
        : field.storage === "projection"
          ? item.claim_values?.[field.key]
          : item[field.key];
      if (value == null || value === "" || (Array.isArray(value) && !value.length)) continue;
      rows.push([field.title || field.label || field.key, formattedValue(field, value)]);
    }
    return rows;
  }

  function informationTimestamp(item) {
    return String(item.information_date || item.acted_at || item.updated_at || item.created_at || "");
  }

  function newestInformation(items) {
    return [...items].sort((left, right) => informationTimestamp(right).localeCompare(informationTimestamp(left)));
  }

  function informationContextLine(item) {
    const identity = [item.information_date || null, item.author || null, item.title || null].filter(Boolean).join(" · ");
    return [identity, item.summary].filter(Boolean).join("\n");
  }

  function workData(projection) {
    return projection.work_issue || projection;
  }

  function workActivity(projection) {
    const activity = projection?.work_activity;
    if (!activity) return null;
    if (activity.schema?.id !== WORK_ACTIVITY_SCHEMA.id || activity.schema?.revision !== WORK_ACTIVITY_SCHEMA.revision) {
      return { invalid: true, reason: "Projection d’activité incompatible." };
    }
    if (!activity.issue || !Array.isArray(activity.activity) || !Array.isArray(activity.trace_refs)) {
      return { invalid: true, reason: "Projection d’activité incomplète." };
    }
    if (activity.execution_trace_summary != null && (typeof activity.execution_trace_summary !== "object" || Array.isArray(activity.execution_trace_summary))) {
      return { invalid: true, reason: "Résumé d’exécution technique incompatible." };
    }
    return activity;
  }

  function activityEventLine(item) {
    const identity = [item.occurred_at, item.label].filter(Boolean).join(" — ");
    return [identity, item.detail].filter(Boolean).join(" — ");
  }

  function technicalExecutionRows(summary) {
    if (!summary || typeof summary !== "object" || Array.isArray(summary)) return [];
    const execution = summary.execution && typeof summary.execution === "object" ? summary.execution : {};
    const runtime = summary.runtime && typeof summary.runtime === "object" ? summary.runtime : {};
    const correlation = summary.correlation && typeof summary.correlation === "object" ? summary.correlation : {};
    const limits = summary.limits && typeof summary.limits === "object" ? summary.limits : {};
    const provenance = summary.provenance && typeof summary.provenance === "object" ? summary.provenance : {};
    const rows = [];

    const compact = [
      execution.terminal_status ? `terminal=${execution.terminal_status}` : null,
      Number.isInteger(execution.step_count) ? `steps=${execution.step_count}` : null,
      Number.isInteger(execution.tool_call_count) ? `tool_calls=${execution.tool_call_count}` : null,
      Number.isInteger(execution.retry_count) ? `retries=${execution.retry_count}` : null,
      Number.isInteger(execution.repair_count) ? `repairs=${execution.repair_count}` : null,
    ].filter(Boolean);
    rows.push(["Exécution technique", compact.join(" · ") || "Résumé technique enregistré."]);

    const runtimeLine = [runtime.implementation, runtime.version, runtime.profile].filter(Boolean).join(" · ");
    if (runtimeLine) rows.push(["Runtime observé", runtimeLine]);

    const correlationLines = [
      ["admission_id", correlation.admission_id],
      ["launch_reservation_id", correlation.launch_reservation_id],
      ["snapshot_id", correlation.snapshot_id],
      ["snapshot_digest", correlation.snapshot_digest],
      ["run_id", correlation.run_id],
    ].filter(([, value]) => value).map(([key, value]) => `${key}=${value}`);
    if (correlationLines.length) rows.push(["Corrélation technique", correlationLines.join("\n")]);

    const tools = Array.isArray(summary.tools) ? summary.tools : [];
    if (tools.length) {
      rows.push(["Outils observés", tools.map(item => [item.tool_id, Number.isInteger(item.call_count) ? `×${item.call_count}` : null, item.terminal_status].filter(Boolean).join(" · ")).join("\n")]);
    }

    const limitLine = Object.entries(limits).map(([key, value]) => `${key}=${value}`).join(" · ");
    if (limitLine) rows.push(["Limites techniques", limitLine]);

    const refusals = Array.isArray(summary.refusals) ? summary.refusals : [];
    if (refusals.length) {
      rows.push(["Refus techniques", refusals.map(item => `${item.code}${Number.isInteger(item.count) ? ` ×${item.count}` : ""}`).join("\n")]);
    }

    const provenanceLine = [
      ["Pantheon observé", provenance.pantheon_observed],
      ["Binding observé", provenance.binding_observed],
      ["Runtime rapporté", provenance.runtime_reported],
    ].filter(([, values]) => Array.isArray(values)).map(([label, values]) => `${label}: ${values.length}`).join(" · ");
    if (provenanceLine) rows.push(["Provenance technique", provenanceLine]);

    rows.push(["Portée", "Information technique uniquement · succès runtime ≠ Evidence · Decision · Knowledge · résolution du Work Issue."]);
    return rows;
  }

  function projectContextRows() {
    const information = newestInformation(state.information);
    const working = information.find(item => ["draft", "in_progress"].includes(item.status));
    const acted = information.find(item => item.status === "acted");
    const sensitive = information.find(item => {
      const vocabulary = [item.category, ...(item.subject_tags || [])].map(slug);
      return vocabulary.some(value => ["assurance", "sinistre", "responsabilite", "reserve", "reservations", "reprise", "reprises"].includes(value));
    });
    const activeWork = state.workIssues.map(workData)
      .filter(item => ["open", "in_progress", "waiting", "review", "needs_review"].includes(item.status));
    const pendingCandidates = state.changeCandidates.filter(item => item.status === "pending_review");
    const reviewWork = activeWork.filter(item => ["review", "needs_review"].includes(item.status));
    const rows = [];
    if (working) rows.push(["Situation en cours", `${statusLabel(working.status)}\n${informationContextLine(working)}`]);
    else if (acted) rows.push(["Situation actuelle", informationContextLine(acted)]);
    if (acted && acted !== working) rows.push(["Dernière base ACTÉE", informationContextLine(acted)]);
    if (sensitive && sensitive !== working && sensitive !== acted) rows.push(["Dossier sensible", informationContextLine(sensitive)]);
    if (activeWork.length) {
      rows.push(["Suites à donner", activeWork.slice(0, 3).map(item => {
        const responsibility = (item.responsibilities || []).join(" · ");
        const identity = [statusLabel(item.status), item.title, responsibility].filter(Boolean).join(" · ");
        return [identity, item.description].filter(Boolean).join(" — ");
      }).join("\n")]);
    }
    const reviewCount = reviewWork.length + pendingCandidates.length;
    if (reviewCount) rows.push(["Revue humaine", `${reviewCount} proposition(s) ou travail(aux) attendent une validation humaine.`]);
    return rows;
  }

  function normalizeProject(item, { selected = false } = {}) {
    const projectId = item.project_id || item.entity_id || item.code || item.display_name;
    const title = item.display_name || item.code || projectId || "Affaire";
    const contactCount = Array.isArray(item.contacts) ? item.contacts.length : 0;
    const informationCount = state.information.length + state.legacyDocuments.length;
    return card({
      entity_id: projectEntityId(item), entity_type: "project", family: "project", presentation_family: "project",
      category: "Projet", title,
      summary: selected ? `${informationCount} information(s) · ${contactCount} contact(s) · ${state.workIssues.length} travail(aux)` : [item.code && item.code !== title ? item.code : null, item.phase, item.location].filter(Boolean).join(" · ") || "Affaire Agency Data",
      status: item.status || "active", subject_tags: Array.isArray(item.tags) ? item.tags : [],
      identity_accent: stableAccent(projectId), index: item.display_index || item.index || null,
      date: item.updated_at || null, front: { issuer: item.primary_client || null },
      back: selected ? [...projectContextRows(), ...projectSchemaRows(item)] : projectSchemaRows(item),
      source_project_id: String(projectId || ""),
    });
  }

  function normalizeInformation(item) {
    return card({
      entity_id: `information:${item.information_id}`, entity_type: "information", family: "information",
      presentation_family: "information", category: item.category || "Information", title: item.title || "Information",
      summary: item.summary || "Résumé non renseigné", status: item.status || "draft", index: item.index_label || null,
      date: item.information_date || item.updated_at || null, author: item.author || null,
      type_tags: item.type_tags || [], subject_tags: item.subject_tags || [], limits: item.limits || [],
      available_actions: item.status === "acted" ? ["Nouvelle version"] : ["Modifier avec Hermès", "Acter"],
      back: [["Résumé", text(item.summary, "Résumé non renseigné")], ["Informations détaillées", text(item.details, "Informations détaillées non renseignées")], ["Source", text(item.source_ref || item.source_note, "Source non renseignée")], ["Version source", text(item.source_version, "Non renseignée")], ["Révision technique", text(item.revision, "Non renseignée")], ["Mis à jour le", text(item.updated_at, "Non renseigné")], ["Auteur", text(item.author, "Non renseigné")]],
      source_refs: [item.source_ref].filter(Boolean), base_acted_id: item.base_acted_id || null,
      series_id: item.series_id || null, technical_revision: item.revision || null,
      corroboration_refs: item.corroboration_refs || item.support_refs || [], contradiction_refs: item.contradiction_refs || [],
    });
  }

  function normalizeLegacyDocument(item) {
    const naming = item.naming || {};
    const structured = item.structured_extraction || {};
    const chunks = item.chunk_summary || {};
    const id = item.document_id || item.card_id || item.source_ref || crypto.randomUUID();
    const category = naming.document_type || item.category || "Document";
    const chunkSummary = chunks.total == null ? null : `${chunks.total} chunk${chunks.total === 1 ? "" : "s"} · ${chunks.indexed ?? 0} indexé${chunks.indexed === 1 ? "" : "s"}`;
    return card({
      entity_id: `document:${id}`, entity_type: "document", family: "information", presentation_family: "information",
      category, title: naming.object_name || item.title || category,
      summary: item.summary || chunkSummary || [naming.document_type, naming.phase_code].filter(Boolean).join(" · ") || "Document source",
      status: item.status || item.analysis_status || "partial", index: naming.revision_index || item.index || null,
      date: item.document_date || item.date || item.created_at || null, author: item.author || naming.issuer || item.issuer || null,
      type_tags: item.type_tags || [slug(category)], subject_tags: item.subject_tags || item.tags || [], limits: item.limits || [],
      available_actions: item.available_actions || (structured.compilation_id && chunks.total ? ["Inspecter les chunks"] : []),
      back: [["Résumé", text(item.summary, "Résumé non renseigné")], ["Informations détaillées", text(item.details, "À produire dans une Information métier")], ["Extraction structurée", text(structured.status, "Non disponible")], ["Unités", text(structured.unit_count, "Non renseigné")], ["Pages / tableaux", `${structured.page_count ?? "—"} / ${structured.table_count ?? "—"}`], ["Anomalies", text(structured.anomaly_count, "Non renseigné")], ["Chunks / indexés", `${chunks.total ?? "—"} / ${chunks.indexed ?? "—"}`], ["Chunks signalés", text(chunks.with_quality_flags, "Non renseigné")], ["Vérification source", chunks.verification_status === "not_observed" ? "Non observée" : text(chunks.verification_status, "Non renseignée")], ["Source", text(item.source_ref, "Source non exposée")]],
      source_refs: [item.source_ref].filter(Boolean),
      corroboration_refs: item.corroboration_refs || item.support_refs || [], contradiction_refs: item.contradiction_refs || [],
    });
  }

  function normalizeKnowledge(item) {
    return card({ entity_id: `knowledge:${item.knowledge_id || item.card_id || crypto.randomUUID()}`, entity_type: "knowledge", family: "information", presentation_family: "information", category: item.family || "Référence", title: item.title || "Knowledge", summary: item.summary || `Version ${item.version || 1}`, status: item.review_status || "generated_unreviewed", date: item.updated_at || null, author: item.author || null, type_tags: item.type_tags || ["etude"], subject_tags: item.subject_tags || item.tags || [], limits: item.limits || ["consultatif"], corroboration_refs: item.corroboration_refs || item.support_refs || [], contradiction_refs: item.contradiction_refs || [], back: [["Informations détaillées", text(item.markdown, "Contenu non exposé")]] });
  }

  function normalizeWork(projection) {
    const issue = workData(projection);
    const activity = workActivity(projection);
    const id = issue.issue_id || crypto.randomUUID();
    const projectedIssue = activity && !activity.invalid ? activity.issue : null;
    const typeTags = projectedIssue?.type_tags || issue.type_tags || [];
    const subjectTags = projectedIssue?.subject_tags || issue.subject_tags || issue.tags || [];
    const issueLimits = projectedIssue?.limits || issue.limits || [];
    if (activity?.invalid || (!activity && !window.PANTHEON_COCKPIT_DEMO)) {
      return card({
        entity_id: `work:${id}`,
        entity_type: "work_issue",
        family: "work",
        presentation_family: "work",
        category: "Travail",
        title: issue.title || "Travail",
        summary: activity?.reason || "Projection d’activité absente.",
        status: "conflict",
        type_tags: typeTags,
        subject_tags: subjectTags,
        limits: issueLimits,
        back: [["Refus", activity?.reason || "Le serveur n’a pas fourni le contrat d’activité attendu."], ["Limite", "Aucune activité runtime n’est reconstruite dans le navigateur."]],
        source_work_id: id,
      });
    }

    const milestones = issue.milestones || issue.steps || [];
    const resources = [...(issue.responsibilities || []), ...(issue.skills || []), ...(issue.functions || []), ...(issue.tools || [])];
    const back = [["Objectif", text(issue.description, "Non renseigné")]];
    if (activity) {
      const assignment = [activity.issue.status_label, activity.issue.assigned_to ? `Assigné à ${activity.issue.assigned_to}` : null].filter(Boolean).join(" · ");
      const latestRun = activity.latest_run
        ? [activity.latest_run.status_label, activity.latest_run.run_id].filter(Boolean).join(" · ")
        : "Aucun run observé";
      const timeline = activity.activity.map(activityEventLine).filter(Boolean).join("\n");
      const result = activity.result_candidate;
      back.push(["Suivi", assignment || "État non renseigné"]);
      back.push(["Dernier run", latestRun]);
      back.push(...technicalExecutionRows(activity.execution_trace_summary));
      if (activity.latest_event) back.push(["Dernier événement", activityEventLine(activity.latest_event)]);
      if (timeline) back.push(["Chronologie", timeline]);
      if (result) {
        back.push(["Résultat candidat", [result.outcome_label, result.summary].filter(Boolean).join(" — ")]);
        if (result.result_refs.length) back.push(["Résultats liés", result.result_refs.join("\n")]);
        if (result.evidence_candidate_refs.length) back.push(["Evidence candidates", result.evidence_candidate_refs.join("\n")]);
      }
      if (activity.trace_refs.length) back.push(["Traces", activity.trace_refs.join("\n")]);
      const allLimits = [...issueLimits, ...(activity.limits || [])];
      if (allLimits.length) back.push(["Limites", [...new Set(allLimits)].join(" · ")]);
    }
    back.push(["Jalons", milestones.length ? milestones.map(step => typeof step === "string" ? step : step.label || step.title).filter(Boolean).join("\n") : "Non renseignés"]);
    back.push(["Responsabilités · Skills · Fonctions · Outils", resources.length ? resources.map(String).join(" · ") : "Non renseignés"]);
    back.push(["Résultat attendu", text(issue.result_ref || issue.output_ref || issue.requested_effect, "Non renseigné")]);

    return card({
      entity_id: `work:${id}`,
      entity_type: "work_issue",
      family: "work",
      presentation_family: "work",
      category: "Travail",
      title: issue.title || "Travail",
      summary: issue.description || "Objectif de travail non renseigné",
      status: projectedIssue?.status || issue.status || "open",
      type_tags: typeTags,
      subject_tags: subjectTags,
      limits: issueLimits,
      back,
      source_work_id: id,
      source_run_id: activity?.latest_run?.run_id || null,
      task_contract_ref: activity?.issue?.task_contract_ref || issue.task_contract_ref || null,
      trace_refs: activity?.trace_refs || [],
    });
  }


  function candidateFieldTitle(key) {
    const field = (state.projectSchema?.fields || []).find(item => item.key === key);
    return field?.title || field?.label || key.replaceAll("_", " ");
  }

  function candidateChangeLine(change) {
    const field = (state.projectSchema?.fields || []).find(item => item.key === change.field);
    return `${candidateFieldTitle(change.field)} : ${formattedValue(field, change.before)} → ${formattedValue(field, change.proposed)}`;
  }

  function normalizeChangeCandidate(item) {
    const changes = Array.isArray(item.changes) ? item.changes : [];
    return card({ entity_id: `decision:change:${item.candidate_id}`, entity_type: "project_change_candidate", family: "decision", presentation_family: "decision", category: "Décision · Modification", title: changes.length === 1 ? `Modifier ${candidateFieldTitle(changes[0].field)}` : `Modifier ${changes.length} champs du Projet`, summary: item.reason || changes.map(candidateChangeLine).join(" · ") || "Proposition de modification à examiner.", status: item.status || "pending_review", date: item.created_at || null, available_actions: item.status === "pending_review" ? ["Refuser", "Valider"] : [], back: [["Projet", text(item.entity_id, state.project)], ["Proposition", changes.map(candidateChangeLine).join("\n") || "Aucun diff exposé"], ["Proposé par", `${text(item.proposer, "Inconnu")} · ${text(item.proposer_kind, "inconnu")}`], ["Révision de base", text(item.base_revision, "Non renseignée")], ["Motif", text(item.reason, "Non renseigné")], ["Sources", (item.source_refs || []).join("\n") || "Aucune source déclarée"]], source_candidate_id: item.candidate_id, source_project_id: item.entity_id });
  }

  function normalizeCurrentRun(item) {
    const runId = item.run_id || item.execution_id || item.id || crypto.randomUUID();
    return card({ entity_id: `run:${runId}`, entity_type: item.entity_type || "hermes_run", family: item.family || "work", presentation_family: item.presentation_family || item.family || "work", category: item.category || "Run en cours", title: item.title || item.task_title || `Run ${runId}`, summary: item.summary || item.task_summary || "Exécution Hermès en cours.", status: item.status || item.run_status || "in_progress", date: item.started_at || item.created_at || null, subject_tags: item.subject_tags || item.tags || [], limits: item.limits || [], available_actions: item.available_actions || [], back: item.back || [["Runtime", text(item.runtime || item.runtime_owner, "Non renseigné")], ["Scope", text(item.scope_ref || item.scope, "Non renseigné")], ["Démarré", text(item.started_at, "Non renseigné")]], source_run_id: runId });
  }

  function currentRunItems() {
    return state.currentRuns.filter(item => ["active", "in_progress", "running", "waiting"].includes(item.status || item.run_status));
  }

  function contactDisplay(item) {
    const identity = [item.name, item.organization].filter(Boolean).join(" · ");
    const role = item.role ? ` — ${item.role}` : "";
    const details = [item.email, item.phone].filter(Boolean).join(" · ");
    return `${identity || "Contact non renseigné"}${role}${details ? `\n${details}` : ""}`;
  }

  function normalizeContacts(projectId, contacts = []) {
    const groups = new Map(CONTACT_GROUPS.map(name => [name, []]));
    for (const item of Array.isArray(contacts) ? contacts : []) {
      const group = CONTACT_GROUPS.includes(item.group) ? item.group : "Autres intervenants";
      groups.get(group).push(item);
    }
    const back = [];
    for (const group of CONTACT_GROUPS) {
      const values = groups.get(group) || [];
      if (values.length) back.push([group, values.map(contactDisplay).join("\n")]);
    }
    return card({ entity_id: `project:${projectId}:contacts`, entity_type: "project_contacts", family: "contact", presentation_family: "contact", category: "Contacts", title: "Contacts", summary: `${Array.isArray(contacts) ? contacts.length : 0} contact(s)`, status: "neutral", identity_accent: stableAccent(projectId), back: back.length ? back : [["Contacts", "Aucun contact renseigné pour cette affaire."]], source_project_id: projectId });
  }

  function toolStatus(item) {
    if (item.governance_state === "approved") return "reviewed";
    if (item.governance_state === "candidate") return "candidate";
    if (item.governance_state === "watch") return "watch";
    if (item.health_state === "observed_ready") return "ready";
    if (item.governance_state === "unreviewed") return "unreviewed";
    return "neutral";
  }

  function permissionLines(permissions = {}) {
    return Object.entries(permissions).map(([key, value]) => `${key.replaceAll("_", " ")} : ${value}`).join("\n");
  }

  function valueOrNotObserved(value) {
    return value == null || value === "" ? NOT_OBSERVED : String(value);
  }

  function anchorLabel(anchor) {
    if (!anchor || typeof anchor !== "object") return NOT_OBSERVED;
    return `${valueOrNotObserved(anchor.kind)} · ${valueOrNotObserved(anchor.value)}`;
  }

  function activationScopeLabel(scope) {
    if (!scope || typeof scope !== "object") return NOT_OBSERVED;
    return [scope.scope_type, scope.scope_id, scope.scope_label].filter(Boolean).join(" · ") || NOT_OBSERVED;
  }

  function exactGovernanceRows(item) {
    return [
      ["Binding exact", valueOrNotObserved(item.binding_id)],
      ["Release immuable", anchorLabel(item.implementation_anchor)],
      ["Activation", valueOrNotObserved(item.activation_state)],
      ["Scope d’activation", activationScopeLabel(item.activation_scope)],
      ["Compatibilité observée", valueOrNotObserved(item.compatibility_status)],
      ["Sécurité qualifiée", valueOrNotObserved(item.safety_status)],
      ["Fraîcheur observation", valueOrNotObserved(item.freshness_status)],
      ["Source observation", valueOrNotObserved(item.source_observation_ref)],
      ["Observation datée", valueOrNotObserved(item.compatibility_observed_at)],
      ["Limite d’autorité", "binding sélectionné ≠ dépendance adoptée · compatible ≠ activé · UI projetée ≠ autorisation"],
    ];
  }

  function normalizeTool(item) {
    const slots = Array.isArray(item.capability_slots) ? item.capability_slots : [];
    const runtimeCapabilities = Array.isArray(item.capabilities) ? item.capabilities : [];
    const permissions = item.permissions && typeof item.permissions === "object" && !Array.isArray(item.permissions) ? item.permissions : {};
    const back = [
      ["Description", text(item.long_description || item.short_description, "Non renseignée")],
      ["Capability Slots", slots.length ? slots.join("\n") : "Aucun slot déclaré"],
      ["Provenance", text(item.provenance_mode, "Non renseignée")],
      ["Owner runtime", text(item.runtime_owner, "Non renseigné")],
      ["Installation", text(item.installation_state, "unknown")],
      ["État natif", text(item.native_state, "unknown")],
      ["Santé observée", text(item.health_state, "unknown")],
      ["Gouvernance", text(item.governance_state, "unknown")],
      ["Mise à jour", text(item.update_state, "unknown")],
      ["Permissions", permissionLines(permissions) || "Non qualifiées"],
      ["Capacités runtime", runtimeCapabilities.length ? runtimeCapabilities.join("\n") : "Non observées"],
      ["Evidence attendue", text(item.evidence_expectation, "À définir avant usage conséquent")],
      ["Rollback", text(item.rollback_posture, "Non renseigné")],
      ["Prochaine décision humaine", text(item.next_human_decision, "Aucune")],
      ["Risques connus", (item.known_risks || []).join("\n") || "Non renseignés"],
      ["Interdits", (item.forbidden || []).join("\n") || "Aucun interdit déclaré"],
      ...exactGovernanceRows(item),
    ];
    return card({
      entity_id: `tool:${item.tool_id}`,
      entity_type: "tool",
      family: "tool",
      presentation_family: "tool",
      category: item.category || item.resource_type || "Outil",
      type_tags: ["outil"],
      subject_tags: slots,
      title: item.name || item.tool_id,
      summary: item.short_description || "Outil ou binding candidat.",
      status: toolStatus(item),
      date: item.observed_at || null,
      back,
    });
  }

  function buildToolCards() {
    if (state.toolCatalog.length) return state.toolCatalog.map(normalizeTool);
    return [card({ entity_id: "tools:catalog-unavailable", entity_type: "tool_container", role: "container", family: "tool", presentation_family: "tool", category: "Outil", type_tags: ["outil"], title: "Catalogue indisponible", summary: "Aucun état runtime n’est inventé lorsque le catalogue ne peut pas être chargé.", status: "neutral", back: [["Principe", "Catalogue absent ≠ outil absent · runtime non observé ≠ non installé."]] })];
  }

  let projectLoadGeneration = 0;
  let graphLoadGeneration = 0;

  function findProject(projects, project) {
    const wanted = String(project || "").trim().toLocaleLowerCase("fr-FR");
    if (!wanted) return null;
    return projects.find(item => [item.project_id, item.code, item.display_name].filter(Boolean).some(value => String(value).toLocaleLowerCase("fr-FR") === wanted)) || null;
  }

  function projectLookup() {
    return findProject(state.projects, state.project);
  }

  function publishGraphMutation() {
    window.PantheonCockpitGraph = Object.freeze({ cards: state.cards, children: state.children });
    window.dispatchEvent(new CustomEvent("pantheon:graph-updated"));
  }

  function rebuildGraph() {
    graphLoadGeneration += 1;
    state.cards.clear();
    state.children.clear();
    for (const model of rootCards()) putCard(model);
    const selected = projectLookup();
    const selectedProjectId = selected?.project_id || state.project || null;
    const selectedCardId = selected ? projectEntityId(selected) : selectedProjectId ? `project:${selectedProjectId}` : null;
    childAssembler.assemble({ rootItemIds: navigationProjection.rootItemIds, sourcesFor: navigationProjection.sourcesFor, state, selected, selectedProjectId, selectedCardId, putCard, setChildren, normalizeProject, normalizeKnowledge, normalizeChangeCandidate, normalizeCurrentRun, normalizeContacts, normalizeInformation, normalizeLegacyDocument, normalizeWork, buildToolCards, workData, currentRunItems });
    state.navigator = window.PantheonSpatialNavigation.create({
      root_collection_id: navigationProjection.rootCollectionId,
      root_item_ids: navigationProjection.rootItemIds,
    });
    // Read-only exposure for the bounded knowledge-map lens (map/). The lens
    // reads this snapshot; it never writes back. See mvp_vertical/cockpit/map/.
    publishGraphMutation();
  }

  function currentModel() { return state.cards.get(state.navigator?.currentId()) || null; }
  function breadcrumbLabels() { return state.navigator.snapshot().path.map(part => state.cards.get(part.current_id)?.title).filter(Boolean); }

  function childCollectionFor(model) {
    return model?.child_collection && typeof model.child_collection === "object"
      ? model.child_collection
      : null;
  }

  function loadedChildrenFor(model) {
    return model?.entity_id ? state.children.get(model.entity_id) || [] : [];
  }

  function canDescend(model) {
    if (!model) return false;
    const childCollection = childCollectionFor(model);
    if (loadedChildrenFor(model).length) return Boolean(childCollection?.collection_id);
    return childCollection?.state === "available" && Boolean(childCollection.load_action);
  }

  function renderFallbackCard(model) {
    const article = document.createElement("article");
    article.className = "card v2-card";
    article.dataset.family = model.presentation_family || model.family;
    article.dataset.flipped = state.flipped.has(model.entity_id) ? "true" : "false";
    const inner = document.createElement("div");
    inner.className = "card-inner v2-card-inner";
    const front = document.createElement("div");
    front.className = "card-face card-front v2-card-face v2-card-front";
    const title = document.createElement("h2");
    title.className = "card-title v2-card-title";
    title.textContent = model.title;
    const summary = document.createElement("p");
    summary.className = "card-summary v2-card-summary";
    summary.textContent = model.summary;
    front.append(title, summary);
    const back = document.createElement("div");
    back.className = "card-face card-back v2-card-face v2-card-back";
    for (const [heading, value] of model.back || []) {
      const section = document.createElement("section");
      const h3 = document.createElement("h3"); h3.textContent = heading;
      const p = document.createElement("p"); p.textContent = value;
      section.append(h3, p); back.append(section);
    }
    inner.append(front, back); article.append(inner); return article;
  }

  function updateChrome(snapshot, model) {
    $("v2-breadcrumb").textContent = breadcrumbLabels().join(" / ");
    $("v2-previous").disabled = !snapshot.can_move_previous;
    $("v2-next").disabled = !snapshot.can_move_next;
    $("v2-ascend").disabled = !snapshot.can_ascend;
    $("v2-descend").disabled = !canDescend(model);
    $("v2-flip").disabled = !model;
    const rootCurrent = snapshot.path[0]?.current_id;
    for (const button of document.querySelectorAll("[data-space]")) button.classList.toggle("is-active", `space:${button.dataset.space}` === rootCurrent);
  }

  function render() {
    if (!state.navigator) return;
    const snapshot = state.navigator.snapshot();
    const siblings = snapshot.sibling_ids.map(id => state.cards.get(id)).filter(Boolean);
    const model = currentModel();
    const parentEntityId = snapshot.path[snapshot.path.length - 1]?.parent_entity_id || null;
    if (window.PANTHEON_COCKPIT_SWIPER?.mount) {
      window.PANTHEON_COCKPIT_SWIPER.mount({ key: snapshot.collection_id, models: siblings, activeIndex: snapshot.current_index, parentEntityId, onActiveChange(active) { if (active?.entity_id) state.navigator.selectSibling(active.entity_id); updateChrome(state.navigator.snapshot(), active); } });
    } else {
      const stage = $("v2-stage");
      stage.replaceChildren(model ? renderFallbackCard(model) : document.createTextNode("Aucune carte dans cette collection."));
    }
    updateChrome(snapshot, model);
  }

  function moveHorizontal(delta) { state.lastMove = delta < 0 ? "right" : "left"; state.navigator.moveHorizontal(delta); render(); }

  async function loadProjectedChildCollection(model, childCollection) {
    const generation = ++graphLoadGeneration;
    const parentId = String(model?.entity_id || "").trim();
    const expectedCollectionId = String(childCollection?.collection_id || "").trim();
    const token = $("v2-token").value;
    if (!token) return setMessage("Clé d’accès requise pour lire cette collection.");
    if (!parentId || !expectedCollectionId) {
      return setMessage("Projection enfant incomplète : relation parent/collection absente.");
    }

    try {
      const collection = await dataLoader.loadChildCollection(childCollection.load_action, token);
      if (generation !== graphLoadGeneration) return;
      if (collection.collection_id !== expectedCollectionId) {
        throw new Error("La collection chargée ne correspond pas à la projection demandée.");
      }
      if (collection.parent_entity_id !== parentId) {
        throw new Error("La collection chargée ne correspond pas à son parent projeté.");
      }

      const ids = childAssembler.registerLoadedCollection(parentId, collection, {
        state,
        putCard,
        setChildren,
      });
      publishGraphMutation();

      if (currentModel()?.entity_id !== parentId) {
        render();
        return;
      }
      if (!ids.length) {
        render();
        setMessage("Collection chargée : aucune carte.");
        return;
      }

      state.navigator.descend({
        parent_entity_id: parentId,
        collection_id: collection.collection_id,
        item_ids: ids,
      });
      render();
      setMessage(`${ids.length} carte(s) chargée(s).`);
    } catch (error) {
      if (generation !== graphLoadGeneration) return;
      setMessage(`Chargement de collection refusé : ${error.message}`);
    }
  }

  async function loadAvailableChildCollection(model, childCollection) {
    if (childCollection.load_action?.kind === "project_bundle") {
      await loadProject({ focusProject: true, childLoadAction: childCollection.load_action });
      return;
    }
    await loadProjectedChildCollection(model, childCollection);
  }

  async function descend() {
    const model = currentModel();
    if (!model) return;
    const children = loadedChildrenFor(model);
    const childCollection = childCollectionFor(model);
    if (!children.length && childCollection?.state === "available" && childCollection.load_action) {
      await loadAvailableChildCollection(model, childCollection);
      return;
    }
    if (!children.length) return toggleFlip();
    if (!childCollection?.collection_id) return setMessage("Projection enfant incomplète : identité de collection absente.");
    state.navigator.descend({
      parent_entity_id: model.entity_id,
      collection_id: childCollection.collection_id,
      item_ids: children,
    });
    render();
  }

  function ascend() { state.navigator.ascend(); render(); }
  function toggleFlip() { const model = currentModel(); if (!model) return; if (state.flipped.has(model.entity_id)) state.flipped.delete(model.entity_id); else state.flipped.add(model.entity_id); render(); }
  function jumpToSpace(space) { state.navigator.returnToRoot(`space:${space}`); render(); }
  function setMessage(message) { $("v2-status").textContent = message; }

  function emptyProjectBundle() {
    return {
      information: [], legacyDocuments: [], knowledge: [], workIssues: [],
      decisionRequests: [], changeCandidates: [], projectAnatomy: null,
    };
  }

  async function loadProject({ focusProject = false, childLoadAction = null } = {}) {
    const generation = ++projectLoadGeneration;
    const graphGeneration = ++graphLoadGeneration;
    const requested = String(childLoadAction?.context_id || $("v2-project").value || "").trim();
    if (childLoadAction?.context_id) $("v2-project").value = requested;
    const loadButton = $("v2-load");
    const token = $("v2-token").value;
    if (!token) {
      loadButton.disabled = false;
      return setMessage("Clé d’accès requise pour lire Agency Data.");
    }
    loadButton.disabled = true;
    try {
      const [projects, projectSchema, globalDecisionRequests] = await Promise.all([
        dataLoader.loadAgencyProjects(token),
        dataLoader.loadProjectSchema(token),
        dataLoader.loadDecisionInbox(token),
      ]);
      if (generation !== projectLoadGeneration || graphGeneration !== graphLoadGeneration) return;

      let project = requested;
      const matched = findProject(projects, project);
      if (matched?.project_id) project = matched.project_id;
      const bundle = project
        ? childLoadAction
          ? await dataLoader.loadChildCollection(childLoadAction, token)
          : await dataLoader.loadProjectBundle(project, token)
        : emptyProjectBundle();
      if (generation !== projectLoadGeneration || graphGeneration !== graphLoadGeneration) return;

      state.token = token;
      state.projects = projects;
      state.projectSchema = projectSchema;
      state.project = project;
      Object.assign(state, bundle);
      window.PantheonGlobalDecisionRequests = Object.freeze((globalDecisionRequests || []).slice());
      window.PantheonProjectDecisionRequests = Object.freeze((bundle.decisionRequests || []).slice());

      rebuildGraph();
      state.navigator.returnToRoot("space:affaires");
      if (focusProject || state.project) {
        const projectIds = state.children.get("space:affaires") || [];
        const target = projectIds.find(id => state.cards.get(id)?.source_project_id === state.project);
        if (target) state.navigator.descend({ parent_entity_id: "space:affaires", collection_id: "children:space:affaires", item_ids: projectIds, initial_entity_id: target });
      }
      render();
      setMessage(state.project ? `Affaire ${matched?.display_name || matched?.code || state.project} chargée · ${state.changeCandidates.length} modification(s) à valider.` : `${state.projects.length} affaire(s) chargée(s).`);
    } catch (error) {
      if (generation !== projectLoadGeneration || graphGeneration !== graphLoadGeneration) return;
      setMessage(`Chargement refusé : ${error.message}`);
    } finally {
      if (generation === projectLoadGeneration) loadButton.disabled = false;
    }
  }

  function bindControls() {
    $("v2-previous").addEventListener("click", () => moveHorizontal(-1));
    $("v2-next").addEventListener("click", () => moveHorizontal(1));
    $("v2-ascend").addEventListener("click", ascend);
    $("v2-descend").addEventListener("click", () => void descend());
    $("v2-flip").addEventListener("click", toggleFlip);
    $("v2-load").addEventListener("click", () => void loadProject());
    document.querySelectorAll("[data-space]").forEach(button => button.addEventListener("click", () => jumpToSpace(button.dataset.space)));
  }

  async function init() {
    state.toolCatalog = await dataLoader.loadToolCatalog();
    rebuildGraph();
    bindControls();
    window.addEventListener("pantheon:current-runs", event => { state.currentRuns = Array.isArray(event.detail?.runs) ? event.detail.runs : []; rebuildGraph(); render(); });
    render();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => void init(), { once: true });
  else void init();
})();