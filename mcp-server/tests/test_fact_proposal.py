import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pantheon_mcp import server
from pantheon_mcp.card_proposal import prepare_card_proposal
from pantheon_mcp.fact_proposal import FENCE, KIND, prepare_fact_proposal


class FactProposalTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        Path(self.directory.name, "A01.json").write_text("{}", encoding="utf-8")
        patcher = mock.patch.dict(os.environ, {"PANTHEON_ANATOMY_DIR": self.directory.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.directory.cleanup)

    def test_prepares_block_beside_the_reading(self):
        result = prepare_fact_proposal("a01", "la cuisine donne au nord", "cuisine : fenêtre façade nord",
                                       "Concorde", subject="cuisine")
        self.assertEqual(result["status"], "prepared")
        proposal = result["proposal"]
        self.assertEqual((proposal["code"], proposal["comparison"], proposal["confidence"]), ("A01", "concorde", "déclaré"))
        self.assertEqual(proposal["source"], "énoncé par l'utilisateur")
        self.assertTrue(result["block"].startswith(f"```{FENCE}\n"))
        self.assertEqual(json.loads(result["block"].split("\n")[1])["kind"], KIND)

    def test_refuses_unknown_affaire_missing_reading_and_bad_comparison(self):
        self.assertEqual(prepare_fact_proposal("B02", "x", "y", "concorde")["reason"], "affaire inconnue")
        self.assertIn("lecture manquante", prepare_fact_proposal("A01", "x", "", "concorde")["reason"])
        self.assertEqual(prepare_fact_proposal("A01", "x", "y", "peut-être")["status"], "refused")
        self.assertEqual(prepare_fact_proposal("A01", "x", "aucune lecture", "differe")["proposal"]["comparison"], "diffère")

    def test_tool_is_read_only_projection(self):
        result = json.loads(server.prepare_fact_proposal("A01", "x", "aucune lecture", "non lu"))
        self.assertEqual(result["operation"], "fact.proposal.prepare")
        self.assertFalse(result["write_effect"])


class CardProposalSourceTest(unittest.TestCase):
    def test_user_reading_is_a_source_but_no_reading_is_not(self):
        ok = prepare_card_proposal("v", "a.pdf", [{"field": "index", "value": "C", "source": "cartouche, lu par l'utilisateur"}])
        self.assertEqual(ok["status"], "prepared")
        for source in ("absence de source consultée", "aucune source", "non confirmé"):
            refused = prepare_card_proposal("v", "a.pdf", [{"field": "index", "value": "C", "source": source}])
            self.assertEqual(refused["status"], "refused", source)


if __name__ == "__main__":
    unittest.main()
