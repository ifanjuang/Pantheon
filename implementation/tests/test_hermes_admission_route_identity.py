from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "mvp_vertical" / "hermes_execution_api.py"
CLIENT = ROOT / "mvp_vertical" / "cockpit" / "handoff" / "handoff_lifecycle.js"


STABLE_COCKPIT_ROUTES = {
    "/cockpit/hermes-handoffs/{handoff_id}/admissions",
    "/cockpit/hermes-execution-admissions/{admission_id}",
    "/cockpit/hermes-execution-admissions/{admission_id}/revocations",
}

RETIRED_COCKPIT_ROUTES = {
    "/v1/cockpit/hermes-handoffs/{handoff_id}/admissions",
    "/v1/cockpit/hermes-execution-admissions/{admission_id}",
    "/v1/cockpit/hermes-execution-admissions/{admission_id}/revocations",
}


def test_admission_api_parses_and_uses_only_stable_cockpit_routes() -> None:
    source = API.read_text(encoding="utf-8")
    ast.parse(source)

    for route in STABLE_COCKPIT_ROUTES:
        assert route in source
    for route in RETIRED_COCKPIT_ROUTES:
        assert route not in source


def test_cockpit_calls_stable_admission_routes_without_runtime_dispatch() -> None:
    client = CLIENT.read_text(encoding="utf-8")

    assert "../cockpit/hermes-handoffs/" in client
    assert "/admissions`" in client
    assert "../cockpit/hermes-execution-admissions/" in client
    assert "/revocations`" in client
    assert "../v1/cockpit/hermes-handoffs/" not in client
    assert "../v1/cockpit/hermes-execution-admissions/" not in client

    assert "/runs/start" not in client
    assert "/v1/hermes/execution-admissions" not in client
    assert "Pantheon n’a pas lancé Hermes" in client
    assert "sans scheduler" in client


def test_runtime_routes_are_stable_and_remain_separate_from_cockpit() -> None:
    source = API.read_text(encoding="utf-8")

    runtime_routes = {
        "/hermes/execution-admissions/{admission_id}",
        "/hermes/execution-admissions/{admission_id}/launch-reservations",
        "/hermes/execution-admissions/{admission_id}/runs/start",
        "/hermes/execution-admissions/{admission_id}/runs/{run_id}/context",
        "/hermes/execution-admissions/{admission_id}/runs/{run_id}/return",
    }
    for route in runtime_routes:
        assert route in source
        assert f"/v1{route}" not in source
