from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_superseded_hosting_plans_stay_out_of_working_tree() -> None:
    retired = (
        "docs/governance/HERMES_CODE_HOSTING_BOUNDARY.md",
        "docs/governance/MVP_VERTICAL_IMPLEMENTATION_PLAN.md",
        "docs/governance/MONOREPO_INTEGRATION_PROPOSAL.md",
    )
    for relative in retired:
        assert not (ROOT / relative).exists()

    authority = _read("docs/governance/authority/GOVERNANCE_AUTHORITY_INDEX.md")
    obsolete = _read("docs/governance/authority/OBSOLETE_AND_ABSENT_INDEX.md")
    for relative in retired:
        name = Path(relative).name
        assert name not in authority
        assert f"`{name}` (removed; Pantheon-Next archive)" in obsolete


def test_current_owners_preserve_surviving_responsibilities() -> None:
    control = _read("docs/governance/PANTHEON_CONTROL_BOUNDARY.md")
    loop_schema = _read("schemas/mvp_governed_loop_objects.schema.yaml")

    assert "`CLAUDE.md`, `NEXT_MVP_REPOSITORY_PLACEMENT.md`" in control
    assert "MONOREPO_INTEGRATION_PROPOSAL.md" not in control

    assert "docs/governance/MVP_GOVERNED_TASK_LOOP.md" in loop_schema
    assert "docs/governance/USER_DECISION_GATE.md" in loop_schema
    assert "MVP_VERTICAL_IMPLEMENTATION_PLAN.md" not in loop_schema

    assert (ROOT / "docs/governance/NEXT_MVP_REPOSITORY_PLACEMENT.md").is_file()
    assert (ROOT / "docs/governance/HERMES_INTEGRATION.md").is_file()
    assert (ROOT / "docs/governance/MVP_GOVERNED_TASK_LOOP.md").is_file()
