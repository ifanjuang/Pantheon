from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
ACTIVE_DOCS = (ROOT / "docs" / "cockpit" / "JS_MODULE_INVENTORY.md",)

RETIRED_PATHS = (
    "v2_app_schema.js",
    "v2_handoff.js",
    "v2_hermes_send.js",
    "styles/gradient_borders.css",
)

TEXT_SUFFIXES = {".html", ".js", ".json", ".md", ".yml", ".yaml"}


def active_text_files() -> list[Path]:
    files = [
        path
        for root in (COCKPIT, ROOT / ".github" / "workflows")
        if root.exists()
        for path in root.rglob("*")
        if path.is_file() and path.suffix in TEXT_SUFFIXES
    ]
    files.extend(path for path in ACTIVE_DOCS if path.exists())
    return sorted(set(files))


def test_retired_cockpit_module_paths_are_absent_from_active_contracts() -> None:
    violations: list[str] = []

    for path in active_text_files():
        content = path.read_text(encoding="utf-8")
        for retired in RETIRED_PATHS:
            if retired in content:
                violations.append(f"{path.relative_to(ROOT)}: {retired}")

    assert not violations, "Retired Cockpit paths remain active:\n" + "\n".join(violations)


def test_canonical_projection_module_exists_without_compatibility_wrapper() -> None:
    assert (COCKPIT / "projection" / "cockpit_projection.js").is_file()
    assert not (COCKPIT / "v2_app_schema.js").exists()
