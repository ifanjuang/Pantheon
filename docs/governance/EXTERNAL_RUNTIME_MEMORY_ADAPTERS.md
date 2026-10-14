# External Runtime Memory Adapters

Status: active support doctrine — generic boundary for external runtime memory, checkpoint, graph recall and observability adapters.

This document defines how external systems that store, recall, rank, summarize, checkpoint or trace agent context may be evaluated without becoming Pantheon authority.

It does not implement a runtime, memory backend, graph database, vector store, checkpoint engine, observability backend, MCP server, connector, schema, test, operation, platform component, Docker service, approval engine or automatic memory promotion.

Runtime/client/authority placement is inherited from `HERMES_INTEGRATION.md`: external runtime-memory systems remain runtime-side capabilities, optional compatible clients may expose runtime interaction, Pantheon Cockpit projects governed memory/Evidence status, and neither retrieval nor client selection transfers Pantheon authority.

## Purpose

External runtime memory tools are useful, but they sit on a dangerous boundary.

They may remember what an agent saw, what a user said, what a workflow did, what facts were inferred, what sources were retrieved, what trace was recorded, or where a long-running task stopped.

If this is not governed, runtime convenience can quietly become:

```text
truth
memory
Evidence
approval
scope
authorization
```

This document prevents that collapse.

The rule is simple:

```text
External runtime memory may store, recall, rank, summarize, checkpoint or trace.
It may propose Register Candidates and Evidence Pack Candidates.
It must not promote a Registre Probatoire entry, validate truth, approve action, decide scope or authorize external effects.
```

## Scope

This document covers external systems whose primary effect is one or more of the following:

```text
semantic recall
temporal graph memory
conversation or dossier memory
agent state
checkpoint and resume
trace observation
loop detection
provenance linking
context assembly
```

It applies whether the system is local, hosted, open source, managed, MCP-facing, embedded in an agent framework, or used behind Hermes or another execution runtime.

It does not select or endorse any product.

Product-specific reviews belong under:

```text
docs/governance/reference_reviews/
```

A product-specific binding or adapter may name tools because its subject is the tool relationship. This generic document uses abstract roles.

## Placement

External runtime memory belongs outside Pantheon.

Pantheon may define:

```text
adapter eligibility
allowed candidate outputs
forbidden outputs
scope discipline
memory promotion rules
Evidence expectations
review gates
approval thresholds
failure handling
```

Pantheon must not own:

```text
vector index runtime
graph runtime
checkpoint runtime
trace backend
agent memory engine
memory write engine
MCP memory server
observability backend
background scheduler
workflow runner
```

Execution remains in the execution runtime.

Observation remains in the observability layer.

Records remain in the external store or data registry.

Governed status remains in Pantheon.

## Adapter families

### Semantic memory adapter

A semantic memory adapter stores and retrieves memories, notes, summaries, user preferences, project context or agent-relevant statements.

Allowed output:

```text
Register Candidate
recall candidate
review signal
source reference
```

Forbidden output:

```text
Registre Probatoire entry
validated truth
approved project fact
final professional conclusion
```

A similarity score ranks review. It does not validate.

### Temporal graph memory adapter

A temporal graph memory adapter stores entities, relations, events and time-sensitive changes.

Allowed output:

```text
relationship candidate
temporal contradiction signal
supersession signal
Register Candidate
Evidence Pack Candidate material
```

Forbidden output:

```text
proof
approval
canonical dependency graph
final fact status
```

Connectivity is not proof.

A graph edge says that something may be related. It does not say that the relation is true, current, complete or professionally valid.

### Checkpoint state adapter

A checkpoint adapter stores runtime state so an interrupted task can resume.

Allowed output:

```text
Runtime State Reference
checkpoint reference
resume point
human-interrupt marker
```

Forbidden output:

```text
Registre Probatoire entry
Evidence Pack
approval record
scope decision
final status
```

A checkpoint is operational continuity. It is not governance continuity.

### Observability trace adapter

An observability adapter records traces, spans, tool calls, retrieval events, cost, latency, errors, model inputs and outputs, and run metadata.

Allowed output:

```text
Trace Reference
run reference
debug signal
audit-support material
Evidence Pack Candidate material
```

Forbidden output:

```text
Evidence Pack by itself
approval record
truth status
professional conclusion
```

A trace can support review. It is not review.

### Loop and failure detection adapter

A loop or failure detector identifies retries, oscillations, repeated tool calls, stalled reasoning, contradictory memory writes or crash recovery events.

Allowed output:

```text
Review Queue signal
suspend signal
human escalation signal
runtime health warning
```

Forbidden output:

```text
Zeus arbitration
approval refusal
memory deletion
scope change
external action block without governed rule
```

Loop detection can stop and ask. It cannot decide.

## Common envelope

An external runtime memory adapter communicates through the normal Pantheon envelope:

```text
Task Contract in
-> external adapter / runtime
-> Result Candidate + Evidence Pack Candidate + optional Register Candidate out
```

The adapter may return references, candidates and warnings.

It must never return final status.

## Adapter passport

Before any external runtime memory tool is used in a consequential workflow, it should be described through a non-executable adapter passport.

Minimum fields:

```text
adapter_id
adapter_family
owner_layer
primary_effect
storage_class
scope_behavior
memory_write_behavior
recall_behavior
candidate_output_types
forbidden_output_types
evidence_behavior
approval_behavior
trace_behavior
exportability
data_residency
retention_and_deletion_model
supersession_model
auditability
failure_modes
human_gate_triggers
```

