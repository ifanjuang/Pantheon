from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient

from mvp_vertical import workspace_human_note
from mvp_vertical.workspace_qualification_api import install_workspace_qualification_routes


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source(root: Path, name: str = "Plan-RDC-D.pdf") -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"%PDF-1.7\nworkspace-note-test\n")
    return path


def _sidecar(source: Path) -> Path:
    return source.with_name(f"{source.stem}.yaml")


def test_human_note_creates_per_source_info_sidecar_and_roundtrips(tmp_path: Path) -> None:
    source = _source(tmp_path)

    initial = workspace_human_note.read_workspace_human_note(
        {"vault": tmp_path}, "vault", source.name
    )
    assert initial["manifest_state"] == "absent"
    assert initial["manifest_digest"] is None
    assert initial["sidecar_relative_path"] == "Plan-RDC-D.yaml"
    assert initial["human_note"] == ""
    assert initial["governed_identity"] is False

    saved = workspace_human_note.write_workspace_human_note(
        {"vault": tmp_path},
        "vault",
        source.name,
        human_note="À comparer avec le plan BET avant validation.",
        expected_manifest_digest=None,
    )

    sidecar = _sidecar(source)
    raw = sidecar.read_text(encoding="utf-8")
    assert raw.startswith("# >>> Pantheon workspace info\n")
    assert "source_file: Plan-RDC-D.pdf" in raw
    assert "human_note: À comparer avec le plan BET avant validation." in raw
    assert raw.endswith("# <<< Pantheon workspace info\n")
    assert stat.S_IMODE(sidecar.stat().st_mode) == 0o600
    assert saved["manifest_digest"] == _digest(sidecar)
    assert saved["binding_state"] == "bound"
    assert saved["human_note"] == "À comparer avec le plan BET avant validation."


def test_human_note_preserves_unowned_info_bytes_and_comments(tmp_path: Path) -> None:
    source = _source(tmp_path)
    sidecar = _sidecar(source)
    original = (
        "display:\n"
        "  full_name: Plan du rez-de-chaussée\n"
        "# commentaire humain à conserver exactement\n"
    )
    sidecar.write_text(original, encoding="utf-8")

    observed = workspace_human_note.read_workspace_human_note(
        {"vault": tmp_path}, "vault", source.name
    )
    saved = workspace_human_note.write_workspace_human_note(
        {"vault": tmp_path},
        "vault",
        source.name,
        human_note="Note locale",
        expected_manifest_digest=observed["manifest_digest"],
    )

    after = sidecar.read_text(encoding="utf-8")
    assert after.startswith(original)
    assert "# commentaire humain à conserver exactement" in after
    assert saved["human_note"] == "Note locale"

    updated = workspace_human_note.write_workspace_human_note(
        {"vault": tmp_path},
        "vault",
        source.name,
        human_note="Note locale corrigée",
        expected_manifest_digest=saved["manifest_digest"],
    )
    final = sidecar.read_text(encoding="utf-8")
    assert final.startswith(original)
    assert final.count("# >>> Pantheon workspace info") == 1
    assert updated["human_note"] == "Note locale corrigée"


def test_human_note_is_inserted_before_explicit_yaml_document_end(tmp_path: Path) -> None:
    source = _source(tmp_path)
    sidecar = _sidecar(source)
    sidecar.write_text("display:\n  full_name: Plan RDC\n...\n# trailing comment\n", encoding="utf-8")
    observed = workspace_human_note.read_workspace_human_note(
        {"vault": tmp_path}, "vault", source.name
    )

    workspace_human_note.write_workspace_human_note(
        {"vault": tmp_path},
        "vault",
        source.name,
        human_note="Vérifier avec le BET",
        expected_manifest_digest=observed["manifest_digest"],
    )

    text = sidecar.read_text(encoding="utf-8")
    assert text.index("# >>> Pantheon workspace info") < text.index("\n...\n")
    assert text.endswith("...\n# trailing comment\n")
    loaded = yaml.safe_load(text)
    assert loaded["display"]["full_name"] == "Plan RDC"
    assert loaded["pantheon_workspace"]["human_note"] == "Vérifier avec le BET"


