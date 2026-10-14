# Hermes Run Launch Junction

Status: candidate support doctrine — external implementation merged / live target proof not run / activation not authorized.

Date: 2026-07-26

This document specializes `HERMES_EXECUTION_ADMISSION_BRIDGE.md` for the candidate Hermes Agent Runs API binding.

It does not replace the generic Execution Admission model and does not make `launch_reserved` mandatory for every future runtime binding.

It creates no Pantheon runtime, dispatcher, scheduler, queue, retry worker, provider router, MCP host, plugin manager, memory engine or automatic approval system.

```text
Pantheon governs the launch opportunity and its meaning.
An external Hermes Run Binding performs the native Hermes API call.
Hermes starts and executes its own run.
The human decides admission and separately gated consequential effects.
```

## Current external implementation

The executable candidate is now co-located under `Pantheon-Next/implementation/`. The former `ifanjuang/pantheon-mvp` repository is provenance only and is not an active execution owner.

Merged slices:

```text
7fcf2a5  Observe verified Hermes v0.19 Runs API without dispatch
c89aa60  Join governed admission to Hermes Runs API
3031c90  Add operator-only Hermes live binding acceptance
```

These merges establish implementation availability only.

```text
merged != installed
merged != approved
merged != activated
CI green != live target proof
```

The operator acceptance helper has not been run against a live Hermes target in the evidence available to this doctrine.

## Why the junction exists

The generic bridge deliberately leaves actual runtime start outside Pantheon.

Hermes exposes a native Runs API, but endpoint availability does not make Pantheon a dispatcher.

The binding separates four acts:

```text
1. Pantheon records one Execution Admission.
2. The external binding reserves that exact launch opportunity.
3. The external binding asks Hermes to create exactly one run.
4. Pantheon records the real run identity returned by Hermes.
```

Core distinctions:

```text
admission != dispatch
launch reservation != dispatch
launch reservation != Hermes run
POST /v1/runs != Pantheon execution
runtime start receipt != Evidence
runtime success != Evidence
```

## Binding-specific lifecycle

The generic bridge remains abstract.

The Hermes Runs candidate adds a narrower operational boundary:

```text
admitted
→ launch_reserved
→ consumed

launch_reserved
→ launch_expired
```

`launch_reserved` is binding-specific operational governance state.

```text
launch_reserved != universal Execution Admission state
```

Runtime start must match the exact valid `launch_reservation_id`.

## Launch reservation

The external candidate implements one immutable reservation per Execution Admission.

Candidate identity includes:

```text
launch_reservation_id
admission_ref
snapshot_ref
snapshot_digest
field_projection_version
work_issue_version
launch_expires_at
idempotency_key
reserved_by
reserved_at
```

Reservation is allowed only while the admission is still admitted and consumable.

The reservation closes the first-slice pre-launch revocation window before the native cross-system call begins.

The candidate reservation expires no later than 120 seconds after reservation and never later than the parent admission expiry. Expiry is evaluated lazily.

```text
no launch-expiry scheduler
launch_expired != renewed launch permission
```

An expired or ambiguous reservation is not automatically recycled.

## Launch Context Snapshot

Before the native Hermes call, the binding freezes a bounded bootstrap snapshot from the exact admitted Context Pack.

External contract:

```text
PostgreSQL isolation = REPEATABLE READ
field projection = scoped-context-v1
serialized ceiling = 120000 characters
source binary included = false
```

```text
Launch Context Snapshot
!= Evidence
!= global Agency Data
!= source-native binary
!= canonical memory
!= future owner state
```

After start, current owner values may be re-read only through Scoped Hermes Data Access for the same admitted identities.

## Tool-surface qualification before launch

The merged observer reads only:

```text
GET /v1/capabilities
GET /v1/toolsets
```

It verifies Runs API support and compares concrete active Hermes tools with an explicit reviewed allowlist and required-tool set.

Launch requires:

```text
runs_api_status = compatible
safety_status = qualified
```

Otherwise no launch reservation and no native run submission occur.

```text
reachable != healthy
healthy != safe
Runs API available != run authorized
toolset configured != toolset approved
read-only prompt != dangerous tool removed
```

