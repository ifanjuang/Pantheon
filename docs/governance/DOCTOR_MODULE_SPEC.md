# Doctor Module Specification

Status: active support doctrine — audit-only module boundary and output contract.

Doctor is a governance-support module for documentary and procedural audit.

It is not an editor, fixer, promoter, approver, execution runtime, repository mutator, scheduler, queue, hidden workflow runner, memory engine or decision authority.

Runtime/client/authority placement is inherited from `HERMES_INTEGRATION.md`: Hermes/the external runtime may execute admitted audit preparation, optional compatible runtime clients may expose runtime interaction, Pantheon Cockpit projects governed audit status and decision material, and neither surface gains approval or governance authority.

## Purpose

Doctor exists to make defects visible before a consequential decision is made.

It helps review doctrine, specs, examples, templates, module declarations, domain packs, operational proposals and repository changes without silently changing their status.

Doctor's job is narrow:

```text
Doctor verifies, cites, classifies and flags.
Doctor does not edit, fix, promote or decide.
```

## Boundary phrase

```text
Doctor audits.
Zeus arbitrates.
Pantheon records status.
Humans decide.
```

## What Doctor may do

Doctor may:

- verify coherence, completeness, contradictions, missing evidence, outdated status, boundary drift and source alignment;
- cite the documents, sections, issues, pull requests, review threads or external sources used in the audit;
- classify each finding with a review status;
- flag unresolved tensions, risks, missing approvals and decisions that require Zeus or human arbitration;
- produce an Audit Report Candidate;
- recommend possible next actions without applying them.

Doctor may read repository documents, discussions, issues, pull requests and review threads when relevant.

Doctor may compare a proposal against active doctrine.

Doctor may say that a correction is needed.

Doctor must not perform the correction.

## What Doctor must not do

Doctor must not:

- edit files;
- apply patches;
- rewrite doctrine;
- correct examples or templates;
- promote a candidate into active doctrine;
- approve a source, output, memory item or external action;
- merge code;
- create or modify `operations/` files;
- create executable schemas, tests, platform code, Docker files or runtime configuration;
- install or run tools;
- dispatch work to an external runtime;
- persist a Registre Probatoire entry;
- hide unresolved tensions behind a clean summary.

If a task requires modification, Doctor may only report that modification is needed and identify the appropriate authority or follow-up path.

## Inputs

Doctor may receive:

```text
Task Contract
repository path or diff
issue / PR / review-thread reference
document candidate
module candidate
domain-pack candidate
operations proposal
source list
expected doctrine reference
review question
```

Inputs remain candidates until reviewed under the relevant governance document.

## Outputs

Doctor outputs an Audit Report Candidate.

Minimum shape:

```text
audited_element:
sources_checked:
findings:
  - finding:
    classification:
    risk:
    evidence:
    decision_expected:
    recommendation_not_applied:
summary:
residual_uncertainties:
```

The report may be projected by Pantheon Cockpit, exposed as candidate material through a compatible runtime client, or used by Zeus as review material.

The report is not, by itself, approval, correction, promotion, proof or memory.

## Classification vocabulary

Doctor may classify findings as:

```text
conformant
incomplete
contradictory
outdated
candidate_only
non_canonical
boundary_drift
runtime_creep
missing_evidence
missing_approval
to_verify
to_arbitrate
out_of_scope
```

These labels are review classifications only.

They do not change the canonical status of the audited element.

## Evidence expectation

Every substantive finding must carry evidence.

Evidence may include:

- repository file path;
- section heading;
- line reference when available;
- issue or pull request reference;
- review-thread reference;
- external source citation when the claim depends on external information;
- explicit statement that evidence is missing.

Doctor must distinguish:

```text
fact
interpretation
recommendation
```

## Relationship to Zeus

Doctor does not arbitrate.

Doctor can mark a finding as `to_arbitrate` and explain the tension.

Zeus decides procedure, status and whether the issue is accepted, refused, deferred or escalated.

Doctor may support Zeus by making the proof chain legible.

Doctor must not impersonate Zeus.

## Relationship to Hermes

Hermes may execute checking, extraction, source retrieval, diff analysis or report preparation under a Task Contract.

When Hermes performs Doctor-like work, its output remains a candidate.

Hermes must not use Doctor as permission to patch, merge, approve, promote memory or mutate doctrine.

## Relationship to runtime clients and Pantheon Cockpit

A compatible runtime client may expose Doctor runtime interaction, report candidates, warnings or requests for review. It is not the governed decision surface.

Pantheon Cockpit may project Doctor reports, classifications, warnings and governed decision-gate state.

Neither a runtime client nor a Cockpit projection may turn a Doctor report into approval, a Registre Probatoire entry, doctrine or an automatic repository modification.

```text
runtime interaction != governed projection
projection != approval
projection != persistence
```

## Relationship to operations

Doctor may audit an `operations/` proposal.

Doctor must verify whether a governing documentation spec has been explicitly validated before any `operations/` file exists or changes.

Doctor may flag an operations proposal as blocked, incomplete or to arbitrate.

Doctor must not create or modify files under `operations/`.

## Anti-patterns

```text
Doctor report = corrected document
Doctor classification = Zeus decision
Doctor recommendation = approval
Doctor source check = proof
Doctor audit = merge permission
Doctor warning = automatic refusal
Doctor memory note = Registre Probatoire entry
Doctor operations review = operations file authorization
```

## Status rule

Doctor's output status is always candidate until reviewed.

```text
Audit Report Candidate in.
Decision material out.
No silent mutation.
```

## Final rule

```text
Doctor makes the defect visible.
Doctor does not make the decision disappear.
```
