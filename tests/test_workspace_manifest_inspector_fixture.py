from __future__ import annotations

import hashlib
import re
from pathlib import Path
from uuid import UUID

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "docs" / "examples" / "workspace_manifest_inspector"
PACKAGE = FIXTURE / "workspace" / "CCTP"
QUALIFIABLE_PACKAGE = FIXTURE / "workspace_qualifiable" / "CCTP"
QUALIFIABLE_EXPECTED = FIXTURE / "expected" / "qualifiable_cctp_local_skeleton.yaml"
GOVERNED = FIXTURE / "governed"
SCHEMAS = ROOT / "schemas" / "architecture-proof-register"

CURRENTNESS_PURPOSES = {
    "latest_received",
    "latest_reviewed",
    "current_working",
    "current_for_coordination",
    "current_for_consultation",
    "current_contractual",
    "current_for_execution",
    "current_for_site",
    "latest_as_built_candidate",
}

GOVERNED_VERSION_FIELDS = {
    "effect_class",
    "version_status",
    "authority_status",
    "approved_by",
    "approved_at",
    "signed_by",
    "signed_at",
}

UUID_PATTERN = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
    r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b"
)
SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


def _yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    assert isinstance(value, dict)
    return value


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for nested in value.values():
            keys.update(_all_keys(nested))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for nested in value:
            keys.update(_all_keys(nested))
        return keys
    return set()


def _git_blob_sha(path: Path) -> str:
    content = path.read_bytes()
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def _mapped_manifest_representation_for_fixture(
    manifest: dict,
) -> tuple[str, str] | None:
    qualification = manifest.get("qualification")
    identity = manifest.get("identity")
    represented_version = manifest.get("represented_version")
    representation = manifest.get("representation")

    if not all(
        isinstance(value, dict)
        for value in (qualification, identity, represented_version, representation)
    ):
        return None

    if qualification.get("status") != "mapped_existing_governed_document":
        return None

    family_id = identity.get("document_family_id")
    version_id = represented_version.get("document_version_id")
    if not isinstance(family_id, str) or not isinstance(version_id, str):
        return None
    try:
        UUID(family_id)
        UUID(version_id)
    except (AttributeError, ValueError):
        return None

    markdown = representation.get("markdown")
    if not isinstance(markdown, dict):
        return None

    file_name = markdown.get("file")
    expected_digest = markdown.get("digest_sha256")
    if not isinstance(file_name, str) or not file_name:
        return None
    if (
        not isinstance(expected_digest, str)
        or SHA256_PATTERN.fullmatch(expected_digest) is None
    ):
        return None

    derived_summary = manifest.get("derived_summary")
    if derived_summary is not None:
        if not isinstance(derived_summary, dict):
            return None
        based_on_digest = derived_summary.get("based_on_digest")
        if based_on_digest is not None and (
            not isinstance(based_on_digest, str)
            or SHA256_PATTERN.fullmatch(based_on_digest) is None
        ):
            return None

    return file_name, expected_digest.lower()


def _local_health_for_fixture(package: Path) -> str:
    manifest_path = package / "document.yaml"
    if manifest_path.exists():
        try:
            manifest = _yaml(manifest_path)
        except (AssertionError, OSError, UnicodeError, yaml.YAMLError):
            return "INVALID"

        mapped_representation = _mapped_manifest_representation_for_fixture(manifest)
        if mapped_representation is None:
            return "INVALID"

        file_name, expected_digest = mapped_representation
        relative_ref = Path(file_name)
        if relative_ref.is_absolute() or ".." in relative_ref.parts:
            return "INVALID"

        markdown = package / relative_ref
        if not markdown.is_file():
            return "INVALID"

        actual_digest = hashlib.sha256(markdown.read_bytes()).hexdigest()
        if actual_digest != expected_digest:
            return "CHECK"

        derived_summary = manifest.get("derived_summary")
        if isinstance(derived_summary, dict):
            based_on_digest = derived_summary.get("based_on_digest")
            if (
                isinstance(based_on_digest, str)
                and based_on_digest.lower() != actual_digest
            ):
                return "CHECK"

        return "COHERENT"

    markdown_files = sorted(
        path for path in package.iterdir() if path.is_file() and path.suffix.lower() == ".md"
    )
    if markdown_files:
        return "QUALIFIABLE"
    return "FREE"


def _copy_mapped_package_for_fixture(tmp_path: Path) -> Path:
    package = tmp_path / "CCTP"
    package.mkdir()
    for name in ("document.yaml", "CCTP.md"):
        (package / name).write_bytes((PACKAGE / name).read_bytes())
    return package


