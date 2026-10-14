from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MEASURE = ROOT / "tools" / "measure_cockpit_loader_requests.js"
LOADER = ROOT / "mvp_vertical" / "cockpit" / "data" / "cockpit_data_loader.js"


def measure() -> dict:
    completed = subprocess.run(
        ["node", str(MEASURE), str(LOADER)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_cockpit_loader_request_baseline_is_reproducible() -> None:
    result = measure()

    assert result["measurement"] == "cockpit_loader_request_count"
    assert result["scenario"] == (
        "project_list_plus_unclassified_decision_inbox_plus_three_schema_reads_plus_one_project_bundle"
    )
    assert result["total_requests"] == 11
    assert result["unique_paths"] == 11
    assert result["schema_requests"] == 1
    assert result["decision_inbox_requests"] == 2
    assert result["project_bundle_requests"] == 8


def test_measurement_reports_every_project_bundle_path() -> None:
    paths = measure()["requests_by_path"]

    assert paths["../agency/projects?limit=200"] == 1
    assert paths["../decision-inbox?status=pending&limit=200"] == 1
    assert paths["../agency/schema/project"] == 1
    assert paths["../agency/projects/project-measurement/information"] == 1
    assert paths["../projects/project-measurement/documents"] == 1
    assert paths["../projects/project-measurement/knowledge"] == 1
    assert paths["../agency/projects/project-measurement/project-anatomy"] == 1
    assert paths["../work/scopes/project/project-measurement/issues"] == 1
    assert paths[
        "../agency/projects/project-measurement/decision-requests?status=pending&limit=100"
    ] == 1
    assert paths[
        "../agency/projects/project-measurement/change-candidates?status=pending_review&limit=100"
    ] == 1
    assert paths[
        "../agency/projects/project-measurement/change-candidates?status=revision_requested&limit=100"
    ] == 1
