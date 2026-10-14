"""Regression checks for optional workspace organization and owner routing."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "docs" / "domain-packs" / "architecture" / "DOCUMENT_AND_KNOWLEDGE_ORGANIZATION.md"
INSPECTOR = ROOT / "docs" / "architecture" / "WORKSPACE_MANIFEST_INSPECTOR_CANDIDATE.md"
COCKPIT = ROOT / "docs" / "governance" / "PANTHEON_COCKPIT_STRUCTURED_AGENCY_INTERFACE.md"
OBSIDIAN = ROOT / "docs" / "governance" / "OBSIDIAN_HINDSIGHT_WORKSPACE_MODEL.md"
AUTHORITY = ROOT / "docs" / "governance" / "authority" / "ARCHITECTURE_AUTHORITY_INDEX.md"
REPOSITORY_INSTRUCTIONS = ROOT / "CLAUDE.md"
GRAPH_HEALTH_FIXTURE = ROOT / "tests" / "fixtures" / "obsidian_graph_health_pilot.json"
PIN_REGISTRY = ROOT / "implementation" / "qualification" / "external-pins.json"


def _numeric_version(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.removeprefix("v").split("."))


def test_workspace_organization_profile_remains_optional() -> None:
    owner = OWNER.read_text(encoding="utf-8")

    for invariant in (
        "recommended structure != mandatory structure",
        "folder/path != governed identity",
        "unclassified folder != invalid folder",
        "Hermes classification proposal != filesystem mutation",
        "Cockpit Space != required physical root folder",
    ):
        assert invariant in owner

    assert "Each project uses one shallow phase hierarchy" not in owner
    assert "Another existing organization remains usable" in owner


def test_workspace_changes_route_through_current_owners() -> None:
    instructions = REPOSITORY_INSTRUCTIONS.read_text(encoding="utf-8")

    for owner in (OWNER, INSPECTOR, COCKPIT, OBSIDIAN):
        assert owner.relative_to(ROOT).as_posix() in instructions

    authority = AUTHORITY.read_text(encoding="utf-8")
    assert OWNER.relative_to(ROOT).as_posix() in authority
    assert "optional recommended agency organization profile" in authority


def test_manifest_and_cockpit_consumers_preserve_optional_layout() -> None:
    inspector = INSPECTOR.read_text(encoding="utf-8")
    cockpit = COCKPIT.read_text(encoding="utf-8")
    owner_ref = OWNER.relative_to(ROOT).as_posix()

    assert owner_ref in inspector
    assert "another existing organization as usable" in inspector
    assert owner_ref in cockpit
    assert "not required physical root-folder names" in cockpit


def test_obsidian_second_brain_remains_optional_and_subordinate() -> None:
    obsidian = OBSIDIAN.read_text(encoding="utf-8")
    inspector = INSPECTOR.read_text(encoding="utf-8")
    instructions = REPOSITORY_INSTRUCTIONS.read_text(encoding="utf-8")

    for invariant in (
        "Neither is a Pantheon prerequisite, workspace owner, memory authority or manifest authority.",
        "Each layer is independently optional.",
        "silently mutate manifest or move files   = forbidden",
        "A missing manifest remains neutral",
    ):
        assert invariant in obsidian

    historical = inspector.split("## 19. Historical topology", 1)[1]
    assert "Obsidian" in historical
    assert "no longer required by the selected AFFAIRES target" in historical
    assert "optional unrelated workflows" in historical
    assert "an Obsidian/second-brain skill is not a workspace prerequisite" in instructions


def test_obsidian_second_brain_prefers_consolidation_over_note_proliferation() -> None:
    obsidian = OBSIDIAN.read_text(encoding="utf-8")

    for invariant in (
        "search-before-create",
        "create a new note only when no suitable existing note exists",
        "Conversation consolidation is explicit by default.",
        "unambiguous workspace-persistence intent",
        "Ambiguous retention wording such as `keep this` or `remember this` does not by itself select workspace persistence.",
        "The intended destination must be resolved before a durable workspace write.",
        "Consolidation is not transcript export",
        "must not silently persist ordinary conversation material",
    ):
        assert invariant in obsidian


def test_obsidian_distillation_reuses_existing_owners_and_keeps_maintenance_report_only() -> None:
    obsidian = OBSIDIAN.read_text(encoding="utf-8")

    for invariant in (
        "must not import `_staging`, `.manifest.json`, a trust ledger",
        "upstream trust ledger != Evidence or approval authority",
        "upstream graph query != replacement for bounded Hindsight retrieval",
        "report-only workspace audit",
        "It must not auto-fix, rename, merge, archive, relink or rewrite professional material.",
        "audit finding != defect confirmed",
        "duplicate candidate != merge authorization",
        "That local equilibrium is a workspace-health observation only",
        "`extracted`, `inferred` or `ambiguous`",
        "They do not introduce a new Pantheon provenance schema",
        "existing owner must be consumed rather than mirrored in frontmatter",
    ):
        assert invariant in obsidian


def test_obsidian_graph_health_qualification_is_advisory_and_bounded() -> None:
    obsidian = OBSIDIAN.read_text(encoding="utf-8")
    fixture = json.loads(GRAPH_HEALTH_FIXTURE.read_text(encoding="utf-8"))
    registry = json.loads(PIN_REGISTRY.read_text(encoding="utf-8"))
    pin = registry["pins"]["obsidian-wiki"]

    for invariant in (
        "upstream graph query != replacement for bounded Hindsight retrieval",
        "report-only workspace audit",
        "It must not auto-fix, rename, merge, archive, relink or rewrite professional material.",
        "audit finding != defect confirmed",
        "audit clean != professionally current",
        "duplicate candidate != merge authorization",
        "That local equilibrium is a workspace-health observation only",
    ):
        assert invariant in obsidian

    assert fixture["execution_status"] == "prepared_not_executed"
    assert fixture["capabilities"] == [
        "workspace_structural_analysis",
        "workspace_health_analysis",
    ]

    reference = fixture["reference_candidate"]
    assert reference["repository"] == pin["repository"]
    assert _numeric_version(reference["reviewed_release"]) == _numeric_version(pin["version"])
    assert reference["reviewed_release_sha"] == pin["ref"]
    assert reference["current_main_observation"]["sha"] == "37596cffeef43faecd9b61246b0b119b11a87bc4"
    assert reference["current_main_observation"]["multilingual_graph_query_fix"] == "427a9016b6aea04625133bd1a4ee00238c8c8518"
    assert "memory server" in reference["excluded_surfaces"]
    assert "provider manifest semantics" in reference["excluded_surfaces"]

    assert "observed_results" not in fixture
    assert "quality_score" not in fixture

    scope = fixture["workspace"]["authorized_scope"]
    assert scope["include_prefixes"] == ["projects/maison/"]
    assert scope["explicitly_out_of_scope_prefixes"] == ["projects/autre-projet/"]

    notes = {note["path"]: note for note in fixture["workspace"]["notes"]}
    sentinel = notes["projects/autre-projet/sentinel-hors-perimetre.md"]
    assert sentinel["role"] == "working_knowledge"
    assert "projects/maison/programme.md" in sentinel["links"]
    assert any("SCOPE_SENTINEL_7F3A" in claim for claim in sentinel["claims"])

    decisions_claim = notes["projects/maison/decisions.md"]["claims"][0]
    heating_claim = notes["projects/maison/chauffage.md"]["claims"][0]
    assert "Au 2026-08-30" in decisions_claim
    assert "Au 2026-08-30" in heating_claim
    assert "retenue" in decisions_claim and "retenue" in heating_claim
    assert "exclusivement" in decisions_claim and "exclusivement" in heating_claim
    assert decisions_claim != heating_claim

    valid_links_note = notes["projects/maison/liens-valides.md"]
    assert {
        "![[plan.pdf]]",
        "![[perspective.png]]",
        "[[planning.base]]",
        "[[schema.canvas]]",
        "[[cctp.md]]",
        "[[cctp#Menuiseries]]",
        "[[cctp|CCTP courant]]",
        "| [[chauffage\\|Chauffage]] |",
    } == set(valid_links_note["raw_markdown"])
    assert set(fixture["workspace"]["non_markdown_files"]) == {
        "projects/maison/plan.pdf",
        "projects/maison/perspective.png",
        "projects/maison/planning.base",
        "projects/maison/schema.canvas",
    }
    assert "Menuiseries" in notes["projects/maison/cctp.md"]["headings"]

    cases = {case["id"]: case for case in fixture["cases"]}
    assert {
        "bookkeeping_not_hub",
        "raw_staging_excluded",
        "bounded_shortest_path",
        "isolated_question",
        "broken_menuiseries_link",
        "valid_obsidian_links_not_broken",
        "heating_duplicate_candidate",
        "heating_contradiction_candidate",
        "bounded_scope",
        "protected_material_no_mutation",
    } == set(cases)

    assert "merge either note automatically" in cases["heating_duplicate_candidate"]["forbidden_claims_or_effects"]
    assert "create a stub automatically" in cases["broken_menuiseries_link"]["forbidden_claims_or_effects"]
    assert "rewrite a valid link during report-only analysis" in cases["valid_obsidian_links_not_broken"]["forbidden_claims_or_effects"]
    assert "silently search unrelated projects or provider-wide memory" in cases["bounded_scope"]["forbidden_claims_or_effects"]
    assert any("SCOPE_SENTINEL_7F3A" in effect for effect in cases["bounded_scope"]["forbidden_claims_or_effects"])
    assert "promote a lint or graph result to Evidence" in cases["protected_material_no_mutation"]["forbidden_claims_or_effects"]
    assert "Do not treat this fixture" in fixture["execution_gate"]["forbidden_shortcut"]
