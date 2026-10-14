"""I8 representative Capability vertical and adversarial qualification."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "catalog" / "examples" / "i8-capability-vertical-qualification.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _validator(path: Path) -> jsonschema.Draft202012Validator:
    schema = _load_yaml(path) if path.suffix in {".yaml", ".yml"} else _load_json(path)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())


def _set_path(targets: dict[str, dict[str, Any]], dotted_path: str, value: Any) -> None:
    parts = dotted_path.split(".")
    target = targets[parts[0]]
    for part in parts[1:-1]:
        target = target[part]
    target[parts[-1]] = copy.deepcopy(value)


def _base_records() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    corpus = _load_yaml(CORPUS_PATH)
    representative = corpus["representative"]
    records = {
        "resource": _load_yaml(ROOT / representative["resource"]),
        "passport": _load_yaml(ROOT / representative["passport"]),
        "binding": _load_yaml(ROOT / representative["binding"]),
        "activation": _load_yaml(ROOT / representative["activation"]),
        "observation": _load_yaml(ROOT / representative["compatibility_observation"]),
    }
    return corpus, records


def _scenario_records(scenario: dict[str, Any]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    corpus, records = _base_records()
    records = copy.deepcopy(records)
    for path, value in scenario.get("mutations", {}).items():
        _set_path(records, path, value)
    return corpus, records


def _chain_errors(records: dict[str, dict[str, Any]]) -> list[str]:
    passport = records["passport"]
    binding = records["binding"]
    activation = records["activation"]
    observation = records["observation"]

    if binding["metadata"]["status"] == "unbound":
        return ["binding_unbound"]

    errors: list[str] = []
    if binding["spec"]["capability_passport_id"] != passport["passport_id"]:
        errors.append("passport_identity_mismatch")

    provenance = passport["implementation_provenance"]
    anchor = binding["spec"]["implementation_anchor"]
    if anchor["kind"] == "content_digest" and anchor["value"] != provenance.get("content_digest"):
        errors.append("binding_anchor_mismatch")

    if activation["spec"]["binding_id"] != binding["metadata"]["id"]:
        errors.append("activation_binding_mismatch")

    if observation["subject"]["binding_id"] != binding["metadata"]["id"]:
        errors.append("observation_binding_mismatch")
    if observation["subject"]["implementation_anchor"] != binding["spec"]["implementation_anchor"]:
        errors.append("observation_anchor_mismatch")
    return errors


def _validate_governed_records(records: dict[str, dict[str, Any]]) -> None:
    _validator(ROOT / "schemas" / "capability_passport.schema.yaml").validate(records["passport"])
    _validator(ROOT / "catalog" / "schemas" / "capability-binding.schema.json").validate(records["binding"])
    _validator(ROOT / "catalog" / "schemas" / "capability-activation.schema.json").validate(records["activation"])
    _validator(ROOT / "catalog" / "schemas" / "capability-compatibility-observation.schema.json").validate(records["observation"])


def _assert_invariant(name: str, scenario: dict[str, Any], records: dict[str, dict[str, Any]]) -> None:
    passport = records["passport"]
    binding = records["binding"]
    activation = records["activation"]
    observation = records["observation"]
    runtime = scenario.get("runtime_facts", {})

    if name == "non_authorizing_chain":
        assert passport["governance"]["task_authorization"] == "unauthorized"
        assert binding["governance"]["dependency_adopted"] is False
        assert binding["governance"]["task_authorized"] is False
        assert activation["governance"]["runtime_activation_effect"] == "none"
        assert activation["governance"]["task_authorization_effect"] == "none"
        assert observation["governance"]["authorization_effect"] == "none"
        assert observation["governance"]["evidence_effect"] == "none"
    elif name == "compatibility_safety_independent":
        assert observation["observation"]["compatibility_status"] == "compatible"
        assert observation["observation"]["safety_status"] != "qualified"
    elif name == "activation_task_authorization_independent":
        assert activation["spec"]["state"] == "project_enabled"
        assert activation["governance"]["task_authorization_effect"] == "none"
        assert passport["governance"]["task_authorization"] == "unauthorized"
    elif name == "prior_observation_not_inherited":
        assert observation["governance"]["release_replacement_inherits_observation"] is False
    elif name == "replacement_inherits_nothing":
        assert activation["governance"]["binding_replacement_inherits_activation"] is False
        assert observation["governance"]["release_replacement_inherits_observation"] is False
        assert binding["governance"]["dependency_adopted"] is False
        assert binding["governance"]["task_authorized"] is False
    elif name == "installed_not_admitted":
        assert runtime["installation_state"] == "installed"
        assert passport["status"] == "candidate"
        assert passport["governance"]["task_authorization"] == "unauthorized"
    elif name == "healthy_not_authorized":
        assert runtime["endpoint_health"] == "healthy"
        assert binding["governance"]["task_authorized"] is False
    elif name == "healthy_not_safe":
        assert observation["observation"]["health_status"] == "healthy"
        assert observation["observation"]["safety_status"] == "not_qualified"
    elif name == "stale_observation_non_authorizing":
        assert observation["metadata"]["status"] == "stale"
        assert observation["observation"]["freshness_status"] == "stale"
        assert observation["governance"]["authorization_effect"] == "none"
        assert observation["governance"]["evidence_effect"] == "none"
    elif name == "unavailable_binding_fails_closed":
        assert binding["metadata"]["status"] == "unbound"
        assert binding["spec"]["capability_passport_id"] is None
        assert binding["spec"]["implementation_anchor"] is None
        assert binding["governance"]["task_authorized"] is False
    elif name == "ui_projection_non_authorizing":
        fixture = scenario["downstream_projection_fixture"]
        assert fixture["binding_id"] == binding["metadata"]["id"]
        assert fixture["activation_state"] == activation["spec"]["state"]
        assert fixture["compatibility_status"] == observation["observation"]["compatibility_status"]
        assert "task_authorized" not in fixture
        assert passport["governance"]["task_authorization"] == "unauthorized"
    else:
        raise AssertionError(f"unknown I8 invariant: {name}")


def _scenarios() -> list[dict[str, Any]]:
    return _load_yaml(CORPUS_PATH)["scenarios"]


@pytest.mark.parametrize("scenario", _scenarios(), ids=lambda item: item["id"])
def test_i8_vertical_scenarios_keep_exact_identity_and_authority_boundaries(scenario: dict[str, Any]) -> None:
    corpus, records = _scenario_records(scenario)
    _validate_governed_records(records)

    assert records["binding"]["spec"]["slot_id"] == corpus["representative"]["slot_id"]
    assert records["activation"]["spec"]["scope"]["scope_id"] == corpus["representative"]["project_scope_id"]
    assert _chain_errors(records) == scenario["expected_chain_errors"]

    for invariant in scenario["invariants"]:
        _assert_invariant(invariant, scenario, records)


def test_i8_corpus_covers_the_parent_adversarial_matrix_without_new_owners() -> None:
    scenarios = {scenario["id"] for scenario in _scenarios()}
    assert scenarios == {
        "baseline_exact_chain",
        "release_digest_drift",
        "binding_replacement_without_inheritance",
        "installed_available_but_not_admitted",
        "healthy_but_not_safety_qualified",
        "activated_but_task_unauthorized",
        "stale_observation",
        "unavailable_binding",
        "ui_projection_cannot_authorize",
    }

    corpus, records = _base_records()
    assert records["resource"]["metadata"]["id"] == "docling"
    assert records["resource"]["metadata"]["status"] == "candidate"
    assert records["binding"]["spec"]["resource_id"] == records["resource"]["metadata"]["id"]
    assert corpus["representative"]["slot_id"] == "document_structural_analysis"