This is a governance description, not an executable schema.

If a machine-checked schema is later created, it belongs under `schemas/` and requires explicit approval before modification.

## Write discipline

Any external memory write that may influence a later consequential answer must be recorded as candidate material.

Minimum write expectations:

```text
scope_id
source or origin
source_date or event_date
created_at
actor or runtime origin
statement or payload summary
confidence or extraction basis
status: candidate by default
review_after if time-sensitive
supersedes / superseded_by if known
```

A runtime may cache temporary execution context without review if the context does not affect future truth, memory, approval, scope or external action.

If it can affect a future consequential answer, it is a Register Candidate or Runtime State Reference, not a Registre Probatoire entry.

## Read discipline

External runtime memory may be read only inside the relevant scope.

Read rules:

```text
no cross-scope recall by default
no hidden generalization from one dossier to another
stale memory triggers review or reconfirmation
contradictory memory triggers review
low-confidence memory remains visibly low-confidence
summary must not hide missing sources
```

A retrieved memory is not proof.

A retrieved memory may become Evidence only when selected, represented and reviewed inside an Evidence Pack.

## Promotion discipline

Only the applicable Pantheon governance path and relevant human decision can promote durable governed memory.

An adapter must not promote memory because of:

```text
frequency of retrieval
embedding similarity
recency
confidence score
graph centrality
trace success
agent preference
lack of contradiction
```

Scores can prioritize review.

They cannot validate.

## Evidence discipline

External runtime memory may support Evidence Pack construction when it exposes:

```text
source reference
retrieval path
runtime trace reference
claim extracted
assumption made
contradiction found
scope attached
```

But an adapter output is only Evidence Pack Candidate material.

The Evidence Pack remains a governed object.

## Approval discipline

External runtime memory has no approval authority.

It cannot decide:

```text
send
file
sign
publish
merge
approve quote
approve invoice
promote memory
mark fact as final
commit a professional position
```

If an adapter detects that a candidate action touches an approval cliff, it must return an escalation signal or open a User Decision Gate through the appropriate surface.

## MCP boundary

If an adapter exposes MCP tools, MCP availability is not authorization.

Allowed:

```text
list memory candidates
retrieve scoped candidates
return trace reference
return checkpoint reference
emit review signal
```

Forbidden without governed approval:

```text
write canonical memory
approve memory promotion
send external message
modify project status
apply irreversible change
bypass Task Contract
```

MCP is an exposure or tool interface. It is not a governance grant.

## Review Queue relation

External runtime memory adapters may enqueue review items.

Examples:

```text
possible duplicate memory
possible contradiction
stale project fact
low-confidence extracted preference
cross-scope recall attempt
loop detected
missing source for recalled fact
```

A Review Queue item is a question, not a decision.

The queue may order the review. It does not validate the answer.

## Request Lifecycle relation

During request lifecycle work, external runtime memory may support existing owners with candidate material such as:

```text
MNEMOSYNE continuity framing with scoped prior context
ARGOS source/provenance challenge when recalled material must support a claim
MEMORY / Register-owner reconfirmation or retention candidates
ZEUS status/procedure arbitration with Evidence references when conflict remains
```

The adapter itself is not a Pantheon Role, memory authority, Evidence authority, approval authority or persistence authority.

It supplies scoped material and observations. The canonical Role registry remains `AGENTS.md`; durable-retention semantics remain with `MEMORY.md`, Register contracts and applicable approval owners.

## Failure modes

Every adapter review should explicitly check:

```text
false recall
stale recall
cross-scope leakage
silent memory write
silent memory deletion
memory summarized without source
trace mistaken for proof
checkpoint mistaken for memory
graph relation mistaken for truth
score mistaken for approval
vendor lock-in
non-exportable memory
unbounded retention
unreviewed personal or client data
```

If any failure can produce a false truth, wrong memory, unapproved external effect, invalid approval or unauthorized action, Pantheon governs the decision point.

## Candidate adoption path

A safe path for any external runtime memory tool:

```text
1. Product-specific reference review under reference_reviews/.
2. Adapter passport drafted.
3. Sandbox test outside Pantheon core.
4. Output limited to candidates and references.
5. Scope isolation verified.
6. Review Queue and Evidence Pack behavior checked.
7. Human decision gate tested for consequential effects.
8. Only then consider a binding or implementation outside Pantheon.
```

Any implementation work under `schemas/`, `tests/`, `operations/`, `platform/`, Docker or `.env` requires explicit confirmation.

## Rejected collapses

```text
runtime memory = Registre Probatoire entry
memory score = validated truth
graph relation = proof
checkpoint = memory
trace = Evidence Pack
MCP tool = task authorization
loop detection = Zeus arbitration
agent OS = Pantheon runtime
memory backend = approval engine
observability backend = governance record
```

## Decision vocabulary

Use the following statuses when reviewing external runtime memory tools:

```text
accepted as external reference
accepted as adapter candidate
sandbox only
to verify
refused as governance model
refused as runtime dependency
refused as memory authority
```

Never use:

```text
approved memory engine
Pantheon runtime memory
self-validating memory
trusted recall by default
```

## Boundary phrase

```text
The runtime may remember.
The adapter may retrieve.
The trace may support.
Pantheon governs status.
The human decides what remains.
```
