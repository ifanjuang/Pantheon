"""The phase vocabulary: registry, schemas, and the two readers of the agency file.

The phase codes used to be a closed list repeated in five schemas (Project
Anatomy and proof register), without ESQ. They now live in one governed
registry; the schemas check only the shape of a code. The validation server
(mcp-server) and the implementation apply the same rules to the add-only agency
file; this test runs the same cases through both and fails if they ever differ.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import jsonschema
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registries" / "architecture_phase_profile.registry.json"
SCHEMA = ROOT / "schemas" / "architecture-project-understanding" / "phase_profile.schema.yaml"
PROJECT_CARD = ROOT / "implementation" / "mvp_vertical" / "agency_schema" / "project.json"

# The fifteen codes of the former closed list.
FORMER_CODES = {
    "DIAG", "APS", "APD", "PRO", "DCE", "ACT", "EXE", "VISA", "DET",
    "OPC", "AOR", "DOE", "GPA", "AGENCY_LIBRARY", "GLOBAL_REFERENCE",
}
SCOPE_MARKERS = {"AGENCY_LIBRARY", "GLOBAL_REFERENCE"}

# Every schema that names a phase, with the JSON path of its phase definition.
PHASE_DEFINITIONS = [
    ("schemas/architecture-project-understanding/shared.schema.yaml", ("$defs", "phase_code")),
    ("schemas/architecture-proof-register/shared.schema.yaml", ("$defs", "phase_code")),
    ("schemas/architecture-proof-register/proof_entry.schema.yaml", ("properties", "phase_code")),
    ("schemas/architecture-proof-register/indexed_document_version.schema.yaml", ("properties", "phase_code")),
    ("schemas/architecture-proof-register/document_family.schema.yaml", ("properties", "phase_origin")),
]
PHASE_FIELDS = ("phase_code", "phase_origin", "established_at_phase", "project_phase")


def _registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def _validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(yaml.safe_load(SCHEMA.read_text(encoding="utf-8")))


def _agency(*entries: dict, **extra) -> dict:
    return {"registry_kind": "vocabulary_overlay", "extends": "architecture_phase_profile",
            "entries": list(entries), **extra}


def _phase(code: str = "FAISA", **extra) -> dict:
    return {"id": code, "status": "active", "category": "mission_element",
            "label": "Faisabilité", "description": "Étude de faisabilité avant esquisse.", **extra}


def test_registry_validates_and_keeps_the_former_codes_plus_esq() -> None:
    registry = _registry()
    _validator().validate(registry)
    ids = [entry["id"] for entry in registry["entries"]]
    assert len(ids) == len(set(ids))
    assert set(ids) == FORMER_CODES | {"ESQ"}
    pattern = re.compile(registry["naming_rules"]["id_pattern"])
    assert all(pattern.fullmatch(code) for code in ids)
    categories = {entry["id"]: entry["category"] for entry in registry["entries"]}
    assert {code for code, category in categories.items() if category == "non_project_scope"} == SCOPE_MARKERS


def test_no_schema_keeps_a_closed_phase_list() -> None:
    rule = _registry()["naming_rules"]["id_pattern"]
    for relative, path in PHASE_DEFINITIONS:
        node = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))
        for key in path:
            node = node[key]
        assert "enum" not in node, relative
        assert node["pattern"] == rule, relative


def _phase_values(text: str) -> set[str]:
    fields = "|".join(PHASE_FIELDS)
    return set(re.findall(rf"^\s*-?\s*(?:{fields}):\s*([A-Z][A-Z0-9_]*)\s*$", text, re.M))


def test_every_phase_used_by_a_governed_example_is_declared() -> None:
    declared = {entry["id"] for entry in _registry()["entries"]}
    used: set[str] = set()
    for base in (ROOT / "schemas" / "examples", ROOT / "docs" / "examples"):
        for path in base.rglob("*.yaml"):
            used |= _phase_values(path.read_text(encoding="utf-8"))
    assert used, "no example uses a phase: the scan is broken"
    assert used <= declared, sorted(used - declared)


def test_project_card_phases_are_declared_project_phases() -> None:
    card = json.loads(PROJECT_CARD.read_text(encoding="utf-8"))
    field = next(item for item in card["fields"] if item["key"] == "phase")
    project_phases = {
        entry["id"] for entry in _registry()["entries"] if entry["category"] != "non_project_scope"
    }
    assert set(field["values"]) <= project_phases


def test_agency_file_schema_is_add_only_and_project_phases_only() -> None:
    validator = _validator()
    validator.validate(_agency(_phase()))
    validator.validate(_agency(_phase(category="project_stage")))
    for broken in (
        _agency(_phase(status="deprecated")),
        _agency(_phase(replaced_by="PRO")),
        _agency(_phase("faisa")),
        _agency(_phase(category="non_project_scope")),
        _agency({key: value for key, value in _phase().items() if key != "category"}),
        _agency(_phase(), extends="architecture_source_kind_profile"),
    ):
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(broken)


# Cases run through both readers: (name, agency file, expected outcome).
# Outcome: a set of codes the vocabulary must contain, or a message fragment.
CASES = [
    ("no agency file", None, {"ESQ", "PRO", "AGENCY_LIBRARY"}),
    ("one addition", _agency(_phase()), {"FAISA", "ESQ"}),
    ("project stage addition", _agency(_phase(category="project_stage")), {"FAISA"}),
    ("candidate addition", _agency(_phase(status="candidate")), {"FAISA"}),
    ("redeclares a base code", _agency(_phase("ESQ")), "redeclares 'ESQ'"),
    ("deprecates a base code", _agency(_phase("DCE", status="deprecated")), "redeclares 'DCE'"),
    ("twice the same id", _agency(_phase(), _phase()), "redeclares 'FAISA'"),
    ("lower-case id", _agency(_phase("faisa")), "invalid id"),
    ("too short id", _agency(_phase("F")), "invalid id"),
    ("scope marker addition", _agency(_phase(category="non_project_scope")), "must have category"),
    ("no category", _agency({key: value for key, value in _phase().items() if key != "category"}), "must have category"),
    ("deprecated addition", _agency(_phase(status="deprecated")), "active or candidate"),
    ("unknown field", _agency(_phase(replaced_by="PRO")), "unknown fields"),
    ("empty description", _agency(_phase(description=" ")), "non-empty description"),
    ("wrong extends", _agency(_phase(), extends="architecture_source_kind_profile"), "must extend"),
    ("not an object", ["FAISA"], "JSON object"),
    ("too many entries", _agency(*[_phase(f"PH_{i:03d}") for i in range(101)]), "more than 100"),
]


@pytest.fixture(scope="module")
def readers():
    sys.path.insert(0, str(ROOT / "mcp-server"))
    sys.path.insert(0, str(ROOT / "implementation"))
    from pantheon_mcp import apu as server  # type: ignore
    from mvp_vertical import apu_vocabulary as owner  # type: ignore

    return server, owner


@pytest.mark.parametrize(("name", "agency", "expected"), CASES, ids=[case[0] for case in CASES])
def test_both_readers_apply_the_same_rules(readers, tmp_path, monkeypatch, name, agency, expected) -> None:
    server, owner = readers
    assert server.PHASE_OVERLAY_ENV == owner.PHASE_OVERLAY_ENV
    if agency is None:
        monkeypatch.delenv(server.PHASE_OVERLAY_ENV, raising=False)
    else:
        path = tmp_path / "phases.json"
        path.write_text(json.dumps(agency), encoding="utf-8")
        monkeypatch.setenv(server.PHASE_OVERLAY_ENV, str(path))

    results = []
    for load in (
        lambda: server.load_phases(ROOT),
        lambda: owner.phases().entries,
    ):
        try:
            results.append(("ok", set(load())))
        except ValueError as exc:  # VocabularyUnavailable is a ValueError
            results.append(("error", str(exc)))
    if isinstance(expected, set):
        assert [kind for kind, _ in results] == ["ok", "ok"], results
        assert all(expected <= value for _, value in results), results
        assert results[0][1] == results[1][1]
    else:
        assert [kind for kind, _ in results] == ["error", "error"], results
        assert all(expected in value for _, value in results), results
        assert results[0][1] == results[1][1], "the two readers must give the same message"


def test_unreadable_agency_file_is_an_error_not_ignored(readers, tmp_path, monkeypatch) -> None:
    server, owner = readers
    monkeypatch.setenv(server.PHASE_OVERLAY_ENV, str(tmp_path / "missing.json"))
    with pytest.raises(ValueError):
        server.load_phases(ROOT)
    with pytest.raises(owner.VocabularyUnavailable):
        owner.phases()


def test_the_two_vocabularies_do_not_share_their_agency_file(readers, tmp_path, monkeypatch) -> None:
    server, owner = readers
    path = tmp_path / "phases.json"
    path.write_text(json.dumps(_agency(_phase())), encoding="utf-8")
    monkeypatch.setenv(server.PHASE_OVERLAY_ENV, str(path))
    monkeypatch.delenv(server.SOURCE_KIND_OVERLAY_ENV, raising=False)
    assert "FAISA" in owner.phases().entries
    assert "FAISA" not in owner.source_kinds().entries
    assert "FAISA" not in server.load_source_kinds(ROOT)


def test_owner_refuses_a_scope_marker_as_a_project_phase(readers, monkeypatch) -> None:
    _server, owner = readers
    monkeypatch.delenv(owner.PHASE_OVERLAY_ENV, raising=False)
    assert owner.require_phase("ESQ", project_phase=True) == "active"
    assert owner.require_phase("AGENCY_LIBRARY") == "active"
    with pytest.raises(owner.VocabularyRefused, match="non-project scope marker"):
        owner.require_phase("AGENCY_LIBRARY", project_phase=True)
    with pytest.raises(owner.VocabularyRefused, match="not declared"):
        owner.require_phase("ESQUISSE")
