from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github/scripts/check_no_local_cockpit.py"
SPEC = importlib.util.spec_from_file_location("check_no_local_cockpit", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def valid_tree(tmp_path: Path) -> Path:
    control = tmp_path / MODULE.CONTROL_REL
    for relative in MODULE.ALLOWED_CONTROL_FILES:
        target = control / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("", encoding="utf-8")
    (control / "index.html").write_text(
        "<!doctype html><title>orientation</title>"
        "<p>implementation/mvp_vertical/cockpit — NON-RUNTIME</p>",
        encoding="utf-8",
    )
    return tmp_path


def test_repository_current_boundary_passes() -> None:
    assert MODULE.check(ROOT) == []


def test_current_allowlisted_boundary_shape_passes(tmp_path: Path) -> None:
    root = valid_tree(tmp_path)
    assert MODULE.check(root) == []


def test_real_dashboard_directory_is_rejected(tmp_path: Path) -> None:
    root = valid_tree(tmp_path)
    (root / "dashboard").mkdir()
    assert any("retired product path exists: dashboard" in item for item in MODULE.check(root))


def test_unexpected_local_product_assets_are_rejected(tmp_path: Path) -> None:
    root = valid_tree(tmp_path)
    control = root / MODULE.CONTROL_REL
    (control / "project.html").write_text("<main>product cockpit</main>", encoding="utf-8")
    (control / "styles").mkdir()
    (control / "styles/cockpit.css").write_text("body{}", encoding="utf-8")
    findings = MODULE.check(root)
    assert any("unexpected cockpit asset: project.html" in item for item in findings)
    assert any("unexpected cockpit asset: styles/cockpit.css" in item for item in findings)


def test_orientation_page_cannot_load_executable_assets(tmp_path: Path) -> None:
    root = valid_tree(tmp_path)
    index = root / MODULE.CONTROL_REL / "index.html"
    index.write_text(
        "<!doctype html><link rel='stylesheet' href='style.css'>"
        "<script src='app.js'></script>"
        "<p>implementation/mvp_vertical/cockpit — NON-RUNTIME</p>",
        encoding="utf-8",
    )
    findings = MODULE.check(root)
    assert any("stylesheet:style.css" in item for item in findings)
    assert any("script:app.js" in item for item in findings)


def test_orientation_page_must_name_co_located_candidate(tmp_path: Path) -> None:
    root = valid_tree(tmp_path)
    index = root / MODULE.CONTROL_REL / "index.html"
    index.write_text("<!doctype html><p>NON-RUNTIME</p>", encoding="utf-8")

    assert any(
        "does not name the co-located implementation cockpit" in item
        for item in MODULE.check(root)
    )


def test_orientation_page_rejects_historical_repository_as_current_cockpit(
    tmp_path: Path,
) -> None:
    root = valid_tree(tmp_path)
    index = root / MODULE.CONTROL_REL / "index.html"
    index.write_text(
        "<!doctype html><p>implementation/ — pantheon-mvp — NON-RUNTIME</p>",
        encoding="utf-8",
    )

    assert any(
        "historical pantheon-mvp repository as current cockpit" in item
        for item in MODULE.check(root)
    )
