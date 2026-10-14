from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/governance/ROLE_ACTIVATION.md"
ROLE_REGISTRY = ROOT / "docs/governance/AGENTS.md"
ROLE_OWNER_SURFACES = (
    ROOT / "docs/governance/REQUEST_LIFECYCLE.md",
    ROOT / "docs/governance/WORKFLOW_SCHEMA.md",
    ROOT / "docs/governance/EXTERNAL_RUNTIME_MEMORY_ADAPTERS.md",
    ROOT / "docs/governance/authority/GOVERNANCE_AUTHORITY_INDEX.md",
)
CANONICAL_ROLES = (
    "ATHENA",
    "ARGOS",
    "THEMIS",
    "APOLLO",
    "ZEUS",
    "IRIS",
    "HEPHAISTOS",
    "MNEMOSYNE",
)


def _text() -> str:
    return DOC.read_text(encoding="utf-8")


def test_role_activation_has_no_retired_openwebui_owner() -> None:
    text = _text()
    assert "OpenWebUI" not in text
    assert "OPENWEBUI_INTEGRATION.md" not in text
    assert "openwebui_template_pack" not in text


def test_role_activation_uses_current_runtime_and_projection_owners() -> None:
    text = _text()
    assert "Hermes clients handle runtime interaction" in text
    assert "Hermes Agent executes externally" in text
    assert "Pantheon Cockpit exposes governed projections" in text
    assert "client selected != governance authority" in text
    assert "projection != persistence" in text


def test_activation_remains_eligibility_not_authority() -> None:
    text = _text()
    for invariant in (
        "role active != agent started",
        "domain enabled != professional authority",
        "skill eligible != task authorized",
        "task authorized != approved",
        "activation != retention authorization",
    ):
        assert invariant in text


def test_activation_reuses_existing_owners() -> None:
    text = _text()
    for owner in (
        "AGENTS.md",
        "MODULE_ACTIVATION.md",
        "UNIFORM_CAPABILITY_GOVERNANCE.md",
        "DOMAIN_PACK_SPEC.md",
        "TASK_CONTRACTS.md",
        "HERMES_INTEGRATION.md",
        "PANTHEON_COCKPIT_STRUCTURED_AGENCY_INTERFACE.md",
    ):
        assert owner in text


def test_canonical_role_registry_keeps_the_eight_current_roles() -> None:
    registry = ROLE_REGISTRY.read_text(encoding="utf-8")
    for role in CANONICAL_ROLES:
        assert f"| {role} |" in registry

    for unregistered_role in ("MÈTIS", "CERBÈRE", "CHARON"):
        assert f"| {unregistered_role} |" not in registry


def test_active_lifecycle_surfaces_reuse_canonical_roles_and_existing_memory_owners() -> None:
    forbidden_personas = ("MÈTIS", "CERBÈRE", "CHARON", "Cerbère", "Charon")
    for path in ROLE_OWNER_SURFACES:
        text = path.read_text(encoding="utf-8")
        for persona in forbidden_personas:
            assert persona not in text, f"{path.relative_to(ROOT).as_posix()}: {persona}"

    lifecycle = ROLE_OWNER_SURFACES[0].read_text(encoding="utf-8")
    assert "Situated clarification is a function, not a Role" in lifecycle
    assert "MNEMOSYNE frames continuity" in lifecycle
    assert "retention placement proposal != persistence authorization" in lifecycle

    workflow = ROLE_OWNER_SURFACES[1].read_text(encoding="utf-8")
    assert "schemas/workflow_manifest.schema.yaml" in workflow
    assert "A future `workflow_manifest.schema.yaml`" not in workflow
    assert "schema_valid != authorized" in workflow

    memory = ROLE_OWNER_SURFACES[2].read_text(encoding="utf-8")
    assert "MNEMOSYNE continuity framing" in memory
    assert "The canonical Role registry remains `AGENTS.md`" in memory

    authority = ROLE_OWNER_SURFACES[3].read_text(encoding="utf-8")
    assert "cap as an explicit Task Contract property" in authority
    assert "Adds no canonical Role, memory-gate persona, router or runtime" in authority
