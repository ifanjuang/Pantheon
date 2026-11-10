"""Reading of the current model: sides, façades, grid lines, neighbours, and its cache.

The geometry helpers are tested on synthetic shapes; no project model is involved.
"""

from __future__ import annotations

import json
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
    assert seen == [("DEMO_E.ifc", "DEMO.maquette-maquette.json", {"piece": "MAQUETTE", "index": "E"})]
