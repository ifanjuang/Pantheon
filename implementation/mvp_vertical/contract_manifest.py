"""Canonical Pantheon contract paths consumed by the implementation.

This module contains identifiers and paths only. The schemas themselves remain
owned by the repository-root ``schemas/`` tree. Build artifacts may carry a
generated copy of these exact files so an installed wheel remains autonomous;
that generated copy is distribution material, never a second source of truth.
"""

from __future__ import annotations

CANONICAL_REPOSITORY = "ifanjuang/Pantheon"

CONTRACT_PATHS: dict[str, str] = {
    "apu_attribute_claim": "schemas/architecture-project-understanding/attribute_claim.schema.yaml",
    "apu_observation_bundle": "schemas/architecture-project-understanding/observation_bundle.schema.yaml",
    "apu_relation_claim": "schemas/architecture-project-understanding/relation_claim.schema.yaml",
    "apu_shared": "schemas/architecture-project-understanding/shared.schema.yaml",
    "apu_source_representation": "schemas/architecture-project-understanding/source_representation.schema.yaml",
    "apu_stable_object": "schemas/architecture-project-understanding/stable_object.schema.yaml",
    "apu_write_command_candidate": "schemas/architecture-project-understanding/write_command_candidate.schema.yaml",
    "decision_request": "schemas/decision_request.schema.yaml",
    "document_currentness_projection": "schemas/architecture-proof-register/document_currentness_projection.schema.yaml",
    "document_knowledge_slice": "schemas/document_knowledge_slice.schema.yaml",
    "document_version_event": "schemas/architecture-proof-register/version_event.schema.yaml",
    "human_response": "schemas/human_response.schema.yaml",
    "information_card_projection": "schemas/information_card_projection.schema.yaml",
    "knowledge_edit_variant_candidate": "schemas/knowledge_edit_variant_candidate.schema.yaml",
    "mvp_governed_loop_objects": "schemas/mvp_governed_loop_objects.schema.yaml",
    "navigation_registry": "schemas/navigation_registry.schema.yaml",
    "project_change_variant_candidate": "schemas/project_change_variant_candidate.schema.yaml",
    "project_claim": "schemas/project_claim.schema.yaml",
    "project_claim_candidate": "schemas/project_claim_candidate.schema.yaml",
    "project_claim_conflict_candidate": "schemas/project_claim_conflict_candidate.schema.yaml",
    "source_intake_admission": "schemas/source_intake_admission.schema.yaml",
    "storage_object": "schemas/storage_object.schema.yaml",
    "tag_registry": "schemas/tag_registry.schema.yaml",
    "work_issue_scope_link": "schemas/work_issue_scope_link.schema.yaml",
    "work_issue_slice": "schemas/work_issue_slice.schema.yaml",
}
