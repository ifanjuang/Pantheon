from pathlib import Path

import jsonschema
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
CARTOUCHE_SCHEMA = ROOT / "schemas" / "workspace_cartouche.schema.yaml"
FOLDER_SCHEMA = ROOT / "schemas" / "workspace_folder_context.schema.yaml"
CARTOUCHE_EXAMPLE = ROOT / "schemas" / "examples" / "workspace_cartouche.example.yaml"
FOLDER_EXAMPLE = ROOT / "schemas" / "examples" / "workspace_folder_context.example.yaml"
SERVER = ROOT / "implementation" / "workspace_cockpit" / "server.py"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_workspace_frontmatter_examples_validate() -> None:
    for schema_path, example_path in (
        (CARTOUCHE_SCHEMA, CARTOUCHE_EXAMPLE),
        (FOLDER_SCHEMA, FOLDER_EXAMPLE),
    ):
        schema = _load(schema_path)
        example = _load(example_path)
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(example)


def test_cartouche_revision_relation_must_be_explicit_and_paired() -> None:
    schema = _load(CARTOUCHE_SCHEMA)
    validator = jsonschema.Draft202012Validator(schema)
    base = {
        "schema": "pantheon/cartouche/v1",
        "document_id": "doc-c",
        "source": "CCTP.pdf",
    }

    validator.validate(base)
    validator.validate({**base, "revision_mode": "supersedes", "revision_of": "doc-b"})

    with pytest.raises(jsonschema.ValidationError):
        validator.validate({**base, "revision_mode": "supersedes"})
    with pytest.raises(jsonschema.ValidationError):
        validator.validate({**base, "revision_of": "doc-b"})
    with pytest.raises(jsonschema.ValidationError):
        validator.validate({**base, "revision_mode": "newer", "revision_of": "doc-b"})


def test_cartouche_source_is_same_directory_basename() -> None:
    schema = _load(CARTOUCHE_SCHEMA)
    validator = jsonschema.Draft202012Validator(schema)
    base = {"schema": "pantheon/cartouche/v1", "document_id": "doc-c"}

    validator.validate({**base, "source": "CCTP_IND_C.pdf"})
    for invalid in ("../CCTP.pdf", "DCE/CCTP.pdf", r"DCE\\CCTP.pdf"):
        with pytest.raises(jsonschema.ValidationError):
            validator.validate({**base, "source": invalid})


def test_frontmatter_schemas_encode_no_authority_promotion() -> None:
    cartouche = _load(CARTOUCHE_SCHEMA)
    folder = _load(FOLDER_SCHEMA)

    assert set(cartouche["x-boundary"].values()) == {False}
    assert set(folder["x-boundary"].values()) == {False}
    assert cartouche["properties"]["index"]["description"].startswith("Opaque descriptive label")
    assert "never inferred" in cartouche["properties"]["revision_mode"]["description"]


def test_runtime_schema_ids_match_machine_contracts() -> None:
    server = SERVER.read_text(encoding="utf-8")
    cartouche = _load(CARTOUCHE_SCHEMA)
    folder = _load(FOLDER_SCHEMA)

    assert f'CARTOUCHE_SCHEMA = "{cartouche["x-pantheon-schema-id"]}"' in server
    assert f'FOLDER_CONTEXT_SCHEMA = "{folder["x-pantheon-schema-id"]}"' in server
