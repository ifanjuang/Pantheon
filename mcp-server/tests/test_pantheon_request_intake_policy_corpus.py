from pathlib import Path

import yaml

from pantheon_mcp import policy


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "hermes_request_intake_policy_cases.yaml"


def test_semantic_intake_candidates_project_through_existing_policy() -> None:
    cases = yaml.safe_load(FIXTURES.read_text(encoding="utf-8"))["cases"]

    for case in cases:
        report = policy.classify_request(case["request"])
        expected = case["expected"]
        handling = report["handling"]

        if "consequence_level" in expected:
            assert report["consequence_level"] == expected["consequence_level"], case["id"]
        assert handling["disposition"] == expected["disposition"], case["id"]

        topology = expected.get("topology")
        if topology is None:
            assert "topology" not in handling, case["id"]
        else:
            assert handling["topology"]["suggested"] == topology, case["id"]

        if "rite_candidate" in expected:
            assert handling["rite_candidate"] == expected["rite_candidate"], case["id"]
