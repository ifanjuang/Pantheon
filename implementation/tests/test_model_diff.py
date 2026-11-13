"""What changed between two indices of a model, compared element by element on their readings.

Synthetic readings only; no real project data.
"""

from __future__ import annotations

import json
from pathlib import Path

from mvp_vertical import anatomy_export, model_diff, model_reading, project_pieces


def _reading(index: str, *, rooms=None, openings=None, walls=None, elements=None, discipline="architecture") -> dict:
    return {"source": {"piece": "MAQUETTE", "index": index, "fingerprint": f"f-{index}"}, "discipline": discipline,
            "spaces": rooms or [], "openings": openings or [], "walls": walls or [], "elements": elements or []}


OLD = _reading("S", rooms=[{"id": "r1", "name": "Séjour / Cuisine", "level": "R00", "area_m2": 48.82},
                           {"id": "r2", "name": "Chambre", "level": "R00", "area_m2": 12.0}],
               openings=[{"id": "o1", "nature": "fenêtre", "width_m": 1.20, "height_m": 1.35, "facade": "sud", "sides": ["r1", None]}],
               walls=[{"id": "w1", "thickness_m": 0.20, "length_m": 4.0, "sides": ["r1", "r2"]},
                      {"id": "w2", "thickness_m": 0.10, "length_m": 2.0, "sides": ["r2"]}],
               elements=[{"id": "e1", "label": "poteau", "level": "R00"}])
NEW = _reading("T", rooms=[{"id": "r1", "name": "Séjour", "level": "R00", "area_m2": 51.17},
                           {"id": "r2", "name": "Chambre", "level": "R00", "area_m2": 12.05},
                           {"id": "r3", "name": "WC", "level": "R01", "area_m2": 1.5}],
               openings=[{"id": "o1", "nature": "fenêtre", "width_m": 1.40, "height_m": 1.35, "facade": "sud", "sides": ["r1", None]}],
               walls=[{"id": "w1", "thickness_m": 0.20, "length_m": 4.0, "sides": ["r1", "r2"]},
                      {"id": "w3", "thickness_m": 0.07, "length_m": 1.0, "sides": ["r3"]},
                      {"id": "w4", "thickness_m": 0.07, "length_m": 1.0, "sides": ["r3"]}],
               elements=[{"id": "e1", "label": "poteau", "level": "R00"}])


def test_changes_are_read_element_by_element_in_the_words_of_the_readings() -> None:
    diff = model_diff.compare(OLD, NEW)
    assert diff["fiable"] and diff["de"]["index"] == "S" and diff["à"]["index"] == "T"
    assert diff["locaux"]["ajoutés"] == ["WC R01"]
    changed = {row["élément"]: row["changements"] for row in diff["locaux"]["modifiés"]}
    assert changed == {"Séjour R00": {"nom": ["Séjour / Cuisine", "Séjour"], "surface_m2": [48.82, 51.17]}}  # 0.05 m² is noise
    assert diff["ouvertures"]["modifiés"][0]["changements"] == {"largeur_m": [1.2, 1.4]}
    assert diff["ouvertures"]["modifiés"][0]["élément"] == "fenêtre, façade sud, Séjour"
    assert diff["murs"]["ajoutés"] == ["mur, WC (×2)"] and diff["murs"]["supprimés"] == ["mur, Chambre"]
    assert "éléments" not in diff
    assert diff["résumé"].startswith("locaux : 2 changés (1 ajoutés, 1 modifiés)")
    assert "modélisation" in diff["limite"]


def test_a_comparison_without_shared_identifiers_says_it_is_not_meaningful() -> None:
    other = _reading("X", rooms=[{"id": "z1", "name": "Séjour", "level": "R00", "area_m2": 50}])
    diff = model_diff.compare(OLD, other)
    assert diff["fiable"] is False and "identifiants" in diff["raison"] and "locaux" not in diff


def test_one_model_under_two_names_becomes_a_question() -> None:
    bet_a = _reading("A", elements=[{"id": f"c{i}"} for i in range(10)], discipline="structure")
    bet_h = _reading("H", elements=[{"id": f"c{i}"} for i in range(1, 12)], discipline="structure")
    questions = model_diff.same_model_questions([bet_a, bet_h, OLD], {"MAQUETTE": None})
    assert len(questions) == 1 and questions[0]["kind"] == "meme_maquette" and "laquelle fait foi" in questions[0]["text"]
    assert "identifiants IFC communs" in questions[0]["text"]
    assert questions[0]["text"].startswith("Maquettes structure : ")  # never read as the architect's model
    bet_h["source"] = {**bet_h["source"], "piece": "BET H"}
    dated = model_diff.same_model_questions([bet_a, bet_h], {"MAQUETTE": "2026-06-16", "BET H": "2026-10-28"})
    assert "MAQUETTE A (2026-06-16) et BET H H (2026-10-28)" in dated[0]["text"]
    assert "la plus récente est BET H H" in dated[0]["text"]
    with_files = model_diff.same_model_questions([bet_a, bet_h], {}, {"MAQUETTE": ["BIM/a.ifc"], "BET H": ["PRO/h.ifc"]})
    assert with_files[0]["files"] == ["BIM/a.ifc", "PRO/h.ifc"]
    assert with_files[0]["action"]["code"] == "activer_source_remplacement"


