"""Reading of the current model: sides, façades, grid lines, neighbours, and its cache.

The geometry helpers are tested on synthetic shapes; no project model is involved.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

shapely = pytest.importorskip("shapely")
from shapely.geometry import box  # noqa: E402

from mvp_vertical import anatomy_export, model_reading as reading  # noqa: E402


@pytest.mark.parametrize("vector, north, expected", [
    ((0, 1), 0, "nord"), ((1, 0), 0, "est"), ((0, -1), 0, "sud"), ((-1, 0), 0, "ouest"),
    ((0, 1), 90, "ouest"),  # model north turned a quarter: +Y faces west
])
def test_facade_follows_the_model_north(vector, north, expected) -> None:
    assert reading.facade(*vector, north_deg=north) == expected


def _spaces():
    # Two rooms side by side along x, a wall on x = 4 between them.
    return [{"id": "salon", "poly": box(0, 0, 4, 5), "z": (0.0, 2.6)},
            {"id": "cuisine", "poly": box(4.2, 0, 8, 5), "z": (0.0, 2.6)}]


def test_an_axis_finds_the_space_on_each_side_or_the_outside() -> None:
    # A wall along y at x = 4.1: normal +x points to the kitchen.
    assert reading.side_spaces((4.1, 2.5), (1.0, 0.0), 1.0, _spaces()) == ("cuisine", "salon")
    # A façade wall along x at y = 5.1: the outside has no space.
    assert reading.side_spaces((2.0, 5.1), (0.0, 1.0), 1.0, _spaces()) == (None, "salon")
    # Another level does not count.
    assert reading.side_spaces((4.1, 2.5), (1.0, 0.0), 6.0, _spaces()) == (None, None)


def test_grid_position_says_on_a_line_or_between_two() -> None:
    axes = {"A": ((0, 0), (0, 1)), "B": ((5, 0), (0, 1)), "1": ((0, 0), (1, 0)), "2": ((0, 4), (1, 0))}
    assert reading.grid_position((5.05, 2.0), axes, direction=(0, 1)) == "sur la file B ; entre 1 et 2"
    assert reading.grid_position((2.5, 2.0), axes) == "entre B et A ; entre 1 et 2"
    # A wall across line B (perpendicular) is not "on" it.
    assert reading.grid_position((5.05, 2.0), axes, direction=(1, 0)).startswith("au-delà de la file B")
    assert reading.grid_position((1, 1), {}) is None


def test_neighbours_come_from_doors_and_shared_walls() -> None:
    openings = [{"id": "p1", "kind": "porte", "sides": ["cuisine", "salon"]},
                {"id": "f1", "kind": "fenêtre", "sides": ["cuisine", None]}]
    walls = [{"id": "m1", "sides": ["salon", "cuisine"]}, {"id": "m2", "sides": ["salon", None]}]
    assert reading.neighbours(openings, walls) == [
        {"spaces": ["cuisine", "salon"], "via": "mur", "elements": ["m1"]},
        {"spaces": ["cuisine", "salon"], "via": "porte", "elements": ["p1"]},
    ]


def test_a_model_is_read_once_per_file_and_a_bad_model_never_blocks(tmp_path, monkeypatch) -> None:
    model = tmp_path / "DEMO_E_261006.ifc"
    model.write_text("ISO-10303-21;")
    calls = []
    monkeypatch.setattr(reading, "read", lambda path: calls.append(path) or {"spaces": [], "openings": [], "walls": []})
    out = tmp_path / "pub" / "DEMO.maquette-maquette.json"
    assert reading.ensure(model, out, piece="MAQUETTE", index="E")["status"] == "read"
    assert reading.ensure(model, out, piece="MAQUETTE", index="E")["status"] == "cached"
    assert len(calls) == 1 and json.loads(out.read_text())["source"]["index"] == "E"
    model.write_text("ISO-10303-21; changed")
    monkeypatch.setattr(reading, "read", lambda path: (_ for _ in ()).throw(RuntimeError("damaged")))
    assert reading.ensure(model, out, piece="MAQUETTE")["status"] == "unreadable"
    assert reading.ensure(tmp_path / "absent.ifc", out, piece="MAQUETTE")["status"] == "absent"


def test_the_export_reads_the_current_model_pieces_only(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MVP_AFFAIRES_ROOT", str(tmp_path / "affaires"))
    seen = []
    monkeypatch.setattr(reading, "ensure", lambda path, out, **kw: seen.append((path.name, out.name, kw)) or {"status": "read"})
    pieces = {"pieces": [
        {"piece": "MAQUETTE", "category": "projet", "current": {"index": "E", "paths": ["CAD/DEMO_E.ifc"]}},
        {"piece": "PLAN RDC", "category": "projet", "current": {"index": "E", "paths": ["DCE/plan.pdf"]}},
        {"piece": "DEVIS IFC", "category": "a_confronter", "current": {"paths": ["ACT/devis.ifc"]}},
    ]}
    assert anatomy_export.read_current_models("DEMO", pieces, tmp_path) == [{"status": "read"}]
    assert [(model, kwargs) for model, _, kwargs in seen] == [("DEMO_E.ifc", {"piece": "MAQUETTE", "index": "E"})]
    # the sheet is named by the model file fingerprint, so an unchanged file is never read twice
    assert re.fullmatch(r"DEMO\.maquette-maquette-[0-9a-f]{12}\.json", seen[0][1])


@pytest.mark.parametrize("cls, exterior, sill, height, width, declared, expected", [
    ("IfcWindow", True, 0.0, 2.8, 1.86, None, "porte-fenêtre"),       # exterior door in a window family
    ("IfcWindow", True, 0.9, 1.2, 1.0, None, "fenêtre"),
    ("IfcWindow", True, 0.0, 2.2, 0.52, None, "fenêtre toute hauteur"),
    ("IfcDoor", True, 0.0, 2.07, 0.8, "Int. Simple:PP", "porte extérieure"),
    ("IfcDoor", False, 0.0, 2.07, 0.8, None, "porte intérieure"),
    ("IfcWindow", False, 1.0, 1.0, 1.0, None, "châssis intérieur"),
])
def test_the_nature_of_an_opening_comes_from_geometry_not_the_family(cls, exterior, sill, height, width, declared, expected) -> None:
    nature, clues = reading.opening_nature(cls, exterior=exterior, sill_m=sill, height_m=height, width_m=width, declared_type=declared)
    assert nature == expected
    assert clues[0] == f"classe IFC {cls}"
    if declared:
        assert "le type déclaré dit intérieur, la géométrie dit extérieur" in clues


def test_spaces_of_one_volume_are_open_onto_each_other_unless_a_wall_or_door_links_them() -> None:
    geo = [{"id": "sejour", "poly": box(0, 0, 5, 5), "z": (0.0, 2.6)},
           {"id": "cuisine", "poly": box(5.01, 0, 8, 5), "z": (0.0, 2.6)},   # touching, no wall
           {"id": "chambre", "poly": box(8.2, 0, 11, 5), "z": (0.0, 2.6)}]   # behind a 20 cm wall
    pairs = reading.open_neighbours(geo, set())
    assert [p["spaces"] for p in pairs] == [["cuisine", "sejour"]] and pairs[0]["longueur_m"] >= 4.5
    assert reading.open_neighbours(geo, {frozenset(("sejour", "cuisine"))}) == []


def test_an_empty_side_inside_the_building_outline_is_unmodelled_not_outside() -> None:
    outline = reading.envelope([box(0, 0, 4, 10), box(6, 0, 10, 10), box(4, 0, 6, 3), box(4, 7, 6, 10)])
    assert outline.contains(shapely.geometry.Point(5, 5))      # a stair hall without a space
    assert not outline.contains(shapely.geometry.Point(12, 5))


def test_model_quality_advises_a_new_export_with_the_settings_to_fix() -> None:
    good = reading.quality({"spaces": True, "north": True, "phases": True, "marks": True})
    assert (good["niveau"], good["réexport_conseillé"], good["conseils_export"]) == ("bonne", False, [])
    poor = reading.quality({"spaces": True, "north": False, "phases": False, "schema": False})
    assert poor["niveau"] == "à améliorer" and poor["réexport_conseillé"]
    assert any("nord" in advice for advice in poor["conseils_export"])
    assert reading.quality({"spaces": False})["niveau"] == "insuffisante"



@pytest.mark.parametrize("features, expected", [
    ({"ifc_class": "IfcColumn"}, "poteau"),
    ({"ifc_class": "IfcMember", "orientation": "vertical"}, "poteau d'ossature"),
    ({"ifc_class": "IfcMember", "orientation": "horizontal"}, "membrure horizontale"),
    ({"ifc_class": "IfcSlab", "predefined_type": "ROOF"}, "pan de toiture"),
    ({"ifc_class": "IfcSlab", "predefined_type": "FLOOR"}, "dalle"),
    ({"ifc_class": "IfcBuildingElementProxy", "type_name": "Garde-corps alu"}, "garde-corps"),
    ({"ifc_class": "IfcBuildingElementProxy", "type_name": "Arbre 3D"}, "objet générique"),
    ({"ifc_class": "IfcFurnishingElement"}, "mobilier"),
    ({"ifc_class": "IfcWall", "exterior": False, "thickness": 0.10}, "cloison"),
    ({"ifc_class": "IfcWallStandardCase", "exterior": False, "thickness": 0.30}, "mur intérieur"),
    ({"ifc_class": "IfcWall", "exterior": True, "thickness": 0.30}, "mur extérieur"),
])
def test_any_element_is_classified_by_the_category_profile(features, expected) -> None:
    rule = reading.classify(features, reading.load_rules())
    assert rule is not None and rule["label"] == expected


def test_a_missing_clue_fails_the_rule_that_asks_for_it() -> None:
    rules = [{"id": "porte_fenetre", "label": "porte-fenêtre", "match": {"classes": ["IfcWindow"], "exterior": True, "sill_max": 0.1}}]
    assert reading.classify({"ifc_class": "IfcWindow", "exterior": True, "sill": None}, rules) is None
    assert reading.classify({"ifc_class": "IfcWindow", "exterior": True, "sill": 0.0}, rules)["label"] == "porte-fenêtre"


def test_the_words_of_the_categories_present_are_published() -> None:
    words = reading.category_words(reading.load_rules(), {"poteau", "garde-corps"})
    assert "poteaux" in words["poteau"] and "garde corps" in words["garde-corps"]
    assert "mobilier" not in words


def test_quality_follows_the_discipline_and_asks_for_shared_coordinates() -> None:
    assert reading.discipline({"spaces": 0, "openings": 0, "structure": 700}) == "structure"
    assert reading.discipline({"spaces": 14, "openings": 22, "structure": 150}) == "architecture"
    structure = reading.quality({"spaces": False, "marks": False, "coordinates": False, "north": True}, "structure")
    assert structure["niveau"] == "à améliorer" and structure["contrôles"]["spaces"] is None
    assert "coordonnées partagées" in structure["conseils_export"][0]  # the most useful advice first
    assert reading.quality({"spaces": False}, "architecture")["niveau"] == "insuffisante"



def _house(dx=0.0, dy=0.0, turn=0.0):
    """A 20 x 10 m house: four exterior walls and one inner wall; posts every metre inside the walls."""
    from mvp_vertical import model_alignment as al
    corners = [(0, 0), (20, 0), (20, 10), (0, 10)]
    walls = [[*corners[i], *corners[(i + 1) % 4], 0.0] for i in range(4)] + [[12, 0, 12, 10, 0.0]]
    posts = [(x, 0.0) for x in range(0, 21, 2)] + [(x, 10.0) for x in range(0, 21, 2)] + [(12.0, y) for y in range(1, 10, 2)]
    moved = [(x + dx, y + dy) for x, y in al.rotate(posts, turn)]
    return walls, moved


def test_an_engineer_model_without_shared_coordinates_is_laid_on_the_architects() -> None:
    from mvp_vertical import model_alignment as al
    walls, posts = _house(dx=230.0, dy=-40.0, turn=0.0)
    architect = {"walls": {f"w{i}": w for i, w in enumerate(walls)}, "floors": {"R00": -22.9},
                 "spaces": {"s": [[0, 0], [20, 0], [20, 10], [0, 10], [0, 0]]}}
    engineer = {"walls": {}, "points": {f"p{i}": [x, y, -0.35, 2.5] for i, (x, y) in enumerate(posts)},
                "floors": {"Fondations": -1.5, "RDC structure": -0.35, "Portail": -0.8}}
    engineer["walls"] = {"e0": [230.0, -40.0, 250.0, -40.0, -0.35], "e1": [230.0, -30.0, 250.0, -30.0, -0.35]}
    result = al.align(architect, engineer)
    assert result["verdict"] == "probable" and result["score"] > 0.9
    assert abs(result["dx"] + 230.0) < 0.05 and abs(result["dy"] - 40.0) < 0.05
    assert result["dz"] == round(-22.9 + 0.35, 3)  # the ground floor, not the gate level
    assert result["status"] == "à confirmer"


def test_an_overlay_without_evidence_is_never_applied() -> None:
    from mvp_vertical import model_alignment as al
    walls, _ = _house()
    architect = {"walls": {f"w{i}": w for i, w in enumerate(walls)}, "floors": {"R00": 0.0}}
    scattered = {"walls": {}, "points": {f"p{i}": [i * 7.3 % 50, i * 3.1 % 40, 0.0, 1.0] for i in range(40)}, "floors": {"RDC": 0.0}}
    assert al.align(architect, scattered)["verdict"] == "incertain"
    assert al.align({"walls": {}}, scattered)["verdict"] == "impossible"


def test_a_model_is_checked_against_the_ids_when_ifctester_is_there(tmp_path, monkeypatch) -> None:
    pytest.importorskip("ifctester")
    import ifcopenshell
    import ifcopenshell.api

    model = ifcopenshell.file(schema="IFC4")
    project = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcProject", name="P")
    ifcopenshell.api.run("unit.assign_unit", model)
    space = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcSpace", name="001")
    door = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcDoor", name="Porte")
    door.Tag = "123456"  # an element id, not a drawing mark
    assert project and space
    result = reading.check_requirements(model)
    rows = {r["exigence"]: r for r in result["exigences"]}
    assert rows["Locaux nommés et numérotés"]["en_échec"] == 1  # no LongName
    assert rows["Portes : repère"]["en_échec"] == 1
    assert result["ids_agence"] is False and result["total"] == len(rows)
    # An agency's own IDS replaces the default.
    own = tmp_path / "agence.ids"
    own.write_text(reading.DEFAULT_IDS.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setenv(reading.IDS_ENV, str(own))
    assert reading.check_requirements(model)["ids_agence"] is True
