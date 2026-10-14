(() => {
  "use strict";

  // Live mount hook — renders the map from the live projection snapshot exposed
  // by cockpit_projection.js as `window.PantheonCockpitGraph` (read-only
  // { cards, children }) and refreshed via the `pantheon:graph-updated` event.
  //
  // Read-only: it reads the snapshot and draws; it never writes back, fetches,
  // or triggers a run. Deferred wiring into the live page is done by the caller
  // (a single opt-in mount), keeping this module bounded.

  function mountLive(svg, opts = {}) {
    let view = null;

    function rebuild() {
      const graph = window.PantheonCockpitGraph;
      if (!graph || !graph.cards) return;
      if (view) view.destroy();
      view = window.PantheonMapView.create(svg, { cards: graph.cards, children: graph.children }, opts);
    }

    window.addEventListener("pantheon:graph-updated", rebuild);
    rebuild();

    return {
      rebuild,
      get view() { return view; },
      destroy() {
        window.removeEventListener("pantheon:graph-updated", rebuild);
        if (view) view.destroy();
        view = null;
      },
    };
  }

  window.PantheonMapMount = Object.freeze({ mountLive });
})();
