---
name: construction-schedule-review
description: "Use to create, analyze or revise a construction schedule when scope, task dependencies, calendars, resources, procurement constraints, milestones, buffers and progress status must remain explicit."
metadata:
  owner_layer: hermes
  status: candidate_template_only
  pantheon_role: ATHENA
  governed_by: docs/domain-packs/architecture/AGENCY_DOMAIN_PACK.md
---

# Construction schedule review

Own sequencing and feasibility assumptions. A date list is not a validated
works programme, and a proposed programme is not an instruction to contractors.

## Required method

1. Identify schedule state: baseline, current update, forecast, recovery option
   or as-built record. Establish scope, status date, calendar and granularity.
2. Derive a work breakdown from admitted project scope. Record dependencies,
   durations, handoffs, access, curing or drying, approvals, procurement lead
   times, inspections and external constraints.
3. Distinguish observed progress from reported progress and forecast. Preserve
   assumptions for resources, productivity and concurrency.
4. Check logical gaps, impossible overlaps, missing activities, milestone
   constraints, float or buffer and the path driving completion.
5. When results change, reforecast affected successors and expose alternatives,
   trade-offs and required decisions instead of silently moving one date.

## Result contract

Return: schedule state and status date; scope and assumptions; sequenced task
table; dependencies and milestones; driving constraints; missing inputs; risks
and options; readiness. Require confirmation before publishing a baseline or
communicating commitments externally.

```text
target date != supported duration
reported progress != observed progress
proposed sequence != contractor instruction
```
