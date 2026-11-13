"""Fact proposals: a fact the user states about an affaire, set beside its reading, for the operator.

« Retiens que la cuisine donne au nord » is not stored by Hermes and not written into memory:
Hermes confronts the statement with what the Anatomy and the model readings say (`get_project`),
then prepares a proposal, checked here, and copies the returned block into its answer. The
Cockpit lists pending proposals; the operator validates or rejects each with a click. Until
then the reading stays the reference. Nothing is stored here.

The comparison is said in one word, so the operator sees at once whether the statement agrees
with the reading, differs from it (a reading error, a modelling choice or a project change: to
be told apart by the operator), or concerns something the readings do not show.
"""

from __future__ import annotations

import json
from typing import Any

from . import project_overview

KIND = "pantheon.fact_proposal"
VERSION = 1
FENCE = "pantheon-fact-proposal"
COMPARISONS = ("concorde", "diffère", "non lu")
COMPARISON_ALIASES = {"differe": "diffère", "diffère de la lecture": "diffère", "concordant": "concorde",
                      "conforme": "concorde", "non_lu": "non lu", "absent": "non lu", "inconnu": "non lu"}
LENGTHS = {"statement": 300, "subject": 120, "reading": 400, "source": 200}


def _text(value: Any, length: int) -> str:
    return " ".join(str(value or "").split())[:length]


def prepare_fact_proposal(code: Any, statement: Any, reading: Any, comparison: Any,
                          subject: Any = "", source: Any = "") -> dict[str, Any]:
    """Check a fact proposal and return it with the block to copy into the answer. Stores nothing."""
    code_text = _text(code, 40).upper()
    directory = project_overview.anatomy_dir()
    if not code_text:
        return {"status": "refused", "reason": "code d'affaire manquant"}
    if directory is not None:
        known = project_overview._available_codes(directory)
        if known and code_text not in known:
            return {"status": "refused", "reason": "affaire inconnue", "affaires": known}
    statement_text = _text(statement, LENGTHS["statement"])
    if not statement_text:
        return {"status": "refused", "reason": "énoncé manquant : le fait tel que l'utilisateur l'a dit"}
    reading_text = _text(reading, LENGTHS["reading"])
    if not reading_text:
        return {"status": "refused", "reason": "lecture manquante : ce que dit get_project sur ce point "
                                               "(« aucune lecture » si rien), à appeler avant de proposer"}
    word = _text(comparison, 40).casefold()
    word = COMPARISON_ALIASES.get(word, word)
    if word not in COMPARISONS:
        return {"status": "refused", "reason": "comparison : concorde, diffère ou non lu"}
    proposal = {"kind": KIND, "version": VERSION, "code": code_text,
                "subject": _text(subject, LENGTHS["subject"]) or None, "statement": statement_text,
                "reading": reading_text, "comparison": word,
                "source": _text(source, LENGTHS["source"]) or "énoncé par l'utilisateur",
                "confidence": "déclaré"}
    return {
        "status": "prepared",
        "proposal": proposal,
        "block": f"```{FENCE}\n{json.dumps(proposal, ensure_ascii=False, separators=(',', ':'))}\n```",
        "instruction": ("Recopie « block » tel quel à la fin de ta réponse, après avoir dit ce que montre la lecture "
                        "et si elle concorde. Rien n'est enregistré : le fait attend la validation de l'opérateur dans "
                        "le Cockpit ; d'ici là la lecture reste la référence. Ne dis jamais que c'est retenu."),
    }

