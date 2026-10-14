"""Read-only portal-ready projection over existing A/B collaboration owners.

This module does not authorize by visibility and does not own document identity,
currentness, access, approval, Evidence or professional status. Every caller must
already hold the server-side B1 access being projected here.
"""

from __future__ import annotations

from typing import Any

import psycopg

from . import agency_data, human_access, project_document_currentness, project_documents


AUTHORITY = {
    "is_projection": True,
    "is_authorization": False,
    "is_professional_role": False,
    "is_approval": False,
    "is_decision": False,
    "is_evidence": False,
    "changes_current_authority": False,
    "changes_project_truth": False,
}


def document_capabilities(
    conn: psycopg.Connection,
    *,
    principal_ref: str,
    project_id: str,
    document_id: str,
) -> dict[str, bool]:
    """Project exact active B1 grants as UI capabilities, never as authority."""
    return {
        "read": human_access.has_access(
            conn,
            principal_ref=principal_ref,
            project_id=project_id,
            resource_type="project_document",
            resource_id=document_id,
            action="document.read",
        ),
        "submit_revision": human_access.has_access(
            conn,
            principal_ref=principal_ref,
            project_id=project_id,
            resource_type="project_document",
            resource_id=document_id,
            action="document.revision.submit",
        ),
        "comment": human_access.has_access(
            conn,
            principal_ref=principal_ref,
            project_id=project_id,
            resource_type="project_document",
            resource_id=document_id,
            action="document.comment",
        ),
    }


def project_portal_projection(
    conn: psycopg.Connection,
    *,
    principal_ref: str,
    project_id: str,
) -> dict[str, Any]:
    """Compose a minimal external-collaboration read model for one exact Project."""
    human_access.require_access(
        conn,
        principal_ref=principal_ref,
        project_id=project_id,
        resource_type="project",
        resource_id=project_id,
        action="project.read",
    )
    project = agency_data.get_project(conn, project_id)
    documents = human_access.list_accessible_documents(
        conn,
        principal_ref=principal_ref,
        project_id=project_id,
    )

    projected_documents: list[dict[str, Any]] = []
    for document in documents:
        document_id = document["document_id"]
        revisions = project_documents.list_revisions(conn, document_id)
        projected_documents.append(
            {
                "document": document,
                "revision_count": len(revisions),
                "capabilities": document_capabilities(
                    conn,
                    principal_ref=principal_ref,
                    project_id=project_id,
                    document_id=document_id,
                ),
                "currentness": {
                    "latest_received": project_document_currentness.resolve_currentness(
                        conn,
                        document_id=document_id,
                        purpose="latest_received",
                    ),
                    "current_for_coordination": project_document_currentness.resolve_currentness(
                        conn,
                        document_id=document_id,
                        purpose="current_for_coordination",
                    ),
                },
            }
        )

    return {
        "principal_ref": principal_ref,
        "project": project,
        "project_capabilities": {
            "read": True,
            "manage_access": human_access.has_access(
                conn,
                principal_ref=principal_ref,
                project_id=project_id,
                resource_type="project",
                resource_id=project_id,
                action="project.access.manage",
            ),
        },
        "documents": projected_documents,
        "authority": dict(AUTHORITY),
    }
