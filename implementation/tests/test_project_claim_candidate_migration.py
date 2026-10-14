from __future__ import annotations

import psycopg
import pytest

from mvp_vertical import agency_claims, agency_data, execution_results


EXPECTED_VALIDATED_CONSTRAINTS = {
    "execution_result_items_result_kind_check",
    "execution_result_review_dispositions_disposition_check",
    "agency_project_claims_certainty_check",
    "agency_project_claims_source_kind_check",
    "agency_project_claims_candidate_identity_check",
    "agency_project_claims_execution_source_check",
    "agency_project_claims_candidate_execution_fk",
    "agency_project_claims_candidate_result_fk",
    "agency_project_claims_candidate_disposition_fk",
    "agency_project_claims_basis_refs_array_check",
    "agency_project_claims_basis_refs_source_check",
}


@pytest.fixture
def migrated_conn():
    try:
        conn = agency_data.connect()
    except Exception as exc:  # pragma: no cover - unit-only environment
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    try:
        # agency_data.connect() deliberately runs the Claim migration before the
        # execution-result owner exists. The composed replay must then install
        # and validate the three provenance foreign keys, followed by the
        # structured-basis extension of the same Claim owner.
        execution_results.ensure_schema(conn)
        conn.execute(agency_claims.MIGRATION.read_text(encoding="utf-8"))
        conn.execute(agency_claims.PROVENANCE_MIGRATION.read_text(encoding="utf-8"))
        conn.commit()
        yield conn
    finally:
        conn.close()


def _constraint_state(conn) -> dict[str, tuple[bool, str]]:
    rows = conn.execute(
        """
        SELECT conname, convalidated, pg_get_constraintdef(oid)
          FROM pg_constraint
         WHERE conname = ANY(%s)
        """,
        (sorted(EXPECTED_VALIDATED_CONSTRAINTS),),
    ).fetchall()
    return {name: (validated, definition) for name, validated, definition in rows}


def test_candidate_constraints_are_present_and_validated(migrated_conn) -> None:
    state = _constraint_state(migrated_conn)
    assert set(state) == EXPECTED_VALIDATED_CONSTRAINTS
    assert all(validated for validated, _definition in state.values())
    assert "project_claim_candidate" in state[
        "execution_result_items_result_kind_check"
    ][1]
    assert "accepted_for_claim" in state[
        "execution_result_review_dispositions_disposition_check"
    ][1]
    assert "execution_result" in state["agency_project_claims_source_kind_check"][1]
    assert "execution_result" in state[
        "agency_project_claims_basis_refs_source_check"
    ][1]


def test_partial_source_kind_state_is_repaired_by_exact_constraint_name(
    migrated_conn,
) -> None:
    # The execution-source constraint also contains both marker words. A broad
    # pg_get_constraintdef search used to mistake it for the source-kind
    # whitelist and skip recreating the named owner constraint.
    migrated_conn.execute(
        "ALTER TABLE agency_project_claims "
        "DROP CONSTRAINT agency_project_claims_source_kind_check"
    )
    migrated_conn.commit()

    migrated_conn.execute(agency_claims.MIGRATION.read_text(encoding="utf-8"))
    migrated_conn.commit()

    state = _constraint_state(migrated_conn)
    validated, definition = state["agency_project_claims_source_kind_check"]
    assert validated is True
    assert "execution_result" in definition


def test_replaying_candidate_migrations_preserves_validated_state(
    migrated_conn,
) -> None:
    before = _constraint_state(migrated_conn)
    migrated_conn.execute(execution_results.MIGRATION.read_text(encoding="utf-8"))
    migrated_conn.execute(agency_claims.MIGRATION.read_text(encoding="utf-8"))
    migrated_conn.execute(agency_claims.PROVENANCE_MIGRATION.read_text(encoding="utf-8"))
    migrated_conn.commit()
    after = _constraint_state(migrated_conn)
    assert after == before
