from pathlib import Path

from mvp_vertical import (
    agency_change_candidate_review,
    agency_claims,
    agency_classification,
    apu_cross_family,
    apu_mapping_reviews,
    apu_owner,
    apu_write_preparation,
    cockpit_composed,
    contradictory_review_store,
    decision_requests,
    document_revision_discussion,
    entity_relations,
    execution_results,
    human_access,
    information_projection,
    knowledge_edit_variants,
    project_claim_conflicts,
    project_document_admission,
    project_document_currentness,
    project_documents,
    source_intake,
    storage_retention,
    work_issue_scopes,
)


class FakeConnection:
    def __init__(self):
        self.statements = []
        self.commits = 0
        self.closed = False

    def execute(self, statement):
        self.statements.append(statement)

    def commit(self):
        self.commits += 1

    def close(self):
        self.closed = True


def test_composed_app_mounts_candidate_review_routes_without_startup_effects():
    app = cockpit_composed.create_composed_cockpit_app(
        connect_fn=lambda: None,
        initialize_fn=None,
        api_key="read-secret",
        editor_api_key="editor-secret",
        hermes_api_key="hermes-secret",
    )
    methods_by_path: dict[str, set[str]] = {}
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            methods_by_path.setdefault(route.path, set()).update(route.methods or set())
    assert "GET" in methods_by_path["/me"]
    assert "GET" in methods_by_path["/me/projects"]
    assert "GET" in methods_by_path["/me/projects/{project_id}"]
    assert "GET" in methods_by_path["/me/projects/{project_id}/portal"]
    assert "GET" in methods_by_path["/me/projects/{project_id}/access/grants"]
    assert "POST" in methods_by_path["/me/projects/{project_id}/access/grants"]
    assert "POST" in methods_by_path[
        "/me/projects/{project_id}/access/grants/{grant_id}/revoke"
    ]
    assert "GET" in methods_by_path["/me/projects/{project_id}/documents"]
    assert "GET" in methods_by_path[
        "/me/projects/{project_id}/documents/{document_id}"
    ]
    assert "GET" in methods_by_path[
        "/me/projects/{project_id}/documents/{document_id}/currentness/{purpose}"
    ]
    assert "GET" in methods_by_path[
        "/me/projects/{project_id}/documents/{document_id}/comparison"
    ]
    revision_content_path = (
        "/me/projects/{project_id}/documents/{document_id}"
        "/revisions/{version_id}/content"
    )
    assert "GET" in methods_by_path[revision_content_path]
    revision_comments_path = (
        "/me/projects/{project_id}/documents/{document_id}"
        "/revisions/{version_id}/comments"
    )
    assert "GET" in methods_by_path[revision_comments_path]
    assert "POST" in methods_by_path[revision_comments_path]
    assert "POST" in methods_by_path[
        "/me/projects/{project_id}/documents/{document_id}/revisions"
    ]
    assert "POST" in methods_by_path[
        "/me/projects/{project_id}/documents/{document_id}/revision-uploads"
    ]
    assert "GET" in methods_by_path["/agency/information/{information_id}/projection"]
    assert "GET" in methods_by_path[
        "/agency/projects/{project_id}/information-projections"
    ]
    assert "GET" in methods_by_path["/agency/categories"]
    assert "POST" in methods_by_path["/agency/categories"]
    assert "GET" in methods_by_path["/agency/category-roots"]
    assert "GET" in methods_by_path["/agency/categories/{category_id}"]
    assert "PATCH" in methods_by_path["/agency/categories/{category_id}"]
    assert "GET" in methods_by_path["/agency/categories/{category_id}/collection"]
    assert "POST" in methods_by_path["/agency/categories/{category_id}/archive"]
    assert "POST" in methods_by_path[
        "/agency/categories/{category_id}/assignments"
    ]
    assert "POST" in methods_by_path[
        "/agency/category-assignments/{assignment_id}/retire"
    ]
    assert "GET" in methods_by_path[
        "/agency/classification/{entity_type}/{entity_id}"
    ]
    assert "POST" in methods_by_path["/agency/entity-relations"]
    assert "GET" in methods_by_path["/agency/entity-relations/{relation_id}"]
    assert "GET" in methods_by_path[
        "/agency/projects/{project_id}/entity-relations"
    ]
    assert "GET" in methods_by_path[
        "/agency/entities/{entity_type}/{entity_id}/relations"
    ]
    assert "POST" in methods_by_path[
        "/agency/entity-relations/{relation_id}/retire"
    ]
    assert "POST" in methods_by_path["/execution-results"]
    disposition_path = (
        "/execution-results/{execution_result_id}/results/{result_ref}/dispositions"
    )
    claim_path = (
        "/execution-results/{execution_result_id}/results/{result_ref}/project-claim"
    )
    project_change_candidate_path = (
        "/execution-results/{execution_result_id}/results/{result_ref}/project-change-candidate"
    )
    assert "POST" in methods_by_path[disposition_path]
    assert "POST" in methods_by_path[claim_path]
    assert "POST" in methods_by_path[project_change_candidate_path]
    assert "POST" in methods_by_path[
        "/execution-results/{execution_result_id}/results/{result_ref}/project-knowledge-edit-variant"
    ]
    assert "POST" in methods_by_path["/knowledge/{knowledge_id}/variant-edit-requests"]
    assert "GET" in methods_by_path["/knowledge/{knowledge_id}/edit-reviews"]
    assert "POST" in methods_by_path["/edit-requests/{request_id}/select-variant"]
    assert "POST" in methods_by_path["/edit-requests/{request_id}/apply-selected"]
    assert "POST" in methods_by_path["/work/issues"]
    assert "GET" in methods_by_path["/work/issues/{issue_id}/scopes"]
    assert "GET" in methods_by_path[
        "/work/scopes/{entity_type}/{entity_id}/issues"
    ]
    assert "POST" in methods_by_path["/work/issues/{issue_id}/scopes"]
    assert "POST" in methods_by_path[
        "/work/issues/{issue_id}/scopes/{scope_link_id}/retire"
    ]
    assert "POST" in methods_by_path[
        "/work/issues/{issue_id}/scopes/{scope_link_id}/replace-primary"
    ]
    assert "POST" in methods_by_path["/decision-requests"]
    assert "GET" in methods_by_path["/decision-requests"]
    assert "GET" in methods_by_path["/decision-inbox"]
    assert "GET" in methods_by_path[
        "/agency/projects/{project_id}/decision-requests"
    ]
    assert "GET" in methods_by_path[
        "/agency/apu-objects/{object_id}/decision-requests"
    ]
    assert "GET" in methods_by_path[
        "/agency/apu-objects/{object_id}/project-claims"
    ]
    assert "GET" in methods_by_path[
        "/work/issues/{issue_id}/blocking-decision-request"
    ]
    assert "POST" in methods_by_path[
        "/decision-requests/{request_id}/resolve"
    ]
    assert "GET" in methods_by_path["/decisions/{decision_id}"]
    mapping_reviews_path = "/execution-results/{execution_result_id}/results/{result_ref}/mappings/{mapping_ref}/reviews"
    assert "POST" in methods_by_path[mapping_reviews_path]
    assert "GET" in methods_by_path[mapping_reviews_path]
    prepare_path = "/execution-results/{execution_result_id}/results/{result_ref}/mappings/{mapping_ref}/prepare-apu-write"
    assert "POST" in methods_by_path[prepare_path]
    assert "GET" in methods_by_path["/apu-write-commands/{command_id}"]
    assert "POST" in methods_by_path["/apu-write-commands/{command_id}/authorizations"]
    assert "GET" in methods_by_path["/apu-write-commands/{command_id}/authorizations"]
    assert "POST" in methods_by_path["/apu-write-commands/{command_id}/apply"]
    assert "GET" in methods_by_path["/agency/projects/{project_id}/project-anatomy"]
    assert "GET" in methods_by_path["/cockpit/role-traces/{run_id}"]
    assert "GET" in methods_by_path["/cockpit/role-traces/{run_id}/events"]


