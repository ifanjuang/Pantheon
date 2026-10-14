#!/usr/bin/env python3
"""Synchronize the public demo with the exact native Hermes dashboard bundle."""

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "templates/hermes/dashboard-plugins/pantheon-modules/dashboard/dist"
PREVIEW = ROOT / "docs/assets/pantheon-control/hermes-preview"

for source_name, target_name in (
    ("index.js", "plugin-index.js"),
    ("style.css", "plugin-style.css"),
):
    source = PLUGIN / source_name
    target = PREVIEW / target_name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    print(f"synced {source.relative_to(ROOT)} -> {target.relative_to(ROOT)}")
