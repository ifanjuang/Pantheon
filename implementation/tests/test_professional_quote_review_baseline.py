"""Observed baseline for the first Pantheon-Next#827 professional quote-review vertical.

This test executes the current project-aware stand-in path and reports what it
can produce without turning today's limitations into permanent expectations.

The human oracle remains separate. A passing baseline is not professional
acceptance: it proves that the observation is reproducible and that the hard
governance/source boundaries remain intact while allowing later behavior to
improve.
"""

from __future__ import annotations

import copy
import json
import os
import re
import uuid
from pathlib import Path

import psycopg
import pytest
import yaml

from mvp_vertical import (
    agency_data,
    human_access,
    project_document_currentness,
    project_documents,
    runner,
    store,
)
from mvp_vertical.contract import TaskContract, load_contract


ROOT = Path(__file__).resolve().parents[1]
ORACLE = yaml.safe_load(
    (ROOT / "tests/fixtures/professional_quote_review_cases.yaml").read_text(encoding="utf-8")
)
PURPOSE = "current_working"


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _connect_or_skip():
    try:
        conn = human_access.connect()
    except psycopg.OperationalError as exc:  # pragma: no cover - local unit-only lane
        if os.environ.get("MVP_PG_DSN"):
            raise
        pytest.skip(f"PostgreSQL/pgvector unreachable: {exc}")

    try:
        project_document_currentness.ensure_schema(conn)
    except Exception:
        conn.close()
        raise
    return conn


def _qualification_contract() -> tuple[TaskContract, str]:
    """Clone the corpus contract into an isolated runtime project/dossier.

    The human-labelled corpus remains ``devis_reprise``. Only the persistence
    namespace used by this executable qualification is unique so retries against
    a reused PostgreSQL database cannot collide with an earlier run or mutate
    another test's technical source ownership.
    """
    base = load_contract(ROOT / "dossiers/devis_reprise/task_contract.yaml")
    project_id = _id("q827-project")
    raw = copy.deepcopy(base.raw)
    raw["scope"]["dossier"] = project_id
    raw["scope"]["parent_project_id"] = project_id
    return (
        TaskContract(
            raw=raw,
            path=base.path,
            dossier=project_id,
            sources=base.sources,
            forbidden=base.forbidden,
        ),
        project_id,
    )


def _prepare_project_review_scope(conn, contract: TaskContract, project_id: str):
    """Materialize the selected synthetic sources as bounded Project Documents.

    The events establish only an internal working posture for this qualification.
    They do not assign contractual/execution authority or claim real-project
    applicability.
    """
    agency_data.create_project(
        conn,
        project_id=project_id,
        code=f"Q827-{project_id[-12:].upper()}",
        display_name="Qualification devis reprise",
        contacts=[],
        actor="qualification-reviewer",
        actor_kind="human",
        idempotency_key=_id("project-create"),
    )
    conn.commit()

    store.ingest(conn, contract, ROOT, ingestion_id=_id("qualification-ingestion"))

    requested_documents: list[tuple[str, str]] = []
    for index, source_ref in enumerate(ORACLE["declared_source_refs"], start=1):
        row = conn.execute(
            """
            SELECT d.document_id, v.version
              FROM source_documents d
              JOIN document_versions v ON v.document_id = d.document_id
             WHERE d.dossier = %s AND d.source_ref = %s
             ORDER BY v.version DESC
             LIMIT 1
            """,
            (contract.dossier, source_ref),
        ).fetchone()
        assert row is not None, source_ref
        source_document_id, source_version = row

        logical = project_documents.create_document(
            conn,
            parent_project_id=project_id,
            document_type="REFERENCE",
            title=f"Qualification source {index}",
            actor="qualification-reviewer",
            actor_kind="human",
            idempotency_key=_id(f"document-{index}"),
        )
        conn.commit()
        linked = project_documents.link_revision(
            conn,
            document_id=logical["document_id"],
            source_document_id=source_document_id,
            source_version=source_version,
            revision_label="qualification-current",
            actor="qualification-reviewer",
            actor_kind="human",
            idempotency_key=_id(f"revision-{index}"),
        )
        conn.commit()
        project_document_currentness.record_version_event(
            conn,
            document_version_id=linked["version_id"],
            event_type="issued",
            new_status="issued",
            new_effect_class="working_revision",
            new_authority_status="internal_working_authority",
            actor="qualification-reviewer",
            actor_kind="human",
            idempotency_key=_id(f"currentness-{index}"),
            reason="synthetic Pantheon-Next#827 baseline qualification only",
            basis_refs=["issue:Pantheon-Next#827", "oracle:professional_quote_review_cases"],
        )
        conn.commit()
        requested_documents.append((logical["document_id"], PURPOSE))

    principal_ref = _id("principal")
    human_access.create_principal(
        conn,
        principal_ref=principal_ref,
        created_by="qualification-reviewer",
    )
    human_access.grant_access(
        conn,
        principal_ref=principal_ref,
        project_id=project_id,
        resource_type="project",
        resource_id=project_id,
        action="project.read",
        granted_by="qualification-reviewer",
    )
    for document_id, _purpose in requested_documents:
        human_access.grant_access(
            conn,
            principal_ref=principal_ref,
            project_id=project_id,
            resource_type="project_document",
            resource_id=document_id,
            action="document.read",
            granted_by="qualification-reviewer",
        )
    conn.commit()

    principal = human_access.PrincipalContext(
        principal_ref=principal_ref,
        issuer="qualification",
        subject="professional-review-baseline",
    )
    return principal, tuple(requested_documents)


