"""Pure contract-shape tests for Source and Information read projections."""

from mvp_vertical.canonical_projections import project_information, project_source


def test_source_projection_uses_canonical_nested_origin_and_project_ref() -> None:
    projected = project_source(
        {
            "source_id": "source-1",
            "source_kind": "email",
            "origin_system": "gmail",
            "origin_external_ref": "message-42",
            "origin_producer": "client@example.test",
            "received_by": "architect@example.test",
            "raw_source_ref": "gmail://message-42",
            "received_at": "2026-08-06T01:00:00+00:00",
            "project_link_status": "linked",
            "project_id": "project-1",
            "declared_project_name": "Maison Tilleul",
            "candidate_project_refs": [],
            "source_date": None,
            "mime_type": "message/rfc822",
            "checksum": None,
            "confidentiality": None,
            "metadata": {"thread": "thread-1"},
            "revision": 4,
            "created_by": "internal-only",
        }
    )
    assert projected["origin"] == {
        "system": "gmail",
        "external_ref": "message-42",
        "producer": "client@example.test",
        "received_by": "architect@example.test",
    }
    assert projected["project_ref"] == "project-1"
    assert "project_id" not in projected
    assert "origin_system" not in projected
    assert "revision" not in projected


def test_information_projection_is_closed_and_flat() -> None:
    projected = project_information(
        {
            "information": {
                "information_id": "information-1",
                "project_id": "project-1",
                "series_id": "series-1",
                "title": "Compte rendu 14",
                "category": "compte_rendu",
                "summary": "Synthèse",
                "details": "Détails",
                "author": "Architecte",
                "source_ref": "source-cr14",
                "source_note": None,
                "information_date": "2026-08-05",
                "status": "acted",
                "index_label": "14",
                "limits": ["non contractuel"],
                "type_tags": ["chantier"],
                "subject_tags": ["façade"],
                "updated_at": "2026-08-06T01:10:00+00:00",
            },
            "projection": {
                "source_date": "2026-08-05",
                "received_at": "2026-08-05T08:00:00+00:00",
                "issued_at": "2026-08-05T16:00:00+00:00",
                "updated_at": "2026-08-06T01:10:00+00:00",
                "media_types": ["pdf", "text"],
                "contact_refs": [{"label": "Entreprise", "role": "destinataire"}],
                "revision": 0,
                "backing_mode": "single_document",
                "document_refs": [
                    {
                        "information_id": "information-1",
                        "document_id": "document-1",
                        "role": "primary",
                        "observed_version": 2,
                        "observed_digest": "sha256:abc",
                        "created_at": "internal-only",
                    }
                ],
            },
            "business_kind": "compte_rendu",
            "professional_index": "14",
            "business_date": "2026-08-05",
            "lifecycle_status": "acted",
            "document_authority_transferred": False,
            "authorization_inferred": False,
        }
    )
    assert projected["information_id"] == "information-1"
    assert projected["business_kind"] == "compte_rendu"
    assert projected["revision"] == 0
    assert projected["document_refs"] == [
        {
            "document_id": "document-1",
            "role": "primary",
            "observed_version": 2,
            "observed_digest": "sha256:abc",
        }
    ]
    assert "information" not in projected
    assert "projection" not in projected
    assert "document_authority_transferred" not in projected
