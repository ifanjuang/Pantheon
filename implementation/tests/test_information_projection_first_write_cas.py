from __future__ import annotations

import uuid
from datetime import date

import pytest

from mvp_vertical import agency_data, agency_information, information_projection


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


@pytest.fixture
def conn():
    try:
        connection = agency_data.connect()
        relations = connection.execute(
            "SELECT to_regclass('agency_information_projection_metadata')"
        ).fetchone()
        connection.rollback()
        if relations[0] is None:
            information_projection.initialize(connection)
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute("BEGIN")
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


def _information(conn) -> dict:
    project = agency_data.create_project(
        conn,
        project_id=_id("project"),
        code=f"CAS-{uuid.uuid4().hex[:8].upper()}",
        display_name="Projection CAS",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=_id("project-create"),
    )
    return agency_information.create_information(
        conn,
        project_id=project["project_id"],
        title="Information CAS",
        category="NOTE",
        source_type="native",
        source_note="test",
        index_label="A",
        information_date=date(2026, 9, 1),
        actor_kind="human",
    )


def _install_competing_revision(conn, information_id: str) -> None:
    conn.execute(
        """
        INSERT INTO agency_information_projection_metadata
            (information_id, source_date, revision)
        VALUES (%s, %s, 1)
        """,
        (information_id, date(2026, 8, 31)),
    )


def _lie_that_revision_is_still_zero(monkeypatch, information_id: str) -> None:
    original = information_projection._metadata_row

    def stale_read(conn, requested_id: str, *, lock: bool = False):
        if requested_id == information_id and lock:
            return {
                "information_id": information_id,
                "source_date": None,
                "received_at": None,
                "issued_at": None,
                "media_types": ["text"],
                "contact_refs": [],
                "revision": 0,
                "updated_at": None,
            }
        return original(conn, requested_id, lock=lock)

    monkeypatch.setattr(information_projection, "_metadata_row", stale_read)


def test_metadata_upsert_rechecks_revision_at_write_time(conn, monkeypatch) -> None:
    info = _information(conn)
    information_id = info["information_id"]
    _install_competing_revision(conn, information_id)
    _lie_that_revision_is_still_zero(monkeypatch, information_id)

    with pytest.raises(
        information_projection.StaleInformationProjectionWrite,
        match="changed during mutation",
    ):
        information_projection.update_projection_metadata(
            conn,
            information_id=information_id,
            source_date=date(2026, 9, 1),
            received_at=None,
            issued_at=None,
            media_types=["text"],
            contact_refs=[],
            expected_revision=0,
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("metadata"),
        )

    revision, source_date = conn.execute(
        "SELECT revision, source_date FROM agency_information_projection_metadata WHERE information_id = %s",
        (information_id,),
    ).fetchone()
    assert revision == 1
    assert source_date == date(2026, 8, 31)


def test_link_write_rolls_back_when_revision_cas_loses(conn, monkeypatch) -> None:
    info = _information(conn)
    information_id = info["information_id"]
    document_id = _id("document")
    conn.execute(
        """
        INSERT INTO source_documents (
            document_id, dossier, parent_project_id, source_ref,
            source_digest, media_type, byte_size, analysis_status
        ) VALUES (%s,%s,%s,%s,%s,'application/pdf',1,'ready')
        """,
        (
            document_id,
            info["project_id"],
            info["project_id"],
            f"upload://{document_id}",
            _id("digest"),
        ),
    )
    _install_competing_revision(conn, information_id)
    _lie_that_revision_is_still_zero(monkeypatch, information_id)

    with pytest.raises(information_projection.StaleInformationProjectionWrite):
        information_projection.add_document_link(
            conn,
            information_id=information_id,
            document_id=document_id,
            role="primary",
            observed_version=1,
            observed_digest=None,
            expected_revision=0,
            actor="reviewer",
            actor_kind="human",
            idempotency_key=_id("link"),
        )

    assert conn.execute(
        "SELECT 1 FROM agency_information_document_links WHERE information_id = %s AND document_id = %s",
        (information_id, document_id),
    ).fetchone() is None
    assert conn.execute(
        "SELECT revision FROM agency_information_projection_metadata WHERE information_id = %s",
        (information_id,),
    ).fetchone()[0] == 1
