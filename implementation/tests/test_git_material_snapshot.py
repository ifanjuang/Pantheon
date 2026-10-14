from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

IMPLEMENTATION = Path(__file__).resolve().parents[1]
if str(IMPLEMENTATION) not in sys.path:
    sys.path.insert(0, str(IMPLEMENTATION))

from tools.git_material_snapshot import porcelain_status, snapshot_tracked_material


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True, text=True)
    _git(repo, "config", "user.email", "qualification@example.invalid")
    _git(repo, "config", "user.name", "Qualification Test")
    (repo / "tracked.txt").write_text("alpha\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "baseline")
    return repo


def test_snapshot_hashes_current_file_bytes_and_status_detects_mutation(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    before = snapshot_tracked_material(repo)

    assert before["tracked.txt"]["kind"] == "file"
    assert porcelain_status(repo) == []

    (repo / "tracked.txt").write_text("beta\n", encoding="utf-8")
    after = snapshot_tracked_material(repo)

    assert before["tracked.txt"]["sha256"] != after["tracked.txt"]["sha256"]
    assert porcelain_status(repo)


def test_snapshot_records_gitlink_without_opening_it_as_a_file(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    commit = _git(repo, "rev-parse", "HEAD")

    _git(repo, "update-index", "--add", "--cacheinfo", f"160000,{commit},vendor/upstream")
    snapshot = snapshot_tracked_material(repo)

    assert snapshot["vendor/upstream"] == {
        "kind": "gitlink",
        "index_object_id": commit,
    }


def test_snapshot_hashes_symlink_identity_without_following_target(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    link = repo / "tracked-link"
    try:
        os.symlink("tracked.txt", link)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this platform")

    _git(repo, "add", "tracked-link")
    snapshot = snapshot_tracked_material(repo)
    first_digest = snapshot["tracked-link"]["sha256"]

    (repo / "tracked.txt").write_text("changed target bytes\n", encoding="utf-8")
    snapshot_after_target_change = snapshot_tracked_material(repo)

    assert snapshot["tracked-link"]["kind"] == "symlink"
    assert snapshot_after_target_change["tracked-link"]["sha256"] == first_digest
