from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
ACTIONS = COCKPIT / "actions" / "card_actions.js"
EDITOR = COCKPIT / "schema_editor.js"
DOMAIN = ROOT / "mvp_vertical" / "agency_information.py"


def test_information_actions_keep_lifecycle_outside_generic_editor() -> None:
    actions = ACTIONS.read_text(encoding="utf-8")
    editor = EDITOR.read_text(encoding="utf-8")

    assert 'if (label === "Acter") return actInformation();' in actions
    assert 'if (label === "Nouvelle version") return deriveInformation();' in actions
    assert 'openInformation(informationId)' in editor
    assert '"/act"' not in editor
    assert '"/working-version"' not in editor


def test_information_actions_recheck_server_state_before_specialized_effects() -> None:
    actions = ACTIONS.read_text(encoding="utf-8")

    assert "async function informationContextForCurrent()" in actions
    assert "const { id, title, current } = await informationContextForCurrent();" in actions
    assert "const { id, title, current: acted } = await informationContextForCurrent();" in actions
    assert '["draft", "in_progress"].includes(current.status)' in actions
    assert 'acted.status !== "acted"' in actions
    assert "expected_revision: current.revision" in actions


def test_information_actions_do_not_turn_hermes_prepare_into_execution_or_approval() -> None:
    actions = ACTIONS.read_text(encoding="utf-8")

    assert '$("v2-handoff-prepare")?.click()' in actions
    assert '$("v2-handoff-submit")?.click()' not in actions
    assert '$("v2-handoff-admit")?.click()' not in actions
    assert '$("v2-handoff-revoke")?.click()' not in actions
    assert "/runs/start" not in actions


def test_information_domain_remains_authoritative_for_acted_and_version_gates() -> None:
    domain = DOMAIN.read_text(encoding="utf-8")

    assert 'raise InformationGateRequired("only a human may act an Information version")' in domain
    assert 'raise ImmutableActedInformation("acted or superseded Information cannot be edited")' in domain
    assert 'raise InformationGateRequired("Hermes cannot create the next source version directly")' in domain
