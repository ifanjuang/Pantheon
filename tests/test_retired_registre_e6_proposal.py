from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = ROOT / "docs/governance/REGISTRE_PROBATOIRE_SCHEMA_PROPOSAL.md"
REGISTER_SCHEMA = ROOT / "schemas/register_candidate.schema.yaml"
REGISTER_EXAMPLE = ROOT / "schemas/examples/register_candidate.example.yaml"
OBSOLETE_INDEX = ROOT / "docs/governance/authority/OBSOLETE_AND_ABSENT_INDEX.md"


def test_applied_e6_proposal_and_old_schema_paths_stay_retired() -> None:
    assert not PROPOSAL.exists()
    assert not (ROOT / "schemas/memory_candidate.schema.yaml").exists()
    assert not (ROOT / "schemas/examples/memory_candidate.example.yaml").exists()


def test_current_register_candidate_contract_and_provenance_are_conserved() -> None:
    assert REGISTER_SCHEMA.is_file()
    assert REGISTER_EXAMPLE.is_file()

    schema = REGISTER_SCHEMA.read_text(encoding="utf-8")
    assert "certainty" in schema
    assert "deprecated" in schema.lower()
    assert "memory_promotion: false" in schema


def test_e6_exemptions_are_not_kept_in_active_ci() -> None:
    axis = (ROOT / ".github/scripts/check_axis_vocabulary.py").read_text(encoding="utf-8")
    links = (ROOT / ".github/scripts/check_internal_links.py").read_text(encoding="utf-8")

    for retired in (
        "REGISTRE_PROBATOIRE_SCHEMA_PROPOSAL.md",
        "schemas/memory_candidate.schema.yaml",
        "schemas/examples/memory_candidate.example.yaml",
    ):
        assert retired not in axis
        assert retired not in links

    assert '"deprecated" in context or "legacy" in context' in axis
    assert "REGISTRE_PROBATOIRE_SCHEMA_PROPOSAL.md" in OBSOLETE_INDEX.read_text(encoding="utf-8")
