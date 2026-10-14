from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STRUCTURED_INTERFACE = ROOT / "mvp_vertical" / "cockpit" / "structured_interface.js"
COCKPIT_PROJECTION = ROOT / "mvp_vertical" / "cockpit" / "projection" / "cockpit_projection.js"


def test_root_projection_is_built_only_from_the_declared_definition() -> None:
    source = STRUCTURED_INTERFACE.read_text(encoding="utf-8")
    assert "function buildRootProjection(definition)" in source
    assert "if (rootDefinition) return buildRootProjection(rootDefinition);" in source
    assert "role: definition.card_role" in source
    assert "title: definition.title" in source
    assert "summary: definition.summary" in source
    assert "available_actions: []" in source


def test_root_input_metadata_cannot_survive_as_projection_fallback() -> None:
    source = STRUCTURED_INTERFACE.read_text(encoding="utf-8")
    root_start = source.index("function buildRootProjection")
    root_end = source.index("function buildCardProjection")
    root_builder = source[root_start:root_end]
    for token in (
        "input.role",
        "input.family",
        "input.category",
        "input.title",
        "input.summary",
        "input.status",
        "input.back",
        "input.available_actions",
    ):
        assert token not in root_builder


def test_historical_root_literals_are_non_authoritative_until_removed() -> None:
    projection = COCKPIT_PROJECTION.read_text(encoding="utf-8")
    interface = STRUCTURED_INTERFACE.read_text(encoding="utf-8")
    assert 'entity_type: "cockpit_space"' in projection
    assert "Root card projection definition unavailable" in interface
    assert "buildRootProjection(rootDefinition)" in interface
