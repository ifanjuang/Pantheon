# Review Queue

Status: candidate support doctrine — governed review queue rule.
Boundary profile: candidate_support_note.

This document defines the governance rule for a review queue that surfaces doubtful, conflicting, stale, low-confidence or consequential items to a human decision.

It is documentation only.

It does not implement a queue, scheduler, database table, UI gesture, swipe interface, notification system, OpenWebUI action, Hermes skill, workflow runtime, approval engine or memory engine.

In abstract form:

```text
The exposure surface exposes.
The execution runtime executes.
Pantheon governs.
```

## Purpose

A document, workflow, ingestion or Register Candidate process may produce unresolved items.

Examples:

```text
duplicate candidates
near-duplicate candidates
possible conflicts
low-confidence facts
stale facts
unverified claims
contradicted claims
scope uncertainty
pending Register Candidates
rename or contact-update proposals
merge proposals
```

The review queue exists to expose those unresolved items to a human decision without letting the system quietly apply them.

## Governance rule

```text
The review queue is a queue of governed decisions.
A trigger may enqueue an item and notify; it never applies.
Resolution is always human: yes, no, defer or inspect evidence.
Every answer is an append-only event: who, what, before, after, why.
Trivial items may apply only at a low authority level and only if logged.
Consequential items require detail-before-yes or an approved proposal.
Every answer is reversible by a compensating event; no hard delete.
The queue is scoped and isolated.
An answered question is not re-asked until its evidence changes.
A priority score orders the review; it validates nothing.
```

## What may enqueue an item

A trigger may enqueue a review item when a candidate, conflict or ambiguity appears.

Allowed trigger classes:

```text
ingestion trigger
extraction trigger
document-intelligence trigger
workflow proposal trigger
Register Candidate trigger
scope conflict trigger
staleness trigger
risk trigger
phase or milestone trigger
manual user request
```

A trigger may:

```text
create a review item candidate
attach evidence references
set suggested priority
notify the user or expose the item in the cockpit
```

A trigger must not:

```text
approve
apply
merge
promote memory
send
transmit
file
archive as final
delete
resolve a conflict silently
```

## Review item shape

A review item should make the decision small, inspectable and reversible.

Conceptual shape:

```text
review_item:
  question
  type: merge | verify | classify | promote | rename | resolve_conflict | defer | reject
  candidates
  evidence_ref
  scope_id
  yes_effect
  no_effect
  defer_effect
  authority_level
  status: open | answered | applied | reverted | obsolete
  created_from
  created_at
  answered_by
  answered_at
```

This is not an approved database schema. Any schema candidate belongs under a separate approved schema change.

## Scope isolation

The queue must follow the same perimeter as the dossier, project, user, organization or domain scope.

A review session must not silently mix projects.

Required principle:

```text
One review session, one governed perimeter.
```

A cross-scope item must be explicit and must carry a stricter gate.

## Authority levels

Authority levels may reuse the workflow lifecycle authority scale when available.

Minimum posture:

```text
low consequence: logged correction may be allowed
medium consequence: human answer required
high consequence: detail-before-yes required
critical consequence: approved proposal or higher gate required
```

A swipe, click or quick answer may express intent. It must not bypass the authority level required by the item.

## Detail-before-yes

Consequential items must not be accepted blindly.

Detail-before-yes means the human must inspect enough evidence before an affirmative answer can apply.

Required for:

```text
merge of dossiers or matters
promotion to Registre Probatoire entry
approval field changes
contractual status changes
external transmission
delete or destructive action
cross-project classification
client or contractor identity merge
```

## Priority

Priority may help order the queue.

A useful conceptual score is:

```text
consequence x uncertainty x staleness
```

But priority is only sorting.

```text
Priority is not approval.
Confidence is not validation.
Staleness is not deletion.
Frequency is not memory promotion.
```

## Idempotence

An answered item should not be re-asked until the evidence changes.

Evidence changes may include:

```text
source version changed
new contradictory evidence found
scope changed
approval requirement changed
register-admission rule changed
user reverted the prior answer
```

## Reversibility

Resolution must be append-only.

Do not erase the prior answer. Add a compensating event.

Examples:

```text
answered_yes
applied
reverted_by_user
superseded_by_new_evidence
reopened_due_to_scope_change
```

## Relationship to document intelligence

`DOCUMENT_INTELLIGENCE.md` may produce review items when extraction or comparison produces uncertain claims.

Examples:

```text
confirm this obligation candidate?
classify this source as project or agency knowledge?
ask contractor to clarify this missing quote item?
promote this recurring vigilance point to agency checklist candidate?
```

The queue receives candidates. It does not validate them by receiving them.

## Relationship to the Registre Probatoire

Register-related review items are consequential by default.

The queue may ask:

```text
promote this Register Candidate?
reject this Register Candidate?
keep as project-scoped only?
mark as obsolete?
```

It must not promote a Registre Probatoire entry automatically.

## Relationship to implementation design

A future implementation may provide a gesture-based surface such as:

```text
yes
no
defer
inspect evidence
undo last answer
```

That surface belongs outside Pantheon governance doctrine.

The implementation may include tables, UI states, notification triggers or adapters, but those are external implementation details. They must reference this rule rather than redefine it.

## Non-goals

This document does not authorize:

```text
hidden queue runtime inside Pantheon
automatic scheduler inside Pantheon
automatic application of consequential decisions
automatic memory promotion
cross-scope review without explicit scope
hard delete as normal resolution
silent merge
decision by score
decision by confidence
external action without approval
```

## Boundary phrase

```text
The queue surfaces decisions.
It does not decide.
The answer is human, logged, scoped and reversible.
```
