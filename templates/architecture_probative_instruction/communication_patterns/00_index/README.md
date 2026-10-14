# Communication Pattern Index

Status: template index — candidate-only, documented non-implemented.

This folder holds registry and metadata rules for architecture communication patterns.

## Pattern metadata header

Every pattern file should begin with:

```text
pattern_id:
title:
status: wording_fragment | draft_candidate | pattern_candidate | approved_for_internal_use | rejected | obsolete
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

## Status rules

```text
wording_fragment:
  reusable phrase only; not a full response.

draft_candidate:
  one-off draft candidate; not reusable until reviewed.

pattern_candidate:
  generalized pattern candidate; source and risk gates still apply.

approved_for_internal_use:
  usable as internal preparation material only.

rejected:
  known unsafe or refused pattern.

obsolete:
  superseded by later pattern or doctrine.
```

## Default gate

```text
external_transmission_allowed:
  no by default
```
