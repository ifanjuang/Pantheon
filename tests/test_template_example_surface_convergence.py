from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    "templates/TEMPLATE_MODEL.md",
    "docs/examples/README.md",
    "docs/examples/architecture_legal_module_panel/README.md",
)


def test_active_template_and_example_surfaces_have_no_openwebui_owner() -> None:
    for relative in TARGETS:
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "OpenWebUI" not in text, relative
        assert "OPENWEBUI_INTEGRATION.md" not in text, relative


def test_template_model_uses_existing_runtime_and_projection_owners() -> None:
    text = (ROOT / "templates/TEMPLATE_MODEL.md").read_text(encoding="utf-8")
    assert "Hermes Agent executes externally under Task Contract" in text
    assert "Hermes Web/dashboard" in text
    assert "Pantheon Cockpit" in text
    assert "projection != persistence" in text
    assert "provider selected != authority transfer" in text


def test_architecture_legal_panel_is_projection_not_authority() -> None:
    text = (
        ROOT / "docs/examples/architecture_legal_module_panel/README.md"
    ).read_text(encoding="utf-8")
    assert "Pantheon Cockpit Module Panel" in text
    assert "projection != persistence" in text
    assert "client selected != governance authority" in text
    assert "approve_plus_separate_retention_authorization" in text
