"""H5.4 IFC cross-source conflict remains source-scoped and candidate-only."""

from pathlib import Path
from typing import Any

import jsonschema
import yaml
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas" / "architecture-project-understanding"
EXAMPLE = ROOT / "schemas" / "examples" / "architecture-project-understanding" / "ifc_cross_source_conflict.example.yaml"


def _load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_ifc_cross_source_conflict_is_valid_but_unresolved_and_non_authoritative() -> None:
    registry = Registry()
    for name in (
        "shared.schema.yaml",
        "source_representation.schema.yaml",
        "attribute_claim.schema.yaml",
        "relation_claim.schema.yaml",
    ):
        registry = registry.with_resource(
            uri=name,
            resource=Resource.from_contents(_load(SCHEMAS / name), default_specification=DRAFT202012),
        )
    bundle = _load(EXAMPLE)
    validator = jsonschema.Draft202012Validator(
        _load(SCHEMAS / "observation_bundle.schema.yaml"),
        format_checker=jsonschema.FormatChecker(),
        registry=registry,
    )
    validator.validate(bundle)

    assert set(bundle["authority"].values()) == {False}
    assert len(bundle["source_representations"]) == 2
    assert {item["source_kind"] for item in bundle["source_representations"]} == {"ifc", "other"}
    claims = bundle["attribute_claim_candidates"]
    assert [item["value"]["value"] for item in claims] == ["EI30", "EI60"]
    assert len({tuple(item["source_representation_refs"]) for item in claims}) == 2
    assert bundle["relation_claim_candidates"] == []
    assert any(item["code"] == "conflict.source_scoped_unresolved" for item in bundle["warnings"])
    assert not any("accepted" in item["attribute_key"] for item in claims)
