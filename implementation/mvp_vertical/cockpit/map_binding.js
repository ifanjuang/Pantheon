(() => {
  "use strict";

  // Presentation-only glue for the read-only knowledge-map lens. This binding
  // owns the single Pantheon verso host so canonical and non-Swiper rendering
  // paths converge on the same graph mount. It never fetches or mutates
  // governed state.

  function buildTokens() {
    const icons = window.PantheonTagIcons;
    const NAMED = (window.PantheonMapTokens && window.PantheonMapTokens.NAMED) || {};
    const STATUS_COLOR = {
      draft: "slate", in_progress: "amber", running: "cyan", review: "amber",
      needs_review: "amber", pending_review: "amber", acted: "green", ready: "green",
      reviewed: "green", active: "green", done: "slate", waiting: "amber",
      conflict: "red", failed: "red", superseded: "slate", generated_unreviewed: "amber",
      neutral: "slate",
    };
    const hex = name => NAMED[name] || "#8b98a6";
    const present = subj => (subj && icons && icons.tagPresentation ? icons.tagPresentation(subj, "subject") : null);
    return {
      subjectColor: subj => { const p = present(subj); return p && p.color ? hex(p.color) : "#66758c"; },
      subjectIconKey: subj => { const p = present(subj); return p ? p.icon_key : null; },
      statusColor: st => hex(STATUS_COLOR[st] || "slate"),
      originStroke: origin =>
        origin === "hermes" ? { stroke: "#9aa4b4", dash: "4 3" }
        : origin === "knowledge" ? { stroke: "#6f7a8c", dash: "" }
        : { stroke: "#8492a8", dash: "" },
      radius: (m, b = 9) => (m > 1 ? Math.min(20, b + Math.sqrt(m) * 1.3) : b),
    };
  }

  function createLens() {
    const lens = document.createElement("section");
    lens.className = "card-map-lens v2-card-map-lens";
    lens.dataset.pantheonMapLens = "true";
    lens.setAttribute("aria-label", "Graphes de connaissance");

    const bar = document.createElement("div");
    bar.className = "card-map-bar v2-map-bar";

    const title = document.createElement("span");
    title.className = "card-map-title v2-map-title";
    title.textContent = "Graphes";
    bar.append(title);

    for (const [layout, label] of [
      ["cluster", "Cluster"],
      ["radial", "Radial"],
      ["grid", "Grille"],
      ["chain", "Chaîne"],
    ]) {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.mapLayout = layout;
      button.setAttribute("aria-pressed", String(layout === "cluster"));
      button.textContent = label;
      bar.append(button);
    }

    const supportLabel = document.createElement("label");
    supportLabel.className = "card-map-support v2-map-support";
    const support = document.createElement("input");
    support.type = "checkbox";
    support.dataset.mapSupportToggle = "true";
    supportLabel.append(support, document.createTextNode(" Corroboration"));
    bar.append(supportLabel);

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.classList.add("card-map-svg", "v2-map-svg");
    svg.dataset.pantheonMap = "true";
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", "Carte de connaissance");

    lens.append(bar, svg);
    return lens;
  }

  function ensureLens(card) {
    const existing = card.querySelector("[data-pantheon-map-lens]");
    if (existing) return existing;
    const back = card.querySelector(".card-back-body") || card.querySelector(".card-back");
    if (!back) return null;
    const lens = createLens();
    back.append(lens);
    return lens;
  }

  function init() {
    const stage = document.getElementById("v2-stage");
    if (!stage || !window.PantheonMapMount || typeof MutationObserver !== "function") return;

    const mounts = new Map();

    function destroyLens(lens) {
      const state = mounts.get(lens);
      if (!state) return;
      state.mount.destroy();
      mounts.delete(lens);
    }

    function mountLens(lens) {
      if (mounts.has(lens)) return;
      const svg = lens.querySelector("[data-pantheon-map]");
      if (!svg) return;

      const opts = { tokens: buildTokens(), layout: "cluster", groupBy: "subject" };
      const mount = window.PantheonMapMount.mountLive(svg, opts);
      mounts.set(lens, { mount, opts });

      lens.querySelectorAll("[data-map-layout]").forEach(button => {
        button.addEventListener("click", () => {
          const layout = button.dataset.mapLayout;
          opts.layout = layout;
          opts.groupBy = (layout === "radial" || layout === "chain") ? "family" : "subject";
          lens.querySelectorAll("[data-map-layout]").forEach(other =>
            other.setAttribute("aria-pressed", String(other === button)));
          if (mount.view) {
            mount.view.setGroupBy(opts.groupBy);
            mount.view.setLayout(layout);
          }
        });
      });

      const support = lens.querySelector("[data-map-support-toggle]");
      support?.addEventListener("change", () => {
        opts.support = support.checked;
        if (mount.view) mount.view.setSupport(support.checked);
      });
    }

    function sync() {
      const live = new Set();
      for (const card of stage.querySelectorAll('.card[data-family="pantheon"]')) {
        const lens = ensureLens(card);
        if (lens) live.add(lens);
      }
      for (const lens of mounts.keys()) {
        if (!live.has(lens)) destroyLens(lens);
      }
      for (const lens of live) mountLens(lens);
    }

    const observer = new MutationObserver(sync);
    observer.observe(stage, { childList: true, subtree: true });
    sync();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true });
  else init();
})();
