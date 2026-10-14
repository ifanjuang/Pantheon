from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_evidence_topology_is_current_and_client_agnostic():
    text = _read("docs/governance/EVIDENCE_TOPOLOGY.md")
    assert "OpenWebUI" not in text
    assert "OPENWEBUI_INTEGRATION.md" not in text
    assert "schema candidate note" not in text.lower()
    assert "Historical changelog addendum" not in text
    assert "schemas/workflow_manifest.schema.yaml" in text
    assert "schemas/task_contract.schema.yaml" in text
    assert "schemas/evidence_pack.schema.yaml" in text
    assert "reasoning_topology" in text
    assert "Evidence Items" in text
    assert "Handoff Artifacts" in text
    assert "Pantheon Cockpit" in text
    assert "topology_dispatch: false" in text
    assert "runtime topology != governance authority" in text


def test_evidence_topology_machine_contract_exists_in_current_schemas():
    workflow = _read("schemas/workflow_manifest.schema.yaml")
    task = _read("schemas/task_contract.schema.yaml")
    evidence = _read("schemas/evidence_pack.schema.yaml")

    assert "reasoning_topology_requirements:" in workflow
    assert "evidence_item_requirements:" in workflow
    assert "handoff_artifact_requirements:" in workflow
    assert "topology_dispatch: false" in workflow

    assert "reasoning_topology:" in task
    assert "topology_dispatch: false" in task

    assert "evidence_items:" in evidence
    assert "handoff_artifacts:" in evidence
    assert "reasoning_topology_record:" in evidence
    assert "topology_dispatch: false" in evidence
    assert "hidden_chain_of_thought_archive: false" in evidence


def test_evidence_topology_examples_are_explicitly_illustrative_not_schema_fixtures():
    text = _read("docs/examples/evidence_topology/README.md")
    assert "OpenWebUI" not in text
    assert "not current schema-conformance fixtures" in text
    assert "predate those current shapes" in text
    assert "must not be presented as validating against them" in text
    assert "schemas/workflow_manifest.schema.yaml" in text
    assert "schemas/task_contract.schema.yaml" in text
    assert "schemas/evidence_pack.schema.yaml" in text
    assert "Pantheon Cockpit" in text
