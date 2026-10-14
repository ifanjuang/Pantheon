"""H5.6 multi-source identity review qualification."""

from pathlib import Path
from typing import Any

import jsonschema
import yaml
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas" / "architecture-project-understanding"
CORPUS = (
    ROOT
    / "schemas"
    / "examples"
    / "architecture-project-understanding"
    / "multi_source_identity_review_corpus.yaml"
)


def _load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _registry() -> Registry:
    registry = Registry()
    for name in (
        "shared.schema.yaml",
        "source_representation.schema.yaml",
        "attribute_claim.schema.yaml",
        "relation_claim.schema.yaml",
    ):
        registry = registry.with_resource(
            uri=name,
            resource=Resource.from_contents(
                _load(SCHEMAS / name),
                default_specification=DRAFT202012,
            ),
        )
    return registry


def test_h5_6_bundle_and_each_targeted_review_validate() -> None:
    corpus = _load(CORPUS)
    bundle = corpus["observation_bundle"]
    observation_validator = jsonschema.Draft202012Validator(
        _load(SCHEMAS / "observation_bundle.schema.yaml"),
        format_checker=jsonschema.FormatChecker(),
        registry=_registry(),
    )
    observation_validator.validate(bundle)

    review_validator = jsonschema.Draft202012Validator(
        _load(SCHEMAS / "mapping_review.schema.yaml"),
        format_checker=jsonschema.FormatChecker(),
    )
    for review in corpus["reviews"]:
        review_validator.validate(review)


def test_h5_6_reviews_are_independent_and_do_not_choose_attribute_truth() -> None:
    corpus = _load(CORPUS)
    bundle = corpus["observation_bundle"]
    reviews = corpus["reviews"]

    assert {item["source_kind"] for item in bundle["source_representations"]} == {
        "drawing",
        "ifc",
        "revit",
    }
    relations = {
        item["relation_claim_id"]: item for item in bundle["relation_claim_candidates"]
    }
    assert len(relations) == 3
    assert {item["object_ref"]["entity_id"] for item in relations.values()} == {
        "OBJ-DOOR-017"
    }
    assert all(item["proof_status"] == "candidate" for item in relations.values())
    assert all(item["assertion_mode"] == "proposed" for item in relations.values())

    actions = {review["mapping_ref"]: review["action"] for review in reviews}
    assert actions == {
        "identity.pdf.p12.obj-door-017": "select_existing_object",
        "identity.ifc.door-a.obj-door-017": "reject_mapping",
        "identity.revit.door-a.obj-door-017": "needs_clarification",
    }
    assert set(actions) == set(relations)
    assert all(set(review["authority"].values()) == {False} for review in reviews)

    values = [claim["value"]["value"] for claim in bundle["attribute_claim_candidates"]]
    assert values == [0.90, 0.93, 0.93]
    assert all(claim["proof_status"] == "candidate" for claim in bundle["attribute_claim_candidates"])
    assert all("accepted" not in claim["attribute_key"] for claim in bundle["attribute_claim_candidates"])
    assert any(item["code"] == "conflict.attribute_values_source_scoped" for item in bundle["warnings"])


def test_h5_6_mapping_review_semantics_reuse_existing_owner_without_new_result_kind() -> None:
    corpus = _load(CORPUS)
    assert corpus["status"] == "qualification_only"
    schema = _load(SCHEMAS / "mapping_review.schema.yaml")
    description = schema["description"]
    assert "Observation Bundle" in description
    mapping_ref_description = schema["properties"]["mapping_ref"]["description"]
    assert "relation_claim_id" in mapping_ref_description
    assert (
        "schemas/architecture-project-understanding/observation_bundle.schema.yaml"
        in schema["governance_refs"]["default"]
    )

    # H5.6 reuses the existing mapping review/write owners. It does not add a
    # second result kind or a resolver authority to the canonical bundle.
    bundle = corpus["observation_bundle"]
    assert set(bundle["authority"].values()) == {False}
    assert all(review["mapping_result_ref"] == "result.h56.observation-bundle" for review in corpus["reviews"])
