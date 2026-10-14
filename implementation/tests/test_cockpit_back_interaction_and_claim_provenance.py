from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
HTML = COCKPIT / "index.html"
POLICY = COCKPIT / "interactions" / "interaction_policy.js"
CLAIMS = COCKPIT / "project_claim_view_adapter.js"
CLAIM_CSS = COCKPIT / "styles" / "editors.css"
PROJECTION_MODULE = '"projection/cockpit_projection.js"'


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_v2_loads_back_face_interaction_policy_after_renderer() -> None:
    bootstrap = _text(COCKPIT / "live_bootstrap.js")

    assert PROJECTION_MODULE in bootstrap
    assert '"interactions/interaction_policy.js"' in bootstrap
    assert bootstrap.index(PROJECTION_MODULE) < bootstrap.index('"interactions/interaction_policy.js"')


def test_back_face_blocks_spatial_swipe_and_keyboard_navigation_only() -> None:
    policy = _text(POLICY)

    assert 'currentCard()?.dataset.flipped === "true"' in policy
    assert 'stage.addEventListener("pointerdown", stopSpatialPointer, true)' in policy
    assert 'stage.addEventListener("pointerup", stopSpatialPointer, true)' in policy
    assert 'document.addEventListener("keydown", stopSpatialKeys, true)' in policy
    assert 'event.stopImmediatePropagation();' in policy
    assert '"v2-flip"' in policy
    assert 'const NAV_IDS = ["v2-previous", "v2-next", "v2-ascend", "v2-descend"]' in policy
    assert 'SPATIAL_KEYS = new Set(["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Enter"])' in policy
    assert '" "' not in policy


def test_project_claim_provenance_is_visible_and_can_open_backing_information() -> None:
    claims = _text(CLAIMS)

    assert 'provenance.textContent = `Provenance · ${label}`' in claims
    assert 'button.textContent = "Ouvrir la source"' in claims
    assert 'backing.entity_type === "information"' in claims
    assert 'const target = `information:${informationId}`' in claims
    assert 'descend.click();' in claims
    assert 'next.click();' in claims
    assert 'L’Information source n’est pas disponible dans le scope Projet courant.' in claims


def test_project_claim_projection_exposes_time_structured_basis_and_conflict_candidates() -> None:
    claims = _text(CLAIMS)

    assert 'request(`../agency/projects/${encodeURIComponent(id)}/claims`)' in claims
    assert 'temporal.textContent = `Temporalité · ${pieces.join(" · ")}`' in claims
    assert 'else pieces.push("effectivité métier non déclarée")' in claims
    assert 'summary.textContent = `Bases structurées · ${basis.length}`' in claims
    assert 'claim.provenance?.basis_refs' in claims
    assert 'conflict.textContent = `À examiner · ${relevant.length} candidat' in claims
    assert 'item.claim_type === claimType' in claims
    assert 'section.dataset.claimConflictCandidates' in claims
    assert 'card.dataset.claimPerspective = claimPayload.perspective.mode' in claims
    assert 'card.dataset.claimConflictCount = String(conflictCandidates.length)' in claims


def test_unavailable_conflict_projection_is_visible_and_does_not_imply_absence() -> None:
    claims = _text(CLAIMS)

    assert 'card.dataset.claimConflictProjection = status || "unknown"' in claims
    assert 'if (status !== "unavailable") return;' in claims
    assert 'heading.textContent = "Tensions"' in claims
    assert 'Analyse des tensions indisponible · absence de conflit non déduite' in claims
    assert 'section.dataset.projectClaimProjection = "conflict-status"' in claims


def test_claim_projection_falls_back_to_existing_project_cache_if_enriched_read_is_unavailable() -> None:
    claims = _text(CLAIMS)

    assert 'request(`../agency/projects/${encodeURIComponent(id)}/claims`).catch(() => null)' in claims
    assert 'const valuesSource = claimPayload?.claim_values || project.claim_values;' in claims
    assert 'const refsSource = claimPayload?.claim_refs || project.claim_refs;' in claims


def test_claim_provenance_remains_a_project_projection_not_a_claim_card() -> None:
    claims = _text(CLAIMS)

    assert 'section.dataset.projectClaimProjection = field.key' in claims
    assert 'data-project-claim-projection' in claims
    assert 'entity_type: "claim"' not in claims
    assert 'family: "claim"' not in claims


def test_claim_provenance_has_canonical_component_styles() -> None:
    css = _text(CLAIM_CSS)

    assert '.v2-claim-provenance' in css
    assert '.v2-claim-provenance-action' in css
    assert ':focus-visible' in css
