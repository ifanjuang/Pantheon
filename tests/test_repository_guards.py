from __future__ import annotations

import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".github" / "scripts"


def _load(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_predecessor_guard_accepts_a_self_contained_tree() -> None:
    guard = _load("check_no_predecessor_dependency")
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "docs").mkdir()
        (root / "docs" / "README.md").write_text(
            "Pantheon Next is self-contained.\n", encoding="utf-8"
        )
        assert guard.find_dependencies(root) == []


def test_predecessor_guard_skips_long_unrelated_minified_lines() -> None:
    guard = _load("check_no_predecessor_dependency")
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        assets = root / "static"
        assets.mkdir()
        (assets / "vendor.js").write_text("x" * 500_000 + "\n", encoding="utf-8")
        assert guard.find_dependencies(root) == []


def test_predecessor_guard_rejects_active_remote_and_environment_dependency() -> None:
    guard = _load("check_no_predecessor_dependency")
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "scripts").mkdir()
        (root / "scripts" / "bootstrap.sh").write_text(
            "git clone https://github.com/ifanjuang/Pantheon-OS.git\n"
            "echo $PANTHEON_OS_PATH\n",
            encoding="utf-8",
        )
        failures = guard.find_dependencies(root)
        labels = {failure[2] for failure in failures}
        assert labels == {
            "https predecessor remote",
            "predecessor environment variable",
        }


def test_predecessor_guard_allows_historical_trace() -> None:
    guard = _load("check_no_predecessor_dependency")
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "ai_logs").mkdir()
        (root / "ai_logs" / "migration.md").write_text(
            "Historical source: https://github.com/ifanjuang/Pantheon-OS\n",
            encoding="utf-8",
        )
        assert guard.find_dependencies(root) == []


def test_predecessor_guard_rejects_vendored_snapshot() -> None:
    guard = _load("check_no_predecessor_dependency")
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        snapshot = root / "legacy" / "Pantheon-OS"
        snapshot.mkdir(parents=True)
        failures = guard.find_dependencies(root)
        assert failures == [
            (
                "legacy/Pantheon-OS",
                0,
                "vendored predecessor snapshot",
                "active tree contains a Pantheon-OS snapshot",
            )
        ]


def test_internal_link_guard_does_not_treat_v1_hermes_route_as_repo_path() -> None:
    guard = _load("check_internal_links")
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        doc = root / "docs" / "governance" / "API.md"
        doc.parent.mkdir(parents=True)
        doc.write_text(
            "GET /v1/hermes/execution-admissions/{admission_id}\n"
            "Schema: schemas/work_issue_slice.schema.yaml\n",
            encoding="utf-8",
        )
        schema = root / "schemas" / "work_issue_slice.schema.yaml"
        schema.parent.mkdir(parents=True)
        schema.write_text("type: object\n", encoding="utf-8")

        original_root = guard.ROOT
        original_prefix = guard.DOCS_PREFIX
        try:
            guard.ROOT = root
            guard.DOCS_PREFIX = "docs/governance"
            refs = guard.find_refs("docs/governance/API.md", None)
        finally:
            guard.ROOT = original_root
            guard.DOCS_PREFIX = original_prefix

        assert refs == [(2, "schemas/work_issue_slice.schema.yaml")]
