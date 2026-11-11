"""Anatomy sources: which files feed an affaire's readings, and in what state.

The human declares, on each file, whether it is an anatomy source and how
(``anatomy_source`` on the Workspace document card): added as a complement or
replacing another source, its role (reference, complement, control), discipline,
use, scope, the alignment known at export, a note, and whether to consolidate
now. The Workspace owns that declaration.

Consolidation, on the agency side, reads the declared sources, overlays the
engineers' models, and decides each source's state, published with the Anatomy
for the Cockpit and Hermes:

- ``en attente``: declared but not consolidated yet;
- ``activée``: consolidated without problem;
- ``avertissement``: consolidated with minor inconsistencies (model quality to
  improve, overlay to confirm, size gaps, unreadable index);
- ``erreur``: cannot be brought together (unreadable, overlay uncertain,
  missing file);
- ``remplacée``: replaced by a source whose consolidation succeeded;
- ``inactive``: declared, then switched off on its card; not read.

A replacement takes effect only when the new source's consolidation succeeds;
otherwise the old source stays active and the new one carries the error. In the
readings the replaced source is no longer read; in the validated Anatomy nothing
is erased: values from the old source are superseded through a reviewed batch.

While no file of an affaire declares anything, the readings keep their former
behaviour (every current model piece is read).
"""

from __future__ import annotations

from typing import Any

PENDING, ACTIVE, WARNING, ERROR, REPLACED = "en attente", "activée", "avertissement", "erreur", "remplacée"
DISABLED = "inactive"
USABLE = {ACTIVE, WARNING}
ROLES = {"référence", "complément", "contrôle"}
MODES = {"complément", "remplacement"}
DECLARED_TEXT = ("discipline", "usage", "perimeter", "declared_alignment", "note", "set_by", "set_at")


def normalize(raw: Any) -> dict[str, Any] | None:
    """The declaration of one file, with defaults; None when the file is not declared at all."""
    if not isinstance(raw, dict):
        return None
    declared = {
        "active": raw.get("active") is True,
        "mode": raw.get("mode") if raw.get("mode") in MODES else "complément",
        "role": raw.get("role") if raw.get("role") in ROLES else "complément",
        "consolidate_now": raw.get("consolidate_now") is True,
    }
    if declared["mode"] == "remplacement" and isinstance(raw.get("replaces"), str) and raw["replaces"].strip():
        declared["replaces"] = raw["replaces"].strip()
    for key in DECLARED_TEXT:
        if isinstance(raw.get(key), str) and raw[key].strip():
            declared[key] = raw[key].strip()[:300]
    confirmed = raw.get("alignment_confirmed")
    if isinstance(confirmed, dict) and confirmed.get("by"):
        declared["alignment_confirmed"] = {k: str(confirmed[k]) for k in ("by", "at", "reference_fingerprint", "source_fingerprint")
                                           if confirmed.get(k)}
    return declared


def common_frame(declared: dict[str, Any]) -> bool:
    """The card says the model was exported in shared coordinates or from an agreed origin."""
    text = declared.get("declared_alignment", "").lower()
    return "partag" in text or "origine" in text or "shared" in text


def model_state(reading: dict[str, Any] | None, status: dict[str, Any] | None,
                declared: dict[str, Any]) -> tuple[str, list[str]]:
    """State of a model source from its reading, with the reasons."""
    if status is None or status.get("status") == "absent":
        return ERROR, ["fichier introuvable"]
    if status.get("status") == "unreadable" or reading is None:
        return ERROR, [f"maquette illisible ({status.get('error') or 'lecture impossible'})"]
    quality = reading.get("quality") or {}
    messages: list[str] = []
    if quality.get("niveau") == "insuffisante":
        return ERROR, ["qualité insuffisante : " + "; ".join(quality.get("conseils_export") or [])[:300]]
    alignment = reading.get("alignment")
    if reading.get("discipline") == "structure" and alignment is not None:
        if alignment.get("verdict") != "probable" and not common_frame(declared):
            why = alignment.get("reason") or f"score {alignment.get('score')}, marge {alignment.get('margin')}"
            return ERROR, [f"rapprochement impossible avec la maquette d'architecture (recalage {alignment.get('verdict')} : {why}) ; "
                           "réexporter en coordonnées partagées ou depuis une origine convenue"]
        confirmed = declared.get("alignment_confirmed") or {}
        if alignment.get("verdict") == "probable" and confirmed.get("reference_fingerprint") != alignment.get("reference_fingerprint"):
            messages.append(f"recalage estimé à confirmer ({round(100 * (alignment.get('score') or 0))} % des points sur les murs)")
    elif reading.get("discipline") == "structure" and not common_frame(declared):
        messages.append("pas de maquette d'architecture active pour la superposer")
    if quality.get("niveau") == "à améliorer":
        messages.append("qualité de la maquette à améliorer")
    gaps = sum(1 for o in reading.get("openings") or [] if any("dimension déclarée" in c for c in o.get("clues") or []))
    if gaps:
        messages.append(f"{gaps} ouvertures dont la dimension déclarée diffère de la mesure")
    return (WARNING if messages else ACTIVE), messages


