from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STRUCTURED_INTERFACE = ROOT / "mvp_vertical" / "cockpit" / "structured_interface.js"


def test_root_spaces_fail_closed_without_projection_definition() -> None:
    source = STRUCTURED_INTERFACE.read_text(encoding="utf-8")
    assert "Root card projection definition unavailable" in source
    assert "if (!definition)" in source


def test_non_root_cards_remain_on_generic_projection_path() -> None:
    source = STRUCTURED_INTERFACE.read_text(encoding="utf-8")
    assert 'input?.entity_type !== "cockpit_space"' in source
    assert "const rootDefinition = rootProjectionDefinition(input);" in source
    assert "if (rootDefinition) return buildRootProjection(rootDefinition);" in source
    for token in (
        "category: input.category ?? null",
        "type_tags: normalizeStringList(input.type_tags)",
        "subject_tags: normalizeStringList(input.subject_tags ?? input.tags",
        "presentation_family: input.presentation_family ?? presentationFamily(input)",
    ):
        assert token in source


def test_root_definition_controls_projection_metadata_through_builder() -> None:
    source = STRUCTURED_INTERFACE.read_text(encoding="utf-8")
    for token in (
        "role: definition.card_role",
        "family: definition.presentation_family",
        "presentation_family: definition.presentation_family",
        "category: definition.category",
        "title: definition.title",
        "summary: definition.summary",
        "status: definition.status",
        "definition.detail_rows",
    ):
        assert token in source
