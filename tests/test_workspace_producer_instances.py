"""Contract for templated Workspace producer instances.

`configure-workspace-producer` deploys one `pantheon-workspace-producer@NAME`
instance per mounted source root. These tests exercise its dry-run and
validation paths only; nothing is written outside a temporary directory.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "deployment" / "ubuntu" / "configure-workspace-producer"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["bash", str(SCRIPT), *args], text=True, capture_output=True)


def test_help_documents_set_list_and_remove() -> None:
    result = _run("--help")
    assert result.returncode == 0
    for verb in ("--list", "--set NAME", "--remove NAME", "--apply"):
        assert verb in result.stdout
    assert "indexing != Evidence" in result.stdout


def test_dry_run_plans_instance_without_writing(tmp_path: Path) -> None:
    source = tmp_path / "library"
    source.mkdir()
    result = _run(
        "--set", "library", "--root", str(source), "--bank", "LIBRARY_BANK",
        "--label", "Library", "--max-depth", "1", "--reconcile-seconds", "300",
    )
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "nothing written" in out
    assert "WORKSPACE_ROOT_LABEL=Library" in out
    assert f"WORKSPACE_ROOT_PATH={source}" in out
    assert "WORKSPACE_MAX_DEPTH=1" in out
    assert "WORKSPACE_HINDSIGHT_BANK_ID=LIBRARY_BANK" in out
    assert "WORKSPACE_HINDSIGHT_SOURCE_KIND=library" in out
    assert "WORKSPACE_INDEX_DB=/var/lib/pantheon-workspace-producer/library/index.sqlite3" in out
    assert "AUTHORIZATION" not in out
    assert "--workspace-db Library=/var/lib/pantheon-workspace-producer/library/index.sqlite3" in out


def test_invalid_instances_fail_closed(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    cases = [
        (("--set", "Bad Name", "--root", str(source), "--bank", "B"), "NAME must match"),
        (("--set", "ok", "--root", "relative", "--bank", "B"), "--root must be absolute"),
        (("--set", "ok", "--root", str(tmp_path / "missing"), "--bank", "B"), "is the share mounted"),
        (("--set", "ok", "--root", str(source)), "requires --root and --bank"),
        (("--set", "ok", "--root", str(source), "--bank", "B", "--max-depth", "17"), "--max-depth must be 1-16"),
        (("--set", "ok", "--root", str(source), "--bank", "B", "--state-db", str(source / "i.db")), "outside the watched root"),
        (("--set", "ok", "--root", str(source), "--bank", "B", "--enable"), "--enable requires --apply"),
    ]
    for args, message in cases:
        result = _run(*args)
        assert result.returncode != 0, args
        assert message in result.stderr, (args, result.stderr)


def test_template_is_hardened_and_reads_instance_configuration() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "EnvironmentFile=$CONFIG_DIR/%i.env" in text
    assert "EnvironmentFile=-$SHARED_ENV" in text
    assert "--root \\${WORKSPACE_ROOT_LABEL}=\\${WORKSPACE_ROOT_PATH}" in text
    for setting in ("NoNewPrivileges=true", "ProtectSystem=strict", "ProtectHome=true", "PrivateTmp=true"):
        assert setting in text
    assert "RequiresMountsFor=" in text
    assert "--remove disables the instance and deletes its configuration; the index is kept." in text
