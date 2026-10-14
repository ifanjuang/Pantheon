"""Shared test fixtures.

CI honesty (external review, finding #11): the DB-gated tests skip when
pgvector is unreachable so that unit-only environments stay green. But in CI —
where pgvector is a required service and MVP_PG_DSN is set — an unreachable
database must be a loud FAILURE, not a silent skip. A skipped integration test
in CI is a test that lies about coverage:

    runtime_success != evidence

So when MVP_PG_DSN is set, this asserts pgvector is reachable once at session
start and fails the whole run if it is not. Locally (no MVP_PG_DSN) it is a
no-op and the per-test fixtures skip exactly as before.
"""

from __future__ import annotations

import os

import pytest

from mvp_vertical import store


@pytest.fixture(scope="session", autouse=True)
def _require_pgvector_when_configured():
    dsn = os.environ.get("MVP_PG_DSN")
    if not dsn:
        return  # unit-only environment: the per-test fixtures skip DB tests
    try:
        store.connect().close()
    except Exception as exc:  # noqa: BLE001 - any connection failure is fatal here
        pytest.fail(
            "MVP_PG_DSN is set but pgvector is unreachable — a skipped "
            f"integration test would hide a broken cage: {exc}",
            pytrace=False,
        )
