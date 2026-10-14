"""PostgreSQL + filesystem acceptance tests for A7b Storage Object retention."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

import psycopg
import pytest

from mvp_vertical import project_documents, storage_retention, pantheon_contracts


PROVIDER = "agency-retention-primary"


@pytest.fixture
def conn():
    try:
        connection = storage_retention.connect()
        project_documents.ensure_schema(connection)
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL unreachable: {exc}")
    connection.execute(
        "TRUNCATE document_version_storage_bindings, storage_object_locations, "
        "storage_objects, doc_document_version_reference_observations, "
        "doc_document_events, doc_document_versions, doc_documents, "
        "document_versions, source_documents RESTART IDENTITY CASCADE"
    )
    connection.commit()
    yield connection
    connection.close()


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _technical_version(
    conn,
    *,
    data: bytes,
    document_id: str | None = None,
    version: int = 1,
    source_ref: str | None = None,
) -> tuple[str, int]:
    document_id = document_id or f"source-document-{uuid.uuid4().hex}"
    digest = _digest(data)
    source_ref = source_ref or f"incoming/{document_id}.pdf"
    exists = conn.execute(
        "SELECT 1 FROM source_documents WHERE document_id = %s", (document_id,)
    ).fetchone()
    if exists is None:
        conn.execute(
            """
            INSERT INTO source_documents (
                document_id, dossier, parent_project_id, source_ref, source_digest,
                media_type, byte_size, analysis_status
            ) VALUES (%s, %s, %s, %s, %s, 'application/pdf', %s, 'ready')
            """,
            (document_id, "project-alpha", "project-alpha", source_ref, digest, len(data)),
        )
    conn.execute(
        """
        INSERT INTO document_versions (
            document_id, version, source_ref, source_digest, media_type, byte_size
        ) VALUES (%s, %s, %s, %s, 'application/pdf', %s)
        """,
        (document_id, version, source_ref, digest, len(data)),
    )
    conn.commit()
    return document_id, version


def _source(tmp_path: Path, name: str, data: bytes) -> Path:
    path = tmp_path / name
    path.write_bytes(data)
    return path


def _counts(conn) -> tuple[int, int, int]:
    return tuple(
        int(conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0])
        for table in (
            "storage_objects",
            "storage_object_locations",
            "document_version_storage_bindings",
        )
    )


def test_storage_contract_uses_canonical_source() -> None:
    provenance = pantheon_contracts.provenance("storage_object")
    assert provenance["source_repository"] == "ifanjuang/Pantheon"
    assert provenance["source_path"] == "schemas/storage_object.schema.yaml"
    assert provenance["posture"] == "canonical-repository"
    assert provenance["authority_transfer"] is False
    assert provenance["sha256"] == hashlib.sha256(
        pantheon_contracts.schema_path("storage_object").read_bytes()
    ).hexdigest()


def test_exact_file_can_be_retained_without_document_binding(conn, tmp_path: Path) -> None:
    data = b"exact gmail rfc822 bytes\r\n"
    source = _source(tmp_path, "message.eml", data)
    root = tmp_path / "retention"

    result = storage_retention.retain_exact_file(
        conn,
        source_path=source,
        retention_root=root,
        storage_provider_ref=PROVIDER,
        media_type="message/rfc822",
        expected_digest=_digest(data),
        expected_size=len(data),
    )

    storage_object = result["storage_object"]
    assert storage_object["content_sha256"] == _digest(data)
    assert storage_object["byte_size"] == len(data)
    assert storage_object["media_type"] == "message/rfc822"
    assert storage_object["locations"][0]["location_status"] == "verified"
    assert result["document_version_binding_created"] is False
    assert _counts(conn) == (1, 1, 0)

    retained = root / storage_object["locations"][0]["locator"]
    assert retained.read_bytes() == data


def test_exact_bytes_use_same_verified_storage_owner(conn, tmp_path: Path) -> None:
    data = b"raw gmail bytes supplied in memory"
    result = storage_retention.retain_exact_bytes(
        conn,
        content=data,
        retention_root=tmp_path / "retention",
        storage_provider_ref=PROVIDER,
        media_type="message/rfc822",
        expected_digest=_digest(data),
    )

    storage_object = result["storage_object"]
    assert storage_object["content_sha256"] == _digest(data)
    assert storage_object["byte_size"] == len(data)
    assert result["document_version_binding_created"] is False
    assert _counts(conn) == (1, 1, 0)


def test_exact_file_reuses_storage_object_without_creating_document_identity(conn, tmp_path: Path) -> None:
    data = b"same raw email bytes"
    root = tmp_path / "retention"
    first = storage_retention.retain_exact_file(
        conn,
        source_path=_source(tmp_path, "one.eml", data),
        retention_root=root,
        storage_provider_ref=PROVIDER,
        media_type="message/rfc822",
    )
    second = storage_retention.retain_exact_file(
        conn,
        source_path=_source(tmp_path, "two.eml", data),
        retention_root=root,
        storage_provider_ref=PROVIDER,
        media_type="message/rfc822",
    )

    assert (
        first["storage_object"]["storage_object_id"]
        == second["storage_object"]["storage_object_id"]
    )
    assert _counts(conn) == (1, 1, 0)


def test_exact_file_digest_mismatch_fails_before_storage_rows(conn, tmp_path: Path) -> None:
    source = _source(tmp_path, "message.eml", b"actual bytes")

    with pytest.raises(
        storage_retention.SourceContentMismatch,
        match="expected SHA-256",
    ):
        storage_retention.retain_exact_file(
            conn,
            source_path=source,
            retention_root=tmp_path / "retention",
            storage_provider_ref=PROVIDER,
            media_type="message/rfc822",
            expected_digest="0" * 64,
        )

    assert _counts(conn) == (0, 0, 0)


def test_retained_bytes_survive_source_overwrite_and_delete(conn, tmp_path: Path) -> None:
    original = b"historical BET study index B\n"
    document_id, version = _technical_version(conn, data=original)
    source = _source(tmp_path, "study_B.pdf", original)
    retention_root = tmp_path / "retention"

    result = storage_retention.retain_document_version(
        conn,
        document_id=document_id,
        version=version,
        source_path=source,
        retention_root=retention_root,
        storage_provider_ref=PROVIDER,
    )
    assert result["storage_object"]["content_sha256"] == _digest(original)
    assert result["storage_object"]["locations"][0]["location_status"] == "verified"
    assert result["authority"]["is_evidence"] is False

    source.write_bytes(b"replacement index C\n")
    source.unlink()

    retained = storage_retention.resolve_retained_version_path(
        conn,
        document_id=document_id,
        version=version,
        retention_root=retention_root,
        storage_provider_ref=PROVIDER,
    )
    assert retained.read_bytes() == original
    assert _digest(retained.read_bytes()) == _digest(original)


def test_identical_bytes_reuse_one_storage_object_without_merging_bindings(conn, tmp_path: Path) -> None:
    data = b"same exact professional source bytes\n"
    doc_a, ver_a = _technical_version(conn, data=data)
    doc_b, ver_b = _technical_version(conn, data=data)
    source_a = _source(tmp_path, "a.pdf", data)
    source_b = _source(tmp_path, "b.pdf", data)
    root = tmp_path / "retention"

    first = storage_retention.retain_document_version(
        conn,
        document_id=doc_a,
        version=ver_a,
        source_path=source_a,
        retention_root=root,
        storage_provider_ref="opaque-provider-ref",
    )
    second = storage_retention.retain_document_version(
        conn,
        document_id=doc_b,
        version=ver_b,
        source_path=source_b,
        retention_root=root,
        storage_provider_ref="opaque-provider-ref",
    )

    assert first["storage_object"]["storage_object_id"] == second["storage_object"]["storage_object_id"]
    assert _counts(conn) == (1, 1, 2)


def test_changed_bytes_create_distinct_storage_objects(conn, tmp_path: Path) -> None:
    data_b = b"index B\n"
    data_c = b"index C changed\n"
    doc_b, ver_b = _technical_version(conn, data=data_b)
    doc_c, ver_c = _technical_version(conn, data=data_c)
    root = tmp_path / "retention"

    b = storage_retention.retain_document_version(
        conn,
        document_id=doc_b,
        version=ver_b,
        source_path=_source(tmp_path, "b.pdf", data_b),
        retention_root=root,
        storage_provider_ref=PROVIDER,
    )
    c = storage_retention.retain_document_version(
        conn,
        document_id=doc_c,
        version=ver_c,
        source_path=_source(tmp_path, "c.pdf", data_c),
        retention_root=root,
        storage_provider_ref=PROVIDER,
    )

    assert b["storage_object"]["storage_object_id"] != c["storage_object"]["storage_object_id"]
    assert _counts(conn) == (2, 2, 2)


def test_source_digest_mismatch_refuses_before_any_storage_binding(conn, tmp_path: Path) -> None:
    expected = b"expected bytes\n"
    document_id, version = _technical_version(conn, data=expected)
    wrong = _source(tmp_path, "wrong.pdf", b"wrong bytes\n")

    with pytest.raises(storage_retention.SourceContentMismatch):
        storage_retention.retain_document_version(
            conn,
            document_id=document_id,
            version=version,
            source_path=wrong,
            retention_root=tmp_path / "retention",
            storage_provider_ref=PROVIDER,
        )
    assert _counts(conn) == (0, 0, 0)


def test_corrupt_preexisting_content_addressed_target_fails_closed(conn, tmp_path: Path) -> None:
    data = b"correct retained bytes\n"
    document_id, version = _technical_version(conn, data=data)
    source = _source(tmp_path, "correct.pdf", data)
    digest = _digest(data)
    root = tmp_path / "retention"
    target = root / "sha256" / digest[:2] / digest
    target.parent.mkdir(parents=True)
    target.write_bytes(b"corrupt target\n")

    with pytest.raises(storage_retention.RetainedObjectCorrupt):
        storage_retention.retain_document_version(
            conn,
            document_id=document_id,
            version=version,
            source_path=source,
            retention_root=root,
            storage_provider_ref=PROVIDER,
        )

    assert target.read_bytes() == b"corrupt target\n"
    assert _counts(conn) == (0, 0, 0)


def test_publish_failure_leaves_no_verified_database_binding(conn, tmp_path: Path, monkeypatch) -> None:
    data = b"copy failure fixture\n"
    document_id, version = _technical_version(conn, data=data)
    source = _source(tmp_path, "source.pdf", data)
    root = tmp_path / "retention"

    def fail_replace(_src, _dst):
        raise OSError("synthetic publish failure")

    monkeypatch.setattr(storage_retention.os, "replace", fail_replace)
    with pytest.raises(storage_retention.StorageRetentionError, match="atomically publish"):
        storage_retention.retain_document_version(
            conn,
            document_id=document_id,
            version=version,
            source_path=source,
            retention_root=root,
            storage_provider_ref=PROVIDER,
        )

    assert _counts(conn) == (0, 0, 0)
    digest = _digest(data)
    parent = root / "sha256" / digest[:2]
    assert not (parent / digest).exists()
    assert not list(parent.glob("*.tmp"))
    assert not list(parent.glob("*.lock"))


def test_binding_and_storage_object_identity_are_sql_immutable(conn, tmp_path: Path) -> None:
    data = b"immutable binding\n"
    document_id, version = _technical_version(conn, data=data)
    storage_retention.retain_document_version(
        conn,
        document_id=document_id,
        version=version,
        source_path=_source(tmp_path, "source.pdf", data),
        retention_root=tmp_path / "retention",
        storage_provider_ref=PROVIDER,
    )
    conn.commit()

    with pytest.raises(psycopg.errors.RaiseException, match="immutable"):
        conn.execute(
            """
            UPDATE document_version_storage_bindings
               SET storage_object_id = 'other-object'
             WHERE document_id = %s AND version = %s
            """,
            (document_id, version),
        )
    conn.rollback()

    with pytest.raises(psycopg.errors.RaiseException, match="immutable"):
        conn.execute("UPDATE storage_objects SET byte_size = byte_size + 1")
    conn.rollback()


def test_retained_corruption_is_detected_on_resolution(conn, tmp_path: Path) -> None:
    data = b"will be corrupted after verified retention\n"
    document_id, version = _technical_version(conn, data=data)
    root = tmp_path / "retention"
    source = _source(tmp_path, "source.pdf", data)
    storage_retention.retain_document_version(
        conn,
        document_id=document_id,
        version=version,
        source_path=source,
        retention_root=root,
        storage_provider_ref=PROVIDER,
    )
    retained = storage_retention.resolve_retained_version_path(
        conn,
        document_id=document_id,
        version=version,
        retention_root=root,
        storage_provider_ref=PROVIDER,
    )
    retained.write_bytes(b"corrupted later\n")

    with pytest.raises(storage_retention.RetainedObjectCorrupt):
        storage_retention.resolve_retained_version_path(
            conn,
            document_id=document_id,
            version=version,
            retention_root=root,
            storage_provider_ref=PROVIDER,
        )


def test_retention_does_not_change_professional_latest_received(conn, tmp_path: Path) -> None:
    data = b"project document source\n"
    source_document_id, source_version = _technical_version(conn, data=data)
    professional = project_documents.create_document(
        conn,
        document_id=f"project-document-{uuid.uuid4().hex}",
        parent_project_id="project-alpha",
        document_type="ETUDE",
        title="Étude BET",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=f"create-{uuid.uuid4().hex}",
    )
    revision = project_documents.link_revision(
        conn,
        document_id=professional["document_id"],
        source_document_id=source_document_id,
        source_version=source_version,
        revision_label="B",
        actor="reviewer",
        actor_kind="human",
        idempotency_key=f"revision-{uuid.uuid4().hex}",
    )
    before = project_documents.resolve_latest_received(conn, professional["document_id"])

    storage_retention.retain_document_version(
        conn,
        document_id=source_document_id,
        version=source_version,
        source_path=_source(tmp_path, "bet.pdf", data),
        retention_root=tmp_path / "retention",
        storage_provider_ref=PROVIDER,
    )
    after = project_documents.resolve_latest_received(conn, professional["document_id"])

    assert before == after
    assert after["version"]["version_id"] == revision["version_id"]


def test_storage_object_projection_is_schema_conformant(conn, tmp_path: Path) -> None:
    data = b"schema conformant storage object\n"
    document_id, version = _technical_version(conn, data=data)
    result = storage_retention.retain_document_version(
        conn,
        document_id=document_id,
        version=version,
        source_path=_source(tmp_path, "source.pdf", data),
        retention_root=tmp_path / "retention",
        storage_provider_ref="custom://opaque-binding-01",
    )
    assert pantheon_contracts.problems("storage_object", result["storage_object"]) == []
    locator = result["storage_object"]["locations"][0]["locator"]
    assert locator == f"sha256/{_digest(data)[:2]}/{_digest(data)}"
    assert ".." not in locator
