# Rite Examples

Status: active support doctrine - fictional examples for rite usage.

This document contains fictional examples showing how rites may be used in governed work.

It does not define new rites.

It does not implement runtime behavior.

It does not define prompts, schemas, tests, runtime-client components, Hermes skills or executable workflows.

Runtime/client/authority placement is inherited from `HERMES_INTEGRATION.md`: optional compatible runtime clients expose runtime interaction only, Hermes/the external runtime executes admitted work, Pantheon Cockpit projects governed rite and decision state, and Pantheon retains governance authority.

## Purpose

P0 defined the rite mechanism.

P1 protected it from drift.

P2 made it easier to select and size.

P3 tests whether the mechanism remains usable in realistic situations without becoming a hidden workflow.

These examples are fictional and non-executable.

They should be read as governance examples only.

## Example 1 - Divergence Controlee for a Pantheon architecture decision

### Situation

Pantheon must decide how to project rites in the governed user surface.

Several options exist:

- keep rites as hidden governance notes;
- show rites as visible Pantheon Cockpit status cards;
- expose only Rite Review Cards inside Evidence Packs;
- project rites only when ZEUS opens a User Decision Gate;
- optionally mirror non-authoritative runtime-interaction status in a compatible client.

### Symptom

```text
Too many plausible options.
Premature convergence risk.
UI labels may create runtime illusion.
```

### Candidate rite

```text
RITE_DIVERGENCE_CONTROLEE.md
```

### Mode

```text
mode_standard
```

Reason: the task affects interface semantics and may create governance drift if labels imply execution.

### Rite Review Card

```text
rite_id: RITE_DIVERGENCE_CONTROLEE
trigger_reason: Several governed-projection options exist and premature convergence could create runtime illusion.
proposed_by: ATHENA
ZEUS_status: rite_completed_with_reserve
role_viewpoints_involved: ATHENA, APOLLO, THEMIS, IRIS, ZEUS
inputs_considered: Pantheon Cockpit boundary, optional runtime-client boundary, rites doctrine, invocation policy, anti-patterns
outputs_retained: project rite review only as governance status, not runtime state
option_clusters: hidden-only, visible-status, Evidence-Pack-only, User-Decision-Gate-only, runtime-client-mirror
traps_detected: `rite_active` may imply a process is running; `rite_completed` may imply approval
blocked_claims: a runtime client or Cockpit projection can execute or complete a rite by UI state
User_Decision_Gate: not required if wording is changed to non-runtime labels
Evidence_Pack_impact: record UI label decision and rationale if implemented
memory_impact: no Registre Probatoire entry; possible scoped Register Candidate after approval
next_allowed_action: update Cockpit wording in documentation only
```

### What must not happen

- A runtime client or Cockpit projection must not execute the rite.
- A status label must not imply approval.
- The chosen display pattern must not become a plugin or workflow engine.

## Example 2 - Autocritique Contradictoire for a client email

### Situation

A professional email to a client explains that a document is suitable for transmission, but the evidence is partial.

The draft is clear and convincing.

That is precisely the risk.

### Symptom

```text
Candidate output looks too convincing.
Professional delivery risk.
Evidence may be incomplete.
```

### Candidate rite

```text
AUTOCRITIQUE_CONTRADICTOIRE.md
```

### Mode

```text
mode_full
```

Reason: the output may be externally transmitted and could affect professional responsibility.

### Rite Review Card

```text
rite_id: AUTOCRITIQUE_CONTRADICTOIRE
trigger_reason: External client email may overstate readiness or certainty.
proposed_by: THEMIS
ZEUS_status: rite_completed_with_reserve
role_viewpoints_involved: THEMIS, APOLLO, ARGOS, IRIS, ZEUS
inputs_considered: draft email, available sources, known uncertainties, approval boundary
outputs_retained: revise wording to distinguish estimate, evidence, reserve and requested confirmation
claim_separation: fact = document exists; interpretation = appears sufficient; recommendation = transmit with reserve
unsupported_claims: any statement that the file is fully compliant without final verification
contradictions: none detected, but evidence coverage is partial
blocked_claims: `the file is complete and compliant` unless independently verified
User_Decision_Gate: required if client asks to transmit despite missing evidence
Evidence_Pack_impact: record visible evidence and reserve wording
memory_impact: no memory candidate
next_allowed_action: send revised draft only after user approval
```

