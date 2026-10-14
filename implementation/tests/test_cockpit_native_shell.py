from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
PROJECTION = COCKPIT / "projection" / "cockpit_projection.js"
ASSEMBLER = COCKPIT / "projection" / "child_collection_assembler.js"
CANONICAL_RENDERER = COCKPIT / "rendering" / "card_renderer.js"
TAG_ICONS = COCKPIT / "rendering" / "tag_icons.js"
PROJECTION_MODULE = '"projection/cockpit_projection.js"'


def test_cockpit_uses_schema_renderer_without_presentation_adapter():
    bootstrap = (COCKPIT / "live_bootstrap.js").read_text(encoding="utf-8")
    assert PROJECTION_MODULE in bootstrap
    assert '"v2_' + 'app_schema.js"' not in bootstrap
    assert '"v2_app.js"' not in bootstrap
    assert '"v2_card_presentation.js"' not in bootstrap


def test_cockpit_loads_four_current_stylesheet_authorities():
    html = (COCKPIT / "index.html").read_text(encoding="utf-8")
    expected = ("cockpit.css", "cards.css", "families.css", "editors.css")
    for filename in expected:
        assert f'href="styles/{filename}"' in html
    for retired in ("v2.css", "v2_refinement.css", "v3_living_cards.css"):
        assert retired not in html

    cockpit = (COCKPIT / "styles" / "cockpit.css").read_text(encoding="utf-8")
    cards = (COCKPIT / "styles" / "cards.css").read_text(encoding="utf-8")
    assert "@layer reset, tokens, shell, navigation, cards, families, states, editors, responsive;" in cockpit
    assert ".card-back" in cards
    assert ".card-face" in cards
    assert ".card-body" in cards


def test_schema_renderer_exposes_one_contacts_card_per_project():
    projection = PROJECTION.read_text(encoding="utf-8")
    assembler = ASSEMBLER.read_text(encoding="utf-8")
    assert 'entity_type: "project_contacts"' in projection
    assert 'title: "Contacts"' in projection
    assert 'context.setChildren(contactsId, [])' in assembler
    assert "context.selected?.contacts" in assembler
    assert "normalizeParticipation" not in projection
    assert "/participations" not in projection


def test_schema_renderer_uses_unified_card_projection_fields():
    structured = (COCKPIT / "structured_interface.js").read_text(encoding="utf-8")
    renderer = CANONICAL_RENDERER.read_text(encoding="utf-8")
    for field in ("category", "index", "date", "author", "type_tags", "subject_tags", "limits", "available_actions"):
        assert field in structured
    assert "model.type_tags" in renderer
    assert "model.subject_tags" in renderer
    assert "model.limits" in renderer


def test_handoff_machine_identity_contract_is_preserved():
    renderer = CANONICAL_RENDERER.read_text(encoding="utf-8")
    handoff = (COCKPIT / "handoff" / "handoff_lifecycle.js").read_text(encoding="utf-8")
    assert 'machineIdentity.className = "card-entity-id v2-entity-id"' in renderer
    assert 'v2-card-kicker--machine' in renderer
    assert '.v2-entity-id' in handoff
    assert '.v2-card-back .v2-card-kicker' in handoff


def test_schema_renderer_keeps_type_subject_status_and_limits_separate():
    renderer = CANONICAL_RENDERER.read_text(encoding="utf-8")
    icons = TAG_ICONS.read_text(encoding="utf-8")
    assert "model.type_tags" in renderer
    assert "model.subject_tags" in renderer
    assert "model.status" in renderer
    assert "model.limits" in renderer
    assert 'new URL("../registries/tag_registry.json"' in icons
    assert 'registries = { type: new Map(), subject: new Map() }' in icons
    assert 'groupIds.has("type")' in icons
    assert 'groupIds.has("subject")' in icons
    assert "tagPresentation" in icons
