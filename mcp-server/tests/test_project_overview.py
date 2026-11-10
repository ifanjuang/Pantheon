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
        result = project_overview.project_overview("DEMO", self.directory)
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
        pieces = project_overview.project_overview("DEMO", self.directory)["pieces"]
        self.assertEqual(pieces["current"][0], {"piece": "PLAN RDC", "index": "E", "date": "2026-01-01", "position": "certaine",
                                              "file": "DEMO/DCE/x.pdf"})
        self.assertEqual(pieces["current"][1]["variants"], ["C1", "C2"])
        self.assertEqual(pieces["to_confront"], [{"piece": "DEVIS LOT 4", "position": "incertaine"}])
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
        self.assertEqual(result["pieces"]["current"][0]["date_from"], "création du PDF (incertaine)")

    def test_an_anatomy_published_without_pieces_has_no_pieces_section(self):
        data = _projection()
        del data["pieces"]
        (self.directory / "BARE.json").write_text(json.dumps({**data, "project": {**data["project"], "code": "BARE"}}), encoding="utf-8")
        self.assertNotIn("pieces", project_overview.project_overview("BARE", self.directory))

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
