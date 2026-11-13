import json
import unittest

from pantheon_mcp import server
from pantheon_mcp.card_proposal import FENCE, KIND, prepare_card_proposal


class CardProposalTest(unittest.TestCase):
    def test_prepares_checked_block_without_storing(self):
        result = prepare_card_proposal("agence", "Affaires/A01/plan.pdf", [
            {"field": "date", "value": "12/03/2026", "source": "cartouche, page 1"},
            {"field": "indice", "value": "Indice C", "source": "cartouche", "confidence": "lu"},
            {"field": "title", "value": "  Plan   du rez-de-chaussée ", "source": "cartouche",
             "confidence": "deduit", "reason": "titre plus précis"},
            {"field": "corps_etat", "value": "Structure, CVC, Structure", "source": "légende"},
        ])
        self.assertEqual(result["status"], "prepared")
        changes = {c["field"]: c for c in result["proposal"]["changes"]}
        self.assertEqual(changes["document_date"]["value"], "2026-03-12")
        self.assertEqual(changes["index"]["value"], "C")
        self.assertEqual(changes["title"]["value"], "Plan du rez-de-chaussée")
        self.assertEqual(changes["title"]["confidence"], "déduit")
        self.assertEqual(changes["corps_etat"]["value"], ["Structure", "CVC"])
        self.assertTrue(result["block"].startswith(f"```{FENCE}\n"))
        block = json.loads(result["block"].split("\n")[1])
        self.assertEqual(block, result["proposal"])
        self.assertEqual(block["kind"], KIND)

    def test_rejects_without_source_unknown_field_validated_and_bad_date(self):
        result = prepare_card_proposal("agence", "a/b.pdf", [
            {"field": "index", "value": "B"},
            {"field": "surface_cuisine", "value": "12", "source": "maquette"},
            {"field": "issuer", "value": "BET", "source": "mail", "confidence": "validé"},
            {"field": "document_date", "value": "31/02/2026", "source": "cartouche"},
        ])
        self.assertEqual(result["status"], "refused")
        self.assertEqual(len(result["rejected"]), 4)
        self.assertNotIn("block", result)

    def test_refuses_path_escape_and_keeps_one_value_per_field(self):
        self.assertEqual(prepare_card_proposal("agence", "../x.pdf", [])["status"], "refused")
        self.assertEqual(prepare_card_proposal("agence", "/x.pdf", [])["status"], "refused")
        result = prepare_card_proposal("agence", "x.pdf", [
            {"field": "index", "value": "B", "source": "cartouche"},
            {"field": "indice", "value": "C", "source": "nom du fichier"},
        ])
        self.assertEqual([c["value"] for c in result["proposal"]["changes"]], ["B"])
        self.assertEqual(result["rejected"][0]["raison"], "champ déjà proposé")

    def test_anatomy_source_only_as_the_users_choice(self):
        choice = {"field": "source anatomique", "source": "choix de l'utilisateur dans la discussion",
                  "confidence": "déclaré",
                  "value": {"active": True, "mode": "remplacement", "replaces": "A01/BIM/structure A.ifc",
                            "role": "référence", "discipline": "structure"}}
        result = prepare_card_proposal("Affaires", "A01/BIM/structure H.ifc", [choice])
        self.assertEqual(result["status"], "prepared")
        self.assertEqual(result["proposal"]["changes"][0]["field"], "anatomy_source")
        self.assertEqual(result["proposal"]["changes"][0]["value"]["mode"], "remplacement")
        for bad in ({**choice, "confidence": "lu"},
                    {**choice, "value": {"active": True, "mode": "remplacement"}},
                    {**choice, "value": {"active": True, "set_by": "hermes"}},
                    {**choice, "value": {"active": True, "mode": "remplacement", "replaces": "[maquette X]"}},
                    {**choice, "value": {"active": "oui"}}):
            self.assertEqual(prepare_card_proposal("Affaires", "A01/h.ifc", [bad])["status"], "refused", bad)

    def test_tool_is_read_only_projection(self):
        result = json.loads(server.prepare_card_proposal(
            "agence", "x.pdf", [{"field": "index", "value": "B", "source": "cartouche"}]))
        self.assertEqual(result["operation"], "card.proposal.prepare")
        self.assertFalse(result["write_effect"])
        self.assertEqual(result["authorization_effect"], "none")


if __name__ == "__main__":
    unittest.main()
