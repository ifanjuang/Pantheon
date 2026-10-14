(() => {
  "use strict";

  // Read-only token resolver: subject colour + icon, status colour, origin
  // border and magnitude→radius. Colour is never the sole identifier — a subject
  // icon disambiguates same-colour subjects (the registry collapses ~33 subjects
  // onto ~9 colour tokens). Dependency-injected: pass the real registries, or
  // fall back to a bundled palette. No fetch.

  const NAMED = Object.freeze({
    blue: "#5f83b8", green: "#3fae6d", amber: "#e0b84a", violet: "#9a6fc0",
    slate: "#8b98a6", cyan: "#4bb3c4", red: "#cf5b5b", orange: "#d98a4a", indigo: "#5b62b0",
  });

  function listOf(registry, key) {
    if (!registry) return [];
    if (Array.isArray(registry)) return registry;
    return registry[key] || [];
  }

  function create(opts = {}) {
    const named = Object.assign({}, NAMED, opts.namedColors || {});
    const tags = listOf(opts.tagRegistry, "tags");
    const statuses = listOf(opts.statusRegistry, "values");

    const subjColor = new Map();
    const subjIcon = new Map();
    for (const t of tags) {
      const slug = t && (t.slug || t.name);
      if (!slug) continue;
      const cname = t.presentation && t.presentation.color;
      if (cname) subjColor.set(slug, named[cname] || named.slate);
      const ic = t.presentation && t.presentation.icon_key;
      if (ic) subjIcon.set(slug, ic);
    }
    const statusColor = new Map();
    for (const s of statuses) {
      if (s && s.slug) statusColor.set(s.slug, named[s.color] || "#8592a8");
    }

    return {
      subjectColor: subj => subjColor.get(subj) || named.slate,
      subjectIconKey: subj => subjIcon.get(subj) || null,
      statusColor: st => statusColor.get(st) || "#8592a8",
      // Factual origin border — NOT an authority claim.
      originStroke: origin =>
        origin === "hermes" ? { stroke: "#9aa4b4", dash: "4 3" }
        : origin === "knowledge" ? { stroke: "#6f7a8c", dash: "" }
        : { stroke: "#3a4657", dash: "" },
      radius: (mag, base = 9) => (mag > 1 ? Math.min(20, base + Math.sqrt(mag) * 1.3) : base),
      named,
    };
  }

  window.PantheonMapTokens = Object.freeze({ create, NAMED });
})();
