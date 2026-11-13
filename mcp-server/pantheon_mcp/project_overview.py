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
    "les signaler en tête quand elles concernent la réponse, sinon en fin, en une ligne.",
    "Chaque date dit d'où elle vient (fiche, cartouche, nom du fichier, création du PDF) : "
    "une date de création du PDF n'est pas la date du plan.",
    "Ne rien ajouter qui ne figure pas ici (type de bâtiment, statut d'une pièce, pièces absentes) : "
    "dire « non renseigné » plutôt que supposer.",
    "Quand la focalisation renvoie plusieurs candidats avec une question, poser cette question à "
    "l'utilisateur au lieu de choisir.",
    "Quand une position est déduite (droite, gauche, côté), citer l'indice utilisé (façade, files) et "
    "l'hypothèse du nord en haut du plan.",
    "Quand des sources anatomiques sont déclarées, seules les sources activées ou en avertissement sont lues : "
    "qualifier la réponse par leur rôle (contrôle, complément), un calage non confirmé ou un périmètre ; "
    "une source en attente ou en erreur n'est pas lue, le dire si on la demande.",
    "Confiance, de la plus sûre à la moins sûre : validé (confirmé par un humain), lu (écrit dans la source), "
    "déduit (calculé), estimé (rapprochement entre sources, ex. recalage du BET : citer son score et demander "
    "confirmation). Qualifier la réponse par le niveau le plus faible ; ne jamais présenter un déduit ou un estimé comme lu.",
    "Si la qualité de la maquette est insuffisante ou qu'un réexport est conseillé : répondre avec ce qui "
    "est lu sans rien inventer, dire ce qui manque, et proposer à l'utilisateur de réexporter la maquette "
    "en citant les conseils d'export (donnés en entier par le focus « qualité »).",
]
PIECE_KEYS = ("index", "date", "position")
# One confidence scale for every value, strongest first: validé (confirmed by a human), lu (written in the
# source), déduit (computed from the source: geometry, neighbours), estimé (brought together across sources).
INDEX_CONFIDENCE = {"fiche": "validé", "cartouche": "lu", "nom": "déduit", None: "estimé"}
MODEL_CONFIDENCE = {
    "dimensions, nature, côtés, façade, files, locaux": "déduit (géométrie de la maquette)",
    "type_déclaré, dimension déclarée": "lu (déclaré dans la maquette)",
    "lignes marquées confiance estimé": "estimé (recalage sur la maquette d'architecture, à confirmer)",
    "état": "lu (Anatomie, valeurs candidates)",
}
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
        row = {"piece": item.get("piece"), **{key: state.get(key) for key in PIECE_KEYS if state.get(key)},
               "confiance": _piece_confidence(state)}
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


def _piece_confidence(state: dict[str, Any]) -> str:
    """How sure the current index of a piece is; files published before the index origin was kept use its position."""
    if state.get("reference"):
        return "validé"
    if "index_source" in state:
        return INDEX_CONFIDENCE.get(state["index_source"], "estimé")
    return {"certaine": "lu", "probable": "déduit"}.get(str(state.get("position")), "estimé")


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


CHANGES_FILE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}\.changements-[a-z0-9-]{1,40}\.json$")
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
    if item.get("exterior") and item.get("facade"):
        return f"extérieur, façade {item['facade']}"
    if item.get("unmodelled_side"):
        return "vers un local non modélisé (circulation, escalier)"
    return "côté non déterminé"


def _what(item: dict[str, Any]) -> str:
    """What an element is: its deduced nature or category label when the reading gives one; its family otherwise."""
    return item.get("nature") or item.get("label") or item.get("kind") or "mur"


def _to_check(item: dict[str, Any]) -> list[str]:
    return [c for c in item.get("clues") or [] if "contredit" in c or "dit intérieur" in c or "dimension déclarée" in c]


def _with_overlay(element: dict[str, Any]) -> dict[str, Any]:
    """An element of the reading as the selections see it; an engineer's element takes the rooms and grid
    position its estimated overlay on the architect's model gives it."""
    item = {**element, "_what": _what(element), "sides": [element["space"]] if element.get("space") else []}
    overlay = element.get("via_recalage")
    if overlay and not element.get("space"):
        rooms = [overlay["local"]] if overlay.get("local") else list(overlay.get("locaux_voisins") or [])
        item.update(_rooms=rooms, grid=element.get("grid") or overlay.get("files"),
                    level=overlay.get("niveau_archi") or element.get("level"), _overlaid=True)
    return item


