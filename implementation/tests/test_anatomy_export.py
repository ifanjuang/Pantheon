"""The owner publishes one Anatomy projection file per Project; the file is never a source."""

from __future__ import annotations

import json

import pytest

from mvp_vertical import anatomy_export
from test_apu_progressive_claims import _import, _project, conn  # noqa: F401 - conn is a fixture


def _code(conn, project_id: str) -> str:
    return conn.execute("SELECT code FROM agency_projects WHERE project_id = %s", (project_id,)).fetchone()[0]


def test_export_writes_the_owner_projection_atomically(conn, tmp_path) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    path = anatomy_export.export_project_anatomy(conn, project_id, directory=tmp_path)
    assert path == tmp_path / f"{_code(conn, project_id)}.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["schema"] == anatomy_export.SCHEMA
    assert document["project"] == {"project_id": project_id, "code": _code(conn, project_id), "display_name": "Écriture APU progressive"}
    assert document["anatomy"]["summary"]["stable_object_count"] >= 1
    assert document["anatomy"]["authority"]
    assert not list(tmp_path.glob(".*.partial"))


def test_without_an_export_directory_nothing_is_written(conn, monkeypatch) -> None:
    monkeypatch.delenv(anatomy_export.EXPORT_DIR_ENV, raising=False)
    project_id = _project(conn)
    _import(conn, project_id)
    assert anatomy_export.export_project_anatomy(conn, project_id) is None


def test_a_relative_export_directory_is_refused(monkeypatch) -> None:
    monkeypatch.setenv(anatomy_export.EXPORT_DIR_ENV, "relative/dir")
    with pytest.raises(anatomy_export.AnatomyExportError, match="absolute"):
        anatomy_export.export_dir()


def test_a_code_that_cannot_name_a_file_is_refused(conn, tmp_path) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    conn.execute("UPDATE agency_projects SET code = '../escape' WHERE project_id = %s", (project_id,))
    with pytest.raises(anatomy_export.AnatomyExportError, match="cannot name"):
        anatomy_export.export_project_anatomy(conn, project_id, directory=tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_an_affaire_is_published_before_its_anatomy_is_installed(conn, tmp_path) -> None:
    project_id = _project(conn)  # no reviewed dossier imported
    path = anatomy_export.export_project_anatomy(conn, project_id, directory=tmp_path)
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["anatomy"]["status"] == "not_installed"
    assert document["anatomy"]["structure"]["objects"] == []
    assert tmp_path / f"{_code(conn, project_id)}.json" in anatomy_export.export_all(conn, directory=tmp_path)


def test_export_all_covers_every_initialized_project(conn, tmp_path) -> None:
    project_id = _project(conn)
    _import(conn, project_id)
    written = anatomy_export.export_all(conn, directory=tmp_path)
    assert tmp_path / f"{_code(conn, project_id)}.json" in written


def test_the_published_anatomy_carries_property_labels_and_lists_undeclared_keys() -> None:
    section = anatomy_export.property_labels(
        {"attribute_claims": [{"attribute_key": "space.area"}, {"attribute_key": "local.inconnue"}]})
    assert section == {"labels": {"space.area": {"label": "Surface", "unit": "m2", "facet": "geometrie"}},
                       "undeclared": ["local.inconnue"]}


def _workspace_with_triggers(path, code: str, *, requested: str | None = None, changed: str | None = None):
    import sqlite3

    db = path / "workspace.sqlite3"
    with sqlite3.connect(db) as c:
        c.execute("CREATE TABLE IF NOT EXISTS workspace_anatomy_consolidation_requests "
                  "(workspace TEXT, project_code TEXT, requested_at TEXT, requested_by TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS workspace_document_metadata_overrides "
                  "(workspace TEXT, source_path TEXT, overrides_json TEXT, updated_at TEXT)")
        if requested:
            c.execute("INSERT INTO workspace_anatomy_consolidation_requests VALUES ('Affaires', ?, ?, 'human:test')",
                      (code, requested))
        if changed:
            c.execute("INSERT INTO workspace_document_metadata_overrides VALUES ('Affaires', ?, ?, ?)",
                      (f"{code}/DCE/m.ifc", json.dumps({"anatomy_source": {"active": True}}), changed))
            c.execute("INSERT INTO workspace_document_metadata_overrides VALUES ('Affaires', ?, ?, ?)",
                      (f"{code}/DCE/p.pdf", json.dumps({"index": "C"}), "2099-01-01"))  # not an anatomy change
    return db


def test_consolidation_triggers_are_read_from_the_workspace(tmp_path) -> None:
    from mvp_vertical import project_pieces

    db = _workspace_with_triggers(tmp_path, "DEMO", requested="2026-11-11T10:00:00Z", changed="2026-11-11T09:00:00Z")
    assert project_pieces.read_consolidation_triggers(db) == {
        "DEMO": {"requested": "2026-11-11T10:00:00Z", "changed": "2026-11-11T09:00:00Z"}}


def test_pending_consolidations_run_once_per_workspace_request(conn, tmp_path, monkeypatch) -> None:
    from mvp_vertical import project_pieces

    project_id = _project(conn)
    code = _code(conn, project_id)
    calls = []
    monkeypatch.setattr(anatomy_export, "export_project_anatomy",
                        lambda conn, pid, directory=None, consolidate=False: calls.append((pid, consolidate)))
    db = _workspace_with_triggers(tmp_path, code, changed="2026-11-11T09:00:00Z")
    monkeypatch.setenv(project_pieces.WORKSPACE_DB_ENV, str(db))
    out = tmp_path / "anatomie"

    # A changed card brings in only the sources that ask for it now.
    assert anatomy_export.consolidate_pending(conn, directory=out) == [code]
    assert calls == [(project_id, False)]
    assert anatomy_export.consolidate_pending(conn, directory=out) == []  # handled once

    # The project card button consolidates every declared source.
    _workspace_with_triggers(tmp_path, code, requested="2026-11-11T10:00:00Z")
    assert anatomy_export.consolidate_pending(conn, directory=out) == [code]
    assert calls[-1] == (project_id, True)
    assert anatomy_export.consolidate_pending(conn, directory=out) == []
    assert "UNKNOWN" not in json.loads((out / "consolidation-requests.json").read_text(encoding="utf-8"))
