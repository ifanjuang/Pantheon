from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/professional_review_private_source_patterns.yaml"


def _fixture() -> dict:
    value = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _patterns_by_id() -> dict[str, dict]:
    fixture = _fixture()
    return {pattern["pattern_id"]: pattern for pattern in fixture["patterns"]}


def test_private_source_patterns_retain_no_private_source_material() -> None:
    fixture = _fixture()
    posture = fixture["source_posture"]
    assert posture == {
        "private_sources_retained": False,
        "source_content_retained": False,
        "raw_extraction_retained": False,
        "identifying_metadata_retained": False,
        "original_file_names_retained": False,
        "exact_digests_retained": False,
        "original_dates_retained": False,
        "original_amounts_retained": False,
        "original_geometry_retained": False,
        "sufficient_to_reconstruct_private_source": False,
    }

    text = FIXTURE.read_text(encoding="utf-8")
    lowered = text.casefold()
    assert not re.search(r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b", lowered)
    assert not re.search(r"\b[0-9a-f]{64}\b", lowered)
    assert not re.search(r"\bfr\d{2}(?:\s?\d){10,}\b", lowered)
    assert not re.search(r"(?m)(?<![\w:])/(?:[^/\s]+/)+[^/\s]+", text)
    assert not re.search(r"(?i)\b[a-z]:\\(?:[^\\\r\n]+\\)*[^\\\r\n]+", text)
    assert "file://" not in lowered
    assert ".pdf" not in lowered
    assert ".docx" not in lowered
    assert ".xlsx" not in lowered
    assert "€" not in text


def test_private_source_patterns_are_non_authoritative_companions() -> None:
    fixture = _fixture()
    assert fixture["role"] == "companion_to_synthetic_oracle"
    assert fixture["companion_oracle_ref"] == (
        "implementation/tests/fixtures/professional_quote_review_cases.yaml"
    )
    assert fixture["authority"] == {
        "is_fact": False,
        "is_evidence": False,
        "is_decision": False,
        "is_memory": False,
        "authorizes_external_effect": False,
    }

    patterns = fixture["patterns"]
    pattern_ids = [pattern["pattern_id"] for pattern in patterns]
    assert len(pattern_ids) == len(set(pattern_ids))
    for pattern in patterns:
        assert pattern["failure_layer"]
        assert pattern["observed_shape"]
        assert pattern["expected_system_posture"]
        assert pattern["forbidden_inferences"]


def test_currentness_conflict_routes_to_existing_currentness_owner() -> None:
    pattern = _patterns_by_id()["cross_document_revision_conflict"]
    assert pattern["observed_shape"]["authority_between_documents_resolved"] is False
    assert "project_document_currentness" in pattern["existing_owner_route"]
    assert (
        "a later revision label alone establishes contractual truth"
        in pattern["forbidden_inferences"]
    )


def test_foreign_source_treatment_depends_on_explicit_task_intent_without_relabeling() -> None:
    pattern = _patterns_by_id()["foreign_quote_semantic_near_match"]
    intents = pattern["intent_cases"]
    assert intents["accidental_same_project_review"]["treatment"] == (
        "exclude_foreign_source_from_same_project_review"
    )
    assert intents["explicit_cross_project_benchmark"]["treatment"] == (
        "allow_bounded_comparison_without_relabeling_source"
    )
    assert (
        "an explicit benchmark request changes the source's governed identity"
        in pattern["forbidden_inferences"]
    )


def test_missing_reference_quantity_remains_insufficient_evidence() -> None:
    pattern = _patterns_by_id()["prescribed_item_without_reference_quantity"]
    assert pattern["expected_posture"] == "requires_more_evidence"
    assert pattern["observed_shape"] == {
        "prescribed_item_identifiable": True,
        "reference_quantity_defined": False,
        "quote_quantity_present": True,
    }
    assert "the quoted quantity is too high" in pattern["forbidden_inferences"]
    assert "the quoted quantity is too low" in pattern["forbidden_inferences"]


def test_similarity_and_status_never_become_conformity_or_settled_base() -> None:
    patterns = _patterns_by_id()
    similarity = patterns["similar_product_without_equivalence_evidence"]
    assert similarity["expected_posture"] == "requires_more_evidence"
    assert "semantic similarity proves technical conformity" in similarity["forbidden_inferences"]

    statuses = patterns["unresolved_pricing_statuses"]
    assert statuses["observed_shape"]["status_vocabulary"] == [
        "base",
        "option",
        "to_confirm",
        "to_verify",
        "to_measure",
    ]
    assert "an option belongs to the base price by default" in statuses["forbidden_inferences"]