def test_human_note_preserves_existing_mode_owner_and_xattrs(tmp_path: Path) -> None:
    source = _source(tmp_path)
    sidecar = _sidecar(source)
    sidecar.write_text("display:\n  full_name: Plan RDC\n", encoding="utf-8")
    sidecar.chmod(0o600)
    before = sidecar.stat()

    xattr_supported = all(hasattr(os, name) for name in ("setxattr", "getxattr", "listxattr"))
    xattr_name = "user.pantheon-test"
    if xattr_supported:
        try:
            os.setxattr(sidecar, xattr_name, b"keep-me")
        except OSError:
            xattr_supported = False

    observed = workspace_human_note.read_workspace_human_note(
        {"vault": tmp_path}, "vault", source.name
    )
    workspace_human_note.write_workspace_human_note(
        {"vault": tmp_path},
        "vault",
        source.name,
        human_note="Note locale",
        expected_manifest_digest=observed["manifest_digest"],
    )

    after = sidecar.stat()
    assert stat.S_IMODE(after.st_mode) == stat.S_IMODE(before.st_mode)
    assert after.st_uid == before.st_uid
    assert after.st_gid == before.st_gid
    if xattr_supported:
        assert os.getxattr(sidecar, xattr_name) == b"keep-me"


def test_human_note_refuses_stale_sidecar_digest(tmp_path: Path) -> None:
    source = _source(tmp_path)
    first = workspace_human_note.write_workspace_human_note(
        {"vault": tmp_path},
        "vault",
        source.name,
        human_note="Première note",
        expected_manifest_digest=None,
    )
    sidecar = _sidecar(source)
    sidecar.write_text(sidecar.read_text(encoding="utf-8") + "external: edit\n", encoding="utf-8")

    with pytest.raises(workspace_human_note.WorkspaceHumanNoteConflict, match="changed"):
        workspace_human_note.write_workspace_human_note(
            {"vault": tmp_path},
            "vault",
            source.name,
            human_note="Écrasement interdit",
            expected_manifest_digest=first["manifest_digest"],
        )

    assert "external: edit" in sidecar.read_text(encoding="utf-8")


def test_two_sources_in_same_folder_keep_independent_info_sidecars(tmp_path: Path) -> None:
    first_source = _source(tmp_path, "Plan-A.pdf")
    second_source = _source(tmp_path, "Plan-B.pdf")

    first = workspace_human_note.write_workspace_human_note(
        {"vault": tmp_path},
        "vault",
        first_source.name,
        human_note="Concerne uniquement le plan A",
        expected_manifest_digest=None,
    )
    second = workspace_human_note.write_workspace_human_note(
        {"vault": tmp_path},
        "vault",
        second_source.name,
        human_note="Concerne uniquement le plan B",
        expected_manifest_digest=None,
    )

    assert first["sidecar_relative_path"] == "Plan-A.yaml"
    assert second["sidecar_relative_path"] == "Plan-B.yaml"
    assert (tmp_path / "Plan-A.yaml").exists()
    assert (tmp_path / "Plan-B.yaml").exists()
    assert "plan A" in (tmp_path / "Plan-A.yaml").read_text(encoding="utf-8")
    assert "plan B" in (tmp_path / "Plan-B.yaml").read_text(encoding="utf-8")


def test_mismatched_explicit_info_binding_is_refused(tmp_path: Path) -> None:
    source = _source(tmp_path, "Plan-B.pdf")
    sidecar = _sidecar(source)
    sidecar.write_text(
        "# >>> Pantheon workspace info\n"
        "pantheon_workspace:\n"
        "  source_file: Plan-A.pdf\n"
        "  human_note: Mauvaise liaison\n"
        "# <<< Pantheon workspace info\n",
        encoding="utf-8",
    )
    observed = workspace_human_note.read_workspace_human_note(
        {"vault": tmp_path}, "vault", source.name
    )
    assert observed["binding_state"] == "mismatch"

    with pytest.raises(workspace_human_note.WorkspaceHumanNoteConflict, match="another workspace source"):
        workspace_human_note.write_workspace_human_note(
            {"vault": tmp_path},
            "vault",
            source.name,
            human_note="Ne doit pas remplacer la mauvaise liaison",
            expected_manifest_digest=observed["manifest_digest"],
        )


