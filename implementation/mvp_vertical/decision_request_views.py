"""Read projections for Decision Requests.

The global Decisions space is not an agency-level Decision owner. It contains
only pending requests that have not been classified into a Project. Project
views continue to read the same request identities through their ``project_id``.
"""

from __future__ import annotations

from typing import Any

import psycopg

from . import decision_requests


def list_unclassified_requests(
    conn: psycopg.Connection,
    *,
    status: str | None = "pending",
    limit: int = 100,
) -> list[dict[str, Any]]:
    if status not in {None, "pending", "resolved", "cancelled"}:
        raise decision_requests.DecisionRequestError(
            f"unsupported Decision Request status: {status!r}"
        )
    if limit < 1 or limit > 500:
        raise decision_requests.DecisionRequestError("limit must be between 1 and 500")

    filters = ["project_id IS NULL"]
    params: list[Any] = []
    if status is not None:
        filters.append("status = %s")
        params.append(status)
    params.append(limit)

    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT request_id
              FROM agency_decision_requests
             WHERE {' AND '.join(filters)}
             ORDER BY
                   CASE priority
                       WHEN 'urgent' THEN 0
                       WHEN 'high' THEN 1
                       WHEN 'normal' THEN 2
                       WHEN 'low' THEN 3
                       ELSE 99
                   END,
                   created_at,
                   request_id
             LIMIT %s
            """,
            tuple(params),
        )
        request_ids = [row[0] for row in cur.fetchall()]

    return [decision_requests.get_request(conn, request_id) for request_id in request_ids]
