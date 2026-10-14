from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_central_doctrine_has_no_openwebui_transition_owner() -> None:
    for relative in (
        "docs/governance/MODULES.md",
        "docs/governance/WATCHLIST.md",
        "docs/governance/DOMAIN_PACK_SPEC.md",
    ):
        text = _read(relative)
        assert "OPENWEBUI_INTEGRATION.md" not in text
        assert "OpenWebUI exposes" not in text


def test_watchlist_routes_current_ui_responsibilities_to_existing_owners() -> None:
    text = _read("docs/governance/WATCHLIST.md")
    assert "Runtime client/exposure pattern" in text
    assert "generic MCP exposure verification" in text
    assert "Governed Cockpit/Card projection pattern" in text
    assert "PANTHEON_COCKPIT_STRUCTURED_AGENCY_INTERFACE.md" in text


def test_domain_templates_do_not_create_client_specific_subsystem() -> None:
    text = _read("docs/governance/DOMAIN_PACK_SPEC.md")
    assert "CARD_STACK_MODEL.md" in text
    assert "does not create a client-specific template subsystem" in text
