from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from mvp_vertical import workspace_markdown_write


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_create_read_patch_roundtrip_with_verified_receipts(tmp_path: Path) -> None:
    roots = {"vault": tmp_path}
    (tmp_path / "Affaires" / "Alpha").mkdir(parents=True)

    created = workspace_markdown_write.create_workspace_markdown(
        roots,
        "vault",
        "Affaires/Alpha/note.md",
        content="# Alpha\n\nStatus: draft\n",
    )
    note = tmp_path / "Affaires" / "Alpha" / "note.md"
    assert created["operation"] == "create"
    assert created["basis_digest"] is None
    assert created["result_digest"] == _digest(note)
    assert created["verified_by_reread"] is True
    assert created["persistence_effect"] == "workspace_file"
    assert created["couchdb_direct_write"] is False
    assert created["hindsight_direct_write"] is False
    assert created["authorized"] is False
    assert created["is_evidence"] is False

    observed = workspace_markdown_write.read_workspace_markdown(
        roots, "vault", "Affaires/Alpha/note.md"
    )
    assert observed["text"] == "# Alpha\n\nStatus: draft\n"
    assert observed["result_digest"] == created["result_digest"]

    patched = workspace_markdown_write.patch_workspace_markdown(
        roots,
        "vault",
        "Affaires/Alpha/note.md",
        expected_digest=observed["result_digest"],
        old_text="Status: draft",
        new_text="Status: reviewed",
    )
    assert note.read_text(encoding="utf-8") == "# Alpha\n\nStatus: reviewed\n"
    assert patched["basis_digest"] == observed["result_digest"]
    assert patched["result_digest"] == _digest(note)
    assert patched["changed"] is True


def test_create_refuses_to_overwrite_existing_markdown(tmp_path: Path) -> None:
    note = tmp_path / "note.md"
    note.write_text("existing\n", encoding="utf-8")

    with pytest.raises(
        workspace_markdown_write.WorkspaceMarkdownWriteConflict,
        match="already exists",
    ):
        workspace_markdown_write.create_workspace_markdown(
            {"vault": tmp_path}, "vault", "note.md", content="replacement\n"
        )

    assert note.read_text(encoding="utf-8") == "existing\n"


def test_patch_refuses_stale_digest_and_preserves_external_edit(tmp_path: Path) -> None:
    note = tmp_path / "note.md"
    note.write_text("Status: draft\n", encoding="utf-8")
    basis = _digest(note)
    note.write_text("Status: changed elsewhere\n", encoding="utf-8")

    with pytest.raises(
        workspace_markdown_write.WorkspaceMarkdownWriteConflict,
        match="changed since it was read",
    ):
        workspace_markdown_write.patch_workspace_markdown(
            {"vault": tmp_path},
            "vault",
            "note.md",
            expected_digest=basis,
            old_text="Status: draft",
            new_text="Status: reviewed",
        )

    assert note.read_text(encoding="utf-8") == "Status: changed elsewhere\n"


def test_patch_requires_one_exact_anchor(tmp_path: Path) -> None:
    note = tmp_path / "note.md"
    note.write_text("same\nsame\n", encoding="utf-8")

    with pytest.raises(
        workspace_markdown_write.WorkspaceMarkdownWriteConflict,
        match="exactly once",
    ):
        workspace_markdown_write.patch_workspace_markdown(
            {"vault": tmp_path},
            "vault",
            "note.md",
            expected_digest=_digest(note),
            old_text="same",
            new_text="other",
        )

    assert note.read_text(encoding="utf-8") == "same\nsame\n"


def test_patch_refuses_missing_file(tmp_path: Path) -> None:
    with pytest.raises(
        workspace_markdown_write.WorkspaceMarkdownWriteConflict,
        match="does not exist",
    ):
        workspace_markdown_write.patch_workspace_markdown(
            {"vault": tmp_path},
            "vault",
            "missing.md",
            expected_digest="0" * 64,
            old_text="x",
            new_text="y",
        )


def test_write_surface_is_markdown_only_and_cannot_escape_root(tmp_path: Path) -> None:
    with pytest.raises(workspace_markdown_write.WorkspaceMarkdownWriteError):
        workspace_markdown_write.create_workspace_markdown(
            {"vault": tmp_path}, "vault", "../outside.md", content="no\n"
        )
    with pytest.raises(workspace_markdown_write.WorkspaceMarkdownWriteError, match=".md files only"):
        workspace_markdown_write.create_workspace_markdown(
            {"vault": tmp_path}, "vault", "note.txt", content="no\n"
        )
    with pytest.raises(workspace_markdown_write.WorkspaceMarkdownWriteError, match="not writable"):
        workspace_markdown_write.create_workspace_markdown(
            {"vault": tmp_path}, "vault", ".hidden.md", content="no\n"
        )
    with pytest.raises(workspace_markdown_write.WorkspaceMarkdownWriteError, match="not writable"):
        workspace_markdown_write.create_workspace_markdown(
            {"vault": tmp_path}, "vault", "_VAULT.md", content="no\n"
        )


def test_symlink_parent_is_not_followed(tmp_path: Path) -> None:
    if not hasattr(os, "O_NOFOLLOW"):
        pytest.skip("O_NOFOLLOW unavailable")
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "vault"
    root.mkdir()
    (root / "linked").symlink_to(outside, target_is_directory=True)

    with pytest.raises(workspace_markdown_write.WorkspaceMarkdownWriteError):
        workspace_markdown_write.create_workspace_markdown(
            {"vault": root}, "vault", "linked/note.md", content="no\n"
        )

    assert not (outside / "note.md").exists()


def test_patch_rejects_noncanonical_expected_digest(tmp_path: Path) -> None:
    note = tmp_path / "note.md"
    note.write_text("x\n", encoding="utf-8")

    with pytest.raises(
        workspace_markdown_write.WorkspaceMarkdownWriteError,
        match="lowercase SHA-256",
    ):
        workspace_markdown_write.patch_workspace_markdown(
            {"vault": tmp_path},
            "vault",
            "note.md",
            expected_digest="ABC",
            old_text="x",
            new_text="y",
        )
