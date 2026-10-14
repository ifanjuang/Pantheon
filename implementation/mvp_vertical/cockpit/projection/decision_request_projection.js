(() => {
  "use strict";

  const TYPE_LABELS = Object.freeze({
    question: "Question",
    validation: "Validation",
    approval: "Approbation",
    arbitration: "Arbitrage",
  });
  const ACTION_LABELS = Object.freeze({
    question: "Répondre",
    validation: "Valider",
    approval: "Approuver",
    arbitration: "Arbitrer",
  });
  const PRIORITY_LABELS = Object.freeze({
    low: "Faible",
    normal: "Normale",
    high: "Haute",
    urgent: "Urgente",
  });

  const text = (value, fallback = "") => value == null || value === "" ? fallback : String(value);

  function card(input) {
    const projection = window.PantheonStructuredInterface?.buildCardProjection?.(input) || {};
    return {
      role: "entity",
      family: "decision",
      presentation_family: "decision",
      status: "pending",
      summary: "",
      type_tags: [],
      subject_tags: [],
      limits: [],
      available_actions: [],
      back: [],
      ...input,
      ...projection,
      presentation_family: projection.presentation_family || input.presentation_family || "decision",
    };
  }

  function requestData(envelope) {
    return envelope?.decision_request || envelope || {};
  }

  function optionsText(request) {
    return (request.options || [])
      .map(option => `${option.label} — ${option.consequence}`)
      .join("\n") || "Réponse selon le mode déclaré";
  }

  function normalize(envelope) {
    const request = requestData(envelope);
    const requestId = request.request_id || crypto.randomUUID();
    const typeLabel = TYPE_LABELS[request.decision_type] || "Décision";
    const actionLabel = ACTION_LABELS[request.decision_type] || "Décider";
    const priorityLabel = PRIORITY_LABELS[request.priority] || text(request.priority, "Normale");
    const sources = Array.isArray(request.source_refs) ? request.source_refs : [];
    const gaps = Array.isArray(request.evidence_gaps) ? request.evidence_gaps : [];
    return card({
      entity_id: `decision-request:${requestId}`,
      entity_type: "decision_request",
      category: typeLabel,
      title: text(request.question, "Détermination humaine requise"),
      summary: text(
        request.blocked_action || request.next_safe_action,
        request.blocking ? "Cette demande bloque une suite déclarée." : "Préférence ou revue humaine demandée.",
      ),
      status: request.status || "pending",
      date: request.created_at || null,
      author: request.created_by || null,
      type_tags: [request.decision_type, request.response_mode].filter(Boolean),
      subject_tags: [request.project_ref, request.work_issue_ref].filter(Boolean),
      limits: [
        request.blocking ? "bloquant" : "non bloquant",
        ...gaps.map(gap => `écart: ${gap}`),
      ],
      available_actions: request.status === "pending" ? [actionLabel] : [],
      back: [
        ["Type", typeLabel],
        ["Priorité", priorityLabel],
        ["Propriétaire", text(request.decision_owner, "Non renseigné")],
        ["Options / réponse", optionsText(request)],
        ["Recommandation candidate", text(request.recommendation_candidate, "Aucune")],
        ["Action bloquée", text(request.blocked_action, "Aucune action bloquée")],
        ["Prochaine action sûre", text(request.next_safe_action, "À déterminer")],
        ["Sources", sources.join("\n") || "Aucune source déclarée"],
        ["Écarts de preuve", gaps.join("\n") || "Aucun écart déclaré"],
        ["Digest candidat", text(request.candidate_digest?.value, "Non renseigné")],
      ],
      source_request_id: requestId,
      source_project_id: request.project_ref || null,
      source_work_issue_id: request.work_issue_ref || null,
      request_is_not_decision: true,
      attention_required: request.status === "pending",
    });
  }

  function rootCard() {
    return card({
      entity_id: "space:decisions",
      entity_type: "cockpit_space",
    });
  }

  window.PantheonDecisionRequestProjection = Object.freeze({ normalize, rootCard });
})();
