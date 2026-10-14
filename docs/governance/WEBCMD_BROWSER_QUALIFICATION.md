# Webcmd browser qualification

Status: candidate qualification note — no selection, installation, activation or task authorization.

Tracking issue: Pantheon-Next#1051.

Observed qualification baseline:

```text
Pantheon-Next/main = c986b0560ae991fb659109d6270d4e0d3156008b
Hermes             = v0.21.3 / v2026.9.14
Webcmd              = 0.8.4 @ 719a75786a43158d1a9112830797610cda68bb03
```

This baseline records review provenance only. Any live qualification must record
its own exact Pantheon/Hermes/Webcmd refs and effective profile/settings.

## Purpose

Qualify `agentrhq/webcmd` only as a replaceable Hermes-side browser-control implementation candidate when it demonstrates a concrete advantage over the currently reviewed Hermes native browser capability.

This note does not create a Pantheon browser runtime, browser-memory authority, MCP sequencing path or orchestration layer.

## Existing selection rule

```text
Hermes native capability sufficient
-> use it
-> no external binding required

capability gap demonstrated
-> compare one bounded external candidate
-> qualify it
-> select only if the demonstrated benefit justifies the added runtime surface
```

## Candidate responsibility

Webcmd combines live browser control with a local `site-memory` intended to retain useful navigation context such as observed pages, actions, workflows, endpoints and pitfalls.

For Pantheon/Hermes purposes:

```text
Webcmd site-memory
= runtime procedural/navigation memory
!= Pantheon Memory
!= Hindsight project/document memory
!= Knowledge
!= Evidence
!= source authority

Webcmd browser result
= runtime candidate/observation material
!= authorization
!= Evidence
!= professional validation
```

If selected later, Webcmd remains an external Hermes-side skill/runtime adapter. Pantheon continues to own only the existing governance boundary around scope, consequential effects, Evidence and approval.

## Adjacent capabilities

Keep the responsibilities distinct:

```text
Crawlberg / public-web evidence intake
!= interactive authenticated browser control

Hindsight / external runtime memory
!= navigation procedure memory

Hermes native browser capability
!= Webcmd adoption

Webcmd installed
!= Webcmd selected

Webcmd selected
!= Webcmd activated

Webcmd activated
!= browser action authorized
```

No Hindsight ingestion or Pantheon memory promotion is required for Webcmd `site-memory`.

## Qualification target

Compare the same bounded task corpus under the same model/profile/settings:

```text
A — Hermes native browser capability
B — Hermes + pinned Webcmd candidate
```

The qualification must record the exact Hermes and Webcmd artifacts used.

Reuse the empirical controls already owned by
`HERMES_IMPROVEMENT_PATH.md` / Pantheon-Next#1108 rather than creating a browser-specific
benchmark owner: matched repeated trials, predeclared review/aggregation rules,
time-local counterbalanced arm order, equal experiment-controlled initial mutable
state, and workload-class conclusions aggregated across independent cases rather
than pooled repetition counts. If those controls cannot be demonstrated, the
comparison is inconclusive.

For repeated-run `site-memory` value, both arms start from equivalent clean initial
state. State intentionally created by the first run may then persist only inside
that arm's declared repeated-run sequence; cross-arm memory, profile, workspace or
cache leakage invalidates the comparison.

### Minimum corpus

Use synthetic/test accounts and non-sensitive data only for the first pass.

1. unfamiliar public site — read-only retrieval;
2. repeated navigation on the same site — measure second-run reuse;
3. authenticated synthetic/test account — read-only retrieval;
4. multi-step form/workflow stopping before consequential submission;
5. two concurrent isolated Sessions when practical.

### Minimum observations

Record:

- first-run success/failure;
- repeated-run success/failure;
- agent turns;
- token use where observable;
- elapsed time where observable;
- authenticated-session behavior;
- profile/session isolation;
- parallel-session isolation;
- timeout/error recovery;
- stale-navigation-memory behavior after a controlled page/state change;
- whether repeated execution materially reduces rediscovery.

A favorable upstream benchmark is not sufficient for selection.

## Privacy and runtime posture

Start from the narrowest local posture supported by the pinned Webcmd release:

```text
local execution only
Webcmd Cloud unused
global site-memory seed lookup disabled
candidate public-IP lookup disabled
isolated dedicated browser profile
explicit Sessions
no consequential browser mutation by default
no automatic external transmission
```

Re-check the exact upstream privacy/runtime behavior at qualification time rather than relying on this note as release documentation. The reviewed 0.8.4 README states that first access may use a Webcmd Cloud seed, so the local-only arm must prove that external seed lookup is disabled rather than assuming it from installation mode.

## Governance invariants

```text
reachable browser != authorized action
browser login != source admission
retrieved page != true
site-memory recall != current page state
site-memory recall != Evidence
successful browser run != professional validation
runtime success != authorization
runtime approval != Pantheon approval
profile cookie availability != permission to use every reachable account
```

Any consequential browser effect remains behind the existing Pantheon-owned effect boundary defined by Pantheon-Next#1109: raw consequential credentials/tools are not exposed directly to Hermes/Webcmd; a governed effect request reaches the effect owner/PEP before execution. Runtime hooks remain defense in depth, not the authority chokepoint.

## Failure cases to exercise

At least one controlled failure must test each relevant class before selection:

- stale or changed page structure;
- expired or unavailable session;
- timeout or interrupted browser action;
- concurrent Session isolation;
- site-memory failure or unavailable learned context;
- exact outcome unknown after interruption when applicable.

The required behavior is bounded failure or explicit uncertainty, not silent widening or blind retry.

## Decision

Close Pantheon-Next#1051 with exactly one posture:

```text
preferred_candidate
fallback_candidate
watch
rejected
```

`preferred_candidate` is justified only when Webcmd materially improves representative repeated/authenticated workflows over Hermes native browser after considering reliability, cost, privacy, operational complexity and replacement cost.

If Hermes native browser is sufficient, keep Webcmd unselected.

## Non-goals

```text
no new Pantheon browser engine
no new Role / Rite / governed Space
no browser-specific authority owner
no second memory authority
no automatic Webcmd -> Hindsight promotion
no automatic Webcmd -> Pantheon Memory promotion
no new MCP server solely for Webcmd
no duplicate public-web evidence pipeline
no production/client-account rollout in the first qualification
no selection from upstream benchmark claims alone
```

## Exit criteria

- exact candidate artifacts recorded;
- local-only privacy posture verified;
- same-task A/B comparison completed under the existing Pantheon-Next#1108 matched-run controls;
- first-run versus repeated-run behavior measured;
- session/profile isolation observed;
- at least one stale-memory/failure case exercised;
- consequential actions remain governed through existing effect boundaries;
- no navigation memory promoted to governed memory/Evidence;
- workload-class preference, if any, is supported across independent representative cases rather than repetition count alone;
- one explicit selection posture recorded;
- no new governance abstraction introduced unless a residual failure proves the current owners insufficient.
