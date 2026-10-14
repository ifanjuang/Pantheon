# Iterative Deliberation Lifecycle

Status: candidate support doctrine — model for how multi-turn AI deliberation maps onto governed candidates, gates and registers.
Boundary profile: candidate_support_note.

This document is not canonical doctrine yet.

It does not implement a runtime, conversation engine, chat memory, summarizer, workflow engine, scheduler, queue, router, approval engine, memory engine, OpenWebUI Function, Hermes skill, connector or external action.

It defines how a long correction-and-clarification dialogue with an AI — many round-trips before a draft compte rendu (CR), more round-trips, then a finalized CR — is read in Pantheon terms without turning every message into a governance event.

## Purpose

Working with an AI is iterative: the right answer is not produced in one run. A real treatment is ten or more exchanges — corrections, clarifying questions, partial drafts, reversals — before anything is finalized.

This creates a tension:

```text
the dialogue is fluid, continuous and mostly ephemeral;
governance is discrete, by artifact, and must promote nothing silently.
```

The model resolves the tension by refusing the wrong premise: ten round-trips are not ten governance events. Pantheon does not govern every message; it governs what is promoted. Deliberation and governance run on two clocks.

## Core thesis

```text
A deliberation is an append-only event log (a search).
A CR candidate is a projection folded from that log.
The constraint/decision ledger is the reduced state of the fold.
A gate is a command.
A Registre Probatoire entry is the commit, under human decision.
```

In plain terms this is event-sourcing in governance clothing:

```text
trace      = event log
candidate  = materialized view
ledger     = reduced state
gate       = command
register   = canonical store
```

The `command` analogy is bounded: a Gate Card exposes a threshold and collects a
human decision. It does not itself command an execution. The command is the
human's, recorded; the gate is where it is asked for, not an actuator.

Two consequences drive everything else:

```text
a conversation is a search: most turns are abandoned paths, and that is normal;
what must be retained is not the paths but the constraints that pruned them
and the conclusion that survived.
```

The log is never replayed in full each turn. The projection is maintained incrementally and the reduced state is pinned.

## Two clocks

```text
Deliberation clock: continuous, cheap, mostly ephemeral. Lives in the cockpit
(OpenWebUI) and the runtime (Hermes). Pantheon does not gate it.

Governance clock: ticks only at consequential transitions — is this
transmissible? does it become canon? does it imply responsibility? The
chokepoint (PDP/PEP) is not inside the conversation loop; it sits at the
boundary where an artifact tries to act.
```

Governance cost must be proportional to consequence, not to message count.

## Turn taxonomy and optimal routing

Each turn is first classified, then routed at the lowest sufficient cost.

| Turn (what it does) | Touches consequence? | Optimal route |
|---|---|---|
| Cosmetic correction (wording, tone, format) | no | ephemeral; no governed object, no tracked revision |
| Structural correction (reorder, resection) | no | tracked revision of the same candidate; diff vN→vN+1 |
| Factual / value correction (`42.30`, not `43`) | yes (assertion) | revision + re-bind to evidence + cascade over downstream uses |
| Scope / mission extension | yes (responsibility) | gate the contract, not the output; Themis warns early |
| System asks a question | no | consultative facet expression; batch the blocking questions |
| Branch / exploration (two versions) | no | sibling candidates under one subject; the unchosen branch is a trace |
| Backtrack (revert to v3) | no | pointer to an immutable snapshot; O(1) revert |
| Context overflow → summary | trap | a constraint must not live only in fungible history |
| Cross-session resumption | yes (continuity) | rehydrate from candidate + ledger, never from the transcript |
| Finalization | yes | opens at minimum a diff-review gate over the delta; transmission, canonical memory or external effect opens a separate, additional gate |

Most turns fall in the "no" rows and carry zero governance friction. Only a few rows engage the governance clock.

## The three persistences

A deliberation is not a two-layer system (ephemeral vs canon). It has three layers, and the middle one is the load-bearing optimization.

```text
1. Fungible deliberation
   the turns, the attempts. Evaporates. Summarizable, discardable.

2. Constraint & decision ledger
   "never name the neighbour"; "surface = 42.30 validated at turn 6";
   "scope limited to taxation". Pinned. Survives summarization AND session end.
   This is the reduced state of the fold — a first-class governed object.
   It stays candidate / non-canonical: it is governed working state, not a
   parallel memory. It never bypasses the Registre Probatoire — only a gate
   promotes any of its elements to canon.

3. Canon (Registre Probatoire)
   committed only at a gate, under human decision.
```

Why layer 2 is decisive:

```text
If a constraint given at turn 2 lives only in chat history, a context summary
or an ephemeral-container restart silently drops it, and the final CR violates
a rule believed settled. This is the truncation failure mode raised one level:
state must never be reconstructed from a partial read of the transcript.
The remedy is identical to the file-level one — a single pinned source of
truth, projected from, never rebuilt from a window.
```

## Optimization principles

