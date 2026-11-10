"""The category profile of the model reading: registry, schema, agency file and classification.

A category says what a model element is whatever the family a modeller picked;
door and window rules are entries like any other.
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
REGISTRY = ROOT / "registries" / "architecture_category_profile.registry.json"
SCHEMA = ROOT / "schemas" / "architecture-project-understanding" / "category_profile.schema.yaml"
SHARED = ROOT / "schemas" / "architecture-project-understanding" / "shared.schema.yaml"

sys.path.insert(0, str(ROOT / "implementation"))
from mvp_vertical import apu_vocabulary as vocabulary  # noqa: E402


def _registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def _validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(yaml.safe_load(SCHEMA.read_text(encoding="utf-8")))


def _agency(*entries: dict) -> dict:
    return {"registry_kind": "vocabulary_overlay", "extends": "architecture_category_profile", "entries": list(entries)}


def _category(key: str = "brise_soleil", **extra) -> dict:
    return {"id": key, "status": "candidate", "label": "brise-soleil", "description": "Lames de protection solaire.",
            "family": "element", "priority": 85, "synonyms": ["brise-soleil", "brise soleil"],
            "match": {"type_name_patterns": ["brise"]}, **extra}


def test_registry_validates_and_names_each_category_once() -> None:
    registry = _registry()
    _validator().validate(registry)
    ids = [entry["id"] for entry in registry["entries"]]
    assert len(ids) == len(set(ids))
    pattern = re.compile(registry["naming_rules"]["id_pattern"])
    assert all(pattern.fullmatch(key) for key in ids)
    shared = yaml.safe_load(SHARED.read_text(encoding="utf-8"))["$defs"]
    schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))["$defs"]
    assert set(schema["object_family"]["enum"]) == set(shared["object_family"]["enum"])
    assert set(schema["match"]["properties"]) == set(vocabulary.MATCH_KEYS)


def test_the_profile_covers_openings_walls_structure_and_noise() -> None:
    labels = {entry["label"] for entry in _registry()["entries"]}
    assert {"porte-fenêtre", "fenêtre", "porte intérieure", "baie libre", "cloison", "mur extérieur",
            "poteau", "poutre", "semelle", "dalle", "escalier", "garde-corps"} <= labels
    ignored = {entry["id"] for entry in _registry()["entries"] if entry.get("ignore")}
    assert {"mobilier", "objet_generique"} <= ignored


def test_an_agency_adds_categories_but_never_changes_the_repository_ones() -> None:
    base = _registry()
    _validator().validate(_agency(_category()))
    assert vocabulary.merge_agency_file(base, _agency(_category()))["brise_soleil"]["origin"] == "agency"
    for broken, message in (
        (_category("poteau"), "add-only"),
        (_category(family="meuble"), "object family"),
        (_category(priority=-1), "priority"),
        (_category(synonyms=[]), "synonyms"),
        (_category(match={"couleur": "rouge"}), "known clues"),
        (_category(ignore="oui"), "ignore"),
    ):
        with pytest.raises(vocabulary.VocabularyUnavailable, match=message):
            vocabulary.merge_agency_file(base, _agency(broken))


def test_categories_are_loaded_by_priority(monkeypatch) -> None:
    monkeypatch.delenv(vocabulary.CATEGORY_OVERLAY_ENV, raising=False)
    loaded = vocabulary.categories()
    priorities = [entry["priority"] for entry in loaded]
    assert priorities == sorted(priorities) and loaded[0]["id"] == "fenetre_toute_hauteur"
