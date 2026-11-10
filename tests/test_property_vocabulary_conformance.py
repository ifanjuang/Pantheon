"""The property vocabulary: registry, schema, agency file rules and its first consumers.

The profile names the keys of attribute claims (position, geometry, function,
composition, performance, state, quantity) so an object can gain properties as
the project advances. It is advisory: an undeclared key is reported, never
refused.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import jsonschema
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registries" / "architecture_property_profile.registry.json"
SCHEMA = ROOT / "schemas" / "architecture-project-understanding" / "property_profile.schema.yaml"
SHARED = ROOT / "schemas" / "architecture-project-understanding" / "shared.schema.yaml"
EXAMPLES = ROOT / "schemas" / "examples" / "architecture-project-understanding"

sys.path.insert(0, str(ROOT / "implementation"))
from mvp_vertical import apu_vocabulary as vocabulary  # noqa: E402


def _registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def _validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(yaml.safe_load(SCHEMA.read_text(encoding="utf-8")))


def _agency(*entries: dict) -> dict:
    return {"registry_kind": "vocabulary_overlay", "extends": "architecture_property_profile", "entries": list(entries)}


def _property(key: str = "agence.ventilation", **extra) -> dict:
    return {"id": key, "status": "candidate", "facet": "fonction", "value_type": "text",
            "label": "Ventilation", "description": "Mode de ventilation d'un local.", **extra}


def test_registry_validates_and_names_each_property_once_in_a_declared_facet() -> None:
    registry = _registry()
    _validator().validate(registry)
    ids = [entry["id"] for entry in registry["entries"]]
    assert len(ids) == len(set(ids))
    pattern = re.compile(registry["naming_rules"]["id_pattern"])
    assert all(pattern.fullmatch(key) for key in ids)
    facets = {facet["id"] for facet in registry["facets"]}
    assert {entry["facet"] for entry in registry["entries"]} <= facets
    assert next(e for e in registry["entries"] if e["id"] == "space.area")["status"] == "active"


def test_schema_lists_are_the_claim_schema_lists() -> None:
    shared = yaml.safe_load(SHARED.read_text(encoding="utf-8"))["$defs"]
    schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))["$defs"]
    assert set(schema["value_type"]["enum"]) == set(shared["claim_value_type"]["enum"]) == vocabulary.VALUE_TYPES
    assert set(schema["object_family"]["enum"]) == set(shared["object_family"]["enum"]) == vocabulary.OBJECT_FAMILIES
    assert set(schema["facet"]["enum"]) == {facet["id"] for facet in _registry()["facets"]}


def test_every_key_matches_the_attribute_claim_key_shape() -> None:
    claim = yaml.safe_load((SHARED.parent / "attribute_claim.schema.yaml").read_text(encoding="utf-8"))
    shape = re.compile(claim["properties"]["attribute_key"]["pattern"])
    assert all(shape.fullmatch(entry["id"]) for entry in _registry()["entries"])


def test_keys_already_used_by_the_governed_examples_keep_their_names() -> None:
    used: set[str] = set()
    for path in EXAMPLES.glob("*.yaml"):
        used |= set(re.findall(r"attribute_key:\s*([a-z][a-z0-9_.-]*)", path.read_text(encoding="utf-8")))
    declared = {entry["id"] for entry in _registry()["entries"]}
    for key in ("space.area", "space.number", "geometry.width", "thermal.uw", "physical.apparent_condition"):
        assert key in used and key in declared, key


def test_the_ifc_reader_writes_only_declared_properties() -> None:
    source = (ROOT / "implementation" / "mvp_vertical" / "ifc_observation.py").read_text(encoding="utf-8")
    written = set(re.findall(r'"attribute_key":\s*"([a-z][a-z0-9_.-]*)"', source))
    assert written and written <= {entry["id"] for entry in _registry()["entries"]}


def test_an_agency_adds_properties_but_never_changes_the_repository_ones() -> None:
    base = _registry()
    _validator().validate(_agency(_property(unit="m3/h", applies_to=["spatial"])))
    merged = vocabulary.merge_agency_file(base, _agency(_property(unit="m3/h")))
    assert merged["agence.ventilation"]["origin"] == "agency" and merged["agence.ventilation"]["unit"] == "m3/h"
    for broken, message in (
        (_property("space.area"), "add-only"),
        (_property(facet="ambiance"), "facet"),
        (_property(value_type="couleur"), "value_type"),
        (_property(applies_to=["piece"]), "applies_to"),
        (_property(unit=""), "unit"),
        ({**_property(), "category": "x"}, "unknown fields"),
        (_property("Ventilation"), "invalid id"),
    ):
        with pytest.raises(vocabulary.VocabularyUnavailable, match=message):
            vocabulary.merge_agency_file(base, _agency(broken))


def test_undeclared_keys_are_reported_not_refused(monkeypatch) -> None:
    monkeypatch.delenv(vocabulary.PROPERTY_OVERLAY_ENV, raising=False)
    assert vocabulary.describe_property("space.area")["label"] == "Surface"
    assert vocabulary.describe_property("local.inconnue") is None
    assert vocabulary.undeclared_properties(["space.area", "local.inconnue", "local.inconnue"]) == ["local.inconnue"]


def test_the_published_anatomy_carries_labels_and_lists_undeclared_keys() -> None:
    from mvp_vertical import anatomy_export

    section = anatomy_export.property_labels(
        {"attribute_claims": [{"attribute_key": "space.area"}, {"attribute_key": "local.inconnue"}]})
    assert section == {"labels": {"space.area": {"label": "Surface", "unit": "m2", "facet": "geometrie"}},
                       "undeclared": ["local.inconnue"]}
