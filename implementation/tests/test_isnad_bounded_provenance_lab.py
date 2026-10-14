from __future__ import annotations

import importlib.util
import sys
from copy import deepcopy
from importlib.metadata import version as package_version
from pathlib import Path

import pytest

pytest.importorskip("isnad")

LAB = Path(__file__).resolve().parents[1] / "labs" / "isnad_provenance" / "adapter.py"
SPEC = importlib.util.spec_from_file_location("pantheon_isnad_922_adapter", LAB)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

AdvisoryProvenanceObservation = MODULE.AdvisoryProvenanceObservation
IsnadQualificationError = MODULE.IsnadQualificationError
ProvenanceLink = MODULE.ProvenanceLink
ProvenanceSource = MODULE.ProvenanceSource
observe_transmission = MODULE.observe_transmission
verify_serialized_audit_record = MODULE.verify_serialized_audit_record


def _links() -> tuple[ProvenanceLink, ...]:
    return (
        ProvenanceLink(
            narrator_id="source:cctp-current",
            narrator_type="source",
            step=0,
            grade="reliable",
            transform_type="pass_through",
            version="sha256:source-v3",
            output_snapshot="La poutre principale est en acier S355.",
        ),
        ProvenanceLink(
            narrator_id="tool:pdf-extractor",
            narrator_type="scraper",
            step=1,
            grade="acceptable",
            transform_type="destructive",
            version="2.4.1",
            input_snapshot="La poutre principale est en acier S355.",
            output_snapshot="poutre principale acier S355",
        ),
        ProvenanceLink(
            narrator_id="model:hermes-runtime",
            narrator_type="model",
            step=2,
            grade="reliable",
            transform_type="generative",
            version="qualification-model",
            input_snapshot="poutre principale acier S355",
            output_snapshot="Le CCTP prescrit de l'acier S355 pour la poutre principale.",
        ),
    )


def test_complete_chain_emits_provider_neutral_advisory_observation() -> None:
    observation = observe_transmission(
        claim_text="Le CCTP prescrit de l'acier S355 pour la poutre principale.",
        links=_links(),
        sources=(
            ProvenanceSource(
                uri="sources/cctp.pdf",
                content_hash="sha256:current-cctp",
                retrieved_at="2026-09-01T17:00:00+00:00",
            ),
        ),
    )

    assert isinstance(observation, AdvisoryProvenanceObservation)
    assert observation.provider == "isnad"
    assert observation.provider_version == package_version("isnad")
    assert observation.chain_status == "complete"
    assert observation.advisory_chain_grade == "hasan"
    assert observation.weakest_link_narrator_id == "tool:pdf-extractor"
    assert observation.advisory_only is True
    assert observation.evidence_admitted is False
    assert observation.claim_verified is False
    assert observation.authorized_effect is False
    assert observation.persisted is False

    audit = observation.audit_record
    assert audit["claim_text"].startswith("sha256:")
    assert "Le CCTP prescrit" not in audit["claim_text"]
    assert audit["source_documents"][0]["content_hash"] == "sha256:current-cctp"
    assert audit["grading_strategy"]["parameters"]["pantheon_authority"] == "none"
    assert audit["chain"][0]["output_hash"] is not None
    assert audit["chain"][0]["upstream_ids"] == []
    assert audit["chain"][1]["upstream_ids"] == ["source:cctp-current"]
    assert audit["chain"][2]["upstream_ids"] == ["tool:pdf-extractor"]


def test_incomplete_chain_is_advisory_daif_without_bridging_audit_gap() -> None:
    links = (
        ProvenanceLink(
            narrator_id="source:mail",
            narrator_type="source",
            step=0,
            grade="reliable",
            transform_type="pass_through",
        ),
        ProvenanceLink(
            narrator_id="model:summary",
            narrator_type="model",
            step=2,
            grade="reliable",
            transform_type="generative",
        ),
    )

    observation = observe_transmission(claim_text="Projet validé.", links=links)

    assert observation.chain_status == "munqati"
    assert observation.advisory_chain_grade == "daif"
    assert observation.audit_record["chain"][0]["upstream_ids"] == []
    assert observation.audit_record["chain"][1]["upstream_ids"] == []
    assert observation.evidence_admitted is False
    assert observation.claim_verified is False
    assert observation.authorized_effect is False


def test_rejected_transmitter_is_observed_as_mawdu_but_cannot_mutate_pantheon() -> None:
    links = (
        ProvenanceLink(
            narrator_id="source:trusted",
            narrator_type="source",
            step=0,
            grade="reliable",
            transform_type="pass_through",
        ),
        ProvenanceLink(
            narrator_id="tool:compromised",
            narrator_type="tool",
            step=1,
            grade="rejected",
            transform_type="destructive",
        ),
    )

    observation = observe_transmission(claim_text="Budget approuvé.", links=links)

    assert observation.advisory_chain_grade == "mawdu"
    assert observation.weakest_link_narrator_id == "tool:compromised"
    assert observation.advisory_only is True
    assert observation.evidence_admitted is False
    assert observation.claim_verified is False
    assert observation.authorized_effect is False
    assert observation.persisted is False


def test_self_hash_and_detached_signature_fail_after_payload_tamper() -> None:
    observation = observe_transmission(
        claim_text="Le CCTP prescrit de l'acier S355 pour la poutre principale.",
        links=_links(),
        hmac_secret="qualification-only-secret",
    )

    assert verify_serialized_audit_record(
        observation.audit_record,
        hmac_secret="qualification-only-secret",
    )
    assert not verify_serialized_audit_record(
        observation.audit_record,
        hmac_secret="wrong-secret",
    )

    tampered = deepcopy(observation.audit_record)
    tampered["chain"][1]["grade"] = "reliable"

    assert not verify_serialized_audit_record(
        tampered,
        hmac_secret="qualification-only-secret",
    )


def test_unsigned_record_can_verify_self_hash_but_not_claim_a_signature() -> None:
    observation = observe_transmission(
        claim_text="Observation non signée.",
        links=_links(),
    )

    assert verify_serialized_audit_record(observation.audit_record)
    assert not verify_serialized_audit_record(
        observation.audit_record,
        hmac_secret="qualification-only-secret",
    )
    assert observation.detached_signature is None


def test_lab_has_no_pantheon_or_isnad_decision_persistence_path() -> None:
    source = LAB.read_text(encoding="utf-8")
    forbidden = (
        "from isnad.core.decision",
        "isnad.api",
        "store_claim(",
        "review_queue",
        "mvp_vertical",
    )
    for token in forbidden:
        assert token not in source

    assert MODULE.AUTHORITY == {
        "qualification_lab_only": True,
        "advisory_grade_only": True,
        "owns_claim_status": False,
        "verifies_claim": False,
        "admits_evidence": False,
        "owns_review": False,
        "owns_persistence": False,
        "authorizes_effect": False,
        "pdp_authority": False,
        "governed_identity_authority": False,
    }


def test_invalid_inputs_fail_closed() -> None:
    with pytest.raises(IsnadQualificationError, match="unsupported narrator grade"):
        ProvenanceLink(
            narrator_id="model:test",
            narrator_type="model",
            step=0,
            grade="verified",
            transform_type="generative",
        )

    with pytest.raises(IsnadQualificationError, match="at least one provenance link"):
        observe_transmission(claim_text="x", links=())

    with pytest.raises(IsnadQualificationError, match="hmac_secret"):
        observe_transmission(claim_text="x", links=_links(), hmac_secret="")
