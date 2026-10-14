from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RETIRED = ROOT / "docs/governance/REGISTER_LINK_CASCADE_SCHEMA_PROPOSAL.md"
CANONICAL = ROOT / "docs/governance/EVIDENCE_MEMORY_CANONICALIZATION.md"
REGISTER_LINK = ROOT / "schemas/register_link.schema.yaml"
IMPACT_REVIEW = ROOT / "schemas/impact_review.schema.yaml"
OBSOLETE_INDEX = ROOT / "docs/governance/authority/OBSOLETE_AND_ABSENT_INDEX.md"


def test_applied_cascade_proposal_stays_out_of_active_corpus() -> None:
    assert not RETIRED.exists()

    active_consumers = (
        ROOT / "docs/governance/ITERATIVE_DELIBERATION_LIFECYCLE.md",
        ROOT / "docs/examples/cascade_register/candidate.p-150.yaml",
        ROOT / "docs/examples/cascade_register/candidate.p-202.yaml",
    )
    for path in active_consumers:
        assert "REGISTER_LINK_CASCADE_SCHEMA_PROPOSAL.md" not in path.read_text(encoding="utf-8")


def test_cascade_semantics_and_contracts_are_conserved() -> None:
    canonical = CANONICAL.read_text(encoding="utf-8")
    assert "## Dependency model" in canonical
    assert "## Impact review" in canonical
    assert "Critical impacts should never be silently downgraded." in canonical

    for schema in (REGISTER_LINK, IMPACT_REVIEW):
        text = schema.read_text(encoding="utf-8")
        assert "automatic_cascade_resolution: false" in text


def test_retirement_keeps_provenance_and_disposition() -> None:
    assert "REGISTER_LINK_CASCADE_SCHEMA_PROPOSAL.md" in OBSOLETE_INDEX.read_text(encoding="utf-8")