The general Hermes API-server profile is not automatically qualified.

## External native run submission

The external binding performs exactly one native:

```text
POST /v1/runs
```

The request supplies:

```text
input        = bounded immutable launch material
session_id   = exact Pantheon admission_id
instructions = fixed read-only governance constraints
```

It supplies no model/provider override.

```text
Pantheon selects no provider/model
external binding selects no provider/model
Hermes retains provider/model routing
```

`session_id` is correlation only.

```text
session_id correlation != memory promotion
```

## Session/task identity

Current upstream Hermes Runs source maps a supplied Runs `session_id` to the `task_id` passed into agent execution.

That source review reduces implementation uncertainty but does not establish the behavior of any specific deployed target.

The candidate plugin therefore continues to fail closed unless its host task/session identity is shaped as the expected Pantheon admission identity.

```text
upstream source mapping reviewed
!= live target proof
```

## Distributed ambiguity and retry refusal

Pantheon and Hermes do not share one atomic transaction.

If `POST /v1/runs` has an uncertain network outcome after reservation:

```text
no automatic second POST
no reservation recycling
explicit operator reconciliation required
```

If Hermes returns a `run_id` but Pantheon start registration is uncertain:

```text
preserve run_id
preserve launch_reservation_id
explicit operator reconciliation required
no second run submitted automatically
```

The merged acceptance helper projects these cases as `inconclusive` rather than hiding them as generic failure.

```text
submission_unknown != retry instruction
registration_unknown != queue item
inconclusive != pass
```

## Active context after runtime start

Once the exact Hermes run is recorded as `running`, the candidate exposes admission-session reads over Scoped Hermes Data Access.

Pantheon resolves the run server-side. The caller/model does not supply a `run_id`.

The read boundary remains:

```text
exact admitted identity only
scoped-context-v1 allowlisted fields
current_owner_read semantics
no global Agency Data list/search
no source binary dereference
no write
access ends when the run is no longer running
```

## Candidate Hermes context plugin

The co-located implementation contains the candidate plugin `implementation/hermes/plugins/pantheon-context-bridge`.

It registers only:

```text
pantheon_context_manifest
pantheon_context_entity
```

The model-facing tool schemas expose no:

```text
admission_id
run_id
Pantheon URL
credential
arbitrary query
```

The model may request only an exact entity already present in its admitted manifest.

The plugin derives admission identity from host-provided Hermes task/session context and fails closed when the host identity is absent or invalid.

## Operator-only synthetic live acceptance

The co-located implementation also contains:

```text
implementation/scripts/hermes_live_binding_acceptance.py
```

Default mode observes only the Hermes Runs/toolset surfaces.

A live attempt requires all of:

```text
--run-live
--ack SYNTHETIC_ONLY
pre-created synthetic Execution Admission
question marker PANTHEON_HERMES_LIVE_ACCEPTANCE_V1
synthetic root entity id
explicit request for both Pantheon context tools
qualified tool surface
```

The first live proof must not use a professional dossier.

The helper returns:

```text
pass
fail
inconclusive
```

PASS requires, at minimum:

```text
Runs API compatible
tool surface qualified
Hermes status session_id == Pantheon admission_id
synthetic root visible in active manifest
out-of-scope entity read refused
tool.started/tool.completed for pantheon_context_manifest
tool.started/tool.completed for pantheon_context_entity
both required tools error-free
Hermes runtime completed
Pantheon return reconciled
active context closed after return
```

The helper never automatically:

```text
installs or enables the plugin
answers Hermes approval requests
retries an ambiguous launch
stops a run after an acceptance failure
activates the binding
```

```text
synthetic acceptance pass != production adoption
technical receipt != Evidence
```

## One-shot reconciliation

The external adapter may explicitly inspect one known run once.

Current mapping:

```text
completed -> Result Candidate path
failed    -> failed return
running   -> observation only
pending   -> observation only
stopping  -> observation only
cancelled -> observation only; no invented success mapping
```

It is not a poll loop, scheduler or monitor.

```text
Hermes completed != Evidence
Hermes completed != Knowledge
Hermes completed != Decision
Hermes completed != Work Issue resolved automatically
```

