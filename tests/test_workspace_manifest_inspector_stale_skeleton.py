from __future__ import annotations

import hashlib
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "docs" / "examples" / "workspace_manifest_inspector"
PACKAGE = FIXTURE / "workspace_qualifiable" / "CCTP"
EXPECTED = FIXTURE / "expected" / "qualifiable_cctp_local_skeleton.yaml"


def _yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    assert isinstance(value, dict)
    return value


def _matches_package(skeleton: dict, package: Path) -> bool:
    representation = skeleton["observed"]["representation"]["markdown"]
    markdown = package / representation["file"]
    if not markdown.is_file():
        return False
    digest = hashlib.sha256(markdown.read_bytes()).hexdigest()
    return digest == representation["digest_sha256"]


def test_local_skeleton_becomes_stale_after_markdown_change(tmp_path: Path) -> None:
    skeleton = _yaml(EXPECTED)

    copied_package = tmp_path / "CCTP"
    copied_package.mkdir()
    copied_markdown = copied_package / "CCTP.md"
    copied_markdown.write_bytes((PACKAGE / "CCTP.md").read_bytes())

    assert _matches_package(skeleton, copied_package)

    copied_markdown.write_text(
        copied_markdown.read_text(encoding="utf-8")
        + "\nModification après génération du squelette.\n",
        encoding="utf-8",
    )

    assert not _matches_package(skeleton, copied_package)
