"""Contract tests for request provenance on governed-loop candidate outputs."""

from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "mvp_governed_loop_objects.schema.yaml"
REQUEST_REF = "mvp.devis-reprise.tc-001"
REQUEST_SCOPE_DIGEST = "sha256:" + "4" * 64


def _validator() -> jsonschema.Draft202012Validator:
    schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def _result_candidate() -> dict:
    return {
        "object_type": "result_candidate",
        "object_id": "mvp.devis-reprise.tc-001.rc-001",
        "result_candidate_id": "mvp.devis-reprise.tc-001.rc-001",
        "status": "draft_to_review",
        "request_ref": REQUEST_REF,
        "request_scope_digest": REQUEST_SCOPE_DIGEST,
        "body": "Projet de réponse à revoir.",
        "external_action_authorized": False,
    }


def _evidence_pack() -> dict:
    return {
        "object_type": "evidence_pack_candidate",
        "object_id": "mvp.devis-reprise.tc-001.ep-001",
        "evidence_pack_id": "mvp.devis-reprise.tc-001.ep-001",
        "status": "candidate",
        "request_ref": REQUEST_REF,
        "request_scope_digest": REQUEST_SCOPE_DIGEST,
        "applies_to": "mvp.devis-reprise.tc-001.rc-001",
        "evidence_items": [
            {
                "claim": "Le devis mentionne une reprise.",
                "source_ref": "sources/devis_reprise.md",
                "support_status": "sourced_not_verified",
            }
        ],
        "possible_decisions": ["approve", "request_revision"],
    }


def test_result_and_evidence_pack_share_request_provenance() -> None:
    check = _validator()
    result = _result_candidate()
    evidence = _evidence_pack()
    check.validate(result)
    check.validate(evidence)
    assert result["request_ref"] == evidence["request_ref"]
    assert result["request_scope_digest"] == evidence["request_scope_digest"]


@pytest.mark.parametrize("field", ["request_ref", "request_scope_digest"])
def test_candidate_outputs_require_request_provenance(field: str) -> None:
    check = _validator()
    for candidate in (_result_candidate(), _evidence_pack()):
        broken = deepcopy(candidate)
        broken.pop(field)
        with pytest.raises(jsonschema.ValidationError):
            check.validate(broken)


def test_request_scope_digest_is_a_prefixed_sha256() -> None:
    check = _validator()
    broken = _result_candidate()
    broken["request_scope_digest"] = "4" * 64
    with pytest.raises(jsonschema.ValidationError):
        check.validate(broken)
