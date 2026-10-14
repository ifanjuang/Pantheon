from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "templates/hermes/skills/pantheon-request-intake"
SKILL = SKILL_ROOT / "SKILL.md"
VOCABULARY = SKILL_ROOT / "references/condition-vocabulary.md"
ROLE_ACTIVATION = ROOT / "docs/governance/ROLE_ACTIVATION.md"
FIXTURES = ROOT / "tests/fixtures/hermes_request_intake_cases.yaml"
REGISTRY = ROOT / "templates/TEMPLATE_REGISTRY.md"


def _role_triggers() -> set[str]:
    text = ROLE_ACTIVATION.read_text(encoding="utf-8")
    block = text.split("```yaml\nmandatory_role_triggers:\n", 1)[1].split("```", 1)[0]
    data = yaml.safe_load("mandatory_role_triggers:\n" + block)
    return {trigger for values in data["mandatory_role_triggers"].values() for trigger in values}


def test_request_intake_is_minimal_and_defers_policy() -> None:
    text = SKILL.read_text(encoding="utf-8")
    vocabulary = VOCABULARY.read_text(encoding="utf-8")
    assert "name: pantheon-request-intake" in text
    assert "status: candidate_template_only" in text
    assert "Return a request candidate, never K/V/C." in text
    assert "Pantheon, not Hermes, returns `PROCEED`, `CONSULT` or `GATE`." in text
    assert "Prefer the smallest sufficient" in text
    assert "Do not choose a topology or reconsult" in text
    assert "condition-vocabulary.md" in text
    assert "memory recall != memory promotion" in text
    assert "persistent, canonical or official" in vocabulary
    assert "external_transmission` and `external_effect`" in vocabulary
    assert "relations, never worker topology" in vocabulary


def test_vocabulary_uses_only_owned_policy_triggers() -> None:
    doctrine = _role_triggers()
    vocabulary = VOCABULARY.read_text(encoding="utf-8")
    advertised = {
        "source_required", "factual_claim", "external_reference", "evidence_gap",
        "memory_recall_requested", "memory_candidate", "memory_promotion",
        "approval_required", "legal_or_professional_risk", "external_transmission",
        "external_effect", "client_delivery", "unclear_output", "delivery_quality_required",
    }
    assert advertised <= doctrine
    assert all(f"`{trigger}`" in vocabulary for trigger in advertised)


def test_fixture_corpus_keeps_positive_and_negative_expectations() -> None:
    cases = yaml.safe_load(FIXTURES.read_text(encoding="utf-8"))["cases"]
    assert len(cases) >= 15
    doctrine = _role_triggers()
    for case in cases:
        expected = case["expected"]
        conditions = set(expected.get("conditions") or [])
        forbidden = set(expected.get("forbidden_conditions") or [])
        assert conditions <= doctrine
        assert forbidden <= doctrine
        assert not conditions.intersection(forbidden)


def test_registry_lists_request_intake_once() -> None:
    registry = REGISTRY.read_text(encoding="utf-8")
    assert registry.count("templates/hermes/skills/pantheon-request-intake/SKILL.md") == 1
