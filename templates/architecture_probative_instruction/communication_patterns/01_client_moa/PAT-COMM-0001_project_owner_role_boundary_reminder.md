# PAT-COMM-0001 — Project-owner role boundary reminder

Status: pattern_candidate — candidate-only, documented non-implemented.

This pattern frames a cautious reminder to the project owner when roles, validations, contractor obligations, payments, reserves or mission scope begin to blur.

It is not approved wording, not legal advice, not a claim response, not a project record and not external communication.

## Metadata

```text
pattern_id: PAT-COMM-0001
title: Project-owner role boundary reminder
folder: 01_client_moa
status: pattern_candidate
recipient_class: project_owner
professional_act: clarify / remind
project_phase: DET / AOR / dispute_watch
risk_level: Haut
source_basis: chatgpt_project_context_candidate
external_gate: source_pack_required + human_review_required
related_slice: role_drift_early_warning_slice
```

## Purpose

Use when a project owner may be expecting the MOE to absorb, validate or resolve matters that must remain separated between:

```text
project-owner decision;
contractor obligation;
MOE mission scope;
additional mission requirement;
source completion before conclusion.
```

## Required sources before case use

```text
architecture mission contract;
relevant amendments;
contractor quote / market;
meeting minutes or site reports;
client written decisions;
contractor exchanges;
payment / reserve / reception status if relevant;
prior warnings or role reminders.
```

## Required output structure

```text
1. acknowledge the open points without admission;
2. state that review must be source-based;
3. separate MOA decisions from contractor obligations;
4. state MOE mission perimeter;
5. mark additional service / amendment if needed;
6. ask for missing source material or decision;
7. keep external gate visible.
```

## Forbidden uses

```text
Do not use as admission.
Do not use as blame allocation.
Do not use as legal position.
Do not use as payment decision.
Do not use as reserve closure.
Do not use when a critical professional-risk trigger exists without senior review.
```

## Human gate

```text
external_transmission_allowed: no by default
requires_source_review: true
requires_human_review: true
```
