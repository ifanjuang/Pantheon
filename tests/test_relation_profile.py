"""Read-only tests for the Project Anatomy relation profile architecture@1.

They exercise the coherence rules of .github/scripts/check_relation_profile.py
on the governed profile and on deliberately broken copies. A declared relation
type is governable, not true, admitted, Evidence or approved.
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github/scripts/check_relation_profile.py"
PROFILE = ROOT / "registries/architecture_relation_profile.registry.json"
MODEL = ROOT / "docs/domain-packs/architecture/PROJECT_ANATOMY_MODEL.md"

DOCTRINE_RELATION_TYPES = {
    "identity.represents",
    "spatial.contains",
    "spatial.located_in",
    "spatial.adjacent_to",
    "architecture.opens_to",
    "architecture.hosted_by",
    "assembly.part_of",
    "model.instance_of",
    "project.belongs_to_group",
    "identity.replaced_by",
    "identity.split_into",
    "identity.merged_into",
    "identity.supersedes",
}


def _check_module():
    spec = importlib.util.spec_from_file_location("check_relation_profile", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _profile() -> dict:
    return json.loads(PROFILE.read_text(encoding="utf-8"))


def _entry(profile: dict, relation_id: str) -> dict:
    return next(entry for entry in profile["entries"] if entry["id"] == relation_id)


def test_relation_profile_check_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "architecture@1 coherent" in result.stdout


def test_section_6_names_exactly_the_active_doctrine_types() -> None:
    module = _check_module()
    named = set(module.doctrine_relation_types(MODEL.read_text(encoding="utf-8")))
    assert named == DOCTRINE_RELATION_TYPES
    active = {entry["id"] for entry in _profile()["entries"] if entry["status"] == "active"}
    assert active == DOCTRINE_RELATION_TYPES


def test_governed_profile_is_coherent() -> None:
    assert _check_module().coherence_failures(_profile()) == []


def test_relation_names_never_encode_time_or_negation() -> None:
    module = _check_module()
    profile = _profile()
    profile["entries"].append(
        dict(copy.deepcopy(_entry(profile, "spatial.adjacent_to")), id="spatial.was_adjacent_to")
    )
    failures = module.coherence_failures(profile)
    assert any("spatial.was_adjacent_to: name encodes time or negation" in item for item in failures)


def test_namespace_must_equal_family() -> None:
    module = _check_module()
    profile = _profile()
    _entry(profile, "spatial.bounded_by")["family"] = "architecture"
    failures = module.coherence_failures(profile)
    assert any("spatial.bounded_by: namespace 'spatial' differs" in item for item in failures)


def test_inverse_must_point_back() -> None:
    module = _check_module()
    profile = _profile()
    _entry(profile, "spatial.located_in")["inverse"] = None
    failures = module.coherence_failures(profile)
    assert any("spatial.contains: inverse 'spatial.located_in' does not point back" in item
               for item in failures)


def test_symmetric_relation_declares_no_inverse() -> None:
    module = _check_module()
    profile = _profile()
    _entry(profile, "spatial.adjacent_to")["inverse"] = "spatial.contains"
    failures = module.coherence_failures(profile)
    assert any("spatial.adjacent_to: a symmetric relation declares no inverse" in item
               for item in failures)


def test_deprecation_requires_a_live_replacement() -> None:
    module = _check_module()
    profile = _profile()
    _entry(profile, "architecture.connects_via")["status"] = "deprecated"
    failures = module.coherence_failures(profile)
    assert any("architecture.connects_via: deprecated without" in item for item in failures)


def test_inverse_pair_must_swap_endpoints() -> None:
    module = _check_module()
    profile = _profile()
    _entry(profile, "structure.supports")["object_object_families"] = ["element"]
    failures = module.coherence_failures(profile)
    assert any("inverse 'structure.supports' does not swap the endpoints" in item
               for item in failures)


def test_symmetric_relation_needs_identical_endpoints() -> None:
    module = _check_module()
    profile = _profile()
    _entry(profile, "spatial.adjacent_to")["object_object_families"] = ["element"]
    failures = module.coherence_failures(profile)
    assert any("spatial.adjacent_to: a symmetric relation needs identical endpoints" in item
               for item in failures)


def test_replaced_by_is_reserved_for_deprecated_entries() -> None:
    module = _check_module()
    profile = _profile()
    _entry(profile, "architecture.separates")["replaced_by"] = "spatial.bounded_by"
    failures = module.coherence_failures(profile)
    assert any("architecture.separates: replaced_by is reserved" in item for item in failures)


def test_activation_requires_naming_in_section_6() -> None:
    module = _check_module()
    profile = _profile()
    _entry(profile, "spatial.bounded_by")["status"] = "active"
    failures = module.doctrine_failures(profile, MODEL.read_text(encoding="utf-8"))
    assert any("spatial.bounded_by: active in the profile but not named by section 6" in item
               for item in failures)


def test_allowed_qualifiers_need_a_vocabulary() -> None:
    module = _check_module()
    profile = _profile()
    _entry(profile, "construction.junction_with")["allowed_qualifiers"] = ["junction_kind"]
    failures = module.coherence_failures(profile)
    assert any("allowed qualifier 'junction_kind' has no vocabulary" in item for item in failures)


def test_profile_carries_no_ifc_global_id_as_identity() -> None:
    represents = _entry(_profile(), "identity.represents")
    ifc = represents.get("ifc") or []
    assert ifc and all(item["fidelity"] == "none" for item in ifc)
    assert "never becomes Pantheon identity" in ifc[0]["note"]


def test_registry_index_lists_existing_consumers() -> None:
    index = json.loads((ROOT / "registries/registry_index.json").read_text(encoding="utf-8"))
    entry = next(item for item in index["entries"] if item["id"] == "architecture_relation_profile")
    assert entry["status"] == "candidate"
    assert entry["profile"] == "architecture@1"
    for consumer in entry["consumers"]:
        assert (ROOT / consumer).is_file(), consumer