def test_packaged_source_uses_same_basename_for_source_and_info(tmp_path: Path) -> None:
    source = _source(tmp_path, "Plans/Plan-RDC-D/Plan-RDC-D.pdf")
    relative = source.relative_to(tmp_path).as_posix()
    saved = workspace_human_note.write_workspace_human_note(
        {"vault": tmp_path},
        "vault",
        relative,
        human_note="Package source",
        expected_manifest_digest=None,
    )
    assert saved["sidecar_relative_path"] == "Plans/Plan-RDC-D/Plan-RDC-D.yaml"
    assert source.with_name("Plan-RDC-D.yaml").exists()


def test_info_binding_survives_moving_source_and_sidecar_together(tmp_path: Path) -> None:
    source = _source(tmp_path, "Plans/Plan-RDC-D.pdf")
    relative = source.relative_to(tmp_path).as_posix()
    workspace_human_note.write_workspace_human_note(
        {"vault": tmp_path},
        "vault",
        relative,
        human_note="À conserver pendant le packaging",
        expected_manifest_digest=None,
    )
    package = tmp_path / "Plans" / "Plan-RDC-D"
    package.mkdir()
    source.rename(package / source.name)
    (tmp_path / "Plans" / "Plan-RDC-D.yaml").rename(package / "Plan-RDC-D.yaml")

    moved_relative = "Plans/Plan-RDC-D/Plan-RDC-D.pdf"
    observed = workspace_human_note.read_workspace_human_note(
        {"vault": tmp_path}, "vault", moved_relative
    )
    assert observed["binding_state"] == "bound"
    assert observed["human_note"] == "À conserver pendant le packaging"


def test_clearing_only_managed_note_removes_empty_sidecar(tmp_path: Path) -> None:
    source = _source(tmp_path)
    saved = workspace_human_note.write_workspace_human_note(
        {"vault": tmp_path},
        "vault",
        source.name,
        human_note="Temporaire",
        expected_manifest_digest=None,
    )
    cleared = workspace_human_note.write_workspace_human_note(
        {"vault": tmp_path},
        "vault",
        source.name,
        human_note="",
        expected_manifest_digest=saved["manifest_digest"],
    )
    assert not _sidecar(source).exists()
    assert cleared["manifest_state"] == "absent"
    assert cleared["human_note"] == ""


def test_human_note_refuses_symlink_sidecar(tmp_path: Path) -> None:
    source = _source(tmp_path)
    outside = tmp_path / "outside.yaml"
    outside.write_text("secret: keep\n", encoding="utf-8")
    os.symlink(outside, _sidecar(source))

    with pytest.raises(workspace_human_note.WorkspaceHumanNoteError, match="symlink"):
        workspace_human_note.read_workspace_human_note(
            {"vault": tmp_path}, "vault", source.name
        )
    assert outside.read_text(encoding="utf-8") == "secret: keep\n"


def _note_api(root: Path) -> TestClient:
    app = FastAPI()
    install_workspace_qualification_routes(
        app,
        workspace_roots={"vault": root},
        with_connection=lambda operation: operation(None),
        require_read_key=lambda: None,
        require_editor_key=lambda: None,
        require_human_actor=lambda: "ifan",
    )
    return TestClient(app)


def test_note_api_requires_explicit_write_and_returns_non_authority_boundaries(tmp_path: Path) -> None:
    source = _source(tmp_path)
    client = _note_api(tmp_path)

    read = client.post(
        "/cockpit/workspace-notes/read",
        json={"workspace_ref": "vault", "relative_path": source.name},
    )
    assert read.status_code == 200
    assert read.json()["manifest_digest"] is None
    assert read.json()["sidecar_relative_path"] == "Plan-RDC-D.yaml"

    write = client.post(
        "/cockpit/workspace-notes/write",
        json={
            "workspace_ref": "vault",
            "relative_path": source.name,
            "human_note": "Note humaine",
            "expected_manifest_digest": None,
        },
    )
    assert write.status_code == 200
    payload = write.json()
    assert payload["written_by"] == "ifan"
    assert payload["workspace_write"] is True
    assert payload["automatic_document_admission"] is False
    assert payload["is_evidence"] is False
    assert payload["human_note"] == "Note humaine"
