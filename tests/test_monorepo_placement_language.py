from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_active_work_rules_close_initial_import_compatibility_debt() -> None:
    text = _read("CLAUDE.md")

    assert "compatibility debt created by the initial `pantheon-mvp` import is closed" in text
    assert "initial import may temporarily retain vendored governance snapshots" not in text
    assert "Do not reintroduce vendored governance snapshots" in text


def test_current_implementation_placement_is_monorepo_native() -> None:
    placement = _read("docs/governance/NEXT_MVP_REPOSITORY_PLACEMENT.md")
    tool_card = _read("docs/governance/TOOL_CARD_MODEL.md")
    registry = _read("registries/README.md")

    assert "Pantheon implementation" in placement
    assert "implementation/" in placement
    assert "Pantheon implementation under `implementation/`" in tool_card
    assert "implementation/mvp_vertical/cockpit/registries/" in registry

    assert "belongs in `pantheon-mvp`" not in tool_card
    assert "`pantheon-mvp` may own operational instances" not in registry
    assert "validate the existing pantheon-mvp tag instance against a vendored reference" not in registry


def test_hermes_templates_review_current_monorepo_consumers() -> None:
    readme = _read("templates/hermes/README.md")
    design = _read("templates/hermes/DESIGN.md")
    claude = _read("templates/hermes/CLAUDE.md")

    assert "current co-located consumers under `implementation/`" in readme
    assert "former `pantheon-mvp/main` remains historical provenance" in readme
    assert "current `pantheon-mvp/main`" not in readme
    assert "current `pantheon-mvp/main`" not in claude
    assert "- `pantheon-mvp`: candidate PostgreSQL/API/Cockpit implementation" not in design


def test_hermes_templates_use_current_hosting_owners() -> None:
    skills = _read("templates/hermes/SKILLS.md")
    design = _read("templates/hermes/DESIGN.md")
    claude = _read("templates/hermes/CLAUDE.md")

    for text in (skills, design, claude):
        assert "HERMES_CODE_HOSTING_BOUNDARY.md" not in text
        assert "NEXT_MVP_REPOSITORY_PLACEMENT.md" in text
        assert "HERMES_INTEGRATION.md" in text

    assert "Executable scripts, installers, provider routers, queues and schedulers do not belong in this template surface." in skills
    assert "External Hermes execution boundary" in design
    assert "Hermes runtime code and execution remain external" in claude


def test_cockpit_orientation_points_to_co_located_candidate() -> None:
    assets = _read("docs/assets/README.md")
    card_stack = _read("docs/assets/card-stack/README.md")
    control_readme = _read("docs/assets/pantheon-control/README.md")
    control_index = _read("docs/assets/pantheon-control/index.html")
    control_boundary = _read("docs/governance/PANTHEON_CONTROL_BOUNDARY.md")

    for text in (assets, card_stack, control_readme, control_index, control_boundary):
        assert "implementation/mvp_vertical/cockpit" in text

    assert "Product cockpit screens, executable product renderers, synthetic project data and runtime scenarios belong in `ifanjuang/pantheon-mvp`" not in assets
    assert "implemented cards-first frontend is owned by the external `ifanjuang/pantheon-mvp`" not in card_stack
    assert "Le cockpit candidat vit dans <code>pantheon-mvp</code>" not in control_index
    assert "Executable candidate cockpit and demo scenarios | external repository `ifanjuang/pantheon-mvp`" not in control_boundary
    assert "`PANTHEON_MCP_POLICY_SERVER_DEVELOPMENT.md`" not in control_boundary


def test_historical_repository_name_remains_valid_provenance() -> None:
    placement = _read("docs/governance/NEXT_MVP_REPOSITORY_PLACEMENT.md")
    card_stack = _read("docs/assets/card-stack/README.md")

    assert "former repository = ifanjuang/pantheon-mvp" in placement
    assert "source cutoff      = d960862dd0e23b7003a0f3e4ee0ea630ffc12af9" in placement
    assert "historical commit: 4ee41a845ec51db3118a584db0411a300450ccbd" in card_stack


def test_retired_external_vertical_binding_stays_out_of_active_governance() -> None:
    retired = ROOT / "docs/governance/PANTHEON_MVP_VERTICAL_BINDING.md"
    assert not retired.exists()

    active_sources = (
        "docs/governance/README.md",
        "docs/governance/STATUS.md",
        "docs/governance/authority/RUNTIME_ADAPTERS_AUTHORITY_INDEX.md",
    )
    for relative in active_sources:
        assert "PANTHEON_MVP_VERTICAL_BINDING.md" not in _read(relative)

    obsolete = _read("docs/governance/authority/OBSOLETE_AND_ABSENT_INDEX.md")
    reviews = _read("docs/governance/reference_reviews/README.md")
    assert "`PANTHEON_MVP_VERTICAL_BINDING.md` (removed; Pantheon-Next archive)" in obsolete
    assert "superseded / historical provenance" in reviews
    assert "NEXT_MVP_REPOSITORY_PLACEMENT.md" in reviews


def test_active_mcp_owners_do_not_reference_retired_policy_server_docs() -> None:
    modules = _read("docs/governance/MODULES.md")
    hermes = _read("docs/governance/HERMES_INTEGRATION.md")

    for text in (modules, hermes):
        assert "MCP_POLICY_SERVER_CANDIDATE.md" not in text
        assert "PANTHEON_MCP_POLICY_SERVER_DEVELOPMENT.md" not in text

    assert "`MCP_PANTHEON_MINIMAL_PROFILE.md`, `mcp-server/docs/HTTP_API_CONTRACT.md`, `mcp-server/`" in modules
    assert "The current Pantheon decision interface is the bounded policy service described by `mcp-server/docs/HTTP_API_CONTRACT.md`" in hermes


