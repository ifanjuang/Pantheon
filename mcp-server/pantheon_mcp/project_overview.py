"""Where an affaire stands, for Hermes, from the file the implementation published.

The implementation writes ``<dir>/<CODE>.json`` (``pantheon.anatomy.v1``); the
Workspace Cockpit already displays it on the back of the affaire card. This
module is a second reader of the same file: no database, no key, no APU table.
It returns a compact summary a local model can quote: the current index of each
piece (drawings, models, written documents) and the questions they raise, then
the Anatomy: levels and their spaces, surfaces, the state of the work (existing
kept, projected...), totals by state and where the values come from.

Every number in the answer is read from the file, so Hermes can repeat it
instead of computing or recalling it. The summary is a projection of candidate
values, never evidence, a decision or an approval. Without
``PANTHEON_ANATOMY_DIR`` the tool answers ``anatomy_not_configured``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
from typing import Any

SCHEMA = "pantheon.anatomy.v1"
ANATOMY_DIR_ENV = "PANTHEON_ANATOMY_DIR"
MAX_BYTES = 2 * 1024 * 1024
MAX_LISTED = 200
_CODE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")

STATE_LABELS = {
    "existing": "existant",
    "to_keep": "existant conservé",
    "to_demolish": "à démolir",
    "temporary": "provisoire",
    "projected": "projeté",
    "executed": "exécuté",
}
UNSTATED = "état non renseigné"

READING_RULES = [
    "Citer les chiffres tels qu'ils figurent ici ; ne pas les recalculer ni les compléter de mémoire.",
    "Valeurs candidates lues dans les pièces, non validées : ni preuve, ni décision.",
    "Un local absent de la liste n'est pas une absence constatée : l'Anatomie ne couvre que ce qui a été lu.",
    "Les totaux par état ne portent que sur les locaux dont la surface et l'état sont renseignés.",
    "L'état actuel du projet est le dernier indice de chaque pièce de l'agence et des bureaux d'études ; "
    "une position « référence » signifie choisie par l'architecte sur la fiche du fichier, et l'emporte ; "
    "« incertaine » signifie sans indice, « probable » un indice lu dans le nom du fichier.",
    "Les questions sont des écarts relevés, à poser à l'architecte : ne pas les trancher ; "
    "toujours les signaler, en tête de réponse.",
    "Chaque date dit d'où elle vient (fiche, cartouche, nom du fichier, création du PDF) : "
    "une date de création du PDF n'est pas la date du plan.",
    "Ne rien ajouter qui ne figure pas ici (type de bâtiment, statut d'une pièce, pièces absentes) : "
    "dire « non renseigné » plutôt que supposer.",
    "Quand la focalisation renvoie plusieurs candidats avec une question, poser cette question à "
    "l'utilisateur au lieu de choisir.",
]
PIECE_KEYS = ("index", "date", "position")
SYNTHESIS_NAMES = 10  # names listed in one synthesis line; the full list stays in "current"
DATE_SOURCES = {"fiche": "fiche", "cartouche": "cartouche", "nom": "nom du fichier", "pdf": "création du PDF (incertaine)"}


def _synthesis(current: list[dict[str, Any]], to_confront: list[dict[str, Any]], questions: list[str]) -> list[str]:
    """Sentences already written from the published state, so a local model quotes instead of counting."""
    by_index: dict[str, list[str]] = {}
    for row in current:
        by_index.setdefault(row.get("index") or "", []).append(str(row["piece"]))
    lines = []
    for index in sorted(key for key in by_index if key):
        names = by_index[index]
        lines.append(f"Indice {index} : {len(names)} pièce{'s' if len(names) > 1 else ''} ({', '.join(names)}).")
    if by_index.get(""):
        names = by_index[""]
        shown = ", ".join(names[:SYNTHESIS_NAMES]) + (f" et {len(names) - SYNTHESIS_NAMES} autres" if len(names) > SYNTHESIS_NAMES else "")
        lines.append(f"Sans indice lisible ({len(names)}) : {shown}.")
    if to_confront:
        lines.append(f"{len(to_confront)} devis ou offre{'s' if len(to_confront) > 1 else ''} à confronter.")
    lines.append(f"{len(questions)} question{'s' if len(questions) > 1 else ''} ouverte{'s' if len(questions) > 1 else ''}."
                 if questions else "Aucune question ouverte.")
    return lines


def _pieces(data: dict[str, Any]) -> dict[str, Any] | None:
    """Current index of each piece and the open questions, as published beside the Anatomy."""
    pieces = data.get("pieces")
    if not isinstance(pieces, dict):
        return None
    if pieces.get("error"):
        return {"error": str(pieces["error"])}
    current, to_confront = [], []
    for item in pieces.get("pieces") or []:
        if not isinstance(item, dict):
            continue
        state = item.get("current") if isinstance(item.get("current"), dict) else {}
        row = {"piece": item.get("piece"), **{key: state.get(key) for key in PIECE_KEYS if state.get(key)}}
        if state.get("date") and state.get("date_source"):
            row["date_from"] = DATE_SOURCES.get(state["date_source"], state["date_source"])
        if state.get("paths"):
            row["file"] = f"{data['project'].get('code')}/{state['paths'][0]}"
        if item.get("variants"):
            row["variants"] = list(item["variants"])
        (to_confront if item.get("category") == "a_confronter" else current).append(row)
    questions = [str(q.get("text")) for q in pieces.get("questions") or [] if isinstance(q, dict)][:MAX_LISTED]
    return {
        "read_at": pieces.get("read_at"),
        "questions": questions,
        "synthesis": _synthesis(current, to_confront, questions),
        "current": current[:MAX_LISTED],
        "to_confront": to_confront[:MAX_LISTED],
    }


def anatomy_dir() -> Path | None:
    configured = os.environ.get(ANATOMY_DIR_ENV, "").strip()
    if not configured:
        return None
    path = Path(configured)
    return path if path.is_absolute() else None


def _available_codes(directory: Path) -> list[str]:
    try:
        names = sorted(path.stem for path in directory.glob("*.json") if not path.name.startswith("."))
    except OSError:
        return []
    return [name for name in names if _CODE.fullmatch(name)][:MAX_LISTED]


def _area(item: dict[str, Any]) -> float | None:
    for claim in item.get("attribute_claims") or []:
        value = claim.get("value") if isinstance(claim.get("value"), dict) else {}
        if claim.get("attribute_key") == "space.area" and value.get("unit") == "m2":
            number = value.get("value")
            if isinstance(number, (int, float)) and not isinstance(number, bool):
                return round(float(number), 2)
    return None


def _source(item: dict[str, Any]) -> tuple[str, str, str, str]:
    context = item.get("context") if isinstance(item.get("context"), dict) else {}
    native = context.get("native_context") if isinstance(context.get("native_context"), dict) else {}
    return (
        str(item.get("source_kind") or ""),
        str(context.get("document_ref") or item.get("source_artifact_ref") or ""),
        str(native.get("index") or ""),
        str(native.get("issuer") or ""),
    )


def summarize(data: dict[str, Any]) -> dict[str, Any]:
    """Compact summary of one published projection (already parsed and checked)."""
    anatomy = data["anatomy"]
    objects = {item["object_id"]: item for item in (anatomy.get("structure") or {}).get("objects") or []
               if isinstance(item, dict) and item.get("object_id")}
    children: dict[str, list[tuple[str, str | None]]] = {}
    contained: set[str] = set()
    for item in objects.values():
        for relation in item.get("relations") or []:
            target = (relation.get("object_ref") or {}).get("entity_id")
            if (relation.get("relation_type") != "spatial.contains"
                    or (relation.get("subject_ref") or {}).get("entity_id") != item["object_id"]
                    or target not in objects):
                continue
            qualifier = relation.get("qualifier") if isinstance(relation.get("qualifier"), dict) else {}
            children.setdefault(item["object_id"], []).append((target, qualifier.get("ouvrage_state")))
            contained.add(target)

    def entry(object_id: str, state: str | None = None) -> dict[str, Any]:
        item = objects[object_id]
        row: dict[str, Any] = {"name": item.get("display_name") or object_id}
        if item.get("internal_code"):
            row["code"] = item["internal_code"]
        area = _area(item)
        if area is not None:
            row["area_m2"] = area
        row["state"] = STATE_LABELS.get(state, state) if state else UNSTATED
        return row

    levels = []
    totals: dict[str, float] = {}
    counted = 0
    for object_id, item in objects.items():
        if object_id not in children or object_id in contained:
            continue
        spaces = [entry(child, state) for child, state in children[object_id]]
        for space in spaces:
            if "area_m2" in space and space["state"] != UNSTATED:
                totals[space["state"]] = round(totals.get(space["state"], 0.0) + space["area_m2"], 2)
                counted += 1
        levels.append({"name": item.get("display_name") or object_id, **({"code": item["internal_code"]} if item.get("internal_code") else {}),
                       "spaces": spaces[:MAX_LISTED]})
    others = [{**{k: v for k, v in entry(object_id).items() if k != "state"}, "family": objects[object_id].get("object_family")}
              for object_id in objects if object_id not in children and object_id not in contained]

    sources: dict[tuple[str, str, str, str], int] = {}
    for item in anatomy.get("sources") or []:
        if isinstance(item, dict):
            key = _source(item)
            sources[key] = sources.get(key, 0) + 1
    summary = anatomy.get("summary") or {}
    pieces = _pieces(data)
    project = {key: data["project"].get(key) for key in ("code", "display_name", "description", "phase")
               if data["project"].get(key)}
    return {
        "found": True,
        "project": project,
        **({"anatomy_status": "Anatomie non encore installée : seules les pièces et la lecture de la maquette "
                              "sont disponibles."} if anatomy.get("status") == "not_installed" else {}),
        **({"open_questions": pieces["questions"]} if pieces and pieces.get("questions") else {}),
        "published_at": data.get("generated_at"),
        **({"pieces": pieces} if pieces is not None else {}),
        "owner_revision": anatomy.get("owner_revision"),
        "levels": levels,
        "other_objects": others[:MAX_LISTED],
        "surfaces_by_state_m2": totals,
        "spaces_counted_in_totals": counted,
        "sources": [
            {"kind": kind, "document": document, **({"index": index} if index else {}),
             **({"issuer": issuer} if issuer else {}), "occurrences": count}
            for (kind, document, index, issuer), count in sorted(sources.items())
        ],
        "attention": {
            "claims_requiring_attention": summary.get("attention_claim_count", 0),
            "sources_with_identity_pending": summary.get("unmapped_source_representation_count", 0),
        },
        "status": "valeurs candidates, non validées",
        "reading_rules": list(READING_RULES),
    }


MODEL_FILE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}\.maquette-[a-z0-9-]{1,40}\.json$")
MAX_MODEL_BYTES = 8 * 1024 * 1024


def _fold(text: Any) -> str:
    table = str.maketrans("àâäéèêëîïôöùûüç", "aaaeeeeiioouuuc")
    words = str(text or "").lower().translate(table).replace("_", " ").replace("n°", " ").replace("nº", " ").split()
    return " ".join(w for w in words if w not in {"no", "numero", "num"})


def _load_models(directory: Path, data: dict[str, Any]) -> list[dict[str, Any]]:
    """Model readings published beside the projection (one per current model piece)."""
    models = []
    for status in data.get("models") or []:
        name = status.get("file") if isinstance(status, dict) else None
        if not isinstance(name, str) or not MODEL_FILE.fullmatch(name):
            continue
        try:
            with (directory / name).open("rb") as file:
                raw = file.read(MAX_MODEL_BYTES + 1)
            reading = json.loads(raw) if len(raw) <= MAX_MODEL_BYTES else None
        except (OSError, ValueError):
            reading = None
        if isinstance(reading, dict) and reading.get("schema") == "pantheon.model_reading.v1":
            models.append(reading)
    return models


def _states(data: dict[str, Any]) -> dict[str, str]:
    """State of the work by IFC GlobalId: containment state of the object each IFC occurrence represents."""
    anatomy = data["anatomy"]
    by_object: dict[str, str] = {}
    for item in (anatomy.get("structure") or {}).get("objects") or []:
        for relation in item.get("relations") or []:
            qualifier = relation.get("qualifier") if isinstance(relation.get("qualifier"), dict) else {}
            target = (relation.get("object_ref") or {}).get("entity_id")
            if relation.get("relation_type") == "spatial.contains" and qualifier.get("ouvrage_state") and target:
                by_object[target] = STATE_LABELS.get(qualifier["ouvrage_state"], qualifier["ouvrage_state"])
    states: dict[str, str] = {}
    for source in anatomy.get("sources") or []:
        guid = next((i.get("value") for i in source.get("identifiers") or []
                     if isinstance(i, dict) and i.get("scheme") == "ifc.global_id"), None)
        if not guid:
            continue
        objects = list(source.get("mapped_object_refs") or []) + [
            (claim.get("object_ref") or {}).get("entity_id") for claim in source.get("identity_claims") or []
            if claim.get("relation_type") == "identity.represents"]
        state = next((by_object[o] for o in objects if o in by_object), None)
        if state:
            states[guid] = state
    return states


def _side(item: dict[str, Any], own: str, names: dict[str, str]) -> str:
    other = [names.get(s, "?") for s in item.get("sides") or [] if s and s != own]
    if other:
        return f"vers {other[0]}"
    return f"extérieur, façade {item['facade']}" if item.get("exterior") and item.get("facade") else "côté non déterminé"


FACADE_NAMES = {"nord", "est", "sud", "ouest"}
# Element words of a designation: kind of element, and whether it is exterior (None: either).
ELEMENT_WORDS = {
    "cloison": ("mur", False), "cloisons": ("mur", False), "mur": ("mur", None), "murs": ("mur", None),
    "fenetre": ("fenêtre", None), "fenetres": ("fenêtre", None), "porte": ("porte", None), "portes": ("porte", None),
}
LABELS = {("mur", False): "la cloison", ("mur", True): "le mur extérieur", ("mur", None): "le mur",
          ("fenêtre", None): "la fenêtre", ("porte", None): "la porte"}


def _designation(reading: dict[str, Any], words: list[str], names: dict[str, str],
                 elements: list[dict[str, Any]], row) -> dict[str, Any] | None:
    """'cloison file 5', 'fenêtre façade sud chambre 1': one element, or the candidates and the question to ask."""
    kind_word = next((w for w in words if w in ELEMENT_WORDS), None)
    if kind_word is None:
        return None
    kind, exterior = ELEMENT_WORDS[kind_word]
    plural = kind_word.endswith("s")  # "fenêtres de la chambre 1": all of them, not "which one?"
    rest = [w for w in words if w != kind_word]
    if "exterieur" in rest or "exterieurs" in rest:
        exterior, rest = True, [w for w in rest if w not in {"exterieur", "exterieurs"}]
    if "interieur" in rest:
        exterior, rest = False, [w for w in rest if w != "interieur"]
    tags, facade_dir, level = [], None, None
    levels = {_fold(lv.get("name")) for lv in reading.get("levels") or []}
    grid_lines = {g.upper() for g in reading.get("grid_lines") or []}
    room_words = []
    i = 0
    while i < len(rest):
        word = rest[i]
        if word in {"file", "files", "axe"} and i + 1 < len(rest):
            tags.append(rest[i + 1].upper()); i += 2; continue
        if word == "facade" and i + 1 < len(rest) and rest[i + 1] in FACADE_NAMES:
            facade_dir = rest[i + 1]; i += 2; continue
        if word in levels:
            level = word; i += 1; continue
        # A bare grid tag counts only after a grid word: the "1" of "chambre 1" names the room.
        if word.upper() in grid_lines and len(word) <= 3 and i > 0 and rest[i - 1] in {"entre", "et", "sur"}:
            tags.append(word.upper()); i += 1; continue
        if word not in {"de", "du", "la", "le", "les", "sur", "entre", "et", "dans", "des"}:
            room_words.append(word)
        i += 1
    room = " ".join(room_words)
    found = [e for e in elements if e["_what"] == kind
             and (exterior is None or bool(e.get("exterior")) == exterior)
             and all(_on_grid(e.get("grid"), tag) for tag in tags)
             and (facade_dir is None or e.get("facade") == facade_dir)
             and (level is None or _fold(e.get("level")) == level)
             and (not room or any(room in _fold(names.get(s)) for s in e.get("sides") or [] if s))]
    label = LABELS.get((kind, exterior if kind == "mur" else None), "l'élément")
    if not found:
        return {"found": False, "kind": "désignation", "reason": f"aucun élément ne correspond à « {' '.join(words)} »"}
    rows = [row(e) for e in found]
    if len(rows) == 1:
        return {"found": True, "kind": "élément", **rows[0]}
    if plural:
        return {"found": True, "kind": "sélection", "critère": " ".join(words), "nombre": len(rows), "éléments": rows[:MAX_LISTED]}

    def describe(item: dict[str, Any], detailed: bool = False) -> str:
        where = (item.get("files") or "position non déterminée").replace(" ; ", ", ")
        def metres(value: float) -> str:
            return f"{value:.2f}".replace(".", ",") + " m"

        details = list(dict.fromkeys(item.get("locaux") or []))
        details = [" / ".join(details)] if details else []
        if item.get("façade"):
            details.append(f"façade {item['façade']}")
        if detailed:  # same place, same rooms: tell them apart by size
            details += [metres(v) for v in (item.get("longueur_m"), item.get("largeur_m")) if v]
            details += [f"ép. {metres(item['épaisseur_m'])}"] if item.get("épaisseur_m") else []
        return f"{label} {where}" + (f" ({', '.join(details)})" if details else "")

    plain = [describe(r) for r in rows]
    if len(set(plain)) < len(plain):
        plain = [describe(r, detailed=True) for r in rows]

    question = ("Parlez-vous de " + ", ou de ".join(plain) + " ?") if len(rows) <= 4 else \
        f"{len(rows)} éléments correspondent : précisez la file, la façade, le niveau ou la pièce."
    return {"found": False, "kind": "désignation", "plusieurs": len(rows), "candidats": rows[:MAX_LISTED], "question": question}


def _on_grid(position: Any, tag: str) -> bool:
    """'sur la file M' or 'entre L et M' names the grid line tag."""
    text = f" {position or ''} ".replace(";", " ; ")
    return f" file {tag} " in text or f" et {tag} " in text or f"entre {tag} " in text


def _selection(reading: dict[str, Any], wanted: str, states: dict[str, str]) -> dict[str, Any] | None:
    """Elements on one grid line, on one façade, or spaces on one level: the reverse questions."""
    names = {s["id"]: s["name"] for s in reading.get("spaces") or []}
    elements = [{**o, "_what": o["kind"]} for o in reading.get("openings") or []] + \
               [{**w, "_what": "mur"} for w in reading.get("walls") or []]

    def row(item: dict[str, Any]) -> dict[str, Any]:
        sides = [names.get(s, "?") for s in item.get("sides") or [] if s]
        return {"élément": item["_what"], **({"largeur_m": item["width_m"]} if item.get("width_m") else {}),
                **({"hauteur_m": item["height_m"]} if item.get("height_m") else {}),
                **({"épaisseur_m": item["thickness_m"]} if item.get("thickness_m") else {}),
                **({"longueur_m": item["length_m"]} if item.get("length_m") else {}),
                "locaux": sides, **({"façade": item["facade"]} if item.get("facade") else {}),
                **({"files": item["grid"]} if item.get("grid") else {}), "niveau": item.get("level"), "id": item["id"]}

    words = wanted.split()
    designated = _designation(reading, words, names, elements, row)
    if designated is not None:
        return designated
    if len(words) == 2 and words[0] in {"file", "files", "axe"}:
        tag = words[1].upper()
        if tag not in set(reading.get("grid_lines") or []):
            return {"found": False, "reason": f"pas de file {tag} dans la maquette",
                    "candidates": list(reading.get("grid_lines") or [])}
        rows = [row(e) for e in elements if _on_grid(e.get("grid"), tag)]
        return {"found": True, "kind": "sélection", "critère": f"file {tag}", "nombre": len(rows), "éléments": rows[:MAX_LISTED]}
    if len(words) == 2 and words[0] == "facade" and words[1] in FACADE_NAMES:
        rows = [row(e) for e in elements if e.get("facade") == words[1]]
        return {"found": True, "kind": "sélection", "critère": f"façade {words[1]}", "nombre": len(rows), "éléments": rows[:MAX_LISTED]}
    levels = {_fold(level.get("name")): level.get("name") for level in reading.get("levels") or []}
    if wanted in levels:
        spaces = [{"local": s["name"], "surface_m2": s.get("area_m2"), "état": states.get(s["id"], UNSTATED)}
                  for s in reading.get("spaces") or [] if _fold(s.get("level")) == wanted]
        return {"found": True, "kind": "sélection", "critère": f"niveau {levels[wanted]}", "nombre": len(spaces),
                "locaux": spaces[:MAX_LISTED],
                "ouvertures": sum(1 for o in reading.get("openings") or [] if _fold(o.get("level")) == wanted)}
    return None


def _focus(directory: Path, data: dict[str, Any], focus: str) -> dict[str, Any]:
    """Sheet of one space or element, or a selection by grid line, façade or level, from the current model reading."""
    models = _load_models(directory, data)
    if not models:
        return {"found": False, "reason": "aucune lecture de maquette publiée pour cette affaire"}
    wanted = _fold(focus)
    states = _states(data)
    # The architect's model (with spaces) first; engineers' models complete it.
    models.sort(key=lambda r: -len(r.get("spaces") or []))
    missed = None
    for reading in models:
        selected = _selection(reading, wanted, states)
        if selected is None:
            continue
        selected = {**selected, "source": {"piece": reading["source"].get("piece"), "index": reading["source"].get("index")},
                    "limites": list(reading.get("limits") or [])}
        if selected.get("found"):
            return selected
        missed = missed or selected
    if missed is not None:
        return missed
    for reading in models:
        names = {s["id"]: s["name"] for s in reading.get("spaces") or []}
        spaces = reading.get("spaces") or []
        exact = [s for s in spaces if wanted in {_fold(s.get("name")), _fold(s.get("number"))}]
        partial = exact or [s for s in spaces if wanted and wanted in _fold(s.get("name"))]
        if not partial:  # "chambre r01": a name followed by a level or a number
            words = wanted.split()
            partial = [s for s in spaces if words and any(
                _fold(s.get("name")) == " ".join(words[:cut]) and set(words[cut:]) <= {_fold(s.get("level")), _fold(s.get("number"))}
                for cut in range(1, len(words)))]
        element = next((e for e in (reading.get("openings") or []) + (reading.get("walls") or [])
                        if len(wanted) >= 6 and str(e.get("id", "")).lower().startswith(wanted)), None)
        source = {"piece": reading["source"].get("piece"), "index": reading["source"].get("index"),
                  "file": reading["source"].get("file")}
        notes = list(reading.get("limits") or [])
        if len(partial) > 1:
            return {"found": False, "candidates": [f"{s['name']} {s.get('level') or ''} (n° {s.get('number') or '?'})".strip()
                                                   for s in partial][:MAX_LISTED],
                    "reason": "plusieurs locaux correspondent : préciser le niveau ou le numéro"}
        if partial:
            space = partial[0]
            sid = space["id"]
            openings = [{"élément": o["kind"], "largeur_m": o.get("width_m"), "hauteur_m": o.get("height_m"),
                         "donne": _side(o, sid, names), **({"files": o["grid"]} if o.get("grid") else {}),
                         **({"type": o["type"]} if o.get("type") else {}), "id": o["id"]}
                        for o in reading.get("openings") or [] if sid in (o.get("sides") or [])]
            walls = [{"mur": _side(w, sid, names), "épaisseur_m": w.get("thickness_m"), "longueur_m": w.get("length_m"),
                      **({"composition": w["composition"]} if w.get("composition") else {}),
                      **({"files": w["grid"]} if w.get("grid") else {}), "jonctions": len(w.get("junctions") or []),
                      "id": w["id"]}
                     for w in reading.get("walls") or [] if sid in (w.get("sides") or [])]
            linked = sorted({names.get(x, "?") for n in reading.get("neighbours") or [] if sid in n["spaces"]
                             for x in n["spaces"] if x != sid and n["via"] == "porte"})
            touching = sorted({names.get(x, "?") for n in reading.get("neighbours") or [] if sid in n["spaces"]
                               for x in n["spaces"] if x != sid and n["via"] == "mur"})
            return {"found": True, "kind": "local", "name": space["name"], "level": space.get("level"),
                    "surface_m2": space.get("area_m2"), "état": states.get(sid, UNSTATED),
                    "relié_par_porte_à": linked, "mur_commun_avec": touching,
                    "ouvertures": openings, "murs": walls, "source": source, "limites": notes}
        if element:
            return {"found": True, "kind": "élément", "élément": element.get("kind", "mur"),
                    **{k: v for k, v in element.items() if k not in {"sides", "kind"}},
                    "côtés": [names.get(s, "extérieur") if s else "extérieur" for s in element.get("sides") or []],
                    "source": source, "limites": notes}
    return {"found": False, "candidates": [f"{s['name']} {s.get('level') or ''} (n° {s.get('number') or '?'})".strip()
                                           for r in models for s in r.get("spaces") or []][:MAX_LISTED],
            "reason": "aucun local ni élément ne correspond"}


DETAIL_HINT = ("Détail sur demande avec focus : « pièces » (toutes les pièces courantes et leurs fichiers), "
               "« devis », « locaux », un local (« cuisine », « chambre 101 »), « file M », « façade sud », "
               "un niveau (« R01 »), ou un élément (« cloison file 5 », « fenêtre façade sud chambre 1 »).")


def _compact(full: dict[str, Any], directory: Path, data: dict[str, Any]) -> dict[str, Any]:
    """The answer without focus: small enough for a local model to read whole (target a few kilobytes)."""
    pieces = full.get("pieces") or {}
    compact: dict[str, Any] = {key: full[key] for key in ("code", "found", "source", "project", "anatomy_status",
                                                          "open_questions", "published_at") if key in full}
    if pieces:
        compact["pieces"] = {k: pieces[k] for k in ("questions", "synthesis", "error") if k in pieces}
        compact["pieces"]["counts"] = {"current": len(pieces.get("current") or []),
                                       "to_confront": len(pieces.get("to_confront") or [])}
    if full.get("models"):
        compact["models"] = full["models"]
    if full.get("levels"):
        compact["levels"] = [{"name": level["name"], "spaces": [
            f"{s['name']}" + (f" {s['area_m2']} m²" if s.get("area_m2") is not None else "")
            + (f" ({s['state']})" if s.get("state") and s["state"] != UNSTATED else "") for s in level["spaces"]]}
            for level in full["levels"]]
        compact["surfaces_by_state_m2"] = full.get("surfaces_by_state_m2")
        compact["spaces_counted_in_totals"] = full.get("spaces_counted_in_totals")
    else:  # no Anatomy yet: the rooms the current model shows
        models = sorted(_load_models(directory, data), key=lambda r: -len(r.get("spaces") or []))
        if models and models[0].get("spaces"):
            by_level: dict[str, list[str]] = {}
            for space in models[0]["spaces"]:
                by_level.setdefault(space.get("level") or "?", []).append(f"{space['name']} {space.get('area_m2')} m²")
            compact["model_spaces"] = {"source": models[0]["source"].get("piece"), "index": models[0]["source"].get("index"),
                                       "levels": by_level}
    compact["status"] = full.get("status")
    compact["reading_rules"] = full.get("reading_rules")
    compact["detail"] = DETAIL_HINT
    return compact


def project_overview(code: str, directory: Path | None = None, focus: str = "") -> dict[str, Any]:
    directory = directory if directory is not None else anatomy_dir()
    code = str(code or "").strip()
    result: dict[str, Any] = {"code": code, "found": False, "source": f"projection publiée {SCHEMA}"}
    if directory is None:
        return {**result, "error": "anatomy_not_configured"}
    if not code:
        return {**result, "error": "code_required", "available_codes": _available_codes(directory)}
    if not _CODE.fullmatch(code):
        return {**result, "error": "invalid_code"}
    if not (directory / f"{code}.json").exists():  # "demo" names DEMO: match the code whatever its case
        code = next((c for c in _available_codes(directory) if c.lower() == code.lower()), code)
        result["code"] = code
    try:
        with (directory / f"{code}.json").open("rb") as file:
            raw = file.read(MAX_BYTES + 1)
    except FileNotFoundError:
        return {**result, "error": "no_anatomy", "available_codes": _available_codes(directory)}
    except OSError:
        return {**result, "error": "anatomy_unavailable"}
    try:
        if len(raw) > MAX_BYTES:
            raise ValueError("oversize")
        data = json.loads(raw)
        if data.get("schema") != SCHEMA or (data.get("project") or {}).get("code") != code:
            raise ValueError("schema")
        full = {**result, **summarize(data)}
        if data.get("models"):
            full["models"] = [{k: m.get(k) for k in ("piece", "index", "status") if m.get(k)}
                              for m in data["models"] if isinstance(m, dict)]
        wanted = _fold(focus)
        if not wanted:
            return _compact(full, directory, data)
        # With a focus, only a short header travels with the detail asked for.
        overview = {key: full[key] for key in ("code", "found", "source", "project", "anatomy_status", "open_questions")
                    if key in full}
        first, _, rest = wanted.partition(" ")
        if first in {"pieces", "documents", "plans"}:
            listed = (full.get("pieces") or {}).get("current", [])
            if rest:  # "pièces dce", "pièces cctp": name or folder contains the word
                listed = [row for row in listed if rest in _fold(row.get("piece")) or rest in _fold(row.get("file"))]
            overview["focus"] = {"found": True, "kind": "pièces", "filtre": rest or None, "nombre": len(listed), "pièces": listed}
        elif wanted in {"devis", "offres"}:
            overview["focus"] = {"found": True, "kind": "devis", "devis": (full.get("pieces") or {}).get("to_confront", [])}
        elif wanted in {"locaux", "surfaces", "anatomie"}:
            overview["focus"] = {"found": True, "kind": "locaux", "levels": full.get("levels", []),
                                 "surfaces_by_state_m2": full.get("surfaces_by_state_m2"),
                                 "spaces_counted_in_totals": full.get("spaces_counted_in_totals")}
        elif wanted:
            overview["focus"] = _focus(directory, data, str(focus))
        return overview
    except (ValueError, TypeError, KeyError, AttributeError):
        return {**result, "error": "anatomy_unreadable"}