def _build_local_unqualified_skeleton(package: Path) -> dict:
    assert not (package / "document.yaml").exists()

    markdown_files = sorted(
        path for path in package.iterdir() if path.is_file() and path.suffix.lower() == ".md"
    )
    assert len(markdown_files) == 1
    markdown = markdown_files[0]

    return {
        "fixture_status": "synthetic_candidate",
        "local_health": "QUALIFIABLE",
        "qualification": {
            "status": "unadmitted",
            "identity_mapping": "unresolved",
        },
        "observed": {
            "package_name": package.name,
            "representation": {
                "markdown": {
                    "file": markdown.name,
                    "digest_sha256": hashlib.sha256(markdown.read_bytes()).hexdigest(),
                }
            },
        },
        "semantic_enrichment": {
            "status": "not_requested",
        },
    }


def test_governed_fixture_records_validate_against_existing_contracts() -> None:
    family_schema = _yaml(SCHEMAS / "document_family.schema.yaml")
    version_schema = _yaml(SCHEMAS / "indexed_document_version.schema.yaml")
    currentness_schema = _yaml(SCHEMAS / "document_currentness_projection.schema.yaml")

    family = _yaml(GOVERNED / "document_family.yaml")
    version = _yaml(GOVERNED / "indexed_document_version.yaml")
    currentness = _yaml(GOVERNED / "currentness_current_for_consultation.yaml")

    format_checker = jsonschema.FormatChecker()
    jsonschema.Draft202012Validator(
        family_schema, format_checker=format_checker
    ).validate(family)
    jsonschema.Draft202012Validator(
        version_schema, format_checker=format_checker
    ).validate(version)
    jsonschema.Draft202012Validator(
        currentness_schema, format_checker=format_checker
    ).validate(currentness)

    assert version["document_family_id"] == family["document_family_id"]
    assert currentness["document_family_id"] == family["document_family_id"]
    assert currentness["document_version_id"] == version["document_version_id"]


def test_manifest_maps_existing_document_identity_without_inventing_an_owner() -> None:
    manifest = _yaml(PACKAGE / "document.yaml")
    family = _yaml(GOVERNED / "document_family.yaml")
    version = _yaml(GOVERNED / "indexed_document_version.yaml")

    family_id = manifest["identity"]["document_family_id"]
    version_id = manifest["represented_version"]["document_version_id"]

    UUID(family_id)
    UUID(version_id)

    assert manifest["qualification"]["status"] == "mapped_existing_governed_document"
    assert family_id == family["document_family_id"]
    assert version_id == version["document_version_id"]
    assert version["document_family_id"] == family_id
    assert manifest["represented_version"]["index_label"] == version["index_label"]

    keys = _all_keys(manifest)
    assert not CURRENTNESS_PURPOSES.intersection(keys)
    assert not GOVERNED_VERSION_FIELDS.intersection(keys)


def test_manifest_digest_matches_exact_workspace_representation_and_version() -> None:
    manifest = _yaml(PACKAGE / "document.yaml")
    version = _yaml(GOVERNED / "indexed_document_version.yaml")
    markdown = PACKAGE / manifest["representation"]["markdown"]["file"]

    digest = hashlib.sha256(markdown.read_bytes()).hexdigest()

    assert digest == manifest["representation"]["markdown"]["digest_sha256"]
    assert digest == manifest["derived_summary"]["based_on_digest"]
    assert digest == version["hash_sha256"]
    assert version["source_file_ref"] == "workspace/CCTP/CCTP.md"


def test_card_title_source_stays_physical_while_semantic_name_stays_metadata() -> None:
    manifest = _yaml(PACKAGE / "document.yaml")

    assert PACKAGE.name == "CCTP"
    assert manifest["display"]["full_name"] == (
        "Cahier des clauses techniques particulières — Fixture DCE"
    )
    assert manifest["display"]["full_name"] != PACKAGE.name
    assert "title" not in manifest


def test_currentness_is_a_separate_projection_not_manifest_truth() -> None:
    manifest = _yaml(PACKAGE / "document.yaml")
    currentness = _yaml(GOVERNED / "currentness_current_for_consultation.yaml")
    schema = _yaml(SCHEMAS / "document_currentness_projection.schema.yaml")

    assert currentness["purpose"] == "current_for_consultation"
    assert currentness["resolution_status"] == "resolved"
    assert schema["x-currentness"]["universal_current_version"] is False
    assert schema["x-boundary"]["projected_only"] is True
    assert schema["x-boundary"]["persisted_authority"] is False

    assert not CURRENTNESS_PURPOSES.intersection(_all_keys(manifest))