def _category_phrase(reading: dict[str, Any], words: list[str]) -> tuple[set[str], list[str], bool] | None:
    """Labels named by the longest synonym phrase of the query (« garde corps », « poteaux »), the other words, plural."""
    vocabulary: dict[str, set[str]] = {}
    for label, synonyms in (reading.get("categories") or {}).items():
        for synonym in synonyms:
            vocabulary.setdefault(_fold(synonym), set()).add(label)
    for size in (3, 2, 1):
        for start in range(0, len(words) - size + 1):
            phrase = " ".join(words[start:start + size])
            # A plural is a word ending in s or x whose form without it is also a known word ("poteaux");
            # "garde-corps" stays singular.
            plural = phrase.endswith(("s", "x")) and phrase[:-1] in vocabulary
            labels = vocabulary.get(phrase) or (vocabulary.get(phrase[:-1]) if plural else None)
            if labels:
                return set(labels), words[:start] + words[start + size:], plural
    return None


def _quality(reading: dict[str, Any]) -> dict[str, Any] | None:
    q = reading.get("quality")
    if not isinstance(q, dict):
        return None
    return {"niveau": q.get("niveau"), **({"discipline": q["discipline"]} if q.get("discipline") else {}),
            "réexport_conseillé": q.get("réexport_conseillé"),
            "conseils_export": list(q.get("conseils_export") or [])[:5],
            "déclaré_constaté": list(reading.get("declared_vs_observed") or [])[:3]}


# Short labels for the summary; the full export advice is in focus "qualité".
ADVICE_LABELS = (("coordonnées partagées", "coordonnées partagées"), ("nord", "nord géographique"),
                 ("phase", "phases"), ("Marque", "repères des portes et fenêtres"),
                 ("limites d'espace", "limites d'espace"), ("IFC4", "IFC4"), ("locaux", "noms des locaux"),
                 ("fonction", "fonction des murs"), ("porteur", "murs porteurs"), ("IfcExportAs", "classes IFC"))


def _advice_label(advice: str) -> str:
    return next((label for word, label in ADVICE_LABELS if word in advice), advice[:50])


def _quality_short(reading: dict[str, Any]) -> dict[str, Any] | None:
    """The quality of a model in a few words, for the summary."""
    q = reading.get("quality")
    if not isinstance(q, dict):
        return None
    short = {"niveau": q.get("niveau"), **({"discipline": q["discipline"]} if q.get("discipline") else {})}
    if q.get("réexport_conseillé"):
        short["réexport_conseillé"] = True
    labels = list(dict.fromkeys(_advice_label(str(a)) for a in q.get("conseils_export") or []))
    if labels:
        short["à_corriger"] = labels
    return short


def _overlay(reading: dict[str, Any], keys=("verdict", "score", "margin", "reference", "reference_index", "status")):
    return {k: reading["alignment"].get(k) for k in keys} if isinstance(reading.get("alignment"), dict) else None


def _quality_focus(models: list[dict[str, Any]]) -> dict[str, Any]:
    """Every model's quality in full: checks, export advice to cite, declared against observed, overlay."""
    rows = []
    for reading in models:
        quality = _quality(reading)
        if quality is None:
            continue
        row = {"maquette": reading["source"].get("piece"), "index": reading["source"].get("index"), **quality}
        if _overlay(reading):
            row["recalage"] = _overlay(reading)
        rows.append(row)
    return {"found": bool(rows), "kind": "qualité", "maquettes": rows}


FACADE_NAMES = {"nord", "est", "sud", "ouest"}
SELECTION_ROWS = 30  # beyond this, a selection gives counts by level and room with an extract
SEVERAL_MODELS_ROWS = 12  # per model, when one answer spans several models
# Words people use for the same room (a model names it "Séjour", the question says "salon").
ROOM_SYNONYMS = [
    {"sejour", "salon", "living", "piece de vie", "piece a vivre"},
    {"sdb", "salle de bain", "salle de bains", "salle d eau", "sde"},
    {"wc", "toilettes", "toilette", "sanitaires"},
    {"l tech", "local technique", "chaufferie", "technique"},
    {"sam", "salle a manger"},
    {"palier", "degagement", "circulation", "couloir"},
    {"entree", "hall", "sas"},
]
NOT_FOUND_ADVICE = ("Réessayer avec un nom de la liste, précédé d'une catégorie pour des éléments "
                    "(« poteaux Séjour », « poteaux du BET Séjour ») ; ne pas chercher ailleurs avant.")


