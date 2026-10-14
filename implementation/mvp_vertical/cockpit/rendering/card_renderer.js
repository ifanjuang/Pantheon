import { createTagToken } from "./tag_icons.js";

const FAMILY_MARKS = Object.freeze({
  pantheon: "P",
  project: "A",
  information: "I",
  contact: "C",
  work: "W",
  decision: "D",
  tool: "#",
});

function stableVariant(value) {
  const input = String(value || "card");
  let hash = 0;
  for (let index = 0; index < input.length; index += 1) {
    hash = ((hash << 5) - hash + input.charCodeAt(index)) | 0;
  }
  return String((Math.abs(hash) % 3) + 1);
}

function presentationAxes(model) {
  const presentation = model?.presentation_family || model?.family || "information";
  const entityType = model?.entity_type || "information";
  const isPack = entityType === "cockpit_space";

  let family = presentation;
  if (["project", "work", "contact"].includes(presentation)) family = "affaires";
  if (presentation === "tool") family = "tools";

  let kind = entityType;
  if (["legacy_document", "document"].includes(entityType)) kind = "folder";
  if (presentation === "project") kind = "project";
  if (presentation === "work") kind = "work";

  return {
    family,
    level: isPack ? "pack" : entityType === "project" ? "booster" : "card",
    kind,
  };
}

function statusLabel(value) {
  return String(value || "neutral").replaceAll("_", " ");
}

function token(value, className, legacyClassName) {
  const node = document.createElement("span");
  node.className = `${className} ${legacyClassName}`;
  node.title = String(value);
  node.setAttribute("aria-label", String(value));
  const label = String(value);
  node.textContent = label.length <= 3 ? label.toUpperCase() : label.slice(0, 2).toUpperCase();
  return node;
}

function tagToken(value, kind, className, legacyClassName, labelled = false) {
  return createTagToken(value, kind, { className, legacyClassName, labelled });
}

function renderIdentity(model) {
  const identity = document.createElement("div");
  identity.className = "card-identity v2-card-identity";

  const line = document.createElement("div");
  line.className = "card-identity-line v2-card-identity-line";

  const mark = document.createElement("span");
  mark.className = "family-mark v2-family-mark v2-family-mark--identity";
  mark.textContent = FAMILY_MARKS[model.presentation_family] || "I";

  const category = document.createElement("span");
  category.className = "card-category v2-card-category";
  category.textContent = model.category || model.presentation_family || model.family;

  const typeTags = document.createElement("span");
  typeTags.className = "card-type-tags v2-card-type-tags";
  for (const tag of (model.type_tags || []).slice(0, 4)) {
    typeTags.append(tagToken(tag, "type", "type-tag", "v2-type-tag"));
  }

  line.append(mark, category, typeTags);

  const meta = document.createElement("div");
  meta.className = "card-meta v2-card-meta";
  meta.textContent = [model.index, model.date ? String(model.date).slice(0, 10) : null]
    .filter(Boolean)
    .join(" · ");

  identity.append(line, meta);
  return identity;
}

function renderStates(model) {
  const states = document.createElement("div");
  states.className = "card-states v2-card-states";
  states.append(token(statusLabel(model.status), "state-icon", "v2-state-icon"));
  for (const limit of (model.limits || []).slice(0, 3)) {
    states.append(token(limit, "state-icon", "v2-state-icon"));
  }
  return states;
}

function renderFront(model) {
  const face = document.createElement("div");
  face.className = "card-face card-front v2-card-face v2-card-front";

  const header = document.createElement("header");
  header.className = "card-top v2-card-top";
  header.append(renderIdentity(model), renderStates(model));

  const body = document.createElement("div");
  body.className = "card-body v2-card-body";
  if (model.front?.issuer) {
    const issuer = document.createElement("p");
    issuer.className = "card-kicker v2-card-kicker";
    issuer.textContent = model.front.issuer;
    body.append(issuer);
  }

  const title = document.createElement("h2");
  title.className = "card-title v2-card-title";
  title.textContent = model.title;

  const summary = document.createElement("p");
  summary.className = "card-summary v2-card-summary";
  summary.textContent = model.summary;
  body.append(title, summary);

  const footer = document.createElement("footer");
  footer.className = "card-footer v2-card-footer";
  const rail = document.createElement("div");
  rail.className = "indicator-rail v2-indicator-rail";
  for (const tag of (model.subject_tags || []).slice(0, 5)) {
    rail.append(tagToken(tag, "subject", "subject-tag-icon", "v2-subject-tag-icon"));
  }
  footer.append(rail);

  face.append(header, body, footer);
  return face;
}

