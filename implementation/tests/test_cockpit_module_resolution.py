"""Every relative browser resource we ship must resolve to a real file.

`node --check` parses a file; it never resolves what that file imports or what a
literal browser `fetch()` will request. A missing local resource therefore fails
only in the browser. These checks close the class rather than one instance: they
walk shipped browser scripts, resolve relative module specifiers from the source
file and resolve literal static fetches from the Cockpit document root.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"
SCAN_ROOTS = (
    COCKPIT,
    ROOT / "mvp_vertical" / "mobile_editor",
)

# from "./x.js" | import "./x.js" | import("./x.js") | export ... from "./x.js"
SPECIFIER = re.compile(
    r"""(?:\bfrom|\bimport|\bnew\s+Worker)\s*\(?\s*["'](?P<spec>\.[^"']*)["']""",
)
STATIC_FETCH = re.compile(
    r"""\bfetch\s*\(\s*["'](?P<spec>[^"']+\.(?:json|js|css|svg|png|webp))["']""",
)


def _sources() -> list[Path]:
    found = [
        path
        for root in SCAN_ROOTS
        if root.exists()
        for path in root.rglob("*.js")
        if "vendor" not in path.relative_to(ROOT).parts
    ]
    assert found, "no browser JavaScript discovered"
    return sorted(found)


def _references(path: Path) -> list[tuple[int, str]]:
    text = path.read_text(encoding="utf-8")
    out: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("//"):
            continue
        for match in SPECIFIER.finditer(line):
            out.append((number, match.group("spec")))
    return out


def _static_fetches(path: Path) -> list[tuple[int, str]]:
    text = path.read_text(encoding="utf-8")
    out: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("//"):
            continue
        for match in STATIC_FETCH.finditer(line):
            spec = match.group("spec")
            if spec.startswith(("http://", "https://", "/", "../")):
                continue
            out.append((number, spec.removeprefix("./")))
    return out


@pytest.mark.parametrize("source", _sources(), ids=lambda p: str(p.relative_to(ROOT)))
def test_relative_module_specifiers_resolve(source: Path) -> None:
    unresolved = [
        f"{source.relative_to(ROOT)}:{number} -> {spec} "
        f"(resolves to {(source.parent / spec).resolve().relative_to(ROOT)})"
        for number, spec in _references(source)
        if not (source.parent / spec).is_file()
    ]
    assert not unresolved, "unresolvable relative import(s):\n" + "\n".join(unresolved)


def test_literal_cockpit_static_fetches_resolve_from_document_root() -> None:
    unresolved = [
        f"{source.relative_to(ROOT)}:{number} -> {spec}"
        for source in _sources()
        if COCKPIT in source.parents
        for number, spec in _static_fetches(source)
        if not (COCKPIT / spec).is_file()
    ]
    assert not unresolved, "unresolvable local fetch resource(s):\n" + "\n".join(unresolved)


def test_the_check_would_catch_a_broken_specifier(tmp_path: Path) -> None:
    """A guard is only worth its false-negative rate; prove this one bites."""
    broken = tmp_path / "broken.js"
    broken.write_text('import { thing } from "./missing/module.js";\n', encoding="utf-8")

    references = _references(broken)
    assert references == [(1, "./missing/module.js")]
    assert not (broken.parent / references[0][1]).is_file()


def test_static_fetch_check_would_catch_a_missing_registry(tmp_path: Path) -> None:
    broken = tmp_path / "broken.js"
    broken.write_text('fetch("registries/missing.json");\n', encoding="utf-8")

    assert _static_fetches(broken) == [(1, "registries/missing.json")]
    assert not (COCKPIT / "registries/missing.json").is_file()


def test_every_shipped_script_is_covered() -> None:
    """The scan must follow the tree, not a list that silently stops matching."""
    discovered = {path.relative_to(ROOT) for path in _sources()}
    on_disk = {
        path.relative_to(ROOT)
        for root in SCAN_ROOTS
        if root.exists()
        for path in root.rglob("*.js")
        if "vendor" not in path.relative_to(ROOT).parts
    }
    assert discovered == on_disk
