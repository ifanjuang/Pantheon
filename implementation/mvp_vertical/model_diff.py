"""What changed between two indices of a model, from their readings.

Authoring tools keep an element's IFC GlobalId from one export to the next, so
two readings of one model can be compared element by element: rooms added,
removed or changed (name, area), openings and walls resized or moved to another
façade, elements of each category added or removed. The comparison works on the
readings (file sheets), not on the IFC files: it is quick, says what changed in
the words of the readings, and needs no geometry engine.

When few identifiers are shared, the authoring tool did not keep them (or the
files are not two indices of one model): the comparison says so instead of
reporting everything as removed and added.

Two current model pieces sharing most identifiers are one model under two names
(a provisional index filed apart): that is a question for the architect, never
resolved here.
"""

from __future__ import annotations

from typing import Any

RELIABLE_SHARE = 0.30   # below this share of common identifiers the comparison is not meaningful
SAME_MODEL_SHARE = 0.50  # two current models sharing this share of the smaller one are one model
LENGTH_TOLERANCE = 0.02  # metres
AREA_TOLERANCE = 0.10    # square metres
LISTED = 15

FIELDS = {
    "spaces": (("name", None), ("level", None), ("area_m2", AREA_TOLERANCE)),
    "openings": (("nature", None), ("level", None), ("width_m", LENGTH_TOLERANCE), ("height_m", LENGTH_TOLERANCE),
                 ("sill_m", LENGTH_TOLERANCE), ("facade", None)),
    "walls": (("label", None), ("level", None), ("thickness_m", LENGTH_TOLERANCE), ("length_m", LENGTH_TOLERANCE),
              ("facade", None)),
    "elements": (("label", None), ("level", None), ("width_m", LENGTH_TOLERANCE), ("height_m", LENGTH_TOLERANCE),
                 ("length_m", LENGTH_TOLERANCE)),
}
WORDS = {"name": "nom", "level": "niveau", "area_m2": "surface_m2", "nature": "nature", "width_m": "largeur_m",
         "height_m": "hauteur_m", "sill_m": "allège_m", "facade": "façade", "thickness_m": "épaisseur_m",
         "length_m": "longueur_m", "label": "catégorie"}


def _ids(reading: dict[str, Any]) -> set[str]:
    return {item["id"] for kind in FIELDS for item in reading.get(kind) or [] if item.get("id")}


def shared_share(a: dict[str, Any], b: dict[str, Any]) -> float:
    """Share of the smaller reading's identifiers found in the other."""
    ids_a, ids_b = _ids(a), _ids(b)
    smaller = min(len(ids_a), len(ids_b))
    return len(ids_a & ids_b) / smaller if smaller else 0.0


def _differs(old: Any, new: Any, tolerance: float | None) -> bool:
    if tolerance is None or not isinstance(old, (int, float)) or not isinstance(new, (int, float)):
        return old != new
    return abs(old - new) > tolerance


def _label(kind: str, item: dict[str, Any], rooms: dict[str, str]) -> str:
    """How a person names an element: its nature or category, where it is."""
    if kind == "spaces":
        return f"{item.get('name') or 'local'} {item.get('level') or ''}".strip()
    what = item.get("nature") or item.get("label") or item.get("kind") or ("mur" if kind == "walls" else "élément")
    where = [rooms[s] for s in item.get("sides") or [] if s in rooms] or ([rooms[item["space"]]] if item.get("space") in rooms else [])
    parts = [what]
    if item.get("facade"):
        parts.append(f"façade {item['facade']}")
    if where:
        parts.append(" / ".join(sorted(set(where))))
    if item.get("level"):
        parts.append(str(item["level"]))
    return ", ".join(parts)


