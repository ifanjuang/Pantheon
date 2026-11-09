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
    "Les questions sont des écarts relevés, à poser à l'architecte : ne pas les trancher.",
]
PIECE_KEYS = ("index", "date", "position")


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
        if state.get("paths"):
            row["file"] = f"{data['project'].get('code')}/{state['paths'][0]}"
        if item.get("variants"):
            row["variants"] = list(item["variants"])
        (to_confront if item.get("category") == "a_confronter" else current).append(row)
    return {
        "read_at": pieces.get("read_at"),
        "current": current[:MAX_LISTED],
        "to_confront": to_confront[:MAX_LISTED],
        "questions": [str(q.get("text")) for q in pieces.get("questions") or [] if isinstance(q, dict)][:MAX_LISTED],
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
    return {
        "found": True,
        "project": {key: data["project"].get(key) for key in ("code", "display_name")},
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


def project_overview(code: str, directory: Path | None = None) -> dict[str, Any]:
    directory = directory if directory is not None else anatomy_dir()
    code = str(code or "").strip()
    result: dict[str, Any] = {"code": code, "found": False, "source": f"projection publiée {SCHEMA}"}
    if directory is None:
        return {**result, "error": "anatomy_not_configured"}
    if not code:
        return {**result, "error": "code_required", "available_codes": _available_codes(directory)}
    if not _CODE.fullmatch(code):
        return {**result, "error": "invalid_code"}
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
        return {**result, **summarize(data)}
    except (ValueError, TypeError, KeyError, AttributeError):
        return {**result, "error": "anatomy_unreadable"}
