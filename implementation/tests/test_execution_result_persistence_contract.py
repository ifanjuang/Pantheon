"""Contract tests for append-only execution-result persistence."""

from pathlib import Path

from mvp_vertical import execution_results


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "mvp_vertical" / "sql" / "010_execution_results.sql"
API = ROOT / "mvp_vertical" / "execution_result_api.py"
COMPOSED = ROOT / "mvp_vertical" / "cockpit_composed.py"


def test_execution_result_vocabulary_matches_governed_contract() -> None:
    assert execution_results.RESULT_KINDS == {
        "fragment_qualification",
        "document_alignment",
        "spatial_observation",
        "apu_object_mapping",
        "relation_candidate",
        "contradiction_candidate",
        "work_issue_candidate",
        "knowledge_edit_variant",
        "project_change_variant",
        "project_claim_candidate",
        "observation_bundle",
    }
    assert execution_results.DISPOSITIONS == {
        "pending",
        "needs_clarification",
        "accepted_for_mapping",
        "selected_for_change_candidate",
        "accepted_for_claim",
        "rejected",
        "superseded",
    }


def test_execution_result_authority_is_candidate_only() -> None:
    assert execution_results.AUTHORITY == {
        "is_fact": False,
        "is_evidence": False,
        "is_decision": False,
        "is_memory": False,
        "is_apu_write": False,
        "authorizes_external_effect": False,
    }


def test_migration_is_append_only_and_has_no_apu_projection() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    for table in (
        "execution_results",
        "execution_result_items",
        "execution_clarification_requests",
        "execution_result_review_dispositions",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql
        assert f"ON {table}" in sql
    assert "BEFORE UPDATE OR DELETE" in sql
    assert "observation_bundle" in sql
    assert "apu_objects" not in sql.lower()
    assert "evidence" not in sql.lower().replace("evidence_pack_candidate_ref", "")
    assert "memory" not in sql.lower()


def test_routes_separate_hermes_submission_from_human_review() -> None:
    source = API.read_text(encoding="utf-8")
    assert '"/execution-results"' in source
    assert "Depends(require_hermes_key)" in source
    assert 'alias="X-Pantheon-Human-Actor"' in source
    assert 'alias="Idempotency-Key"' in source
    assert '"apu_mutated": False' in source
    assert '"human_decision_recorded": False' in source
    assert '"evidence_admitted": False' in source
    assert '"memory_promoted": False' in source
    assert '"external_effect_authorized": False' in source


def test_composed_cockpit_mounts_migration_and_routes() -> None:
    source = COMPOSED.read_text(encoding="utf-8")
    assert "execution_results.MIGRATION" in source
    assert "install_execution_result_routes(" in source
    assert "require_read_key=require_read_key" in source
    assert "require_hermes_key=require_hermes_key" in source


def test_disposition_acceptance_does_not_mean_apu_write() -> None:
    api_source = API.read_text(encoding="utf-8")
    persistence_source = (
        ROOT / "mvp_vertical" / "execution_results.py"
    ).read_text(encoding="utf-8")
    assert "accepted_for_mapping" in persistence_source
    assert "apu_mutated" in api_source
    assert "INSERT INTO execution_result_review_dispositions" in persistence_source
    assert "INSERT INTO apu" not in persistence_source.lower()
    assert "UPDATE " not in persistence_source
    assert "DELETE " not in persistence_source
