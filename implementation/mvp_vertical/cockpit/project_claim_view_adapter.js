(() => {
  "use strict";

  const $ = id => document.getElementById(id);
  let schemaPromise = null;

  function token() {
    return $("v2-token")?.value || "";
  }

  async function request(path) {
    const response = await fetch(path, {
      headers: { Authorization: `Bearer ${token()}` },
      cache: "no-store",
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || response.statusText);
    return payload;
  }

  function schema() {
    if (!schemaPromise) {
      schemaPromise = request("../agency/schema/project")
        .then(payload => payload.schema || null)
        .catch(error => {
          schemaPromise = null;
          throw error;
        });
    }
    return schemaPromise;
  }

  function projectId(card) {
    const entityId = card.querySelector(".v2-entity-id")?.textContent?.trim() || "";
    return entityId.startsWith("project:") && !entityId.endsWith(":contacts")
      ? entityId.slice("project:".length)
      : "";
  }

  function hasValue(value) {
    return !(value == null || value === "" || (Array.isArray(value) && value.length === 0));
  }

  function formatValue(field, value) {
    if (Array.isArray(value)) return value.join(" · ");
    if (field?.unit === "EUR" && typeof value === "number") {
      return new Intl.NumberFormat("fr-FR", {
        style: "currency",
        currency: "EUR",
        maximumFractionDigits: 0,
      }).format(value);
    }
    if (field?.unit === "m²" && typeof value === "number") {
      return `${new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 2 }).format(value)} m²`;
    }
    return String(value);
  }

  function formatDateTime(value) {
    if (!value) return "";
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return String(value);
    return new Intl.DateTimeFormat("fr-FR", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(parsed);
  }

  function refsList(ref) {
    if (Array.isArray(ref)) return ref.filter(item => item && typeof item === "object");
    return ref && typeof ref === "object" ? [ref] : [];
  }

  function primaryRef(ref) {
    return refsList(ref)[0] || null;
  }

  function provenanceLabel(ref) {
    const first = primaryRef(ref);
    if (!first) return "";
    const backing = first.backing_ref || {};
    const provenance = first.provenance || {};
    const pieces = [
      first.status,
      first.certainty || null,
      backing.entity_type && backing.entity_id ? `${backing.entity_type}:${backing.entity_id}` : null,
      provenance.source_ref || null,
    ].filter(Boolean);
    return pieces.join(" · ");
  }

  function backingInformationId(ref) {
    const first = primaryRef(ref);
    const backing = first ? first.backing_ref || {} : {};
    return backing.entity_type === "information" && backing.entity_id ? String(backing.entity_id) : "";
  }

  function currentEntityId() {
    return $("v2-stage")?.querySelector(".v2-entity-id")?.textContent?.trim() || "";
  }

  function waitFrame() {
    return new Promise(resolve => requestAnimationFrame(() => resolve()));
  }

  async function navigateToInformation(informationId) {
    const target = `information:${informationId}`;
    const flip = $("v2-flip");
    const descend = $("v2-descend");
    const next = $("v2-next");
    if (!flip || !descend || !next) return false;

    const card = $("v2-stage")?.querySelector(".v2-card");
    if (card?.dataset.flipped === "true") {
      flip.click();
      await waitFrame();
    }
    descend.click();
    await waitFrame();
    if (currentEntityId() === target) return true;

    for (let index = 0; index < 250 && !next.disabled; index += 1) {
      next.click();
      await waitFrame();
      if (currentEntityId() === target) return true;
    }
    return false;
  }

  function appendProvenance(section, ref) {
    const label = provenanceLabel(ref);
    if (!label) return;

    const provenance = document.createElement("p");
    provenance.className = "v2-claim-provenance";
    provenance.textContent = `Provenance · ${label}`;
    section.dataset.claimProvenance = label;
    section.append(provenance);

    const informationId = backingInformationId(ref);
    if (!informationId) return;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "v2-claim-provenance-action";
    button.textContent = "Ouvrir la source";
    button.addEventListener("click", () => {
      void navigateToInformation(informationId).then(found => {
        if (!found) window.alert("L’Information source n’est pas disponible dans le scope Projet courant.");
      });
    });
    section.append(button);
  }

  function appendTemporalPerspective(section, ref) {
    const first = primaryRef(ref);
    if (!first) return;
    const pieces = [];
    if (first.observed_at) pieces.push(`observé ${formatDateTime(first.observed_at)}`);
    if (first.effective_at) pieces.push(`effectif ${formatDateTime(first.effective_at)}`);
    else pieces.push("effectivité métier non déclarée");
    if (!pieces.length) return;

    const temporal = document.createElement("p");
    temporal.className = "v2-claim-provenance";
    temporal.textContent = `Temporalité · ${pieces.join(" · ")}`;
    section.dataset.claimTemporalPerspective = pieces.join(" | ");
    section.append(temporal);
  }

  function basisMarker(item) {
    if (!item || typeof item !== "object") return "";
    const identity = item.entity_type && item.entity_id
      ? `${item.entity_type}:${item.entity_id}`
      : "";
    const details = [
      item.observed_revision != null ? `r${item.observed_revision}` : null,
      item.observed_status || null,
    ].filter(Boolean);
    return [identity, ...details].filter(Boolean).join(" · ");
  }

  function structuredBasis(ref) {
    const result = [];
    const seen = new Set();
    for (const claim of refsList(ref)) {
      const basisRefs = claim.provenance?.basis_refs;
      if (!Array.isArray(basisRefs)) continue;
      for (const basis of basisRefs) {
        const marker = basisMarker(basis);
        if (!marker || seen.has(marker)) continue;
        seen.add(marker);
        result.push(marker);
      }
    }
    return result;
  }

  function appendStructuredBasis(section, ref) {
    const basis = structuredBasis(ref);
    if (!basis.length) return;

    const details = document.createElement("details");
    details.className = "v2-claim-provenance";
    details.dataset.claimBasisCount = String(basis.length);
    const summary = document.createElement("summary");
    summary.textContent = `Bases structurées · ${basis.length}`;
    details.append(summary);
    for (const marker of basis) {
      const row = document.createElement("p");
      row.textContent = marker;
      details.append(row);
    }
    section.append(details);
  }

  function conflictLabel(classification) {
    if (classification === "value_conflict_same_effective_start") {
      return "valeurs différentes au même début d’effectivité";
    }
    if (classification === "value_conflict_undated") {
      return "valeurs différentes sans effectivité déclarée";
    }
    if (classification === "temporal_ambiguity") {
      return "ambiguïté temporelle à examiner";
    }
    return "tension à examiner";
  }

  function appendConflictCandidates(section, claimType, conflictCandidates) {
    const relevant = (Array.isArray(conflictCandidates) ? conflictCandidates : [])
      .filter(item => item && item.claim_type === claimType);
    if (!relevant.length) return;

    const labels = [...new Set(relevant.map(item => conflictLabel(item.classification)))];
    const conflict = document.createElement("p");
    conflict.className = "v2-claim-provenance";
    conflict.textContent = `À examiner · ${relevant.length} candidat${relevant.length > 1 ? "s" : ""} · ${labels.join(" · ")}`;
    section.dataset.claimConflictCandidates = relevant
      .map(item => item.conflict_candidate_id)
      .filter(Boolean)
      .join(",");
    section.append(conflict);
  }

  function appendConflictProjectionStatus(body, card, conflictProjection) {
    const status = conflictProjection?.status || "";
    card.dataset.claimConflictProjection = status || "unknown";
    if (status !== "unavailable") return;

    const section = document.createElement("section");
    section.className = "v2-back-section";
    section.dataset.projectClaimProjection = "conflict-status";
    const heading = document.createElement("h3");
    heading.textContent = "Tensions";
    const content = document.createElement("p");
    content.className = "v2-claim-provenance";
    content.textContent = "Analyse des tensions indisponible · absence de conflit non déduite";
    section.append(heading, content);
    body.append(section);
  }

  function renderProjection(card, project, projectSchema, claimPayload) {
    const body = card.querySelector(".v2-card-back .v2-back-body");
    if (!body) return;
    body.querySelectorAll("[data-project-claim-projection]").forEach(node => node.remove());

    const valuesSource = claimPayload?.claim_values || project.claim_values;
    const refsSource = claimPayload?.claim_refs || project.claim_refs;
    const values = valuesSource && typeof valuesSource === "object" ? valuesSource : {};
    const refs = refsSource && typeof refsSource === "object" ? refsSource : {};
    const conflictCandidates = Array.isArray(claimPayload?.conflict_candidates)
      ? claimPayload.conflict_candidates
      : [];
    const conflictProjection = claimPayload?.conflict_projection || null;

    if (claimPayload?.perspective?.mode) {
      card.dataset.claimPerspective = claimPayload.perspective.mode;
    }
    card.dataset.claimConflictCount = String(conflictCandidates.length);
    appendConflictProjectionStatus(body, card, conflictProjection);

    for (const field of projectSchema?.fields || []) {
      if (field.storage !== "projection" || field.semantics !== "claim") continue;
      const claimType = field.claim_type || field.key;
      const value = values[claimType];
      if (!hasValue(value)) continue;

      const section = document.createElement("section");
      section.className = "v2-back-section";
      section.dataset.projectClaimProjection = field.key;
      const heading = document.createElement("h3");
      heading.textContent = field.title || field.label || field.key;
      const content = document.createElement("p");
      content.textContent = formatValue(field, value);
      section.append(heading, content);
      appendTemporalPerspective(section, refs[claimType]);
      appendProvenance(section, refs[claimType]);
      appendStructuredBasis(section, refs[claimType]);
      appendConflictCandidates(section, claimType, conflictCandidates);
      body.append(section);
    }
  }

  async function enhance(card) {
    if (card.dataset.family !== "project" || card.dataset.claimProjectionState) return;
    const id = projectId(card);
    if (!id || !token()) return;
    card.dataset.claimProjectionState = "loading";
    try {
      const [projectSchema, payload, claimPayload] = await Promise.all([
        schema(),
        request(`../agency/projects/${encodeURIComponent(id)}`),
        request(`../agency/projects/${encodeURIComponent(id)}/claims`).catch(() => null),
      ]);
      renderProjection(card, payload.project || {}, projectSchema, claimPayload);
      card.dataset.claimProjectionState = "ready";
    } catch (error) {
      card.dataset.claimProjectionState = "error";
      card.dataset.claimProjectionError = error.message || String(error);
    }
  }

  function scan(root = document) {
    for (const card of root.querySelectorAll?.(".v2-card[data-family='project']") || []) {
      void enhance(card);
    }
  }

  function install() {
    const stage = $("v2-stage");
    if (!stage) return;
    scan(stage);
    new MutationObserver(() => scan(stage)).observe(stage, { childList: true, subtree: true });
    $("v2-load")?.addEventListener("click", () => { schemaPromise = null; });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install, { once: true });
  else install();
})();
