"""The source kind vocabulary: registry, schema, and the two readers of the agency file.

The validation server (mcp-server) and the implementation apply the same rules to
the add-only agency file. They are separate distributions, so the rules exist
twice; this test runs the same cases through both and fails if they ever differ.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
from pathlib import Path

import jsonschema
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registries" / "architecture_source_kind_profile.registry.json"
SCHEMA = ROOT / "schemas" / "architecture-project-understanding" / "source_kind_profile.schema.yaml"
SHARED = ROOT / "schemas" / "architecture-project-understanding" / "shared.schema.yaml"
EXAMPLES = ROOT / "schemas" / "examples" / "architecture-project-understanding"

# The ten kinds that existed before the vocabulary moved to a registry.
FORMER_KINDS = {
    "revit", "ifc", "drawing", "drawing_takeoff", "image",
    "photo", "manual", "scan", "point_cloud", "other",
}


def _registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def _validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(yaml.safe_load(SCHEMA.read_text(encoding="utf-8")))


def _agency(*entries: dict, **extra) -> dict:
    return {"registry_kind": "vocabulary_overlay", "extends": "architecture_source_kind_profile",
            "entries": list(entries), **extra}


def _kind(kind: str = "plan_recolement", **extra) -> dict:
    return {"id": kind, "status": "active", "label": "Plan de récolement",
            "description": "Plan fourni par l'entreprise.", **extra}


def test_registry_validates_against_its_schema_and_keeps_the_former_kinds() -> None:
    registry = _registry()
    _validator().validate(registry)
    ids = [entry["id"] for entry in registry["entries"]]
    assert len(ids) == len(set(ids))
    assert FORMER_KINDS | {"document", "email", "cad_drawing"} == set(ids)
    pattern = re.compile(registry["naming_rules"]["id_pattern"])
    assert all(pattern.fullmatch(kind) for kind in ids)


def test_schema_shape_rule_is_the_registry_naming_rule() -> None:
    shared = yaml.safe_load(SHARED.read_text(encoding="utf-8"))
    assert shared["$defs"]["source_kind"]["pattern"] == _registry()["naming_rules"]["id_pattern"]
    assert "enum" not in shared["$defs"]["source_kind"]


def test_every_source_kind_used_by_a_governed_example_is_declared() -> None:
    declared = {entry["id"] for entry in _registry()["entries"]}
    used: set[str] = set()
    for path in EXAMPLES.glob("*.yaml"):
        used |= set(re.findall(r"^\s*-?\s*source_kind:\s*([a-z_]+)\s*$", path.read_text(encoding="utf-8"), re.M))
    assert used, "no example uses a source_kind: the scan is broken"
    assert used <= declared, sorted(used - declared)


def test_agency_file_schema_is_add_only() -> None:
    validator = _validator()
    validator.validate(_agency(_kind()))
    for broken in (
        _agency(_kind(status="deprecated")),
        _agency(_kind(replaced_by="other")),
        _agency(_kind("Plan")),
        _agency(_kind(), extends="something_else"),
    ):
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(broken)


# Cases run through both readers: (name, agency file, expected outcome).
# Outcome: a set of kinds the vocabulary must contain, or a message fragment.
CASES = [
    ("no agency file", None, {"document", "cad_drawing", "other"}),
    ("one addition", _agency(_kind()), {"plan_recolement", "document"}),
    ("candidate addition", _agency(_kind(status="candidate")), {"plan_recolement"}),
    ("redeclares a base kind", _agency(_kind("document")), "redeclares 'document'"),
    ("deprecates a base kind", _agency(_kind("other", status="deprecated")), "redeclares 'other'"),
    ("twice the same id", _agency(_kind(), _kind()), "redeclares 'plan_recolement'"),
    ("bad id", _agency(_kind("Plan")), "invalid id"),
    ("too short id", _agency(_kind("x")), "invalid id"),
    ("deprecated addition", _agency(_kind(status="deprecated")), "active or candidate"),
    ("unknown field", _agency(_kind(replaced_by="other")), "unknown fields"),
    ("empty label", _agency(_kind(label=" ")), "non-empty label"),
    ("wrong extends", _agency(_kind(), extends="x"), "must extend"),
    ("wrong kind of file", {"registry_kind": "vocabulary", "extends": "architecture_source_kind_profile", "entries": []}, "vocabulary_overlay"),
    ("not an object", ["plan"], "JSON object"),
    ("no entries list", {"registry_kind": "vocabulary_overlay", "extends": "architecture_source_kind_profile"}, "no entries list"),
    ("too many entries", _agency(*[_kind(f"genre_{i:03d}") for i in range(201)]), "more than 200"),
]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


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
    if agency is None:
        monkeypatch.delenv(server.SOURCE_KIND_OVERLAY_ENV, raising=False)
    else:
        path = tmp_path / "source-kinds.json"
        path.write_text(json.dumps(agency), encoding="utf-8")
        monkeypatch.setenv(server.SOURCE_KIND_OVERLAY_ENV, str(path))
    assert server.SOURCE_KIND_OVERLAY_ENV == owner.OVERLAY_ENV

    results = []
    for load in (
        lambda: server.load_source_kinds(ROOT),
        lambda: owner.source_kinds().kinds,
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
    monkeypatch.setenv(server.SOURCE_KIND_OVERLAY_ENV, str(tmp_path / "missing.json"))
    with pytest.raises(ValueError):
        server.load_source_kinds(ROOT)
    with pytest.raises(owner.VocabularyUnavailable):
        owner.source_kinds()
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    monkeypatch.setenv(server.SOURCE_KIND_OVERLAY_ENV, str(broken))
    with pytest.raises(ValueError):
        server.load_source_kinds(ROOT)
    with pytest.raises(owner.VocabularyUnavailable):
        owner.source_kinds()
