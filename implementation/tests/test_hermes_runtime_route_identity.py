from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "mvp_vertical" / "hermes_execution_api.py"


STABLE_RUNTIME_ROUTES = {
    "/hermes/execution-admissions/{admission_id}",
    "/hermes/execution-admissions/{admission_id}/launch-reservations",
    "/hermes/execution-admissions/{admission_id}/runs/start",
    "/hermes/execution-admissions/{admission_id}/runs/{run_id}/context",
    "/hermes/execution-admissions/{admission_id}/runs/{run_id}/context/entities/{entity_type}/{entity_id}",
    "/hermes/execution-admissions/{admission_id}/active-context",
    "/hermes/execution-admissions/{admission_id}/active-context/entities/{entity_type}/{entity_id}",
    "/hermes/execution-admissions/{admission_id}/runs/{run_id}/return",
}


def test_runtime_api_parses_and_uses_stable_routes_without_aliases() -> None:
    source = API.read_text(encoding="utf-8")
    ast.parse(source)

    for route in STABLE_RUNTIME_ROUTES:
        assert route in source
        assert f"/v1{route}" not in source


def test_runtime_boundary_remains_external_and_bounded() -> None:
    source = API.read_text(encoding="utf-8")

    assert "require_hermes_key" in source
    assert "require_hermes_actor" in source
    assert "reserve_launch" in source
    assert "record_external_runtime_start" in source
    assert "get_context_manifest" in source
    assert "get_active_context_manifest" in source
    assert "record_external_runtime_return" in source

    assert "scheduler" in source
    assert "queue" in source
    assert "provider routing" in source
    assert "pending-work listing" in source


def test_project_change_candidate_route_is_stable_and_still_separate() -> None:
    project_api = (
        ROOT / "mvp_vertical" / "hermes_project_change_candidate_api.py"
    ).read_text(encoding="utf-8")

    route = (
        "/hermes/execution-admissions/{admission_id}/projects/{project_id}/change-candidates"
    )
    assert route in project_api
    assert f"/v1{route}" not in project_api
    assert "project_mutated" in project_api
    assert "human_apply_required" in project_api
    assert "runtime authority != human apply authority" in project_api