def test_composed_initializer_replays_owner_and_review_migrations_in_dependency_order(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(cockpit_composed.store, "connect", lambda: connection)
    cockpit_composed.initialize_composed_schema()
    assert connection.commits == 1
    assert connection.closed is True
    assert len(connection.statements) == 31
    assert "CREATE TABLE IF NOT EXISTS agency_apu_objects" in connection.statements[2]
    assert "model_version" in connection.statements[2]
    assert "CREATE TABLE IF NOT EXISTS agency_sources" in connection.statements[3]
    assert "CREATE TABLE IF NOT EXISTS doc_documents" in connection.statements[4]
    assert "CREATE TABLE IF NOT EXISTS agency_categories" in connection.statements[5]
    assert "CREATE TABLE IF NOT EXISTS agency_category_assignments" in connection.statements[5]
    assert "CREATE TABLE IF NOT EXISTS doc_document_version_sources" in connection.statements[6]
    assert "CREATE TABLE IF NOT EXISTS doc_document_version_effect_events" in connection.statements[7]
    assert "CREATE TABLE IF NOT EXISTS storage_objects" in connection.statements[8]
    assert "CREATE TABLE IF NOT EXISTS human_principals" in connection.statements[9]
    assert "human_resource_grants_action_allowed_check" in connection.statements[10]
    assert "project.access.manage" in connection.statements[11]
    assert "CREATE TABLE IF NOT EXISTS doc_document_revision_comments" in connection.statements[12]
    assert "CREATE TABLE IF NOT EXISTS agency_information_projection_metadata" in connection.statements[13]
    assert "CREATE TABLE IF NOT EXISTS work_issue_scope_links" in connection.statements[14]
    assert "CREATE TABLE IF NOT EXISTS agency_decision_requests" in connection.statements[15]
    assert "CREATE TABLE IF NOT EXISTS agency_human_responses" in connection.statements[16]
    assert "agency_decision_requests_effect_binding_check" in connection.statements[17]
    assert "CREATE TABLE IF NOT EXISTS agency_entity_relations" in connection.statements[18]
    assert "CREATE TABLE IF NOT EXISTS execution_results" in connection.statements[21]
    assert "project_change_variant" in connection.statements[22]
    assert "candidate_execution_id" in connection.statements[23]
    assert "basis_refs" in connection.statements[24]
    assert "agency_project_claims_validate_candidate_basis_refs" in connection.statements[24]
    assert "CREATE TABLE IF NOT EXISTS agency_project_claim_conflict_candidates" in connection.statements[25]
    assert "validate_agency_project_claim_conflict_pair" in connection.statements[25]
    assert "agency_decision_request_scope_refs" in connection.statements[26]
    assert "apu_object" in connection.statements[26]
    assert "CREATE TABLE IF NOT EXISTS knowledge_edit_variants" in connection.statements[27]
    assert "CREATE TABLE IF NOT EXISTS apu_mapping_review_events" in connection.statements[28]
    assert "CREATE TABLE IF NOT EXISTS apu_write_command_candidates" in connection.statements[29]
    assert "expected_owner_revision" in connection.statements[29]
    assert "agency_apu_source_match_command_once" in connection.statements[30]


def test_composed_migrations_are_packaged_under_sql_directory():
    for migration, expected_name in (
        (apu_owner.MIGRATION, "021_project_anatomy_owner.sql"),
        (source_intake.MIGRATION, "009_source_intake_admission.sql"),
        (project_documents.MIGRATION, "025_project_document_revisions.sql"),
        (agency_classification.MIGRATION, "034_category_classification.sql"),
        (project_document_admission.MIGRATION, "026_project_document_source_admission.sql"),
        (project_document_currentness.MIGRATION, "027_project_document_version_effect_events.sql"),
        (storage_retention.MIGRATION, "029_storage_object_retention.sql"),
        (human_access.MIGRATION, "030_human_principal_access.sql"),
        (human_access.ACTION_MIGRATION, "031_human_document_comment_access.sql"),
        (human_access.MANAGEMENT_MIGRATION, "033_human_project_access_management.sql"),
        (document_revision_discussion.MIGRATION, "032_document_revision_discussion.sql"),
        (information_projection.MIGRATION, "013_information_card_projection.sql"),
        (work_issue_scopes.MIGRATION, "016_work_issue_scopes.sql"),
        (decision_requests.MIGRATION, "018_decision_requests.sql"),
        (decision_requests.HUMAN_RESPONSE_MIGRATION, "038_human_response_resolution.sql"),
        (decision_requests.EFFECT_BINDING_MIGRATION, "039_decision_effect_binding.sql"),
        (entity_relations.MIGRATION, "015_entity_relations.sql"),
        (agency_change_candidate_review.MIGRATION, "005_change_candidate_review.sql"),
        (contradictory_review_store.MIGRATION, "003_contradictory_review_candidates.sql"),
        (execution_results.MIGRATION, "010_execution_results.sql"),
        (execution_results.VARIANT_MIGRATION, "020_project_change_variants.sql"),
        (agency_claims.MIGRATION, "019_project_claim_candidates.sql"),
        (agency_claims.PROVENANCE_MIGRATION, "036_project_claim_provenance_basis.sql"),
        (project_claim_conflicts.MIGRATION, "037_project_claim_conflict_candidates.sql"),
        (apu_cross_family.MIGRATION, "023_apu_cross_family_links.sql"),
        (knowledge_edit_variants.MIGRATION, "014_knowledge_edit_variants.sql"),
        (apu_mapping_reviews.MIGRATION, "011_apu_mapping_reviews.sql"),
        (apu_write_preparation.MIGRATION, "012_apu_write_preparation.sql"),
        (apu_write_preparation.APPLICATION_MIGRATION, "022_project_anatomy_match_application.sql"),
    ):
        assert isinstance(migration, Path)
        assert migration.name == expected_name
        assert migration.parent.name == "sql"
        assert migration.is_file()


def test_console_entrypoint_targets_composed_cockpit():
    # Resolve from this file, not the working directory: read relatively, the
    # monorepo root's governance pyproject.toml is picked up instead and the
    # assertion fails for a contributor running pytest from the repository root.
    pyproject = (
        Path(__file__).resolve().parents[1] / "pyproject.toml"
    ).read_text(encoding="utf-8")
    assert 'mvp-cockpit-api = "mvp_vertical.cockpit_composed:run"' in pyproject
