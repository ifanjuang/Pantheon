# Architecture Communication Patterns

Status: template index — candidate-only, documented non-implemented.

This directory classifies architecture-domain mail and letter candidates by professional act, recipient, project phase, risk level and approval gate.

It is not a mail generator, not a sending tool, not a legal opinion, not an insurer notice, not a project record and not a memory system.

## Purpose

Examples created in Pantheon are starting points. Future mail and letter candidates may be produced on the fly by the Pantheon role collective, but they must enter a stable classification before reuse.

```text
A draft is not a precedent.
A recurring draft may become a pattern candidate.
A pattern candidate is not approved wording.
Approved external transmission remains a human decision.
```

## Classification axes

Every communication pattern must be classified by:

```text
recipient_class:
  project_owner | contractor | BET | bureau_de_controle | AMO | administration | insurer_or_counsel | internal | mixed

professional_act:
  inform | clarify | request | remind | alert | record | reserve | refuse | propose | escalate | prepare_reception | close_point | other

project_phase:
  prospect | contract | DIAG | ESQ | APS | APD | DP_PC | PRO | DCE | ACT | EXE_VISA | DET | AOR | GPA | dispute_watch | archive

risk_level:
  Bas | Moyen | Haut | Critique

source_basis:
  example_only | chatgpt_project_context_candidate | partial_project_sources | complete_project_sources

output_status:
  wording_fragment | draft_candidate | pattern_candidate | approved_for_internal_use | rejected | obsolete

external_gate:
  not_applicable | human_review_required | source_pack_required | senior_review_required | insurer_or_counsel_review_required
```

## Directory map

```text
00_index/
  registry and metadata format

01_client_moa/
  reminders to project owner, role boundaries, decision requests, reception preparation

02_contractors/
  contractor status requests, open items, scope clarification, execution responsibility reminders

03_bet_control/
  BET / bureau de controle / SPS / technical-role coordination patterns

04_admin_third_parties/
  administration, concessionnaires, syndic, AMO / finance actors

05_reception_reserves_gpa/
  reception preparation, reserve tracking, GPA follow-up

06_role_drift_risk/
  role drift, mission perimeter, source completion, professional-risk gates

07_internal_review/
  internal notes, risk summaries, evidence tree outputs, review checklists

08_rejected_or_obsolete/
  wording patterns rejected, superseded or too risky
```

## Rule for on-the-fly additions

When Pantheon role collective creates a new communication candidate, it must be stored with a metadata header before reuse:

```text
pattern_id:
title:
status:
recipient_class:
professional_act:
project_phase:
risk_level:
source_basis:
external_gate:
created_from:
required_sources:
forbidden_uses:
review_notes:
```

## Boundary

```text
Communication patterns are preparation material.
They do not send.
They do not approve.
They do not replace source verification.
They do not replace professional review.
```
