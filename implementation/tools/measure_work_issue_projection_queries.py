"""Measure SQL executions for one bounded Work Issue Cockpit projection.

This is a deterministic performance probe, not an application endpoint. It creates
three isolated Work Issues, resets the counter and measures only
``work_issue_read.list_issue_projections``.
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any

from mvp_vertical import work_issue_read, work_issues


class CountingCursor:
    def __init__(self, inner: Any, owner: "CountingConnection") -> None:
        self._inner = inner
        self._owner = owner

    def __enter__(self) -> "CountingCursor":
        self._inner.__enter__()
        return self

    def __exit__(self, exc_type, exc, traceback) -> Any:
        return self._inner.__exit__(exc_type, exc, traceback)

    def execute(self, query: Any, params: Any = None) -> Any:
        self._owner.query_count += 1
        if params is None:
            return self._inner.execute(query)
        return self._inner.execute(query, params)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


class CountingConnection:
    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.query_count = 0

    def cursor(self, *args: Any, **kwargs: Any) -> CountingCursor:
        return CountingCursor(self._inner.cursor(*args, **kwargs), self)

    def execute(self, query: Any, params: Any = None) -> Any:
        self.query_count += 1
        if params is None:
            return self._inner.execute(query)
        return self._inner.execute(query, params)

    def transaction(self, *args: Any, **kwargs: Any) -> Any:
        return self._inner.transaction(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _truncate(connection: Any) -> None:
    connection.execute(
        "TRUNCATE issue_events, hermes_runs, issue_comments, work_issues "
        "RESTART IDENTITY CASCADE"
    )
    connection.commit()


def measure(*, issue_count: int = 3) -> dict[str, Any]:
    if issue_count < 1:
        raise ValueError("issue_count must be positive")

    connection = work_issues.connect(os.getenv("MVP_PG_DSN"))
    case_ref = _id("query-baseline")
    try:
        _truncate(connection)
        for index in range(issue_count):
            work_issues.create_issue(
                connection,
                issue_id=_id("issue"),
                case_ref=case_ref,
                title=f"Measured Work Issue {index + 1}",
                description="Measure the bounded Cockpit read path without changing its semantics.",
                created_by="performance-measurement",
                idempotency_key=_id("create"),
            )

        counted = CountingConnection(connection)
        projections = work_issue_read.list_issue_projections(counted, case_ref)
        return {
            "measurement": "work_issue_projection_sql_query_count",
            "scenario": "list_three_empty_work_issue_aggregates_with_card_metadata",
            "issue_count": issue_count,
            "projection_count": len(projections),
            "sql_queries": counted.query_count,
            "query_strategy": "constant_batch_for_non_empty_case",
            "expected_current_formula": "5",
        }
    finally:
        try:
            _truncate(connection)
        finally:
            connection.close()


def main() -> None:
    print(json.dumps(measure(), sort_keys=True))


if __name__ == "__main__":
    main()