def _fr(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


def _plain(text: Any) -> str:
    return " ".join(re.sub(r"[^\w ]", " ", _fold(text)).split())


ROOM_STOPWORDS = {"de", "du", "des", "la", "le", "les", "a", "au", "aux", "d"}


def _room_key(text: Any) -> str:
    """Canonical room phrase, matching the grammatical-word removal in designations."""
    return " ".join(word for word in _plain(text).split() if word not in ROOM_STOPWORDS)


def _room_match(query: str, name: Any) -> bool:
    """A room named by the query, directly or through a usual synonym ("salon" for "Séjour")."""
    query, plain = _room_key(query), _room_key(name)
    if not query:
        return False
    if query in plain:
        return True
    groups = [{_room_key(word) for word in group} for group in ROOM_SYNONYMS]
    return any(query in group and any(word == plain or plain.startswith(word + " ") for word in group)
               for group in groups)


def _selected(criterion: str, rows: list[dict[str, Any]], limit: int = SELECTION_ROWS) -> dict[str, Any]:
    """A selection small enough to read: every row when few, otherwise counts and an extract."""
    answer: dict[str, Any] = {"found": True, "kind": "sélection", "critère": criterion, "nombre": len(rows)}
    if len(rows) <= limit:
        return {**answer, "éléments": rows}
    by_level: dict[str, int] = {}
    by_room: dict[str, int] = {}
    by_position: dict[str, int] = {}
    sizes: dict[str, list[float]] = {}
    for row in rows:
        by_level[str(row.get("niveau") or "?")] = by_level.get(str(row.get("niveau") or "?"), 0) + 1
        for room in row.get("locaux") or ["hors local"]:
            by_room[room] = by_room.get(room, 0) + 1
        position = str(row.get("files") or row.get("façade") or "sans repère")
        by_position[position] = by_position.get(position, 0) + 1
        for key in ("largeur_m", "longueur_m", "hauteur_m", "épaisseur_m"):
            if isinstance(row.get(key), (int, float)):
                sizes.setdefault(key, []).append(row[key])
    # Distributions over every row: the extract is a sample and must not be generalised from.
    return {**answer, "par_niveau": by_level, "par_local": dict(sorted(by_room.items(), key=lambda kv: -kv[1])[:15]),
            "par_position": dict(sorted(by_position.items(), key=lambda kv: -kv[1])[:10]),
            **({"dimensions_m": {k: [round(min(v), 2), round(max(v), 2)] for k, v in sizes.items()}} if sizes else {}),
            "extrait": [{k: v for k, v in row.items() if k != "id"} for row in rows[:8]], "reste": len(rows) - 8,
            "note": "Liste longue : par_niveau, par_local, par_position et dimensions_m (min, max) portent sur tous "
                    "les éléments ; l'extrait n'en montre que 8, n'en tirer aucune répartition. Préciser une file, "
                    "une façade, un niveau ou un local pour le détail."}
# Element words of a designation: kind of element, and whether it is exterior (None: either).
ELEMENT_WORDS = {
    "cloison": ("mur", False), "cloisons": ("mur", False), "mur": ("mur", None), "murs": ("mur", None),
    "fenetre": ("fenêtre", None), "fenetres": ("fenêtre", None), "porte": ("porte", None), "portes": ("porte", None),
    "baie": ("baie", None), "baies": ("baie", None),
}
# A word of the user names every deduced nature it covers: a "porte" may be modelled in a window family.
KIND_NATURES = {
    "fenêtre": {"fenêtre", "fenêtre toute hauteur", "porte-fenêtre", "châssis intérieur"},
    "porte": {"porte", "porte extérieure", "porte intérieure", "porte-fenêtre"},
    "baie": {"baie libre", "porte-fenêtre"},
    "mur": {"mur", "mur extérieur", "mur intérieur", "cloison"},
}
LABELS = {("mur", False): "la cloison", ("mur", True): "le mur extérieur", ("mur", None): "le mur",
          ("fenêtre", None): "la fenêtre", ("porte", None): "la porte", ("baie", None): "la baie"}


def _designation(reading: dict[str, Any], words: list[str], names: dict[str, str],
                 elements: list[dict[str, Any]], row) -> dict[str, Any] | None:
    """'cloison file 5', 'fenêtre façade sud chambre 1': one element, or the candidates and the question to ask."""
    named = _category_phrase(reading, words)
    if named is not None:
        labels, rest, plural = named
        kind, exterior = None, None
    else:
        kind_word = next((w for w in words if w in ELEMENT_WORDS), None)
        if kind_word is None:
            return None
        kind, exterior = ELEMENT_WORDS[kind_word]
        labels = KIND_NATURES.get(kind, {kind})
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
    # « cloison entre la chambre 3 et la SDB »: two rooms named, the element between them.
    rooms_known = {n for n in names.values() if n}
    pair = None
    if room and not any(_room_match(room, n) for n in rooms_known):
        split_words = room.split()
        for cut in range(1, len(split_words)):
            left, right = " ".join(split_words[:cut]), " ".join(split_words[cut:])
            if any(_room_match(left, n) for n in rooms_known) and any(_room_match(right, n) for n in rooms_known):
                pair = (left, right)
                break

    def in_rooms(e: dict[str, Any]) -> bool:
        around = e.get("_rooms") or [names.get(s) for s in e.get("sides") or [] if s]
        if pair:
            return all(any(_room_match(part, n) for n in around) for part in pair)
        return not room or any(_room_match(room, n) for n in around)

    def matching(wanted_labels: set[str]) -> list[dict[str, Any]]:
        return [e for e in elements if (e["_what"] in wanted_labels or e["_what"] == kind)
                and (exterior is None or bool(e.get("exterior")) == exterior)
                and all(_on_grid(e.get("grid"), tag) for tag in tags)
                and (facade_dir is None or e.get("facade") == facade_dir)
                and (level is None or _fold(e.get("level")) == level)
                and in_rooms(e)]

    found, note = matching(labels), None
    # « Cloison » is said of any interior wall: without a partition there, the interior walls answer, said so.
    if not found and labels == {"cloison"}:
        found = matching({"cloison", "mur intérieur"})
        note = "aucune cloison à cet endroit : murs intérieurs donnés à la place" if found else None
    label = LABELS.get((kind, exterior if kind == "mur" else None))
    if not found:
        return {"found": False, "kind": "désignation", "reason": f"aucun élément ne correspond à « {' '.join(words)} »",
                "locaux": sorted(set(names.values()))[:MAX_LISTED], "conseil": NOT_FOUND_ADVICE}
    rows = [row(e) for e in found]
    if len(rows) == 1:
        return {"found": True, "kind": "élément", **rows[0], **({"note": note} if note else {})}
    if plural:
        return {**_selected(" ".join(words), rows), **({"note": note} if note else {})}

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
        name = label or item.get("élément") or "élément"
        return f"{name} {where}" + (f" ({', '.join(details)})" if details else "")

    plain = [describe(r) for r in rows]
    if len(set(plain)) < len(plain):
        plain = [describe(r, detailed=True) for r in rows]

    question = (("Parlez-vous de " + ", ou de ".join(plain) + " ?") if label else
                ("Plusieurs correspondent : " + " ; ".join(plain) + ". Lequel ?")) if len(rows) <= 4 else \
        f"{len(rows)} éléments correspondent : précisez la file, la façade, le niveau ou la pièce."
    return {"found": False, "kind": "désignation", "plusieurs": len(rows), "candidats": rows[:MAX_LISTED], "question": question}


def _on_grid(position: Any, tag: str) -> bool:
    """'sur la file M' or 'entre L et M' names the grid line tag."""
    text = f" {position or ''} ".replace(";", " ; ")
    return f" file {tag} " in text or f" et {tag} " in text or f"entre {tag} " in text


def _selection(reading: dict[str, Any], wanted: str, states: dict[str, str]) -> dict[str, Any] | None:
    """Elements on one grid line, on one façade, or spaces on one level: the reverse questions."""
    names = {s["id"]: s["name"] for s in reading.get("spaces") or []}
    elements = [{**o, "_what": _what(o)} for o in reading.get("openings") or []] + \
               [{**w, "_what": w.get("label") or "mur"} for w in reading.get("walls") or []] + \
               [_with_overlay(e) for e in reading.get("elements") or []]

    def row(item: dict[str, Any]) -> dict[str, Any]:
        sides = item.get("_rooms") or [names.get(s, "?") for s in item.get("sides") or [] if s]
        return {"élément": item["_what"], **({"largeur_m": item["width_m"]} if item.get("width_m") else {}),
                **({"hauteur_m": item["height_m"]} if item.get("height_m") else {}),
                **({"épaisseur_m": item["thickness_m"]} if item.get("thickness_m") else {}),
                **({"longueur_m": item["length_m"]} if item.get("length_m") else {}),
                "locaux": sides, **({"façade": item["facade"]} if item.get("facade") else {}),
                **({"files": item["grid"]} if item.get("grid") else {}), "niveau": item.get("level"),
                **({"à_vérifier": _to_check(item)} if _to_check(item) else {}),
                **({"confiance": "estimé"} if item.get("_overlaid") else {}), "id": item["id"]}

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
        return _selected(f"file {tag}", rows)
    if len(words) == 2 and words[0] == "facade" and words[1] in FACADE_NAMES:
        rows = [row(e) for e in elements if e.get("facade") == words[1]]
        return _selected(f"façade {words[1]}", rows)
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
    # "poteaux du BET séjour": only the engineers' models; "murs archi": only the architect's.
    words = wanted.split()
    for markers, discipline in (({"bet", "structure", "structurel", "structurelle", "beton"}, "structure"),
                                ({"archi", "architecte", "architecture"}, "architecture")):
        if markers & set(words):
            kept = [r for r in models if r.get("discipline") == discipline]
            if not kept:
                available = sorted({r.get("discipline") for r in models if r.get("discipline")})
                return {"found": False, "reason": f"aucune lecture publiée pour la discipline {discipline}",
                        "discipline_demandée": discipline, "disciplines_disponibles": available}
            models = kept
            words = [w for i, w in enumerate(words) if w not in markers
                     and not (w in {"du", "de", "la", "l"} and i + 1 < len(words) and words[i + 1] in markers)]
            wanted = " ".join(words)
    # The architect's model (with spaces) first; engineers' models complete it.
    models.sort(key=lambda r: -len(r.get("spaces") or []))
    missed, found = None, []
    for reading in models:
        selected = _selection(reading, wanted, states)
        if selected is None:
            continue
        selected = {**selected, "source": {"piece": reading["source"].get("piece"), "index": reading["source"].get("index"),
                                           **({"discipline": reading["discipline"]} if reading.get("discipline") else {})},
                    "limites": list(reading.get("limits") or [])}
        if reading.get("alignment"):
            align = reading["alignment"]
            selected["recalage"] = {k: align.get(k) for k in ("verdict", "score", "reference", "reference_index", "status")}
        if selected.get("found"):
            found.append(selected)
        else:
            missed = missed or selected
    if len(found) == 1 or (found and found[0].get("kind") != "sélection"):
        return found[0]
    if found:  # the same category in several models (an architect's posts, an engineer's columns): one answer per model
        for answer in found:
            rows = answer.get("éléments")
            if isinstance(rows, list) and len(rows) > SEVERAL_MODELS_ROWS:
                answer.pop("éléments")
                answer.update(_selected(answer.get("critère", ""), rows, limit=SEVERAL_MODELS_ROWS))
        return {"found": True, "kind": "sélections", "par_maquette": found,
                "nombre": sum(f.get("nombre") or 0 for f in found)}
    if missed is not None:
        return missed
    for reading in models:
        names = {s["id"]: s["name"] for s in reading.get("spaces") or []}
        spaces = reading.get("spaces") or []
        exact = [s for s in spaces if wanted in {_fold(s.get("name")), _fold(s.get("number"))}]
        partial = exact or [s for s in spaces if wanted and _room_match(wanted, s.get("name"))]
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
            openings = [{"élément": _what(o), "largeur_m": o.get("width_m"), "hauteur_m": o.get("height_m"),
                         **({"allège_m": o["sill_m"]} if o.get("sill_m") is not None else {}),
                         "donne": _side(o, sid, names), **({"files": o["grid"]} if o.get("grid") else {}),
                         **({"type_déclaré": o["type"]} if o.get("type") else {}),
                         **({"à_vérifier": _to_check(o)} if _to_check(o) else {}), "id": o["id"]}
                        for o in reading.get("openings") or [] if sid in (o.get("sides") or [])]
            # Exterior openings grouped by façade, ready to quote: a local model restating the list
            # once swapped two windows between façades.
            by_facade: dict[str, list[str]] = {}
            for o in openings:
                side = str(o.get("donne") or "")
                if "façade" in side:
                    size = " × ".join(_fr(v) for v in (o.get("largeur_m"), o.get("hauteur_m")) if isinstance(v, (int, float)))
                    by_facade.setdefault(side.split("façade", 1)[1].strip(), []).append(
                        f"{o['élément']}{' ' + size + ' m' if size else ''}")
            walls = [{"mur": _side(w, sid, names), "épaisseur_m": w.get("thickness_m"), "longueur_m": w.get("length_m"),
                      **({"composition": w["composition"]} if w.get("composition") else {}),
                      **({"files": w["grid"]} if w.get("grid") else {}), "jonctions": len(w.get("junctions") or []),
                      "id": w["id"]}
                     for w in reading.get("walls") or [] if sid in (w.get("sides") or [])]
            linked = sorted({names.get(x, "?") for n in reading.get("neighbours") or [] if sid in n["spaces"]
                             for x in n["spaces"] if x != sid and n["via"] == "porte"})
            free = sorted({names.get(x, "?") for n in reading.get("neighbours") or [] if sid in n["spaces"]
                           for x in n["spaces"] if x != sid and n["via"] == "baie libre"})
            open_onto = sorted({names.get(x, "?") for n in reading.get("neighbours") or [] if sid in n["spaces"]
                                for x in n["spaces"] if x != sid and n["via"] == "ouvert"})
            touching = sorted({names.get(x, "?") for n in reading.get("neighbours") or [] if sid in n["spaces"]
                               for x in n["spaces"] if x != sid and n["via"] == "mur"})
            inside = [e for e in reading.get("elements") or [] if e.get("space") == sid]
            contains: dict[str, int] = {}
            for element in inside:
                contains[element["label"]] = contains.get(element["label"], 0) + 1
            return {"found": True, "kind": "local", "name": space["name"], "level": space.get("level"),
                    **({"contient": contains} if contains else {}),
                    "surface_m2": space.get("area_m2"), "état": states.get(sid, UNSTATED),
                    "relié_par_porte_à": linked, **({"relié_par_baie_libre_à": free} if free else {}),
                    **({"ouvert_sur": open_onto} if open_onto else {}), "mur_commun_avec": touching,
                    "ouvertures": openings, **({"ouvertures_par_façade": by_facade} if by_facade else {}),
                    "murs": walls, "source": source, "limites": notes,
                    **({"qualité_maquette": _quality(reading)["niveau"]} if _quality(reading) else {})}
        if element:
            return {"found": True, "kind": "élément", "élément": element.get("kind", "mur"),
                    **{k: v for k, v in element.items() if k not in {"sides", "kind"}},
                    "côtés": [names.get(s, "extérieur") if s else "extérieur" for s in element.get("sides") or []],
                    "source": source, "limites": notes}
    return {"found": False, "candidates": [f"{s['name']} {s.get('level') or ''} (n° {s.get('number') or '?'})".strip()
                                           for r in models for s in r.get("spaces") or []][:MAX_LISTED],
            "reason": "aucun local ni élément ne correspond", "conseil": NOT_FOUND_ADVICE}


DETAIL_HINT = ("Détail sur demande avec focus : « changements <maquette> » (ce qui a changé depuis l'indice précédent), « qualité » (contrôles et conseils d'export de chaque maquette), "
               "« sources » (sources anatomiques et leurs états), "
               "« fichier <partie du nom> » (fiche d'une source), « pièces » (toutes les pièces courantes et leurs fichiers), "
               "« devis », « locaux », un local (« cuisine », « chambre 101 »), « file M », « façade sud », "
               "un niveau (« R01 »), ou des éléments (« cloison file 5 », « fenêtre façade sud chambre 1 », « poteaux du BET séjour »).")


SOURCE_KEYS = ("fichier", "état", "rôle", "discipline", "usage", "perimeter", "remplace", "remplacée_par", "déplacé_depuis", "messages")


def _sources(section: dict[str, Any]) -> dict[str, Any]:
    """The anatomy sources, one short line each: which files the readings rest on, and in what state."""
    out: dict[str, Any] = {"mode": section.get("mode")}
    lines = []
    for line in (section.get("liste") or [])[:SELECTION_ROWS]:
        if not isinstance(line, dict):
            continue
        short = {k: line[k] for k in SOURCE_KEYS if line.get(k)}
        reading = line.get("lecture") or {}
        if reading.get("indice"):
            short["indice"] = reading["indice"]
        calage = line.get("calage") or {}
        if calage.get("verdict"):
            short["calage"] = f"{calage['verdict']}, " + ("confirmé" if calage.get("confirmé") else "non confirmé")
        elif calage.get("déclaré"):
            short["calage"] = f"déclaré : {calage['déclaré']}"
        lines.append(short)
    if lines:
        out["liste"] = lines
    if section.get("en_attente"):
        out["en_attente"] = section["en_attente"]
    if section.get("dernière_consolidation"):
        out["dernière_consolidation"] = section["dernière_consolidation"]
    return out


def _changes(directory: Path, changes: list[dict[str, Any]], wanted: str) -> dict[str, Any]:
    """What changed since the previous index of one model (or of every model), from the published comparison."""
    chosen = [c for c in changes if not wanted or wanted in _fold(c.get("pièce"))]
    if not chosen:
        return {"found": False, "kind": "changements",
                "message": "aucune comparaison publiée" if not changes else "aucune maquette ne correspond",
                "maquettes": [c.get("pièce") for c in changes]}
    if len(chosen) > 1 and wanted:
        return {"found": False, "kind": "changements", "question": "Plusieurs maquettes correspondent : laquelle ?",
                "candidats": [c.get("pièce") for c in chosen]}
    answers = []
    for change in chosen:
        name = change.get("fichier")
        detail = None
        if isinstance(name, str) and CHANGES_FILE.fullmatch(name):
            try:
                with (directory / name).open("rb") as file:
                    raw = file.read(MAX_MODEL_BYTES + 1)
                detail = json.loads(raw) if len(raw) <= MAX_MODEL_BYTES else None
            except (OSError, ValueError):
                detail = None
        if isinstance(detail, dict):
            # Rooms and openings in full; walls and elements as short lists and counts (a local model reads it whole).
            for section in ("murs", "éléments"):
                if isinstance(detail.get(section), dict):
                    part = detail[section]
                    detail[section] = {**{k: part[k][:8] for k in ("ajoutés", "supprimés") if part.get(k)},
                                       **({"modifiés": len(part["modifiés"])} if part.get("modifiés") else {})}
            for section in ("locaux", "ouvertures"):
                for row in (detail.get(section) or {}).get("modifiés") or []:
                    row.pop("id", None)
        answers.append(detail if isinstance(detail, dict) else {k: change.get(k) for k in ("pièce", "de", "à", "résumé")})
    return {"found": True, "kind": "changements", "comparaisons": answers}


def _file_sheet(section: dict[str, Any], wanted: str) -> dict[str, Any]:
    """The sheet of one declared source file, found by a part of its path or of its piece name."""
    lines = [line for line in section.get("liste") or [] if isinstance(line, dict)]
    found = [line for line in lines
             if wanted and (wanted in _fold(str(line.get("fichier", "")))
                            or wanted in _fold(str((line.get("lecture") or {}).get("pièce", ""))))]
    if not found:
        return {"found": False, "kind": "fiche fichier",
                "message": "aucune source anatomique déclarée ne correspond" if lines else "aucune source anatomique déclarée",
                "fichiers": [line.get("fichier") for line in lines][:SELECTION_ROWS]}
    if len(found) > 1:
        return {"found": False, "kind": "fiche fichier", "question": "Plusieurs fichiers correspondent : lequel ?",
                "candidats": [{k: line.get(k) for k in ("fichier", "état") if line.get(k)} for line in found][:SELECTION_ROWS]}
    return {"found": True, "kind": "fiche fichier", "fiche": found[0]}


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
    models_read = sorted(_load_models(directory, data), key=lambda r: -len(r.get("spaces") or []))
    counted: dict[str, dict[str, int]] = {}
    for reading in models_read:
        counts: dict[str, int] = {}
        for element in reading.get("elements") or []:
            counts[element["label"]] = counts.get(element["label"], 0) + 1
        if counts:
            counted[f"{reading['source'].get('piece')} {reading['source'].get('index') or ''}".strip()] = counts
    if counted:
        compact["model_elements"] = counted
    if models_read and _quality_short(models_read[0]):
        main = models_read[0]
        compact["model_quality"] = {"maquette": main["source"].get("piece"), "index": main["source"].get("index"),
                                    **_quality_short(main),
                                    "déclaré_constaté": list(main.get("declared_vs_observed") or [])[:2],
                                    "détail": "focus « qualité » : conseils d'export complets à citer"}
        others = [{"maquette": r["source"].get("piece"), "index": r["source"].get("index"), **_quality_short(r),
                   **({"recalage": _overlay(r, ("verdict", "score", "status"))} if _overlay(r) else {})}
                  for r in models_read[1:] if _quality_short(r)]
        if others:
            compact["model_quality"]["autres_maquettes"] = others
    if full.get("anatomy_sources"):
        compact["anatomy_sources"] = full["anatomy_sources"]
    if full.get("model_changes"):
        compact["model_changes"] = full["model_changes"]
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
            # Each model with its discipline and file: an engineer's model is never taken for the architect's.
            known = {r["source"].get("piece"): r for r in _load_models(directory, data)}
            full["models"] = [{**{k: m.get(k) for k in ("piece", "index") if m.get(k)},
                               **({"discipline": known[m.get("piece")].get("discipline")}
                                  if known.get(m.get("piece"), {}).get("discipline") else {}),
                               **({"fichier": known[m.get("piece")]["source"].get("file")}
                                  if known.get(m.get("piece"), {}).get("source", {}).get("file") else {})}
                              for m in data["models"] if isinstance(m, dict)]
        changes = [c for c in data.get("model_changes") or [] if isinstance(c, dict)]
        if changes:
            disciplines = {m.get("piece"): m.get("discipline") for m in full.get("models") or []}
            full["model_changes"] = [{k: c.get(k) for k in ("pièce", "de", "à", "résumé") if c.get(k)}
                                     | ({"discipline": disciplines[c.get("pièce")]} if disciplines.get(c.get("pièce")) else {})
                                     | ({"fiable": False} if c.get("fiable") is False else {}) for c in changes]
        sources = data.get("anatomy_sources")
        if isinstance(sources, dict):
            full["anatomy_sources"] = _sources(sources)
        wanted = _fold(focus)
        if not wanted:
            return _compact(full, directory, data)
        if wanted in {"sources", "source", "sources anatomiques"}:
            overview = {key: full[key] for key in ("code", "found", "source", "project") if key in full}
            return {**overview, "anatomy_sources": full.get("anatomy_sources") or {"mode": "non publié"}}
        if wanted in {"qualite", "qualité", "qualite maquette", "qualité maquette", "qualite des maquettes"}:
            overview = {key: full[key] for key in ("code", "found", "source", "project") if key in full}
            return {**overview, "focus": _quality_focus(sorted(_load_models(directory, data),
                                                                key=lambda r: -len(r.get("spaces") or [])))}
        if wanted.split()[0] in {"changements", "changement", "modifications", "evolutions"}:
            overview = {key: full[key] for key in ("code", "found", "source", "project") if key in full}
            return {**overview, "focus": _changes(directory, changes, wanted.partition(" ")[2])}
        if wanted.startswith("fichier ") or wanted.startswith("fiche "):
            overview = {key: full[key] for key in ("code", "found", "source", "project") if key in full}
            return {**overview, "focus": _file_sheet(sources if isinstance(sources, dict) else {}, wanted.partition(" ")[2])}
        # With a focus, only a short header travels with the detail asked for.
        overview = {key: full[key] for key in ("code", "found", "source", "project", "anatomy_status", "open_questions")
                    if key in full}
        first, _, rest = wanted.partition(" ")
        if first in {"pieces", "documents", "plans"}:
            listed = (full.get("pieces") or {}).get("current", [])
            if rest:  # "pièces dce", "pièces cctp": name or folder contains the word
                listed = [row for row in listed if rest in _fold(row.get("piece")) or rest in _fold(row.get("file"))]
            overview["focus"] = {"found": True, "kind": "pièces", "filtre": rest or None, "nombre": len(listed),
                                 "pièces": listed[:SELECTION_ROWS],
                                 **({"reste": len(listed) - SELECTION_ROWS,
                                     "conseil": "liste longue : filtrer par un mot du nom ou du dossier (« pièces dce », « pièces cctp »)"}
                                    if len(listed) > SELECTION_ROWS else {})}
        elif wanted in {"devis", "offres"}:
            overview["focus"] = {"found": True, "kind": "devis", "devis": (full.get("pieces") or {}).get("to_confront", [])}
        elif wanted in {"locaux", "surfaces", "anatomie"}:
            overview["focus"] = {"found": True, "kind": "locaux", "levels": full.get("levels", []),
                                 "surfaces_by_state_m2": full.get("surfaces_by_state_m2"),
                                 "spaces_counted_in_totals": full.get("spaces_counted_in_totals")}
        elif wanted:
            overview["focus"] = _focus(directory, data, str(focus))
            if overview["focus"].get("kind") in {"sélection", "sélections", "élément", "local", "désignation"}:
                # Its own key: a single element answered at the top level keeps its own "confiance".
                overview["focus"]["légende_confiance"] = MODEL_CONFIDENCE
        return overview
    except (ValueError, TypeError, KeyError, AttributeError):
        return {**result, "error": "anatomy_unreadable"}
