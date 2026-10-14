import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/source_research_evaluation_pilot.json"


def _pilot():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_source_research_pilot_has_exact_abc_provenance_and_representative_cases():
    pilot = _pilot()

    assert pilot["pilot_id"] == "source-research-governed-eval-001"
    assert pilot["capability"] == "source_research"
    assert pilot["execution_status"] == "blocked_missing_reproducible_runtime"

    variants = pilot["variants"]
    assert set(variants) == {"A", "B", "C"}
    assert variants["A"]["specialized_skill_loaded"] is False
    assert variants["B"]["commit"] == "80b2aa93365a84081ab114c31db2c11338dadc35"
    assert variants["B"]["blob_sha"] == "4c85fdf96af45d3de5065e6dafdce5d7f1368aa8"
    assert variants["C"]["commit"] == "47ae870d128ca101f6c07f0ba93bf20be8c3b70e"
    assert variants["C"]["blob_sha"] == "bb382bc8dff12c1b1c338dbef516b9536f7a5ff9"

    cases = pilot["cases"]
    assert len(cases) == 9
    assert {case["id"] for case in cases} == {
        "version_changed",
        "authority_derivative_disagreement",
        "citation_does_not_support_claim",
        "information_absent",
        "wrong_jurisdiction",
        "freshness_mismatch",
        "private_detail_not_needed",
        "broad_research_stop_condition",
        "challenge_supported_claim",
    }

    required_case_fields = {
        "id",
        "failure_mode",
        "input",
        "expected_posture",
        "required_observations",
        "forbidden_claims_or_effects",
        "human_label",
    }
    for case in cases:
        assert required_case_fields <= set(case)
        assert case["expected_posture"]
        assert case["required_observations"]
        assert case["forbidden_claims_or_effects"]
        assert case["human_label"]


def test_source_research_pilot_does_not_fake_behavioral_acceptance():
    pilot = _pilot()

    measures = set(pilot["measures"])
    assert {
        "supported_material_claims",
        "unsupported_material_claims",
        "material_contradictions_detected",
        "correct_refusals",
        "false_refusals",
        "scope_drift",
        "source_currentness_errors",
        "private_disclosure_boundary_errors",
    } <= measures

    blocker = pilot["execution_blocker"]
    assert "reproducible sandbox runtime" in blocker["missing_prerequisite"]
    assert "cannot establish behavioral quality" in blocker["why_repo_tests_are_insufficient"]
    assert "Do not treat this fixture" in blocker["forbidden_shortcut"]

    assert "observed_results" not in pilot
    assert "quality_score" not in pilot
