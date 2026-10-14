from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
PROJECTION = COCKPIT / "projection" / "project_anatomy_projection.js"
LOADER = COCKPIT / "data" / "cockpit_data_loader.js"
ASSEMBLER = COCKPIT / "projection" / "child_collection_assembler.js"
BOOTSTRAP = COCKPIT / "live_bootstrap.js"


def test_anatomy_projection_remains_read_only_and_does_not_infer_absence() -> None:
    source = PROJECTION.read_text(encoding="utf-8")

    assert 'entity_type: "project_anatomy_projection"' in source
    assert 'entity_type: "apu_object"' in source
    assert 'entity_type: "apu_source_representation"' in source
    assert '"Non mappé ≠ absent"' in source
    assert '"Couverture d’observation non persistée"' in source
    assert '"Hiérarchie non dérivée sans sémantique admise"' in source
    assert "available_actions: []" in source
    assert "fetch(" not in source


def test_data_loader_reads_anatomy_optionally_without_hiding_other_failures() -> None:
    source = LOADER.read_text(encoding="utf-8")

    assert "project-anatomy" in source
    assert "[404, 409]" in source
    assert "projectAnatomy: anatomyPayload?.project_anatomy || null" in source


def test_anatomy_is_loaded_before_child_assembly_and_attached_under_project() -> None:
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
    assembler = ASSEMBLER.read_text(encoding="utf-8")

    anatomy_module = '"projection/project_anatomy_projection.js"'
    assembler_module = '"projection/child_collection_assembler.js"'
    assert bootstrap.index(anatomy_module) < bootstrap.index(assembler_module)
    assert "context.state.projectAnatomy" in assembler
    assert "anatomy.project_ref !== context.selectedProjectId" in assembler
    assert "...assembleAnatomy(context)" in assembler


@pytest.mark.skipif(shutil.which("node") is None, reason="node is required for JS syntax checks")
@pytest.mark.parametrize(
    "path",
    [PROJECTION, LOADER, ASSEMBLER, BOOTSTRAP],
)
def test_anatomy_frontend_javascript_parses(path: Path) -> None:
    subprocess.run(["node", "--check", str(path)], check=True, capture_output=True, text=True)


@pytest.mark.skipif(shutil.which("node") is None, reason="node is required for JS behavior checks")
def test_cockpit_renders_claim_values_source_claims_and_native_identifiers() -> None:
    anatomy = {
        "project_ref": "project-1",
        "model_version": 2,
        "model_authority_ref": "contracts@baseline",
        "model_doctrine_ref": "doctrine@baseline",
        "summary": {
            "stable_object_count": 1,
            "source_representation_count": 1,
            "attribute_claim_count": 2,
            "relation_claim_count": 0,
            "unmapped_source_representation_count": 1,
            "attention_claim_count": 1,
        },
        "coverage": {"status": "not_persisted"},
        "structure": {
            "hierarchy": {"status": "not_derived"},
            "objects": [
                {
                    "object_id": "door-1",
                    "object_family": "element",
                    "display_name": "Porte",
                    "attribute_claims": [
                        {
                            "attribute_key": "architecture.width",
                            "value": {"value_type": "number", "value": 0.9, "unit": "m"},
                            "certainty": "E2",
                            "proof_status": "accepted_as_support",
                        }
                    ],
                    "relations": [],
                    "source_representation_refs": [],
                    "phase_refs": [],
                    "attention_claim_refs": [],
                }
            ],
        },
        "unmapped_material": [
            {
                "representation_id": "revit-1",
                "source_artifact_ref": "model.rvt",
                "source_kind": "revit",
                "proof_status": "source_incomplete",
                "identifiers": [{"scheme": "revit.unique_id", "value": "abc"}],
                "locators": [],
                "limitations": [],
                "attribute_claims": [
                    {
                        "attribute_key": "architecture.condition",
                        "value": {"value_type": "controlled_label", "value": "damaged"},
                        "certainty": "E1",
                        "proof_status": "requires_more_evidence",
                    }
                ],
            }
        ],
    }
    script = f"""
global.window = global;
require({str(PROJECTION)!r});
const cards = window.PantheonProjectAnatomyProjection.projectCards({json.dumps(anatomy)});
console.log(JSON.stringify(cards.children.map(card => ({{
  entity_type: card.entity_type,
  back: Object.fromEntries(card.back),
}}))));
"""

    completed = subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    cards = {item["entity_type"]: item["back"] for item in json.loads(completed.stdout)}

    assert "architecture.width : 0.9 m" in cards["apu_object"]["Attributs"]
    source = cards["apu_source_representation"]
    assert "revit.unique_id : abc" in source["Identifiants natifs"]
    assert "architecture.condition : damaged" in source["Claims d’attribut"]
