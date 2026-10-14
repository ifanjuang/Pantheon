"""Every present-tense property in CLAUDE.md names a control, honestly graded.

The registry says how strong each control is. These tests hold the part that
matters: the grade cannot be inflated, the link to CLAUDE.md cannot rot in
either direction, and the uncontrolled debt cannot grow quietly.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECK = load_module("check_asserted_properties", ".github/scripts/check_asserted_properties.py")
REGISTRY = json.loads((ROOT / ".github" / "asserted-properties.json").read_text(encoding="utf-8"))
CLAIMS = CHECK.asserted_properties((ROOT / "CLAUDE.md").read_text(encoding="utf-8"))


def test_the_doctrine_and_the_registry_agree_today() -> None:
    errors, rows = CHECK.verify(CLAIMS, REGISTRY)
    assert errors == [], "\n".join(errors)
    assert len(rows) == len(CLAIMS)


def test_both_enumerable_blocks_are_actually_found() -> None:
    kinds = set(CLAIMS.values())
    assert kinds == {"non_equivalence", "forbidden_component"}, (
        "CLAUDE.md's enumerable claim blocks moved; the extractor reads "
        f"the '!=' invariants and the non-negotiable list. Found: {kinds}"
    )
    assert "installed != approved" in CLAIMS
    assert "message bus" in CLAIMS


def test_a_property_asserted_with_no_entry_fails() -> None:
    errors, _ = CHECK.verify({**CLAIMS, "faith != proof": "non_equivalence"}, REGISTRY)
    assert any("nothing here names a control" in error for error in errors)


def test_an_entry_for_a_property_no_longer_asserted_fails() -> None:
    """A stale entry is how the registry drifts away from the doctrine."""
    errors, _ = CHECK.verify(
        {key: value for key, value in CLAIMS.items() if key != "message bus"}, REGISTRY
    )
    assert any("no longer asserts it" in error for error in errors)


def test_a_binding_cannot_be_stronger_than_its_control_supports() -> None:
    inflated = {
        "uncontrolled_ceiling": 2,
        "properties": [
            {
                "claim": "installed != approved",
                "binding": "behavioural",
                "controls": [{"path": "tests/test_monorepo_placement_language.py"}],
            }
        ],
    }
    errors, _ = CHECK.verify({"installed != approved": "non_equivalence"}, inflated)
    assert any("declared 'behavioural'" in error for error in errors)


def test_documentary_is_the_floor_and_is_always_accepted() -> None:
    modest = {
        "uncontrolled_ceiling": 2,
        "properties": [
            {
                "claim": "installed != approved",
                "binding": "documentary",
                "controls": [{"path": "tests/test_monorepo_placement_language.py"}],
            }
        ],
    }
    errors, _ = CHECK.verify({"installed != approved": "non_equivalence"}, modest)
    assert errors == []


def test_a_named_control_must_exist_and_define_what_it_claims() -> None:
    for control in ({"path": "tests/test_does_not_exist.py"},
                    {"path": "tests/test_monorepo_placement_language.py", "name": "test_absent"}):
        errors, _ = CHECK.verify(
            {"installed != approved": "non_equivalence"},
            {
                "uncontrolled_ceiling": 2,
                "properties": [
                    {
                        "claim": "installed != approved",
                        "binding": "documentary",
                        "controls": [control],
                    }
                ],
            },
        )
        assert errors, f"expected {control} to be refused"


def test_an_uncontrolled_property_must_say_why_and_stay_under_the_ceiling() -> None:
    silent = {
        "uncontrolled_ceiling": 0,
        "properties": [{"claim": "installed != approved", "binding": "none"}],
    }
    errors, _ = CHECK.verify({"installed != approved": "non_equivalence"}, silent)
    assert any("must say why" in error for error in errors)
    assert any("exceed the declared" in error for error in errors)


def test_the_uncontrolled_ceiling_matches_the_debt_that_exists() -> None:
    """A ceiling above the real count is headroom nobody decided to grant."""
    _, rows = CHECK.verify(CLAIMS, REGISTRY)
    uncontrolled = [row for row in rows if row["binding"] == "none"]
    assert REGISTRY["uncontrolled_ceiling"] == len(uncontrolled)


def test_the_report_separates_what_a_contract_holds_from_what_a_sentence_holds() -> None:
    _, rows = CHECK.verify(CLAIMS, REGISTRY)
    report = CHECK.render(rows, REGISTRY["uncontrolled_ceiling"])
    assert "fails when the wording changes, not when the property stops being true" in report
    for binding in ("behavioural", "schema", "documentary", "uncontrolled"):
        assert f"- {binding}:" in report