def compare(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """The changes from the old reading to the new one, bounded for a screen or a local model."""
    share = shared_share(old, new)
    result: dict[str, Any] = {
        "de": {k: (old.get("source") or {}).get(k) for k in ("piece", "index")},
        "à": {k: (new.get("source") or {}).get(k) for k in ("piece", "index")},
        "identifiants_communs": round(share, 2),
        "confiance": "déduit (comparaison des lectures, élément par élément)",
        "limite": "un changement peut venir de la modélisation (local ajouté ou redessiné, famille changée), "
                  "pas seulement du projet : le dire avant d'en tirer une conclusion",
    }
    if share < RELIABLE_SHARE:
        result["fiable"] = False
        result["raison"] = ("trop peu d'identifiants communs : l'outil d'export ne les a pas conservés, ou ce ne sont "
                            "pas deux indices d'une même maquette ; comparaison élément par élément impossible")
        return result
    result["fiable"] = True
    old_rooms = {s["id"]: s.get("name") for s in old.get("spaces") or [] if s.get("id")}
    new_rooms = {s["id"]: s.get("name") for s in new.get("spaces") or [] if s.get("id")}
    counts: dict[str, dict[str, int]] = {}
    for kind, fields in FIELDS.items():
        before = {i["id"]: i for i in old.get(kind) or [] if i.get("id")}
        after = {i["id"]: i for i in new.get(kind) or [] if i.get("id")}
        added = [_label(kind, after[i], new_rooms) for i in after.keys() - before.keys()]
        removed = [_label(kind, before[i], old_rooms) for i in before.keys() - after.keys()]
        changed = []
        for element_id in sorted(before.keys() & after.keys()):
            a, b = before[element_id], after[element_id]
            changes = {WORDS[f]: [a.get(f), b.get(f)] for f, tolerance in fields if _differs(a.get(f), b.get(f), tolerance)}
            if changes:
                changed.append({"élément": _label(kind, b, new_rooms), "changements": changes, "id": element_id})
        counts[kind] = {"ajoutés": len(added), "supprimés": len(removed), "modifiés": len(changed)}
        section = {}
        if added:
            section["ajoutés"] = _grouped(added)
        if removed:
            section["supprimés"] = _grouped(removed)
        if changed:
            section["modifiés"] = changed[:LISTED]
        if section:
            result[{"spaces": "locaux", "openings": "ouvertures", "walls": "murs", "elements": "éléments"}[kind]] = section
    result["nombres"] = counts
    result["résumé"] = summary(counts)
    return result


def _grouped(labels: list[str]) -> list[str]:
    """Identical labels once, with their count: « cloison, Chambre 2, R00 (×2) »."""
    counts: dict[str, int] = {}
    for label in labels:
        counts[label] = counts.get(label, 0) + 1
    return [f"{label} (×{n})" if n > 1 else label for label, n in sorted(counts.items())][:LISTED]


def summary(counts: dict[str, dict[str, int]]) -> str:
    """One line: « locaux : 2 ajoutés, 3 modifiés ; murs : 12 supprimés … »."""
    names = {"spaces": "locaux", "openings": "ouvertures", "walls": "murs", "elements": "éléments"}
    parts = []
    for kind, numbers in counts.items():
        said = [f"{n} {word}" for word, n in numbers.items() if n]
        if said:
            parts.append(f"{names[kind]} : {', '.join(said)}")
    return " ; ".join(parts) or "aucun changement lu"


def same_model_questions(readings: list[dict[str, Any]], dates: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """Current model pieces that are one model under two names: a question each, never a decision.

    The question gives each index and its date, and which one is more recent: a fact to help the
    architect, not a choice.
    """
    dates = dates or {}
    questions = []
    for i, a in enumerate(readings):
        for b in readings[i + 1:]:
            if a.get("discipline") != b.get("discipline"):
                continue
            share = shared_share(a, b)
            if share < SAME_MODEL_SHARE:
                continue
            named = []
            for reading in (a, b):
                source = reading.get("source") or {}
                date = dates.get(str(source.get("piece")))
                named.append((f"{source.get('piece')} {source.get('index') or ''}".strip(), date))
            text = (f"{named[0][0]}{f' ({named[0][1]})' if named[0][1] else ''} et {named[1][0]}"
                    f"{f' ({named[1][1]})' if named[1][1] else ''} : même maquette sous deux noms "
                    f"({round(100 * share)} % d'identifiants IFC communs)")
            if named[0][1] and named[1][1] and named[0][1] != named[1][1]:
                text += f" ; la plus récente est {max(named, key=lambda n: n[1])[0]}"
            questions.append({"piece": named[0][0], "kind": "meme_maquette", "share": round(share, 2),
                              "text": text + " ; laquelle fait foi ?"})
    return questions