### What must not happen

- Clear prose must not be treated as verification.
- The rite must not approve transmission.
- Client-facing confidence must not exceed the evidence.

## Example 3 - Refondation de Session for a Hydre-like long thread

### Situation

A long conversation has produced many variants, partial corrections, competing vocabulary and old decisions that no longer match the current objective.

Continuing inside the same frame creates more confusion than progress.

### Symptom

```text
Session has too many contradictory iterations.
Corrections improve locally but degrade globally.
Old context contaminates current decision.
```

### Candidate rite

```text
REFONDATION_DE_SESSION.md
```

### Mode

```text
mode_full
```

Reason: refoundation can erase tensions if done carelessly.

### Rite Review Card

```text
rite_id: REFONDATION_DE_SESSION
trigger_reason: Current session contains conflicting variants and no longer provides a clean Task Contract.
proposed_by: ZEUS
ZEUS_status: task_split_required
role_viewpoints_involved: ZEUS, ATHENA, ARGOS, THEMIS, IRIS
inputs_considered: current thread summary, validated decisions, unresolved contradictions, source references
outputs_retained: new Task Contract draft and preserved invariants
preserved_invariants: Pantheon governs; Hermes/external runtime executes; compatible runtime clients expose interaction only; Pantheon Cockpit projects governed state; rites do not execute
preserved_sources: validated governance docs and relevant user decisions
preserved_user_decisions: keep rites as methods, not gods or agents
unresolved_tensions: Cockpit/runtime-client labels still need non-runtime wording alignment
discarded_noise: obsolete naming variants and abandoned branches
User_Decision_Gate: required if discarded variants include user-valued directions
Evidence_Pack_impact: record refoundation reason, preserved invariants and unresolved tensions
memory_impact: no Registre Probatoire entry; only explicit scoped Register Candidate after approval
next_allowed_action: start new Task Contract from preserved invariants and unresolved tensions
```

### What must not happen

- Reset must not delete contradiction.
- Discarded variants must not silently become memory.
- A user decision must not disappear without status.

## Example 4 - Rite conflict leading to User Decision Gate

### Situation

A task starts with Divergence Controlee because several options exist.

Autocritique Contradictoire then blocks the most attractive option because evidence is insufficient.

Concordance des Sources also reports source disagreement.

### Conflict

```text
Divergence opens options.
Autocritique blocks unsafe candidates.
Concordance slows delivery until claim status is clear.
```

### ZEUS procedural choice

```text
open_User_Decision_Gate
```

Reason: the system cannot safely choose between speed, evidence and risk without exposing the trade-off to the human.

### User Decision Gate summary

```text
conflict: attractive option lacks sufficient evidence
positions:
  ATHENA: option remains structurally useful
  THEMIS: delivery should be blocked without stronger evidence
  ARGOS: sources disagree and claim status is not stable
severity: high if externally delivered
options:
  1. proceed as internal draft only
  2. request stronger evidence
  3. choose a lower-risk option
  4. split the task
recommended_procedure: request stronger evidence or continue as internal draft only
impact_on_delivery: external delivery blocked
impact_on_memory: no memory candidate
impact_on_Evidence_Pack: preserve contradiction ledger and decision
```

### What must not happen

- ZEUS must not smooth the conflict into a confident answer.
- The user must not be shielded from a value or risk trade-off.
- A rite conflict must not become hidden orchestration.

## Final rule

Examples test usability.

They do not authorize execution.

They do not add new doctrine beyond the active rite policy.
