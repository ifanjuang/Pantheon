# Architecture memory integrity review — fictional example

Status: fictional example — documented non-implemented.

This example shows a non-destructive shadow reconstruction of one architecture
project scope. It is educational support only. It does not implement ingestion,
OCR, embeddings, a memory backend, a diff engine, a scheduler, an approval
engine or a register write.

## Situation

The fictional project `MAISON-AULNE` has three admitted sources:

| Source | Date | Current content | Allowed use |
|---|---|---|---|
| Approved meeting record `CR-2026-07-15` | 2026-07-15 | Client decision: single-flow ventilation. | project coordination candidate pending technical confirmation |
| Thermal note `NOTE-TH-A` | 2026-06-20 | Double-flow ventilation assumption. | technical-study support |
| Current DCE specification `CCTP-CVC-B` | 2026-07-01 | Double-flow ventilation specified. | consultation draft |

The current register projection still recalls:

```yaml
current_projection:
  subject: ventilation_system
  claim: double_flow
  source_refs: [NOTE-TH-A, CCTP-CVC-B]
  status: approved_for_internal_use
```

## External reconstruction candidate

Under a project-scoped Task Contract, Hermes or another external execution
runtime reads the admitted manifest up to a fixed cutoff and creates atomic
claim candidates. It does not read another project and it writes no register
status.

```yaml
shadow_projection_candidate:
  scope:
    scope_type: project
    scope_id: MAISON-AULNE
  source_cutoff: 2026-07-15T23:00:00+02:00
  claims:
    - claim_id: CLM-VENT-01
      statement: double_flow
      effective_date: 2026-06-20
      source_ref: NOTE-TH-A
      source_authority: approved_technical_report
    - claim_id: CLM-VENT-02
      statement: double_flow
      effective_date: 2026-07-01
      source_ref: CCTP-CVC-B
      source_authority: project_working_document
    - claim_id: CLM-VENT-03
      statement: single_flow
      effective_date: 2026-07-15
      source_ref: CR-2026-07-15
      source_authority: approved_client_decision
```

## Discrepancy candidate

The reconstruction does not declare that `single_flow` is true or that the DCE
must change. It exposes a possible decision-propagation gap:

```yaml
integrity_review_candidate:
  review_id: MIR-MAISON-AULNE-001
  scope:
    scope_type: project
    scope_id: MAISON-AULNE
  source_cutoff: 2026-07-15T23:00:00+02:00
  discrepancies:
    - discrepancy_id: DISC-VENT-001
      class: temporal_supersession_candidate
      subject_ref: ventilation_system
      current_claim_refs: [CLM-VENT-01, CLM-VENT-02]
      reconstructed_claim_refs: [CLM-VENT-03]
      evidence_refs: [NOTE-TH-A, CCTP-CVC-B, CR-2026-07-15]
      possible_impacts:
        - thermal-study consistency
        - CCTP CVC content
        - estimate and contractor consultation
      consequence_level: K3
      proposed_path: governance_path
      decision_status: pending_human
  authority_note: candidate comparison only; no register mutation
```

## Review card

The cockpit may expose one consequential card rather than every wording
difference:

```text
Ventilation decision may not be propagated

Current project projection: double flow
Latest admitted meeting decision: single flow
Current DCE specification: double flow

Possible impact: thermal study, CCTP, estimate and consultation

[Confirm the intended system]
[Request BET verification]
[Keep current DCE pending evidence]
[Open all sources]
```

These controls record a human decision candidate. They do not edit the CCTP,
approve the technical solution or promote a register entry by themselves.

## What may happen next

If the human confirms that the recent decision is valid for the intended use,
the governed path may produce:

- a supersession proposal for the previous register claim;
- an impact review covering the thermal note, specification and estimate;
- source-completion or BET-verification requests;
- document-update candidates;
- an audit event after an authorized status change.

If the human rejects or defers the change, the competing claims remain visible.

## Boundaries exercised

```text
latest source != automatically authoritative
reconstruction != truth
runtime success != evidence
discrepancy != resolution
candidate projection != register mutation
```

Pantheon governs the comparison status and required path. The external runtime
executes the bounded reconstruction. The exposure surface displays the review.
The human decides.
