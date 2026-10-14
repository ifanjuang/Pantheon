(() => {
  "use strict";

  async function start() {
    const params = new URLSearchParams(window.location.search);
    const isDemo = params.get("mode") === "demo";

    window.PANTHEON_COCKPIT_DEMO = isDemo;
    document.documentElement.dataset.cockpitMode = isDemo ? "demo" : "live";

    if (isDemo) await import("./demo_bootstrap.js");

    const tagIcons = await import("./rendering/tag_icons.js");
    await tagIcons.loadTagIconRegistries();

    const { loadNavigationRegistry } = await import("./projection/navigation_registry_loader.js");
    await loadNavigationRegistry();

    const { loadCardProjectionDefinitions } = await import("./projection/card_projection_definition_loader.js");
    await loadCardProjectionDefinitions();

    const { ensureSwiper } = await import("./navigation/swiper_loader.js");
    const swiperReady = await ensureSwiper();
    document.documentElement.dataset.cockpitNavigation = swiperReady ? "swiper" : "fallback";
    if (swiperReady) {
      await import("./live_collection_adapter.js");
    } else {
      for (const id of ["v2-previous", "v2-next"]) {
        const control = document.getElementById(id);
        if (control) control.hidden = false;
      }
    }

    const { ensureD3, d3Version } = await import("./visualization/d3_loader.js");
    window.PantheonD3Loader = Object.freeze({ ensureD3, d3Version });

    const { loadClassicScriptsInOrder } = await import("./boot/classic_script_loader.js");
    const scripts = [
      "shell_controls.js",
      "structured_interface.js",
      "context_resolver.js",
      "agency_data_binding.js",
      "spatial_navigation.js",
      "projection/navigation_registry_adapter.js",
      "projection/decision_request_projection.js",
      "projection/project_anatomy_projection.js",
      "projection/child_collection_assembler.js",
      "data/cockpit_data_loader.js",
      "projection/cockpit_projection.js",
      "interactions/interaction_policy.js",
      "project_claim_view_adapter.js",
      "information_view_adapter.js",
      "context/context_selection.js",
      "handoff/handoff_lifecycle.js",
      "handoff/handoff_send.js",
      "handoff/runtime_topology.js",
      "handoff/role_dialogue.js",
      "actions/card_actions.js",
      "actions/decision_request_actions.js",
      "actions/change_candidate_actions.js",
      "actions/change_candidate_review.js",
      "schema_editor.js",
      "contacts_editor.js",
      "information_create.js",
      "interactions/card_interactions.js",
      "map/map_graph_model.js",
      "map/map_layouts.js",
      "map/map_tokens.js",
      "map/map_corroboration.js",
      "map/map_bundle.js",
      "map/map_view.js",
      "map/map_mount.js",
      "map_binding.js",
    ];

    await loadClassicScriptsInOrder(scripts);

    if (isDemo && window.PantheonDemoBootstrap?.start) {
      await window.PantheonDemoBootstrap.start();
    }

    const network = document.getElementById("v2-network");
    if (network && window.matchMedia("(max-width: 620px)").matches && !swiperReady) {
      network.textContent = "navigation tactile simplifiée";
    }
  }

  start().catch(async error => {
    try {
      const { projectBootFailure } = await import("./shell/boot_failure.js");
      projectBootFailure(error);
    } catch (projectionError) {
      console.error(error, projectionError);
      document.documentElement.dataset.cockpitLoad = "failed";
    }
  });
})();