def _explicit_claim_types(body: str) -> list[str]:
    """Read only explicit DOCUMENT_REVIEW claim-type labels from candidate prose.

    This deliberately does not infer professional meaning from free text. If a
    behavior wants qualification credit, it must make the existing claim type
    explicit rather than rely on this observer to act as a second reviewer.
    """
    return sorted(
        set(
            re.findall(
                r"(?im)^\s*claim_type\s*:\s*([a-z_]+)\s*$",
                body,
            )
        )
    )


def _normalized(text: str) -> str:
    return " ".join(text.casefold().split())


def test_current_project_aware_professional_review_baseline_is_observed_not_assumed() -> None:
    conn = _connect_or_skip()
    contract, project_id = _qualification_contract()

    try:
        principal, requested_documents = _prepare_project_review_scope(
            conn,
            contract,
            project_id,
        )
        output = runner.run_accessible_applicable(
            conn,
            principal,
            contract,
            ORACLE["review_request"],
            project_id=project_id,
            requested_documents=requested_documents,
        )

        assert output.kind == "candidates"
        result_candidate, evidence_pack = output.documents
        body = result_candidate["body"]
        normalized_body = _normalized(body)

        expected_attention_cases = [
            case for case in ORACLE["cases"] if case.get("expected_claim_type")
        ]
        claim_types = _explicit_claim_types(body)
        explicitly_typed_cases = [
            case["case_id"]
            for case in expected_attention_cases
            if case["expected_claim_type"] in claim_types
        ]
        forbidden_hits = sorted(
            {
                claim
                for case in ORACLE["cases"]
                for claim in case["forbidden_claims"]
                if _normalized(claim) in normalized_body
            }
        )

        declared = set(ORACLE["declared_source_refs"])
        controls = set(ORACLE["control_source_refs"])
        resolved_sources = {
            source["source_ref"]
            for source in evidence_pack["source_scope_resolution"]["sources"]
        }
        evidence_sources = {
            item["source_ref"] for item in evidence_pack["evidence_items"]
        }

        observation = {
            "corpus_id": ORACLE["corpus_id"],
            "execution_path": "runner.run_accessible_applicable+DeterministicDrafter",
            "output_kind": output.kind,
            "result_status": result_candidate["status"],
            "resolved_source_count": len(resolved_sources),
            "resolved_source_refs": sorted(resolved_sources),
            "evidence_item_count": len(evidence_pack["evidence_items"]),
            "evidence_source_refs": sorted(evidence_sources),
            "retrieval_source_coverage_complete": evidence_sources == declared,
            "missing_evidence_source_refs": sorted(declared - evidence_sources),
            "evidence_previews": [
                {
                    "source_ref": item["source_ref"],
                    "claim": item["claim"],
                }
                for item in evidence_pack["evidence_items"]
            ],
            "expected_attention_case_count": len(expected_attention_cases),
            "explicit_claim_types": claim_types,
            "explicitly_typed_case_count": len(explicitly_typed_cases),
            "explicitly_typed_case_ids": explicitly_typed_cases,
            "forbidden_claim_hits": forbidden_hits,
            "claim_support_status": result_candidate["claim_support_review"]["status"],
            "external_action_authorized": result_candidate["external_action_authorized"],
        }
        print(
            "PROFESSIONAL_QUOTE_REVIEW_BASELINE="
            + json.dumps(observation, ensure_ascii=False, sort_keys=True)
        )

        # Hard boundaries: the qualification may narrow the declared perimeter,
        # but it may not leak the planted old revision or invent authority.
        assert resolved_sources == declared
        assert controls.isdisjoint(resolved_sources)
        assert evidence_sources == declared
        assert controls.isdisjoint(evidence_sources)
        assert result_candidate["external_action_authorized"] is False
        assert evidence_pack["source_scope_resolution"]["authority"] == {
            "decides_professional_approval": False,
            "admits_evidence": False,
            "widens_task_contract": False,
        }
        assert forbidden_hits == []

        # Source coverage is now regression-protected. Professional finding
        # quality remains observational and may improve without changing this test.
        assert len(expected_attention_cases) == 7
    finally:
        conn.close()
