from __future__ import annotations

import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"


def test_cockpit_runtime_assets_use_one_recursive_package_pattern() -> None:
    config = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    patterns = config["tool"]["setuptools"]["package-data"]["mvp_vertical"]

    assert "cockpit/**/*" in patterns
    assert not any(
        pattern.startswith("cockpit/") and pattern != "cockpit/**/*"
        for pattern in patterns
    )
