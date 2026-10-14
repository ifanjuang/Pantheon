from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/hermes_request_intake_cases.yaml"


def _cases() -> dict[str, dict]:
    data = yaml.safe_load(FIXTURES.read_text(encoding="utf-8"))
    return {case["id"]: case["expected"] for case in data["cases"]}


def test_harmless_transformations_do_not_inherit_risk_from_subject_words() -> None:
    cases = _cases()

    assert cases["harmless_rewrite"]["conditions"] == []
    assert "source_required" in cases["harmless_rewrite"]["forbidden_conditions"]

    contract_format = cases["format_contract_text_without_review"]
    assert contract_format["requested_transformation"] == "formatting"
    assert contract_format["conditions"] == []
    assert "legal_or_professional_risk" in contract_format["forbidden_conditions"]


def test_material_effects_and_reuse_are_not_silently_weakened() -> None:
    cases = _cases()

    assert {"external_transmission", "client_delivery", "external_effect"} <= set(
        cases["send_client_message"]["conditions"]
    )
    assert {"memory_candidate", "memory_promotion", "approval_required"} <= set(
        cases["remember_as_canonical"]["conditions"]
    )
    assert {"memory_recall_requested", "prior_decision_reuse", "project_history_reuse"} <= set(
        cases["prior_decision_recall"]["conditions"]
    )


def test_coordination_is_expressed_as_relations_not_domain_recipes() -> None:
    cases = _cases()

    assert cases["current_product_comparison"]["coordination"] == {
        "independent": True,
        "synthesize": True,
    }
    assert cases["software_diagnosis"]["coordination"]["repeat_until"] == ["tests_pass"]
    assert cases["conditional_future_action"]["coordination"]["branch_on"] == ["control_result"]
    assert cases["verify_contract_claim"]["coordination"]["requires"] is True
