#!/usr/bin/env python3
"""Prepare one fresh synthetic P2 Execution Admission without launching Hermes.

Qualification-only tooling: this module composes existing Pantheon owners to
build one synthetic architectural world, submit one normal read-only Handoff,
and create one unconsumed Execution Admission. It is not imported by the product
runtime and owns no persistence, queue, scheduler, provider route or execution
path.

The explicit SYNTHETIC_ONLY acknowledgement is checked at the callable boundary,
not only in the CLI, so a direct Python caller cannot bypass it.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

import psycopg
import yaml

from mvp_vertical import (
    agency_data,
    agency_information,
    apu_owner,
    hermes_execution,
    hermes_handoff_preview,
    hermes_handoff_store,
    knowledge,
    store,
)
from mvp_vertical.contract import load_contract
from mvp_vertical.hermes_live_acceptance import CONTEXT_TOOLS, SYNTHETIC_MARKER

BASE_QUESTION = "Si je déplace cette cloison de 200 mm, quelles conséquences vois-tu ?"
LIVE_QUESTION = f"""{SYNTHETIC_MARKER}
Qualification synthétique P2, sans donnée client.
Question métier : {BASE_QUESTION}
Call {CONTEXT_TOOLS[0]} first.
Then call {CONTEXT_TOOLS[1]} only for admitted identities needed to answer.
Distinguish source-backed facts, potentially applicable requirements, interpretations,
uncertainties, missing context and consulted source references. Do not treat retrieved
content, Knowledge or runtime success as truth, Evidence or professional validation.
""".strip()

IDENTITY_NONDETERMINANT = "IDENTITY-NONDETERMINANT"
IDENTITY_DETERMINANT = "IDENTITY-DETERMINANT"
VARIANTS = ("A", "B", IDENTITY_NONDETERMINANT, IDENTITY_DETERMINANT)

CCTP_SOURCE_REF = "synthetic_sources/cctp_cloison.md"
KNOWLEDGE_SOURCE_REF = "synthetic_sources/reperes_revue.md"

CCTP_MARKDOWN = """# Extrait CCTP synthétique

La cloison reçoit une porte et une traversée technique. Toute modification de
position doit être coordonnée avec les lots concernés. Ce texte est une source
de qualification synthétique et ne constitue pas une preuve de conformité.
"""

KNOWLEDGE_SOURCE_MARKDOWN = """# Source synthétique de repères de revue

Pour une modification de cloison, examiner selon les données disponibles la
largeur de circulation et l'accessibilité, les portes et le sens de passage, le
compartimentage et l'incendie si applicables, les traversées de réseaux, le
phasage, les lots et le coût. Ces repères orientent la revue ; ils ne démontrent
ni l'applicabilité d'une règle ni la conformité du projet.
"""

KNOWLEDGE_MARKDOWN = """# Repères modification cloison — qualification P2

Contexte de travail : circulation d'un ERP et phase PRO, uniquement pour ce
fixture synthétique.

Pour une modification de cloison, examiner selon les données disponibles :
largeur de circulation et accessibilité, portes et sens de passage,
compartimentage/incendie si applicable, traversées de réseaux, phasage, lots et
coût.

