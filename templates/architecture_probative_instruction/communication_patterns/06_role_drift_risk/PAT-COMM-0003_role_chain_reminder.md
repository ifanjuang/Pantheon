# PAT-COMM-0003 — Role-chain reminder MOA / MOE / contractor

Status: pattern_candidate — candidate-only, documented non-implemented.

This pattern frames a role-chain reminder when project-owner decisions, MOE assistance and contractor obligations risk being mixed.

It is not approved wording, not legal advice, not a claim response, not a project record and not external communication.

## Metadata

```text
pattern_id: PAT-COMM-0003
title: Role-chain reminder MOA / MOE / contractor
folder: 06_role_drift_risk
status: pattern_candidate
recipient_class: mixed
professional_act: clarify / alert
project_phase: DET / AOR / dispute_watch
risk_level: Haut
source_basis: chatgpt_project_context_candidate
external_gate: source_pack_required + human_review_required
related_slice: role_drift_early_warning_slice
```

## Purpose

Use when a message must restate the professional chain without accusing any actor.

The pattern should separate:

```text
project owner:
  arbitrates, validates choices, signs markets, accepts or refuses quotes, decides payment and reception.

contractor:
  prices, verifies, executes, corrects, answers on schedule and lot scope.

architect / MOE:
  assists, alerts, coordinates, checks coherence and records observations within mission scope.

additional mission:
  required when the expected service exceeds the current contract perimeter.
```

## Required sources before case use

```text
mission contract;
contractor market / quote;
latest project-owner instruction;
latest contractor request or response;
site report / meeting minutes;
current phase and open issues;
source showing why role clarification is needed.
```

## Required output structure

```text
1. state reason for clarification;
2. separate each role;
3. state what is inside MOE mission;
4. state what would require additional mission or amendment;
5. request missing source material or decision;
6. avoid admission, accusation and final responsibility language;
7. stop at human review gate.
```

## Forbidden uses

```text
Do not use as blame allocation.
Do not use as formal notice.
Do not use to decide contractor liability.
Do not use to close reserves.
Do not use to validate payment.
Do not use when an official challenge, counsel or insurer trigger exists without senior review.
```

## Human gate

```text
external_transmission_allowed: no by default
requires_source_review: true
requires_human_review: true
senior_review_if_risk_critical: true
```
