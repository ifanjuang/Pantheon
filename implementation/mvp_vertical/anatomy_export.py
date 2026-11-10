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
import json
import os
from pathlib import Path
import re
import sqlite3
from typing import Any

from . import apu_owner, apu_vocabulary, model_reading, project_pieces
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


def export_project_anatomy(conn, project_id: str, *, directory: Path | None = None) -> Path | None:
    """Write the Project's projection atomically; None when no export directory is configured."""
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
        document["pieces"] = pieces
        models = read_current_models(code, pieces, directory)
        if models:
            document["models"] = models
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{code}.json"
    partial = directory / f".{code}.json.partial"
    partial.write_text(json.dumps(document, ensure_ascii=False, default=str), encoding="utf-8")
    partial.replace(target)
    return target


def read_current_models(code: str, pieces: dict[str, Any], directory: Path) -> list[dict[str, Any]]:
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
        slug = re.sub(r"[^a-z0-9]+", "-", project_pieces._fold(str(piece["piece"]))).strip("-")[:40] or "maquette"
        statuses.append(model_reading.ensure(root / code / path, directory / f"{code}.maquette-{slug}.json",
                                             piece=str(piece["piece"]), index=current.get("index")))
    return statuses


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