Ces repères sont du Knowledge candidat. Ils n'établissent ni l'applicabilité
d'une exigence, ni la conformité, ni une décision architecturale.
"""


class P2LiveFixtureError(ValueError):
    pass


def _id(prefix: str, token: str) -> str:
    return f"{prefix}.{token}"


def _stable(project_id: str, object_id: str, family: str, name: str) -> dict[str, Any]:
    return {
        "stable_object_id": object_id,
        "project_ref": project_id,
        "object_family": family,
        "nomenclature": {
            "internal_code": object_id[-12:],
            "display_name": name,
        },
    }


def _representation(project_id: str, representation_id: str) -> dict[str, Any]:
    return {
        "representation_id": representation_id,
        "project_ref": project_id,
        "source_artifact_ref": "drawing://synthetic-p2/A-101",
        "source_kind": "drawing",
        "identifiers": [{"scheme": "drawing.fragment", "value": "A-101/RDC"}],
        "observed_at": "2026-09-06T12:00:00Z",
        "binding_ref": "fixture.p2.live.plan",
        "adapter_version": "1.0",
        "freshness_token": "P2-LIVE-A101-r1",
        "proof_status": "candidate",
    }


def _attribute(
    object_id: str,
    claim_id: str,
    representation_id: str,
    key: str,
    value: float,
    unit: str,
) -> dict[str, Any]:
    return {
        "attribute_claim_id": claim_id,
        "subject_ref": {"entity_type": "stable_object", "entity_id": object_id},
        "attribute_key": key,
        "value": {"value_type": "number", "value": value, "unit": unit},
        "assertion_mode": "observed",
        "source_authority": "project_working_document",
        "proof_status": "candidate",
        "source_representation_refs": [representation_id],
    }


def _relation(
    subject_id: str,
    object_id: str,
    claim_id: str,
    representation_id: str,
    relation_type: str,
) -> dict[str, Any]:
    return {
        "relation_claim_id": claim_id,
        "subject_ref": {"entity_type": "stable_object", "entity_id": subject_id},
        "relation_type": relation_type,
        "object_ref": {"entity_type": "stable_object", "entity_id": object_id},
        "assertion_mode": "human_asserted",
        "source_authority": "project_working_document",
        "proof_status": "accepted_as_support",
        "source_representation_refs": [representation_id],
    }


def _entity(entity_type: str, entity_id: str) -> dict[str, str]:
    return {"entity_type": entity_type, "entity_id": f"{entity_type}:{entity_id}"}


def _write_ingestion_contract(
    root: Path,
    *,
    project_id: str,
    token: str,
    actor: str,
) -> Path:
    payload = {
        "object_type": "task_contract",
        "object_id": f"p2.synthetic.{token}.document-intake",
        "contract_id": f"p2.synthetic.{token}.document-intake",
        "status": "active",
        "requested_by": actor,
        "exposure_surface": "human_oidc_revision_upload",
        "approval_ceiling": "technical_access_only",
        "intent": {"summary": "Synthetic P2 live qualification document intake"},
        "scope": {
            "dossier": project_id,
            "parent_project_id": project_id,
            "declared_sources": [
                {"source_ref": CCTP_SOURCE_REF, "title": "CCTP synthétique", "traceable": True},
                {"source_ref": KNOWLEDGE_SOURCE_REF, "title": "Repères synthétiques", "traceable": True},
            ],
        },
        "expected_outputs": ["technical_document_capture"],
        "forbidden_scope": [
            "project_scope_expansion",
            "professional_approval",
            "external_send",
        ],
    }
    path = root / "task_contract.yaml"
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def _supporting_context(
    conn: psycopg.Connection,
    *,
    project_id: str,
    token: str,
    actor: str,
) -> tuple[str, str]:
    with tempfile.TemporaryDirectory(prefix="pantheon-p2-live-") as directory:
        root = Path(directory)
        (root / CCTP_SOURCE_REF).parent.mkdir(parents=True, exist_ok=True)
        (root / CCTP_SOURCE_REF).write_text(CCTP_MARKDOWN, encoding="utf-8")
        (root / KNOWLEDGE_SOURCE_REF).write_text(KNOWLEDGE_SOURCE_MARKDOWN, encoding="utf-8")
        task_contract = load_contract(
            _write_ingestion_contract(
                root,
                project_id=project_id,
                token=token,
                actor=actor,
            )
        )
        store.ingest(
            conn,
            task_contract,
            root,
            ingestion_id=f"p2-live-{token}",
        )

    cctp = store.get_document_card(conn, project_id, CCTP_SOURCE_REF)
    knowledge_source = store.get_document_card(conn, project_id, KNOWLEDGE_SOURCE_REF)
    chunk_refs = list(knowledge_source.get("extraction", {}).get("chunk_refs") or [])
    if not chunk_refs:
        raise P2LiveFixtureError("synthetic Knowledge source produced no current chunks")

    knowledge_id = _id("knowledge.synthetic-p2", token)
    published = knowledge.publish_knowledge(
        conn,
        knowledge_id=knowledge_id,
        document_id=knowledge_source["document_id"],
        title="Repères modification cloison — qualification P2",
        family="reglementations",
        markdown=KNOWLEDGE_MARKDOWN,
        source_chunk_refs=chunk_refs,
        created_by="system:p2-live-fixture",
        actor_kind="system",
        idempotency_key=f"p2-live-{token}-knowledge",
        review_status="generated_unreviewed",
    )
    if published.get("review_status") != "generated_unreviewed":
        raise P2LiveFixtureError("synthetic Knowledge unexpectedly acquired a reviewed status")
    return cctp["document_id"], knowledge_id


def _scenario(conn: psycopg.Connection, *, variant: str, actor: str) -> dict[str, str]:
    token = uuid.uuid4().hex
    identity_variant = variant in {IDENTITY_NONDETERMINANT, IDENTITY_DETERMINANT}
    project_id = _id(f"project.synthetic-p2-{variant.lower()}", token)
    project = agency_data.create_project(
        conn,
        project_id=project_id,
        code=(
            f"P2I{'D' if variant == IDENTITY_DETERMINANT else 'N'}-{token[:10]}".upper()
            if identity_variant
            else f"P2{variant.upper()}-{token[:10]}".upper()
        ),
        display_name=(
            "Qualification synthétique P2 identité"
            if identity_variant
            else f"Qualification synthétique P2 {variant.upper()}"
        ),
        description="Fixture synthétique non client pour qualification live Hermès P2.",
        actor=actor,
        actor_kind="human",
        idempotency_key=f"p2-live-{token}-project",
    )
    project_id = project["project_id"]

    ids = {
        "partition": _id("apu.synthetic-p2.partition", token),
        "partition_alt": _id("apu.synthetic-p2.partition-alt", token),
        "corridor": _id("apu.synthetic-p2.corridor", token),
        "office": _id("apu.synthetic-p2.office", token),
        "door": _id("apu.synthetic-p2.door", token),
        "duct": _id("apu.synthetic-p2.duct", token),
        "unrelated": _id("apu.synthetic-p2.unrelated", token),
    }
    representation_id = _id("representation.synthetic-p2", token)

    stable_objects = [
        _stable(project_id, ids["partition"], "element", "Cloison P2"),
        _stable(project_id, ids["corridor"], "spatial", "Circulation P2"),
        _stable(project_id, ids["office"], "spatial", "Bureau P2"),
        _stable(project_id, ids["door"], "element", "Porte P2"),
        _stable(project_id, ids["duct"], "system", "Réseau technique P2"),
        _stable(project_id, ids["unrelated"], "element", "Objet hors contexte P2"),
    ]
    attribute_claims = [
        _attribute(
            ids["partition"],
            _id("attribute.synthetic-p2.partition", token),
            representation_id,
            "geometry.thickness",
            120,
            "mm",
        ),
        _attribute(
            ids["corridor"],
            _id("attribute.synthetic-p2.corridor", token),
            representation_id,
            "geometry.clear_width",
            1400,
            "mm",
        ),
    ]
    if identity_variant:
        stable_objects.append(
            _stable(project_id, ids["partition_alt"], "element", "Cloison P2")
        )
        attribute_claims.append(
            _attribute(
                ids["partition_alt"],
                _id("attribute.synthetic-p2.partition-alt", token),
                representation_id,
                "geometry.thickness",
                120,
                "mm",
            )
        )

    relation_claims = []
    if variant != IDENTITY_NONDETERMINANT:
        office_subject = (
            ids["partition_alt"] if variant == IDENTITY_DETERMINANT else ids["partition"]
        )
        relation_claims = [
            _relation(
                ids["partition"],
                ids["corridor"],
                _id("relation.synthetic-p2.corridor", token),
                representation_id,
                "spatial.adjacent_to",
            ),
            _relation(
                office_subject,
                ids["office"],
                _id("relation.synthetic-p2.office", token),
                representation_id,
                "spatial.adjacent_to",
            ),
            _relation(
                ids["door"],
                ids["partition"],
                _id("relation.synthetic-p2.door", token),
                representation_id,
                "architecture.hosted_by",
            ),
            _relation(
                ids["duct"],
                ids["partition"],
                _id("relation.synthetic-p2.duct", token),
                representation_id,
                "building_services.passes_through",
            ),
        ]

    apu_owner.store_reviewed_dossier(
        conn,
        project_id=project_id,
        stable_objects=stable_objects,
        source_representations=[_representation(project_id, representation_id)],
        attribute_claims=attribute_claims,
        relation_claims=relation_claims,
        review_ref=f"fixture:synthetic-p2:{token}",
        actor="system:p2-live-fixture",
        idempotency_key=f"p2-live-{token}-apu",
    )

    if identity_variant:
        return {"token": token, "project_id": project_id, **ids}

    information = agency_information.create_information(
        conn,
        project_id=project_id,
        title="Prémisse de contexte P2",
        category="Programme",
        source_type="document",
        source_ref=f"fixture://synthetic-p2/{token}/programme",
        index_label="A01",
        summary="Circulation ERP étudiée en phase PRO.",
        details=(
            "Pour cette qualification synthétique uniquement, la circulation adjacente "
            "est déclarée comme participant à un cheminement ERP. Cette Information est "
            "une prémisse de contexte, pas une preuve de conformité."
        ),
        actor_kind="system",
        author="system:p2-live-fixture",
    )
    document_id, knowledge_id = _supporting_context(
        conn,
        project_id=project_id,
        token=token,
        actor=actor,
    )
    return {
        "token": token,
        "project_id": project_id,
        **ids,
        "information_id": information["information_id"],
        "document_id": document_id,
        "knowledge_id": knowledge_id,
    }


def prepare_p2_live_admission(
    conn: psycopg.Connection,
    *,
    variant: str,
    actor: str,
    ack: str,
    ttl_seconds: int = 1800,
) -> dict[str, Any]:
    """Create one fresh, unconsumed synthetic P2 admission for live qualification."""

    if ack != "SYNTHETIC_ONLY":
        raise P2LiveFixtureError("preparation requires explicit SYNTHETIC_ONLY acknowledgement")
    variant = str(variant or "").strip().upper()
    actor = str(actor or "").strip()
    if variant not in VARIANTS:
        raise P2LiveFixtureError(
            "variant must be A, B, IDENTITY-NONDETERMINANT or IDENTITY-DETERMINANT"
        )
    if not actor:
        raise P2LiveFixtureError("a human operator actor is required")

    state = _scenario(conn, variant=variant, actor=actor)
    identity_ambiguity: dict[str, Any] | None = None
    if variant in {"A", "B"}:
        selected = [_entity("stable_object", state["partition"])]
        if variant == "B":
            selected.extend(
                [
                    _entity("stable_object", state["corridor"]),
                    _entity("stable_object", state["office"]),
                    _entity("stable_object", state["door"]),
                    _entity("stable_object", state["duct"]),
                    _entity("information", state["information_id"]),
                    _entity("document", state["document_id"]),
                    _entity("knowledge", state["knowledge_id"]),
                ]
            )
    else:
        determinant = variant == IDENTITY_DETERMINANT
        candidate_target_refs = [
            _entity("stable_object", state["partition"]),
            _entity("stable_object", state["partition_alt"]),
        ]
        selected = list(candidate_target_refs)
        if determinant:
            selected.extend(
                [
                    _entity("stable_object", state["corridor"]),
                    _entity("stable_object", state["office"]),
                    _entity("stable_object", state["door"]),
                    _entity("stable_object", state["duct"]),
                ]
            )
        identity_ambiguity = {
            "class": "determinant" if determinant else "non_determinant",
            "candidate_target_refs": candidate_target_refs,
            "qualification_expectation": (
                "ask_targeted_identity_clarification"
                if determinant
                else "continue_with_explicit_uncertainty"
            ),
            "safe_non_success_fallback": (
                "explicitly_refuse_to_conclude" if determinant else None
            ),
            "silent_identity_selection_allowed": False,
            "cognitive_result_observed": False,
        }

    envelope = {
        "root_entity": {
            "entity_id": f"project:{state['project_id']}",
            "entity_type": "project",
        },
        "descendants": [],
        "source_refs": [],
        "explicit_additions": [],
        "explicit_exclusions": [],
        "scope_widened_implicitly": False,
    }
    preview = hermes_handoff_preview.build_preview(
        question=LIVE_QUESTION,
        card_context_envelope=envelope,
        selected_context=selected,
    )
    handoff = hermes_handoff_store.submit_handoff(
        conn,
        actor=actor,
        idempotency_key=f"p2-live-{state['token']}-handoff",
        question=LIVE_QUESTION,
        preview=preview,
        card_context_envelope=envelope,
        selected_context=selected,
        include_declared_descendants=False,
    )
    admission = hermes_execution.admit_handoff(
        conn,
        handoff_id=handoff["handoff_id"],
        actor=actor,
        idempotency_key=f"p2-live-{state['token']}-admission",
        ttl_seconds=ttl_seconds,
    )
    if admission.get("admission_state") != "admitted" or not admission.get(
        "ready_for_external_runtime"
    ):
        raise P2LiveFixtureError("fresh synthetic admission is not ready for the external runtime")

    non_equivalences = [
        "synthetic fixture != professional project truth",
        "Knowledge candidate != applicable requirement",
        "Execution Admission != Hermes run",
        "prepared admission != runtime authorization beyond this bounded task",
        "technical receipt != Evidence",
    ]
    if identity_ambiguity is not None:
        non_equivalences.extend(
            [
                "two admitted candidates != one selected target",
                "identity clarification != sibling claim validation",
            ]
        )

    return {
        "object_type": "p2_live_admission_preparation_receipt",
        "synthetic": True,
        "variant": variant,
        "question": LIVE_QUESTION,
        "project_id": state["project_id"],
        "handoff_id": handoff["handoff_id"],
        "work_issue_id": handoff["work_issue"]["issue_id"],
        "admission_id": admission["admission_id"],
        "admission_state": admission["admission_state"],
        "expires_at": admission["expires_at"],
        "selected_context": selected,
        "unrelated_object_ref": _entity("stable_object", state["unrelated"]),
        "identity_ambiguity": identity_ambiguity,
        "execution_started": False,
        "hermes_run_created": False,
        "knowledge_review_status": (
            "generated_unreviewed" if variant in {"A", "B"} else None
        ),
        "apu_review_ref_is_synthetic_fixture": True,
        "technical_receipt_is_evidence": False,
        "professional_validation": False,
        "production_authorization": False,
        "non_equivalences": non_equivalences,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare a fresh synthetic P2 A/B or identity-ambiguity admission "
            "for live Hermes qualification."
        )
    )
    parser.add_argument("--variant", choices=VARIANTS, required=True)
    parser.add_argument("--ack", default="")
    parser.add_argument(
        "--actor",
        default=os.environ.get("PANTHEON_OPERATOR_ACTOR", ""),
        help="Human operator identity; prefer PANTHEON_OPERATOR_ACTOR.",
    )
    parser.add_argument("--ttl-seconds", type=int, default=1800)
    parser.add_argument(
        "--dsn",
        default=os.environ.get("MVP_PG_DSN", ""),
        help="Optional PostgreSQL DSN; otherwise store configuration is used.",
    )
    return parser


def _error(message: str) -> int:
    print(
        json.dumps(
            {
                "object_type": "p2_live_admission_preparation_error",
                "error": message,
                "synthetic": True,
                "execution_started": False,
                "technical_receipt_is_evidence": False,
                "production_authorization": False,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        file=sys.stderr,
    )
    return 1


def main() -> int:
    args = build_parser().parse_args()
    if not str(args.actor or "").strip():
        return _error("--actor / PANTHEON_OPERATOR_ACTOR is required")

    conn = None
    try:
        conn = store.connect(args.dsn or None)
        receipt = prepare_p2_live_admission(
            conn,
            variant=args.variant,
            actor=args.actor,
            ack=args.ack,
            ttl_seconds=args.ttl_seconds,
        )
        print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (P2LiveFixtureError, ValueError, OSError) as exc:
        return _error(str(exc))
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
