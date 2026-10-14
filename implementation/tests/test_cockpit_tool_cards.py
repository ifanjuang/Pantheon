from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
PROJECTION = COCKPIT / "projection" / "cockpit_projection.js"
ASSEMBLER = COCKPIT / "projection" / "child_collection_assembler.js"
DATA_LOADER = COCKPIT / "data" / "cockpit_data_loader.js"
BOOTSTRAP = COCKPIT / "live_bootstrap.js"
RETIRED_DECORATOR = COCKPIT / "projection" / "tool_governance_projection.js"


def test_tool_space_is_driven_by_catalogue_not_legacy_static_containers():
    renderer = PROJECTION.read_text(encoding="utf-8")
    assembler = ASSEMBLER.read_text(encoding="utf-8")
    data_loader = DATA_LOADER.read_text(encoding="utf-8")

    assert 'toolCatalog: () => "tool_catalog.json"' in data_loader
    assert 'loadOptionalCollection(ROUTES.toolCatalog(), "items")' in data_loader
    assert "dataLoader.loadToolCatalog()" in renderer
    assert "state.toolCatalog" in renderer
    assert "state.toolCatalog.map(normalizeTool)" in renderer
    assert 'entity_id: `tool:${item.tool_id}`' in renderer
    assert "tools(context)" in assembler
    assert "return context.buildToolCards();" in assembler
    assert 'entity_id: "tools:capabilities"' not in renderer
    assert 'entity_id: "tools:hosts"' not in renderer


def test_tool_cards_keep_governance_axes_visibly_separate():
    renderer = PROJECTION.read_text(encoding="utf-8")

    for label in (
        "Installation",
        "État natif",
        "Santé observée",
        "Gouvernance",
        "Mise à jour",
        "Permissions",
        "Evidence attendue",
        "Rollback",
        "Prochaine décision humaine",
        "Binding exact",
        "Release immuable",
        "Activation",
        "Scope d’activation",
        "Compatibilité observée",
        "Sécurité qualifiée",
        "Fraîcheur observation",
        "Source observation",
    ):
        assert label in renderer

    assert 'item.governance_state === "candidate"' in renderer
    assert 'item.health_state === "observed_ready"' in renderer
    assert "runtime non observé ≠ non installé" in renderer


def test_exact_capability_projection_is_direct_and_never_infers_authority():
    renderer = PROJECTION.read_text(encoding="utf-8")
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")

    assert not RETIRED_DECORATOR.exists()
    assert '"projection/tool_governance_projection.js"' not in bootstrap
    assert "item.binding_id" in renderer
    assert "item.implementation_anchor" in renderer
    assert "item.activation_scope" in renderer
    assert "item.compatibility_status" in renderer
    assert "item.safety_status" in renderer
    assert "item.freshness_status" in renderer
    assert '"not_observed"' in renderer
    assert "binding sélectionné ≠ dépendance adoptée" in renderer
    assert "compatible ≠ activé" in renderer
    assert "UI projetée ≠ autorisation" in renderer


def test_tool_catalog_failure_does_not_invent_runtime_absence():
    renderer = PROJECTION.read_text(encoding="utf-8")
    data_loader = DATA_LOADER.read_text(encoding="utf-8")

    assert 'title: "Catalogue indisponible"' in renderer
    assert "Catalogue absent ≠ outil absent" in renderer
    assert "state.toolCatalog = await dataLoader.loadToolCatalog()" in renderer
    assert "return []" in data_loader