def test_retired_cockpit_reconciliation_stays_out_of_active_governance() -> None:
    retired = ROOT / "docs/governance/PANTHEON_MVP_COCKPIT_RECONCILIATION.md"
    assert not retired.exists()

    lifecycle = _read("docs/governance/DOCUMENT_LIFECYCLE_GOVERNANCE.md")
    runtime_index = _read("docs/governance/authority/RUNTIME_ADAPTERS_AUTHORITY_INDEX.md")
    obsolete = _read("docs/governance/authority/OBSOLETE_AND_ABSENT_INDEX.md")

    assert "PANTHEON_MVP_COCKPIT_RECONCILIATION.md" not in lifecycle
    assert "PANTHEON_MVP_COCKPIT_RECONCILIATION.md" not in runtime_index
    assert "Pantheon implementation under `implementation/`" in lifecycle
    assert "Historical `pantheon-mvp` commits or PRs remain provenance only" in lifecycle
    assert "`PANTHEON_MVP_COCKPIT_RECONCILIATION.md` (removed; Pantheon-Next archive)" in obsolete


def test_superseded_external_mvp_review_stays_as_strategic_memory_only() -> None:
    retired = ROOT / "docs/governance/reference_reviews/PANTHEON_MVP_VERTICAL_CURRENT_REVIEW.md"
    assert not retired.exists()

    reviews = _read("docs/governance/reference_reviews/README.md")
    assert "Pantheon MVP Vertical bundle" in reviews
    assert "superseded / historical provenance" in reviews
    assert "NEXT_MVP_REPOSITORY_PLACEMENT.md" in reviews
    assert "implementation/` tests" in reviews


def test_runtime_adapter_index_uses_logical_tool_card_owner() -> None:
    text = _read("docs/governance/authority/RUNTIME_ADAPTERS_AUTHORITY_INDEX.md")

    assert "Concrete catalogue records, card projection and Hermes/runtime reconciliation belong to `Pantheon implementation` under `implementation/`" in text
    assert "Concrete catalogue records, card projection and Hermes/runtime reconciliation belong in `pantheon-mvp`" not in text


def test_retired_paperless_and_document_observer_paths_stay_absent() -> None:
    retired = (
        "implementation/compose.paperless.yaml",
        "implementation/mvp_vertical/paperless.py",
        "implementation/mvp_vertical/paperless_gateway.py",
        "implementation/mvp_vertical/paperless_ingestion.py",
        "implementation/mvp_vertical/document_runtime_observer.py",
        "implementation/mvp_vertical/document_runtime_network_observer.py",
        "implementation/hermes/skills/pantheon-document-intake/SKILL.md",
        "docs/governance/PAPERLESS_NGX_DOCUMENT_RUNTIME.md",
        "docs/governance/HERMES_PAPERLESS_DOCUMENT_INTAKE_BINDING.md",
        "docs/governance/DOCUMENT_RUNTIME_STATUS_PROJECTION.md",
        "docs/governance/DOCUMENT_RUNTIME_LIVE_OBSERVATIONS.md",
    )
    for relative in retired:
        assert not (ROOT / relative).exists(), relative


def test_paperless_is_not_still_advertised_by_base_compose() -> None:
    compose = _read("implementation/docker-compose.yml").lower()
    for token in (
        "paperless",
        "paperless-gateway",
        "mvp_vertical.paperless_gateway",
        "paperless_api_url",
    ):
        assert token not in compose


def test_document_source_management_can_remain_intentionally_unbound() -> None:
    capability = yaml.safe_load(_read("catalog/capabilities/document-source-management.yaml"))
    assert capability["spec"]["candidate_resources"] == {
        "preferred": [],
        "alternatives": [],
    }

    schema = json.loads(_read("catalog/schemas/capability.schema.json"))
    preferred = schema["properties"]["spec"]["properties"]["candidate_resources"]["properties"]["preferred"]
    assert "minItems" not in preferred


def test_phase_b_keeps_current_generic_runtime_owners() -> None:
    current = (
        "implementation/compose.phase-b.yaml",
        "implementation/mvp_vertical/source_intake.py",
        "implementation/mvp_vertical/source_intake_api.py",
        "implementation/mvp_vertical/runtime_observation.py",
    )
    for relative in current:
        assert (ROOT / relative).is_file(), relative

    compose = _read("implementation/compose.phase-b.yaml").lower()
    assert "paperless" not in compose
    assert "document-runtime-observer" not in compose

    runbook = _read("docs/install/COMMON_BASELINE_RUNBOOK.md")
    assert "Hermes" in runbook
    assert "source" in runbook.lower()


def test_status_uses_current_interaction_and_governance_owners() -> None:
    status = _read("docs/governance/STATUS.md")

    assert "Hermes Web/dashboard exposes chat, sessions and runtime controls." in status
    assert "Hermes Agent executes externally." in status
    assert "Pantheon Cockpit projects governed Cards, navigation, decisions and status." in status
    assert "OpenWebUI exposes." not in status
    assert "OpenWebUI and Paperless-ngx are refused/retired target integrations." in status
    assert "NON_EQUIVALENCE_RULES.md" in status
    rules = _read("docs/governance/NON_EQUIVALENCE_RULES.md")
    assert "test_pass != authority_promotion" in rules
