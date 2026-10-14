from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


IMPLEMENTATION_ROOT = Path(__file__).resolve().parents[1]
PROBE = IMPLEMENTATION_ROOT / "tools" / "measure_work_issue_projection_queries.py"


def test_work_issue_projection_query_baseline() -> None:
    if not os.getenv("MVP_PG_DSN"):
        pytest.skip("PostgreSQL DSN not configured for performance probe")

    completed = subprocess.run(
        [sys.executable, str(PROBE)],
        cwd=IMPLEMENTATION_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout.strip())

    assert result == {
        "measurement": "work_issue_projection_sql_query_count",
        "scenario": "list_three_empty_work_issue_aggregates_with_card_metadata",
        "issue_count": 3,
        "projection_count": 3,
        "sql_queries": 5,
        "query_strategy": "constant_batch_for_non_empty_case",
        "expected_current_formula": "5",
    }