## Transaction-boundary hardening

Implementation CI exposed and corrected an older handoff transaction defect that could prevent a genuine `REPEATABLE READ` launch snapshot.

The merged implementation now keeps owner/case resolution inside the explicit handoff transaction and returns the top-level connection to idle before the launch snapshot transaction begins.

This is covered by regression tests.

## Responsibility allocation

### Pantheon governs

- Work Issue / Task Contract / Context Pack admission;
- whether one exact launch opportunity exists;
- reservation identity and bounded lifetime;
- launch snapshot provenance and digest;
- allowed identity perimeter and field projection contract;
- meaning of runtime start/return observations;
- consequential-effect gates;
- Evidence, Knowledge, Decision and canonicalization boundaries.

Pantheon does not call Hermes `/v1/runs`.

### Hermes executes

- actual agent run;
- provider/model routing;
- runtime tool calls inside its configured tool surface;
- runtime session/run identity;
- runtime status and candidate output.

### External Hermes Run Binding executes

- read-only Hermes API/tool-surface observation;
- one launch reservation request;
- exactly one native Runs API submission;
- start registration;
- optional explicit one-shot reconciliation.

It owns no queue, scheduler, retry worker, provider router or approval engine.

### External acceptance helper executes

- read-only target observation;
- one explicitly acknowledged synthetic acceptance attempt;
- finite event observation;
- negative scope probe;
- one-shot terminal reconciliation.

It does not install, enable, approve or activate the binding.

### Cockpit / OpenWebUI exposes

- Work Issue and admitted scope;
- admission / reservation / run observation states;
- unqualified profile, launch expiry and ambiguous-submission warnings;
- returned candidate and review need.

### Human approves

- Work Issue where required;
- Execution Admission;
- synthetic live attempt acknowledgement;
- separately gated consequential effects;
- future plugin/profile installation, enablement and activation if adopted.

### Forbidden

- Pantheon dispatching or running Hermes;
- PostgreSQL becoming a runtime queue;
- automatic launch retry after ambiguous network outcome;
- model-selected admission or run identity;
- generic Hermes profile treated as safe because healthy;
- source binary authority inferred from Context Pack inclusion;
- plugin installation implying approval or activation;
- first live proof using a real professional dossier;
- runtime success treated as Evidence or professional truth.

## Replaceable execution transport qualification — UHP Pantheon-Next#1141

The native Hermes Runs binding remains the current baseline. Issue Pantheon-Next#1141 qualified UHP as a possible replacement for the **external transport only** and closed with final posture `watch` because the stock HarnessRouter candidate did not match Pantheon's Hermes runtime. The last qualification pin was UHP 2026-09-28; the issue was initially characterized on UHP 2026-09-12.

```text
Pantheon Execution Admission
        |
        v
external execution binding
        |
        +--> current: native Hermes Runs API
        |
        `--> candidate: UHP client -> UHP server -> Hermes
