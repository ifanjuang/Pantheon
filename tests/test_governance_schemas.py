"""Read-only tests for Pantheon Next governance schemas.

These tests validate declarative schema structure and fictional examples only.
They must not execute workflows, call tools, mutate memory, approve outputs, or
interact with OpenWebUI/Hermes runtime surfaces.
"""

from __future__ import annotations

from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
EXAMPLES = SCHEMAS / "examples"

SCHEMA_TO_EXAMPLE = {
    "document_knowledge_slice.schema.yaml": "document_knowledge_slice.example.yaml",
    "work_issue_slice.schema.yaml": "work_issue_slice.example.yaml",
    "task_contract.schema.yaml": "task_contract.example.yaml",
    "task_contract_revision.schema.yaml": "task_contract_revision.example.yaml",
    "evidence_pack.schema.yaml": "evidence_pack.example.yaml",
    "register_candidate.schema.yaml": "register_candidate.example.yaml",
    "register_link.schema.yaml": "register_link.example.yaml",
    "project_claim.schema.yaml": "project_claim.example.yaml",
    "impact_review.schema.yaml": "impact_review.example.yaml",
    "answer_status.schema.yaml": "answer_status.example.yaml",
    "policy_decision.schema.yaml": "policy_decision.example.yaml",
    "capability_passport.schema.yaml": "capability_passport.example.yaml",
    "module_manifest.schema.yaml": "module_manifest.example.yaml",
    "shared_axes.schema.yaml": "shared_axes.example.yaml",
    "mvp_governed_loop_objects.schema.yaml": "mvp_governed_loop_objects.example.yaml",
    "architecture-proof-register/shared.schema.yaml": "architecture-proof-register/shared.example.yaml",
    "architecture-proof-register/document_family.schema.yaml": "architecture-proof-register/document_family.example.yaml",
    "architecture-proof-register/indexed_document_version.schema.yaml": "architecture-proof-register/indexed_document_version.example.yaml",
    "architecture-proof-register/version_event.schema.yaml": "architecture-proof-register/version_event.example.yaml",
    "architecture-proof-register/proof_entry.schema.yaml": "architecture-proof-register/proof_entry.example.yaml",
    "architecture-proof-register/review_trigger.schema.yaml": "architecture-proof-register/review_trigger.example.yaml",
    "architecture-project-understanding/shared.schema.yaml": "architecture-project-understanding/shared.example.yaml",
    "architecture-project-understanding/stable_object.schema.yaml": "architecture-project-understanding/stable_object.example.yaml",
    "architecture-project-understanding/attribute_claim.schema.yaml": "architecture-project-understanding/attribute_claim.example.yaml",
    "architecture-project-understanding/calibration.schema.yaml": "architecture-project-understanding/calibration.example.yaml",
    "architecture-project-understanding/derivation.schema.yaml": "architecture-project-understanding/derivation.example.yaml",
    "architecture-project-understanding/contradiction.schema.yaml": "architecture-project-understanding/contradiction.example.yaml",
    "architecture-project-understanding/program.schema.yaml": "architecture-project-understanding/program.example.yaml",
    "architecture-project-understanding/requirement.schema.yaml": "architecture-project-understanding/requirement.example.yaml",
    "architecture-project-understanding/classification_scheme.schema.yaml": "architecture-project-understanding/classification_scheme.example.yaml",
    "architecture-project-understanding/observation_bundle.schema.yaml": "architecture-project-understanding/observation_bundle.example.yaml",
    "role_signal.schema.yaml": "role_signal.example.yaml",
    "workflow_manifest.schema.yaml": "workflow_manifest.example.yaml",
    "skill_manifest.schema.yaml": "skill_manifest.example.yaml",
    "context_pack.schema.yaml": "context_pack.example.yaml",
}

FORBIDDEN_SCHEMA_TERMS = {
    "athena-agent",
    "argos-agent",
    "themis-agent",
    "apollo-agent",
    "zeus-agent",
    "iris-agent",
    "hephaistos-agent",
    "mnemosyne-agent",
    "HEPHAESTUS",
    "hephaestus-agent",
}

BOUNDARY_MARKERS = {
    "runtime_execution: false",
    "provider_routing: false",
    "memory_promotion: false",
}


def test_schema_and_example_files_exist() -> None:
    """Every governed schema should have a fictional example fixture."""

    assert SCHEMAS.exists(), "schemas/ directory is missing"
    assert EXAMPLES.exists(), "schemas/examples/ directory is missing"

    for schema_name, example_name in SCHEMA_TO_EXAMPLE.items():
        assert (SCHEMAS / schema_name).is_file(), f"missing schema: {schema_name}"
        assert (EXAMPLES / example_name).is_file(), f"missing example: {example_name}"


