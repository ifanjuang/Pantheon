"""Qualification checks for the source-reviewed zoom-map -> visual-focus V0 seam."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "tests" / "fixtures" / "zoom_map_visual_focus_pilot.json"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "zoom_map_visual_focus"
SOURCE = FIXTURE_DIR / "source.svg"
SIDECAR = FIXTURE_DIR / "source.svg.markers.json"
REGISTER = ROOT / "docs" / "governance" / "EXTERNAL_TOOL_PLACEMENT_REGISTER.md"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_dimensions() -> tuple[int, int]:
    root = ET.parse(SOURCE).getroot()
    return int(root.attrib["width"]), int(root.attrib["height"])


def _focus_rectangles(sidecar: dict, layer_name: str) -> list[dict]:
    layer_ids = {
        layer["id"]
        for layer in sidecar.get("drawLayers", [])
        if layer.get("name") == layer_name and layer.get("visible") is True
    }
    return [
        drawing
        for drawing in sidecar.get("drawings", [])
        if drawing.get("layerId") in layer_ids
        and drawing.get("visible") is True
        and drawing.get("kind") == "rect"
    ]


def _normalized_bbox(drawing: dict) -> list[float]:
    rect = drawing["rect"]
    x0, x1 = sorted((float(rect["x0"]), float(rect["x1"])))
    y0, y1 = sorted((float(rect["y0"]), float(rect["y1"])))
    assert 0.0 <= x0 < x1 <= 1.0
    assert 0.0 <= y0 < y1 <= 1.0
    return [x0, y0, x1, y1]


def _pixel_bbox(normalized: list[float], width: int, height: int) -> list[int]:
    x0, y0, x1, y1 = normalized
    return [
        round(x0 * width),
        round(y0 * height),
        round(x1 * width),
        round(y1 * height),
    ]


def test_zoom_map_candidate_is_source_reviewed_not_runtime_accepted() -> None:
    pilot = _load(PILOT)

    assert pilot["pilot_id"] == "zoom-map-visual-focus-001"
    assert pilot["capability"] == "optional_visual_focus_client"
    assert pilot["execution_status"] == "source_reviewed_mapping_fixture_runtime_smoke_pending"

    reference = pilot["reference_candidate"]
    assert reference == {
        "repository": "Jareika/zoom-map",
        "reviewed_release": "2.2.8",
        "reviewed_commit": "f6daa072c484dff1235a070da48d703de51cf143",
        "license": "MIT",
        "reviewed_source_blobs": {
            "README.md": "0236e225c6658600c77e6da2f18b15ed40794ed4",
            "src/markerStore.ts": "82ec77f13dc5ef853e21971d09cb2ea5a5561ce2",
            "src/map.ts": "870faaa176dda4fd586ffb66c9d5ac91d8569969",
        },
    }

    register = REGISTER.read_text(encoding="utf-8")
    assert "Jareika/zoom-map" not in register


def test_zoom_map_fixture_binds_regions_to_exact_source() -> None:
    pilot = _load(PILOT)
    source = SOURCE.read_bytes()

    assert hashlib.sha256(source).hexdigest() == pilot["fixture"]["image_sha256"]
    assert _source_dimensions() == (
        pilot["fixture"]["image_width_px"],
        pilot["fixture"]["image_height_px"],
    )

    boundaries = set(pilot["existing_owner_alignment"]["rules"])
    assert {
        "zoom-map sidecar != Pantheon document.yaml",
        "zoom-map UX sidecar != document routing persistence",
        "plugin drawing id != governed identity",
        "human focus != professional conclusion",
        "annotation != Evidence",
        "projection != persistence authority",
    } <= boundaries


def test_three_focus_rectangles_map_to_hermes_native_pixel_regions() -> None:
    pilot = _load(PILOT)
    sidecar = _load(SIDECAR)
    width, height = _source_dimensions()

    selected = _focus_rectangles(sidecar, pilot["fixture"]["focus_layer_name"])
    assert [drawing["id"] for drawing in selected] == ["focus_a", "focus_b", "focus_c"]

    expected = {row["drawing_id"]: row for row in pilot["fixture"]["expected_regions"]}
    assert set(expected) == {"focus_a", "focus_b", "focus_c"}

    for drawing in selected:
        row = expected[drawing["id"]]
        normalized = _normalized_bbox(drawing)
        assert normalized == row["normalized_bbox"]
        assert _pixel_bbox(normalized, width, height) == row["pixel_bbox"]
        assert drawing["style"]["label"] == row["label"]


def test_other_layers_are_not_implicitly_selected() -> None:
    pilot = _load(PILOT)
    sidecar = _load(SIDECAR)

    selected_ids = {
        drawing["id"]
        for drawing in _focus_rectangles(sidecar, pilot["fixture"]["focus_layer_name"])
    }
    assert "reference_whole" not in selected_ids
    assert sidecar["activeBase"] == "source.svg"
    assert sidecar["bases"] == [{"path": "source.svg", "name": "Synthetic visual focus"}]


def test_v0_reuses_visual_focus_without_admitting_a_sidecar_or_provider() -> None:
    pilot = _load(PILOT)
    owners = pilot["existing_owner_alignment"]
    profile = pilot["candidate_profile"]

    assert owners["hermes_skill"] == "templates/hermes/skills/visual-focus/SKILL.md"
    assert owners["native_runtime_surface"] == "vision_analyze.region"
    assert owners["obsidian_workspace_qualification"] == "Pantheon-Next#714"
    assert owners["document_sidecar_boundary"] == "Pantheon-Next#859"
    assert owners["document_routing_decision"] == "Pantheon-Next#865"

    assert profile["name"] == "sidecar_read_only_rect_to_visual_focus"
    assert profile["write_behavior"] == "none in this qualification"
    assert "not a Pantheon production sidecar" in profile["sidecar_posture"]
    assert "document routing persistence" in profile["sidecar_posture"]
    assert "currentness owner" in profile["sidecar_posture"]
    assert "Evidence store" in profile["sidecar_posture"]

    assert set(profile["deferred"]) == {
        "circle-to-region conversion",
        "polygon-to-region conversion",
        "polyline handling",
        "point-marker padding policy",
        "mask or segmentation",
        "automatic plugin-to-Hermes command/button",
        "production sidecar admission",
    }


def test_runtime_smoke_remains_required_before_placement() -> None:
    pilot = _load(PILOT)
    cases = {case["id"]: case for case in pilot["cases"]}

    assert cases["three_human_rectangles_map_to_native_regions"]["runtime_smoke_required"] is False
    assert cases["other_layer_is_not_implicitly_selected"]["runtime_smoke_required"] is False
    assert cases["exact_source_digest_precedes_focus_reuse"]["runtime_smoke_required"] is False
    assert cases["obsidian_emits_equivalent_sidecar"]["runtime_smoke_required"] is True
    assert cases["hermes_consumes_selected_regions"]["runtime_smoke_required"] is True

    gate = pilot["execution_gate"]
    assert "isolated Obsidian test vault" in gate["required_runtime_smoke"]
    assert "at least two selected regions" in gate["required_runtime_smoke"]
    assert "Do not add zoom-map to the external-tool placement register" in gate["register_placement"]
    assert "Do not treat source review" in gate["forbidden_shortcut"]