def document_state(piece: dict[str, Any] | None, questions: list[str]) -> tuple[str, list[str]]:
    """State of a drawing or written document from the current-state reading."""
    if piece is None:
        return WARNING, ["pas l'indice courant d'une pièce suivie : lu comme document isolé"]
    messages = ["indice et texte, sans calage géométrique"]
    position = (piece.get("current") or {}).get("position")
    if position in {"probable", "incertaine"}:
        messages.insert(0, "indice lu dans le nom du fichier" if position == "probable" else "indice non lu")
    messages += [q for q in questions if q.startswith(str(piece.get("piece")))]
    return (WARNING if len(messages) > 1 else ACTIVE), messages


def declaration_stamp(declared: dict[str, Any]) -> str:
    """What, in a declaration, asks for a new consolidation when it changes."""
    import json

    return json.dumps({k: declared.get(k) for k in ("active", "mode", "replaces", "declared_alignment", "alignment_confirmed")},
                      sort_keys=True, ensure_ascii=False)


def alignment_line(alignment: dict[str, Any] | None, declared: dict[str, Any]) -> dict[str, Any] | None:
    """The overlay of an engineer's model, short, for the screen and Hermes."""
    if not alignment:
        return {"déclaré": declared["declared_alignment"]} if declared.get("declared_alignment") else None
    line = {"méthode": "recalage estimé", "verdict": alignment.get("verdict"), "sur": alignment.get("reference"),
            "indice": alignment.get("reference_index"), "rotation_deg": alignment.get("rotation_deg"),
            "décalage_m": [alignment.get("dx"), alignment.get("dy"), alignment.get("dz")],
            "score": alignment.get("score"), "marge": alignment.get("margin")}
    confirmed = declared.get("alignment_confirmed") or {}
    line["confirmé"] = ({"par": confirmed.get("by"), "le": confirmed.get("at")}
                        if confirmed.get("reference_fingerprint") == alignment.get("reference_fingerprint") else False)
    if declared.get("declared_alignment"):
        line["déclaré"] = declared["declared_alignment"]
    return line


def resolve_replacements(results: dict[str, dict[str, Any]]) -> None:
    """Replace a source only when its replacement succeeded; otherwise keep the old one active."""
    for result in results.values():
        result.pop("remplacée_par", None)
        result.pop("remplace", None)
        if result["état"] == REPLACED:
            result["état"] = result.get("état_propre", ACTIVE)
    for path, result in results.items():
        target = (result.get("declared") or {}).get("replaces")
        if not target:
            continue
        if result["état"] in USABLE:
            if target in results and results[target]["état"] != DISABLED:
                results[target]["état_propre"] = results[target]["état"]
                results[target]["état"] = REPLACED
                results[target]["remplacée_par"] = path
            result["remplace"] = target
        elif result["état"] != DISABLED:
            note = ("remplacement en attente : l'ancienne source reste active" if result["état"] == PENDING
                    else "remplacement annulé : l'ancienne source reste active")
            if note not in result.setdefault("messages", []):
                result["messages"].append(note)


def summary_line(path: str, result: dict[str, Any]) -> dict[str, Any]:
    """One short line per source, for Hermes."""
    declared = result.get("declared") or {}
    line = {"fichier": path, "état": result["état"], "rôle": declared.get("role")}
    for key in ("discipline", "usage", "perimeter"):
        if declared.get(key):
            line[key] = declared[key]
    if result.get("calage"):
        line["calage"] = result["calage"]
    for key in ("remplace", "remplacée_par"):
        if result.get(key):
            line[key] = result[key]
    if result.get("messages"):
        line["messages"] = result["messages"][:4]
    return line
