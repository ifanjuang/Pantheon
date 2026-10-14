from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "templates/hermes/skills/source-research/SKILL.md"
OLD_SOURCE_AUDIT = ROOT / "templates/hermes/skills/source_audit_skill_candidate.template.yaml"
REGISTRY = ROOT / "templates/TEMPLATE_REGISTRY.md"


def test_source_research_is_single_surviving_research_skill_candidate():
    assert SKILL.is_file()
    assert not OLD_SOURCE_AUDIT.exists()

    text = SKILL.read_text(encoding="utf-8")
    assert "name: source-research" in text
    assert "status: candidate_template_only" in text
    assert "pantheon_role: ARGOS" in text

    for mode in ("`discover`", "`investigate`", "`audit`", "`synthesize`", "`validate`"):
        assert mode in text

    assert "retrieved != truth" in text
    assert "research synthesis != Evidence" in text
    assert "autonomous recurring research loops" in text
    assert "optional workspace source notebook" in text
    assert "notebook entry != Source Registry Entry" in text
    assert "registered route != inspected source" in text
    assert "Never hard-code its filename or Obsidian path" in text
    assert "`source_addition_candidate`" in text

    assert "Before an external retrieval query, minimize unnecessary private" in text
    assert "task/context access != external transmission authorization" in text
    assert "Secrets must never be sent to an external retrieval surface" in text
    assert "local context available != external disclosure required" in text
    assert "### 6. Challenge material claims" in text
    assert "support found != challenge completed" in text
    assert "### 9. Stop proportionally" in text
    assert "more searching possible != more searching decision-relevant" in text

    registry = REGISTRY.read_text(encoding="utf-8")
    skill_path = "templates/hermes/skills/source-research/SKILL.md"
    assert registry.count(skill_path) == 1
    assert "source_audit_skill_candidate.template.yaml" not in registry
