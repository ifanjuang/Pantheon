from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = ROOT / "docs/governance/RUNTIME_REVIEW_MODEL_PASSPORT_VALIDATION_PROMOTION.md"

TEMPLATES = (
    ROOT / "templates/external_runtime_review_candidate.yaml",
    ROOT / "templates/model_capability_passport_candidate.yaml",
    ROOT / "templates/validation_report_candidate.yaml",
)

ABSENT_SCHEMAS = (
    ROOT / "schemas/external_runtime_review_candidate.schema.yaml",
    ROOT / "schemas/model_capability_passport_candidate.schema.yaml",
    ROOT / "schemas/validation_report_candidate.schema.yaml",
)


def test_templates_exist_but_protected_validation_is_not_claimed() -> None:
    text = PROPOSAL.read_text(encoding="utf-8")

    for template in TEMPLATES:
        assert template.is_file(), template

    for schema in ABSENT_SCHEMAS:
        assert not schema.exists(), schema

    assert "implementation partial" in text
    assert "human-fillable templates present" in text
    assert "no dedicated schemas for these three candidate objects" in text
    assert "no schema-backed/read-only validation tests or validator" in text
    assert "no MCP validation functions" in text

    # Templates are scaffolds, not proof that the proposed validation layer exists.
    assert "Templates are not schemas and not validators" in text
    assert "Their existence does not authorize the protected validation step" in text


def test_proposed_mcp_validation_functions_remain_proposal_only() -> None:
    text = PROPOSAL.read_text(encoding="utf-8")

    for function_name in (
        "validate_external_runtime_review",
        "validate_model_capability_passport",
        "classify_runtime_review_gate",
        "classify_model_passport_gate",
    ):
        assert function_name in text

    assert "no such functions currently exist in the repository" in text
