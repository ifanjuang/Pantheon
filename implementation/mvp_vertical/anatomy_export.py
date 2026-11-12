"""Publish each Project's Anatomy projection as one file a read-only screen can display.

The owner publishes, the screen displays. After a successful APU write, the
owner rewrites ``<MVP_ANATOMY_EXPORT_DIR>/<CODE>.json`` with the projection it
already computes (``get_project_anatomy_projection``), so the Workspace Cockpit
can show it on the back of the matching affaire card without reading the
database, holding a key or knowing the APU tables.

The file is a projection, never a source: nothing reads it back into the APU,
and ``export-anatomy`` regenerates it at any time. Without
``MVP_ANATOMY_EXPORT_DIR`` nothing is written.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
from typing import Any

from . import anatomy_sources, apu_owner, apu_vocabulary, model_alignment, model_diff, model_reading, project_pieces
from .project_anatomy_projection import get_project_anatomy_projection

SCHEMA = "pantheon.anatomy.v1"
EXPORT_DIR_ENV = "MVP_ANATOMY_EXPORT_DIR"
_CODE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


# Published in place of the projection while a Project has no installed Anatomy.
EMPTY_ANATOMY: dict[str, Any] = {
    "status": "not_installed", "owner_revision": None, "summary": {}, "structure": {"objects": []},
    "attribute_claims": [], "relation_claims": [], "relations": [], "sources": [], "phases": {"status": "no_anatomy"},
}


class AnatomyExportError(ValueError):
    pass


def export_dir() -> Path | None:
    configured = os.environ.get(EXPORT_DIR_ENV, "").strip()
    if not configured:
        return None
    path = Path(configured)
    if not path.is_absolute():
        raise AnatomyExportError(f"{EXPORT_DIR_ENV} must be absolute")
    return path


def property_labels(anatomy: dict[str, Any]) -> dict[str, Any]:
    """Label, unit and facet of each property the Anatomy uses, from the property profile.

    Screens and Hermes show French labels and units without reading the registry.
    Undeclared keys are listed, never refused. Without a readable profile the
    section says so and the Anatomy is published anyway.
    """
    keys = sorted({claim.get("attribute_key") for claim in anatomy.get("attribute_claims") or []
                   if isinstance(claim, dict) and isinstance(claim.get("attribute_key"), str)})
    try:
        labels = {key: {field: entry[field] for field in ("label", "unit", "facet") if entry.get(field)}
                  for key in keys if (entry := apu_vocabulary.describe_property(key))}
    except apu_vocabulary.VocabularyUnavailable:
        return {"error": "property_profile_unavailable", "keys": keys}
    return {"labels": labels, "undeclared": [key for key in keys if key not in labels]}


def export_project_anatomy(conn, project_id: str, *, directory: Path | None = None,
                           consolidate: bool = False) -> Path | None:
    """Write the Project's projection atomically; None when no export directory is configured.

    ``consolidate`` brings every declared anatomy source in now; otherwise only the
    sources whose card asks for an immediate consolidation are, the others wait.
    """
    directory = directory or export_dir()
    if directory is None:
        return None
    row = conn.execute(
        "SELECT project_id, code, display_name, description, phase FROM agency_projects WHERE project_id = %s",
        (project_id,),
    ).fetchone()
    if row is None:
        raise AnatomyExportError(f"unknown Project: {project_id}")
    code = str(row[1] or "").strip()
    if not _CODE.fullmatch(code):
        raise AnatomyExportError(f"Project code cannot name an export file: {code!r}")
    try:
        anatomy = get_project_anatomy_projection(conn, project_id=project_id)
    except apu_owner.ApuOwnerNotFound:
        # An affaire is published before its Anatomy exists: its pieces and model
        # reading are useful from the first document on.
        anatomy = dict(EMPTY_ANATOMY)
    document: dict[str, Any] = {
        "schema": SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": {"project_id": row[0], "code": code, "display_name": row[2],
                    **({"description": row[3]} if row[3] else {}), **({"phase": row[4]} if row[4] else {})},
        "anatomy": anatomy,
        "properties": property_labels(anatomy),
    }
    # The current state of the affaire's documents travels with its Anatomy, so a
    # screen or Hermes reads one file. A reading failure never blocks the Anatomy.
    try:
        pieces = project_pieces.read_project_pieces(code)
    except (OSError, sqlite3.Error) as exc:
        pieces = {"error": f"pieces_unreadable: {type(exc).__name__}"}
    if pieces is not None:
        declared = pieces.pop("declared_sources", None) if isinstance(pieces, dict) else None
        document["pieces"] = pieces
        previous = previous_models(code, pieces, directory)
        keep = frozenset(entry[1].name for entry in previous.values())
        if declared:
            models, document["anatomy_sources"] = read_declared_sources(code, pieces, declared, directory,
                                                                        consolidate=consolidate, keep_extra=keep)
        else:
            models = read_current_models(code, pieces, directory, keep_extra=keep)
            document["anatomy_sources"] = {"mode": "toutes les maquettes courantes (aucune source déclarée)"}
        if models:
            # The source path is internal comparison metadata, not part of the public projection.
            document["models"] = [{key: value for key, value in status.items() if not key.startswith("_")}
                                  for status in models]
            dates = {str(p.get("piece")): (p.get("current") or {}).get("date") for p in pieces.get("pieces") or []}
            paths = {str(p.get("piece")): (p.get("current") or {}).get("paths") or [] for p in pieces.get("pieces") or []}
            changes, questions = compare_models(code, models, previous, directory, dates=dates, paths=paths)
            if changes:
                document["model_changes"] = changes
            if questions and isinstance(pieces.get("questions"), list):
                pieces["questions"].extend(questions)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{code}.json"
    partial = directory / f".{code}.json.partial"
    partial.write_text(json.dumps(document, ensure_ascii=False, default=str), encoding="utf-8")
    partial.replace(target)
    return target


def read_current_models(code: str, pieces: dict[str, Any], directory: Path,
                        keep_extra: frozenset[str] = frozenset()) -> list[dict[str, Any]]:
    """Read the current index of each model piece next to the projection; cached by file fingerprint."""
    root = project_pieces._env_path(project_pieces.AFFAIRES_ROOT_ENV)
    if root is None:
        return []
    statuses = []
    for piece in pieces.get("pieces") or []:
        current = piece.get("current") or {}
        path = next((p for p in current.get("paths") or [] if p.lower().endswith(".ifc")), None)
        if not path or piece.get("category") != "projet":
            continue
        statuses.append(model_reading.ensure(root / code / path, sheet_file(directory, code, str(piece["piece"]), root / code / path),
                                             piece=str(piece["piece"]), index=current.get("index")))
    align_structural_models(directory, statuses)
    prune_sheets(directory, code, {s["file"] for s in statuses if s.get("file")} | keep_extra)
    return statuses


def previous_models(code: str, pieces: dict[str, Any], directory: Path) -> dict[str, tuple[Path, Path, str | None]]:
    """For each model piece, its previous index's file and the sheet it is (or will be) read into."""
    root = project_pieces._env_path(project_pieces.AFFAIRES_ROOT_ENV)
    if root is None:
        return {}
    previous = {}
    for piece in pieces.get("pieces") or []:
        path = next((p for p in (piece.get("previous") or {}).get("paths") or [] if p.lower().endswith(".ifc")), None)
        if path and piece.get("category") == "projet":
            previous[str(piece["piece"])] = (root / code / path, sheet_file(directory, code, str(piece["piece"]), root / code / path),
                                             (piece.get("previous") or {}).get("index"))
    return previous