```text
Shift the governance signal left.
  Facets colour continuously, not only at the gate. A scope drift or a weak
  source is flagged at the turn it is introduced — the cheapest point to fix.
  Discovering at turn 9 that the draft already implied responsibility wastes
  eight turns.

Gate the contract, not the output.
  Validating "we cover taxation only" early is cheap; producing then discarding
  an out-of-scope CR is expensive. Detect drift before the work.

Front-load uncertainty.
  A round-trip costs latency and context. Batch the blocking questions
  (missing-information register) instead of one question per turn. Reduce the
  number of round-trips, not only their unit cost.

Everything in diff.
  Revision = diff. Finalization = diff review. Propagation = impact diff.
  Review becomes O(change), not O(document); diffs prevent silent drift.

Idempotent finalize.
  Re-finalizing an unchanged CR is a no-op. After a small correction, only the
  delta is re-gated, not the whole CR. Finalize opens at minimum a diff-review
  gate; it does not by itself authorize transmission, canonical memory or any
  external effect — each of those is a separate gate.

Per-assertion status, not per-document.
  Partial finalization is allowed: the surface is validated while the legal
  qualification stays candidate. The status label travels with each assertion.
```

## Invariants

```text
One candidate, N immutable revisions, with a traceable lineage.
A status label is inseparable from its artifact.
No automatic promotion: an abandoned candidate stays a candidate.
A factual correction re-binds evidence and cascades to dependent assertions.
A cross-turn contradiction is surfaced, not silently resolved by the last turn.
Resumption reads governed state (candidate + ledger), never the raw transcript.
```

## Edge situations

```text
Contradiction across turns:
  turn 8 reverses turn 3 — the ledger (Athena) surfaces the conflict; the human
  decides. The last turn does not win by default.

Draft leak:
  a draft CR must not circulate as fact before validation — the status is
  inseparable from the artifact (Hermes / Iris).

Evidence staleness:
  a source changes at turn 5 — assertions depending on it return to to_verify
  (Chronos / Mnemosyne) and cascade.

Abandonment:
  an abandoned candidate is never auto-promoted; it is archivable as trace.

Concurrency:
  two editors on one candidate — versioned revisions plus divergence detection
  (still: one object, N immutable revisions).
```

## Card-stack representation

This lifecycle is a Workflow Scene (see `CARD_STACK_MODEL.md`):

```text
the whole treatment      = one deck;
the draft CR             = a Result Candidate card with a closure status
                           (e.g. draft_allowed);
each correction          = a version of that card (diff vN→vN+1);
"finalize"               = a Gate card that opens;
validation               = a Promotion card → a Register Candidate;
the messages             = Trace cards, grouped/collapsed per the complexity budget;
the constraint ledger    = a pinned card that survives scene and session,
                           shown as governed working state, not canon.
```

Per `CARD_STACK_MODEL.md`, the ledger card displays governed
working state only; it is not a Register/Memory card and does not promote
itself.

## Relationship with existing documents

This document depends on and composes:

```text
CARD_STACK_MODEL.md
ROLE_ACTIVATION_MODEL.md
EVIDENCE_MEMORY_CANONICALIZATION.md
schemas/register_link.schema.yaml
schemas/impact_review.schema.yaml
TASK_CONTRACT_REVISIONS.md
REVIEW_QUEUE.md
AUTHORITY_INDEX.md
```

`EVIDENCE_MEMORY_CANONICALIZATION.md` owns the dependency and impact-review semantics. `schemas/register_link.schema.yaml` and `schemas/impact_review.schema.yaml` carry the applied validation contracts; they record relations and proposed consequences but resolve nothing automatically.

It adds vocabulary and invariants; it promotes no schema, runtime, role, rite, memory rule or implementation.

Articulation notes:

```text
TASK_CONTRACT_REVISIONS.md:
  finalize-by-diff leans on the existing contract/task revision discipline. It
  must not create a second, competing revision vocabulary; revision identity and
  lineage are owned there.

AUTHORITY_INDEX.md / EVIDENCE_MEMORY_CANONICALIZATION.md:
  candidate / projection / ledger / register here reuse the existing status and
  register vocabulary. "register = commit" means a Registre Probatoire entry; it
  introduces no new canonical store and no parallel memory.

CARD_STACK_ROLE_QUALITY_ALIGNMENT.md:
  the ledger surfaces as a pinned working-state card, never as canon.
```

## Final rule

```text
The conversation is a free, fast search.
Governance is an incremental fold over it.
It retains the constraints and the proven conclusion, never the journey.
Most turns are ephemeral; only consequence ticks the governance clock.
State is never rebuilt from a partial view — at the file, the CR, or the dialogue.
The human decides at the gate.
```

## Open questions and validation plan

This note stays candidate support doctrine; it is not promoted to canonical
doctrine. Recorded from maintainer review (PR Pantheon-Next#231):

```text
Generic vs specialized:
  keep generic Pantheon support doctrine now, then specialize for architecture
  through a CR chantier example (leaning: generic first).

Constraint & Decision Ledger artifact:
  a candidate Markdown template before any schema proposal (leaning: template
  yes, schema not now).

Does finalize always open a gate:
  finalize opens at minimum a diff-review gate; an external action (transmission,
  Notion write, email) opens a separate gate (leaning recorded above and folded
  into the model).
```

Validation before any promotion: exercise the lifecycle on one CR chantier run
covering 10 corrections, 1 old pinned constraint, 1 factual correction, 1
backtrack, 1 contradiction, 1 draft, 1 finalization, 1 candidate email and 1
Notion gate — then re-review.

## Boundary

This document is a method/governance candidate.

It creates no runtime, no conversation engine, no chat memory, no summarizer, no UI, no schema, no database, no tool call, no connector, no skill, no approval engine and no memory engine. Any implementation belongs later in the appropriate exposure surface or execution runtime, under the existing placement doctrine, and remains a candidate until reviewed.
