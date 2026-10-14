from __future__ import annotations

from pathlib import Path

import pytest

from mvp_vertical import workspace_collection_read, workspace_human_note


def _write_source(root: Path, name: str, payload: bytes = b"source-bytes") -> Path:
    path = root / name
    path.write_bytes(payload)
    return path


def test_yaml_source_is_never_aliased_to_its_own_infos_sidecar(tmp_path: Path) -> None:
    source = _write_source(tmp_path, "config.yaml", b"source: preserve\n")

    with pytest.raises(
        workspace_human_note.WorkspaceHumanNoteError,
        match="YAML workspace sources",
    ):
        workspace_human_note.write_workspace_human_note(
            {"vault": tmp_path},
            "vault",
            source.name,
            human_note="must not overwrite source",
            expected_manifest_digest=None,
        )

    assert source.read_bytes() == b"source: preserve\n"
    observed = workspace_collection_read.observe_workspace_file(
        {"vault": tmp_path},
        "vault",
        source.name,
        include_digest=False,
    )
    assert observed["workspace_file"]["adjacent_document_sidecar"] == {
        "state": "unsupported_source_collision",
        "relative_path": None,
        "parsed": False,
        "identity_mapping_resolved": False,
    }


def test_legacy_note_markers_and_source_path_are_migrated_on_write(tmp_path: Path) -> None:
    source = _write_source(tmp_path, "Plan.pdf")
    sidecar = tmp_path / "Plan.yaml"
    sidecar.write_text(
        "# >>> Pantheon workspace note\n"
        "pantheon_workspace:\n"
        "  source_path: Plans/Plan.pdf\n"
        "  human_note: Ancienne note\n"
        "# <<< Pantheon workspace note\n",
        encoding="utf-8",
    )

    observed = workspace_human_note.read_workspace_human_note(
        {"vault": tmp_path}, "vault", source.name
    )
    assert observed["binding_state"] == "bound"
    assert observed["human_note"] == "Ancienne note"

    saved = workspace_human_note.write_workspace_human_note(
        {"vault": tmp_path},
        "vault",
        source.name,
        human_note="Note migrée",
        expected_manifest_digest=observed["manifest_digest"],
    )

    text = sidecar.read_text(encoding="utf-8")
    assert "# >>> Pantheon workspace info" in text
    assert "# <<< Pantheon workspace info" in text
    assert "workspace note" not in text
    assert "source_file: Plan.pdf" in text
    assert "source_path:" not in text
    assert saved["binding_state"] == "bound"
    assert saved["human_note"] == "Note migrée"


def test_source_basename_whitespace_is_preserved_in_infos_sidecar_name(tmp_path: Path) -> None:
    source = _write_source(tmp_path, " Plan .pdf")

    saved = workspace_human_note.write_workspace_human_note(
        {"vault": tmp_path},
        "vault",
        source.name,
        human_note="Conserver le nom exact",
        expected_manifest_digest=None,
    )

    sidecar = tmp_path / " Plan .yaml"
    assert sidecar.is_file()
    assert not (tmp_path / "Plan.yaml").exists()
    assert saved["sidecar_relative_path"] == " Plan .yaml"

    observed = workspace_collection_read.observe_workspace_file(
        {"vault": tmp_path},
        "vault",
        source.name,
        include_digest=False,
    )
    assert observed["workspace_file"]["adjacent_document_sidecar"] == {
        "state": "present",
        "relative_path": " Plan .yaml",
        "parsed": False,
        "identity_mapping_resolved": False,
    }
