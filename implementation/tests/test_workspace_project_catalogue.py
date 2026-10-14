"""Tests for producer-owned Workspace project catalogue consumption."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3

import pytest

from mvp_vertical import workspace_project_catalogue as catalogue


def _write_catalogue(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "CREATE TABLE workspace_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO workspace_meta(key, value) VALUES ('project_catalogue', ?)",
            (json.dumps(payload),),
        )
        connection.commit()
    finally:
        connection.close()


def _payload(*projects: dict, truncated: bool = False) -> dict:
    return {
        "read_only": True,
        "bounded": True,
        "limit": 10_000,
        "truncated": truncated,
        "project_count": len(projects),
        "conflict_count": sum(
            1 for item in projects if item.get("routing_status") == "conflict"
        ),
        "projects": list(projects),
        "conflicts": [],
        "roots": [],
    }


def _active(name: str = "VERGER") -> dict:
    return {
        "name": name,
        "workspace": "Affaires",
        "state": "active",
        "root_kind": "AFFAIRES",
        "relative_root": name,
        "available": True,
        "write_requires_confirmation": False,
        "routing_status": "valid",
        "automatic_routing_allowed": True,
    }


def _archived(name: str = "ANCIEN") -> dict:
    return {
        "name": name,
        "workspace": "ArchivesProjet",
        "state": "archived",
        "root_kind": "ARCHIVES_PROJET",
        "relative_root": name,
        "available": True,
        "write_requires_confirmation": True,
        "routing_status": "valid",
        "automatic_routing_allowed": False,
    }


def test_load_and_resolve_active_project_without_scanning_siblings(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite3"
    _write_catalogue(db, _payload(_active()))
    affaires = tmp_path / "AFFAIRES"
    destination = affaires / "VERGER"
    destination.mkdir(parents=True)

    loaded = catalogue.load_project_catalogue(db)
    result = catalogue.resolve_project_destination(
        loaded,
        project_name="VERGER",
        root_paths={"AFFAIRES": affaires},
    )

    assert result["path"] == destination.resolve()
    assert result["state"] == "active"
    assert result["automatic_routing_allowed"] is True
    assert result["governed_project_identity_asserted"] is False


def test_archived_project_requires_explicit_confirmation(tmp_path: Path) -> None:
    archived_root = tmp_path / "project-platform" / "ARCHIVES" / "PROJET"
    destination = archived_root / "ANCIEN"
    destination.mkdir(parents=True)
    payload = _payload(_archived())

    with pytest.raises(
        catalogue.ArchivedProjectWriteRequiresConfirmation,
        match="explicit write confirmation",
    ):
        catalogue.resolve_project_destination(
            payload,
            project_name="ANCIEN",
            root_paths={"ARCHIVES_PROJET": archived_root},
        )

    confirmed = catalogue.resolve_project_destination(
        payload,
        project_name="ANCIEN",
        root_paths={"ARCHIVES_PROJET": archived_root},
        allow_archived_write=True,
    )
    assert confirmed["path"] == destination.resolve()
    assert confirmed["state"] == "archived"
    assert confirmed["write_requires_confirmation"] is True


def test_conflict_and_case_mismatch_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "AFFAIRES"
    (root / "VERGER").mkdir(parents=True)
    conflict = _active()
    conflict["routing_status"] = "conflict"
    conflict["automatic_routing_allowed"] = False

    with pytest.raises(catalogue.ProjectDestinationConflict):
        catalogue.resolve_project_destination(
            _payload(conflict),
            project_name="VERGER",
            root_paths={"AFFAIRES": root},
        )

    with pytest.raises(catalogue.ProjectDestinationNotFound):
        catalogue.resolve_project_destination(
            _payload(_active()),
            project_name="verger",
            root_paths={"AFFAIRES": root},
        )


def test_truncated_catalogue_is_not_usable_for_automatic_routing(tmp_path: Path) -> None:
    db = tmp_path / "index.sqlite3"
    _write_catalogue(db, _payload(_active(), truncated=True))

    with pytest.raises(
        catalogue.ProjectCatalogueUnavailable,
        match="truncated",
    ):
        catalogue.load_project_catalogue(db)


def test_relative_root_traversal_is_rejected_even_if_catalogue_is_malformed(
    tmp_path: Path,
) -> None:
    root = tmp_path / "AFFAIRES"
    root.mkdir()
    item = _active()
    item["relative_root"] = "../OTHER"

    with pytest.raises(
        catalogue.ProjectDestinationUnsafe,
        match="one child directory",
    ):
        catalogue.resolve_project_destination(
            _payload(item),
            project_name="VERGER",
            root_paths={"AFFAIRES": root},
        )


def test_missing_or_invalid_projection_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(catalogue.ProjectCatalogueUnavailable):
        catalogue.load_project_catalogue(tmp_path / "missing.sqlite3")

    db = tmp_path / "index.sqlite3"
    connection = sqlite3.connect(db)
    try:
        connection.execute(
            "CREATE TABLE workspace_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO workspace_meta(key, value) VALUES ('project_catalogue', 'not-json')"
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(catalogue.ProjectCatalogueUnavailable, match="invalid JSON"):
        catalogue.load_project_catalogue(db)