def test_each_piece_keeps_its_previous_index_in_the_same_format() -> None:
    files = [{"path": "PRO/PLAN_B.pdf", "title": "PLAN_B.pdf", "fingerprint": "1"},
             {"path": "DCE/PLAN_C.pdf", "title": "PLAN_C.pdf", "fingerprint": "2"},
             {"path": "DCE/PLAN_C.ifc", "title": "PLAN_C.ifc", "fingerprint": "3"},
             {"path": "PRO/PLAN_B.ifc", "title": "PLAN_B.ifc", "fingerprint": "4"}]
    piece = project_pieces.current_state(files, "DEMO")["pieces"][0]
    assert piece["previous"]["index"] == "B" and piece["previous"]["paths"][0].endswith(piece["current"]["paths"][0][-4:])


def test_the_publication_compares_each_model_with_its_previous_index_once(tmp_path, monkeypatch) -> None:
    readings = {"old.ifc": OLD, "new.ifc": NEW}
    reads = []

    def fake_ensure(path, out_file, *, piece, index=None):
        if not out_file.exists():
            reads.append(path.name)
            out_file.write_text(json.dumps(readings[path.name]), encoding="utf-8")
        return {"piece": piece, "index": index, "file": out_file.name, "status": "read"}

    monkeypatch.setattr(model_reading, "ensure", fake_ensure)
    (tmp_path / "DEMO.maquette-new.json").write_text(json.dumps(NEW), encoding="utf-8")
    models = [{"piece": "MAQUETTE", "index": "T", "file": "DEMO.maquette-new.json"}]
    previous = {"MAQUETTE": (tmp_path / "old.ifc", tmp_path / "DEMO.maquette-old.json", "S")}
    (tmp_path / "DEMO.changements-stale-000000000000.json").write_text("{}", encoding="utf-8")

    changes, questions = anatomy_export.compare_models("DEMO", models, previous, tmp_path)
    assert changes[0]["de"] == "S" and changes[0]["à"] == "T" and changes[0]["fiable"]
    assert (tmp_path / changes[0]["fichier"]).exists() and not (tmp_path / "DEMO.changements-stale-000000000000.json").exists()
    assert questions == []
    again, _ = anatomy_export.compare_models("DEMO", models, previous, tmp_path)
    assert again == changes and reads == ["old.ifc"]  # the previous index is read once


def test_same_model_question_uses_the_paths_of_declared_noncurrent_sources(tmp_path) -> None:
    bet_a = _reading("A", elements=[{"id": f"c{i}"} for i in range(10)], discipline="structure")
    bet_h = _reading("H", elements=[{"id": f"c{i}"} for i in range(1, 12)], discipline="structure")
    bet_a["source"]["piece"] = "BET A"
    bet_h["source"]["piece"] = "BET H"
    (tmp_path / "BET-A.json").write_text(json.dumps(bet_a), encoding="utf-8")
    (tmp_path / "BET-H.json").write_text(json.dumps(bet_h), encoding="utf-8")
    models = [
        {"piece": "BET A", "file": "BET-A.json", "_workspace_path": "PRO/structure-a.ifc"},
        {"piece": "BET H", "file": "BET-H.json", "_workspace_path": "DCE/structure-h.ifc"},
    ]

    changes, questions = anatomy_export.compare_models("DEMO", models, {}, tmp_path)

    assert changes == []
    assert set(questions[0]["files"]) == {"PRO/structure-a.ifc", "DCE/structure-h.ifc"}


def test_a_wall_changing_category_is_a_change() -> None:
    old = _reading("S", walls=[{"id": "w1", "label": "cloison", "thickness_m": 0.10, "length_m": 3.0}])
    new = _reading("T", walls=[{"id": "w1", "label": "mur porteur", "thickness_m": 0.10, "length_m": 3.0}])
    assert model_diff.compare(old, new)["murs"]["modifiés"][0]["changements"] == {"catégorie": ["cloison", "mur porteur"]}


def test_variants_of_the_current_index_are_not_its_previous_index() -> None:
    files = [{"path": "PRO/PLAN_B.ifc", "title": "PLAN_B.ifc", "fingerprint": "1"},
             {"path": "DCE/PLAN_C1.ifc", "title": "PLAN_C1.ifc", "fingerprint": "2"},
             {"path": "DCE/PLAN_C2.ifc", "title": "PLAN_C2.ifc", "fingerprint": "3"}]
    piece = project_pieces.current_state(files, "DEMO")["pieces"][0]
    assert piece["current"]["index"] == "C2" and piece["previous"]["index"] == "B"


def test_without_a_read_date_the_file_date_is_given_and_said() -> None:
    a = _reading("A", elements=[{"id": f"c{i}"} for i in range(10)], discipline="structure")
    b = _reading("H", elements=[{"id": f"c{i}"} for i in range(10)], discipline="structure")
    a["source"] = {"piece": "BET A", "index": "A", "fingerprint": "size:1:mtime:1781000000"}
    b["source"] = {"piece": "BET H", "index": "H", "fingerprint": "size:1:mtime:1793000000"}
    text = model_diff.same_model_questions([a, b])[0]["text"]
    assert "date du fichier" in text and "la plus récente est BET H H" in text
