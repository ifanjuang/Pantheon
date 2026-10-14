"""Canonical read projections for Source Intake and Information cards.

Persistence keeps owner-specific column names. These functions materialize the
Pantheon-Next contracts without renaming storage columns or transferring
Document, Project, Person or Organization authority.
"""

from __future__ import annotations

from typing import Any


def project_source(source: dict[str, Any]) -> dict[str, Any]:
    """Map one internal Source row to source_intake_admission.schema.yaml."""
    return {
        "source_id": source["source_id"],
        "source_kind": source["source_kind"],
        "origin": {
            "system": source["origin_system"],
            "external_ref": source["origin_external_ref"],
            "producer": source.get("origin_producer"),
            "received_by": source.get("received_by"),
        },
        "raw_source_ref": source["raw_source_ref"],
        "received_at": source["received_at"],
        "project_link_status": source["project_link_status"],
        "project_ref": source.get("project_id"),
        "declared_project_name": source.get("declared_project_name"),
        "candidate_project_refs": list(source.get("candidate_project_refs") or []),
        "source_date": source.get("source_date"),
        "mime_type": source.get("mime_type"),
        "checksum": source.get("checksum"),
        "confidentiality": source.get("confidentiality"),
        "metadata": dict(source.get("metadata") or {}),
    }


def project_information(envelope: dict[str, Any]) -> dict[str, Any]:
    """Map the internal Information envelope to the closed card projection."""
    information = dict(envelope["information"])
    metadata = dict(envelope["projection"])
    document_refs = []
    for link in metadata.get("document_refs") or []:
        document_refs.append(
            {
                "document_id": link["document_id"],
                "role": link.get("role"),
                "observed_version": link.get("observed_version"),
                "observed_digest": link.get("observed_digest"),
            }
        )
    source_refs = []
    if information.get("source_ref"):
        source_refs.append(str(information["source_ref"]))
    return {
        "information_id": information["information_id"],
        "project_id": information["project_id"],
        "series_id": information.get("series_id"),
        "title": information["title"],
        "business_kind": envelope["business_kind"],
        "summary": information.get("summary") or "",
        "details": information.get("details") or "",
        "author_or_origin": information.get("author") or information.get("source_note"),
        "lifecycle_status": envelope["lifecycle_status"],
        "professional_index": envelope["professional_index"],
        "business_date": envelope.get("business_date"),
        "dates": {
            "source_date": metadata.get("source_date"),
            "received_at": metadata.get("received_at"),
            "issued_at": metadata.get("issued_at"),
            "updated_at": metadata.get("updated_at") or information.get("updated_at"),
        },
        "backing_mode": metadata["backing_mode"],
        "document_refs": document_refs,
        "source_refs": source_refs,
        "media_types": list(metadata.get("media_types") or ["text"]),
        "limits": list(information.get("limits") or []),
        "type_tags": list(information.get("type_tags") or []),
        "subject_tags": list(information.get("subject_tags") or []),
        "contact_refs": list(metadata.get("contact_refs") or []),
        "revision": int(metadata.get("revision") or 0),
    }
