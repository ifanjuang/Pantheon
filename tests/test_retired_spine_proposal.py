from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPINE = ROOT / "docs/governance/SPINE_HARDENING_PROPOSAL.md"
OBSOLETE = ROOT / "docs/governance/authority/OBSOLETE_AND_ABSENT_INDEX.md"

SCHEMAS = (
    ROOT / "schemas/shared_axes.schema.yaml",
    ROOT / "schemas/capability_passport.schema.yaml",
    ROOT / "schemas/policy_decision.schema.yaml",
    ROOT / "schemas/answer_status.schema.yaml",
    ROOT / "schemas/register_candidate.schema.yaml",
)


def test_applied_spine_proposal_stays_retired() -> None:
    assert not SPINE.exists()
    assert not (ROOT / "docs/governance/SHARED_AXES_PROPOSAL.md").exists()

    active = (
        *SCHEMAS,
        ROOT / "templates/mcp_capability_passport.yaml",
        ROOT / ".github/scripts/check_axis_vocabulary.py",
    )
    for path in active:
        assert "SPINE_HARDENING_PROPOSAL.md" not in path.read_text(encoding="utf-8")

    links = (ROOT / ".github/scripts/check_internal_links.py").read_text(encoding="utf-8")
    assert "SHARED_AXES_PROPOSAL.md" not in links
    assert '"schemas/shared_axes.yaml"' not in links


def test_spine_contracts_and_boundaries_are_conserved() -> None:
    for schema in SCHEMAS:
        text = schema.read_text(encoding="utf-8")
        assert "runtime_execution: false" in text, schema

    passport = (ROOT / "schemas/capability_passport.schema.yaml").read_text(encoding="utf-8")
    for field in ("can_execute_code", "can_change_register", "can_promote_memory"):
        assert field in passport
    assert "Legacy operation flag. Prefer can_change_register." in passport
    assert "Legacy operation flag. Prefer can_promote_memory." in passport
    assert "runtime_activation: false" in passport
    assert "task_authorization: false" in passport

    policy = (ROOT / "schemas/policy_decision.schema.yaml").read_text(encoding="utf-8")
    assert "decision_is_data: true" in policy

    answer = (ROOT / "schemas/answer_status.schema.yaml").read_text(encoding="utf-8")
    assert "approves_nothing: true" in answer


def test_spine_application_provenance_and_disposition_remain() -> None:
    assert "SPINE_HARDENING_PROPOSAL.md" in OBSOLETE.read_text(encoding="utf-8")
