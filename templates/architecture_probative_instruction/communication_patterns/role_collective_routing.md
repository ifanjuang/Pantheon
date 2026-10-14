# Role Collective Routing — Communication Patterns

Status: template routing note — candidate-only, documented non-implemented.

This file describes how on-the-fly communication candidates should be classified when produced by the Pantheon role collective.

It does not define final Pantheon roles. It only provides a routing discipline for communication pattern creation.

## Principle

```text
On-the-fly production is allowed.
On-the-fly classification is mandatory.
On-the-fly transmission is forbidden by default.
```

## Routing steps

```text
1. Identify the professional act.
2. Identify the recipient class.
3. Identify the project phase.
4. Identify the risk level.
5. Identify the source basis.
6. Identify the required gate.
7. Place the candidate in the right folder.
8. Mark whether it is a one-off draft or a reusable pattern candidate.
```

## Role responsibilities as abstract functions

```text
arbitration_role:
  classifies decision status and unresolved tension.

risk_review_role:
  detects professional-risk signals and required review gates.

evidence_role:
  checks source basis, missing sources, dates and contradictions.

writing_role:
  prepares wording candidates inside the approved structure.

memory_role:
  prevents automatic promotion to canonical memory.

human_role:
  decides whether wording is accepted, corrected, rejected or escalated.
```

## Folder selection rule

```text
recipient first, risk second.
```

Examples:

```text
Client role reminder -> 01_client_moa.
Contractor status request -> 02_contractors.
BET PRO / EXE clarification -> 03_bet_control.
Reception reserve reminder -> 05_reception_reserves_gpa.
High-risk role drift note -> 06_role_drift_risk.
Internal evidence summary -> 07_internal_review.
Unsafe wording -> 08_rejected_or_obsolete.
```

## Promotion rule

```text
draft_candidate -> pattern_candidate:
  requires at least one human review and removal of project-specific facts.

pattern_candidate -> approved_for_internal_use:
  requires source-basis clarity, risk classification and forbidden-use notes.

approved_for_internal_use -> external use:
  never automatic; always case-by-case human approval.
```

## Boundary

```text
The role collective may propose.
Pantheon classifies.
Evidence constrains.
Human review decides.
Validated patterns remain internal preparation material unless explicitly approved for a case.
```