```

Pantheon does not become the UHP task client. The external binding remains the actor that materializes one already-admitted launch opportunity.

Initial scope is UHP Core. Extended file/artifact surfaces may be qualified only where a demonstrated use case requires them. UHP Full lifecycle management is outside the selected scope.

The matched A/B uses two distinct one-shot Execution Admissions derived from the same immutable Task Contract / Context Pack / execution-basis digest. A single admission is never consumed twice merely to manufacture comparability.

The candidate must preserve several seams that the native binding currently makes explicit:

```text
UHP configured harness != effective Hermes tool surface proven
UHP session id != Pantheon admission identity
UHP task accepted != Pantheon authorization
UHP success != Evidence
UHP input_file available != ephemeral source-context lease qualified
UHP artifact produced != professional Source
```

In particular, the current context plugin derives the admission identity from host-provided Hermes task/session context. A model-visible prompt, instruction or arbitrary metadata field carrying `admission_id` is not a substitute. Pantheon-Next#1141 must prove a host-level correlation seam or classify that mismatch as blocking.

Likewise, UHP `disabledTools` is not assumed to prove a hard runtime block: the protocol permits runtimes that can only convey the restriction as standing instruction. Existing target-local tool-surface qualification must remain until an equal or stronger effective-surface proof exists.

Pantheon-Next#1141 concluded with final posture `watch`: stock HarnessRouter remained runtime-mismatched against Pantheon's selected Hermes release, so no causal matched A/B was manufactured. UHP therefore does not supersede Pantheon-Next#1125. Exact SHA-256 basis, immutable execution binding, bounded lifetime and fail-closed expiry remain owned by the smallest Pantheon-side transient lease seam.

The decision vocabulary for Pantheon-Next#1141 was:

```text
replace_native_binding
partial_transport_only
watch
reject
```

The recorded result is `watch`. UHP is not adopted. External pin freshness may trigger a new bounded qualification if a future reference implementation reaches exact Hermes runtime comparability.


## Ephemeral source-context lease — Pantheon-Next#1125

Ask-only transient material follows one bounded path:

```text
provider-normalized UTF-8 context
→ server recomputes exact content SHA-256
→ local ephemeral lease
→ lease_ref + lease_digest + provenance + expiry in Context Pack
→ Execution Admission
→ launch reservation revalidates exact lease
→ external binding materializes exact content
→ one Hermes submission
```

The lease owner is deliberately not a Source, storage, memory or execution owner.

```text
ephemeral lease != Source admission
ephemeral lease != AFFAIRES persistence
ephemeral lease != Hindsight memory
lease created != run authorized
lease materialized != run started
runtime success != Evidence
```

Only UTF-8 text is admitted in the first slice. Payload bytes live under a replaceable local transient root, are bounded by item/count/TTL limits and are checked on every read. Restart loss, expiry, deletion or digest drift fails closed and requires handoff re-preparation. No cleanup scheduler is introduced; expiry cleanup is lazy/best-effort.

The persisted handoff and launch snapshot contain descriptors only. The payload is returned only through the Hermes-authenticated materialization route for the exact live `admission_id + launch_reservation_id`, before the one-shot external binding submits Hermes. After runtime start, the admission is consumed and the pre-run materialization seam is no longer valid.

Provider credentials are not part of lease provenance. Provider-specific adapters such as Gmail remain responsible for verifying their own raw provider bytes before producing the bounded normalized lease representation.


## Capability Slot

```text
abstract capability:
  execute one admitted read-only Hermes work item

candidate binding:
  Hermes Agent Runs API
  + external Run Binding
  + pantheon-context-bridge plugin

installation:
  implementation package available externally
  target plugin/profile installation not proven

health:
  public API contract verified
  executable candidate CI green
  live target health not established

update:
  no update action authorized by this doctrine

activation:
  not authorized

Pantheon gates:
  Execution Admission before launch opportunity
  tool-surface qualification before native submission
  separate effect chokepoint for consequential effects
```

## Current implementation status

```text
external observer implementation           co-located under Pantheon-Next/implementation
external launch junction implementation    co-located under Pantheon-Next/implementation
operator live acceptance helper            co-located under Pantheon-Next/implementation
launch reservation persistence             implemented externally
Launch Context Snapshot                    implemented externally
launch_reserved / launch_expired state     implemented externally
Hermes Runs HTTP client                    implemented externally
external one-shot launch binding           implemented externally
ephemeral context lease owner               implemented externally
reserved transient materialization seam     implemented externally
active-context server resolver             implemented externally
native Hermes context plugin               implemented externally
live Hermes target                         not connected / not proven
live synthetic acceptance                  not run in available evidence
plugin installation on target              not proven
plugin enablement on target                not proven
production activation                      not authorized
```

## Adoption posture

Before any production activation, evidence must cover at least:

```text
dedicated target profile with reviewed concrete tool surface
plugin installed and enabled by operator action
synthetic target acceptance PASS
session/task identity target proof
out-of-scope refusal target proof
runtime event/tool target proof
return/context-closure target proof
rollback readiness
human activation decision
```

No item is satisfied merely because implementation code is merged.

## Final rule

```text
Pantheon may govern whether one exact Hermes run opportunity exists.
The external binding may materialize that opportunity exactly once.
Hermes runs Hermes.
A synthetic target proof may demonstrate behavior.
The human still decides installation, activation and consequential effects.
```
