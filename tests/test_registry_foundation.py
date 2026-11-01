"""Read-only validation tests for the generic registry foundation."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_registry_foundation_validator() -> None:
    result = subprocess.run(
        [sys.executable, ".github/scripts/check_registry_foundation.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_registry_foundation_holds_only_reviewed_governance_registries() -> None:
    # No implementation instance is migrated here; the only governance-owned
    # registry is the candidate Project Anatomy relation profile architecture@1.
    business_registries = sorted(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "registries").rglob("*.registry.json")
    )
    assert business_registries == ["registries/architecture_relation_profile.registry.json"]


def test_fictional_registry_descriptor_validates() -> None:
    schema = yaml.safe_load((ROOT / "schemas/registry.schema.yaml").read_text(encoding="utf-8"))
    example = json.loads(
        (ROOT / "schemas/examples/registry.example.json").read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(example, schema)


def test_readme_acknowledges_existing_mvp_registries_and_tag_pilot() -> None:
    readme = (ROOT / "registries/README.md").read_text(encoding="utf-8")
    assert "tag_registry.json" in readme
    assert "navigation_registry.json" in readme
    assert "status label registry != canonical lifecycle" in readme
    assert "descriptor versus specialized schema" in readme.lower()
