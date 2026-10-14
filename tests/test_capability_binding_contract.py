import copy
import json
from pathlib import Path

import jsonschema
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "catalog" / "schemas" / "capability-binding.schema.json"
BOUND_PATH = ROOT / "catalog" / "bindings" / "document-analysis-docling.yaml"
UNBOUND_PATH = ROOT / "catalog" / "bindings" / "external-runtime-memory-unbound.yaml"
HERMES_BINDINGS = ROOT / "docs" / "governance" / "HERMES_CAPABILITY_BINDINGS.md"
OBSOLETE_INDEX = ROOT / "docs" / "governance" / "authority" / "OBSOLETE_AND_ABSENT_INDEX.md"


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    assert isinstance(value, dict)
    return value


def _validator() -> jsonschema.Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def test_exact_binding_candidate_is_selection_only_and_non_authorizing() -> None:
    binding = _load_yaml(BOUND_PATH)
    _validator().validate(binding)

    assert binding["metadata"]["status"] == "preferred_candidate"
    assert binding["spec"]["binding_role"] == "preferred"
    assert binding["spec"]["implementation_anchor"]["kind"] == "content_digest"
    assert binding["governance"] == {
        "selection_only": True,
        "dependency_adopted": False,
        "installation_authorized": False,
        "activation_authorized": False,
        "task_authorized": False,
    }


def test_unbound_slot_is_valid_governance_state_not_missing_data() -> None:
    binding = _load_yaml(UNBOUND_PATH)
    _validator().validate(binding)

    assert binding["metadata"]["status"] == "unbound"
    assert binding["spec"]["binding_role"] == "unbound"
    assert binding["spec"]["capability_passport_id"] is None
    assert binding["spec"]["implementation_anchor"] is None


def test_bound_relation_requires_exact_capability_and_release_anchor() -> None:
    binding = _load_yaml(BOUND_PATH)

    without_passport = copy.deepcopy(binding)
    without_passport["spec"]["capability_passport_id"] = None
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(without_passport)

    without_anchor = copy.deepcopy(binding)
    without_anchor["spec"]["implementation_anchor"] = None
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(without_anchor)


def test_binding_replacement_does_not_promote_dependency_or_authority() -> None:
    first = _load_yaml(BOUND_PATH)
    replacement = copy.deepcopy(first)
    replacement["metadata"]["id"] = "capability_binding_document_analysis_docling_next"
    replacement["spec"]["implementation_anchor"]["value"] = "sha256:" + "b" * 64
    replacement["spec"]["supersedes"] = first["metadata"]["id"]

    _validator().validate(first)
    _validator().validate(replacement)

    assert first["spec"]["slot_id"] == replacement["spec"]["slot_id"]
    assert first["spec"]["capability_passport_id"] == replacement["spec"]["capability_passport_id"]
    assert first["spec"]["implementation_anchor"] != replacement["spec"]["implementation_anchor"]
    assert replacement["governance"]["dependency_adopted"] is False
    assert replacement["governance"]["activation_authorized"] is False
    assert replacement["governance"]["task_authorized"] is False


def test_binding_status_vocabulary_reuses_existing_doctrine_and_does_not_restore_presets() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    doctrine = HERMES_BINDINGS.read_text(encoding="utf-8")
    obsolete = OBSOLETE_INDEX.read_text(encoding="utf-8")

    statuses = schema["properties"]["metadata"]["properties"]["status"]["enum"]
    for status in (
        "external_reference",
        "watch",
        "candidate",
        "to_verify",
        "preferred_candidate",
        "fallback_candidate",
        "rejected",
        "superseded",
    ):
        assert status in statuses
        assert status in doctrine

    assert "Former installation-composition manifests under `catalog/`" in obsolete
    assert not (ROOT / "catalog" / "presets").exists()