def test_schema_files_keep_non_runtime_boundaries() -> None:
    """Schemas must remain validation contracts, not runtime declarations."""

    for schema_name in SCHEMA_TO_EXAMPLE:
        text = (SCHEMAS / schema_name).read_text(encoding="utf-8")

        assert "x-boundary:" in text, f"missing x-boundary in {schema_name}"
        assert "runtime_execution: false" in text, f"runtime boundary missing in {schema_name}"

        if schema_name != "context_pack.schema.yaml":
            assert any(marker in text for marker in BOUNDARY_MARKERS), (
                f"expected at least one core anti-runtime marker in {schema_name}"
            )

        for forbidden in FORBIDDEN_SCHEMA_TERMS:
            assert forbidden not in text, f"non-canonical term {forbidden!r} in {schema_name}"


def test_schema_readme_records_validation_only_boundary() -> None:
    """The schema index should state the validation-only boundary explicitly."""

    readme = (SCHEMAS / "README.md").read_text(encoding="utf-8")

    assert "Status: implemented validation baseline — D3 reconciliation pending" in readme
    assert "module_manifest.schema.yaml" in readme
    assert "context_pack.schema.yaml" in readme
    assert "Schemas are validation contracts." in readme
    assert "runtime components" in readme
    assert "provider routers" in readme
    assert "memory promotion engines" in readme
    assert "workflow engines" in readme
    assert "tool routers" in readme
    assert "schedulers" in readme
    assert "queues" in readme


def test_schema_governance_refs_point_to_existing_docs() -> None:
    """Schema governance references should resolve to repository files when local."""

    for schema_name in SCHEMA_TO_EXAMPLE:
        schema = yaml.safe_load((SCHEMAS / schema_name).read_text(encoding="utf-8"))
        refs = schema.get("properties", {}).get("governance_refs", {}).get("default", [])

        assert refs, f"governance_refs default is missing in {schema_name}"

        for ref in refs:
            if ref.startswith("docs/") or ref.startswith("schemas/"):
                assert (ROOT / ref).exists(), f"broken governance ref in {schema_name}: {ref}"


def _family_registry():
    """Registry exposing each family's shared.schema.yaml under its bare filename,
    so factored cross-file ``$ref: "shared.schema.yaml#/$defs/X"`` resolves.
    Schemas that do not use cross-file refs simply ignore it."""

    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012

    shared = SCHEMAS / "architecture-project-understanding" / "shared.schema.yaml"
    registry = Registry()
    for name in (
        "shared.schema.yaml",
        "source_representation.schema.yaml",
        "attribute_claim.schema.yaml",
        "relation_claim.schema.yaml",
    ):
        content = yaml.safe_load(
            (SCHEMAS / "architecture-project-understanding" / name).read_text(
                encoding="utf-8"
            )
        )
        resource = Resource.from_contents(
            content,
            default_specification=DRAFT202012,
        )
        registry = registry.with_resource(uri=name, resource=resource)
    return registry


def test_examples_validate_against_schemas() -> None:
    """Validate fictional examples against their schemas; dependencies are required."""

    validator_cls = jsonschema.Draft202012Validator
    format_checker = jsonschema.FormatChecker()
    registry = _family_registry()

    for schema_name, example_name in SCHEMA_TO_EXAMPLE.items():
        schema = yaml.safe_load((SCHEMAS / schema_name).read_text(encoding="utf-8"))
        example = yaml.safe_load((EXAMPLES / example_name).read_text(encoding="utf-8"))

        validator_cls.check_schema(schema)
        validator = validator_cls(schema, format_checker=format_checker, registry=registry)
        errors = sorted(validator.iter_errors(example), key=lambda error: list(error.path))

        assert not errors, _format_validation_errors(schema_name, example_name, errors)


def _format_validation_errors(schema_name: str, example_name: str, errors: list[object]) -> str:
    lines = [f"{example_name} failed validation against {schema_name}:"]

    for error in errors[:10]:
        path = ".".join(str(part) for part in getattr(error, "path", [])) or "<root>"
        lines.append(f"- {path}: {getattr(error, 'message', error)}")

    if len(errors) > 10:
        lines.append(f"- ... {len(errors) - 10} additional errors")

    return "\n".join(lines)