function renderBackValue(value) {
  const node = document.createElement("p");
  const lines = String(value ?? "").split("\n").filter(Boolean);
  if (lines.length <= 1) {
    node.textContent = String(value ?? "");
    return node;
  }
  node.className = "card-back-multiline v2-back-multiline";
  for (const line of lines) {
    const span = document.createElement("span");
    span.textContent = line;
    node.append(span);
  }
  return node;
}

function renderBack(model) {
  const face = document.createElement("div");
  face.className = "card-face card-back v2-card-face v2-card-back";

  const header = document.createElement("header");
  header.className = "card-top v2-card-top";
  header.append(renderIdentity(model), renderStates(model));

  const machineKicker = document.createElement("span");
  machineKicker.className = "card-kicker v2-card-kicker v2-card-kicker--machine";
  machineKicker.textContent = `${model.family} · ${model.entity_type}`;
  machineKicker.hidden = true;
  header.append(machineKicker);

  const body = document.createElement("div");
  body.className = "card-back-body v2-back-body";
  const title = document.createElement("h2");
  title.className = "card-back-title v2-back-title";
  title.textContent = model.title;
  body.append(title);

  for (const [heading, value] of model.back || []) {
    const row = document.createElement("section");
    row.className = "card-back-section v2-back-section";
    const headingNode = document.createElement("h3");
    headingNode.textContent = heading;
    row.append(headingNode, renderBackValue(value));
    body.append(row);
  }

  const footer = document.createElement("footer");
  footer.className = "card-footer v2-card-footer";

  const actions = document.createElement("div");
  actions.className = "card-actions v2-card-actions";
  for (const action of model.available_actions || []) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = action;
    button.disabled = true;
    button.title = "L’action ne devient cliquable qu’après autorisation serveur";
    actions.append(button);
  }

  const labels = document.createElement("div");
  labels.className = "card-back-tags v2-back-tag-labels";
  for (const tag of model.subject_tags || []) {
    labels.append(tagToken(tag, "subject", "card-back-tag", "v2-back-tag-label", true));
  }

  const machineIdentity = document.createElement("span");
  machineIdentity.className = "card-entity-id v2-entity-id";
  machineIdentity.textContent = model.entity_id;
  machineIdentity.hidden = true;

  footer.append(actions, labels, machineIdentity);
  face.append(header, body, footer);
  return face;
}

export function renderCanonicalCard(model, { flipped = false } = {}) {
  const axes = presentationAxes(model);
  const wrapper = document.createElement("article");
  wrapper.className = "card v2-card";
  wrapper.dataset.family = axes.family;
  wrapper.dataset.level = axes.level;
  wrapper.dataset.kind = axes.kind;
  wrapper.dataset.role = model.role || "entity";
  wrapper.dataset.status = model.status || "neutral";
  wrapper.dataset.variant = stableVariant(model.entity_id);
  wrapper.dataset.flipped = flipped ? "true" : "false";
  if (model.base_acted_id) wrapper.dataset.baseActedId = model.base_acted_id;

  const accent = model.identity_accent;
  if (accent) {
    wrapper.style.setProperty("--identity-accent", accent);
    wrapper.style.setProperty("--project-accent", accent);
  }

  const inner = document.createElement("div");
  inner.className = "card-inner v2-card-inner";
  inner.append(renderFront(model), renderBack(model));
  wrapper.append(inner);
  return wrapper;
}
