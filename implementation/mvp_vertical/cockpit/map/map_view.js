(() => {
  "use strict";

  // Read-only SVG renderer for the Cockpit knowledge map.
  //
  // Boundary (map/README.md): binds to the projection (state.cards /
  // state.children), reshapes and draws only. No fetch, no mutation, no run
  // launch, no memory promotion.
  //
  // Layers (all read-only, several data-gated):
  //   - subject colour + icon (tokens; colour is never the sole identifier)
  //   - origin border (factual source, not authority) · status badge
  //   - magnitude sizing (pages/chunks) · organic metaballs
  //   - containment + version lineage links
  //   - support overlay (corroboration/contradiction) via hierarchical edge
  //     bundling — renders empty until the corroboration signal is wired
  //   - subject focus · time scrubber (accretion)

  const NS = "http://www.w3.org/2000/svg";
  let SEQ = 0;

  // Compact subject glyph sheet (inline SVG; the CSP blocks font CDNs). Colour
  // identifies the token; the icon disambiguates same-colour subjects.
  const GLYPH = {
    surfaces: "M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5",
    assurance: "M12 3l7 3v5c0 5-7 9-7 9s-7-4-7-9V6z",
    responsabilite: "M12 4v16M6 20h12M4 9h16M7 9l-3 6h6zM17 9l-3 6h6z",
    budget: "M15 8a5 5 0 100 8M6 11h8M6 14h7",
    cctp: "M7 3h7l4 4v14H7zM14 3v4h4M9 12h6M9 15h6",
    plan: "M4 6l5-2 6 2 5-2v14l-5 2-6-2-5 2zM9 4v16M15 6v16",
    reservations: "M6 5h12v14H6zM9 11l2 2 4-4",
    structure: "M5 5h14M5 19h14M12 5v14",
    accessibilite: "M12 8v6M8 10h8M9 14l-1 5M15 14l1 5",
    sinistre: "M12 4l9 16H3zM12 10v5M12 17.5v.1",
  };

  function el(name, attrs) {
    const node = document.createElementNS(NS, name);
    if (attrs) for (const k in attrs) node.setAttribute(k, attrs[k]);
    return node;
  }

  function create(svg, data, opts = {}) {
    const width = opts.width || 1000;
    const height = opts.height || 620;
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    const model = window.PantheonMapGraphModel;
    const layouts = window.PantheonMapLayouts;
    const corroboration = window.PantheonMapCorroboration;
    const bundle = window.PantheonMapBundle;
    if (!model || !layouts) throw new Error("Map model/layouts unavailable");

    const tokens = opts.tokens || (window.PantheonMapTokens && window.PantheonMapTokens.create(opts)) || {
      subjectColor: () => "#66758c", subjectIconKey: () => null, statusColor: () => "#8592a8",
      originStroke: () => ({ stroke: "#3a4657", dash: "" }), radius: (m, b = 9) => b,
    };

    const graph = model.build(data.cards, data.children);
    const supportEdges = corroboration ? corroboration.build(data.cards) : [];

    const state = {
      layout: opts.layout || "cluster",
      groupBy: opts.groupBy || "subject",
      lens: opts.lens !== false,
      meta: opts.meta !== false,
      support: !!opts.support,
      focus: null,
      timeMax: null,
    };
    const groupOf = n => (state.groupBy === "family" ? (n.family || "—") : (n.subject || "—"));
    const arrived = n => state.timeMax == null || !n.date || String(n.date) <= state.timeMax;

    // defs: per-instance metaball filter + subject symbols
    const uid = "map" + (SEQ += 1);
    const defs = el("defs");
    defs.innerHTML =
      `<filter id="${uid}-goo" x="-20%" y="-20%" width="140%" height="140%">` +
      `<feGaussianBlur in="SourceGraphic" stdDeviation="11" result="b"/>` +
      `<feColorMatrix in="b" type="matrix" values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 22 -9" result="goo"/>` +
      `<feMorphology in="goo" operator="dilate" radius="3" result="grown"/>` +
      `<feColorMatrix in="grown" type="matrix" values="0.55 0 0 0 0 0 0.55 0 0 0 0 0 0.55 0 0 0 0 0 22 -9" result="rim"/>` +
      `<feComposite in="goo" in2="rim" operator="over"/></filter>` +
      Object.entries(GLYPH).map(([k, d]) =>
        `<symbol id="${uid}-ic-${k}" viewBox="0 0 24 24"><path d="${d}" fill="none" stroke="#fff" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/></symbol>`).join("");
    svg.append(defs);

    const gMeta = el("g", { filter: `url(#${uid}-goo)`, opacity: "0.5" });
    const gSupport = el("g", { "data-layer": "support", fill: "none" });
    const gLinks = el("g", { "data-layer": "links" });
    const gNodes = el("g", { "data-layer": "nodes" });
    const gLabels = el("g", { "data-layer": "labels" });
    svg.append(gMeta, gSupport, gLinks, gNodes, gLabels);

    const nodeEls = new Map();
    for (const n of graph.nodes) {
      const mb = el("circle");
      gMeta.append(mb);
      const g = el("g", { "data-id": n.id, tabindex: "0", role: "button" });
      g.setAttribute("aria-label", n.title);
      const c = el("circle", { "stroke-width": 1.6 });
      let icon = null;
      if (GLYPH[n.subject]) { icon = el("use", { href: `#${uid}-ic-${n.subject}` }); icon.style.pointerEvents = "none"; }
      const dot = el("circle", { r: 3.4, stroke: "#fff", "stroke-width": 1.2 });
      const title = el("title");
      title.textContent = `${n.title}${n.subject ? " · " + n.subject : ""}`;
      g.append(c, ...(icon ? [icon] : []), dot, title);
      gNodes.append(g);
      nodeEls.set(n.id, { g, c, dot, icon, mb, n });
    }

    const linkEls = graph.links.map(link => {
      const line = el("line", {
        "data-kind": link.kind,
        stroke: link.kind === "lineage" ? "#5f83b8" : "#c3cbd8",
        "stroke-width": link.kind === "lineage" ? 1.6 : 1,
      });
      gLinks.append(line);
      return { line, ...link };
    });

    function fillOf(n) { return state.lens ? tokens.subjectColor(n.subject) : "#66758c"; }
    function radiusOf(n) { return tokens.radius(n.magnitude || 1); }

    function render() {
      const pos = layouts.layout(state.layout, graph.nodes, { width, height, groupOf });
      for (const [id, e] of nodeEls) {
        const p = pos[id] || { x: width / 2, y: height / 2 };
        const r = radiusOf(e.n);
        e.x = p.x; e.y = p.y; e.r = r;
        e.g.setAttribute("transform", `translate(${p.x} ${p.y})`);
        e.c.setAttribute("r", r);
        e.c.setAttribute("fill", fillOf(e.n));
        const os = tokens.originStroke(e.n.origin);
        e.c.setAttribute("stroke", os.stroke);
        e.c.setAttribute("stroke-dasharray", os.dash);
        if (e.icon) {
          const s = Math.min(13, Math.max(9, r * 1.05));
          e.icon.setAttribute("width", s); e.icon.setAttribute("height", s);
          e.icon.setAttribute("x", -s / 2); e.icon.setAttribute("y", -s / 2);
          e.icon.style.display = state.lens ? "" : "none";
        }
        e.dot.setAttribute("cx", r * 0.74); e.dot.setAttribute("cy", -r * 0.74);
        e.dot.setAttribute("fill", tokens.statusColor(e.n.status));
        const dim = (state.focus && e.n.subject !== state.focus) || !arrived(e.n);
        e.g.style.opacity = dim ? 0.08 : (e.n.origin === "hermes" ? 0.85 : 1);
      }
      for (const l of linkEls) {
        const a = nodeEls.get(l.source), b = nodeEls.get(l.target);
        const show = a && b && arrived(a.n) && arrived(b.n);
        l.line.style.display = show ? "" : "none";
        if (show) { l.line.setAttribute("x1", a.x); l.line.setAttribute("y1", a.y); l.line.setAttribute("x2", b.x); l.line.setAttribute("y2", b.y); }
      }
      renderMeta(pos);
      renderSupport();
      renderLabels(pos);
    }

    function renderMeta(pos) {
      const on = state.meta && (state.layout === "cluster" || state.layout === "radial");
      gMeta.style.display = on ? "" : "none";
      if (!on) return;
      for (const [id, e] of nodeEls) {
        const show = (!state.focus || groupOf(e.n) === state.focus) && arrived(e.n);
        e.mb.setAttribute("r", radiusOf(e.n) + 5);
        e.mb.setAttribute("cx", pos[id] ? pos[id].x : width / 2);
        e.mb.setAttribute("cy", pos[id] ? pos[id].y : height / 2);
        e.mb.setAttribute("fill", state.groupBy === "family" ? "#8b98a6" : tokens.subjectColor(e.n.subject));
        e.mb.style.display = show ? "" : "none";
      }
    }

    function renderSupport() {
      gSupport.textContent = "";
      if (!state.support || !bundle) return;
      const visible = graph.nodes.filter(arrived);
      const edges = supportEdges.filter(x => arrived(nodeEls.get(x.source)?.n || {}) && arrived(nodeEls.get(x.target)?.n || {}));
      const paths = bundle.paths(visible, edges, { width, height, groupOf, r: Math.min(width, height) * 0.4 });
      for (const p of paths) {
        gSupport.append(el("path", {
          d: p.d, fill: "none",
          stroke: p.kind === "contradiction" ? "#cf5b5b" : "#3fae6d",
          "stroke-width": Math.min(3, 1 + p.weight * 0.5), "stroke-opacity": 0.5,
        }));
      }
    }

    function renderLabels(pos) {
      gLabels.textContent = "";
      const groups = new Map();
      for (const n of graph.nodes) {
        if (!arrived(n)) continue;
        const k = groupOf(n);
        let b = groups.get(k); if (!b) { b = []; groups.set(k, b); }
        b.push(pos[n.id] || { x: width / 2, y: height / 2 });
      }
      for (const [k, pts] of groups) {
        if (!pts.length) continue;
        const cx = pts.reduce((s, p) => s + p.x, 0) / pts.length;
        const minY = Math.min(...pts.map(p => p.y));
        const faded = state.focus && k !== state.focus;
        const t = el("text", { x: cx, y: Math.max(14, minY - 18), "text-anchor": "middle", "font-size": 11, "font-family": "ui-monospace, monospace", fill: "#6c7789", opacity: faded ? 0.3 : 1 });
        t.textContent = `${k} · ${pts.length}`;
        gLabels.append(t);
      }
    }

    render();

    return {
      setLayout(name) { state.layout = name; render(); },
      setGroupBy(mode) { state.groupBy = mode; render(); },
      setLens(on) { state.lens = !!on; render(); },
      setMeta(on) { state.meta = !!on; render(); },
      setSupport(on) { state.support = !!on; render(); },
      setFocus(subject) { state.focus = subject || null; render(); },
      setTime(isoOrNull) { state.timeMax = isoOrNull || null; render(); },
      render,
      graph,
      supportEdges,
      destroy() { svg.textContent = ""; nodeEls.clear(); },
    };
  }

  window.PantheonMapView = Object.freeze({ create });
})();
