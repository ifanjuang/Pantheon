"""Card metadata proposals: what a discussion found for a document card, for the operator to accept.

During a discussion Hermes may read a date, an index, an issuer or a better title that the
card lacks or gets wrong. It does not write the card: it prepares a proposal, checked here,
and copies the returned block into its answer. The Cockpit shows the block as a checklist
next to the card (current value, proposed value, source, confidence); the operator ticks
the lines to keep and accepts, which saves them as card corrections. Nothing is stored here.

The fields are those a card correction accepts. A proposal never carries « validé »: only
the operator's acceptance validates. Facts about the building go to the Anatomy, not here.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import PurePosixPath
from typing import Any

KIND = "pantheon.card_proposal"
VERSION = 1
FENCE = "pantheon-card-proposal"
MAX_CHANGES = 10
SOURCE_LENGTH = 300
REASON_LENGTH = 300

# Same fields and lengths as a card correction saved from the Cockpit.
TEXT_FIELDS = {
    "title": 300, "document_date": 80, "index": 80, "issuer": 250, "recipient": 250,
    "family": 100, "document_type": 120, "summary": 1200,
}
LIST_FIELDS = {"corps_etat", "sujet_technique"}
LIST_ITEMS, LIST_ITEM_LENGTH = 20, 100
FIELD_ALIASES = {
    "titre": "title", "date": "document_date", "indice": "index", "émetteur": "issuer", "emetteur": "issuer",
    "auteur": "issuer", "destinataire": "recipient", "famille": "family", "type": "document_type",
    "type_document": "document_type", "corps_d_etat": "corps_etat", "lot": "corps_etat",
    "sujet": "sujet_technique", "résumé": "summary", "resume": "summary", "descriptif": "summary",
    "description": "summary",
}
CONFIDENCES = ("lu", "déduit", "estimé")
CONFIDENCE_ALIASES = {"deduit": "déduit", "estime": "estimé"}

_DATE_ISO = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")
_DATE_FR = re.compile(r"^(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{2}|\d{4})$")
_INDEX_PREFIX = re.compile(r"^(?:indice|ind\.?|index|rev\.?|révision)\s*[:\-]?\s*", re.IGNORECASE)


def _date(value: str) -> str | None:
    """An ISO date from « 2026-03-12 », « 12/03/2026 », « 12.03.26 »; None if not a real date."""
    found = _DATE_ISO.match(value)
    if found:
        y, m, d = (int(x) for x in found.groups())
    else:
        found = _DATE_FR.match(value)
        if not found:
            return None
        d, m, y = (int(x) for x in found.groups())
        if y < 100:
            y += 2000
    try:
        return date(y, m, d).isoformat()
    except ValueError:
        return None


def _path_error(vault: Any, relative_path: Any) -> str | None:
    if not isinstance(vault, str) or not vault.strip():
        return "vault manquant : celui du périmètre de la discussion"
    if (not isinstance(relative_path, str) or not relative_path.strip() or relative_path.startswith("/")
            or "\\" in relative_path or ".." in PurePosixPath(relative_path).parts):
        return "relative_path invalide : le chemin relatif du périmètre de la discussion"
    return None


def _value(field: str, raw: Any) -> tuple[Any, str | None]:
    if field in LIST_FIELDS:
        items = raw.split(",") if isinstance(raw, str) else raw
        if not isinstance(items, list) or any(not isinstance(i, str) for i in items):
            return None, "liste de textes attendue"
        cleaned = list(dict.fromkeys(i.strip() for i in items if i.strip()))
        if not cleaned:
            return None, "valeur vide"
        if len(cleaned) > LIST_ITEMS or any(len(i) > LIST_ITEM_LENGTH for i in cleaned):
            return None, "liste trop longue"
        return cleaned, None
    if not isinstance(raw, str) or not raw.strip():
        return None, "valeur vide"
    value = " ".join(raw.split())
    if field == "document_date":
        iso = _date(value)
        return (iso, None) if iso else (None, "date non reconnue (attendu 2026-03-12 ou 12/03/2026)")
    if field == "index":
        value = _INDEX_PREFIX.sub("", value).strip()
        if not value or len(value) > 20:
            return None, "indice non reconnu"
    if len(value) > TEXT_FIELDS[field]:
        return None, "valeur trop longue"
    return value, None


def prepare_card_proposal(vault: Any, relative_path: Any, changes: Any) -> dict[str, Any]:
    """Check a proposal and return it with the block to copy into the answer. Stores nothing."""
    error = _path_error(vault, relative_path)
    if error:
        return {"status": "refused", "reason": error}
    if isinstance(changes, dict):
        changes = [changes]
    if not isinstance(changes, list) or not changes:
        return {"status": "refused", "reason": "changes : une liste de {field, value, source} attendue"}
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in changes[:MAX_CHANGES]:
        if not isinstance(item, dict):
            rejected.append({"field": None, "raison": "objet {field, value, source} attendu"})
            continue
        name = str(item.get("field") or "").strip().casefold().replace(" ", "_").replace("'", "_")
        field = FIELD_ALIASES.get(name, name)
        if field not in TEXT_FIELDS and field not in LIST_FIELDS:
            rejected.append({"field": item.get("field"), "raison": "champ non modifiable sur une fiche "
                             "(un fait sur le bâtiment va à l'Anatomie)"})
            continue
        if field in seen:
            rejected.append({"field": field, "raison": "champ déjà proposé"})
            continue
        value, problem = _value(field, item.get("value"))
        source = " ".join(str(item.get("source") or "").split())
        if not problem and not source:
            problem = "source manquante : où la valeur a été trouvée (page, cartouche, courriel…)"
        confidence = str(item.get("confidence") or "lu").strip().casefold()
        confidence = CONFIDENCE_ALIASES.get(confidence, confidence)
        if not problem and confidence not in CONFIDENCES:
            problem = "confiance : lu, déduit ou estimé (seul l'opérateur valide)"
        if problem:
            rejected.append({"field": field, "raison": problem})
            continue
        seen.add(field)
        change = {"field": field, "value": value, "source": source[:SOURCE_LENGTH], "confidence": confidence}
        reason = " ".join(str(item.get("reason") or "").split())
        if reason:
            change["reason"] = reason[:REASON_LENGTH]
        accepted.append(change)
    for item in changes[MAX_CHANGES:]:
        rejected.append({"field": item.get("field") if isinstance(item, dict) else None,
                         "raison": f"au plus {MAX_CHANGES} champs par proposition"})
    result: dict[str, Any] = {"status": "prepared" if accepted else "refused"}
    if rejected:
        result["rejected"] = rejected
    if not accepted:
        result["reason"] = "aucun champ recevable"
        return result
    proposal = {"kind": KIND, "version": VERSION, "vault": vault.strip(), "relative_path": relative_path.strip(),
                "changes": accepted}
    result["proposal"] = proposal
    result["block"] = f"```{FENCE}\n{json.dumps(proposal, ensure_ascii=False, separators=(',', ':'))}\n```"
    result["instruction"] = ("Recopie « block » tel quel à la fin de ta réponse, après une phrase qui dit ce qui est "
                             "proposé. Rien n'est enregistré : l'opérateur coche et accepte depuis la fiche.")
    return result
