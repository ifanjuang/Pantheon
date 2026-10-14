(() => {
  "use strict";

  function text(value, fallback = "—") {
    return value == null || value === "" ? fallback : String(value);
  }

  function entityId(ref) {
    return ref && typeof ref === "object" ? ref.entity_id || null : null;
  }

  function relationLine(item, currentObjectId) {
    const subject = entityId(item.subject_ref);
    const object = entityId(item.object_ref);
    const other = subject === currentObjectId ? object : subject;
    return [item.relation_type, other].filter(Boolean).join(" → ");
  }

  function claimLine(item) {
    const claimValue = item?.value;
    const rawValue = claimValue && typeof claimValue === "object" ? claimValue.value : null;
    let renderedValue = "";
    if (rawValue !== null && rawValue !== undefined) {
      renderedValue = typeof rawValue === "object" ? JSON.stringify(rawValue) : String(rawValue);
      if (claimValue.unit) renderedValue += ` ${claimValue.unit}`;
    }
    const value = renderedValue ? ` : ${renderedValue}` : "";
    const certainty = item.certainty ? ` · ${item.certainty}` : "";
    const proof = item.proof_status ? ` · ${item.proof_status}` : "";
    return `${item.attribute_key || item.claim_id || "Attribut"}${value}${certainty}${proof}`;
  }

  function identifierLine(item) {
    return [item.scheme, item.value].filter(Boolean).join(" : ");
  }

  function identityLine(item) {
    const target = entityId(item.object_ref);
    const proof = item.proof_status ? ` · ${item.proof_status}` : "";
    return `${item.relation_type || "identity.represents"}${target ? ` → ${target}` : ""}${proof}`;
  }

  function sourceLine(item) {
    return [item.source_kind, item.source_artifact_ref, item.proof_status]
      .filter(Boolean)
      .join(" · ");
  }

  function baseCard(input) {
    return {
      role: "entity",
      family: "project",
      presentation_family: "information",
      status: "neutral",
      summary: "",
      type_tags: [],
      subject_tags: [],
      limits: ["Projection en lecture seule"],
      available_actions: [],
      back: [],
      ...input,
    };
  }

  function rootCard(anatomy) {
    const summary = anatomy.summary || {};
    const coverage = anatomy.coverage || {};
    const hierarchy = anatomy.structure?.hierarchy || {};
    return baseCard({
      entity_id: `project-anatomy:${anatomy.project_ref}`,
      entity_type: "project_anatomy_projection",
      category: "Anatomie du projet",
      title: "Anatomie du projet",
      summary: `${summary.stable_object_count || 0} objet(s) · ${summary.source_representation_count || 0} source(s) · ${summary.unmapped_source_representation_count || 0} non mappée(s)`,
      type_tags: ["project-anatomy", `v${anatomy.model_version || 2}`],
      subject_tags: summary.attention_claim_count ? [`${summary.attention_claim_count} point(s) à qualifier`] : [],
      limits: [
        "Projection en lecture seule",
        coverage.status === "not_persisted" ? "Couverture d’observation non persistée" : null,
        hierarchy.status === "not_derived" ? "Hiérarchie non dérivée sans sémantique admise" : null,
      ].filter(Boolean),
      back: [
        ["Objets stables", text(summary.stable_object_count, "0")],
        ["Représentations source", text(summary.source_representation_count, "0")],
        ["Relations", text(summary.relation_claim_count, "0")],
        ["Claims d’attribut", text(summary.attribute_claim_count, "0")],
        ["Matériau non mappé", text(summary.unmapped_source_representation_count, "0")],
        ["Incertitudes à qualifier", text(summary.attention_claim_count, "0")],
        ["Couverture", coverage.status === "not_persisted" ? "Non persistée — aucune absence n’est déduite." : text(coverage.status)],
        ["Hiérarchie", hierarchy.status === "not_derived" ? "Non dérivée — relations exposées sans parentage inventé." : text(hierarchy.status)],
        ["Contrats", text(anatomy.model_authority_ref)],
        ["Doctrine", text(anatomy.model_doctrine_ref)],
      ],
      source_project_id: anatomy.project_ref,
    });
  }

  function objectCard(item) {
    const relations = Array.isArray(item.relations) ? item.relations : [];
    const attributes = Array.isArray(item.attribute_claims) ? item.attribute_claims : [];
    const sources = Array.isArray(item.source_representation_refs) ? item.source_representation_refs : [];
    const phases = Array.isArray(item.phase_refs) ? item.phase_refs : [];
    const attention = Array.isArray(item.attention_claim_refs) ? item.attention_claim_refs : [];
    return baseCard({
      entity_id: `apu-object:${item.object_id}`,
      entity_type: "apu_object",
      category: item.object_family || "Objet du projet",
      title: item.display_name || item.internal_code || item.object_id,
      summary: `${attributes.length} attribut(s) · ${relations.length} relation(s) · ${sources.length} source(s)`,
      type_tags: [item.object_family].filter(Boolean),
      subject_tags: phases,
      limits: [
        "Projection en lecture seule",
        attention.length ? `${attention.length} claim(s) nécessitent une qualification` : null,
      ].filter(Boolean),
      back: [
        ["Identité stable", item.object_id],
        ["Famille", text(item.object_family)],
        ["Code", text(item.internal_code)],
        ["Phases", phases.join(" · ") || "Non renseignées"],
        ["Sources", sources.join("\n") || "Aucune représentation source reliée"],
        ["Attributs", attributes.map(claimLine).join("\n") || "Aucun claim d’attribut"],
        ["Relations", relations.map(relation => relationLine(relation, item.object_id)).join("\n") || "Aucune relation exposée"],
        ["Attention", attention.join("\n") || "Aucun claim explicitement signalé"],
      ],
      source_object_id: item.object_id,
    });
  }

  function unmappedSourceCard(item) {
    const limitations = Array.isArray(item.limitations) ? item.limitations : [];
    const identifiers = Array.isArray(item.identifiers) ? item.identifiers : [];
    const locators = Array.isArray(item.locators) ? item.locators : [];
    const attributes = Array.isArray(item.attribute_claims) ? item.attribute_claims : [];
    const identityClaims = Array.isArray(item.identity_claims) ? item.identity_claims : [];
    return baseCard({
      entity_id: `apu-source:${item.representation_id}`,
      entity_type: "apu_source_representation",
      category: "Source non mappée",
      title: item.source_artifact_ref || item.representation_id,
      summary: sourceLine(item) || "Représentation source sans identité stable résolue.",
      type_tags: [item.source_kind].filter(Boolean),
      subject_tags: [],
      limits: [
        "Non mappé ≠ absent",
        "Projection en lecture seule",
        ...limitations,
      ],
      back: [
        ["Représentation", item.representation_id],
        ["Type de source", text(item.source_kind)],
        ["Source", text(item.source_artifact_ref)],
        ["Version source", text(item.source_version_ref)],
        ["Observé", text(item.observed_at)],
        ["État de preuve source", text(item.proof_status)],
        ["Binding", text(item.binding_ref)],
        ["Adapter", text(item.adapter_version)],
        ["Identifiants natifs", identifiers.length ? identifiers.map(identifierLine).join("\n") : "Non renseignés"],
        ["Localisateurs", locators.length ? locators.map(value => JSON.stringify(value)).join("\n") : "Non renseignés"],
        ["Claims d’attribut", attributes.map(claimLine).join("\n") || "Aucun claim d’attribut porté par la source"],
        ["Rapprochements d’identité", identityClaims.map(identityLine).join("\n") || "Aucun rapprochement d’identité déclaré"],
        ["Limites", limitations.join("\n") || "Aucune limite explicitement déclarée"],
      ],
      source_representation_id: item.representation_id,
    });
  }

  function projectCards(anatomy) {
    if (!anatomy || !anatomy.project_ref) return null;
    const root = rootCard(anatomy);
    const objects = Array.isArray(anatomy.structure?.objects)
      ? anatomy.structure.objects.map(objectCard)
      : [];
    const unmapped = Array.isArray(anatomy.unmapped_material)
      ? anatomy.unmapped_material.map(unmappedSourceCard)
      : [];
    return { root, children: [...objects, ...unmapped] };
  }

  window.PantheonProjectAnatomyProjection = Object.freeze({ projectCards });
})();
