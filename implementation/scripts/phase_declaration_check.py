"""Check per-project phase declarations against a disposable PostgreSQL database.

Creates a test project, declares phases, compares them with the card phase and
optionally stores one Project Anatomy claim at a phase, then prints what the
Cockpit projection reports. Writes only to the database named by MVP_PG_DSN; it
reads no project file (--document is only a text reference). Never point it at
a production database.

  python scripts/phase_declaration_check.py --code FLOQUET --card-phase DCE \
      --declare ESQ:2025-01-10 --declare APS:2025-03-01 --claim-phase PRO
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid

from mvp_vertical import agency_claims, agency_data, apu_owner
from mvp_vertical.project_anatomy_projection import get_project_anatomy_projection


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", required=True)
    parser.add_argument("--card-phase", default=None)
    parser.add_argument("--declare", action="append", default=[], help="PHASE:AAAA-MM-JJ")
    parser.add_argument("--claim-phase", default=None)
    parser.add_argument("--document", default="document")
    args = parser.parse_args()

    conn = agency_data.connect()
    conn.execute(apu_owner.MIGRATION.read_text(encoding="utf-8"))
    conn.commit()
    project_id = f"test-{args.code.lower()}-{uuid.uuid4().hex[:8]}"
    conn.execute(
        "INSERT INTO agency_projects (project_id, code, display_name, phase, created_by, updated_by) "
        "VALUES (%s, %s, %s, %s, 'test', 'test')",
        (project_id, f"{args.code}-{uuid.uuid4().hex[:6]}", args.code, args.card_phase),
    )
    conn.commit()
    print(f"Projet de test : {project_id} (phase de la fiche : {args.card_phase})")

    for item in args.declare:
        phase, _, date = item.partition(":")
        try:
            agency_claims.record_claim(
                conn, project_id=project_id, claim_type="phase", value=phase,
                actor="human:test", effective_at=f"{date}T00:00:00Z" if date else None,
            )
            print(f"  déclarée : {phase} au {date}")
        except agency_claims.AgencyClaimError as exc:
            print(f"  REFUSÉE  : {phase} -> {exc}")

    print("Cohérence fiche / déclarations :")
    print(json.dumps(agency_claims.project_phase_consistency(conn, project_id), ensure_ascii=False, indent=2))

    if args.claim_phase:
        object_id, rep_id, claim_id = (f"{p}-{uuid.uuid4().hex[:8]}" for p in ("obj", "rep", "claim"))
        try:
            apu_owner.store_reviewed_dossier(
                conn, project_id=project_id,
                stable_objects=[{"stable_object_id": object_id, "project_ref": project_id,
                                 "object_family": "element",
                                 "nomenclature": {"internal_code": "TEST", "display_name": "Objet de test"}}],
                source_representations=[{"representation_id": rep_id, "project_ref": project_id,
                                         "source_artifact_ref": args.document, "source_kind": "document",
                                         "identifiers": [{"scheme": "document.fragment", "value": rep_id}],
                                         "observed_at": "2026-11-05T09:00:00Z", "binding_ref": "test",
                                         "adapter_version": "test", "freshness_token": "test",
                                         "proof_status": "candidate"}],
                attribute_claims=[{"attribute_claim_id": claim_id,
                                   "subject_ref": {"entity_type": "stable_object", "entity_id": object_id},
                                   "attribute_key": "test.phase", "value": {"value_type": "text", "value": "test"},
                                   "assertion_mode": "observed", "source_authority": "project_working_document",
                                   "proof_status": "candidate", "source_representation_refs": [rep_id],
                                   "validity": {"established_at_phase": args.claim_phase}}],
                relation_claims=[], review_ref="review:test", actor="human:test",
                idempotency_key=f"test-{uuid.uuid4().hex}",
            )
            conn.commit()
            lens = get_project_anatomy_projection(conn, project_id=project_id)["phases"]
            print(f"Élément de l'Anatomie à la phase {args.claim_phase} : accepté")
            print(json.dumps({"status": lens["status"], "declared_phases": lens["declared_phases"],
                              "hors_phases_declarees": [i["phase"] for i in lens["claims_outside_declared_phases"]]},
                             ensure_ascii=False, indent=2))
        except apu_owner.ApuOwnerError as exc:
            conn.rollback()
            print(f"Élément de l'Anatomie à la phase {args.claim_phase} : REFUSÉ -> {exc}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
