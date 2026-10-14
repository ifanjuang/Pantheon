from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import yaml

from mvp_vertical import pantheon_contracts


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = REPO_ROOT / "schemas"
RUNTIME_ROOT = REPO_ROOT / "implementation" / "mvp_vertical"


def _refs(value):
    if isinstance(value, dict):
        ref = value.get("$ref")
        if isinstance(ref, str):
            yield ref
        for child in value.values():
            yield from _refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from _refs(child)


def test_declared_contracts_resolve_from_canonical_root() -> None:
    for name, relative in pantheon_contracts.CONTRACT_PATHS.items():
        expected = (REPO_ROOT / relative).resolve()
        actual = pantheon_contracts.schema_path(name).resolve()
        assert actual == expected
        source = pantheon_contracts.provenance(name)
        assert source["source_path"] == relative
        assert source["posture"] == "canonical-repository"
        assert source["authority_transfer"] is False


def test_registry_indexes_complete_schema_tree_not_only_direct_contracts() -> None:
    paths = pantheon_contracts._all_schema_paths()
    assert paths
    assert len(paths) >= len(pantheon_contracts.CONTRACT_PATHS)
    assert all(path.is_relative_to(SCHEMA_ROOT) for path in paths)


def test_every_local_schema_ref_resolves_inside_canonical_tree() -> None:
    schema_root = SCHEMA_ROOT.resolve()
    missing: list[str] = []
    escaped: list[str] = []
    for schema_path in sorted(SCHEMA_ROOT.rglob("*.schema.yaml")):
        document = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
        for ref in _refs(document):
            target = ref.split("#", 1)[0]
            if not target:
                continue
            parsed = urlparse(target)
            if parsed.scheme:
                continue
            resolved = (schema_path.parent / target).resolve()
            if not resolved.is_relative_to(schema_root):
                escaped.append(f"{schema_path.relative_to(SCHEMA_ROOT)} -> {ref}")
            elif not resolved.is_file():
                missing.append(f"{schema_path.relative_to(SCHEMA_ROOT)} -> {ref}")
    assert not escaped, "schema refs escape schemas/: " + "; ".join(escaped)
    assert not missing, "schema refs target missing files: " + "; ".join(missing)


def test_runtime_does_not_reconstruct_retired_vendor_schema_paths() -> None:
    forbidden = (
        '"vendor" / "pantheon"',
        "'vendor' / 'pantheon'",
        "vendor/pantheon",
        "vendor_contracts",
    )
    stale: list[str] = []
    for path in sorted(RUNTIME_ROOT.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                stale.append(f"{path.relative_to(RUNTIME_ROOT)}: {token}")
    assert not stale, "retired vendor contract path reconstructed by runtime: " + "; ".join(stale)


def test_dirty_checkout_does_not_claim_head_as_exact_source_commit(monkeypatch) -> None:
    revision = "a" * 40
    monkeypatch.setattr(pantheon_contracts, "_repository_revision", lambda: revision)
    monkeypatch.setattr(
        pantheon_contracts,
        "_repository_file_matches_head",
        lambda _relative: False,
    )
    source = pantheon_contracts.provenance("project_claim")
    assert source["repository_revision"] == revision
    assert source["source_commit"] is None
    assert source["working_tree_dirty"] is True
