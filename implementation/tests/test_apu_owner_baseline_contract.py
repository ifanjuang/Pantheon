from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mvp_vertical import pantheon_contracts
from mvp_vertical import apu_owner


ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "mvp_vertical" / "vendor" / "pantheon"


def _blob_sha(payload: bytes) -> str:
    return hashlib.sha1(
        f"blob {len(payload)}\0".encode() + payload,
        usedforsecurity=False,
    ).hexdigest()


def test_project_anatomy_is_installed_at_its_final_shape() -> None:
    assert apu_owner.MIGRATION.name == "021_project_anatomy_owner.sql"
    sql = apu_owner.MIGRATION.read_text(encoding="utf-8")

    for table in (
        "agency_apu_project_state",
        "agency_apu_objects",
        "agency_apu_source_representations",
        "agency_apu_attribute_claims",
        "agency_apu_relation_claims",
        "agency_apu_events",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql
    assert "model_version = 2" in sql
    assert "stable_object_payload" in sql
    assert "append-only" in sql.lower()
    for discarded in (
        "agency_apu_object_relations",
        "agency_apu_v02_owner_migrations",
        "canonical_stable_object",
        "object_identity",
        "object_kind",
        "model_version = 1",
    ):
        assert discarded not in sql
    assert not (ROOT / "mvp_vertical/sql/024_project_anatomy_v02_owner.sql").exists()


def test_project_anatomy_contracts_use_one_canonical_path_family() -> None:
    expected_paths = {
        "shared": "shared.schema.yaml",
        "stable_object": "stable_object.schema.yaml",
        "source_representation": "source_representation.schema.yaml",
        "attribute_claim": "attribute_claim.schema.yaml",
        "relation_claim": "relation_claim.schema.yaml",
        "write_command_candidate": "write_command_candidate.schema.yaml",
        "observation_bundle": "observation_bundle.schema.yaml",
    }
    for name, upstream_name in expected_paths.items():
        contract_name = f"apu_{name}"
        source = pantheon_contracts.provenance(contract_name)
        assert source["source_path"] == (
            "schemas/architecture-project-understanding/" + upstream_name
        )
        assert source["posture"] == "canonical-repository"
        assert source["authority_transfer"] is False
        assert source["source_blob_sha"] == _blob_sha(
            pantheon_contracts.schema_path(contract_name).read_bytes()
        )

    names = {name for name in pantheon_contracts.CONTRACT_PATHS if name.startswith("apu_")}
    assert not any("v02" in name for name in names)
    assert "apu_object_identity" not in names
    assert "apu_object_relation" not in names


def test_runtime_has_no_discarded_reader_writer_or_migration_surface() -> None:
    source = (ROOT / "mvp_vertical/apu_owner.py").read_text(encoding="utf-8")
    for discarded in (
        "get_project_anatomy_v02",
        "store_reviewed_v02_dossier",
        "migrate_project_to_v02",
        "list_v02_owner_migrations",
        "target_model_version",
        "stable_object.matches",
        "object_identity",
        "agency_apu_object_relations",
    ):
        assert discarded not in source

    assert "def get_project_anatomy(" in source
    assert "def store_reviewed_dossier(" in source
    assert "def apply_source_match(" in source
