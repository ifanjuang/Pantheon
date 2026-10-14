(() => {
  "use strict";

  // Swappable layout registry — each strategy is a pure function
  //   (nodes, opts) -> { [id]: {x, y} }
  // No force, deterministic. opts: { width, height, groupOf(node) -> key }.
  // Adding a graph type = add one entry here; nothing else changes.

  function clump(members, cx, cy, pos, sp) {
    members.forEach((m, i) => {
      const r = sp * Math.sqrt(i + 0.55);
      const a = i * 2.399963229728653; // golden angle
      pos[m.id] = { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) };
    });
  }

  function groupBy(nodes, groupOf) {
    const groups = new Map();
    for (const n of nodes) {
      const key = groupOf(n) || "—";
      let bucket = groups.get(key);
      if (!bucket) { bucket = []; groups.set(key, bucket); }
      bucket.push(n);
    }
    return groups;
  }

  const REGISTRY = {
    // Organic clusters by group (subject by default).
    cluster(nodes, { width: W, height: H, groupOf }) {
      const pos = {};
      const groups = groupBy(nodes, groupOf);
      const keys = [...groups.keys()];
      const cols = Math.max(1, Math.ceil(Math.sqrt(keys.length)));
      const rows = Math.max(1, Math.ceil(keys.length / cols));
      keys.forEach((k, i) => {
        const c = i % cols, r = Math.floor(i / cols);
        clump(groups.get(k), W * (c + 0.5) / cols, 60 + (H - 120) * (r + 0.5) / rows, pos, 19);
      });
      return pos;
    },

    // Groups as satellites around an empty centre.
    radial(nodes, { width: W, height: H, groupOf }) {
      const pos = {};
      const groups = groupBy(nodes, groupOf);
      const keys = [...groups.keys()];
      const cx = W / 2, cy = H / 2, RR = Math.min(W, H) * 0.32;
      keys.forEach((k, i) => {
        const th = (2 * Math.PI * i / keys.length) - Math.PI / 2;
        clump(groups.get(k), cx + RR * Math.cos(th), cy + RR * Math.sin(th), pos, 19);
      });
      return pos;
    },

    // Dense row-major scan, contiguous by group.
    grid(nodes, { width: W, height: H, groupOf }) {
      const pos = {};
      const sorted = nodes.slice().sort((a, b) => String(groupOf(a)).localeCompare(String(groupOf(b))));
      const cols = Math.max(1, Math.round(Math.sqrt(sorted.length * (W / H))));
      const rows = Math.max(1, Math.ceil(sorted.length / cols));
      const x0 = 50, y0 = 56;
      const dx = cols > 1 ? (W - 2 * x0) / (cols - 1) : 0;
      const dy = rows > 1 ? (H - 2 * y0) / (rows - 1) : 0;
      sorted.forEach((n, i) => { pos[n.id] = { x: x0 + (i % cols) * dx, y: y0 + Math.floor(i / cols) * dy }; });
      return pos;
    },

    // Lineage rows: one lane per group, left-to-right.
    chain(nodes, { width: W, height: H, groupOf }) {
      const pos = {};
      const groups = groupBy(nodes, groupOf);
      const keys = [...groups.keys()];
      const laneH = keys.length > 1 ? (H - 100) / (keys.length - 1) : 0;
      const step = 34;
      const cols = Math.max(1, Math.floor((W - 140) / step));
      keys.forEach((k, li) => {
        const y = 60 + li * laneH;
        groups.get(k).forEach((n, i) => {
          pos[n.id] = { x: 120 + (i % cols) * step, y: y + Math.floor(i / cols) * step };
        });
      });
      return pos;
    },
  };

  function layout(name, nodes, opts) {
    const fn = REGISTRY[name] || REGISTRY.cluster;
    return fn(nodes, opts || {});
  }

  window.PantheonMapLayouts = Object.freeze({ names: Object.keys(REGISTRY), layout });
})();
