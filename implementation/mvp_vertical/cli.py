"""CLI: ingest a dossier, run a question, record a decision, propose retention."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import (
    apu_owner,
    decision_requests,
    human_access,
    register,
    storage_retention,
    store,
    terminal_gate_standin as gate,
)
from .policy_gate import HttpPolicyClient
from .contract import load_contract
from .documents import DoclingServeClient
from .naming import DocumentNameError
from .runner import run


def main() -> int:
    parser = argparse.ArgumentParser(prog="mvp-vertical")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="ingest the contract's declared sources")
    p_ingest.add_argument("--contract", required=True)
    p_ingest.add_argument("--root", default=".")
    p_ingest.add_argument(
        "--docling-url",
        help="self-hosted Docling Serve base URL (default: DOCLING_SERVE_URL or localhost:5001)",
    )

    p_intake = sub.add_parser(
        "intake-document",
        help="validate and ingest one explicitly declared document from a NAS mount",
    )
    p_intake.add_argument("--contract", required=True)
    p_intake.add_argument("--root", required=True, help="mounted project/NAS root")
    p_intake.add_argument("--source-ref", required=True, help="declared path below --root")
    p_intake.add_argument(
        "--subject-tag",
        action="append",
        dest="subject_tags",
        help="explicit subject tag for the Document card (repeatable; no automatic inference)",
    )
    p_intake.add_argument(
        "--docling-url",
        help="self-hosted Docling Serve base URL (default: DOCLING_SERVE_URL or localhost:5001)",
    )

    p_retain = sub.add_parser(
        "retain-document-version",
        help="retain exact bytes for one already-ingested technical document version",
    )
    p_retain.add_argument("--document-id", required=True)
    p_retain.add_argument("--version", required=True, type=int)
    p_retain.add_argument("--source-path", required=True)
    p_retain.add_argument(
        "--retention-root",
        required=True,
        help="explicit local/NAS retention root; no default provider is selected",
    )
    p_retain.add_argument(
        "--provider-ref",
        required=True,
        help="opaque identity of this configured storage binding",
    )

    p_bind = sub.add_parser(
        "bind-oidc-identity",
        help="bind one external OIDC identity to one governed human principal",
        description=(
            "Local provisioning only. This is the root of trust for every route "
            "behind require_principal, and it has no remote route by design: "
            "033_human_project_access_management.sql states that "
            "project.access.manage carries no IdP invitation authority and "
            "remains a locally provisioned bootstrap capability. The effect "
            "routes through the Pantheon chokepoint unless enforcement is "
            "explicitly declared disabled."
        ),
    )
    p_bind.add_argument("--principal-ref", required=True)
    p_bind.add_argument("--issuer", required=True, help="exact OIDC iss claim")
    p_bind.add_argument("--subject", required=True, help="exact OIDC sub claim")
    p_bind.add_argument(
        "--bound-by",
        required=True,
        help="the human taking responsibility for this binding",
    )
    p_bind.add_argument(
        "--decision-ref",
        required=True,
        help="immutable reference of the canonical human Decision this binding is made under",
    )
    p_bind.add_argument("--reason", default=None)
    p_bind.add_argument(
        "--approval-level",
        default="C3",
        help="approval ceiling the effect requires (default: C3)",
    )

    p_dossier = sub.add_parser(
        "store-reviewed-dossier",
        help="install one reviewed canonical APU dossier for one Project",
        description=(
            "Local provisioning only, and the reason is the same as "
            "bind-oidc-identity: review_ref is a caller-supplied string with "
            "nothing in apu_owner.py to verify it against, since no table of "
            "completed dossier reviews exists here. The chokepoint stands in "
            "for that missing verification, bound to the exact dossier content "
            "rather than to review_ref's name. The effect routes through the "
            "Pantheon chokepoint unless enforcement is explicitly declared "
            "disabled."
        ),
    )
    p_dossier.add_argument(
        "--dossier",
        required=True,
        help=(
            "YAML file with project_id, stable_objects, source_representations, "
            "attribute_claims, relation_claims and review_ref"
        ),
    )
    p_dossier.add_argument(
        "--actor",
        required=True,
        help="the human installing this dossier",
    )
    p_dossier.add_argument(
        "--decision-ref",
        required=True,
        help="immutable reference of the canonical human Decision this import is made under",
    )
    p_dossier.add_argument(
        "--idempotency-key",
        required=True,
    )
    p_dossier.add_argument(
        "--approval-level",
        default="C3",
        help="approval ceiling the effect requires (default: C3)",
    )

    p_card = sub.add_parser("document-card", help="project one ingested source as a card")
    p_card.add_argument("--dossier", required=True)
    p_card.add_argument("--source-ref", required=True)

    p_run = sub.add_parser("run", help="answer a question inside the contract's perimeter")
    p_run.add_argument("--contract", required=True)
    p_run.add_argument("--question", required=True)
    p_run.add_argument("--output", help="write the YAML stream here (default: stdout)")

    p_decide = sub.add_parser(
        "decide",
        help="record a HUMAN decision on a candidate stream (terminal gate stand-in)",
    )
    p_decide.add_argument("--candidates", required=True, help="YAML stream produced by `run`")
    p_decide.add_argument("--decision", required=True,
                          help="approve | refuse | request_revision | request_more_evidence")
    p_decide.add_argument("--decided-by", required=True,
                          help="human identity; the system may not sign (Gate 5)")
    p_decide.add_argument("--rationale", default="")
    p_decide.add_argument("--output", help="write the decision_record here (default: stdout)")

    p_register = sub.add_parser(
        "register",
        help="propose a Register Candidate from an approved decision (Block 3)",
    )
    p_register.add_argument("--decision-record", required=True,
                            help="YAML decision_record produced by `decide`")
    p_register.add_argument("--retention-authorized", action="store_true",
                            help="explicit human authorization to retain — required")
    p_register.add_argument("--authorized-by", required=True,
                            help="human authorizing retention; the system may not (Gate 5)")
    p_register.add_argument("--statement", required=True,
                            help="what is being registered (human-authored)")
    p_register.add_argument("--scope", required=True, help="where the statement applies")
    p_register.add_argument("--rationale", default="", help="why retention is authorized")
    p_register.add_argument("--output", help="write the register_candidate here (default: stdout)")

    args = parser.parse_args()

    # The decision gate touches no database and no contract perimeter — it only
    # records a human choice on an existing candidate stream.
    if args.command == "decide":
        documents = gate.load_candidates(args.candidates)
        try:
            record = gate.record_decision(
                documents,
                decision=args.decision,
                decided_by=args.decided_by,
                rationale=args.rationale,
            )
        except gate.GateRefusal as refusal:
            print(f"gate refused: {refusal}", file=sys.stderr)
            return 1
        text = gate.to_yaml(record)
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
            print(f"wrote {args.output} (decision_record: {record['decision']})")
        else:
            sys.stdout.write(text)
        return 0

    if args.command == "register":
        decision = register.load_decision_record(args.decision_record)
        try:
            candidate = register.propose_register_candidate(
                decision,
                retention_authorized=args.retention_authorized,
                statement=args.statement,
                scope=args.scope,
                authorized_by=args.authorized_by,
                rationale=args.rationale,
            )
        except register.RegisterRefusal as refusal:
            print(f"register refused: {refusal}", file=sys.stderr)
            return 1
        text = register.to_yaml(candidate)
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
            print(f"wrote {args.output} (register_candidate)")
        else:
            sys.stdout.write(text)
        return 0

    if args.command == "retain-document-version":
        import yaml

        conn = storage_retention.connect()
        try:
            try:
                result = storage_retention.retain_document_version(
                    conn,
                    document_id=args.document_id,
                    version=args.version,
                    source_path=Path(args.source_path),
                    retention_root=Path(args.retention_root),
                    storage_provider_ref=args.provider_ref,
                )
            except storage_retention.StorageRetentionError as exc:
                print(f"document retention refused: {exc}", file=sys.stderr)
                return 1
            sys.stdout.write(
                yaml.safe_dump(result, sort_keys=False, allow_unicode=True)
            )
            return 0
        finally:
            conn.close()

    if args.command == "bind-oidc-identity":
        import yaml

        enforcement = (os.getenv("MVP_POLICY_ENFORCEMENT", "required") or "").strip()
        if enforcement not in {"required", "disabled"}:
            print(
                "MVP_POLICY_ENFORCEMENT must be 'required' or 'disabled'; "
                f"got {enforcement!r}",
                file=sys.stderr,
            )
            return 1
        base_url = os.getenv("MVP_POLICY_API_URL", "").strip()
        api_key = os.getenv("MVP_POLICY_API_KEY", "").strip()
        policy_client = HttpPolicyClient(base_url, api_key) if base_url and api_key else None
        if enforcement == "required" and policy_client is None:
            print(
                "Pantheon policy decision point is not configured; binding an "
                "external identity to a governed principal cannot be admitted. "
                "Set MVP_POLICY_API_URL and MVP_POLICY_API_KEY, or declare "
                "MVP_POLICY_ENFORCEMENT=disabled explicitly.",
                file=sys.stderr,
            )
            return 1

        conn = human_access.connect()
        try:
            try:
                canonical_decision = decision_requests.policy_decision_payload(
                    conn,
                    args.decision_ref,
                    expectation={},
                )
                binding = human_access.bind_oidc_identity(
                    conn,
                    principal_ref=args.principal_ref,
                    issuer=args.issuer,
                    subject=args.subject,
                    bound_by=args.bound_by,
                    reason=args.reason,
                    policy_client=policy_client,
                    decision_payload=canonical_decision,
                    required_ceiling=args.approval_level,
                )
            except decision_requests.DecisionRequestError as exc:
                print(f"canonical Decision refused for identity binding: {exc}", file=sys.stderr)
                return 1
            except human_access.BindingPolicyUnavailable as exc:
                print(f"identity binding failed closed: {exc}", file=sys.stderr)
                return 1
            except human_access.HumanAccessError as exc:
                print(f"identity binding refused: {exc}", file=sys.stderr)
                return 1
            sys.stdout.write(
                yaml.safe_dump(
                    {
                        "binding": {
                            key: str(value)
                            for key, value in binding.items()
                            if key in {"binding_id", "principal_ref", "issuer", "subject"}
                        },
                        "policy_enforcement": enforcement,
                        "authority": {
                            "is_approval": False,
                            "is_professional_role": False,
                            "grants_any_access": False,
                        },
                    },
                    sort_keys=False,
                    allow_unicode=True,
                )
            )
            return 0
        finally:
            conn.close()

    if args.command == "store-reviewed-dossier":
        import yaml

        enforcement = (os.getenv("MVP_POLICY_ENFORCEMENT", "required") or "").strip()
        if enforcement not in {"required", "disabled"}:
            print(
                "MVP_POLICY_ENFORCEMENT must be 'required' or 'disabled'; "
                f"got {enforcement!r}",
                file=sys.stderr,
            )
            return 1
        base_url = os.getenv("MVP_POLICY_API_URL", "").strip()
        api_key = os.getenv("MVP_POLICY_API_KEY", "").strip()
        policy_client = HttpPolicyClient(base_url, api_key) if base_url and api_key else None
        if enforcement == "required" and policy_client is None:
            print(
                "Pantheon policy decision point is not configured; installing a "
                "reviewed APU dossier cannot be admitted. Set MVP_POLICY_API_URL "
                "and MVP_POLICY_API_KEY, or declare "
                "MVP_POLICY_ENFORCEMENT=disabled explicitly.",
                file=sys.stderr,
            )
            return 1

        dossier = yaml.safe_load(Path(args.dossier).read_text(encoding="utf-8"))
        if not isinstance(dossier, dict):
            print(f"{args.dossier}: not a single dossier document", file=sys.stderr)
            return 1
        required_fields = {
            "project_id", "stable_objects", "source_representations",
            "attribute_claims", "relation_claims", "review_ref",
        }
        missing = required_fields - dossier.keys()
        if missing:
            print(
                f"{args.dossier}: missing required field(s): {', '.join(sorted(missing))}",
                file=sys.stderr,
            )
            return 1

        conn = store.connect()
        try:
            try:
                canonical_decision = decision_requests.policy_decision_payload(
                    conn,
                    args.decision_ref,
                    expectation={},
                )
                installed = apu_owner.store_reviewed_dossier(
                    conn,
                    project_id=dossier["project_id"],
                    stable_objects=dossier["stable_objects"],
                    source_representations=dossier["source_representations"],
                    attribute_claims=dossier["attribute_claims"],
                    relation_claims=dossier["relation_claims"],
                    review_ref=dossier["review_ref"],
                    actor=args.actor,
                    idempotency_key=args.idempotency_key,
                    policy_client=policy_client,
                    decision_payload=canonical_decision,
                    required_ceiling=args.approval_level,
                )
            except decision_requests.DecisionRequestError as exc:
                print(f"canonical Decision refused for dossier import: {exc}", file=sys.stderr)
                return 1
            except apu_owner.ApuOwnerPolicyUnavailable as exc:
                print(f"dossier import failed closed: {exc}", file=sys.stderr)
                return 1
            except apu_owner.ApuOwnerError as exc:
                print(f"dossier import refused: {exc}", file=sys.stderr)
                return 1
            sys.stdout.write(
                yaml.safe_dump(
                    {
                        "project_id": installed["project_ref"],
                        "owner_revision": installed.get("owner_revision"),
                        "policy_enforcement": enforcement,
                        "authority": {
                            "is_approval": False,
                            "is_professional_validation": False,
                            "canonizes_apu_state": True,
                        },
                    },
                    sort_keys=False,
                    allow_unicode=True,
                )
            )
            return 0
        finally:
            conn.close()

    if args.command == "document-card":
        import yaml

        conn = store.connect()
        try:
            sys.stdout.write(
                yaml.safe_dump(
                    store.get_document_card(conn, args.dossier, args.source_ref),
                    sort_keys=False,
                    allow_unicode=True,
                )
            )
            return 0
        finally:
            conn.close()

    contract = load_contract(args.contract)
    conn = store.connect()
    try:
        if args.command == "ingest":
            docling = (
                DoclingServeClient(args.docling_url)
                if args.docling_url
                else DoclingServeClient.from_env()
            )
            n = store.ingest(conn, contract, Path(args.root), docling=docling)
            print(f"ingested {n} chunks from {len(contract.sources)} declared sources")
            return 0
        if args.command == "intake-document":
            docling = (
                DoclingServeClient(args.docling_url)
                if args.docling_url
                else DoclingServeClient.from_env()
            )
            try:
                n = store.intake_document(
                    conn,
                    contract,
                    Path(args.root),
                    args.source_ref,
                    docling=docling,
                    subject_tags=args.subject_tags,
                )
            except DocumentNameError as exc:
                print(f"document intake refused: {exc}", file=sys.stderr)
                return 1
            print(f"ingested {n} chunks from declared source {args.source_ref}")
            return 0
        output = run(conn, contract, args.question)
        text = output.to_yaml()
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
            print(f"wrote {args.output} ({output.kind})")
        else:
            sys.stdout.write(text)
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
