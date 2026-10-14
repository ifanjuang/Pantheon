# PAT-COMM-0005 — PRO / DCE non-EXE footer candidate

Status: pattern_candidate — candidate-only, documented non-implemented.

This pattern classifies a footer / document-status note used to prevent PRO or DCE material from being read as execution drawings.

It is not approved wording, not EXE validation, not BET review replacement, not contractor instruction and not external communication.

## Metadata

```text
pattern_id: PAT-COMM-0005
title: PRO / DCE non-EXE footer candidate
folder: 03_bet_control
status: pattern_candidate
recipient_class: BET / contractor / mixed
professional_act: clarify
project_phase: PRO / DCE / EXE_VISA
risk_level: Haut
source_basis: partial_project_sources
external_gate: source_pack_required + human_review_required
related_slice: pro_exe_responsibility_slice
```

## Purpose

Use when a plan, note or technical document produced in PRO / DCE may be misread as:

```text
execution plan;
final dimension validation;
contractor method approval;
BET calculation replacement;
instruction to execute;
VISA comment beyond mission scope.
```

## Required sources before case use

```text
plan sheets and indices;
cartouche and current footer;
mission contract;
BET mission if applicable;
CCTP / contractor responsibility clauses;
current phase;
recipient list;
related correspondence asking for clarification or validation.
```

## Required output structure

```text
1. identify the document status;
2. state that the document is design / consultation material;
3. state that it does not constitute execution drawing;
4. place final dimensions, calculations, assemblies and methods in the proper contractor / BET chain;
5. keep wording compatible with the actual contract;
6. require architect approval before issue.
```

## Candidate wording boundary

The pattern may support wording equivalent to:

```text
Document de conception / consultation — ne vaut pas plan d'execution.
```

Any longer footer must be adapted to the project contract, phase, document type and responsible parties.

## Forbidden uses

```text
Do not use as EXE validation.
Do not use as BET review replacement.
Do not use as contractor instruction.
Do not use if the document is actually an EXE deliverable without requalification.
Do not use to avoid a required VISA review.
Do not use without checking mission scope.
```

## Human gate

```text
external_transmission_allowed: no by default
requires_source_review: true
requires_human_review: true
```
