"""Read-only tests for the project overview tool.

Hermes reads the projection the implementation publishes for the Cockpit and
gets a compact summary whose numbers it can quote. The projection here is
synthetic, shaped like ``pantheon.anatomy.v1``; no project data is involved.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("PANTHEON_REPO_PATH", str(ROOT))

from pantheon_mcp import project_overview, server  # noqa: E402


def _ref(entity_id):
    return {"entity_type": "stable_object", "entity_id": entity_id}


def _area(subject, value):
    return {"attribute_key": "space.area", "subject_ref": _ref(subject),
            "value": {"value_type": "number", "value": value, "unit": "m2"}}


def _contains(level, space, state=None):
    qualifier = {"containment": "decomposition", **({"ouvrage_state": state} if state else {})}
    return {"relation_type": "spatial.contains", "subject_ref": _ref(level), "object_ref": _ref(space),
            "qualifier": qualifier}


def _object(object_id, name, code=None, family="spatial", areas=(), relations=()):
    return {"object_id": object_id, "object_family": family, "display_name": name, "internal_code": code,
            "attribute_claims": list(areas), "relations": list(relations)}


def _projection(code="DEMO"):
    objects = [
        _object("obj.rdc", "Rez-de-chaussée", "RDC", relations=[
            _contains("obj.rdc", "obj.cuisine", "projected"), _contains("obj.rdc", "obj.sejour", "to_keep")]),
        _object("obj.r01", "Étage", "R01", relations=[_contains("obj.r01", "obj.chambre")]),
        _object("obj.cuisine", "Cuisine", "1", areas=[_area("obj.cuisine", 12.456)],
                relations=[_contains("obj.rdc", "obj.cuisine", "projected")]),
        _object("obj.sejour", "Séjour", "2", areas=[_area("obj.sejour", 20.0)],
                relations=[_contains("obj.rdc", "obj.sejour", "to_keep")]),
        _object("obj.chambre", "Chambre", "3", areas=[_area("obj.chambre", 11.0)],
                relations=[_contains("obj.r01", "obj.chambre")]),
        _object("obj.terrain", "Terrain"),
    ]
    source = {"representation_id": "rep.1", "source_kind": "ifc", "source_artifact_ref": "ifc:demo",
              "context": {"document_ref": "ifc:demo.ifc", "native_context": {"index": "E", "issuer": "agence"}}}
    return {
        "schema": "pantheon.anatomy.v1",
        "generated_at": "2026-01-02T10:00:00+00:00",
        "project": {"project_id": "demo", "code": code, "display_name": "Maison démo"},
        "anatomy": {"owner_revision": 7, "structure": {"objects": objects}, "sources": [source, dict(source)],
                    "summary": {"attention_claim_count": 0, "unmapped_source_representation_count": 2}},
        "pieces": {
            "read_at": "2026-01-02T10:00:00+00:00",
            "pieces": [
                {"piece": "PLAN RDC", "category": "projet", "revisions": 2,
                 "current": {"index": "E", "date": "2026-01-01", "position": "certaine", "paths": ["DCE/x.pdf"]}},
                {"piece": "CCTP", "category": "projet", "variants": ["C1", "C2"],
                 "current": {"index": "C2", "date": None, "position": "certaine"}},
                {"piece": "DEVIS LOT 4", "category": "a_confronter", "current": {"index": None, "position": "incertaine"}},
            ],
            "questions": [{"piece": "CCTP", "kind": "variantes", "text": "CCTP : plusieurs variantes de l'indice C"}],
        },
    }


class TestProjectOverview(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp())
        (self.directory / "DEMO.json").write_text(json.dumps(_projection()), encoding="utf-8")

    def test_levels_spaces_states_and_totals_come_from_the_file(self):
        result = project_overview.summarize(json.loads((self.directory / "DEMO.json").read_text(encoding="utf-8")))
        self.assertTrue(result["found"])
        self.assertEqual(result["project"], {"code": "DEMO", "display_name": "Maison démo"})
        self.assertEqual(result["owner_revision"], 7)
        levels = {level["name"]: level["spaces"] for level in result["levels"]}
        self.assertEqual(levels["Rez-de-chaussée"][0],
                         {"name": "Cuisine", "code": "1", "area_m2": 12.46, "state": "projeté"})
        self.assertEqual(levels["Étage"][0]["state"], "état non renseigné")
        # Only spaces with both a surface and a state are summed, and the count says so.
        self.assertEqual(result["surfaces_by_state_m2"], {"projeté": 12.46, "existant conservé": 20.0})
        self.assertEqual(result["spaces_counted_in_totals"], 2)
        self.assertEqual(result["other_objects"], [{"name": "Terrain", "family": "spatial"}])
        self.assertEqual(result["sources"], [{"kind": "ifc", "document": "ifc:demo.ifc", "index": "E",
                                              "issuer": "agence", "occurrences": 2}])
        self.assertEqual(result["status"], "valeurs candidates, non validées")
        self.assertTrue(any("recalculer" in rule for rule in result["reading_rules"]))

    def test_the_current_index_of_each_piece_and_the_questions_come_first(self):
        result = project_overview.project_overview("DEMO", self.directory, focus="pièces")
        pieces = {"current": result["focus"]["pièces"],
                  "to_confront": project_overview.project_overview("DEMO", self.directory, focus="devis")["focus"]["devis"],
                  "questions": result["open_questions"]}
        self.assertEqual(pieces["current"][0], {"piece": "PLAN RDC", "index": "E", "date": "2026-01-01", "position": "certaine",
                                              "confiance": "lu", "file": "DEMO/DCE/x.pdf"})
        self.assertEqual(pieces["current"][1]["variants"], ["C1", "C2"])
        self.assertEqual(pieces["to_confront"], [{"piece": "DEVIS LOT 4", "position": "incertaine", "confiance": "estimé"}])
        self.assertEqual(pieces["questions"], ["CCTP : plusieurs variantes de l'indice C"])

    def test_questions_come_first_with_a_written_synthesis_and_the_project_nature(self):
        data = _projection()
        data["project"] = {**data["project"], "description": "Maison individuelle", "phase": "ACT"}
        data["pieces"]["pieces"][0]["current"]["date_source"] = "pdf"
        (self.directory / "DEMO.json").write_text(json.dumps(data), encoding="utf-8")
        result = project_overview.project_overview("DEMO", self.directory)
        self.assertEqual(list(result)[:4], ["code", "found", "source", "project"])
        self.assertEqual(result["project"]["description"], "Maison individuelle")
        self.assertEqual(result["open_questions"], ["CCTP : plusieurs variantes de l'indice C"])
        self.assertEqual(result["pieces"]["synthesis"], [
            "Indice C2 : 1 pièce (CCTP).", "Indice E : 1 pièce (PLAN RDC).",
            "1 devis ou offre à confronter.", "1 question ouverte."])
        listed = project_overview.project_overview("DEMO", self.directory, focus="pièces")["focus"]["pièces"]
        self.assertEqual(listed[0]["date_from"], "création du PDF (incertaine)")

    def test_an_anatomy_published_without_pieces_has_no_pieces_section(self):
        data = _projection()
        del data["pieces"]
        (self.directory / "BARE.json").write_text(json.dumps({**data, "project": {**data["project"], "code": "BARE"}}), encoding="utf-8")
        self.assertNotIn("pieces", project_overview.project_overview("BARE", self.directory))

    def test_a_long_list_of_unindexed_pieces_is_shortened_in_the_synthesis(self):
        lines = project_overview._synthesis([{"piece": f"PIECE {n:02d}"} for n in range(25)], [], [])
        self.assertEqual(lines[0], "Sans indice lisible (25) : " + ", ".join(f"PIECE {n:02d}" for n in range(10)) + " et 15 autres.")

    def test_an_affaire_without_an_installed_anatomy_still_gives_its_pieces(self):
        data = _projection()
        data["anatomy"] = {"status": "not_installed", "owner_revision": None, "summary": {}, "structure": {"objects": []},
                           "attribute_claims": [], "relation_claims": [], "relations": [], "sources": []}
        data["project"] = {**data["project"], "code": "NEUF"}
        (self.directory / "NEUF.json").write_text(json.dumps(data), encoding="utf-8")
        result = project_overview.project_overview("NEUF", self.directory)
        self.assertIn("non encore installée", result["anatomy_status"])
        self.assertNotIn("levels", result)
        self.assertEqual(result["pieces"]["counts"], {"current": 2, "to_confront": 1})

    def test_every_piece_and_model_answer_says_how_sure_it_is(self):
        data = _projection()
        data["pieces"]["pieces"][0]["current"]["index_source"] = "cartouche"
        data["pieces"]["pieces"][1]["current"]["index_source"] = "nom"
        data["pieces"]["pieces"][1]["current"]["reference"] = True
        (self.directory / "DEMO.json").write_text(json.dumps(data), encoding="utf-8")
        pieces = project_overview.project_overview("DEMO", self.directory, focus="pièces")["focus"]["pièces"]
        self.assertEqual([p["confiance"] for p in pieces], ["lu", "validé"])
        devis = project_overview.project_overview("DEMO", self.directory, focus="devis")["focus"]["devis"]
        self.assertEqual(devis[0]["confiance"], "estimé")
        self.assertTrue(any("validé (confirmé par un humain)" in r
                            for r in project_overview.project_overview("DEMO", self.directory)["reading_rules"]))

    def test_a_focus_answer_carries_only_a_header_and_the_piece_list_can_be_filtered(self):
        result = project_overview.project_overview("DEMO", self.directory, focus="pièces plan")
        self.assertNotIn("reading_rules", result)
        self.assertEqual([row["piece"] for row in result["focus"]["pièces"]], ["PLAN RDC"])

    def test_the_answer_without_focus_is_a_compact_summary(self):
        result = project_overview.project_overview("DEMO", self.directory)
        self.assertNotIn("current", result["pieces"])
        self.assertNotIn("sources", result)
        self.assertIn("focus", result["detail"])
        self.assertEqual(result["levels"][0]["spaces"][0], "Cuisine 12.46 m² (projeté)")
        self.assertLess(len(json.dumps(result, ensure_ascii=False)), 6000)

    def test_anatomy_sources_come_one_short_line_each_and_on_their_own_focus(self):
        data = _projection()
        data["anatomy_sources"] = {"mode": "déclarées", "en_attente": 1, "liste": [
            {"fichier": "DCE/archi.ifc", "état": "activée", "rôle": "référence", "lecture": {"indice": "C", "éléments": 400}},
            {"fichier": "DCE/bet.ifc", "état": "avertissement", "rôle": "complément", "messages": ["recalage estimé à confirmer"],
             "calage": {"verdict": "probable", "confirmé": False, "score": 0.84}},
            {"fichier": "DCE/bet-b.ifc", "état": "en attente", "rôle": "complément"}]}
        (self.directory / "DEMO.json").write_text(json.dumps(data), encoding="utf-8")
        summary = project_overview.project_overview("DEMO", self.directory)["anatomy_sources"]
        self.assertEqual(summary["en_attente"], 1)
        self.assertEqual(summary["liste"][0], {"fichier": "DCE/archi.ifc", "état": "activée", "rôle": "référence", "indice": "C"})
        self.assertEqual(summary["liste"][1]["calage"], "probable, non confirmé")
        sheet = project_overview.project_overview("DEMO", self.directory, focus="fichier archi")["focus"]
        self.assertEqual(sheet["fiche"]["lecture"]["éléments"], 400)
        self.assertIn("question", project_overview.project_overview("DEMO", self.directory, focus="fichier bet")["focus"])
        self.assertFalse(project_overview.project_overview("DEMO", self.directory, focus="fichier rien")["focus"]["found"])
        focused = project_overview.project_overview("DEMO", self.directory, focus="sources")
        self.assertEqual(len(focused["anatomy_sources"]["liste"]), 3)
        self.assertNotIn("reading_rules", focused)

    def test_changes_since_the_previous_index_come_in_the_summary_and_on_their_focus(self):
        data = _projection()
        data["model_changes"] = [{"pièce": "MAQUETTE", "de": "S", "à": "T", "fiable": True,
                                  "résumé": "locaux : 1 ajoutés", "fichier": "DEMO.changements-maquette-0123456789ab.json"}]
        (self.directory / "DEMO.json").write_text(json.dumps(data), encoding="utf-8")
        detail = {"de": {"index": "S"}, "à": {"index": "T"}, "fiable": True, "locaux": {"ajoutés": ["WC R01"]},
                  "murs": {"ajoutés": [f"mur {i}" for i in range(12)], "modifiés": [{"élément": "x"}] * 3}}
        (self.directory / "DEMO.changements-maquette-0123456789ab.json").write_text(json.dumps(detail), encoding="utf-8")
        summary = project_overview.project_overview("DEMO", self.directory)
        self.assertEqual(summary["model_changes"], [{"pièce": "MAQUETTE", "de": "S", "à": "T", "résumé": "locaux : 1 ajoutés"}])
        focus = project_overview.project_overview("DEMO", self.directory, focus="changements maquette")["focus"]
        comparison = focus["comparaisons"][0]
        self.assertEqual(comparison["locaux"]["ajoutés"], ["WC R01"])
        self.assertEqual(len(comparison["murs"]["ajoutés"]), 8)
        self.assertEqual(comparison["murs"]["modifiés"], 3)
        self.assertFalse(project_overview.project_overview("DEMO", self.directory, focus="changements cctp")["focus"]["found"])

    def test_usual_room_words_and_discipline_words_reach_the_right_answer(self):
        self.assertTrue(project_overview._room_match("salon", "Séjour"))
        self.assertTrue(project_overview._room_match("salle de bain", "SDB"))
        self.assertTrue(project_overview._room_match("local technique", "L.Tech"))
        self.assertFalse(project_overview._room_match("salon", "Chambre 1"))

    def test_multiword_room_synonyms_survive_element_designation_parsing(self):
        reading = _model_reading()
        reading["spaces"] = [
            {"id": "SDB", "name": "SDB", "number": "1", "level": "RDC"},
            {"id": "SAM", "name": "SAM", "number": "2", "level": "RDC"},
        ]
        reading["openings"] = [
            {"id": "P-SDB", "kind": "porte", "sides": ["SDB"]},
            {"id": "P-SAM", "kind": "porte", "sides": ["SAM"]},
        ]
        (self.directory / "DEMO.maquette-maquette.json").write_text(json.dumps(reading), encoding="utf-8")
        bath = project_overview.project_overview("DEMO", self.directory, focus="portes salle de bain")["focus"]
        dining = project_overview.project_overview("DEMO", self.directory, focus="portes salle à manger")["focus"]
        self.assertEqual((bath["kind"], bath["id"]), ("élément", "P-SDB"))
        self.assertEqual((dining["kind"], dining["id"]), ("élément", "P-SAM"))

    def test_an_empty_or_unknown_code_lists_the_published_affaires(self):
        self.assertEqual(project_overview.project_overview("", self.directory)["available_codes"], ["DEMO"])
        unknown = project_overview.project_overview("AUTRE", self.directory)
        self.assertEqual((unknown["found"], unknown["error"], unknown["available_codes"]), (False, "no_anatomy", ["DEMO"]))

    def test_paths_and_foreign_files_are_refused(self):
        self.assertEqual(project_overview.project_overview("../etc", self.directory)["error"], "invalid_code")
        (self.directory / "OTHER.json").write_text(json.dumps(_projection("DEMO")), encoding="utf-8")
        self.assertEqual(project_overview.project_overview("OTHER", self.directory)["error"], "anatomy_unreadable")
        (self.directory / "BAD.json").write_text("{", encoding="utf-8")
        self.assertEqual(project_overview.project_overview("BAD", self.directory)["error"], "anatomy_unreadable")

    def test_without_the_variable_nothing_is_read(self):
        with mock.patch.dict(os.environ, {"PANTHEON_ANATOMY_DIR": ""}):
            self.assertEqual(project_overview.project_overview("DEMO")["error"], "anatomy_not_configured")
        with mock.patch.dict(os.environ, {"PANTHEON_ANATOMY_DIR": "relative/dir"}):
            self.assertEqual(project_overview.project_overview("DEMO")["error"], "anatomy_not_configured")

    def test_the_tool_answers_without_any_effect(self):
        with mock.patch.dict(os.environ, {"PANTHEON_ANATOMY_DIR": str(self.directory)}):
            result = json.loads(server.get_project("DEMO"))
        self.assertEqual(result["operation"], "project.read")
        self.assertEqual(result["source_mode"], "published_projection")
        self.assertEqual(result["authority_effect"], "none")
        self.assertFalse(result["write_effect"])
        self.assertFalse(result["execution_effect"])
        self.assertTrue(result["found"])


def _model_reading():
    return {
        "schema": "pantheon.model_reading.v1",
        "source": {"piece": "MAQUETTE", "index": "E", "file": "DEMO_E.ifc"},
        "north": {"angle_deg": 0.0, "set_in_model": False},
        "spaces": [{"id": "G-CUI", "name": "Cuisine", "number": "1", "level": "RDC", "area_m2": 12.0},
                   {"id": "G-SAL", "name": "Salon", "number": "2", "level": "RDC", "area_m2": 20.0},
                   {"id": "G-CH1", "name": "chambre", "number": "100", "level": "R01", "area_m2": 12.1},
                   {"id": "G-CH2", "name": "chambre", "number": "101", "level": "R01", "area_m2": 12.6}],
        "openings": [{"id": "G-P1", "kind": "porte", "width_m": 0.8, "height_m": 2.07, "sides": ["G-CUI", "G-SAL"], "grid": "entre 6 et 55"},
                     {"id": "0FENETRE01", "kind": "fenêtre", "width_m": 1.61, "height_m": 1.87, "sides": ["G-CUI", None],
                      "exterior": True, "facade": "sud", "grid": "au-delà de la file 6"}],
        "walls": [{"id": "G-M1", "sides": ["G-SAL", "G-CUI"], "thickness_m": 0.1, "length_m": 2.65, "junctions": []}],
        "neighbours": [{"spaces": ["G-CUI", "G-SAL"], "via": "mur", "elements": ["G-M1"]},
                       {"spaces": ["G-CUI", "G-SAL"], "via": "porte", "elements": ["G-P1"]}],
        "limits": ["Côtés, façades et voisinages calculés par la géométrie : déductions, à confirmer."],
    }


class TestFocus(unittest.TestCase):
    """get_project(code, focus): the sheet of one room or element from the current model reading."""

    def setUp(self):
        self.directory = Path(tempfile.mkdtemp())
        data = _projection()
        data["models"] = [{"piece": "MAQUETTE", "index": "E", "file": "DEMO.maquette-maquette.json", "status": "read"}]
        # The Anatomy knows the kitchen as projected, through the IFC occurrence it represents.
        data["anatomy"]["sources"].append({"representation_id": "rep.ifc.G-CUI", "source_kind": "ifc",
                                           "identifiers": [{"scheme": "ifc.global_id", "value": "G-CUI"}],
                                           "identity_claims": [{"relation_type": "identity.represents",
                                                                "object_ref": {"entity_id": "obj.cuisine"}}]})
        data["anatomy"]["structure"]["objects"].append(
            _object("obj.rdc2", "RDC", relations=[_contains("obj.rdc2", "obj.cuisine", "projected")]))
        (self.directory / "DEMO.json").write_text(json.dumps(data), encoding="utf-8")
        (self.directory / "DEMO.maquette-maquette.json").write_text(json.dumps(_model_reading()), encoding="utf-8")

    def test_a_room_sheet_gives_doors_windows_walls_and_its_state(self):
        sheet = project_overview.project_overview("DEMO", self.directory, focus="cuisine")["focus"]
        self.assertEqual((sheet["name"], sheet["level"], sheet["état"]), ("Cuisine", "RDC", "projeté"))
        self.assertEqual(sheet["relié_par_porte_à"], ["Salon"])
        self.assertEqual(sheet["mur_commun_avec"], ["Salon"])
        self.assertEqual([o["donne"] for o in sheet["ouvertures"]], ["vers Salon", "extérieur, façade sud"])
        self.assertEqual(sheet["source"]["index"], "E")
        self.assertTrue(sheet["limites"])

    def test_same_names_are_told_apart_by_level_or_number_and_unknown_names_give_candidates(self):
        ambiguous = project_overview.project_overview("DEMO", self.directory, focus="chambre")["focus"]
        self.assertFalse(ambiguous["found"])
        self.assertEqual(len(ambiguous["candidates"]), 2)
        self.assertEqual(project_overview.project_overview("DEMO", self.directory, focus="chambre 101")["focus"]["surface_m2"], 12.6)
        unknown = project_overview.project_overview("DEMO", self.directory, focus="véranda")["focus"]
        self.assertFalse(unknown["found"])
        self.assertIn("Cuisine RDC", " ".join(unknown["candidates"]))

    def test_an_element_is_found_by_its_id_and_the_overview_lists_the_models(self):
        self.assertEqual(project_overview.project_overview("DEMO", self.directory)["models"],
                         [{"piece": "MAQUETTE", "index": "E", "status": "read"}])
        result = project_overview.project_overview("DEMO", self.directory, focus="0fenetre01")
        self.assertEqual((result["focus"]["kind"], result["focus"]["facade"]), ("élément", "sud"))
        self.assertEqual(result["focus"]["côtés"], ["Cuisine", "extérieur"])

    def test_reverse_questions_select_by_grid_line_facade_or_level(self):
        reading = _model_reading()
        reading["grid_lines"] = ["6", "55"]
        reading["levels"] = [{"name": "RDC", "elevation": 0.0}, {"name": "R01", "elevation": 2.8}]
        for item in reading["openings"] + reading["walls"]:
            item.setdefault("level", "RDC")
        (self.directory / "DEMO.maquette-maquette.json").write_text(json.dumps(reading), encoding="utf-8")
        on_line = project_overview.project_overview("DEMO", self.directory, focus="file 6")["focus"]
        self.assertEqual((on_line["kind"], on_line["nombre"]), ("sélection", 2))
        self.assertEqual({row["élément"] for row in on_line["éléments"]}, {"porte", "fenêtre"})
        south = project_overview.project_overview("DEMO", self.directory, focus="façade sud")["focus"]
        self.assertEqual([row["locaux"] for row in south["éléments"]], [["Cuisine"]])
        level = project_overview.project_overview("DEMO", self.directory, focus="R01")["focus"]
        self.assertEqual([s["local"] for s in level["locaux"]], ["chambre", "chambre"])
        missing = project_overview.project_overview("DEMO", self.directory, focus="file Z")["focus"]
        self.assertFalse(missing["found"])
        self.assertEqual(missing["candidates"], ["6", "55"])

    def test_an_ambiguous_designation_returns_the_question_to_ask(self):
        reading = _model_reading()
        reading["grid_lines"] = ["B", "C", "4", "5"]
        reading["walls"] = [
            {"id": "W1", "sides": ["G-CUI", "G-SAL"], "exterior": False, "grid": "sur la file 5 ; entre B et C", "level": "RDC"},
            {"id": "W2", "sides": ["G-SAL", "G-CUI"], "exterior": False, "grid": "sur la file C ; entre 4 et 5", "level": "RDC"},
            {"id": "W3", "sides": ["G-CUI", None], "exterior": True, "facade": "sud", "grid": "sur la file 5 ; entre C et D", "level": "RDC"},
        ]
        (self.directory / "DEMO.maquette-maquette.json").write_text(json.dumps(reading), encoding="utf-8")
        asked = project_overview.project_overview("DEMO", self.directory, focus="cloison file 5")["focus"]
        self.assertEqual(asked["plusieurs"], 2)
        self.assertEqual(asked["question"], "Parlez-vous de la cloison sur la file 5, entre B et C (Cuisine / Salon), "
                                            "ou de la cloison sur la file C, entre 4 et 5 (Salon / Cuisine) ?")
        # Same place and rooms: the question tells them apart by size.
        reading["walls"][1].update(grid="sur la file 5 ; entre B et C", sides=["G-CUI", "G-SAL"], length_m=2.35, thickness_m=0.1)
        reading["walls"][0].update(length_m=2.8)
        (self.directory / "DEMO.maquette-maquette.json").write_text(json.dumps(reading), encoding="utf-8")
        twins = project_overview.project_overview("DEMO", self.directory, focus="cloison file 5 entre b et c")["focus"]
        self.assertIn("(Cuisine / Salon, 2,80 m)", twins["question"])
        self.assertIn("(Cuisine / Salon, 2,35 m, ép. 0,10 m)", twins["question"])
        reading["walls"][1].update(grid="sur la file C ; entre 4 et 5", sides=["G-SAL", "G-CUI"])
        (self.directory / "DEMO.maquette-maquette.json").write_text(json.dumps(reading), encoding="utf-8")
        # "file C" alone is ambiguous too (on C, or between B and C); naming 4 and 5 settles it.
        self.assertEqual(project_overview.project_overview("DEMO", self.directory, focus="cloison file C")["focus"]["plusieurs"], 2)
        one = project_overview.project_overview("DEMO", self.directory, focus="cloison file C entre 4 et 5")["focus"]
        self.assertEqual((one["kind"], one["id"]), ("élément", "W2"))
        outside = project_overview.project_overview("DEMO", self.directory, focus="mur extérieur façade sud")["focus"]
        self.assertEqual(outside["id"], "W3")
        none = project_overview.project_overview("DEMO", self.directory, focus="porte file B")["focus"]
        self.assertFalse(none["found"])

    def test_what_hermes_actually_typed_is_understood(self):
        # Seen in a real session: lower-case code, "n°", and a plural element word.
        self.assertTrue(project_overview.project_overview("demo", self.directory)["found"])
        self.assertEqual(project_overview.project_overview("DEMO", self.directory, focus="chambre n° 101")["focus"]["surface_m2"], 12.6)
        windows = project_overview.project_overview("DEMO", self.directory, focus="chambre 1 fenêtres")["focus"]
        self.assertFalse(windows["found"])  # no "chambre 1" here, but no "which one?" question either
        self.assertNotIn("question", windows)
        reading = _model_reading()
        reading["openings"].append({"id": "0FENETRE02", "kind": "fenêtre", "width_m": 0.87, "height_m": 2.51,
                                    "sides": ["G-CUI", None], "exterior": True, "facade": "nord"})
        (self.directory / "DEMO.maquette-maquette.json").write_text(json.dumps(reading), encoding="utf-8")
        listed = project_overview.project_overview("DEMO", self.directory, focus="fenêtres cuisine")["focus"]
        self.assertEqual((listed["kind"], listed["nombre"]), ("sélection", 2))
        asked = project_overview.project_overview("DEMO", self.directory, focus="fenêtre cuisine")["focus"]
        self.assertIn("question", asked)

    def test_the_sheet_and_summary_say_what_openings_are_and_how_good_the_model_is(self):
        reading = _model_reading()
        reading["openings"][1].update(nature="porte-fenêtre", sill_m=0.0, kind="fenêtre")
        reading["openings"].append({"id": "0PORTEESC1", "kind": "porte", "nature": "porte intérieure", "width_m": 0.8,
                                    "height_m": 2.07, "sides": ["G-CUI", None], "exterior": False, "unmodelled_side": True,
                                    "clues": ["classe IFC IfcDoor", "la propriété IsExternal contredit la géométrie"]})
        reading["neighbours"].append({"spaces": ["G-CUI", "G-SAL"], "via": "ouvert", "elements": [], "longueur_m": 3.0})
        reading["quality"] = {"niveau": "à améliorer", "réexport_conseillé": True,
                              "conseils_export": ["Régler le nord géographique du projet dans Revit avant l'export."]}
        reading["declared_vs_observed"] = ["39 murs déclarés extérieurs, 14 le sont par la géométrie : la géométrie fait foi."]
        (self.directory / "DEMO.maquette-maquette.json").write_text(json.dumps(reading), encoding="utf-8")
        sheet = project_overview.project_overview("DEMO", self.directory, focus="cuisine")["focus"]
        rows = {o["id"]: o for o in sheet["ouvertures"]}
        self.assertEqual(rows["0FENETRE01"]["élément"], "porte-fenêtre")
        self.assertEqual(rows["0PORTEESC1"]["donne"], "vers un local non modélisé (circulation, escalier)")
        self.assertEqual(rows["0PORTEESC1"]["à_vérifier"], ["la propriété IsExternal contredit la géométrie"])
        self.assertEqual(sheet["ouvert_sur"], ["Salon"])
        self.assertEqual(sheet["qualité_maquette"], "à améliorer")
        # "porte" finds the French window modelled in a window family.
        doors = project_overview.project_overview("DEMO", self.directory, focus="portes cuisine")["focus"]
        self.assertIn("porte-fenêtre", {row["élément"] for row in doors["éléments"]})
        summary = project_overview.project_overview("DEMO", self.directory)
        self.assertTrue(summary["model_quality"]["réexport_conseillé"])
        self.assertEqual(summary["model_quality"]["à_corriger"], ["nord géographique"])
        self.assertNotIn("conseils_export", summary["model_quality"])
        detail = project_overview.project_overview("DEMO", self.directory, focus="qualité")["focus"]
        self.assertIn("nord", detail["maquettes"][0]["conseils_export"][0])
        self.assertTrue(any("réexporter" in rule for rule in summary["reading_rules"]))

    def test_any_category_is_designated_by_its_words(self):
        reading = _model_reading()
        reading["grid_lines"] = ["B", "C", "3", "4"]
        reading["levels"] = [{"name": "RDC", "elevation": 0.0}, {"name": "R01", "elevation": 2.8}]
        reading["categories"] = {"poteau": ["poteau", "poteaux", "pilier"], "garde-corps": ["garde-corps", "garde corps", "rambarde"]}
        reading["elements"] = [
            {"id": "P1", "label": "poteau", "space": "G-SAL", "grid": "sur la file C ; sur la file 3", "level": "RDC", "height_m": 2.6},
            {"id": "P2", "label": "poteau", "space": "G-SAL", "grid": "sur la file C ; sur la file 4", "level": "RDC", "height_m": 2.6},
            {"id": "GC1", "label": "garde-corps", "space": "G-CH1", "grid": "entre B et C", "level": "R01", "length_m": 3.2},
        ]
        (self.directory / "DEMO.maquette-maquette.json").write_text(json.dumps(reading), encoding="utf-8")
        columns = project_overview.project_overview("DEMO", self.directory, focus="poteaux file C")["focus"]
        self.assertEqual((columns["kind"], columns["nombre"]), ("sélection", 2))
        one = project_overview.project_overview("DEMO", self.directory, focus="poteau file C entre 3 et 4")["focus"]
        self.assertFalse(one["found"])  # on 3, on 4: neither is between them
        rail = project_overview.project_overview("DEMO", self.directory, focus="garde corps R01")["focus"]
        self.assertEqual((rail["kind"], rail["id"]), ("élément", "GC1"))
        sheet = project_overview.project_overview("DEMO", self.directory, focus="salon")["focus"]
        self.assertEqual(sheet["contient"], {"poteau": 2})
        summary = project_overview.project_overview("DEMO", self.directory)
        self.assertEqual(summary["model_elements"], {"MAQUETTE E": {"poteau": 2, "garde-corps": 1}})
        reading["elements"] += [{"id": f"P{n}", "label": "poteau", "space": "G-SAL", "level": "RDC"} for n in range(3, 40)]
        (self.directory / "DEMO.maquette-maquette.json").write_text(json.dumps(reading), encoding="utf-8")
        many = project_overview.project_overview("DEMO", self.directory, focus="poteaux")["focus"]
        self.assertEqual((many["nombre"], many["par_niveau"], len(many["extrait"])), (39, {"RDC": 39}, 8))
        asked = project_overview.project_overview("DEMO", self.directory, focus="poteau file C")["focus"]
        self.assertTrue(asked["question"].startswith("Plusieurs correspondent : poteau sur la file C"))

    def test_a_designated_element_shows_its_size_gap_and_each_model_its_quality(self):
        reading = _model_reading()
        reading["openings"][1].update(nature="porte-fenêtre", clues=["dimension déclarée height (OverallHeight) = 2,80 m, mesurée 2,18 m"])
        reading["quality"] = {"niveau": "à améliorer", "discipline": "architecture", "conseils_export": []}
        reading["categories"] = {"porte-fenêtre": ["porte-fenetre", "pf"]}
        (self.directory / "DEMO.maquette-maquette.json").write_text(json.dumps(reading), encoding="utf-8")
        structure = {"schema": "pantheon.model_reading.v1", "source": {"piece": "STRUCTURE", "index": "H"}, "spaces": [],
                     "openings": [], "walls": [], "elements": [], "neighbours": [],
                     "quality": {"niveau": "à améliorer", "discipline": "structure",
                                 "conseils_export": ["Exporter en coordonnées partagées (...)"]}}
        (self.directory / "DEMO.maquette-structure.json").write_text(json.dumps(structure), encoding="utf-8")
        data = json.loads((self.directory / "DEMO.json").read_text(encoding="utf-8"))
        data["models"].append({"piece": "STRUCTURE", "index": "H", "file": "DEMO.maquette-structure.json", "status": "read"})
        (self.directory / "DEMO.json").write_text(json.dumps(data), encoding="utf-8")
        found = project_overview.project_overview("DEMO", self.directory, focus="porte-fenêtre cuisine")["focus"]
        self.assertIn("mesurée 2,18 m", found["à_vérifier"][0])
        quality = project_overview.project_overview("DEMO", self.directory)["model_quality"]
        self.assertEqual(quality["autres_maquettes"][0]["discipline"], "structure")
        self.assertEqual(quality["autres_maquettes"][0]["à_corriger"], ["coordonnées partagées"])

    def test_engineer_elements_take_the_rooms_and_grid_of_the_overlay(self):
        structure = {"schema": "pantheon.model_reading.v1", "source": {"piece": "STRUCTURE", "index": "H"},
                     "discipline": "structure", "spaces": [], "openings": [], "walls": [], "neighbours": [], "levels": [],
                     "categories": {"poteau": ["poteau", "poteaux"]},
                     "alignment": {"verdict": "probable", "score": 0.85, "reference": "MAQUETTE", "reference_index": "E", "status": "à confirmer"},
                     "elements": [{"id": "C1", "label": "poteau", "via_recalage": {"niveau_archi": "RDC", "locaux_voisins": ["Salon", "Cuisine"], "files": "sur la file C ; entre 3 et 4"}},
                                  {"id": "C2", "label": "poteau", "via_recalage": {"niveau_archi": "RDC", "local": "Salon", "files": "entre B et C ; entre 3 et 4"}}]}
        (self.directory / "DEMO.maquette-structure.json").write_text(json.dumps(structure), encoding="utf-8")
        data = json.loads((self.directory / "DEMO.json").read_text(encoding="utf-8"))
        data["models"].append({"piece": "STRUCTURE", "index": "H", "file": "DEMO.maquette-structure.json", "status": "read"})
        (self.directory / "DEMO.json").write_text(json.dumps(data), encoding="utf-8")
        reading = _model_reading()
        reading["grid_lines"] = ["B", "C", "3", "4"]
        (self.directory / "DEMO.maquette-maquette.json").write_text(json.dumps(reading), encoding="utf-8")
        on_c = project_overview.project_overview("DEMO", self.directory, focus="poteaux file C")["focus"]
        self.assertEqual(on_c["recalage"]["verdict"], "probable")
        rows = on_c.get("éléments") or [on_c]
        self.assertTrue(all(row.get("confiance") == "estimé" for row in rows))
        in_salon = project_overview.project_overview("DEMO", self.directory, focus="poteaux salon")["focus"]
        self.assertEqual(in_salon["nombre"], 2)
        self.assertIn("déduit", in_salon["légende_confiance"]["dimensions, nature, côtés, façade, files, locaux"])
        # One element answered alone keeps its own confidence beside the legend.
        structure["elements"] = structure["elements"][:1]
        (self.directory / "DEMO.maquette-structure.json").write_text(json.dumps(structure), encoding="utf-8")
        alone = project_overview.project_overview("DEMO", self.directory, focus="poteau salon")["focus"]
        self.assertEqual(alone["kind"], "élément")
        self.assertEqual(alone["confiance"], "estimé")
        self.assertIn("légende_confiance", alone)

    def test_without_a_model_reading_the_focus_says_so(self):
        (self.directory / "DEMO.maquette-maquette.json").unlink()
        self.assertFalse(project_overview.project_overview("DEMO", self.directory, focus="cuisine")["focus"]["found"])

    def test_unavailable_discipline_does_not_fall_back_to_another_model(self):
        reading = _model_reading()
        reading["discipline"] = "architecture"
        with mock.patch.object(project_overview, "_load_models", return_value=[reading]):
            answer = project_overview._focus(self.directory, _projection(), "poteaux du BET séjour")
        self.assertFalse(answer["found"])
        self.assertEqual(answer["discipline_demandée"], "structure")
        self.assertEqual(answer["disciplines_disponibles"], ["architecture"])

    def test_an_unknown_room_gives_the_rooms_and_advice_instead_of_a_dead_end(self):
        missed = project_overview.project_overview("DEMO", self.directory, focus="portes grenier")["focus"]
        self.assertFalse(missed["found"])
        self.assertIn("poteaux", missed["conseil"])
        self.assertIn("Cuisine", missed["locaux"])


class TestProjectStateRouting(unittest.TestCase):
    """Hermes reaches get_project through the words its project-context Skill uses."""

    def test_the_tool_and_the_skill_name_the_same_live_project_state_source(self):
        phrase = "live project-state source"
        skill = " ".join((ROOT / "templates/hermes/skills/project-context/SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn(phrase, skill)
        self.assertIn("Never infer an index", skill)
        self.assertIn(phrase.capitalize(), " ".join(server.get_project.__doc__.split()))
        self.assertIn("get_project is the live project-state", server.mcp.instructions)


if __name__ == "__main__":
    unittest.main()
