from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / ".github" / "scripts" / "check_apu_referential_integrity.py"


def _load_checker_module():
    spec = importlib.util.spec_from_file_location(
        "check_apu_referential_integrity", CHECKER_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_id_index_accepts_unique_dossier_ids() -> None:
    checker = _load_checker_module()
    docs = {
        "program.yaml": {"program_id": "PROGRAM-1"},
        "requirement_area.yaml": {"requirement_id": "REQ-1"},
    }

    id_index, errors = checker.build_id_index(docs)

    assert errors == []
    assert id_index == {
        "PROGRAM-1": "program.yaml",
        "REQ-1": "requirement_area.yaml",
    }


def test_build_id_index_fails_closed_on_duplicate_dossier_id() -> None:
    checker = _load_checker_module()
    docs = {
        "program.yaml": {"program_id": "DUPLICATE-1"},
        "requirement_area.yaml": {"requirement_id": "DUPLICATE-1"},
    }

    id_index, errors = checker.build_id_index(docs)

    assert id_index == {"DUPLICATE-1": "program.yaml"}
    assert errors == [
        "duplicate id 'DUPLICATE-1': first declared by program.yaml, "
        "repeated by requirement_area.yaml"
    ]
