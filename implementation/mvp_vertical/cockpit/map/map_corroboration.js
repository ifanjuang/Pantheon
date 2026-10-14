(() => {
  "use strict";

  // Support overlay model — GATED on data that only exists once the signal is
  // wired. Corroboration is the positive end of the existing
  // contradictory_review support axis; today only the negative signal is
  // produced upstream, so this returns [] until cards carry support refs.
  //
  // Read-only, pure. `corroboration` never implies promotion: a certainty ring
  // is a candidate signal, not Evidence.

  function refs(card, ...keys) {
    for (const k of keys) {
      const v = card && card[k];
      if (Array.isArray(v) && v.length) return v;
    }
    return [];
  }

  function build(cards) {
    const entries = cards instanceof Map ? [...cards.entries()] : Object.entries(cards || {});
    const present = new Set(entries.map(([id]) => id));
    const edges = [];
    const seen = new Set();
    for (const [id, card] of entries) {
      if (!card) continue;
      for (const ref of refs(card, "corroboration_refs", "support_refs")) {
        if (!present.has(ref) || ref === id) continue;
        const key = "c:" + [id, ref].sort().join("|");
        if (seen.has(key)) continue;
        seen.add(key);
        edges.push({ source: id, target: ref, kind: "corroboration", weight: 1 });
      }
      for (const ref of refs(card, "contradiction_refs")) {
        if (!present.has(ref) || ref === id) continue;
        edges.push({ source: id, target: ref, kind: "contradiction", weight: 1 });
      }
    }
    return edges;
  }

  // Incoming corroboration count per node — a candidate certainty signal.
  function certainty(edges) {
    const m = new Map();
    for (const e of edges || []) {
      if (e.kind !== "corroboration") continue;
      m.set(e.source, (m.get(e.source) || 0) + e.weight);
      m.set(e.target, (m.get(e.target) || 0) + e.weight);
    }
    return m;
  }

  window.PantheonMapCorroboration = Object.freeze({ build, certainty });
})();
