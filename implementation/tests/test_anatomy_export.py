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
