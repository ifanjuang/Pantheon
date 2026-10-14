from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
RENDERER = COCKPIT / "projection" / "cockpit_projection.js"
ASSEMBLER = COCKPIT / "projection" / "child_collection_assembler.js"
CREATE_INFORMATION = COCKPIT / "information_create.js"
FAMILIES_CSS = COCKPIT / "styles" / "families.css"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_contacts_remain_one_grouped_card_with_scrollable_back() -> None:
    renderer = _text(RENDERER)
    css = _text(FAMILIES_CSS)

    assert 'entity_type: "project_contacts"' in renderer
    assert 'title: "Contacts"' in renderer
    assert 'values.map(contactDisplay).join("\\n")' in renderer
    assert '[data-family="contact"] .card-back-body {' in css
    assert 'overflow-y: auto;' in css


def test_change_candidate_decision_exposes_review_context() -> None:
    renderer = _text(RENDERER)

    assert 'category: "Décision · Modification"' in renderer
    assert '["Proposition", changes.map(candidateChangeLine).join("\\n")' in renderer
    assert '["Proposé par",' in renderer
    assert '["Révision de base",' in renderer
    assert '["Sources", (item.source_refs || []).join("\\n")' in renderer
    assert 'available_actions: item.status === "pending_review" ? ["Refuser", "Valider"] : []' in renderer


def test_tool_card_keeps_runtime_and_governance_axes_separate() -> None:
    renderer = _text(RENDERER)

    for label in (
        "Installation",
        "État natif",
        "Santé observée",
        "Gouvernance",
        "Activation",
        "Scope d’activation",
        "Mise à jour",
        "Permissions",
        "Evidence attendue",
        "Rollback",
        "Prochaine décision humaine",
    ):
        assert f'["{label}",' in renderer
    assert '["Activation scope",' not in renderer
    assert 'Catalogue absent ≠ outil absent · runtime non observé ≠ non installé.' in renderer


def test_known_gap_new_information_is_not_yet_a_spatial_child() -> None:
    assembler = _text(ASSEMBLER)
    creator = _text(CREATE_INFORMATION)

    assert 'body.append(blankCard())' in creator
    assert "...context.state.information.map(context.normalizeInformation)" in assembler
    assert "context.setChildren(context.selectedCardId" in assembler
    assert "new-information" not in assembler


def test_known_gap_project_claim_provenance_is_stored_but_not_rendered() -> None:
    renderer = _text(RENDERER)

    assert 'item.claim_values?.[field.key]' in renderer
    project_rows = renderer[renderer.index("function projectSchemaRows"):renderer.index("function informationTimestamp")]
    assert "claim_refs" not in project_rows
