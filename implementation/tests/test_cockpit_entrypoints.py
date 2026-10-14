"""Every cockpit entry point must point at a file that exists.

The consolidation onto a single cockpit page deleted v2.html / v3.html. The
GitHub Pages entry point at the repository root kept redirecting to the deleted
v3.html, which silently produced a 404 for anyone opening the published page.
These checks make a dangling entry point fail the build instead.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COCKPIT = ROOT / "mvp_vertical" / "cockpit"

# Entry points that redirect somewhere, and the directory their targets resolve against.
ENTRY_POINTS = (
    (ROOT / "index.html", ROOT),
    (COCKPIT / "demo.html", COCKPIT),
)

TARGET_PATTERN = re.compile(r'(?:url=|href="|replace\(")\.?/?([A-Za-z0-9_./-]+\.html)')


def test_entry_point_redirect_targets_exist() -> None:
    for entry, base in ENTRY_POINTS:
        html = entry.read_text(encoding="utf-8")
        targets = set(TARGET_PATTERN.findall(html))
        assert targets, f"{entry.name} declares no redirect target"

        for target in targets:
            resolved = (base / target).resolve()
            assert resolved.exists(), (
                f"{entry.relative_to(ROOT)} points at {target}, which does not exist"
            )


def test_repository_root_opens_the_single_cockpit_page() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    assert "mvp_vertical/cockpit/index.html?mode=demo" in html
    # The retired pages must not come back as entry points.
    assert "v2.html" not in html
    assert "v3.html" not in html
