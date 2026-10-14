import copy
import json
from pathlib import Path

import jsonschema
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "catalog" / "schemas" / "capability-activation.schema.json"
EXAMPLE_PATH = ROOT / "catalog" / "activations" / "document-analysis-docling-project.yaml"
MODULE_SCHEMA = ROOT / "schemas" / "module_manifest.schema.yaml"
TASK_SCHEMA = ROOT / "schemas" / "task_contract.schema.yaml"


def _load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _validator() -> jsonschema.Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def test_project_activation_is_scoped_reviewed_and_non_authorizing() -> None:
    activation = _load_yaml(EXAMPLE_PATH)
    _validator().validate(activation)

    assert activation["metadata"]["status"] == "reviewed"
    assert activation["spec"]["state"] == "project_enabled"
    assert activation["spec"]["scope"]["scope_type"] == "project"
    assert activation["spec"]["decision_ref"]
    assert activation["governance"]["runtime_activation_effect"] == "none"
    assert activation["governance"]["task_authorization_effect"] == "none"
    assert activation["governance"]["automatic_activation"] is False


def test_enabled_state_requires_reviewed_record_scope_and_decision_reference() -> None:
    activation = _load_yaml(EXAMPLE_PATH)

    no_decision = copy.deepcopy(activation)
    no_decision["spec"]["decision_ref"] = None
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(no_decision)

    no_scope = copy.deepcopy(activation)
    no_scope["spec"]["scope"] = None
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(no_scope)

    candidate_record = copy.deepcopy(activation)
    candidate_record["metadata"]["status"] = "candidate"
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(candidate_record)


def test_replacement_binding_does_not_inherit_activation() -> None:
    activation_a = _load_yaml(EXAMPLE_PATH)
    activation_b = copy.deepcopy(activation_a)
    activation_b["metadata"]["id"] = "capability_activation_document_analysis_docling_next_project_demo"
    activation_b["spec"]["binding_id"] = "capability_binding_document_analysis_docling_next"
    activation_b["spec"]["decision_ref"] = "decision.capability_activation.document_analysis_docling_next.project_demo"
    activation_b["spec"]["supersedes"] = activation_a["metadata"]["id"]

    _validator().validate(activation_a)
    _validator().validate(activation_b)

    assert activation_a["spec"]["binding_id"] != activation_b["spec"]["binding_id"]
    assert activation_b["governance"]["binding_replacement_inherits_activation"] is False
    assert activation_b["governance"]["task_authorization_effect"] == "none"


def test_activation_vocabulary_reuses_module_and_task_scope_contracts() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    module = _load_yaml(MODULE_SCHEMA)
    task = _load_yaml(TASK_SCHEMA)

    activation_states = set(schema["properties"]["spec"]["properties"]["state"]["enum"])
    module_states = set(
        module["properties"]["activation"]["properties"]["state"]["enum"]
    )
    assert activation_states == module_states

    activation_scopes = set(
        schema["properties"]["spec"]["properties"]["scope"]["oneOf"][1]["properties"]["scope_type"]["enum"]
    )
    task_scopes = set(task["properties"]["scope"]["properties"]["scope_type"]["enum"])
    assert activation_scopes == task_scopes
