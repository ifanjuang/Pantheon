(() => {
  "use strict";

  // Hierarchical edge bundling — the renderer for the support overlay
  // (corroboration / contradiction across Information + Documents + Knowledge).
  // Pure and deterministic (no force). Returns [] when there are no edges, so it
  // renders empty until the corroboration signal is wired.
  //
  // Nodes are placed on a ring, grouped contiguously by `groupOf`; edges bundle
  // toward group centroids via a cubic Bézier (beta controls bundling strength).

  function ringLayout(nodes, groupOf, cx, cy, r) {
    const keys = [];
    const byKey = new Map();
    for (const n of nodes) {
      const k = groupOf(n) || "—";
      if (!byKey.has(k)) { byKey.set(k, []); keys.push(k); }
      byKey.get(k).push(n);
    }
    const ordered = [];
    for (const k of keys) for (const n of byKey.get(k)) ordered.push(n);

    const pos = new Map();
    const N = ordered.length || 1;
    ordered.forEach((n, i) => {
      const a = (2 * Math.PI * i / N) - Math.PI / 2;
      pos.set(n.id, { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) });
    });

    const centroid = new Map();
    for (const k of keys) {
      const arr = byKey.get(k);
      const mx = arr.reduce((s, n) => s + pos.get(n.id).x, 0) / arr.length;
      const my = arr.reduce((s, n) => s + pos.get(n.id).y, 0) / arr.length;
      const ang = Math.atan2(my - cy, mx - cx);
      centroid.set(k, { x: cx + r * 0.42 * Math.cos(ang), y: cy + r * 0.42 * Math.sin(ang) });
    }
    return { pos, centroidOf: n => centroid.get(groupOf(n) || "—") || { x: cx, y: cy } };
  }

  function bundlePath(pa, pb, ca, cb, beta) {
    const b = beta == null ? 0.85 : beta;
    const mx = (pa.x + pb.x) / 2, my = (pa.y + pb.y) / 2;
    const c1 = { x: b * ca.x + (1 - b) * mx, y: b * ca.y + (1 - b) * my };
    const c2 = { x: b * cb.x + (1 - b) * mx, y: b * cb.y + (1 - b) * my };
    return `M ${pa.x} ${pa.y} C ${c1.x} ${c1.y} ${c2.x} ${c2.y} ${pb.x} ${pb.y}`;
  }

  function paths(nodes, edges, opts = {}) {
    if (!edges || !edges.length) return [];
    const groupOf = opts.groupOf || (() => "—");
    const cx = opts.cx != null ? opts.cx : (opts.width || 1000) / 2;
    const cy = opts.cy != null ? opts.cy : (opts.height || 620) / 2;
    const r = opts.r || Math.min(opts.width || 1000, opts.height || 620) * 0.42;
    const { pos, centroidOf } = ringLayout(nodes, groupOf, cx, cy, r);
    const byId = new Map(nodes.map(n => [n.id, n]));
    const out = [];
    for (const e of edges) {
      const a = pos.get(e.source), b = pos.get(e.target);
      if (!a || !b) continue;
      out.push({
        d: bundlePath(a, b, centroidOf(byId.get(e.source)), centroidOf(byId.get(e.target)), opts.beta),
        kind: e.kind, weight: e.weight || 1,
      });
    }
    return out;
  }

  window.PantheonMapBundle = Object.freeze({ ringLayout, bundlePath, paths });
})();
