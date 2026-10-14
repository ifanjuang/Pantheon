from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "graphify-structure-q2.yml"
REGISTRY = ROOT / "implementation" / "qualification" / "external-pins.json"
ANALYZER = ROOT / "implementation" / "tools" / "qualify_graphify_structure.py"
SNAPSHOT_HELPER = ROOT / "implementation" / "tools" / "git_material_snapshot.py"
OBSERVED = ROOT / "tests" / "fixtures" / "graphify_structural_gain_observed.json"


def test_q2_uses_canonical_graphify_pin_without_copying_it() -> None:
    raw = WORKFLOW.read_text(encoding="utf-8")
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    pin = registry["pins"]["graphify"]

    assert pin["kind"] == "package"
    assert pin["env_prefix"] == "GRAPHIFY"
    assert pin["repository"] == "Graphify-Labs/graphify"
    assert pin["package"] == "graphifyy"
    assert isinstance(pin["version"], str) and pin["version"]
    assert re.fullmatch(r"[0-9a-f]{40}", pin["ref"])

    assert "export_external_qualification_pins.py" in raw
    assert " graphify" in raw
    assert "${{ env.GRAPHIFY_REPOSITORY }}" in raw
    assert "${{ env.GRAPHIFY_REF }}" in raw
    assert pin["version"] not in raw
    assert pin["ref"] not in raw
    assert "latest" not in raw.lower()


def test_q2_is_bounded_code_only_read_only_and_uses_shared_snapshot() -> None:
    raw = WORKFLOW.read_text(encoding="utf-8")

    assert raw.count('graphify extract "$GITHUB_WORKSPACE/monorepo"') == 2
    assert raw.count("            --code-only \\") == 2
    assert raw.count("            --no-cluster \\") == 2
    assert "--global" not in raw
    assert "graphify watch" not in raw
    assert "graphify install" not in raw
    assert "semantic LLM extraction" in raw
    assert "implementation/tools/git_material_snapshot.py" in raw
    assert "snapshot_tracked_material" in raw
    assert "porcelain_status" in raw
    assert SNAPSHOT_HELPER.exists()
    assert '"pantheon_state_mutated": bool(changed or status)' in raw
    assert '"evidence_admitted": False' in raw
    assert '"governed_relations_persisted": False' in raw
    assert '"provider_binding_changed": False' in raw
    assert '"mutation_inventory_replaced": False' in raw
    assert "contents: read" in raw


def test_q2_observes_determinism_without_turning_a_provider_finding_into_authority() -> None:
    raw = WORKFLOW.read_text(encoding="utf-8")

    assert "run1/graphify-out/graph.json" in raw
    assert "run2/graphify-out/graph.json" in raw
    assert "same_normalized_graph_fingerprint" in raw
    assert "same_counts" in raw
    assert "same_relation_histogram" in raw
    assert "mismatch is a provider finding, not a harness failure" in raw
    assert "actions/upload-artifact@v4" in raw


def test_q2_analyzer_keeps_native_mutation_inventory_authoritative() -> None:
    raw = ANALYZER.read_text(encoding="utf-8")

    for target in (
        '"policy_gate"',
        '"enforce_consequential"',
        '"execution_results"',
        '"apu_owner"',
        '"knowledge"',
        '"project_claim"',
    ):
        assert target in raw

    assert '"is_evidence": False' in raw
    assert '"is_governed_relation": False' in raw
    assert '"qualifies_mutation_gate": False' in raw
    assert '"authorizes_persistence": False' in raw
    assert '"changes_provider_binding": False' in raw
    assert "Pantheon native mutation inventory remains authoritative" in raw
    assert "normalized_graph_fingerprint" in raw
    assert "cyclic_components" in raw
    assert "blast_radius_targets" in raw


def test_observed_q2_result_is_bound_to_current_pin_but_selects_no_binding() -> None:
    observed = json.loads(OBSERVED.read_text(encoding="utf-8"))
    pin = json.loads(REGISTRY.read_text(encoding="utf-8"))["pins"]["graphify"]

    assert observed["candidate"]["version"] == pin["version"]
    assert observed["candidate"]["ref"] == pin["ref"]
    assert observed["execution"]["same_normalized_graph_fingerprint"] is True
    assert observed["execution"]["tracked_material_unchanged"] is True
    assert observed["execution"]["pantheon_state_mutated"] is False
    assert observed["result"]["marginal_structural_signal_observed"] is True
    assert observed["result"]["existing_capability_slot"] == "structural_repo_analysis"
    assert observed["result"]["preferred_binding_change"] is False
    assert observed["result"]["provider_binding_changed"] is False
    assert observed["result"]["dependency_adopted"] is False