def test_local_validation_basis_pins_exact_existing_schema_blobs() -> None:
    manifest = _yaml(PACKAGE / "document.yaml")
    basis = manifest["validation_basis"]

    assert basis["repository"] == "ifanjuang/Pantheon"
    assert basis["baseline_ref"] == "8c15eff5c767c76410db9e0f3a2e388f85ed1aac"

    expected = {
        "document_family.schema.yaml": SCHEMAS / "document_family.schema.yaml",
        "indexed_document_version.schema.yaml": SCHEMAS
        / "indexed_document_version.schema.yaml",
        "document_currentness_projection.schema.yaml": SCHEMAS
        / "document_currentness_projection.schema.yaml",
    }

    assert set(basis["schema_blobs"]) == set(expected)
    for name, path in expected.items():
        assert basis["schema_blobs"][name] == _git_blob_sha(path)


def test_mapped_manifest_local_health_requires_valid_structure_and_digest(
    tmp_path: Path,
) -> None:
    package = _copy_mapped_package_for_fixture(tmp_path)

    assert _local_health_for_fixture(package) == "COHERENT"

    (package / "document.yaml").write_text("qualification: [", encoding="utf-8")
    assert _local_health_for_fixture(package) == "INVALID"

    manifest = _yaml(PACKAGE / "document.yaml")
    manifest["representation"]["markdown"].pop("digest_sha256")
    (package / "document.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    assert _local_health_for_fixture(package) == "INVALID"


def test_mapped_manifest_local_health_marks_representation_drift_for_check(
    tmp_path: Path,
) -> None:
    package = _copy_mapped_package_for_fixture(tmp_path)
    markdown = package / "CCTP.md"
    markdown.write_text(
        markdown.read_text(encoding="utf-8") + "\nModification locale non qualifiée.\n",
        encoding="utf-8",
    )

    assert _local_health_for_fixture(package) == "CHECK"


def test_mapped_manifest_local_health_marks_stale_summary_basis_for_check(
    tmp_path: Path,
) -> None:
    package = _copy_mapped_package_for_fixture(tmp_path)
    markdown = package / "CCTP.md"
    markdown.write_text(
        markdown.read_text(encoding="utf-8") + "\nModification locale non qualifiée.\n",
        encoding="utf-8",
    )

    manifest = _yaml(package / "document.yaml")
    current_digest = hashlib.sha256(markdown.read_bytes()).hexdigest()
    manifest["representation"]["markdown"]["digest_sha256"] = current_digest
    (package / "document.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    assert _local_health_for_fixture(package) == "CHECK"


def test_markdown_without_manifest_may_be_offered_as_qualifiable_fixture() -> None:
    assert QUALIFIABLE_PACKAGE.is_dir()
    assert not (QUALIFIABLE_PACKAGE / "document.yaml").exists()
    assert (QUALIFIABLE_PACKAGE / "CCTP.md").is_file()

    assert _local_health_for_fixture(QUALIFIABLE_PACKAGE) == "QUALIFIABLE"


def test_qualifiable_fixture_generation_is_deterministic_and_observation_only() -> None:
    generated = _build_local_unqualified_skeleton(QUALIFIABLE_PACKAGE)
    expected = _yaml(QUALIFIABLE_EXPECTED)

    assert generated == expected

    markdown = QUALIFIABLE_PACKAGE / generated["observed"]["representation"]["markdown"]["file"]
    assert generated["observed"]["representation"]["markdown"]["digest_sha256"] == (
        hashlib.sha256(markdown.read_bytes()).hexdigest()
    )
    assert generated["observed"]["package_name"] == QUALIFIABLE_PACKAGE.name


def test_unqualified_skeleton_does_not_fabricate_governed_identity_or_semantics() -> None:
    skeleton = _build_local_unqualified_skeleton(QUALIFIABLE_PACKAGE)
    keys = _all_keys(skeleton)
    serialized = yaml.safe_dump(skeleton, sort_keys=True, allow_unicode=True)

    assert skeleton["local_health"] == "QUALIFIABLE"
    assert skeleton["qualification"] == {
        "status": "unadmitted",
        "identity_mapping": "unresolved",
    }
    assert skeleton["semantic_enrichment"]["status"] == "not_requested"

    assert "document_family_id" not in keys
    assert "document_version_id" not in keys
    assert "identity" not in keys
    assert "display" not in keys
    assert "tags" not in keys
    assert "artifact_origin" not in keys
    assert not CURRENTNESS_PURPOSES.intersection(keys)
    assert not GOVERNED_VERSION_FIELDS.intersection(keys)
    assert UUID_PATTERN.search(serialized) is None
