"""Contracts for the architecture-project-understanding Hermes skill."""

from __future__ import annotations

import importlib.util
from copy import deepcopy
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "hermes" / "skills" / "architecture-project-understanding"
SCRIPT = SKILL / "scripts" / "validate_fragment_qualifications.py"


def _module():
    spec = importlib.util.spec_from_file_location("fragment_qualification_validator", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _structure() -> dict:
    return {
        "structure_id": "compilation.demo",
        "document_ref": "document.demo",
        "fragments": [
            {"fragment_id": "unit-a"},
            {"fragment_id": "unit-b"},
        ],
    }


def _candidate() -> dict:
    return {
        "candidate_id": "fragment-qualification.document.demo.001",
        "document_ref": "document.demo",
        "structure_ref": "compilation.demo",
        "producer": {
            "capability": "architecture-project-understanding",
            "implementation": "hermes-native-vision",
            "skill_version": "0.1.0",
        },
        "status": "needs_review",
        "qualifications": [
            {
                "fragment_ref": "unit-a",
                "representation_kind": "floor_plan",
                "project_state": "to_demolish",
                "supporting_fragment_refs": ["unit-b"],
                "certainty": "E2",
                "rationale": "Le titre et les annotations suggèrent une vue de démolition.",
                "question": "Confirmer le statut de cette vue ?",
            }
        ],
        "limitations": ["Candidate derived from supplied fragments only."],
        "created_at": "2026-08-04T17:30:00Z",
        "authority": {
            "mutates_document_structure": False,
            "is_project_fact": False,
            "is_evidence": False,
            "is_apu_write": False,
            "is_professional_validation": False,
        },
    }


def test_skill_package_is_complete() -> None:
    assert (SKILL / "SKILL.md").is_file()
    assert SCRIPT.is_file()
    prose = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert "qualification candidate != reviewed classification" in prose
    assert "Return the validated candidate only" in prose


def test_validator_accepts_bounded_candidate() -> None:
    module = _module()
    assert module.validate(_structure(), _candidate()) == _candidate()


def test_validator_rejects_unknown_fragment() -> None:
    module = _module()
    candidate = _candidate()
    candidate["qualifications"][0]["fragment_ref"] = "unit-unknown"
    with pytest.raises(module.ValidationError, match="not present"):
        module.validate(_structure(), candidate)


def test_validator_rejects_cross_structure_identity() -> None:
    module = _module()
    candidate = _candidate()
    candidate["structure_ref"] = "compilation.other"
    with pytest.raises(module.ValidationError, match="does not match"):
        module.validate(_structure(), candidate)


def test_validator_rejects_authority_claim() -> None:
    module = _module()
    candidate = deepcopy(_candidate())
    candidate["authority"]["is_project_fact"] = True
    with pytest.raises(module.ValidationError, match="non-authoritative"):
        module.validate(_structure(), candidate)


def test_validator_requires_semantic_content_and_rationale() -> None:
    module = _module()
    candidate = _candidate()
    qualification = candidate["qualifications"][0]
    for field in ("representation_kind", "project_state"):
        qualification.pop(field)
    with pytest.raises(module.ValidationError, match="semantic proposal"):
        module.validate(_structure(), candidate)

    candidate = _candidate()
    candidate["qualifications"][0]["rationale"] = ""
    with pytest.raises(module.ValidationError, match="rationale"):
        module.validate(_structure(), candidate)


def test_validator_rejects_unknown_supporting_fragment() -> None:
    module = _module()
    candidate = _candidate()
    candidate["qualifications"][0]["supporting_fragment_refs"] = ["unit-z"]
    with pytest.raises(module.ValidationError, match="unknown fragments"):
        module.validate(_structure(), candidate)
