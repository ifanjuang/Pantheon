from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTING = ROOT / "templates/hermes/skills/project-context/references/professional-source-routing.md"
STANDARD = ROOT / "templates/hermes/skills/technical-standard-review/SKILL.md"
ADAPTER = ROOT / "implementation/hermes/skills/vault-search/SKILL.md"


def test_mixed_project_and_reference_claims_keep_their_source_roles_distinct() -> None:
    text = " ".join(ROUTING.read_text(encoding="utf-8").lower().split())

    for invariant in (
        "project memory as the project source",
        "inspect the exact project document",
        "inspect the exact passage",
        "project records establish",
        "they do not override applicable law",
        "a standard or general reference does not rewrite the project record",
        "never resolve a `direct_conflict` by retrieval rank",
        "preserve both readings",
        "project statement | exact source + locator + status",
        "reference statement | exact source + edition/date + locator",
    ):
        assert invariant in text

    for classification in (
        "apparent_difference",
        "project_reference_gap",
        "reference_project_gap",
        "stale_or_superseded",
        "direct_conflict",
        "to_verify",
        "to_arbitrate",
    ):
        assert classification in text


def test_standard_review_uses_the_same_conflict_protocol() -> None:
    text = " ".join(STANDARD.read_text(encoding="utf-8").lower().split())
    for invariant in (
        "keep the project statement and the standard's requirement as separate claims",
        "do not make either source erase the other",
        "applicable legal and contractual hierarchy",
        "relationship between each project and reference claim",
        "to_verify",
        "to_arbitrate",
    ):
        assert invariant in text


def test_agency_adapter_applies_conflict_protocol_without_making_recall_authoritative() -> None:
    text = " ".join(ADAPTER.read_text(encoding="utf-8").lower().split())
    for invariant in (
        "treat project recall and standards recall as",
        "discovery leads",
        "inspect the exact project source",
        "inspect the exact",
        "classify an apparent difference",
        "never let retrieval rank",
        "report `to_verify` or `to_arbitrate`",
        "both source locators",
    ):
        assert invariant in text
