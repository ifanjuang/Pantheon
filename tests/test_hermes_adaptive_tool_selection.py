from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE_README = ROOT / "hermes" / "profiles" / "README.md"
PROFILE_CONSTITUTION = ROOT / "hermes" / "profiles" / "PROFILE_CONSTITUTION.md"
BASE_SOUL_RULES = ROOT / "hermes" / "profiles" / "_base" / "base-soul-rules.md"
INTEGRATION = ROOT / "docs" / "governance" / "HERMES_INTEGRATION.md"
TASK_CONTRACTS = ROOT / "docs" / "governance" / "TASK_CONTRACTS.md"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _flat(text: str) -> str:
    return " ".join(text.split())


def test_governed_runtime_prefers_adaptive_qualified_selection_over_fixed_global_tool_lists() -> None:
    readme = _text(PROFILE_README)
    constitution = _text(PROFILE_CONSTITUTION)
    base = _text(BASE_SOUL_RULES)

    assert "qualified observable runtime capability surface" in readme
    assert "Hermes may choose among qualified runtime mechanisms" in _flat(readme)
    assert "runtime_tool_selection: adaptive_within_admitted_boundary" in constitution
    assert "Hermes chooses execution means" in constitution
    assert "A fixed global tool allowlist as the normal expression of Pantheon governance" in constitution
    assert "Hermes may select, combine, replace and sequence qualified runtime tools" in base

    assert "explicit tool allowlist" not in readme.lower()
    assert "tool_allowlist: explicit" not in constitution
    assert "explicit tool allowlist" not in base.lower()


def test_adaptive_selection_never_widens_governance_boundary() -> None:
    constitution = _text(PROFILE_CONSTITUTION)
    base = _text(BASE_SOUL_RULES)
    integration = _text(INTEGRATION)
    contracts = _text(TASK_CONTRACTS)

    assert "tool available != effect authorized" in constitution
    assert "runtime choice != scope expansion" in base
    assert "Hermes must not silently select it" in _flat(constitution)
    assert "Capability Gap" in constitution

    assert "Hermes may decide how to execute inside that boundary" in integration
    assert "tool available != tool authorized" in integration
    assert "Hermes Agent decides how to execute within its own runtime" in contracts
    assert "Task Contracts must never become" in contracts


def test_memory_and_consequential_effect_boundaries_remain_separate_from_tool_freedom() -> None:
    constitution = _text(PROFILE_CONSTITUTION)
    base = _text(BASE_SOUL_RULES)

    assert "stored runtime memory remains inert unless separately admitted" in constitution.lower()
    assert "external_memory_provider: off" in constitution
    assert "built_in_memory_injection: off" in constitution
    assert "memory_tool: off" in constitution
    assert "external effects are approval-bound" in constitution.lower()
    assert "candidate-only outputs" in base