def compare_models(code: str, models: list[dict[str, Any]], previous: dict[str, tuple[Path, Path, str | None]],
                   directory: Path, *, dates: dict[str, str] | None = None,
                   paths: dict[str, list[str]] | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """What changed since each model's previous index, and current models that are one model under two names.

    The previous index is read once into its own sheet; each comparison is kept
    per pair of fingerprints and recomputed only when either file changes.
    """
    readings: dict[str, dict[str, Any]] = {}
    for status in models:
        try:
            readings[status["piece"]] = json.loads((directory / status["file"]).read_text(encoding="utf-8"))
        except (KeyError, OSError, ValueError):
            continue
    changes, kept = [], set()
    for piece, reading in readings.items():
        if piece not in previous:
            continue
        old_path, old_sheet, old_index = previous[piece]
        model_reading.ensure(old_path, old_sheet, piece=piece, index=old_index)
        try:
            old = json.loads(old_sheet.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        pair = f"{(old.get('source') or {}).get('fingerprint')}|{(reading.get('source') or {}).get('fingerprint')}"
        target = directory / f"{code}.changements-{_slug(piece)[:26].strip('-') or 'maquette'}-" \
                             f"{hashlib.sha1(pair.encode('utf-8')).hexdigest()[:12]}.json"
        try:
            diff = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            diff = model_diff.compare(old, reading)
            _write_json(target, diff)
        kept.add(target.name)
        changes.append({"pièce": piece, "de": diff["de"].get("index"), "à": diff["à"].get("index"),
                        "fiable": diff.get("fiable"), "résumé": diff.get("résumé") or diff.get("raison"),
                        "fichier": target.name})
    for stale in directory.glob(f"{code}.changements-*.json"):
        if stale.name not in kept:
            stale.unlink(missing_ok=True)
    question_paths = {piece: list(file_paths) for piece, file_paths in (paths or {}).items()}
    for status in models:
        piece, workspace_path = status.get("piece"), status.get("_workspace_path")
        if piece and workspace_path:
            known = question_paths.setdefault(str(piece), [])
            if workspace_path not in known:
                known.append(workspace_path)
    return changes, model_diff.same_model_questions(list(readings.values()), dates, question_paths)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", project_pieces._fold(text)).strip("-")[:40] or "maquette"


SNAPSHOTS_KEPT = 20


def sheet_file(directory: Path, code: str, piece: str, path: Path) -> Path:
    """The file sheet of one model file, named by its fingerprint: an unchanged file is never read twice.

    Deactivating and reactivating a source, or coming back to an earlier index,
    finds its sheet again; a changed file gets a new sheet.
    """
    try:
        stamp = model_reading.fingerprint(path)
    except OSError:
        stamp = "absent"
    digest = hashlib.sha1(stamp.encode("utf-8")).hexdigest()[:12]
    return directory / f"{code}.maquette-{_slug(piece)[:26].strip('-') or 'maquette'}-{digest}.json"


def prune_sheets(directory: Path, code: str, keep: set[str]) -> None:
    """Remove the affaire's model sheets nothing refers to any more (derived files, regenerable)."""
    for sheet in directory.glob(f"{code}.maquette-*.json"):
        if sheet.name not in keep:
            sheet.unlink(missing_ok=True)


def _snapshots(directory: Path, code: str) -> list[dict[str, Any]]:
    try:
        data = json.loads((directory / f"{code}.consolidations.json").read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def _write_json(target: Path, data: Any) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(f".{target.name}.partial")
    partial.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    partial.replace(target)


def read_declared_sources(code: str, pieces: dict[str, Any], declared: dict[str, dict[str, Any]], directory: Path,
                          *, consolidate: bool = False,
                          keep_extra: frozenset[str] = frozenset()) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read the declared anatomy sources, decide their states, return the model statuses and the published section.

    A declared source is read once consolidated: on ``consolidate``, or when its
    card asks for it. The record of what was consolidated (file fingerprint and
    declaration) lives beside the projection, owned by the agency; a changed file
    or declaration waits for the next consolidation.
    """
    root = project_pieces._env_path(project_pieces.AFFAIRES_ROOT_ENV)
    record_file = directory / f"{code}.sources.json"
    try:
        record = json.loads(record_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        record = {}
    for path, entry in declared.items():  # a moved file keeps what was consolidated
        if entry.get("moved_from") in record and path not in record:
            record[path] = record.pop(entry["moved_from"])
    current = {}
    for piece in pieces.get("pieces") or []:
        for path in (piece.get("current") or {}).get("paths") or []:
            current[path] = piece
    now = datetime.now(timezone.utc).isoformat()
    consolidated_now = False
    results: dict[str, dict[str, Any]] = {}
    statuses: dict[str, dict[str, Any]] = {}
    for path, entry in sorted(declared.items()):
        result: dict[str, Any] = {"declared": entry, "messages": []}
        results[path] = result
        if not entry["active"]:
            result["état"] = anatomy_sources.DISABLED
            continue
        try:
            stamp = model_reading.fingerprint(root / code / path) if root else None
        except OSError:
            stamp = None
        previous = record.get(path) or {}
        fresh = previous.get("fingerprint") == stamp and previous.get("declaration") == anatomy_sources.declaration_stamp(entry)
        if stamp is not None and (consolidate or entry["consolidate_now"]) and not fresh:
            record[path] = {"fingerprint": stamp, "declaration": anatomy_sources.declaration_stamp(entry), "consolidated_at": now}
            fresh = consolidated_now = True
        if stamp is None:
            result["état"], result["messages"] = anatomy_sources.ERROR, ["fichier introuvable"]
            continue
        if not fresh:
            result["état"] = anatomy_sources.PENDING
            result["messages"] = ["consolidation à lancer" if path not in record else "fichier ou déclaration modifiés : consolidation à relancer"]
            continue
        result["consolidée_le"] = record[path]["consolidated_at"]
        piece = current.get(path)
        if path.lower().endswith(".ifc"):
            name = str(piece["piece"]) if piece else Path(path).stem
            index = (piece.get("current") or {}).get("index") if piece else None
            status = model_reading.ensure(root / code / path, sheet_file(directory, code, name, root / code / path),
                                          piece=name, index=index)
            status["_workspace_path"] = path
            statuses[path] = status
            record[path]["sheet"] = statuses[path].get("file")
        else:
            result["état"], result["messages"] = anatomy_sources.document_state(
                piece, [q.get("text", "") for q in pieces.get("questions") or []])
            if piece:
                result["lecture"] = {"pièce": piece.get("piece"), **{k: v for k, v in (piece.get("current") or {}).items()
                                                                     if k in ("index", "date", "position") and v}}

    def judge() -> None:
        for path, status in statuses.items():
            try:
                reading = json.loads((directory / status["file"]).read_text(encoding="utf-8"))
            except (KeyError, OSError, ValueError):
                reading = None
            entry = results[path]["declared"]
            results[path]["état"], results[path]["messages"] = anatomy_sources.model_state(reading, status, entry)
            results[path]["état_propre"] = results[path]["état"]
            calage = anatomy_sources.alignment_line((reading or {}).get("alignment"), entry) if reading else None
            if calage:
                results[path]["calage"] = calage
            if reading:
                results[path]["lecture"] = {"pièce": status.get("piece"), "indice": status.get("index"),
                                            "discipline": reading.get("discipline"),
                                            "qualité": (reading.get("quality") or {}).get("niveau"),
                                            "éléments": len(reading.get("elements") or [])}
                by_label: dict[str, int] = {}
                for element in reading.get("elements") or []:
                    by_label[element.get("label") or "?"] = by_label.get(element.get("label") or "?", 0) + 1
                if by_label:
                    results[path]["lecture"]["par_catégorie"] = dict(sorted(by_label.items(), key=lambda kv: -kv[1])[:8])
        anatomy_sources.resolve_replacements(results)

    judge()  # replacements first, so an old architect's model is not the overlay reference
    kept = [s for p, s in statuses.items() if results[p]["état"] in anatomy_sources.USABLE]
    align_structural_models(directory, kept)
    judge()
    record = {p: r for p, r in record.items() if p in declared}
    _write_json(record_file, record)
    snapshots = _snapshots(directory, code)
    # What the state of the affaire rested on, at this consolidation. A requested consolidation is
    # always dated, even when every source was already up to date: the card then shows it done.
    if consolidated_now or consolidate:
        snapshots = (snapshots + [{"at": now, "sources": [
            {"fichier": p, "empreinte": (record.get(p) or {}).get("fingerprint"), "état": r["état"],
             **({"fiche": statuses[p].get("file")} if p in statuses and statuses[p].get("file") else {})}
            for p, r in results.items()]}])[-SNAPSHOTS_KEPT:]
        _write_json(directory / f"{code}.consolidations.json", snapshots)
    # Sheets stay while a source, inactive included, or a kept snapshot refers to them.
    prune_sheets(directory, code, {s["file"] for s in statuses.values() if s.get("file")}
                 | {r["sheet"] for r in record.values() if r.get("sheet")}
                 | {src["fiche"] for snap in snapshots for src in snap.get("sources") or [] if src.get("fiche")}
                 | keep_extra)

    models = [s for p, s in statuses.items() if results[p]["état"] in anatomy_sources.USABLE]
    section = {
        "mode": "déclarées",
        "liste": [anatomy_sources.summary_line(path, result) for path, result in results.items()],
        "en_attente": sum(1 for r in results.values() if r["état"] == anatomy_sources.PENDING),
        **({"dernière_consolidation": snapshots[-1]["at"]} if snapshots else {}),
        "règle": "seules les sources activées ou en avertissement sont lues ; une source en attente attend la "
                 "consolidation ; un remplacement n'a lieu que si la nouvelle source n'est pas en erreur.",
    }
    for line, result in zip(section["liste"], results.values()):
        for key in ("lecture", "consolidée_le"):
            if result.get(key):
                line[key] = result[key]
    return models, section


def align_structural_models(directory: Path, statuses: list[dict[str, Any]]) -> None:
    """Overlay each engineer's model on the architect's, once per pair of model files (part of the preparation)."""
    readings: dict[str, dict[str, Any]] = {}
    for status in statuses:
        try:
            readings[status["file"]] = json.loads((directory / status["file"]).read_text(encoding="utf-8"))
        except (KeyError, OSError, ValueError):
            continue
    architects = [(name, r) for name, r in readings.items() if r.get("discipline") == "architecture" and r.get("spaces")]
    if not architects:
        return
    reference_name, reference = max(architects, key=lambda item: len(item[1].get("spaces") or []))
    stamp = f"{reference.get('source', {}).get('fingerprint')}"
    for status in statuses:
        reading = readings.get(status.get("file"))
        if reading is None or reading.get("discipline") != "structure" or "geometry" not in reading:
            continue
        previous = reading.get("alignment") or {}
        if previous.get("reference_fingerprint") == stamp:
            status["recalage"] = previous.get("verdict")
            continue
        result = model_alignment.align(reference.get("geometry") or {}, reading["geometry"])
        result.update(reference=reference.get("source", {}).get("piece"), reference_index=reference.get("source", {}).get("index"),
                      reference_fingerprint=stamp)
        for element in reading.get("elements") or []:
            element.pop("via_recalage", None)
        if result.get("verdict") == "probable":
            result["placed"] = model_alignment.place(reading, reference, result)
        reading["alignment"] = result
        target = directory / status["file"]
        partial = target.with_name(f".{target.name}.partial")
        partial.write_text(json.dumps(reading, ensure_ascii=False), encoding="utf-8")
        partial.replace(target)
        status["recalage"] = result.get("verdict")


def consolidate_pending(conn, *, directory: Path | None = None) -> list[str]:
    """Consolidate the affaires whose Workspace asked for it since the last pass; returns their codes.

    Run by a timer on the agency side. The Workspace records the requests (the
    project card button, a changed ``anatomy_source``); the agency never writes
    them back: it keeps, beside the projections, the moment of the last request
    it has handled for each affaire. A card asking for an immediate consolidation
    is consolidated now; the others stay pending until the project card asks.
    """
    directory = directory or export_dir()
    db = project_pieces._env_path(project_pieces.WORKSPACE_DB_ENV)
    if directory is None or db is None or not db.is_file():
        return []
    handled_file = directory / "consolidation-requests.json"
    try:
        handled = json.loads(handled_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        handled = {}
    done = []
    for code, trigger in sorted(project_pieces.read_consolidation_triggers(db).items()):
        previous = handled.get(code) if isinstance(handled.get(code), dict) else {}
        asked = trigger.get("requested", "") > previous.get("requested", "")
        changed = trigger.get("changed", "") > previous.get("changed", "")
        if not (asked or changed):
            continue
        row = conn.execute("SELECT project_id FROM agency_projects WHERE code = %s", (code,)).fetchone()
        if row is None:
            continue
        # The project card button consolidates every declared source; a changed card
        # only brings in the sources whose card asks for it now.
        try:
            export_project_anatomy(conn, row[0], directory=directory, consolidate=asked)
        except AnatomyExportError:
            continue
        handled[code] = trigger
        done.append(code)
    if done:
        _write_json(handled_file, handled)
    return done


def export_all(conn, *, directory: Path | None = None) -> list[Path]:
    """Every Project with a code, whether or not its Anatomy is installed yet."""
    rows = conn.execute("SELECT project_id FROM agency_projects WHERE code IS NOT NULL ORDER BY project_id").fetchall()
    written = []
    for row in rows:
        try:
            written.append(export_project_anatomy(conn, row[0], directory=directory))
        except AnatomyExportError:
            continue  # a code that cannot name a file never blocks the other affaires
    return [path for path in written if path is not None]
